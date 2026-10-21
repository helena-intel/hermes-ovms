"""OpenVINO Model Server provider plugin for Hermes Agent."""

from providers import register_provider
from providers.base import ProviderProfile


class OVMSProfile(ProviderProfile):
    """Connect to an existing OVMS deployment without claiming shared hostnames."""

    def get_hostname(self) -> str:
        return ""


register_provider(OVMSProfile(
    name="ovms",
    aliases=("openvino", "openvino-model-server"),
    display_name="OpenVINO Model Server",
    description="OpenVINO Model Server (local or remote OpenAI-compatible inference)",
    env_vars=("OVMS_API_KEY",),
    base_url="http://127.0.0.1:8000/v3",
    api_mode="chat_completions",
    auth_type="api_key",
))