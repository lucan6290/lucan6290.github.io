use serde::{Deserialize, Serialize};
use std::env;
use std::fs::{self, OpenOptions};
use std::net::{SocketAddr, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
use std::time::{Duration, Instant};
use tauri::{Manager, State};

const BASE_URL: &str = "http://127.0.0.1:18000";

#[derive(Serialize)]
struct BackendConnection {
    base_url: String,
    token: String,
    content_root: String,
}

#[derive(Deserialize, Serialize)]
struct Health {
    service: String,
    api_version: u32,
    project_root: String,
    content_root: String,
}

#[derive(Deserialize)]
struct Session {
    token: String,
    project_root: String,
    content_root: String,
}

#[derive(Default)]
struct BackendRuntime {
    initialization: Mutex<()>,
    process: Mutex<Option<OwnedBackend>>,
    exiting: AtomicBool,
}

/// 只有启动器创建的进程进入此句柄；外部服务不会被管理或终止。
struct OwnedBackend {
    child: Child,
    #[cfg(windows)]
    job: windows_job::Job,
}

impl OwnedBackend {
    fn spawn(command: &mut Command) -> Result<Self, String> {
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            use windows_sys::Win32::System::Threading::{CREATE_NO_WINDOW, CREATE_SUSPENDED};
            command.creation_flags(CREATE_NO_WINDOW | CREATE_SUSPENDED);
        }
        #[cfg(unix)]
        {
            use std::os::unix::process::CommandExt;
            command.process_group(0);
        }
        let mut child = command
            .spawn()
            .map_err(|error| format!("无法启动内容后端：{error}"))?;
        #[cfg(windows)]
        let job = match windows_job::Job::attach_and_resume(&child) {
            Ok(job) => job,
            Err(error) => {
                let _ = child.kill();
                let _ = child.wait();
                return Err(format!("无法隔离内容后端进程树：{error}"));
            }
        };
        Ok(Self {
            child,
            #[cfg(windows)]
            job,
        })
    }
}

impl Drop for OwnedBackend {
    fn drop(&mut self) {
        #[cfg(windows)]
        self.job.terminate();
        #[cfg(unix)]
        {
            let _ = Command::new("kill")
                .args(["-TERM", "--", &format!("-{}", self.child.id())])
                .status();
        }
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

#[cfg(windows)]
mod windows_job {
    use std::io;
    use std::os::windows::io::AsRawHandle;
    use std::process::Child;
    use windows_sys::Win32::Foundation::{CloseHandle, HANDLE, INVALID_HANDLE_VALUE};
    use windows_sys::Win32::System::Diagnostics::ToolHelp::{
        CreateToolhelp32Snapshot, Thread32First, Thread32Next, TH32CS_SNAPTHREAD, THREADENTRY32,
    };
    use windows_sys::Win32::System::JobObjects::{
        AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation,
        SetInformationJobObject, TerminateJobObject, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    };
    use windows_sys::Win32::System::Threading::{OpenThread, ResumeThread, THREAD_SUSPEND_RESUME};

    pub struct Job(HANDLE);
    // 句柄仅由 BackendRuntime 的 Mutex 持有，Win32 Job 可跨线程关闭。
    unsafe impl Send for Job {}

    impl Job {
        pub fn attach_and_resume(child: &Child) -> io::Result<Self> {
            // 子进程以 CREATE_SUSPENDED 创建，入 Job 前不会产生 reload 子进程。
            unsafe {
                let handle = CreateJobObjectW(std::ptr::null(), std::ptr::null());
                if handle.is_null() {
                    return Err(io::Error::last_os_error());
                }
                let job = Self(handle);
                let mut limits: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = std::mem::zeroed();
                limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
                if SetInformationJobObject(
                    handle,
                    JobObjectExtendedLimitInformation,
                    &limits as *const _ as *const _,
                    std::mem::size_of_val(&limits) as u32,
                ) == 0
                    || AssignProcessToJobObject(handle, child.as_raw_handle() as HANDLE) == 0
                {
                    return Err(io::Error::last_os_error());
                }
                let snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
                if snapshot == INVALID_HANDLE_VALUE {
                    return Err(io::Error::last_os_error());
                }
                let mut entry: THREADENTRY32 = std::mem::zeroed();
                entry.dwSize = std::mem::size_of_val(&entry) as u32;
                let mut present = Thread32First(snapshot, &mut entry);
                let mut result = Err(io::Error::other("未找到内容后端的挂起主线程"));
                while present != 0 {
                    if entry.th32OwnerProcessID == child.id() {
                        let thread = OpenThread(THREAD_SUSPEND_RESUME, 0, entry.th32ThreadID);
                        if !thread.is_null() {
                            result = if ResumeThread(thread) == u32::MAX {
                                Err(io::Error::last_os_error())
                            } else {
                                Ok(())
                            };
                            CloseHandle(thread);
                        } else {
                            result = Err(io::Error::last_os_error());
                        }
                        break;
                    }
                    present = Thread32Next(snapshot, &mut entry);
                }
                CloseHandle(snapshot);
                result?;
                Ok(job)
            }
        }

        pub fn terminate(&self) {
            // Job 中只含本次启动的进程及其后代，包含 uvicorn reload 工作进程。
            unsafe {
                TerminateJobObject(self.0, 1);
            }
        }
    }

    impl Drop for Job {
        fn drop(&mut self) {
            unsafe {
                CloseHandle(self.0);
            }
        }
    }
}

fn validate_project_root(path: &Path) -> Result<PathBuf, String> {
    let root = fs::canonicalize(path)
        .map_err(|error| format!("项目根目录不可用（{}）：{error}", path.display()))?;
    if !root.join("frontend/content").is_dir() || !root.join("admin-desktop").is_dir() {
        return Err(format!(
            "项目根目录必须同时包含 frontend/content 与 admin-desktop：{}",
            root.display()
        ));
    }
    Ok(root)
}

fn resolve_project_root(
    explicit: Option<&Path>,
    cwd: Option<&Path>,
    executable_dir: Option<&Path>,
) -> Result<PathBuf, String> {
    if let Some(path) = explicit {
        return validate_project_root(path);
    }
    for start in [cwd, executable_dir].into_iter().flatten() {
        for path in start.ancestors() {
            if path.join("frontend/content").is_dir() && path.join("admin-desktop").is_dir() {
                return validate_project_root(path);
            }
        }
    }
    Err(
        "找不到包含 frontend/content 与 admin-desktop 的项目；请设置 LUCHUAN_PROJECT_ROOT 后重启。"
            .into(),
    )
}

fn find_project_root() -> Result<PathBuf, String> {
    let explicit = env::var_os("LUCHUAN_PROJECT_ROOT").map(PathBuf::from);
    let cwd = env::current_dir().ok();
    let executable = env::current_exe().ok();
    resolve_project_root(
        explicit.as_deref(),
        cwd.as_deref(),
        executable.as_deref().and_then(Path::parent),
    )
}

fn same_absolute_path(actual: &str, expected: &Path) -> bool {
    let path = Path::new(actual);
    if !path.is_absolute() {
        return false;
    }
    let Ok(actual) = fs::canonicalize(path) else {
        return false;
    };
    let Ok(expected) = fs::canonicalize(expected) else {
        return false;
    };
    #[cfg(windows)]
    {
        actual.to_string_lossy().to_lowercase() == expected.to_string_lossy().to_lowercase()
    }
    #[cfg(not(windows))]
    {
        actual == expected
    }
}

fn validate_health(health: &Health, root: &Path) -> Result<(), String> {
    if health.service != "xiaocancoding-content" || health.api_version != 1 {
        return Err("18000 端口上的服务不是兼容的箓川内容后端；请检查占用服务。".into());
    }
    let content_root = root.join("frontend/content");
    for (actual, expected) in [
        (&health.project_root, root),
        (&health.content_root, content_root.as_path()),
    ] {
        if !same_absolute_path(actual, expected) {
            return Err("18000 端口的服务或会话文件属于不同项目/内容目录；请检查 LUCHUAN_PROJECT_ROOT 和会话文件。".into());
        }
    }
    Ok(())
}

fn validate_identity(health: &Health, session: &Session, root: &Path) -> Result<(), String> {
    validate_health(health, root)?;
    if !same_absolute_path(&session.project_root, root)
        || !same_absolute_path(&session.content_root, &root.join("frontend/content"))
    {
        return Err("本项目会话文件的项目/内容目录与当前服务不一致；请重启内容后端。".into());
    }
    if session.token.trim().is_empty() {
        return Err("内容后端会话 token 为空；请重启该项目的内容后端。".into());
    }
    Ok(())
}

fn local_client() -> Result<reqwest::blocking::Client, String> {
    reqwest::blocking::Client::builder()
        .no_proxy()
        .redirect(reqwest::redirect::Policy::none())
        .timeout(Duration::from_secs(2))
        .build()
        .map_err(|error| format!("无法建立本地连接：{error}"))
}

fn connect_existing(
    client: &reqwest::blocking::Client,
    base_url: &str,
    root: &Path,
) -> Result<BackendConnection, String> {
    let health: Health = client
        .get(format!("{base_url}/health"))
        .send()
        .and_then(|response| response.error_for_status())
        .and_then(|response| response.json())
        .map_err(|error| format!("18000 端口健康检查失败：{error}"))?;
    validate_health(&health, root)?;
    let session_path = root.join(".codex-tmp/admin-desktop/session.json");
    let session: Session =
        serde_json::from_str(&fs::read_to_string(&session_path).map_err(|error| {
            format!(
                "无法读取本项目会话文件（{}）：{error}",
                session_path.display()
            )
        })?)
        .map_err(|_| "内容后端会话文件格式无效；请重启该项目的内容后端。".to_string())?;
    validate_identity(&health, &session, root)?;
    let response = client
        .get(format!("{base_url}/api/v1/documents/version"))
        .query(&[("path", "desktop-connection-probe.md")])
        .bearer_auth(&session.token)
        .send()
        .and_then(|response| response.error_for_status())
        .map_err(|_| "内容后端会话认证失败或会话已过期；请重启该项目的内容后端。".to_string())?;
    #[derive(Deserialize)]
    struct VersionProbe {
        exists: bool,
        version: Option<String>,
    }
    let probe: VersionProbe = response
        .json()
        .map_err(|_| "内容后端认证探测响应不符合接口契约。".to_string())?;
    if probe.exists != probe.version.is_some() {
        return Err("内容后端认证探测版本无效。".into());
    }
    Ok(BackendConnection {
        base_url: base_url.into(),
        token: session.token,
        content_root: health.content_root,
    })
}

fn spawn_backend(root: &Path) -> Result<OwnedBackend, String> {
    if !cfg!(debug_assertions) {
        return Err("当前生产包尚未配置内容后端 sidecar（externalBin）；请先启动本项目内容后端于 18000，或使用开发模式。".into());
    }
    let entry = root.join("admin-desktop/src-backend/main.py");
    if !entry.is_file() {
        return Err(format!("找不到内容后端入口：{}", entry.display()));
    }
    let backend_dir = root.join("admin-desktop/src-backend");
    let venv = if cfg!(windows) {
        backend_dir.join(".venv/Scripts/python.exe")
    } else {
        backend_dir.join(".venv/bin/python")
    };
    let python = if venv.is_file() {
        venv
    } else {
        PathBuf::from("python")
    };
    let log_dir = root.join(".codex-tmp/admin-desktop");
    fs::create_dir_all(&log_dir).map_err(|error| format!("无法创建后端日志目录：{error}"))?;
    let log_path = log_dir.join("backend.log");
    let log = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&log_path)
        .map_err(|error| format!("无法打开后端日志：{error}"))?;
    let stderr = log
        .try_clone()
        .map_err(|error| format!("无法打开后端错误日志：{error}"))?;
    let mut command = Command::new(python);
    command
        .arg(entry)
        .arg("--project-root")
        .arg(root)
        .args(["--port", "18000", "--reload"])
        .current_dir(root)
        .env("PYTHONUNBUFFERED", "1")
        .stdin(Stdio::null())
        .stdout(Stdio::from(log))
        .stderr(Stdio::from(stderr));
    OwnedBackend::spawn(&mut command)
}

fn initialize_backend(runtime: &BackendRuntime) -> Result<BackendConnection, String> {
    let root = find_project_root()?;
    let client = local_client()?;
    let address: SocketAddr = "127.0.0.1:18000".parse().unwrap();
    if TcpStream::connect_timeout(&address, Duration::from_millis(500)).is_ok() {
        return connect_existing(&client, BASE_URL, &root);
    }
    {
        let mut process = runtime.process.lock().map_err(|_| "后端进程状态不可用。")?;
        if runtime.exiting.load(Ordering::SeqCst) {
            return Err("应用正在退出。".into());
        }
        if let Some(backend) = process.as_mut() {
            if backend
                .child
                .try_wait()
                .map_err(|error| format!("无法检查后端进程：{error}"))?
                .is_some()
            {
                process.take();
            }
        }
        if process.is_none() {
            *process = Some(spawn_backend(&root)?);
        }
    }
    let start = Instant::now();
    let mut last_error = "内容后端尚未就绪。".to_string();
    while start.elapsed() < Duration::from_secs(30) && !runtime.exiting.load(Ordering::SeqCst) {
        {
            let mut process = runtime.process.lock().map_err(|_| "后端进程状态不可用。")?;
            if let Some(backend) = process.as_mut() {
                if let Some(status) = backend
                    .child
                    .try_wait()
                    .map_err(|error| format!("无法检查后端进程：{error}"))?
                {
                    process.take();
                    return Err(format!(
                        "内容后端已退出（{status}）；请查看 {}。",
                        root.join(".codex-tmp/admin-desktop/backend.log").display()
                    ));
                }
            }
        }
        match connect_existing(&client, BASE_URL, &root) {
            Ok(connection) => return Ok(connection),
            Err(error) => last_error = error,
        }
        std::thread::sleep(Duration::from_millis(250));
    }
    runtime
        .process
        .lock()
        .map_err(|_| "后端进程状态不可用。")?
        .take();
    Err(format!(
        "内容后端启动失败：{last_error} 日志：{}",
        root.join(".codex-tmp/admin-desktop/backend.log").display()
    ))
}

#[tauri::command]
async fn get_backend_connection(app: tauri::AppHandle) -> Result<BackendConnection, String> {
    tauri::async_runtime::spawn_blocking(move || {
        let runtime: State<BackendRuntime> = app.state();
        let _initializing = runtime
            .initialization
            .lock()
            .map_err(|_| "后端连接状态不可用。")?;
        let result = initialize_backend(&runtime);
        if result.is_err() {
            if let Ok(mut process) = runtime.process.lock() {
                process.take();
            }
        }
        result
    })
    .await
    .map_err(|error| format!("内容后端启动任务失败：{error}"))?
}

#[tauri::command]
fn minimize_window(window: tauri::WebviewWindow) {
    let _ = window.minimize();
}

#[tauri::command]
fn maximize_window(window: tauri::WebviewWindow) {
    if window.is_maximized().unwrap_or(false) {
        let _ = window.unmaximize();
    } else {
        let _ = window.maximize();
    }
}

#[tauri::command]
fn close_window(window: tauri::WebviewWindow) {
    let _ = window.close();
}

#[tauri::command]
fn is_maximized(window: tauri::WebviewWindow) -> bool {
    window.is_maximized().unwrap_or(false)
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_process::init())
        .manage(BackendRuntime::default())
        .invoke_handler(tauri::generate_handler![
            get_backend_connection,
            minimize_window,
            maximize_window,
            close_window,
            is_maximized,
        ])
        .build(tauri::generate_context!())
        .expect("构建 Tauri 应用时出错")
        .run(|app, event| {
            if let tauri::RunEvent::Exit = event {
                let runtime: State<BackendRuntime> = app.state();
                runtime.exiting.store(true, Ordering::SeqCst);
                if let Ok(mut process) = runtime.process.lock() {
                    process.take();
                };
            }
        });
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fixture(name: &str) -> PathBuf {
        let root = env::temp_dir().join(format!("luchuan-{}-{}", name, std::process::id()));
        std::fs::create_dir_all(root.join("frontend/content")).unwrap();
        std::fs::create_dir_all(root.join("admin-desktop")).unwrap();
        std::fs::canonicalize(root).unwrap()
    }

    fn identities(root: &std::path::Path) -> (Health, Session) {
        let project_root = root.to_string_lossy().to_string();
        let content_root = root.join("frontend/content").to_string_lossy().to_string();
        (
            Health {
                service: "xiaocancoding-content".into(),
                api_version: 1,
                project_root: project_root.clone(),
                content_root: content_root.clone(),
            },
            Session {
                token: "test-session".into(),
                project_root,
                content_root,
            },
        )
    }

    #[test]
    fn explicit_invalid_project_does_not_fall_back_to_cwd() {
        let root = fixture("invalid-override");
        assert!(resolve_project_root(Some(&root.join("missing")), Some(&root), None).is_err());
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn finds_project_from_executable_ancestors() {
        let root = fixture("executable-root");
        std::fs::create_dir_all(root.join("admin-desktop/target/debug")).unwrap();
        assert_eq!(
            resolve_project_root(None, None, Some(&root.join("admin-desktop/target/debug")))
                .unwrap(),
            root
        );
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_other_service_version_and_project_even_with_matching_session() {
        let root = fixture("identity");
        let (mut health, session) = identities(&root);
        assert!(validate_identity(&health, &session, &root).is_ok());
        health.service = "other-service".into();
        assert!(validate_identity(&health, &session, &root).is_err());
        health.service = "xiaocancoding-content".into();
        health.api_version = 2;
        assert!(validate_identity(&health, &session, &root).is_err());
        health.api_version = 1;
        health.project_root = root.join("admin-desktop").to_string_lossy().to_string();
        assert!(validate_identity(&health, &session, &root).is_err());
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_stale_session_roots_and_empty_token() {
        let root = fixture("session");
        let (health, mut session) = identities(&root);
        session.content_root = root.join("admin-desktop").to_string_lossy().to_string();
        assert!(validate_identity(&health, &session, &root).is_err());
        session.content_root = health.content_root.clone();
        session.token.clear();
        assert!(validate_identity(&health, &session, &root).is_err());
        std::fs::remove_dir_all(root).unwrap();
    }

    #[cfg(windows)]
    #[test]
    fn windows_identity_accepts_case_and_separator_differences() {
        let root = fixture("path-normalization");
        let (mut health, mut session) = identities(&root);
        health.project_root = health
            .project_root
            .trim_start_matches(r"\\?\")
            .replace('\\', "/")
            .to_uppercase();
        session.content_root = session
            .content_root
            .trim_start_matches(r"\\?\")
            .replace('\\', "/")
            .to_uppercase();
        assert!(validate_identity(&health, &session, &root).is_ok());
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn existing_connection_verifies_bearer_token_with_protected_endpoint() {
        use std::io::{Read, Write};
        use std::net::TcpListener;
        for accepted in [false, true] {
            let root = fixture(if accepted { "auth-valid" } else { "auth-stale" });
            let (health, session) = identities(&root);
            std::fs::create_dir_all(root.join(".codex-tmp/admin-desktop")).unwrap();
            std::fs::write(root.join(".codex-tmp/admin-desktop/session.json"), serde_json::json!({"token": session.token,"project_root":session.project_root,"content_root":session.content_root}).to_string()).unwrap();
            let listener = TcpListener::bind("127.0.0.1:0").unwrap();
            let base_url = format!("http://{}", listener.local_addr().unwrap());
            let body = serde_json::to_string(&health).unwrap();
            let server = std::thread::spawn(move || {
                for index in 0..2 {
                    let (mut stream, _) = listener.accept().unwrap();
                    stream
                        .set_read_timeout(Some(Duration::from_secs(3)))
                        .unwrap();
                    let mut request = [0; 4096];
                    let len = stream.read(&mut request).unwrap();
                    let request = String::from_utf8_lossy(&request[..len]).to_lowercase();
                    let (status, response) = if index == 0 {
                        assert!(request.starts_with("get /health "));
                        ("200 OK", body.as_str())
                    } else {
                        assert!(request.starts_with(
                            "get /api/v1/documents/version?path=desktop-connection-probe.md "
                        ));
                        assert!(request.contains("authorization: bearer test-session"));
                        if accepted {
                            ("200 OK", "{\"exists\":false,\"version\":null}")
                        } else {
                            ("401 Unauthorized", "{}")
                        }
                    };
                    write!(stream, "HTTP/1.1 {}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}", status, response.len(), response).unwrap();
                }
            });
            let client = local_client().unwrap();
            assert_eq!(
                connect_existing(&client, &base_url, &root).is_ok(),
                accepted
            );
            server.join().unwrap();
            std::fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn discovers_new_content_project_without_legacy_backend() {
        let root = env::temp_dir().join(format!("luchuan-launcher-root-{}", std::process::id()));
        std::fs::create_dir_all(root.join("frontend/content")).unwrap();
        std::fs::create_dir_all(root.join("admin-desktop/src-tauri")).unwrap();
        let found = resolve_project_root(None, Some(&root.join("admin-desktop/src-tauri")), None);
        let expected = std::fs::canonicalize(&root).unwrap();
        std::fs::remove_dir_all(&root).unwrap();
        assert_eq!(found.unwrap(), expected);
    }

    #[cfg(windows)]
    #[test]
    #[ignore = "仅由 owned_backend_terminates_descendant_process 调用的进程辅助用例"]
    fn process_tree_child() {
        use std::os::windows::process::CommandExt;
        use windows_sys::Win32::System::Threading::CREATE_NO_WINDOW;
        if env::var_os("LUCHUAN_PROCESS_TEST_LEAF").is_some() {
            std::thread::sleep(Duration::from_secs(60));
            return;
        }
        let mut child = Command::new(env::current_exe().unwrap())
            .args([
                "--exact",
                "tests::process_tree_child",
                "--ignored",
                "--nocapture",
            ])
            .env("LUCHUAN_PROCESS_TEST_LEAF", "1")
            .creation_flags(CREATE_NO_WINDOW)
            .spawn()
            .unwrap();
        std::fs::write(
            env::var_os("LUCHUAN_PROCESS_TEST_FILE").unwrap(),
            child.id().to_string(),
        )
        .unwrap();
        let _ = child.wait();
    }

    #[cfg(windows)]
    #[test]
    fn owned_backend_terminates_descendant_process() {
        use windows_sys::Win32::Foundation::{CloseHandle, WAIT_OBJECT_0};
        use windows_sys::Win32::System::Threading::{
            OpenProcess, TerminateProcess, WaitForSingleObject, PROCESS_SYNCHRONIZE,
            PROCESS_TERMINATE,
        };
        let root = fixture("process-tree");
        let pid_file = root.join("descendant.pid");
        let mut command = Command::new(env::current_exe().unwrap());
        command
            .args([
                "--exact",
                "tests::process_tree_child",
                "--ignored",
                "--nocapture",
            ])
            .env("LUCHUAN_PROCESS_TEST_FILE", &pid_file)
            .stdout(Stdio::null())
            .stderr(Stdio::null());
        let backend = OwnedBackend::spawn(&mut command).unwrap();
        let start = Instant::now();
        while !pid_file.exists() && start.elapsed() < Duration::from_secs(10) {
            std::thread::sleep(Duration::from_millis(20));
        }
        let pid: u32 = std::fs::read_to_string(&pid_file)
            .expect("后端辅助进程未创建子进程")
            .parse()
            .unwrap();
        // 保留后代进程句柄，验证其退出；失败路径也显式清理测试进程。
        unsafe {
            let handle = OpenProcess(PROCESS_SYNCHRONIZE | PROCESS_TERMINATE, 0, pid);
            assert!(!handle.is_null());
            drop(backend);
            let result = WaitForSingleObject(handle, 2000);
            if result != WAIT_OBJECT_0 {
                TerminateProcess(handle, 1);
            }
            CloseHandle(handle);
            std::fs::remove_dir_all(root).unwrap();
            assert_eq!(result, WAIT_OBJECT_0, "退出必须终止后端的 reload 后代进程");
        }
    }
}
