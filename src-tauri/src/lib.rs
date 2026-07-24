use serde::Serialize;
use serde_json::{json, Value};
use std::fs;
use std::io::{BufRead, BufReader, Read};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use tauri::{Emitter, Manager};

const BRIDGE_PROGRESS_EVENT: &str = "bridge-progress";
static NEXT_JOB_ID: AtomicU64 = AtomicU64::new(1);

const EMBEDDED_FILES: &[(&str, &[u8])] = &[
    (
        "tools/launcher_bridge.py",
        include_bytes!("../../tools/launcher_bridge.py"),
    ),
    (
        "patch_windowsapps_json_only.py",
        include_bytes!("../../patch_windowsapps_json_only.py"),
    ),
    (
        "patch_chunks_zh_cn.py",
        include_bytes!("../../patch_chunks_zh_cn.py"),
    ),
    (
        "restore_claude_zh_cn_windowsapps.py",
        include_bytes!("../../restore_claude_zh_cn_windowsapps.py"),
    ),
    (
        "best_effort_io.py",
        include_bytes!("../../best_effort_io.py"),
    ),
    (
        "resources/desktop-zh-CN.json",
        include_bytes!("../../resources/desktop-zh-CN.json"),
    ),
    (
        "resources/frontend-zh-CN.json",
        include_bytes!("../../resources/frontend-zh-CN.json"),
    ),
    (
        "resources/statsig-zh-CN.json",
        include_bytes!("../../resources/statsig-zh-CN.json"),
    ),
];

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct BridgeError {
    ok: bool,
    state: String,
    message: String,
    log: String,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct ActionJob {
    job_id: String,
}

#[cfg(windows)]
fn configure_hidden(command: &mut Command) {
    use std::os::windows::process::CommandExt;
    command.creation_flags(0x0800_0000);
}

#[cfg(not(windows))]
fn configure_hidden(_command: &mut Command) {}

fn materialize_embedded_files(root: &Path) -> Result<(), String> {
    for (relative_path, contents) in EMBEDDED_FILES {
        let destination = root.join(relative_path);
        if fs::read(&destination)
            .map(|current| current == *contents)
            .unwrap_or(false)
        {
            continue;
        }
        if let Some(parent) = destination.parent() {
            fs::create_dir_all(parent).map_err(|err| {
                format!(
                    "failed to create runtime directory {}: {err}",
                    parent.display()
                )
            })?;
        }
        fs::write(&destination, contents).map_err(|err| {
            format!(
                "failed to write runtime resource {}: {err}",
                destination.display()
            )
        })?;
    }
    Ok(())
}

fn project_root(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    let development_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_else(|| PathBuf::from("."));
    if cfg!(debug_assertions)
        && development_root
            .join("tools")
            .join("launcher_bridge.py")
            .exists()
    {
        return Ok(development_root);
    }

    let root = app
        .path()
        .app_local_data_dir()
        .map_err(|err| format!("failed to resolve app data directory: {err}"))?
        .join("runtime")
        .join(env!("CARGO_PKG_VERSION"));
    materialize_embedded_files(&root)?;
    Ok(root)
}

fn python_command() -> Command {
    let mut candidates = vec!["python".to_string(), "py".to_string()];
    if let Ok(custom) = std::env::var("CLAUDE_ZH_PYTHON") {
        candidates.insert(0, custom);
    }

    for name in candidates {
        let mut probe = Command::new(&name);
        configure_hidden(&mut probe);
        probe.arg("--version");
        if probe.output().map(|o| o.status.success()).unwrap_or(false) {
            let mut command = Command::new(name);
            configure_hidden(&mut command);
            return command;
        }
    }
    let mut command = Command::new("python");
    configure_hidden(&mut command);
    command
}

fn bridge_script(root: &Path) -> PathBuf {
    let primary = root.join("tools").join("launcher_bridge.py");
    if primary.exists() {
        return primary;
    }
    root.join("launcher_bridge.py")
}

fn bridge_args(command: &str, target: Option<String>, app_dir: Option<String>) -> Vec<String> {
    let mut args = vec![
        command.to_string(),
        "--target".to_string(),
        target.unwrap_or_else(|| "auto".into()),
    ];
    if let Some(path) = app_dir.filter(|path| !path.trim().is_empty()) {
        args.push("--app-dir".to_string());
        args.push(path);
    }
    args
}

fn run_bridge(app: &tauri::AppHandle, args: &[String]) -> Result<Value, String> {
    let root = project_root(app)?;
    let script = bridge_script(&root);
    if !script.exists() {
        return Err(format!(
            "launcher_bridge.py not found under {}",
            root.display()
        ));
    }

    let mut command = python_command();
    command.arg("-B").arg(&script);
    for arg in args {
        command.arg(arg);
    }
    command
        .current_dir(&root)
        .env("PYTHONUTF8", "1")
        .env("PYTHONIOENCODING", "utf-8");

    let output = command
        .output()
        .map_err(|err| format!("failed to spawn python bridge: {err}"))?;

    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();

    if stdout.is_empty() {
        return Err(if stderr.is_empty() {
            format!("bridge returned empty output (exit {})", output.status)
        } else {
            stderr
        });
    }

    serde_json::from_str::<Value>(&stdout)
        .map_err(|err| format!("invalid bridge json: {err}; stdout={stdout}; stderr={stderr}"))
}

fn emit_bridge_event(app: &tauri::AppHandle, job_id: &str, action: &str, mut payload: Value) {
    if let Some(object) = payload.as_object_mut() {
        object.insert("jobId".into(), Value::String(job_id.to_string()));
        object.insert("action".into(), Value::String(action.to_string()));
    } else {
        let text = payload.to_string();
        payload = json!({
            "type": "progress",
            "jobId": job_id,
            "action": action,
            "phase": "output",
            "progress": 0,
            "message": text.clone(),
            "log": text,
            "done": false
        });
    }
    let _ = app.emit(BRIDGE_PROGRESS_EVENT, payload);
}

fn emit_bridge_error(app: &tauri::AppHandle, job_id: &str, action: &str, message: String) {
    let result = error_payload(message.clone());
    emit_bridge_event(
        app,
        job_id,
        action,
        json!({
            "type": "result",
            "phase": "error",
            "progress": 100,
            "message": message.clone(),
            "log": message,
            "done": true,
            "ok": false,
            "result": result
        }),
    );
}

fn run_bridge_stream(app: tauri::AppHandle, job_id: String, action: String, mut args: Vec<String>) {
    let root = match project_root(&app) {
        Ok(root) => root,
        Err(err) => {
            emit_bridge_error(&app, &job_id, &action, err);
            return;
        }
    };
    let script = bridge_script(&root);
    if !script.exists() {
        emit_bridge_error(
            &app,
            &job_id,
            &action,
            format!("launcher_bridge.py not found under {}", root.display()),
        );
        return;
    }

    args.push("--stream".to_string());
    let mut command = python_command();
    command.arg("-B").arg(&script);
    for arg in &args {
        command.arg(arg);
    }
    command
        .current_dir(&root)
        .env("PYTHONUTF8", "1")
        .env("PYTHONIOENCODING", "utf-8")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    emit_bridge_event(
        &app,
        &job_id,
        &action,
        json!({
            "type": "progress",
            "phase": "starting",
            "progress": 1,
            "message": "后台任务已启动",
            "log": "[后台] Python 补丁任务已启动。",
            "done": false
        }),
    );

    let mut child = match command.spawn() {
        Ok(child) => child,
        Err(err) => {
            emit_bridge_error(
                &app,
                &job_id,
                &action,
                format!("failed to spawn python bridge: {err}"),
            );
            return;
        }
    };

    let stderr_task = child.stderr.take().map(|stderr| {
        std::thread::spawn(move || {
            let mut content = String::new();
            let _ = BufReader::new(stderr).read_to_string(&mut content);
            content
        })
    });

    let Some(stdout) = child.stdout.take() else {
        emit_bridge_error(
            &app,
            &job_id,
            &action,
            "python bridge stdout was unavailable".to_string(),
        );
        let _ = child.kill();
        return;
    };

    let mut saw_result = false;
    let mut last_progress = 1_u64;
    for line in BufReader::new(stdout).lines() {
        let line = match line {
            Ok(line) => line,
            Err(err) => {
                emit_bridge_event(
                    &app,
                    &job_id,
                    &action,
                    json!({
                        "type": "progress",
                        "phase": "output",
                        "progress": last_progress,
                        "message": format!("读取后台输出失败: {err}"),
                        "done": false
                    }),
                );
                continue;
            }
        };
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }

        match serde_json::from_str::<Value>(trimmed) {
            Ok(mut payload) => {
                if let Some(progress) = payload.get("progress").and_then(Value::as_u64) {
                    last_progress = progress.min(100);
                }
                let is_result = payload.get("type").and_then(Value::as_str) == Some("result");
                if is_result {
                    saw_result = true;
                    let result = payload.get("result").cloned().unwrap_or(Value::Null);
                    let ok = result.get("ok").and_then(Value::as_bool).unwrap_or(false);
                    let message = result
                        .get("message")
                        .and_then(Value::as_str)
                        .unwrap_or(if ok {
                            "后台任务已完成"
                        } else {
                            "后台任务失败"
                        })
                        .to_string();
                    let log = result
                        .get("log")
                        .and_then(Value::as_str)
                        .unwrap_or(&message)
                        .to_string();
                    if let Some(object) = payload.as_object_mut() {
                        object.insert(
                            "phase".into(),
                            Value::String(if ok { "complete" } else { "error" }.into()),
                        );
                        object.insert("progress".into(), Value::from(100));
                        object.insert("message".into(), Value::String(message));
                        object.insert("log".into(), Value::String(log));
                        object.insert("done".into(), Value::Bool(true));
                        object.insert("ok".into(), Value::Bool(ok));
                    }
                } else if let Some(object) = payload.as_object_mut() {
                    object.insert("done".into(), Value::Bool(false));
                }
                emit_bridge_event(&app, &job_id, &action, payload);
            }
            Err(_) => emit_bridge_event(
                &app,
                &job_id,
                &action,
                json!({
                    "type": "progress",
                    "phase": "output",
                    "progress": last_progress,
                    "message": trimmed,
                    "log": trimmed,
                    "done": false
                }),
            ),
        }
    }

    let status = child.wait();
    let stderr = stderr_task
        .and_then(|task| task.join().ok())
        .unwrap_or_default()
        .trim()
        .to_string();

    if saw_result {
        return;
    }

    let message = match status {
        Ok(status) if stderr.is_empty() => {
            format!("bridge completed without a result (exit {status})")
        }
        Ok(_) => stderr,
        Err(err) => format!("failed to wait for python bridge: {err}"),
    };
    emit_bridge_error(&app, &job_id, &action, message);
}

#[cfg(test)]
mod tests {
    use super::{materialize_embedded_files, EMBEDDED_FILES};
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    #[test]
    fn portable_payload_contains_every_runtime_file() {
        let paths: Vec<&str> = EMBEDDED_FILES.iter().map(|(path, _)| *path).collect();
        for expected in [
            "tools/launcher_bridge.py",
            "patch_windowsapps_json_only.py",
            "patch_chunks_zh_cn.py",
            "restore_claude_zh_cn_windowsapps.py",
            "best_effort_io.py",
            "resources/desktop-zh-CN.json",
            "resources/frontend-zh-CN.json",
            "resources/statsig-zh-CN.json",
        ] {
            assert!(paths.contains(&expected));
        }
        assert!(EMBEDDED_FILES
            .iter()
            .all(|(_, contents)| !contents.is_empty()));

        let unique = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system clock must be after Unix epoch")
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "claude-desktop-zh-cn-portable-test-{}-{unique}",
            std::process::id()
        ));
        materialize_embedded_files(&root).expect("embedded files must materialize");
        for (relative_path, expected) in EMBEDDED_FILES {
            let actual =
                fs::read(root.join(relative_path)).expect("materialized file must be readable");
            assert_eq!(actual, *expected);
        }
        fs::remove_dir_all(root).expect("portable test directory must be removable");
    }
}

fn error_payload(message: String) -> Value {
    serde_json::to_value(BridgeError {
        ok: false,
        state: "error".into(),
        message: message.clone(),
        log: message,
    })
    .unwrap_or_else(|_| Value::Null)
}

#[tauri::command]
fn start_action(
    app: tauri::AppHandle,
    action: String,
    target: Option<String>,
    app_dir: Option<String>,
) -> Result<ActionJob, String> {
    let bridge_action = match action.as_str() {
        "install" => "install",
        "restore" => "restore",
        "open" => "open",
        "check-update" => "check-update",
        _ => return Err(format!("unsupported background action: {action}")),
    };
    let job_id = format!("job-{}", NEXT_JOB_ID.fetch_add(1, Ordering::Relaxed));
    let args = bridge_args(bridge_action, target, app_dir);
    let worker_app = app.clone();
    let worker_job_id = job_id.clone();
    let worker_action = action.clone();
    std::thread::spawn(move || {
        run_bridge_stream(worker_app, worker_job_id, worker_action, args);
    });
    Ok(ActionJob { job_id })
}

#[tauri::command]
fn get_status(
    app: tauri::AppHandle,
    target: Option<String>,
    app_dir: Option<String>,
) -> Result<Value, String> {
    let args = bridge_args("status", target, app_dir);
    match run_bridge(&app, &args) {
        Ok(value) => {
            if let Some(status) = value.get("status") {
                Ok(status.clone())
            } else {
                Ok(value)
            }
        }
        Err(err) => Err(err),
    }
}

#[tauri::command]
fn install_patch(
    app: tauri::AppHandle,
    target: Option<String>,
    app_dir: Option<String>,
) -> Result<Value, String> {
    let args = bridge_args("install", target, app_dir);
    match run_bridge(&app, &args) {
        Ok(value) => Ok(value),
        Err(err) => Ok(error_payload(err)),
    }
}

#[tauri::command]
fn restore_patch(
    app: tauri::AppHandle,
    target: Option<String>,
    app_dir: Option<String>,
) -> Result<Value, String> {
    let args = bridge_args("restore", target, app_dir);
    match run_bridge(&app, &args) {
        Ok(value) => Ok(value),
        Err(err) => Ok(error_payload(err)),
    }
}

#[tauri::command]
fn open_claude(
    app: tauri::AppHandle,
    target: Option<String>,
    app_dir: Option<String>,
) -> Result<Value, String> {
    let args = bridge_args("open", target, app_dir);
    match run_bridge(&app, &args) {
        Ok(value) => Ok(value),
        Err(err) => Ok(error_payload(err)),
    }
}

#[tauri::command]
fn check_update(
    app: tauri::AppHandle,
    target: Option<String>,
    app_dir: Option<String>,
) -> Result<Value, String> {
    let args = bridge_args("check-update", target, app_dir);
    match run_bridge(&app, &args) {
        Ok(value) => Ok(value),
        Err(err) => Ok(error_payload(err)),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            get_status,
            start_action,
            install_patch,
            restore_patch,
            open_claude,
            check_update
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
