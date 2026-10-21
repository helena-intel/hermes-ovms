# OVMS Provider for Hermes Agent

A standalone model-provider plugin that adds **OpenVINO Model Server** to
`hermes model`. Connects to an existing local or remote OVMS deployment using
Hermes's OpenAI Chat Completions transport. No Hermes core changes or additional
Python dependencies are required by the plugin.

## Prerequisites

- A Hermes Agent version supporting model-provider plugins and automatic picker
  registration (the October 2026 plugin API).
- An already-running OVMS server with a chat model deployed. This plugin does not
  install OVMS, export models, start the server, or download model weights.
- For agent workflows, a model and server configuration supporting tool calling.
  Streaming, reasoning, vision, context limits, and tools depend on the deployment;
  this plugin does not assume those capabilities for every served model.

## Install From This Folder

Place `__init__.py` and `plugin.yaml` together in an `ovms` directory under the
active profile's `plugins/model-providers/`. Resolve the profile home with
`hermes_constants.get_hermes_home()` rather than assuming its location.

For example, from a Hermes-enabled PowerShell session:

```powershell
$source = 'C:\Users\helena\repos\hermes-ovms'
$homePath = (& python -c "from hermes_constants import get_hermes_home; print(get_hermes_home())").Trim()
if ($LASTEXITCODE -ne 0) { throw 'Run this from a Hermes-enabled Python environment.' }
$destination = Join-Path $homePath 'plugins\model-providers\ovms'
if (Test-Path $destination) { throw "Already exists: $destination" }
New-Item -ItemType Directory -Path $destination | Out-Null
Copy-Item (Join-Path $source '__init__.py'), (Join-Path $source 'plugin.yaml') -Destination $destination
```

This only installs the two plugin files. It does not overwrite an existing plugin
or change your model configuration. Set `HERMES_HOME` to the intended profile home
before the example when using a non-default profile. Start a new `hermes model`
command after installation.

If this folder is later published as a Git repository, it can also be installed
with `hermes plugins install <owner>/<repo>`. No repository is required for the
local installation above.

## Configure

1. If your endpoint differs from `http://127.0.0.1:8000/v3`, configure the
  provider and endpoint first:

  ```text
  hermes config set model.provider ovms
  hermes config set model.base_url http://your-server:8000/v3
  ```

  Use the server's actual REST port, and include `/v3` but not
  `/chat/completions`. Port 8000 is a convenient default, not a required OVMS
  port. These commands change the active model route; finish setup before
  starting another agent session.
2. Run `hermes model` and choose **OpenVINO Model Server**.
3. For `OVMS_API_KEY`, enter your server's bearer token. For a server with
   authentication disabled, enter the non-secret placeholder `ovms-no-auth`.
4. Accept the displayed base URL. This Hermes version ignores edits to the
  wizard's URL prompt for profiles without a base-URL environment variable;
  use the configuration commands above to change it instead.
5. Select a model from the server catalog, or enter its exact served model ID if
   discovery is unavailable. Select a chat model, not an embedding or reranking
   servable: OVMS catalogs can contain multiple kinds of models.

The canonical provider ID is `ovms`; `openvino` and `openvino-model-server` are
aliases. The resulting model configuration has this shape:

```yaml
model:
  provider: ovms
  base_url: http://127.0.0.1:8000/v3
  default: your-served-model-id
```

Hermes saves the key separately in the active profile's secret store. Endpoint
configuration stays in `config.yaml`; the plugin introduces no base-URL environment
variable. For a protected remote endpoint, use HTTPS with a valid certificate.
The placeholder does not bypass authentication: it is sent as a bearer value and
only works when the server accepts requests without authentication. Hermes's
generic API-key setup currently cancels on an empty key, so the placeholder is
required even for a keyless deployment.

## Behavior and Limitations

- Catalog discovery uses `GET <base_url>/models`; inference uses
  `POST <base_url>/chat/completions`. The default URLs therefore end in
  `/v3/models` and `/v3/chat/completions`.
- Model discovery, credentials, persistence, and streaming reuse Hermes's
  existing provider framework. No fixed catalog is bundled.
- The plugin never identifies servers by hostname alone. Registering OVMS must
  not turn unrelated localhost, LAN, or proxy endpoints into OVMS routes.
- It does not enable Responses API mode, add reasoning parameters, or invent a
  universal context window. Configure model capabilities in Hermes when needed.
- Older OVMS releases or reverse proxies may not expose the model-list endpoint;
  manual model-ID entry remains available. A successful catalog probe does not
  prove that inference authentication or tool calling is configured correctly.

OVMS endpoint reference:
<https://docs.openvino.ai/2025/model-server/ovms_docs_rest_api_chat.html>

## Tests

The integration tests use real Hermes imports, a temporary `HERMES_HOME`, and a
local HTTP fixture, with no live OVMS server or model downloads. Run them from
the Hermes checkout using its prepared test environment and canonical runner:

```bash
scripts/run_tests.sh ../hermes-ovms/tests/test_ovms.py -v
```

A separate live OVMS smoke test is still needed to verify the chosen deployment's
model, streaming, tool calls, and server-side authentication.