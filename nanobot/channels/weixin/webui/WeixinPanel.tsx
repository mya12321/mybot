import { useTranslation } from "react-i18next";

import {
  channelTranslator,
  type ChannelTranslator,
} from "@/channel-plugins/i18n";
import type { ChannelPluginPanelProps } from "@/channel-plugins/types";
import { ChannelInstancesPanel } from "@/components/settings/channels/ChannelInstancesPanel";
import { Button } from "@/components/ui/button";
import type {
  NanobotChannelInstanceInfo,
  NanobotFeatureInfo,
} from "@/lib/types";

import { WeixinConnectFlow } from "./WeixinConnectFlow";

export function WeixinPanel({
  token,
  feature,
  actionKey,
  chatAppsDocsUrl,
  showBrandLogos,
  onAction,
  onFeaturesUpdate,
}: ChannelPluginPanelProps) {
  const { t } = useTranslation();
  const channelTx = channelTranslator(t, "weixin");
  const instances = feature.instances?.length
    ? feature.instances
    : [defaultWeixinInstance(feature)];
  const missingSupport = feature.enabled && !feature.installed;
  const installBusy = actionKey === `enable:${feature.name}`;

  return (
    <ChannelInstancesPanel
      feature={feature}
      showBrandLogos={showBrandLogos}
      chatAppsDocsUrl={chatAppsDocsUrl}
      instances={instances}
      onFeaturesUpdate={onFeaturesUpdate}
      customization={{
        countLabel: (count) => weixinAccountCountLabel(count, channelTx),
        toggleAriaLabel: (instance) => channelTx(
          "custom.toggleAccount",
          "{{name}} account",
          { name: instanceDisplayName(instance) },
        ),
        configuredLabel: channelTx("custom.configured", "Connected"),
        needsSetupLabel: channelTx("custom.needsSetup", "Needs login"),
        renderInstanceAction: (instance) => (
          <WeixinConnectFlow
            key={instance.id}
            token={token}
            feature={feature}
            instanceId={instance.id}
            runtimeError={instance.runtime_error}
            runtimeStatus={instance.runtime_status}
            idleLabel={channelTx("custom.connectAccount", "Connect account")}
            onFeaturesUpdate={onFeaturesUpdate}
          />
        ),
        footer: (
          <div className="mt-4 overflow-hidden rounded-floating border border-border/70 bg-background px-4 py-4">
            {missingSupport && feature.install_supported ? (
              <div className="mb-3 flex justify-end">
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  disabled={installBusy}
                  onClick={() => onAction("enable", feature.name)}
                  className="h-8 rounded-full px-3 text-[12px] font-semibold"
                >
                  {channelTx(
                    "custom.installSupport",
                    "Install WeChat support",
                  )}
                </Button>
              </div>
            ) : null}
            <div className="text-[13px] font-semibold text-foreground">
              {channelTx("custom.addAccount", "Add another account")}
            </div>
            <p className="mt-1 text-[12.5px] leading-5 text-muted-foreground">
              {channelTx(
                "custom.addAccountHint",
                "Add a new account ID in the WeChat channel settings, then connect it here.",
              )}
            </p>
          </div>
        ),
      }}
    />
  );
}

function defaultWeixinInstance(feature: NanobotFeatureInfo): NanobotChannelInstanceInfo {
  return {
    id: "default",
    name: "default",
    enabled: feature.enabled,
    configured: Boolean(feature.configured),
    config_values: feature.config_values ?? {},
    configured_fields: feature.configured_fields ?? [],
  };
}

function weixinAccountCountLabel(
  count: number,
  tx: ChannelTranslator,
): string {
  if (count === 0) return tx("custom.countNone", "No WeChat account connected");
  if (count === 1) return tx("custom.countOne", "1 WeChat account connected");
  return tx("custom.countMany", "{{count}} WeChat accounts connected", { count });
}

function instanceDisplayName(instance: NanobotChannelInstanceInfo): string {
  return instance.display_name?.trim() || instance.name.trim() || instance.id;
}
