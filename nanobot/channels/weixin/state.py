"""WeChat-owned persisted login-state detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nanobot.channels.contracts import channel_field_value
from nanobot.channels.weixin.instances import DEFAULT_INSTANCE_ID, managed_weixin_instance_specs
from nanobot.config.paths import get_config_path


def local_state_present(section: Any) -> bool:
    """Return whether any configured account has saved local login state."""
    configured_dir = channel_field_value(section, "stateDir")
    base_state_dir = (
        Path(str(configured_dir)).expanduser()
        if configured_dir
        else get_config_path().parent / "weixin"
    )
    for spec in managed_weixin_instance_specs(section, enabled_only=False):
        config = spec.config
        account_dir = (
            Path(str(config.get("stateDir") or config.get("state_dir") or "")).expanduser()
            if config.get("stateDir") or config.get("state_dir")
            else base_state_dir
        )
        account_id = str(config.get("account_id") or config.get("accountId") or DEFAULT_INSTANCE_ID).strip()
        safe_id = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in account_id) or DEFAULT_INSTANCE_ID
        state_file = account_dir / ("account.json" if safe_id == DEFAULT_INSTANCE_ID else f"account_{safe_id}.json")
        try:
            payload = json.loads(state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        if bool(str(payload.get("token") or "").strip()):
            return True
    return False


__all__ = ["local_state_present"]
