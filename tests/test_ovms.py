"""OVMS discovery, routing, and catalog contracts against real Hermes imports."""

import json
import shutil
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


@pytest.fixture
def ovms_profile(tmp_path, monkeypatch):
    home = tmp_path / "profile"
    destination = home / "plugins" / "model-providers" / "ovms"
    destination.mkdir(parents=True)
    source = Path(__file__).resolve().parents[1]
    for filename in ("__init__.py", "plugin.yaml"):
        shutil.copyfile(source / filename, destination / filename)
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("OVMS_API_KEY", raising=False)

    from providers import get_provider_profile

    profile = get_provider_profile("ovms")
    assert profile is not None
    return profile


def test_discovery_aliases_and_named_picker(ovms_profile):
    from hermes_cli.main_provider_setup import _build_provider_picker_rows
    from hermes_cli.models_catalog_static import sync_plugin_provider_catalog
    from hermes_cli.providers import resolve_provider_full
    from providers import get_provider_profile

    sync_plugin_provider_catalog()
    rows, _ = _build_provider_picker_rows({}, "ovms", {}, {})
    assert any(key == "ovms" and "OpenVINO Model Server" in label for key, label, _ in rows)
    for name in ("ovms", "openvino", "openvino-model-server"):
        assert get_provider_profile(name) is ovms_profile
        resolved = resolve_provider_full(name)
        assert resolved is not None
        assert resolved.id == "ovms"
        assert resolved.transport == "openai_chat"
    assert ovms_profile.get_hostname() == ""


def test_runtime_uses_selected_endpoint_and_placeholder(ovms_profile, monkeypatch):
    from hermes_cli.config import save_config
    from hermes_cli import runtime_provider

    config = {
        "model": {
            "provider": "ovms",
            "default": "served-chat-model",
            "base_url": "http://127.0.0.1:9988/v3",
        },
    }
    monkeypatch.setenv("OVMS_API_KEY", "ovms-no-auth")
    save_config(config)
    resolved = runtime_provider.resolve_runtime_provider(requested="ovms")
    assert resolved["provider"] == "ovms"
    assert resolved["base_url"] == config["model"]["base_url"]
    assert resolved["api_key"] == "ovms-no-auth"
    assert resolved["api_mode"] == "chat_completions"


@pytest.mark.parametrize("api_key", ["ovms-no-auth", "test-server-token"])
def test_catalog_uses_selected_base_url_and_bearer_token(ovms_profile, api_key):
    requests = []

    class CatalogHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append((self.path, self.headers.get("Authorization")))
            body = json.dumps({
                "object": "list",
                "data": [{"id": "served-chat-model", "object": "model", "owned_by": "OVMS"}],
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), CatalogHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_port}/proxy/v3"
        assert ovms_profile.fetch_models(api_key=api_key, base_url=base_url) == ["served-chat-model"]
        assert requests == [("/proxy/v3/models", f"Bearer {api_key}")]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)