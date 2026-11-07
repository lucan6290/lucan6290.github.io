#[cfg(test)]
mod tests {
    use super::update_enabled;
    use serde_json::json;

    #[test]
    fn update_requires_a_windows_release_and_complete_pinned_config() {
        let release = json!({
            "endpoints": ["https://updates.example.test/latest.json"],
            "pubkey": "test public key",
            "requireSignedVersion": true,
        });
        assert!(update_enabled(Some(&release), true));
        assert!(!update_enabled(Some(&release), false));
        assert!(!update_enabled(None, true));
        assert!(!update_enabled(Some(&json!({})), true));
        let mut unsafe_endpoint = release.clone();
        unsafe_endpoint["endpoints"] = json!(["http://updates.example.test/latest.json"]);
        assert!(!update_enabled(Some(&unsafe_endpoint), true));
        let mut unsigned_version = release;
        unsigned_version["requireSignedVersion"] = json!(false);
        assert!(!update_enabled(Some(&unsigned_version), true));
    }
}
use serde::Serialize;
use serde_json::Value;

fn update_enabled(config: Option<&Value>, windows_release: bool) -> bool {
    let Some(config) = config.filter(|_| windows_release) else {
        return false;
    };
    config["requireSignedVersion"].as_bool() == Some(true)
        && config["pubkey"]
            .as_str()
            .is_some_and(|key| !key.trim().is_empty())
        && config["endpoints"].as_array().is_some_and(|endpoints| {
            !endpoints.is_empty()
                && endpoints.iter().all(|endpoint| {
                    endpoint
                        .as_str()
                        .and_then(|value| tauri::Url::parse(value).ok())
                        .is_some_and(|url| {
                            url.scheme() == "https"
                                && url.username().is_empty()
                                && url.password().is_none()
                        })
                })
        })
}

#[derive(Serialize)]
pub(crate) struct UpdateStatus {
    enabled: bool,
    version: String,
}

#[tauri::command]
pub(crate) fn get_desktop_update_status(app: tauri::AppHandle) -> UpdateStatus {
    UpdateStatus {
        enabled: update_enabled(
            app.config().plugins.0.get("updater"),
            cfg!(all(windows, not(debug_assertions))),
        ),
        version: app.package_info().version.to_string(),
    }
}

#[cfg(windows)]
pub(crate) fn configure(app: &mut tauri::App) -> tauri::Result<()> {
    use tauri::Manager;
    if get_desktop_update_status(app.handle().clone()).enabled {
        app.handle()
            .plugin(tauri_plugin_updater::Builder::new().build())?;
        app.manage(windows::PendingUpdate::default());
    }
    Ok(())
}

#[cfg(windows)]
pub(crate) mod windows {
    use std::time::Duration;
    use tauri::Manager;
    use tauri_plugin_updater::{Update, UpdaterExt};
    use tokio::sync::Mutex;

    #[derive(Default)]
    pub(crate) struct PendingUpdate(Mutex<Option<(Update, Option<Vec<u8>>)>>);

    fn pending(app: &tauri::AppHandle) -> Result<tauri::State<'_, PendingUpdate>, String> {
        app.try_state()
            .ok_or_else(|| "此安装包未配置更新渠道".to_owned())
    }

    #[tauri::command]
    pub(crate) async fn check_desktop_update(
        app: tauri::AppHandle,
    ) -> Result<Option<String>, String> {
        let pending = pending(&app)?;
        let mut candidate = pending.0.try_lock().map_err(|_| "已有更新操作正在执行")?;
        *candidate = None;
        let update = app
            .updater_builder()
            // ShellExecuteW can fail after this hook. Keep the window alive so it can report
            // the error. Windows closes our kill-on-close Jobs when the updater exits.
            .on_before_exit(|| {})
            .timeout(Duration::from_secs(180))
            .build()
            .map_err(|error| error.to_string())?
            .check()
            .await
            .map_err(|error| error.to_string())?;
        let version = update.as_ref().map(|update| update.version.clone());
        *candidate = update.map(|update| (update, None));
        Ok(version)
    }

    #[tauri::command]
    pub(crate) async fn download_desktop_update(
        app: tauri::AppHandle,
        version: String,
    ) -> Result<(), String> {
        let pending = pending(&app)?;
        let mut candidate = pending.0.try_lock().map_err(|_| "已有更新操作正在执行")?;
        let (update, bytes) = candidate
            .as_mut()
            .filter(|(update, _)| update.version == version)
            .ok_or("更新信息已过期，请重新检查")?;
        *bytes = Some(
            update
                .download(|_, _| {}, || {})
                .await
                .map_err(|error| error.to_string())?,
        );
        Ok(())
    }

    #[tauri::command]
    pub(crate) async fn install_desktop_update(
        app: tauri::AppHandle,
        version: String,
    ) -> Result<(), String> {
        let pending = pending(&app)?;
        let candidate = pending.0.try_lock().map_err(|_| "已有更新操作正在执行")?;
        let (update, bytes) = candidate
            .as_ref()
            .filter(|(update, _)| update.version == version)
            .ok_or("更新信息已过期，请重新检查")?;
        update
            .install(bytes.as_ref().ok_or("请先下载更新")?)
            .map_err(|error| error.to_string())
    }
}
