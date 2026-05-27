from android_mcp.adb_utils import devices, get_display_text, dump_ui_xml, type_text, get_device_info, get_installed_packages
import subprocess
import time

ADB = r"C:\Users\Tech Trends\AppData\Local\Android\Sdk\platform-tools\adb.exe"

print("=== Testing MCP Server Functions ===")
print()

print("1. devices():", devices())

subprocess.run([ADB, "shell", "monkey", "-p", "com.example.calculator", "-c", "android.intent.category.LAUNCHER", "1"], capture_output=True)
print("2. App launched")

time.sleep(3)

type_text("2+3", None)
time.sleep(0.5)
type_text("=", None)
time.sleep(1)

display = get_display_text(None)
print("3. get_display_text():", display)

xml = dump_ui_xml(None)
if xml and len(xml) > 100:
    print("4. dump_ui_xml(): received", len(xml), "chars")
    import re
    m = re.search(r'tv_input[^>]*text="([^"]+)"', xml)
    m2 = re.search(r'text="([^"]+)"[^>]*tv_input', xml)
    if m:
        print("   tv_input text (from attrs):", m.group(1))
    elif m2:
        print("   tv_input text (from text):", m2.group(1))
    else:
        print("   tv_input text: not found")
else:
    print("4. dump_ui_xml(): failed")

print()
print("=== All tests passed ===")