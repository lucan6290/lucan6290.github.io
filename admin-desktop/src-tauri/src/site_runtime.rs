use crate::{local_client, same_absolute_path, BackendRuntime, OwnedProcess};
use serde::{Deserialize, Serialize};
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::net::{SocketAddr, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Command, ExitStatus, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
use std::time::{Duration, Instant};
use tauri::{Manager, Url};
use tauri_plugin_opener::OpenerExt;

const SITE_URL: &str = "http://127.0.0.1:3400";
const SITE_ADDRESS: SocketAddr = SocketAddr::V4(std::net::SocketAddrV4::new(
    std::net::Ipv4Addr::LOCALHOST,
    3400,
));
const CONTENT_CLI: &str = "scripts/build-content.mjs";
const VITE_CLI: &str = "node_modules/vite/bin/vite.js";
const TYPE_CLI: &str = "node_modules/vue-tsc/bin/vue-tsc.js";

#[derive(Default)]
pub(crate) struct SiteRuntime {
    preview: Mutex<Option<OwnedProcess>>,
    task: Mutex<Option<OwnedProcess>>,
    exiting: AtomicBool,
}

impl SiteRuntime {
    pub(crate) fn stop_preview(&self) {
        if let Ok(mut process) = self.preview.lock() {
            process.take();
        }
    }

    pub(crate) fn shutdown(&self) {
        self.exiting.store(true, Ordering::SeqCst);
        self.stop_preview();
        if let Ok(mut process) = self.task.lock() {
            process.take();
        }
    }

    fn start_node(
        &self,
        slot: &Mutex<Option<OwnedProcess>>,
        frontend: &Path,
        args: &[&str],
        log_path: &Path,
    ) -> Result<u32, String> {
        let mut process = slot.lock().map_err(|_| "站点进程状态不可用。")?;
        if self.exiting.load(Ordering::SeqCst) {
            return Err("应用正在退出。".into());
        }
        let mut log = OpenOptions::new()
            .append(true)
            .open(log_path)
            .map_err(|error| format!("无法打开站点日志：{error}"))?;
        writeln!(log, "\n> node {}", args.join(" "))
            .map_err(|error| format!("无法写入站点日志：{error}"))?;
        let stderr = log
            .try_clone()
            .map_err(|error| format!("无法打开站点错误日志：{error}"))?;
        let mut command = Command::new("node");
        command
            .args(args)
            .current_dir(frontend)
            .env("NO_COLOR", "1")
            .stdin(Stdio::null())
            .stdout(Stdio::from(log))
            .stderr(Stdio::from(stderr));
        let child = OwnedProcess::spawn(&mut command)
            .map_err(|error| format!("无法启动站点命令，请确认 PATH 中可用 Node.js。{error}"))?;
        let pid = child.child.id();
        *process = Some(child);
        Ok(pid)
    }

    fn run_node(
        &self,
        frontend: &Path,
        args: &[&str],
        log_path: &Path,
    ) -> Result<ExitStatus, String> {
        self.start_node(&self.task, frontend, args, log_path)?;
        loop {
            if let Some(status) = poll_node(&self.task)? {
                return Ok(status);
            }
            std::thread::sleep(Duration::from_millis(100));
        }
    }
}

#[derive(Deserialize)]
struct SiteIdentity {
    service: String,
    project_root: String,
    pid: u32,
    route: Option<String>,
}

#[derive(Serialize)]
pub(crate) struct PreviewResult {
    url: String,
    owned: bool,
    log_path: Option<PathBuf>,
}

#[derive(Serialize)]
pub(crate) struct BuildResult {
    exit_code: Option<i32>,
    output_dir: Option<PathBuf>,
    log_path: PathBuf,
    log_tail: String,
}

fn verified_preview(
    client: &reqwest::blocking::Client,
    base: &str,
    root: &Path,
    document: Option<&str>,
) -> Result<(Url, u32), String> {
    let base = Url::parse(base).map_err(|error| error.to_string())?;
    let endpoint = base
        .join("/__luchuan_desktop_site")
        .map_err(|error| error.to_string())?;
    let mut request = client.get(endpoint).header("X-Luchuan-Desktop", "1");
    if let Some(document) = document {
        request = request.query(&[("document", document)]);
    }
    let identity: SiteIdentity = request
        .send()
        .and_then(|response| response.error_for_status())
        .and_then(|response| response.json())
        .map_err(|_| "3400 端口上的服务无法确认是当前工作区的新站，请检查端口占用。")?;
    if identity.service != "xiaocancoding-site" || !same_absolute_path(&identity.project_root, root)
    {
        return Err("3400 端口已被其他项目或服务占用，请检查占用方。".into());
    }
    let route = identity
        .route
        .filter(|route| route.starts_with('/') && !route.starts_with("//") && !route.contains('\\'))
        .ok_or("当前文档没有可预览的站点地址，请先保存到站点栏目。")?;
    let url = base.join(&route).map_err(|error| error.to_string())?;
    if url.origin() != base.origin() {
        return Err("站点返回了无效的预览地址。".into());
    }
    Ok((url, identity.pid))
}

fn poll_node(slot: &Mutex<Option<OwnedProcess>>) -> Result<Option<ExitStatus>, String> {
    let mut process = slot.lock().map_err(|_| "站点进程状态不可用。")?;
    let child = process.as_mut().ok_or("站点任务已停止。")?;
    let status = child
        .child
        .try_wait()
        .map_err(|error| format!("无法检查站点进程：{error}"))?;
    if status.is_some() {
        process.take();
    }
    Ok(status)
}

fn site_frontend(root: &Path, required_clis: &[&str]) -> Result<PathBuf, String> {
    let frontend = root.join("frontend");
    if !frontend.join("package.json").is_file() || !frontend.join(CONTENT_CLI).is_file() {
        return Err("当前工作区缺少新站源码（frontend/package.json 或内容生成脚本）。".into());
    }
    if required_clis
        .iter()
        .any(|cli| !frontend.join(cli).is_file())
    {
        return Err(format!(
            "当前工作区缺少站点依赖，请在 {} 执行 pnpm install。",
            frontend.display()
        ));
    }
    Ok(frontend)
}

fn create_log(state_dir: &Path, name: &str) -> Result<PathBuf, String> {
    let path = state_dir.join(name);
    fs::create_dir_all(state_dir)
        .and_then(|()| File::create(&path).map(|_| ()))
        .map_err(|error| format!("无法创建站点日志（{}）：{error}", path.display()))?;
    Ok(path)
}

fn read_log_tail(path: &Path) -> std::io::Result<String> {
    let mut file = File::open(path)?;
    file.seek(SeekFrom::Start(
        file.metadata()?.len().saturating_sub(12_000),
    ))?;
    let mut output = Vec::new();
    file.read_to_end(&mut output)?;
    Ok(String::from_utf8_lossy(&output).into_owned())
}

fn site_port_open() -> bool {
    TcpStream::connect_timeout(&SITE_ADDRESS, Duration::from_millis(250)).is_ok()
}

fn open_preview(
    runtime: &SiteRuntime,
    root: &Path,
    state_dir: &Path,
    document: Option<&str>,
) -> Result<PreviewResult, String> {
    let client = local_client()?;
    if site_port_open() {
        let (url, pid) = verified_preview(&client, SITE_URL, root, document)?;
        let owned = runtime
            .preview
            .lock()
            .map_err(|_| "站点进程状态不可用。")?
            .as_ref()
            .is_some_and(|process| process.child.id() == pid);
        return Ok(PreviewResult {
            url: url.into(),
            owned,
            log_path: owned.then(|| state_dir.join("site-preview.log")),
        });
    }

    let frontend = site_frontend(root, &[VITE_CLI])?;
    runtime.stop_preview();
    let log_path = create_log(state_dir, "site-preview.log")?;
    let status = runtime.run_node(&frontend, &[CONTENT_CLI], &log_path)?;
    if !status.success() {
        return Err(format!(
            "站点内容生成失败（{status}）。日志：{}",
            log_path.display()
        ));
    }
    let pid = runtime.start_node(
        &runtime.preview,
        &frontend,
        &[
            VITE_CLI,
            "--host",
            "127.0.0.1",
            "--port",
            "3400",
            "--strictPort",
        ],
        &log_path,
    )?;
    let start = Instant::now();
    let startup = (|| {
        while start.elapsed() < Duration::from_secs(30) {
            if let Some(status) = poll_node(&runtime.preview)? {
                return Err(format!("站点预览已退出（{status}）。"));
            }
            if site_port_open() {
                let (_, actual_pid) = verified_preview(&client, SITE_URL, root, None)?;
                if actual_pid == pid {
                    return Ok(());
                }
                return Err("3400 端口已被外部站点进程占用。".into());
            }
            std::thread::sleep(Duration::from_millis(200));
        }
        Err("站点预览启动超时，请检查 3400 端口和站点配置。".into())
    })();
    if let Err(error) = startup {
        runtime.stop_preview();
        return Err(format!("{error} 日志：{}", log_path.display()));
    }
    let (url, _) = verified_preview(&client, SITE_URL, root, document)?;
    Ok(PreviewResult {
        url: url.into(),
        owned: true,
        log_path: Some(log_path),
    })
}

fn build_site(runtime: &SiteRuntime, root: &Path, state_dir: &Path) -> Result<BuildResult, String> {
    let frontend = site_frontend(root, &[VITE_CLI, TYPE_CLI])?;
    let log_path = create_log(state_dir, "site-build.log")?;
    let dist = frontend.join("dist");
    let index = dist.join("index.html");
    let last_build = || index.metadata().and_then(|file| file.modified()).ok();
    let previous_build = last_build();
    let mut output_dir = None;
    let mut exit_code = None;
    for args in [
        &[CONTENT_CLI][..],
        &[TYPE_CLI, "-b"],
        &[VITE_CLI, "build", "--outDir", "dist"],
    ] {
        let status = runtime.run_node(&frontend, args, &log_path)?;
        exit_code = status.code();
        if !status.success() {
            break;
        }
        if args[0] == VITE_CLI
            && index.is_file()
            && last_build().is_some_and(|modified| Some(modified) != previous_build)
        {
            output_dir = Some(dist.clone());
        }
    }
    let log_tail = read_log_tail(&log_path).unwrap_or_default();
    Ok(BuildResult {
        exit_code,
        output_dir,
        log_path,
        log_tail,
    })
}

#[tauri::command]
pub(crate) async fn open_site_preview(
    app: tauri::AppHandle,
    document_path: Option<String>,
) -> Result<PreviewResult, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let backend = app.state::<BackendRuntime>();
        let _operation = backend
            .initialization
            .try_lock()
            .map_err(|_| "已有站点或工作区任务正在执行。")?;
        let workspace = backend.active_workspace()?;
        let result = open_preview(
            &app.state(),
            &workspace.root,
            &workspace.state_dir,
            document_path.as_deref(),
        )?;
        app.opener()
            .open_url(&result.url, None::<&str>)
            .map_err(|error| format!("无法打开站点预览：{error}"))?;
        Ok(result)
    })
    .await
    .map_err(|error| format!("站点预览任务失败：{error}"))?
}

#[tauri::command]
pub(crate) async fn build_blog_site(app: tauri::AppHandle) -> Result<BuildResult, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let backend = app.state::<BackendRuntime>();
        let _operation = backend
            .initialization
            .try_lock()
            .map_err(|_| "已有站点或工作区任务正在执行。")?;
        let workspace = backend.active_workspace()?;
        build_site(&app.state(), &workspace.root, &workspace.state_dir)
    })
    .await
    .map_err(|error| format!("站点构建任务失败：{error}"))?
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{Read, Write};
    use std::net::TcpListener;

    #[test]
    fn preview_verifies_service_project_and_stays_on_the_fixed_origin() {
        let root = crate::tests::fixture("site-preview-project");
        let other = crate::tests::fixture("site-preview-other-project");
        for (service, project, route, verified) in [
            ("xiaocancoding-site", &root, "/blog/abc%20def", true),
            ("xiaocancoding-site", &other, "/blog/abc", false),
            ("another-site", &root, "/blog/abc", false),
            ("xiaocancoding-site", &root, "//elsewhere.example", false),
        ] {
            let listener = TcpListener::bind("127.0.0.1:0").unwrap();
            let base = format!("http://{}", listener.local_addr().unwrap());
            let body = serde_json::json!({
                "service": service, "project_root": project, "pid": 123, "route": route
            })
            .to_string();
            let server = std::thread::spawn(move || {
                let (mut stream, _) = listener.accept().unwrap();
                stream
                    .set_read_timeout(Some(Duration::from_secs(2)))
                    .unwrap();
                let mut bytes = [0; 4096];
                let size = stream.read(&mut bytes).unwrap();
                let request = String::from_utf8_lossy(&bytes[..size]).to_lowercase();
                assert!(request.starts_with("get /__luchuan_desktop_site?document=blog%2fabc.md "));
                assert!(request.contains("x-luchuan-desktop: 1"));
                write!(stream, "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}", body.len(), body).unwrap();
            });
            let client = crate::local_client().unwrap();
            assert_eq!(
                verified_preview(&client, &base, &root, Some("blog/abc.md")).is_ok(),
                verified
            );
            server.join().unwrap();
        }
        fs::remove_dir_all(root).unwrap();
        fs::remove_dir_all(other).unwrap();
    }

    #[test]
    fn build_reports_a_real_output_and_failing_exit_code() {
        let root = crate::tests::fixture("site-build with spaces-&");
        let frontend = root.join("frontend");
        let state_dir = root.join("app data");
        let vite = frontend.join("node_modules/vite/bin/vite.js");
        for (path, body) in [
            (frontend.join("package.json"), "{}"),
            (frontend.join("scripts/build-content.mjs"), "console.log('generated');"),
            (frontend.join("node_modules/vue-tsc/bin/vue-tsc.js"), "console.log('checked');"),
            (vite.clone(), "const fs = require('node:fs'); fs.mkdirSync('dist', { recursive: true }); fs.writeFileSync('dist/index.html', 'fresh'); console.log('compiled');"),
        ] {
            fs::create_dir_all(path.parent().unwrap()).unwrap();
            fs::write(path, body).unwrap();
        }

        let runtime = SiteRuntime::default();
        let result = build_site(&runtime, &root, &state_dir).unwrap();
        assert_eq!(result.exit_code, Some(0));
        assert_eq!(result.output_dir, Some(frontend.join("dist")));
        assert!(result.log_tail.contains("generated"));
        assert!(result.log_tail.contains("checked"));
        assert!(result.log_tail.contains("compiled"));
        assert_eq!(
            fs::read_to_string(frontend.join("dist/index.html")).unwrap(),
            "fresh"
        );

        fs::write(&vite, "console.error('failed'); process.exit(7);").unwrap();
        let result = build_site(&runtime, &root, &state_dir).unwrap();
        assert_eq!(result.exit_code, Some(7));
        assert!(result.output_dir.is_none());
        assert!(result.log_tail.contains("failed"));
        assert!(!result.log_tail.contains("compiled"));

        fs::write(vite, "console.log('no output');").unwrap();
        let result = build_site(&runtime, &root, &state_dir).unwrap();
        assert_eq!(result.exit_code, Some(0));
        assert!(result.output_dir.is_none(), "旧构建产物不应算作本次构建");
        fs::remove_dir_all(root).unwrap();
    }
}
