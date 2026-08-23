"""WeChat-owned helpers for persisted multi-account configuration.

The public persisted form stays compatible with the legacy ``accounts`` shape
(main kept `accounts` for multi-account setups) while the gateway expands it
through the generic channel management contract. Accounts are independent
working copies of WeixinConfig; ``accounts`` is only a config envelope and is
never passed to the runtime.
"""

from __future__ import annotations

import re
from typing import Any, cast

from loguru import logger

from nanobot.channels.contracts import ChannelInstanceSpec, ChannelManagementSpec

DEFAULT_INSTANCE_ID = "default"
_INSTANCE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")

_DEFAULT_CONFIG: dict[str, Any] = {
    "enabled": False,
    "allowFrom": [],
    "baseUrl": "https://ilinkai.weixin.qq.com",
    "cdnBaseUrl": "https://novac2c.cdn.weixin.qq.com/c2c",
    "routeTag": None,
    "token": "",
    "stateDir": "",
    "accountId": DEFAULT_INSTANCE_ID,
    "pollTimeout": 35,
    "sendProgress": False,
    "sendToolHints": False,
    "replyProgressMessages": False,
    "replyProgressMaxMessages": 2,
    "contextMessageBudget": 8,
    "streaming": True,
    "blockStreaming": False,
    "blockStreamingMinChars": 1200,
    "blockStreamingMaxMessages": 3,
}


def validate_instance_id(value: str) -> str:
    """Return a normalized instance id or raise ValueError."""
    instance_id = value.strip()
    if not instance_id or not _INSTANCE_ID_RE.fullmatch(instance_id):
        raise ValueError("weixin account id must match [A-Za-z0-9_-]+")
    return instance_id


def runtime_channel_name(base_name: str, instance_id: str) -> str:
    """Return the channel key used for routing messages at runtime."""
    return base_name if instance_id == DEFAULT_INSTANCE_ID else f"{base_name}.{instance_id}"


def weixin_default_config() -> dict[str, Any]:
    return dict(_DEFAULT_CONFIG)


def account_id_from(value: Any) -> str:
    """Extract a stable account id from a legacy account entry."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return str(
            value.get("account_id")
            or value.get("accountId")
            or value.get("id")
            or value.get("name")
            or ""
        ).strip()
    return ""


def managed_weixin_instance_specs(
    section: Any,
    *,
    enabled_only: bool = True,
) -> list[ChannelInstanceSpec]:
    """Expand legacy ``accounts`` (or the default single account) into specs."""
    raw_specs, inherited = _weixin_instance_inputs(section)

    specs: list[ChannelInstanceSpec] = []
    instance_ids: set[str] = set()
    for index, raw in enumerate(raw_specs):
        if isinstance(raw, str):
            raw = {"account_id": raw}
        if not isinstance(raw, dict):
            logger.warning("Skipping invalid Weixin account at index {}: expected an object", index)
            continue

        fallback_id = DEFAULT_INSTANCE_ID if index == 0 and not inherited.get("accounts") else f"account-{index + 1}"
        config = _normalize_weixin_instance(
            cast(dict[str, Any], raw),
            inherited,
            fallback_id=fallback_id,
        )
        try:
            instance_id = validate_instance_id(str(config.get("account_id", "")))
        except ValueError as exc:
            logger.warning("Skipping invalid Weixin account '{}': {}", config.get("account_id"), exc)
            continue
        if instance_id in instance_ids:
            logger.warning("Skipping duplicate Weixin account '{}'", instance_id)
            continue
        instance_ids.add(instance_id)
        enabled = bool(config.get("enabled", inherited.get("enabled", False)))
        if enabled_only and not enabled:
            continue
        specs.append(ChannelInstanceSpec(instance_id=instance_id, config=config))
    return specs


def _weixin_instance_inputs(section: Any) -> tuple[list[Any], dict[str, Any]]:
    if hasattr(section, "model_dump"):
        section = section.model_dump(mode="json", by_alias=True)
    if not isinstance(section, dict):
        section = {}
    data = cast(dict[str, Any], section)
    accounts = data.get("accounts")
    inherited = {key: value for key, value in data.items() if key != "accounts"}
    if isinstance(accounts, list) and accounts:
        return list(cast(list[Any], accounts)), inherited
    if isinstance(accounts, list) and not accounts:
        return [], inherited
    return [data], inherited


def _normalize_weixin_instance(
    raw: dict[str, Any],
    inherited: dict[str, Any],
    *,
    fallback_id: str,
) -> dict[str, Any]:
    raw_base = dict(raw)
    account_id = str(account_id_from(raw) or inherited.get("account_id") or inherited.get("accountId") or fallback_id).strip()
    raw_base.pop("id", None)
    raw_base.pop("accountId", None)
    raw_base.pop("account_id", None)
    config = dict(weixin_default_config())
    config.pop("accountId", None)
    config.update(inherited)
    config.update(raw_base)
    config["account_id"] = account_id
    config.pop("accounts", None)
    config.pop("accountId", None)
    return config


def canonical_weixin_section(section: Any) -> dict[str, Any]:
    """Return a canonical account list for config editing."""
    raw_specs, inherited = _weixin_instance_inputs(section)
    accounts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_specs):
        if not isinstance(raw, dict):
            raw = {"account_id": str(raw)}
        fallback_id = DEFAULT_INSTANCE_ID if index == 0 and not inherited.get("accounts") else f"account-{index + 1}"
        config = _normalize_weixin_instance(
            cast(dict[str, Any], raw),
            inherited,
            fallback_id=fallback_id,
        )
        account_id = str(config["account_id"])
        if account_id in seen:
            raise ValueError(f"duplicate Weixin account id '{account_id}'")
        seen.add(account_id)
        accounts.append(config)
    return cast(dict[str, Any], _compact_weixin_accounts(accounts))


def upsert_weixin_account(section: Any, instance_id: str, values: dict[str, Any]) -> dict[str, Any]:
    """Return a canonical section with one account created or updated."""
    instance_id = validate_instance_id(instance_id)
    canonical = canonical_weixin_section(section)
    accounts = canonical.get("accounts")
    if not isinstance(accounts, list):
        accounts = []
        canonical["accounts"] = accounts
    for account in accounts:
        if str(account.get("account_id", "")) == instance_id:
            account.update(values)
            account["account_id"] = instance_id
            return canonical
    account = dict(weixin_default_config())
    account.update(values)
    account["account_id"] = instance_id
    accounts.append(account)
    return canonical


def update_managed_weixin_instance(
    section: Any,
    values: dict[str, Any],
    *,
    instance_id: str = DEFAULT_INSTANCE_ID,
) -> dict[str, Any]:
    if hasattr(section, "model_dump"):
        section = section.model_dump(mode="json", by_alias=True)
    section_data = cast(dict[str, Any], section) if isinstance(section, dict) else {}

    # Preserve a legacy flat section for the default instance; only convert to
    # the account-list shape when a non-default account is edited.
    if (
        instance_id == DEFAULT_INSTANCE_ID
        and not isinstance(section_data.get("accounts"), list)
    ):
        return {**section_data, **values}
    return upsert_weixin_account(section, instance_id, values)


def _compact_weixin_accounts(accounts: list[dict[str, Any]]) -> dict[str, Any]:
    """Move shared default settings back to the section root when useful."""
    if not accounts:
        return {}
    # Keep one canonical shape: accounts list is explicit, root keeps only
    # generic activation metadata. This is also the shape README documents.
    return {"accounts": accounts}


WEIXIN_MANAGEMENT = ChannelManagementSpec(
    multi_instance=True,
    default_config=weixin_default_config,
    instance_specs=managed_weixin_instance_specs,
    update_instance_config=update_managed_weixin_instance,
    runtime_name=runtime_channel_name,
)


__all__ = [
    "DEFAULT_INSTANCE_ID",
    "WEIXIN_MANAGEMENT",
    "account_id_from",
    "canonical_weixin_section",
    "managed_weixin_instance_specs",
    "runtime_channel_name",
    "update_managed_weixin_instance",
    "upsert_weixin_account",
    "validate_instance_id",
    "weixin_default_config",
]
