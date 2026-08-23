"""WeChat setup validation owned by the channel package."""

from typing import Any

from nanobot.channels.contracts import ChannelValidationContext
from nanobot.channels.validation import check, enabled, official_action, payload, string_value
from nanobot.channels.weixin.instances import managed_weixin_instance_specs


def validate(values: dict[str, Any], _context: ChannelValidationContext) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    specs = managed_weixin_instance_specs(values, enabled_only=False)
    has_setup = any(
        enabled(spec.config) or string_value(spec.config.get("token"))
        for spec in specs
    ) if specs else (enabled(values) or string_value(values.get("token")))
    if has_setup:
        checks.append(
            check("local_state", "Local login state", "pass", "Saved local login state was detected.")
        )
        return payload("weixin", "configured", checks, can_enable=True)
    checks.append(
        check(
            "terminal_login",
            "Terminal login",
            "skipped",
            "This channel uses a terminal QR login flow.",
            action_url=official_action("weixin"),
        )
    )
    return payload(
        "weixin",
        "needs_setup",
        checks,
        missing_fields=["terminal_login"],
        can_enable=False,
    )


__all__ = ["validate"]
