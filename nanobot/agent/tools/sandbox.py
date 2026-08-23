"""Sandbox backends for shell command execution.

To add a new backend, implement a function with the signature:
    _wrap_<name>(command: str, workspace: str, cwd: str) -> str
and register it in _BACKENDS below.
"""

import json
import os
import shlex
from pathlib import Path
from typing import Iterable

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


def _normalize_bind_paths(
    paths: Iterable[str] | None,
    *,
    workspace: Path | None = None,
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in paths or []:
        value = str(raw).strip()
        if not value:
            continue
        path = Path(os.path.expandvars(value)).expanduser()
        if not path.is_absolute():
            continue
        resolved_path = path.resolve(strict=False)
        if workspace is not None:
            try:
                workspace.relative_to(resolved_path)
            except ValueError:
                pass
            else:
                # A later bind of the workspace or one of its parents could
                # cover the tmpfs that hides the config directory.
                continue
        resolved = str(resolved_path)
        if resolved in seen:
            continue
        seen.add(resolved)
        out.append(resolved)
    return out


def _bwrap(
    command: str,
    workspace: str,
    cwd: str,
    *,
    sandbox_ro_binds: Iterable[str] | None = None,
    sandbox_rw_binds: Iterable[str] | None = None,
) -> str:
    """Wrap command in a bubblewrap sandbox (requires bwrap in container).

    Only the workspace is bind-mounted read-write; its parent dir (which holds
    config.json) is hidden behind a fresh tmpfs.  The media directory is
    bind-mounted read-only so exec commands can read uploaded attachments.
    """
    ws = Path(workspace).resolve()
    media = get_media_dir().resolve()
    allowed_env_keys = [
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
        "/etc/pki/tls/certs",
        "/etc/pki/ca-trust",
        "/etc/crypto-policies",
        "/etc/resolv.conf",
        "/etc/ld.so.cache",
        "/root/.local",
    ]
    dependencies = ["/root/.nvm"]

    args = [
        "bwrap",
        "--new-session",
        "--die-with-parent",
        "--share-net",
        "--clearenv",
        "--setenv",
        "HOME",
        str(ws),
    ]
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
        f"{str(ws / '.venv' / 'bin')}:{os.environ.get('PATH', '')}",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        str(ws.parent),
        "--dir",
        str(ws),
        "--bind",
        str(ws),
        str(ws),
        "--ro-bind-try",
        str(media),
        str(media),
    ]
    for p in _normalize_bind_paths(sandbox_ro_binds, workspace=ws):
        args += ["--ro-bind-try", p, p]
    for p in _normalize_bind_paths(sandbox_rw_binds, workspace=ws):
        args += ["--bind-try", p, p]
    args += ["--chdir", sandbox_cwd, "--", "sh", "-c", command]
    return shlex.join(args)


_BACKENDS = {"bwrap": _bwrap}


def wrap_command(
    sandbox: str,
    command: str,
    workspace: str,
    cwd: str,
    *,
    sandbox_ro_binds: Iterable[str] | None = None,
    sandbox_rw_binds: Iterable[str] | None = None,
) -> str:
    """Wrap *command* using the named sandbox backend."""
    if backend := _BACKENDS.get(sandbox):
        return backend(
            command,
            workspace,
            cwd,
            sandbox_ro_binds=sandbox_ro_binds,
            sandbox_rw_binds=sandbox_rw_binds,
        )
    raise ValueError(f"Unknown sandbox backend {sandbox!r}. Available: {list(_BACKENDS)}")
