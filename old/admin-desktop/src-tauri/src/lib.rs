use std::env;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::{Duration, Instant};
use tauri::{Manager, State};

/// 全局持有的 Python 后端子进程句柄，应用退出时自动清理
struct BackendProcess(Mutex<Option<Child>>);

/// 查找一个可用的本地端口
fn find_free_port() -> u16 {
    portpicker::pick_unused_port().expect("没有可用端口")
}

/// 等待后端健康检查通过
fn wait_for_backend(port: u16) -> bool {
    let url = format!("http://127.0.0.1:{}/api/v1/health", port);
    let start = Instant::now();
    let timeout = Duration::from_secs(30);

    while start.elapsed() < timeout {
        if let Ok(resp) = reqwest::blocking::Client::new()
            .get(&url)
            .timeout(Duration::from_secs(2))
            .send()
        {
            if resp.status().is_success() {
                return true;
            }
        }
        std::thread::sleep(Duration::from_millis(500));
    }
    false
}

/// 从当前工作目录向上查找项目根目录（包含 admin/ 和 admin-desktop/ 的目录）
fn find_project_root() -> Option<PathBuf> {
    let mut p = env::current_dir().ok()?;
    for _ in 0..6 {
        if p.join("admin").join("backend").exists() && p.join("admin-desktop").exists() {
            return Some(p);
        }
        p = p.parent()?.to_path_buf();
    }
    None
}

/// 查找 venv Python 可执行文件
fn find_python_bin(project_root: &std::path::Path) -> String {
    // 优先使用 admin/backend/.venv
    let venv_python = project_root
        .join("admin")
        .join("backend")
        .join(".venv")
        .join("Scripts")
        .join("python.exe");
    if venv_python.exists() {
        return venv_python.to_string_lossy().to_string();
    }
    // 回退到系统 Python
    "python".to_string()
}

/// 从 admin/backend/.env 读取管理员凭据
fn read_env_credentials(project_root: &std::path::Path) -> (String, String) {
    let env_path = project_root.join("admin").join("backend").join(".env");
    let mut username = "admin".to_string();
    let mut password = "admin123".to_string();
    if let Ok(content) = std::fs::read_to_string(&env_path) {
        for line in content.lines() {
            let line = line.trim();
            if let Some(val) = line.strip_prefix("LUCHUAN_ADMIN_USERNAME=") {
                username = val.to_string();
            }
            if let Some(val) = line.strip_prefix("LUCHUAN_ADMIN_PASSWORD=") {
                password = val.to_string();
            }
        }
    }
    (username, password)
}

/// 启动 Python 后端子进程
fn spawn_backend(port: u16, project_root: &str) -> Option<Child> {
    let is_dev = cfg!(debug_assertions);
    let project_root_path = PathBuf::from(project_root);

    if is_dev {
        // 开发模式：运行 admin-desktop/src-backend/main.py
        let sidecar_entry = project_root_path
            .join("admin-desktop")
            .join("src-backend")
            .join("main.py");

        if !sidecar_entry.exists() {
            eprintln!("错误：找不到 sidecar 入口文件: {:?}", sidecar_entry);
            return None;
        }

        let python_bin = find_python_bin(&project_root_path);

        Command::new(&python_bin)
            .arg(&sidecar_entry)
            .arg("--port")
            .arg(port.to_string())
            .arg("--project-root")
            .arg(project_root)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .ok()
    } else {
        // 生产模式：使用打包后的 sidecar 二进制
        let sidecar_name = if cfg!(target_os = "windows") {
            "admin-backend.exe"
        } else {
            "admin-backend"
        };

        let sidecar_path = env::current_exe()
            .ok()
            .and_then(|exe| {
                let dir = exe.parent()?;
                Some(dir.join("resources").join(sidecar_name))
            })
            .unwrap_or_else(|| std::path::PathBuf::from(sidecar_name));

        Command::new(&sidecar_path)
            .arg("--port")
            .arg(port.to_string())
            .arg("--project-root")
            .arg(project_root)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .ok()
    }
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
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            let window = app.get_webview_window("main").unwrap();

            // 查找可用端口
            let port = find_free_port();

            // 确定项目根目录
            let project_root = if cfg!(debug_assertions) {
                find_project_root()
                    .map(|p| p.to_string_lossy().to_string())
                    .unwrap_or_else(|| ".".to_string())
            } else {
                env::current_exe()
                    .ok()
                    .and_then(|exe| exe.parent().map(|p| p.to_string_lossy().to_string()))
                    .unwrap_or_else(|| ".".to_string())
            };

            // 启动 Python 后端
            if let Some(child) = spawn_backend(port, &project_root) {
                let state: State<BackendProcess> = app.state();
                *state.0.lock().unwrap() = Some(child);

                let backend_ready = wait_for_backend(port);

                if backend_ready {
                    let (admin_user, admin_pass) = read_env_credentials(&PathBuf::from(&project_root));
                    window.eval(&format!(
                        "window.__BACKEND_PORT__ = {}; window.__BACKEND_READY__ = true; window.__ADMIN_USERNAME__ = '{}'; window.__ADMIN_PASSWORD__ = '{}';",
                        port, admin_user, admin_pass
                    )).ok();
                } else {
                    eprintln!("警告：后端未在超时时间内就绪");
                    window.eval(&format!(
                        "window.__BACKEND_PORT__ = {}; window.__BACKEND_READY__ = false;",
                        port
                    )).ok();
                }
            } else {
                eprintln!("错误：无法启动后端进程");
                window.eval("window.__BACKEND_READY__ = false;").ok();
            }

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let state = window.app_handle().state::<BackendProcess>();
                let child = state.0.lock().unwrap().take();
                if let Some(mut child) = child {
                    let _ = child.kill();
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            minimize_window,
            maximize_window,
            close_window,
            is_maximized,
        ])
        .run(tauri::generate_context!())
        .expect("运行 Tauri 应用时出错");
}
