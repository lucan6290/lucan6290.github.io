use super::*;

fn target(root: &Path, state_dir: PathBuf, executable: Option<PathBuf>) -> ActiveWorkspace {
    ActiveWorkspace {
        root: root.to_path_buf(),
        state_dir,
        executable,
    }
}

fn connection(target: &ActiveWorkspace) -> BackendConnection {
    BackendConnection {
        base_url: BASE_URL.into(),
        token: "workspace-test-token".into(),
        content_root: target
            .root
            .join("frontend/content")
            .to_string_lossy()
            .into_owned(),
    }
}

#[cfg(windows)]
fn own_backend_fixture(runtime: &BackendRuntime) -> u32 {
    let mut command = Command::new(env::current_exe().unwrap());
    command
        .args(["--exact", "tests::process_tree_child", "--ignored"])
        .env("LUCHUAN_PROCESS_TEST_LEAF", "1")
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    let child = OwnedProcess::spawn(&mut command).unwrap();
    let pid = child.child.id();
    *runtime.process.lock().unwrap() = Some(child);
    pid
}

#[cfg(windows)]
#[test]
fn invalid_target_keeps_owned_backend_running() {
    let old = crate::tests::fixture("switch-invalid-old");
    let next = crate::tests::fixture("switch-invalid-next");
    let current = target(&old, old.join("state"), None);
    let candidate = target(&next, next.join("state"), None);
    let runtime = BackendRuntime::default();
    let pid = own_backend_fixture(&runtime);

    let result = replace_backend(&runtime, &current, &candidate, |_, _| {
        panic!("无后端入口的目标不得开始连接")
    });
    assert!(result.err().unwrap().contains("内容后端入口"));
    {
        let mut process = runtime.process.lock().unwrap();
        let process = process.as_mut().unwrap();
        assert_eq!(process.child.id(), pid);
        assert!(process.child.try_wait().unwrap().is_none());
    }
    drop(runtime);
    fs::remove_dir_all(old).unwrap();
    fs::remove_dir_all(next).unwrap();
}

#[cfg(windows)]
#[test]
fn persistence_failure_restores_owned_backend_and_keeps_previous_workspace() {
    let old = crate::tests::fixture("switch-rollback-old");
    let next = crate::tests::fixture("switch-rollback-next");
    let executable = env::current_exe().unwrap();
    let current = target(&old, old.join("state"), Some(executable.clone()));
    let candidate_state = next.join("state");
    fs::write(&candidate_state, "not a directory").unwrap();
    let candidate = target(&next, candidate_state, Some(executable));
    let state_file = current.state_dir.join("workspace.json");
    remember_workspace(&state_file, &old).unwrap();
    let runtime = BackendRuntime::default();
    own_backend_fixture(&runtime);
    let mut attempted = Vec::new();

    let result = replace_backend(&runtime, &current, &candidate, |target, stopped| {
        assert!(stopped);
        assert!(runtime.process.lock().unwrap().is_none());
        let pid = own_backend_fixture(&runtime);
        attempted.push((target.root.clone(), pid));
        Ok(connection(target))
    });

    assert!(result.err().unwrap().contains("无法保存博客目录"));
    assert_eq!(
        attempted.iter().map(|(root, _)| root).collect::<Vec<_>>(),
        [&next, &old]
    );
    assert_ne!(attempted[0].1, attempted[1].1);
    assert_eq!(
        runtime.process.lock().unwrap().as_ref().unwrap().child.id(),
        attempted[1].1
    );
    assert_eq!(
        installed_workspace(&state_file, None).unwrap(),
        Some(old.clone())
    );
    drop(runtime);
    fs::remove_dir_all(old).unwrap();
    fs::remove_dir_all(next).unwrap();
}

#[test]
fn failed_switch_with_external_backend_does_not_attempt_rollback() {
    let old = crate::tests::fixture("switch-external-old");
    let next = crate::tests::fixture("switch-external-next");
    let current = target(&old, old.join("state"), None);
    let candidate = target(&next, next.join("state"), Some(env::current_exe().unwrap()));
    let runtime = BackendRuntime::default();
    let mut attempts = 0;

    let result = replace_backend(&runtime, &current, &candidate, |target, stopped| {
        assert_eq!(target.root, next);
        assert!(!stopped);
        attempts += 1;
        Err("18000 端口被外部服务占用".into())
    });

    assert!(result.err().unwrap().contains("外部服务占用"));
    assert_eq!(attempts, 1);
    assert!(!candidate.state_dir.join("workspace.json").exists());
    fs::remove_dir_all(old).unwrap();
    fs::remove_dir_all(next).unwrap();
}

#[test]
fn success_records_candidate_workspace_after_connection() {
    let old = crate::tests::fixture("switch-success-old");
    let next = crate::tests::fixture("switch-success-next");
    let state_dir = old.join("state");
    let executable = env::current_exe().unwrap();
    let current = target(&old, state_dir.clone(), Some(executable.clone()));
    let candidate = target(&next, state_dir.clone(), Some(executable));
    let state_file = state_dir.join("workspace.json");
    remember_workspace(&state_file, &old).unwrap();
    let runtime = BackendRuntime::default();

    let result = replace_backend(&runtime, &current, &candidate, |target, _| {
        assert_eq!(
            installed_workspace(&state_file, None).unwrap(),
            Some(old.clone())
        );
        Ok(connection(target))
    });

    assert_eq!(
        result.unwrap().content_root,
        connection(&candidate).content_root
    );
    assert_eq!(
        installed_workspace(&state_file, None).unwrap(),
        Some(next.clone())
    );
    fs::remove_dir_all(old).unwrap();
    fs::remove_dir_all(next).unwrap();
}

#[cfg(windows)]
#[test]
fn reselecting_current_workspace_keeps_the_owned_backend() {
    let root = crate::tests::fixture("switch-same");
    let current = target(&root, root.join("state"), None);
    let runtime = BackendRuntime::default();
    let pid = own_backend_fixture(&runtime);

    let result = replace_backend(&runtime, &current, &current, |target, stopped| {
        assert!(!stopped);
        let process = runtime.process.lock().unwrap();
        assert_eq!(process.as_ref().unwrap().child.id(), pid);
        Ok(connection(target))
    });

    assert!(result.is_ok());
    drop(runtime);
    fs::remove_dir_all(root).unwrap();
}
