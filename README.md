# OVMS Plugin for Hermes Agent

**Work in progress. For testing only, not production use.**

Adds **OpenVINO Model Server** to `hermes model`. Requires Hermes with
model-provider plugin support and an already-running OVMS server with a chat
model. This plugin does not install or start OVMS.

## Windows Quickstart

Use Windows 11 x64 with the [Visual C++ x64 Redistributable](https://aka.ms/vs/17/release/VC_redist.x64.exe)
installed. Run the following in normal, non-administrator Command Prompt (`cmd.exe`) windows.
Installation and the model download require internet access.

### 1. Install Hermes

Run the official PowerShell installer from Command Prompt. It downloads and runs
a script; `-NonInteractive` skips onboarding so you can configure OVMS directly:

```bat
powershell -NoProfile -Command "& ([scriptblock]::Create((irm https://hermes-agent.nousresearch.com/install.ps1))) -NonInteractive"
```

### 2. Install and Start OVMS

In a separate Command Prompt, download the Python-enabled Windows package,
initialize it, and download a small model for CPU testing:

```bat
if not exist "%USERPROFILE%\ovms-hermes" mkdir "%USERPROFILE%\ovms-hermes"
cd /d "%USERPROFILE%\ovms-hermes"
curl.exe --fail --location --output ovms.zip https://storage.openvinotoolkit.org/repositories/openvino_model_server/packages/2026.4.1/ovms_windows_2026.4.1_python_on.zip
tar.exe -xf ovms.zip
call ovms\setupvars.bat
if not exist models mkdir models
ovms --pull --source_model OpenVINO/Qwen3-4B-int4-ov --model_repository_path "%USERPROFILE%\ovms-hermes\models" --target_device CPU --task text_generation
ovms --model_path "%USERPROFILE%\ovms-hermes\models\OpenVINO\Qwen3-4B-int4-ov" --model_name OpenVINO/Qwen3-4B-int4-ov --rest_port 8000 --rest_bind_address 127.0.0.1 --grpc_bind_address 127.0.0.1
```

Wait for OVMS to finish loading and leave this terminal running.

### 3. Install the Plugin and Chat

Open a fresh Command Prompt so Hermes is on PATH. Do not run OVMS's
setup script in this terminal.

```bat
hermes plugins install helena-intel/hermes-ovms
hermes model
```

In the setup prompts:

1. Choose **OpenVINO Model Server**.
2. Enter `ovms-no-auth` for `OVMS_API_KEY` (do not leave it blank).
3. Accept the default endpoint, `http://127.0.0.1:8000/v3`.
4. Select `OpenVINO/Qwen3-4B-int4-ov`, or enter that model ID manually.

When setup finishes, start chatting:

```bat
hermes chat
```

OVMS 2026.4.1 supports both `/v1` and `/v3`; this guide uses the plugin's `/v3`
default. The 4B model is for short tests: its 40,960-token context is below
Hermes's documented 64K minimum. If Hermes rejects it, use a longer-context
model rather than inflating the context setting. Hermes tools run with your
Windows account's permissions; use non-sensitive files for testing.

For prerequisites and troubleshooting, see the [full Windows guide](https://gist.github.com/helena-intel/a1d74be4f8c19b4919845c8693f593ad).

## Install

```text
hermes plugins install helena-intel/hermes-ovms
```

## Configure

Run the interactive model setup:

```text
hermes model
```

1. Choose **OpenVINO Model Server**.
2. At the `OVMS_API_KEY` prompt, enter your bearer token, or `ovms-no-auth` if
   your server has authentication disabled. Enter alone cancels setup.
3. For the local quickstart, accept `http://127.0.0.1:8000/v3` and select
   `OpenVINO/Qwen3-4B-int4-ov`, or enter its model ID manually.
4. Run `hermes chat`.

The `ovms-no-auth` value is only a placeholder; it does not bypass authentication.
Tool calling and other model capabilities depend on your OVMS deployment.

## API Key

If your OVMS server has no authentication, enter this at the `OVMS_API_KEY` prompt:

```text
ovms-no-auth
```

Do not leave it blank: pressing Enter cancels setup. If your server requires
authentication, enter its actual bearer token instead.

## Uninstall

If OVMS is your active provider, run `hermes model` and select another provider
first. Then remove the plugin:

```text
hermes plugins remove hermes-ovms
```

Restart any running Hermes chat or dashboard after removal. To install it again
for a demo, use the install command above.