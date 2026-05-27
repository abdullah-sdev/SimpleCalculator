"""Android MCP Server — exposes ADB/emulator/Gradle tools as MCP resources & tools."""
import os
import sys
import time
import base64
from io import BytesIO

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, LoggingLevel

from adb_utils import (
    devices, get_screen_size, start_emulator, stop_emulator,
    install_apk, uninstall_app, get_package_name, launch_app,
    take_screenshot, dump_ui_xml, find_element_by_text,
    find_element_by_content_desc, tap, swipe, type_text,
    press_key, wait_for_app, build_apk, run_unit_tests,
    run_espresso_tests, get_apk_path,
)

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))

app = Server("android-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_devices",
            description="List all connected Android devices (emulators and USB).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="start_emulator",
            description="Start an Android emulator AVD. If already running, returns existing device.",
inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "AVD name (default: Pixel_3a_API_34_extension_level_7_x86_64)"},
                    "visible": {"type": "boolean", "description": "Show emulator window (default: true)"},
                    "timeout": {"type": "integer", "description": "Seconds to wait for boot (default: 90)"},
                },
            },
        ),
        Tool(
            name="stop_emulator",
            description="Stop the running emulator.",
            inputSchema={
                "type": "object",
                "properties": {
                    "device": {"type": "string", "description": "Device serial (optional)"},
                },
            },
        ),
        Tool(
            name="build_debug_apk",
            description="Build the Android debug APK using Gradle assembleDebug.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string", "description": "Path to Android project (default: current dir)"},
                },
            },
        ),
        Tool(
            name="install_apk",
            description="Install (or reinstall) an APK on the device.",
            inputSchema={
                "type": "object",
                "properties": {
                    "apk_path": {"type": "string", "description": "Path to APK file"},
                    "device": {"type": "string", "description": "Device serial (optional)"},
                },
                "required": ["apk_path"],
            },
        ),
        Tool(
            name="uninstall_app",
            description="Uninstall a package from the device.",
            inputSchema={
                "type": "object",
                "properties": {
                    "package": {"type": "string", "description": "Package name"},
                    "device": {"type": "string", "description": "Device serial (optional)"},
                },
                "required": ["package"],
            },
        ),
        Tool(
            name="launch_app",
            description="Launch an app by package name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "package": {"type": "string", "description": "Package name"},
                    "activity": {"type": "string", "description": "Full component (optional)"},
                    "device": {"type": "string", "description": "Device serial (optional)"},
                },
                "required": ["package"],
            },
        ),
        Tool(
            name="screenshot",
            description="Take a screenshot and return as base64 PNG.",
            inputSchema={
                "type": "object",
                "properties": {
                    "device": {"type": "string", "description": "Device serial (optional)"},
                    "return_base64": {"type": "boolean", "description": "Return base64 string (default: true)"},
                },
            },
        ),
        Tool(
            name="find_and_tap_by_text",
            description="Find a UI element by its text label and tap it.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Button/text label to find (e.g., '5', '+', '=')"},
                    "device": {"type": "string", "description": "Device serial (optional)"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="find_and_tap_by_desc",
            description="Find a UI element by content-description and tap it.",
            inputSchema={
                "type": "object",
                "properties": {
                    "desc": {"type": "string", "description": "Content description attribute"},
                    "device": {"type": "string", "description": "Device serial (optional)"},
                },
                "required": ["desc"],
            },
        ),
        Tool(
            name="tap_coordinates",
            description="Tap a specific (x, y) coordinate.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate"},
                    "y": {"type": "integer", "description": "Y coordinate"},
                    "device": {"type": "string", "description": "Device serial (optional)"},
                },
                "required": ["x", "y"],
            },
        ),
        Tool(
            name="swipe",
            description="Swipe from one point to another.",
            inputSchema={
                "type": "object",
                "properties": {
                    "x1": {"type": "integer"},
                    "y1": {"type": "integer"},
                    "x2": {"type": "integer"},
                    "y2": {"type": "integer"},
                    "duration": {"type": "integer", "description": "Duration in ms (default: 300)"},
                    "device": {"type": "string", "description": "Device serial (optional)"},
                },
                "required": ["x1", "y1", "x2", "y2"],
            },
        ),
        Tool(
            name="press_key",
            description="Press a key (ENTER, BACK, HOME, BACKSPACE, etc).",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key name (e.g., ENTER, BACK, HOME)"},
                    "device": {"type": "string", "description": "Device serial (optional)"},
                },
                "required": ["key"],
            },
        ),
        Tool(
            name="get_ui_hierarchy",
            description="Dump current UI hierarchy XML for inspection.",
            inputSchema={
                "type": "object",
                "properties": {
                    "device": {"type": "string", "description": "Device serial (optional)"},
                },
            },
        ),
        Tool(
            name="wait_for_app",
            description="Wait for an app to be running (foreground).",
            inputSchema={
                "type": "object",
                "properties": {
                    "package": {"type": "string", "description": "Package name"},
                    "timeout": {"type": "integer", "description": "Seconds to wait (default: 30)"},
                    "device": {"type": "string", "description": "Device serial (optional)"},
                },
                "required": ["package"],
            },
        ),
        Tool(
            name="run_unit_tests",
            description="Run JUnit unit tests (Gradle testDebugUnitTest).",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string", "description": "Path to Android project"},
                },
            },
        ),
        Tool(
            name="run_espresso_tests",
            description="Run Espresso/UI tests (Gradle connectedDebugAndroidTest).",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string", "description": "Path to Android project"},
                },
            },
        ),
        Tool(
            name="smoke_test",
            description="Full pipeline: build APK, install on emulator, launch app, take screenshot, verify no crash.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string", "description": "Path to Android project"},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[dict]:
    device = arguments.pop("device", None)

    try:
        if name == "list_devices":
            devs = devices()
            return [{"type": "text", "text": f"Devices: {devs if devs else 'none'}"}]

        if name == "start_emulator":
            avd_name = arguments.get("name", "Pixel_3a_API_34_extension_level_7_x86_64")
            visible = arguments.get("visible", True)
            timeout = arguments.get("timeout", 90)
            d = start_emulator(avd_name, timeout, visible)
            return [{"type": "text", "text": f"Emulator started: {d}"}]

        if name == "stop_emulator":
            stop_emulator(device)
            return [{"type": "text", "text": "Emulator stopped."}]

        if name == "build_debug_apk":
            proj = arguments.get("project_dir", PROJECT_DIR)
            output, ok = build_apk(proj)
            return [{"type": "text", "text": f"Build {'SUCCESS' if ok else 'FAILED'}\n{output[-2000:]}"}]

        if name == "install_apk":
            apk = arguments.get("apk_path")
            if not apk or not os.path.exists(apk):
                return [{"type": "text", "text": f"APK not found: {apk}"}]
            result = install_apk(apk, device)
            return [{"type": "text", "text": result}]

        if name == "uninstall_app":
            result = uninstall_app(arguments["package"], device)
            return [{"type": "text", "text": result}]

        if name == "launch_app":
            result = launch_app(arguments["package"], arguments.get("activity"), device)
            return [{"type": "text", "text": result}]

        if name == "screenshot":
            b64 = take_screenshot(device)
            return [{"type": "text", "text": f"Screenshot captured (base64 length: {len(b64)})"}]

        if name == "find_and_tap_by_text":
            xml = dump_ui_xml(device)
            coords = find_element_by_text(xml, arguments["text"])
            if not coords:
                return [{"type": "text", "text": f"Element not found: '{arguments['text']}'"}]
            tap(coords[0], coords[1], device)
            return [{"type": "text", "text": f"Tapped '{arguments['text']}' at {coords}"}]

        if name == "find_and_tap_by_desc":
            xml = dump_ui_xml(device)
            coords = find_element_by_content_desc(xml, arguments["desc"])
            if not coords:
                return [{"type": "text", "text": f"Element not found: '{arguments['desc']}'"}]
            tap(coords[0], coords[1], device)
            return [{"type": "text", "text": f"Tapped by desc '{arguments['desc']}' at {coords}"}]

        if name == "tap_coordinates":
            tap(arguments["x"], arguments["y"], device)
            return [{"type": "text", "text": f"Tapped ({arguments['x']}, {arguments['y']})"}]

        if name == "swipe":
            result = swipe(
                arguments["x1"], arguments["y1"],
                arguments["x2"], arguments["y2"],
                arguments.get("duration", 300), device
            )
            return [{"type": "text", "text": f"Swiped {arguments['x1']},{arguments['y1']} -> {arguments['x2']},{arguments['y2']}"}]

        if name == "press_key":
            press_key(arguments["key"], device)
            return [{"type": "text", "text": f"Pressed {arguments['key']}"}]

        if name == "get_ui_hierarchy":
            xml = dump_ui_xml(device)
            return [{"type": "text", "text": xml[:3000] if xml else "No UI hierarchy"}]

        if name == "wait_for_app":
            ok = wait_for_app(
                arguments["package"],
                arguments.get("timeout", 30),
                device
            )
            return [{"type": "text", "text": f"App {'running' if ok else 'NOT running after timeout'}"}]

        if name == "run_unit_tests":
            proj = arguments.get("project_dir", PROJECT_DIR)
            output, ok = run_unit_tests(proj, device)
            return [{"type": "text", "text": f"Unit tests {'PASSED' if ok else 'FAILED'}\n{output[-2000:]}"}]

        if name == "run_espresso_tests":
            proj = arguments.get("project_dir", PROJECT_DIR)
            output, ok = run_espresso_tests(proj, device)
            return [{"type": "text", "text": f"Espresso tests {'PASSED' if ok else 'FAILED'}\n{output[-2000:]}"}]

        if name == "smoke_test":
            # 1. Build
            proj = arguments.get("project_dir", PROJECT_DIR)
            out, ok = build_apk(proj)
            if not ok:
                return [{"type": "text", "text": f"BUILD FAILED:\n{out[-2000:]}"}]

            # 2. Find APK
            apk = get_apk_path(proj)
            if not apk:
                return [{"type": "text", "text": "APK not found after build"}]

            # 3. Start emulator
            dev = start_emulator()
            time.sleep(2)

            # 4. Install
            install_result = install_apk(apk, dev)
            if "Success" not in install_result and "success" not in install_result:
                return [{"type": "text", "text": f"INSTALL FAILED: {install_result}"}]

            # 5. Launch
            launch_app("com.example.calculator", None, dev)
            time.sleep(3)

            # 6. Screenshot
            b64 = take_screenshot(dev)
            time.sleep(1)

            # 7. Check app is running
            app_ok = wait_for_app("com.example.calculator", 10, dev)

            return [{
                "type": "text",
                "text": f"Smoke test {'PASSED' if app_ok else 'FAILED'}\n- APK: {apk}\n- Device: {dev}\n- App launched: {app_ok}\n- Screenshot captured: {len(b64)} bytes"
            }]

    except Exception as e:
        import traceback
        return [{"type": "text", "text": f"Error: {e}\n{traceback.format_exc()[-1000:]}"}]

    return [{"type": "text", "text": "Unknown tool"}]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())