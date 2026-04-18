"""Sandbox backends for shell command execution.

To add a new backend, implement a function with the signature:
    _wrap_<name>(command: str, workspace: str, cwd: str) -> str
and register it in _BACKENDS below.
"""

import json
import os
import shlex
from pathlib import Path

from nanobot.config.paths import get_media_dir


def _load_allowed_env_keys(config_path: Path) -> list[str]:
    """Load tools.exec.allowedEnvKeys from config.json, if available."""
    try:
        with config_path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []

    tools = data.get("tools")
    if not isinstance(tools, dict):
        return []
    exec_cfg = tools.get("exec")
    if not isinstance(exec_cfg, dict):
        return []

    raw_keys = exec_cfg.get("allowedEnvKeys", exec_cfg.get("allowed_env_keys"))
    if not isinstance(raw_keys, list):
        return []
    return [k for k in raw_keys if isinstance(k, str) and k]


def _bwrap(command: str, workspace: str, cwd: str) -> str:
    """Wrap command in a bubblewrap sandbox (requires bwrap in container).

    Only the workspace is bind-mounted read-write; its parent dir (which holds
    config.json) is hidden behind a fresh tmpfs.  The media directory is
    bind-mounted read-only so exec commands can read uploaded attachments.
    """
    ws = Path(workspace).resolve()
    media = get_media_dir().resolve()
    allowed_env_keys = [
        "HOME",
        "LANG",
        "NVM_BIN",
        "NVM_DIR",
        "NVM_INC",
        "TERM",
        *_load_allowed_env_keys(ws.parent / "config.json"),
    ]

    try:
        sandbox_cwd = str(ws / Path(cwd).resolve().relative_to(ws))
    except ValueError:
        sandbox_cwd = str(ws)

    required = ["/usr"]
    optional = [
        "/bin",
        "/lib",
        "/lib64",
        "/etc/alternatives",
        "/etc/ssl/certs",
        "/etc/resolv.conf",
        "/etc/ld.so.cache",
        "/root/.local",
    ]
    dependencies = ["/root/.nvm"]

    args = ["bwrap", "--new-session", "--die-with-parent", "--share-net", "--clearenv"]
    for p in required:
        args += ["--ro-bind", p, p]
    for p in optional:
        args += ["--ro-bind-try", p, p]
    for p in dependencies:
        args += ["--bind-try", p, p]
    for key in allowed_env_keys:
        value = os.environ.get(key)
        if value is not None:
            args += ["--setenv", key, value]
    args += [
        "--setenv",
        "VIRTUAL_ENV",
        str(ws / ".venv"),
        "--setenv",
        "PATH",
        f"{str(ws / '.venv' / 'bin')}:{os.environ.get('PATH')}",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        str(ws.parent),  # mask config dir
        "--dir",
        str(ws),  # recreate workspace mount point
        "--bind",
        str(ws),
        str(ws),
        "--ro-bind-try",
        str(media),
        str(media),  # read-only access to media
        "--chdir",
        sandbox_cwd,
        "--",
        "sh",
        "-c",
        command,
    ]
    return shlex.join(args)


_BACKENDS = {"bwrap": _bwrap}


def wrap_command(sandbox: str, command: str, workspace: str, cwd: str) -> str:
    """Wrap *command* using the named sandbox backend."""
    if backend := _BACKENDS.get(sandbox):
        return backend(command, workspace, cwd)
    raise ValueError(f"Unknown sandbox backend {sandbox!r}. Available: {list(_BACKENDS)}")
