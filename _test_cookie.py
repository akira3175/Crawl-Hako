"""
Test: Tool tự mở Chrome với remote debug port rồi lấy cookie qua CDP
"""
import subprocess, time, urllib.request, json, websocket, os, glob

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.join(os.environ.get("LOCALAPPDATA",""), "Google","Chrome","Application","chrome.exe"),
]

chrome_exe = next((p for p in CHROME_PATHS if os.path.isfile(p)), None)
print("Chrome:", chrome_exe)

if not chrome_exe:
    exit("Chrome not found")

import tempfile
tmp_profile = tempfile.mkdtemp(prefix="hako_chrome_")
PORT = 9223  # dùng port khác để không đụng Chrome đang chạy

proc = subprocess.Popen([
    chrome_exe,
    f"--remote-debugging-port={PORT}",
    f"--remote-allow-origins=http://127.0.0.1:{PORT}",
    f"--user-data-dir={tmp_profile}",
    "--no-first-run",
    "--no-default-browser-check",
    "https://ln.hako.vn/login",
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print(f"Opened Chrome PID={proc.pid}, waiting for debug port...")
time.sleep(3)

BASE = f"http://127.0.0.1:{PORT}"
for i in range(10):
    try:
        with urllib.request.urlopen(f"{BASE}/json/version", timeout=2) as r:
            info = json.loads(r.read())
        print("Connected! Browser WS:", info.get("webSocketDebuggerUrl",""))
        break
    except:
        time.sleep(1)
else:
    proc.terminate()
    exit("Could not connect")

print("=== Đăng nhập vào trang Hako trong Chrome vừa mở rồi nhấn Enter ===")
input()

# Lấy cookie qua CDP
ws_url = info["webSocketDebuggerUrl"]
ws = websocket.WebSocket()
ws.connect(ws_url, origin=f"http://127.0.0.1:{PORT}")
ws.send(json.dumps({"id": 1, "method": "Storage.getCookies"}))
resp = json.loads(ws.recv())
ws.close()

cookies = resp.get("result", {}).get("cookies", [])
hako = [c for c in cookies if "hako" in c.get("domain","") or "docln" in c.get("domain","")]
print(f"Hako cookies: {len(hako)}")
for c in hako:
    print(f"  {c['name']} = {c['value'][:60]}")

proc.terminate()

import shutil
shutil.rmtree(tmp_profile, ignore_errors=True)
