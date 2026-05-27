# Android MCP Server

An MCP (Model Context Protocol) server that provides tools for building, testing, and interacting with Android apps using ADB and Gradle.

## Setup

```bash
cd android_mcp_server
C:\Python\Python312\python.exe -m venv venv
.\venv\Scripts\pip install -r requirements.txt
```

## Running

```bash
.\venv\Scripts\python.exe server.py
```

The server uses stdio transport — connect it to any MCP-compatible AI client.

## Available Tools

| Tool | Description |
|------|-------------|
| `list_devices` | List connected Android devices |
| `start_emulator` | Start an AVD (default: Pixel_3a_API_34) |
| `stop_emulator` | Stop the running emulator |
| `build_debug_apk` | Run `gradlew assembleDebug` |
| `install_apk` | Install APK on device |
| `uninstall_app` | Uninstall package |
| `launch_app` | Launch app by package name |
| `screenshot` | Capture screen as base64 PNG |
| `find_and_tap_by_text` | Find UI element by text label, then tap |
| `find_and_tap_by_desc` | Find UI element by content-desc, then tap |
| `tap_coordinates` | Tap (x, y) coordinates |
| `swipe` | Swipe from point A to point B |
| `press_key` | Press key (ENTER, BACK, HOME, etc.) |
| `get_ui_hierarchy` | Dump UI XML hierarchy |
| `wait_for_app` | Wait for app to be in foreground |
| `run_unit_tests` | Run JUnit tests via `testDebugUnitTest` |
| `run_espresso_tests` | Run UI tests via `connectedDebugAndroidTest` |
| `smoke_test` | Full pipeline: build → install → launch → screenshot → verify |

## Emulator Configuration

- **AVD Name**: `Pixel_3a_API_34_extension_level_7_x86_64`
- **Screen**: 1080x2220
- **API**: 34 (Android 14)
- **GPU**: Software rendering (swiftshader_indirect)

## Gradle Build Environment

```python
JAVA_HOME = r"C:\Program Files\Android\Android Studio\jbr"
```