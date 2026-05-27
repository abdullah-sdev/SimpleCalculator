"""ADB utility helpers."""
import subprocess
import os
import time
import re
from pathlib import Path


ANDROID_SDK = r"C:\Users\Tech Trends\AppData\Local\Android\Sdk"
ADB = os.path.join(ANDROID_SDK, "platform-tools", "adb.exe")
EMULATOR = os.path.join(ANDROID_SDK, "emulator", "emulator.exe")
GRADLE = os.path.join(os.getcwd(), "..", "gradlew.bat")


def _run(args, timeout=30, capture=True, check=True):
    """Run a command, optionally capture output."""
    result = subprocess.run(
        args,
        capture_output=capture,
        text=True,
        timeout=timeout,
        shell=True,
        cwd=os.path.dirname(os.path.dirname(__file__))
    )
    if check and result.returncode != 0:
        return result
    return result


def _run_output(args, timeout=30, check=True):
    """Run a command and return stdout."""
    result = _run(args, timeout, capture=True, check=False)
    return (result.stdout or result.stderr or "").strip()


def devices():
    """List connected devices (emulators + USB)."""
    out = _run_output([ADB, "devices"])
    lines = [l.strip() for l in out.splitlines() if l.strip() and "\t" in l]
    return [l.split("\t")[0] for l in lines]


def get_screen_size(device=None):
    """Get screen resolution WxH."""
    cmd = [ADB]
    if device:
        cmd.extend(["-s", device])
    cmd.extend(["shell", "wm", "size"])
    out = _run_output(cmd)
    m = re.search(r"(\d+)x(\d+)", out)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 1080, 1920


def start_emulator(name="Pixel_3a_API_34_extension_level_7_x86_64", timeout=60, visible=False):
    """Start an AVD emulator and wait for it to boot."""
    print(f"[ADB] Starting emulator '{name}'...")

    existing = [d for d in devices() if d.startswith("emulator")]
    if existing:
        print(f"[ADB] Emulator already running: {existing[0]}")
        return existing[0]

    args = [EMULATOR, "-avd", name, "-no-snapshot", "-gpu", "swiftshader_indirect"]
    if visible:
        print(f"[ADB] Emulator will run with visible window")
    else:
        args.append("-no-window")

    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )

    for _ in range(timeout):
        devs = devices()
        for d in devs:
            if d.startswith("emulator"):
                state = _run_output([ADB, "-s", d, "shell", "getprop", "sys.boot_completed"]).strip()
                if state == "1":
                    print(f"[ADB] Emulator ready: {d}")
                    return d
        time.sleep(2)

    raise RuntimeError(f"Emulator did not boot within {timeout}s")


def stop_emulator(device=None):
    """Kill emulator via ADB emu kill or process termination."""
    if device:
        _run_output([ADB, "-s", device, "emu", "kill"], timeout=10)
    else:
        _run_output([ADB, "emu", "kill"], timeout=10)
    time.sleep(2)
    try:
        import psutil
        for p in psutil.pids():
            try:
                name = psutil.Process(p).name().lower()
                if "emulator" in name or "qemu" in name:
                    os.kill(p, 9)
            except:
                pass
    except ImportError:
        pass


def install_apk(apk_path, device=None, grant_permissions=True):
    """Install an APK on the device."""
    cmd = [ADB, "install", "-r"]
    if device:
        cmd.insert(1, "-s")
        cmd.insert(2, device)
    cmd.append(apk_path)
    result = _run_output(cmd, timeout=60)
    if grant_permissions:
        pkg = get_package_name(apk_path)
        if pkg:
            _run_output([ADB] + (["-s", device] if device else []) + ["shell", "pm", "grant", pkg, "android.permission.INTERNET"], timeout=10)
    return result


def uninstall_app(package, device=None):
    """Uninstall a package."""
    cmd = [ADB]
    if device:
        cmd.extend(["-s", device])
    cmd.extend(["uninstall", package])
    return _run_output(cmd, timeout=30)


def get_package_name(apk_path):
    """Get package name from APK via aapt."""
    aapt = os.path.join(ANDROID_SDK, "build-tools", "34.0.0", "aapt.exe")
    out = _run_output(f'"{aapt}" dump badging "{apk_path}"', timeout=15)
    m = re.search(r"package: name='([^']+)'", out or "")
    return m.group(1) if m else None


def launch_app(package, activity=None, device=None):
    """Launch an app via am start."""
    cmd = [ADB]
    if device:
        cmd.extend(["-s", device])
    if activity:
        cmd.extend(["shell", "am", "start", "-n", f"{package}/{activity}"])
    else:
        cmd.extend(["shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"])
    return _run_output(cmd, timeout=15)


def take_screenshot(device=None, save_path=None):
    """Capture screenshot and return base64-encoded PNG."""
    if save_path is None:
        save_path = os.path.join(os.path.dirname(__file__), "screenshot.png")

    remote = "/sdcard/screen.png"
    cmd_base = [ADB]
    if device:
        cmd_base.extend(["-s", device])

    _run_output(cmd_base + ["shell", "screencap", "-p", remote], timeout=10)
    _run_output(cmd_base + ["pull", remote, save_path], timeout=15)
    _run_output(cmd_base + ["shell", "rm", remote], timeout=5)

    if not os.path.exists(save_path):
        raise RuntimeError("Screenshot file not found after pull")

    with open(save_path, "rb") as f:
        import base64
        return base64.b64encode(f.read()).decode()


def dump_ui_xml(device=None):
    """Get current UI hierarchy as XML string."""
    remote = "/sdcard/ui_dump.xml"
    cmd_base = [ADB]
    if device:
        cmd_base.extend(["-s", device])

    _run_output(cmd_base + ["shell", "uiautomator", "dump", remote], timeout=10)
    out = _run_output(cmd_base + ["shell", "cat", remote], timeout=10)
    _run_output(cmd_base + ["shell", "rm", remote], timeout=5)
    return out


def find_element_by_text(xml, text):
    """Find element bounds by text in UI XML. Returns (x, y, w, h) or None."""
    pattern = re.compile(
        rf'text="{re.escape(text)}"[^>]*bounds="(\d+),(\d+)\[(\d+),(\d+)\]',
        re.IGNORECASE
    )
    m = pattern.search(xml)
    if m:
        x, y, w, h = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        return (x + w // 2, y + h // 2)
    return None


def find_element_by_content_desc(xml, desc):
    """Find element by content-desc."""
    pattern = re.compile(
        rf'content-desc="{re.escape(desc)}"[^>]*bounds="(\d+),(\d+)\[(\d+),(\d+)\]',
        re.IGNORECASE
    )
    m = pattern.search(xml)
    if m:
        x, y, w, h = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        return (x + w // 2, y + h // 2)
    return None


def tap(x, y, device=None):
    """Tap coordinates."""
    cmd = [ADB]
    if device:
        cmd.extend(["-s", device])
    cmd.extend(["shell", "input", "tap", str(x), str(y)])
    return _run_output(cmd, timeout=5)


def swipe(x1, y1, x2, y2, duration=300, device=None):
    """Swipe from (x1,y1) to (x2,y2)."""
    cmd = [ADB]
    if device:
        cmd.extend(["-s", device])
    cmd.extend(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)])
    return _run_output(cmd, timeout=5)


def type_text(text, device=None):
    """Type text via ADB."""
    cmd = [ADB]
    if device:
        cmd.extend(["-s", device])
    cmd.extend(["shell", "input", "text", text.replace(" ", "%s")])
    return _run_output(cmd, timeout=5)


def press_key(key, device=None):
    """Press a key (ENTER, BACK, HOME, etc)."""
    cmd = [ADB]
    if device:
        cmd.extend(["-s", device])
    cmd.extend(["shell", "input", "keyevent", key])
    return _run_output(cmd, timeout=5)


def wait_for_app(package, timeout=30, device=None):
    """Wait for app to appear in processes."""
    cmd_base = [ADB]
    if device:
        cmd_base.extend(["-s", device])

    start = time.time()
    while time.time() - start < timeout:
        out = _run_output(cmd_base + ["shell", "dumpsys", "activity", "activities"], timeout=10)
        if package in out:
            return True
        time.sleep(1)
    return False


def build_apk(project_dir=None):
    """Build debug APK via Gradle."""
    if project_dir is None:
        project_dir = os.path.dirname(os.path.dirname(__file__))

    gradlew = os.path.join(project_dir, "gradlew.bat")
    env = os.environ.copy()
    env["JAVA_HOME"] = r"C:\Program Files\Android\Android Studio\jbr"

    result = subprocess.run(
        [gradlew, "assembleDebug"],
        capture_output=True,
        text=True,
        timeout=300,
        shell=True,
        cwd=project_dir,
        env=env
    )
    return result.stdout + result.stderr, result.returncode == 0


def run_unit_tests(project_dir=None, device=None):
    """Run JUnit unit tests via Gradle."""
    if project_dir is None:
        project_dir = os.path.dirname(os.path.dirname(__file__))

    gradlew = os.path.join(project_dir, "gradlew.bat")
    env = os.environ.copy()
    env["JAVA_HOME"] = r"C:\Program Files\Android\Android Studio\jbr"

    result = subprocess.run(
        [gradlew, "testDebugUnitTest"],
        capture_output=True,
        text=True,
        timeout=300,
        shell=True,
        cwd=project_dir,
        env=env
    )
    return result.stdout + result.stderr, result.returncode == 0


def run_espresso_tests(project_dir=None, device=None):
    """Run Espresso tests via Gradle connectedDebugAndroidTest."""
    if project_dir is None:
        project_dir = os.path.dirname(os.path.dirname(__file__))

    gradlew = os.path.join(project_dir, "gradlew.bat")
    env = os.environ.copy()
    env["JAVA_HOME"] = r"C:\Program Files\Android\Android Studio\jbr"

    result = subprocess.run(
        [gradlew, "connectedDebugAndroidTest"],
        capture_output=True,
        text=True,
        timeout=600,
        shell=True,
        cwd=project_dir,
        env=env
    )
    return result.stdout + result.stderr, result.returncode == 0


def get_apk_path(project_dir=None):
    """Get the debug APK path."""
    if project_dir is None:
        project_dir = os.path.dirname(os.path.dirname(__file__))
    apk = os.path.join(project_dir, "app", "build", "outputs", "apk", "debug", "app-debug.apk")
    if os.path.exists(apk):
        return apk
    return None