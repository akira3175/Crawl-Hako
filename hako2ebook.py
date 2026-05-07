import argparse
import itertools
import json
import re
import time
import threading
from io import BytesIO
from multiprocessing.dummy import Pool as ThreadPool
from os import mkdir
from os.path import isdir, isfile, join

# Khóa luồng cho việc lưu file JSON để tránh xung đột khi tải song song
json_lock = threading.Lock()

import requests
import tqdm
from bs4 import BeautifulSoup
from ebooklib import epub
from PIL import Image
import tkinter as tk
from tkinter import messagebox
import tkinter.font as tkfont

SLEEPTIME = 30
DELAY_MIN = 2.0
DELAY_MAX = 3.0
LINE_SIZE = 80
THREAD_NUM = 8
DEFAULT_URLS = "https://docln.sbs"
DEFAULT_SAVE_FOLDER = "raw"

SETTINGS_FILE = "settings.json"

def _load_settings():
    global SLEEPTIME, DELAY_MIN, DELAY_MAX, LINE_SIZE, THREAD_NUM, DEFAULT_URLS, DEFAULT_SAVE_FOLDER
    if isfile(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "SLEEPTIME" in data: SLEEPTIME = int(data["SLEEPTIME"])
                if "DELAY_MIN" in data: DELAY_MIN = float(data["DELAY_MIN"])
                if "DELAY_MAX" in data: DELAY_MAX = float(data["DELAY_MAX"])
                if "LINE_SIZE" in data: LINE_SIZE = int(data["LINE_SIZE"])
                if "THREAD_NUM" in data: THREAD_NUM = int(data["THREAD_NUM"])
                if "DEFAULT_URLS" in data: DEFAULT_URLS = data["DEFAULT_URLS"]
                if "DEFAULT_SAVE_FOLDER" in data: DEFAULT_SAVE_FOLDER = data["DEFAULT_SAVE_FOLDER"]
        except Exception:
            pass

_load_settings()
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.97 Safari/537.36',
    'Referer': 'https://ln.hako.vn/'
}

tool_version = '2.0.5'
bs4_html_parser = 'html.parser'
import cloudscraper

# ─── Quản lý Cloudscraper để vượt qua Rate Limit (Cloudflare) ────────────────
import random as _random

# Mở rộng số lượng User-Agent và User Profile một cách đa dạng (Windows, Mac, Linux, iOS, Android)
USER_AGENTS = [
    # --- Desktop: Windows ---
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Vivaldi/6.6.3271.45",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 YaBrowser/24.1.1.940 Yowser/2.5 Safari/537.36",
    
    # --- Desktop: macOS ---
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    
    # --- Desktop: Linux ---
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    
    # --- Mobile: Android ---
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 14; Mobile; rv:123.0) Gecko/123.0 Firefox/123.0",
    
    # --- Mobile: iOS (iPhone / iPad) ---
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
]

# Các cấu hình an toàn của cloudscraper (tự match TLS theo base platform)
CLOUD_PROFILES = [
    {'browser': 'chrome',  'platform': 'windows', 'desktop': True},
    {'browser': 'firefox', 'platform': 'windows', 'desktop': True},
    {'browser': 'chrome',  'platform': 'darwin',  'desktop': True},
    {'browser': 'firefox', 'platform': 'darwin',  'desktop': True},
    {'browser': 'chrome',  'platform': 'linux',   'desktop': True},
    {'browser': 'firefox', 'platform': 'linux',   'desktop': True},
    {'browser': 'chrome',  'platform': 'android', 'desktop': False},
    {'browser': 'firefox', 'platform': 'android', 'desktop': False},
]

# ─── Mở rộng xoay tua Proxy (IP rotation) ────────────────────────────────────
PROXY_LIST = []
if isfile("proxies.txt"):
    try:
        with open("proxies.txt", "r", encoding="utf-8") as _pf:
            PROXY_LIST = [p.strip() for p in _pf if p.strip() and not p.startswith("#")]
    except Exception:
        pass

# ─── Cookie đăng nhập (để crawl truyện bị ẩn / chỉ quản lý xem được) ────────
# Đặt file cookies.json (format Netscape/EditThisCookie) hoặc cookies.txt
# bên cạnh hako2ebook.py để tự động load.
SESSION_COOKIES: dict = {}

def _load_cookies():
    """Đọc cookie từ cookies.json hoặc cookies.txt và lưu vào SESSION_COOKIES."""
    global SESSION_COOKIES
    # Ưu tiên cookies.json (export từ EditThisCookie / Cookie-Editor)
    if isfile("cookies.json"):
        try:
            with open("cookies.json", "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Hỗ trợ 2 format: [{"name":..., "value":...}] hoặc {"name": "value"}
            if isinstance(raw, list):
                SESSION_COOKIES = {c["name"]: c["value"] for c in raw if "name" in c and "value" in c}
            elif isinstance(raw, dict):
                SESSION_COOKIES = raw
            if SESSION_COOKIES:
                print(f"[Cookie] Đã load {len(SESSION_COOKIES)} cookie từ cookies.json")
            return
        except Exception as e:
            print(f"[Cookie] Lỗi đọc cookies.json: {e}")
    # Fallback: cookies.txt (format: domain\tFLAG\tpath\tSECURE\texpiry\tname\tvalue)
    if isfile("cookies.txt"):
        try:
            with open("cookies.txt", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) >= 7:
                        SESSION_COOKIES[parts[5]] = parts[6]
            if SESSION_COOKIES:
                print(f"[Cookie] Đã load {len(SESSION_COOKIES)} cookie từ cookies.txt")
        except Exception as e:
            print(f"[Cookie] Lỗi đọc cookies.txt: {e}")

_load_cookies()

COOKIES_FILE = "cookies.json"

HAKO_DOMAINS = ['.hako.vn', '.docln.net', '.docln.sbs']

def grab_cookies_from_browser(port: int = 9223) -> tuple[bool, str]:
    """
    Kết nối qua Chrome DevTools Protocol để lấy cookie từ trình duyệt đã được mở.
    Trả về (True, "Chrome") hoặc (False, thông_báo_lỗi).
    """
    global SESSION_COOKIES
    import urllib.request, json as _json

    try:
        import websocket
    except ImportError:
        return False, "Thiếu thư viện websocket-client. Vui lòng cài đặt (pip install websocket-client)."

    BASE = f"http://127.0.0.1:{port}"
    try:
        with urllib.request.urlopen(f"{BASE}/json/version", timeout=2) as r:
            info = _json.loads(r.read())
        browser_ws = info.get("webSocketDebuggerUrl", "")
    except Exception as e:
        return False, f"Không thể kết nối với trình duyệt đang mở (lỗi: {e}). Hãy thử lại nút 'Mở trang đăng nhập'."

    if not browser_ws:
        return False, "Trình duyệt không hỗ trợ CDP (thiếu webSocketDebuggerUrl)."

    try:
        ws = websocket.WebSocket()
        ws.connect(browser_ws, origin=f"http://127.0.0.1:{port}")
        ws.send(_json.dumps({"id": 1, "method": "Storage.getCookies"}))
        resp = _json.loads(ws.recv())
        ws.close()
    except Exception as e:
        return False, f"Lỗi trong quá trình lấy cookie qua WebSocket: {e}"

    cookies = resp.get("result", {}).get("cookies", [])
    found_cookies = {}
    
    for c in cookies:
        domain = c.get("domain", "")
        if "hako" in domain or "docln" in domain:
            if c.get("name") == "ln_session":
                found_cookies["ln_session"] = c.get("value")
                break

    if not found_cookies:
        return False, "Không tìm thấy cookie ln_session. Bạn đã đăng nhập thành công chưa?"

    SESSION_COOKIES = found_cookies
    try:
        import json
        with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(found_cookies, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    try:
        if hasattr(_tls, 'scraper'):
            _tls.scraper.cookies.update(SESSION_COOKIES)
    except Exception:
        pass

    return True, "Chrome (tự động)"



# Mỗi thread có session cloudscraper riêng → tải song song an toàn
_tls = threading.local()

def _get_scraper():
    """Trả về cloudscraper session giả lập Chrome Windows để khớp TLS fingerprint."""
    if not hasattr(_tls, 'scraper'):
        # CHÚ Ý: Không dùng custom User-Agent ngẫu nhiên vì sẽ gây lỗi lệch TLS Fingerprint với Cloudflare.
        # Luôn để cloudscraper tự chọn User-Agent khớp với nền tảng nó hỗ trợ.
        b_config = {'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        _tls.scraper = cloudscraper.create_scraper(browser=b_config, delay=10)
        
        # Nếu có danh sách proxy, chọn ngẫu nhiên một proxy và gán vào session hiện tại
        if PROXY_LIST:
            proxy = _random.choice(PROXY_LIST)
            if "://" not in proxy:
                proxy = f"http://{proxy}"
            _tls.scraper.proxies = {"http": proxy, "https": proxy}
        
        # Inject cookie đăng nhập nếu có
        if SESSION_COOKIES:
            _tls.scraper.cookies.update(SESSION_COOKIES)
            
    return _tls.scraper

def _rotate_scraper():
    """Huỷ session hiện tại và xoay sang session/browser khác."""
    try:
        if hasattr(_tls, 'scraper'):
            _tls.scraper.close()
    except Exception:
        pass
    if hasattr(_tls, 'scraper'):
        del _tls.scraper

_request_lock = threading.Lock()

def check_available_request(url, steam=False, max_exception_retries=5):
    exception_count = 0
    rate_limit_count = 0
    while True:
        session = _get_scraper()
        
        req_headers = {'Referer': HEADERS.get('Referer', 'https://ln.hako.vn/')}

        # Luôn sync cookie vào session trước mỗi request (phòng trường hợp cookie được load sau)
        if SESSION_COOKIES:
            session.cookies.update(SESSION_COOKIES)

        try:
            # Cực kỳ quan trọng: Sử dụng Global Lock để dàn hàng Request.
            # Ngăn chặn việc 8 Luồng (Threads) ngủ xong và thức dậy bắn Request cùng 1 tích tắc (Gây ra lỗi 429 Cloudflare)
            with _request_lock:
                time.sleep(_random.uniform(DELAY_MIN, DELAY_MAX))
            
            req = session.get(url, stream=steam, headers=req_headers, timeout=30)
            status_code = req.status_code
            
            if any(substr in url for substr in ['ln.hako.vn', 'docln.net', 'docln.sbs']):
                # Hako có thể trả về 503 nhưng nội dung thực chất là trang 404 (truyện bị ẩn)
                is_fake_503_404 = (status_code in [403, 503]) and ('error-name">404<' in req.text or 'error-name">403<' in req.text)

                if status_code in range(200, 299) or status_code == 404 or is_fake_503_404:
                    return req
                elif status_code in [403, 429, 503]:
                    rate_limit_count += 1
                    
                    # Dump HTML ra file để debug
                    try:
                        with open(f"error_{status_code}_debug.html", "w", encoding="utf-8") as f:
                            f.write(req.text)
                    except Exception:
                        pass
                        
                    if rate_limit_count > 5:
                        print(f"Status {status_code}, đã thử đổi session 5 lần nhưng vẫn bị chặn. Bỏ qua link này.")
                        return req
                        
                    jitter = _random.uniform(5, 10)  # Chờ lâu hơn để server hạ nhiệt
                    print(f"Status {status_code}, đang bị chặn (Cloudflare/Rate-limit). Chờ {jitter:.1f}s để đổi session... (lần {rate_limit_count})")
                    _rotate_scraper()
                    time.sleep(jitter)
                    continue
                else:
                    print(f"Status {status_code}, retrying in {SLEEPTIME}s...")
                    time.sleep(SLEEPTIME)
                    continue
            return req
        except Exception as e:
            exception_count += 1
            if exception_count > max_exception_retries:
                raise Exception(f"Kết nối thất bại. Lỗi mạng: {e}")
            print(f"Network error: {e}, retrying in 5s ({exception_count}/{max_exception_retries})...")
            # Rotate scraper khi bị lỗi kết nối SSL/mạng để tránh sticky error
            _rotate_scraper()
            time.sleep(5)


# ─────────────────────────────────────────────────────────────────────────────
# THEME CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
BG_DARK      = "#0d0d1a"   # Nền tối chính
BG_CARD      = "#131326"   # Nền card
BG_INPUT     = "#0e1628"   # Nền input
BG_BUTTON    = "#0f3460"   # Nền nút thường
ACCENT       = "#e94560"   # Màu accent đỏ-hồng
ACCENT2      = "#6c3fc7"   # Tím đậm
ACCENT3      = "#00e5ff"   # Cyan sáng
FG_PRIMARY   = "#eaeaea"   # Chữ chính
FG_SECONDARY = "#8892b0"   # Chữ phụ
FG_SUCCESS   = "#23d18b"   # Xanh lá
FG_ERROR     = "#ff4757"   # Đỏ lỗi
FG_WARNING   = "#ffb347"   # Cam cảnh báo
FG_INFO      = "#00e5ff"   # Cyan thông tin
BORDER       = "#1e2040"   # Màu viền
BG_HEADER    = "#0a0a18"   # Nền header


class HakoApp:
    """
    Giao diện chính của Hako2Ebook — dark cyberpunk, log real-time.
    Cửa sổ ở lại mở trong suốt quá trình tải.
    """
    def __init__(self, engine_ref=None):
        self.root = tk.Tk()
        self.value = None
        self._engine = engine_ref
        self._is_downloading = False
        self._btn_start = None
        self._btn_paste = None
        self._btn_clear = None
        self._novel_rows = {}
        self._settings_visible = False
        self._settings_panel  = None
        self._svar = {}
        # Per-novel log state
        self._novel_logs: dict[str, list] = {}   # line -> [(text, tag), ...]
        self._all_logs:   list            = []   # [(text, tag), ...] global
        self._selected_novel: str | None  = None  # None = xem tất cả
        self._prog_count_var = None  # khởi tạo sau _build_ui
        self._build_window()
        self._build_ui()
        import sys
        sys.stdout = _LogRedirector(self.log_area, self.root, app=self)
        self._append_log("Chào mừng bạn đến với Hako2Ebook!", "info")
        self._append_log(
            f"Phiên bản: {tool_version}  |  Luồng tải: {THREAD_NUM}  |  Tối đa 4 truyện song song",
            "muted"
        )
        self._append_log("⚙  Vui lòng kiểm tra cài đặt bên trên trước khi bắt đầu tải.", "warning")
        self._append_log("─" * 72, "muted")
        self.root.mainloop()

    # ── Window ────────────────────────────────────────────────────────────────
    def _build_window(self):
        self.root.title("Hako2Ebook — Light Novel Downloader")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)
        w, h = 920, 700
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.root.minsize(760, 540)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        if self._is_downloading:
            # Nếu đang tải, hỏi xác nhận
            import tkinter.messagebox as mb
            if not mb.askyesno("Đang tải", "Đang tải truyện. Bạn có muốn thoát không?",
                               parent=self.root):
                return
        self.root.destroy()

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Top accent gradient bar ──
        banner = tk.Canvas(self.root, height=4, bg=BG_DARK, highlightthickness=0)
        banner.pack(fill=tk.X)
        banner.bind("<Configure>", lambda e: self._draw_banner(banner))

        # ── Header block ──
        hdr_frame = tk.Frame(self.root, bg=BG_HEADER)
        hdr_frame.pack(fill=tk.X)

        hdr_inner = tk.Frame(hdr_frame, bg=BG_HEADER)
        hdr_inner.pack(fill=tk.X, padx=20, pady=12)

        # Left: logo + subtitle
        logo_block = tk.Frame(hdr_inner, bg=BG_HEADER)
        logo_block.pack(side=tk.LEFT)

        logo_row = tk.Frame(logo_block, bg=BG_HEADER)
        logo_row.pack(anchor=tk.W)
        tk.Label(logo_row, text="  ",
                 font=("Segoe UI", 18, "bold"), fg=ACCENT3, bg=BG_HEADER
                 ).pack(side=tk.LEFT)
        tk.Label(logo_row, text="HAKO2EBOOK",
                 font=("Segoe UI", 18, "bold"), fg="#ffffff", bg=BG_HEADER
                 ).pack(side=tk.LEFT)
        tk.Label(logo_row, text=f"  v{tool_version}",
                 font=("Segoe UI", 9), fg=FG_SECONDARY, bg=BG_HEADER
                 ).pack(side=tk.LEFT, padx=(2, 0), pady=(4, 0))

        tk.Label(logo_block,
                 text="  Tải Light Novel từ Hako · Docln · chuyển thành EPUB  ",
                 font=("Segoe UI", 9), fg=FG_SECONDARY, bg=BG_HEADER
                 ).pack(anchor=tk.W, pady=(2, 0))

        # Right: settings button
        right_block = tk.Frame(hdr_inner, bg=BG_HEADER)
        right_block.pack(side=tk.RIGHT, anchor=tk.CENTER)
        self._gear_btn = self._make_button(
            right_block, "⚙  Cài đặt", self._toggle_settings,
            "#1c1c35", "#2c2c50", font=("Segoe UI", 9), padx=14, pady=6)
        self._gear_btn.pack()

        # Thin separator
        tk.Frame(self.root, bg="#1a1a35", height=1).pack(fill=tk.X)

        # ── Settings container (được pack/unpack theo toggle) ──
        self._settings_container = tk.Frame(self.root, bg=BG_DARK)
        self._settings_panel = self._build_settings_panel(self._settings_container)
        self._pane_ref = None

        # ── Main content area ──
        content = tk.Frame(self.root, bg=BG_DARK)
        content.pack(fill=tk.BOTH, expand=True, padx=18, pady=(14, 8))

        # ── Input section label ──
        inp_header = tk.Frame(content, bg=BG_DARK)
        inp_header.pack(fill=tk.X, pady=(0, 6))

        # Left: section label with colored accent bar
        accent_dot = tk.Frame(inp_header, bg=ACCENT3, width=3)
        accent_dot.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        tk.Label(inp_header,
                 text="LINK TRUYỆN",
                 font=("Segoe UI", 8, "bold"), fg=ACCENT3, bg=BG_DARK
                 ).pack(side=tk.LEFT)
        tk.Label(inp_header,
                 text="  mỗi dòng một link hoặc ID",
                 font=("Segoe UI", 8), fg=FG_SECONDARY, bg=BG_DARK
                 ).pack(side=tk.LEFT)

        # ── Input card ──
        inp_card = tk.Frame(content, bg=BORDER, padx=1, pady=1)
        inp_card.pack(fill=tk.X)
        inp_inner = tk.Frame(inp_card, bg=BG_INPUT)
        inp_inner.pack(fill=tk.BOTH, expand=True)
        inp_inner.rowconfigure(0, weight=1)
        inp_inner.columnconfigure(0, weight=1)

        self.text_area = tk.Text(
            inp_inner, font=("Consolas", 10),
            bg=BG_INPUT, fg=FG_PRIMARY,
            insertbackground=ACCENT3,
            selectbackground=ACCENT2, selectforeground=FG_PRIMARY,
            relief=tk.FLAT, padx=14, pady=10,
            wrap=tk.WORD, undo=True,
            height=6
        )
        self.text_area.grid(row=0, column=0, sticky=tk.NSEW)
        self.text_area.bind("<Control-v>", self._on_ctrl_v)
        self._set_placeholder()
        self.text_area.bind("<FocusIn>",  self._clear_placeholder)
        self.text_area.bind("<FocusOut>", self._restore_placeholder)

        inp_sb = tk.Scrollbar(inp_inner, command=self.text_area.yview,
                              bg=BG_INPUT, troughcolor=BG_DARK,
                              activebackground=ACCENT2, relief=tk.FLAT, width=10)
        inp_sb.grid(row=0, column=1, sticky=tk.NS)
        self.text_area.configure(yscrollcommand=inp_sb.set)

        # ── Action buttons row ──
        btn_row = tk.Frame(content, bg=BG_DARK)
        btn_row.pack(fill=tk.X, pady=(10, 0))

        self._btn_paste = self._make_button(
            btn_row, "📋  Paste", self._paste_clipboard,
            "#2a1e6e", "#3d2a9e",
            font=("Segoe UI", 9, "bold"), padx=16, pady=7)
        self._btn_paste.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_clear = self._make_button(
            btn_row, "🗑  Xóa", self._clear_text,
            "#1e1e38", "#2e2e50",
            font=("Segoe UI", 9), padx=16, pady=7)
        self._btn_clear.pack(side=tk.LEFT)

        self._btn_start = self._make_button(
            btn_row, "▶  Bắt đầu tải", self._start_download,
            ACCENT, "#c0192b",
            font=("Segoe UI", 10, "bold"), padx=28, pady=8)
        self._btn_start.pack(side=tk.RIGHT)

        # ── Separator ──
        tk.Frame(content, bg=BORDER, height=1).pack(fill=tk.X, pady=(14, 0))

        # ── Horizontal split: left=progress, right=detail log ──
        h_pane = tk.PanedWindow(content, orient=tk.HORIZONTAL,
                                bg="#0a0a18", sashwidth=5, sashrelief=tk.FLAT,
                                sashpad=0, relief=tk.FLAT, bd=0)
        h_pane.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        # ════════════════════════════════════════════════════
        # LEFT — Tiến độ từng truyện
        # ════════════════════════════════════════════════════
        left_outer = tk.Frame(h_pane, bg=BG_DARK)
        h_pane.add(left_outer, minsize=220)

        # Left header
        lhdr = tk.Frame(left_outer, bg=BG_DARK)
        lhdr.pack(fill=tk.X, pady=(0, 6))
        tk.Frame(lhdr, bg=ACCENT3, width=3).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 7))
        tk.Label(lhdr, text="TIẾN ĐỘ",
                 font=("Segoe UI", 8, "bold"), fg=ACCENT3, bg=BG_DARK
                 ).pack(side=tk.LEFT)
        self._prog_count_var = tk.StringVar(value="")
        tk.Label(lhdr, textvariable=self._prog_count_var,
                 font=("Segoe UI", 7), fg=FG_SECONDARY, bg=BG_DARK
                 ).pack(side=tk.LEFT, padx=(6, 0))

        # Scrollable area for novel cards
        prog_scroll_outer = tk.Frame(left_outer, bg=BORDER, padx=1, pady=1)
        prog_scroll_outer.pack(fill=tk.BOTH, expand=True)
        prog_canvas = tk.Canvas(prog_scroll_outer, bg=BG_DARK,
                                highlightthickness=0, bd=0)
        prog_sb = tk.Scrollbar(prog_scroll_outer, orient=tk.VERTICAL,
                               command=prog_canvas.yview,
                               bg=BG_DARK, troughcolor=BG_DARK,
                               activebackground=ACCENT2, relief=tk.FLAT, width=8)
        prog_canvas.configure(yscrollcommand=prog_sb.set)
        prog_sb.pack(side=tk.RIGHT, fill=tk.Y)
        prog_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.progress_frame = tk.Frame(prog_canvas, bg=BG_DARK)
        self._prog_canvas_win = prog_canvas.create_window(
            (0, 0), window=self.progress_frame, anchor=tk.NW)

        def _on_pf_configure(e):
            prog_canvas.configure(scrollregion=prog_canvas.bbox("all"))
        def _on_pc_configure(e):
            prog_canvas.itemconfig(self._prog_canvas_win, width=e.width)
        self.progress_frame.bind("<Configure>", _on_pf_configure)
        prog_canvas.bind("<Configure>", _on_pc_configure)

        # Empty state label
        self._prog_empty_lbl = tk.Label(
            self.progress_frame,
            text="Chưa có truyện nào\nđang được tải.",
            font=("Segoe UI", 9), fg="#353560", bg=BG_DARK,
            justify=tk.CENTER)
        self._prog_empty_lbl.pack(pady=24)

        # ════════════════════════════════════════════════════
        # RIGHT — Chi tiết log
        # ════════════════════════════════════════════════════
        right_outer = tk.Frame(h_pane, bg=BG_DARK)
        h_pane.add(right_outer, minsize=300)

        # Right header
        rhdr = tk.Frame(right_outer, bg=BG_DARK)
        rhdr.pack(fill=tk.X, pady=(0, 6))
        tk.Frame(rhdr, bg=ACCENT2, width=3).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 7))
        self._right_header_var = tk.StringVar(
            value="NHẬT KÝ CHI TIẾT  ·  click truyện để lọc")
        tk.Label(rhdr, textvariable=self._right_header_var,
                 font=("Segoe UI", 8, "bold"), fg=ACCENT2, bg=BG_DARK
                 ).pack(side=tk.LEFT)
        clear_lbl = tk.Label(rhdr, text="✕ Xóa",
                             font=("Segoe UI", 7), fg="#444466", bg=BG_DARK,
                             cursor="hand2")
        clear_lbl.pack(side=tk.RIGHT)
        clear_lbl.bind("<Button-1>", lambda e: self._clear_log())
        clear_lbl.bind("<Enter>", lambda e: clear_lbl.configure(fg=FG_SECONDARY))
        clear_lbl.bind("<Leave>", lambda e: clear_lbl.configure(fg="#444466"))

        log_card = tk.Frame(right_outer, bg=BORDER, padx=1, pady=1)
        log_card.pack(fill=tk.BOTH, expand=True)
        log_inner = tk.Frame(log_card, bg=BG_CARD)
        log_inner.pack(fill=tk.BOTH, expand=True)
        log_inner.rowconfigure(0, weight=1)
        log_inner.columnconfigure(0, weight=1)

        self.log_area = tk.Text(
            log_inner, font=("Consolas", 9),
            bg=BG_CARD, fg=FG_SECONDARY,
            relief=tk.FLAT, padx=12, pady=10,
            state=tk.DISABLED, wrap=tk.WORD
        )
        self.log_area.grid(row=0, column=0, sticky=tk.NSEW)

        log_sb2 = tk.Scrollbar(log_inner, command=self.log_area.yview,
                               bg=BG_CARD, troughcolor=BG_DARK,
                               activebackground=ACCENT2, relief=tk.FLAT, width=8)
        log_sb2.grid(row=0, column=1, sticky=tk.NS)
        self.log_area.configure(yscrollcommand=log_sb2.set)

        # Color tags
        self.log_area.tag_configure("info",    foreground=FG_INFO)
        self.log_area.tag_configure("success", foreground=FG_SUCCESS)
        self.log_area.tag_configure("error",   foreground=FG_ERROR)
        self.log_area.tag_configure("warning", foreground=FG_WARNING)
        self.log_area.tag_configure("muted",   foreground=FG_SECONDARY)
        self.log_area.tag_configure("chapter", foreground="#6a7090")
        self.log_area.tag_configure("title",   foreground=ACCENT3,
                                    font=("Consolas", 9, "bold"))

        # Set default sash position after window draws
        self.root.after(100, lambda: h_pane.sash_place(0, 280, 0))

        # ── Status bar ──
        tk.Frame(self.root, bg="#12122a", height=1).pack(fill=tk.X)
        sb = tk.Frame(self.root, bg=BG_HEADER, pady=5)
        sb.pack(fill=tk.X, padx=0)

        status_left = tk.Frame(sb, bg=BG_HEADER)
        status_left.pack(side=tk.LEFT, padx=18)
        self.status_var = tk.StringVar(value="●  Sẵn sàng")
        self.status_lbl = tk.Label(
            status_left, textvariable=self.status_var,
            font=("Segoe UI", 9), fg=FG_SUCCESS, bg=BG_HEADER, anchor=tk.W)
        self.status_lbl.pack(side=tk.LEFT)

        tk.Label(sb, text="ln.hako.vn  ·  docln.net  ·  docln.sbs",
                 font=("Segoe UI", 8), fg="#404060", bg=BG_HEADER
                 ).pack(side=tk.RIGHT, padx=18)

        # Gán _pane_ref để settings toggle hoạt động
        self._pane_ref = content

    # ── Accent bar ─────────────────────────────────────────────────────────
    def _draw_banner(self, canvas):
        canvas.delete("all")
        w = canvas.winfo_width()
        third = max(w // 3, 1)
        canvas.create_rectangle(0,       0, third,   5, fill=ACCENT,  outline="")
        canvas.create_rectangle(third,   0, third*2, 5, fill=ACCENT2, outline="")
        canvas.create_rectangle(third*2, 0, w,       5, fill=ACCENT3, outline="")

    # ── Button factory ─────────────────────────────────────────────────────
    def _make_button(self, parent, text, cmd, bg, hover_bg,
                     font=("Segoe UI", 10), padx=14, pady=7):
        # Outer frame acts as border / rounded look
        outer = tk.Frame(parent, bg=bg, padx=0, pady=0)
        btn = tk.Label(outer, text=text, font=font,
                       bg=bg, fg=FG_PRIMARY,
                       padx=padx, pady=pady, cursor="hand2", relief=tk.FLAT)
        btn.pack()
        btn._outer   = outer
        btn._bg      = bg
        btn._hov_bg  = hover_bg
        btn._locked  = False
        for w in (btn, outer):
            w.bind("<Button-1>", lambda e, b=btn: b._locked or cmd())
            w.bind("<Enter>",    lambda e, b=btn: b.configure(bg=b._hov_bg) or b._outer.configure(bg=b._hov_bg) if not b._locked else None)
            w.bind("<Leave>",    lambda e, b=btn: b.configure(bg=b._bg) or b._outer.configure(bg=b._bg))
        btn._outer = outer
        return outer

    def _get_btn_label(self, outer):
        """Lấy Label widget bên trong outer Frame của button."""
        for w in outer.winfo_children():
            if isinstance(w, tk.Label):
                return w
        return None

    def _lock_buttons(self):
        for outer, lock_bg in ((self._btn_paste, "#1a1a30"),
                               (self._btn_clear, "#181830"),
                               (self._btn_start, "#6b1025")):
            if not outer:
                continue
            lbl = self._get_btn_label(outer)
            if lbl:
                lbl._locked = True
                lbl.configure(bg=lock_bg, fg="#555566", cursor="arrow")
                outer.configure(bg=lock_bg)
        start_lbl = self._get_btn_label(self._btn_start)
        if start_lbl:
            start_lbl.configure(text="⏳  Đang tải...")

    def _unlock_buttons(self):
        for outer, bg in ((self._btn_paste, "#2a1e6e"),
                          (self._btn_clear, "#1e1e38"),
                          (self._btn_start, ACCENT)):
            if not outer:
                continue
            lbl = self._get_btn_label(outer)
            if lbl:
                lbl._locked = False
                lbl._bg = bg
                lbl.configure(bg=bg, fg=FG_PRIMARY, cursor="hand2")
                outer.configure(bg=bg)
        start_lbl = self._get_btn_label(self._btn_start)
        if start_lbl:
            start_lbl.configure(text="▶  Bắt đầu tải")

    # ── Placeholder ────────────────────────────────────────────────────────
    _PLACEHOLDER = ("Ví dụ:\n"
                    "https://ln.hako.vn/truyen/12345\n"
                    "https://docln.net/truyen/67890\n"
                    "24127")
    _placeholder_active = False

    def _set_placeholder(self):
        self.text_area.insert("1.0", self._PLACEHOLDER)
        self.text_area.configure(fg="#505070")
        self._placeholder_active = True

    def _clear_placeholder(self, _=None):
        if self._placeholder_active:
            self.text_area.delete("1.0", tk.END)
            self.text_area.configure(fg=FG_PRIMARY)
            self._placeholder_active = False

    def _restore_placeholder(self, _=None):
        if not self.text_area.get("1.0", tk.END).strip():
            self._set_placeholder()

    # ── Clipboard ──────────────────────────────────────────────────────────
    def _on_ctrl_v(self, _):
        self._paste_clipboard(); return "break"

    def _paste_clipboard(self):
        self._clear_placeholder()
        try:
            self.text_area.insert(tk.INSERT, self.root.clipboard_get())
        except Exception as e:
            self._append_log(f"Lỗi clipboard: {e}", "error")

    def _clear_text(self):
        self.text_area.delete("1.0", tk.END)
        self._set_placeholder()

    # ── Log helpers ────────────────────────────────────────────────────────
    def _append_log(self, msg, tag="muted"):
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.insert(tk.END, msg + "\n", tag)
        self.log_area.see(tk.END)
        self.log_area.configure(state=tk.DISABLED)

    def _clear_log(self):
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.delete("1.0", tk.END)
        self.log_area.configure(state=tk.DISABLED)

    # ── Novel progress cards ───────────────────────────────────────────────
    def _init_progress_rows(self, lines):
        """Tạo card tiến độ cho mỗi truyện trong panel bên trái."""
        for w in self.progress_frame.winfo_children():
            w.destroy()
        self._novel_rows = {}
        self._novel_logs = {line: [] for line in lines}
        self._all_logs   = []
        self._selected_novel = None
        self._prog_count_var.set(f"{len(lines)} truyện")
        self._update_right_header()

        for line in lines:
            # ── Card container ──
            card = tk.Frame(self.progress_frame, bg="#131328",
                            highlightbackground="#1e2040", highlightthickness=1,
                            cursor="hand2")
            card.pack(fill=tk.X, padx=4, pady=3)

            # Top row: icon + title
            top = tk.Frame(card, bg="#131328", cursor="hand2")
            top.pack(fill=tk.X, padx=8, pady=(7, 2))

            icon_lbl = tk.Label(top, text="⏳", font=("Segoe UI", 11),
                                bg="#131328", fg=FG_WARNING, cursor="hand2")
            icon_lbl.pack(side=tk.LEFT, padx=(0, 6))

            short = line if len(line) <= 28 else line[:25] + "…"
            name_lbl = tk.Label(top, text=short,
                                font=("Segoe UI", 9, "bold"),
                                bg="#131328", fg=FG_SECONDARY, anchor=tk.W,
                                cursor="hand2")
            name_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Status text row
            mid = tk.Frame(card, bg="#131328", cursor="hand2")
            mid.pack(fill=tk.X, padx=14, pady=(0, 4))
            status_lbl = tk.Label(mid, text="Đang chờ…",
                                  font=("Segoe UI", 8), fg="#555577",
                                  bg="#131328", anchor=tk.W, cursor="hand2")
            status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
            pct_lbl = tk.Label(mid, text="",
                               font=("Consolas", 8), fg=ACCENT3,
                               bg="#131328", anchor=tk.E, cursor="hand2")
            pct_lbl.pack(side=tk.RIGHT)

            # Progress bar
            bar_frame = tk.Frame(card, bg="#131328", cursor="hand2")
            bar_frame.pack(fill=tk.X, padx=8, pady=(0, 7))
            bar_bg = tk.Frame(bar_frame, bg="#1e2040", height=4)
            bar_bg.pack(fill=tk.X)
            bar_fill = tk.Frame(bar_bg, bg=ACCENT3, height=4, width=0)
            bar_fill.place(x=0, y=0, relheight=1, relwidth=0)

            self._novel_rows[line] = {
                "card":     card,
                "icon":     icon_lbl,
                "name":     name_lbl,
                "status":   status_lbl,
                "pct":      pct_lbl,
                "bar_bg":   bar_bg,
                "bar_fill": bar_fill,
            }

            # Click handlers — tất cả widgets trong card
            for w in (card, top, mid, bar_frame, icon_lbl, name_lbl, status_lbl, pct_lbl):
                w.bind("<Button-1>", lambda e, ln=line: self._select_novel(ln))
                w.bind("<Enter>",    lambda e, c=card: c.configure(highlightbackground=ACCENT2))
                w.bind("<Leave>",    lambda e, c=card, ln=line: c.configure(
                    highlightbackground=FG_SUCCESS if self._novel_rows.get(ln, {}).get('done') else
                    FG_ERROR if self._novel_rows.get(ln, {}).get('failed') else
                    (ACCENT3 if ln == self._selected_novel else "#1e2040")
                ))

    # ── Novel selection / log routing ───────────────────────────────────
    def _select_novel(self, line):
        """Chuyển right panel sang log của truyện được chọn."""
        if self._selected_novel == line:
            # Toggle off → quay lại xem tất cả
            self._selected_novel = None
        else:
            self._selected_novel = line
        self._refresh_log_panel()
        self._update_right_header()
        # Cập nhật viền card
        for ln, r in self._novel_rows.items():
            if ln == self._selected_novel:
                r["card"].configure(highlightbackground=ACCENT3, highlightthickness=2)
            elif r.get("done"):
                r["card"].configure(highlightbackground=FG_SUCCESS, highlightthickness=1)
            elif r.get("failed"):
                r["card"].configure(highlightbackground=FG_ERROR, highlightthickness=1)
            else:
                r["card"].configure(highlightbackground="#1e2040", highlightthickness=1)

    def _refresh_log_panel(self):
        """Xóa và tải lại right panel theo _selected_novel."""
        self.log_area.configure(state=tk.NORMAL)
        self.log_area.delete("1.0", tk.END)
        items = (self._novel_logs.get(self._selected_novel, [])
                 if self._selected_novel else self._all_logs)
        for text, tag in items:
            self.log_area.insert(tk.END, text + "\n", tag)
        self.log_area.see(tk.END)
        self.log_area.configure(state=tk.DISABLED)

    def _update_right_header(self):
        """Cập nhật tiêu đề panel phải."""
        if hasattr(self, '_right_header_var'):
            if self._selected_novel:
                short = (self._selected_novel if len(self._selected_novel) <= 30
                         else self._selected_novel[:27] + "…")
                self._right_header_var.set(f"LOG — {short}  ·  click để quay lại")
            else:
                self._right_header_var.set("NHẬT KÝ CHI TIẾT  ·  click truyện để lọc")

    def append_novel_log(self, novel_line, text, tag="muted"):
        """Route một dòng log vào buffer truyện tương ứng (thread-safe)."""
        def _do():
            # Lưu vào global buffer
            self._all_logs.append((text, tag))
            # Lưu vào per-novel buffer
            if novel_line in self._novel_logs:
                self._novel_logs[novel_line].append((text, tag))
            # Hiển thị tùy theo lựa chọn
            if self._selected_novel is None or self._selected_novel == novel_line:
                self._append_log_raw(text, tag)
        self.root.after(0, _do)

    def _append_log_raw(self, msg, tag="muted"):
        """Ghi trực tiếp vào text widget, không lưu buffer."""
        try:
            self.log_area.configure(state=tk.NORMAL)
            self.log_area.insert(tk.END, msg + "\n", tag)
            self.log_area.see(tk.END)
            self.log_area.configure(state=tk.DISABLED)
        except Exception:
            pass

    def update_novel_status(self, line, icon, name_text, status_text,
                            icon_color=FG_WARNING, status_color=FG_SECONDARY,
                            progress=None):
        """
        Thread-safe cập nhật card tiến độ truyện.
        progress: 0–100 hoặc None.
        """
        def _do():
            if line not in self._novel_rows:
                return
            r = self._novel_rows[line]
            r["icon"].configure(text=icon, fg=icon_color)
            if name_text:
                short = name_text if len(name_text) <= 28 else name_text[:25] + "…"
                r["name"].configure(text=short, fg=FG_PRIMARY)
            r["status"].configure(text=status_text, fg=status_color)
            # Track state
            r["done"]   = (icon_color == FG_SUCCESS)
            r["failed"] = (icon_color == FG_ERROR)
            if progress is not None:
                pct = max(0, min(100, progress))
                r["pct"].configure(text=f"{pct}%" if pct > 0 else "")
                r["bar_fill"].place(relwidth=pct / 100)
                if pct >= 100 and icon_color == FG_SUCCESS:
                    r["bar_fill"].configure(bg=FG_SUCCESS)
                    r["card"].configure(highlightbackground=FG_SUCCESS)
                elif icon_color == FG_ERROR:
                    r["bar_fill"].configure(bg=FG_ERROR)
                    r["card"].configure(highlightbackground=FG_ERROR)
                else:
                    r["bar_fill"].configure(bg=ACCENT3)
                    if line != self._selected_novel:
                        r["card"].configure(highlightbackground="#1e2040")
        self.root.after(0, _do)

    def update_chapter_progress(self, line, done, total):
        """Cập nhật progress bar theo tỉ lệ chương (thread-safe)."""
        def _do():
            if line not in self._novel_rows:
                return
            r = self._novel_rows[line]
            pct = int(done / total * 100) if total else 0
            r["pct"].configure(text=f"{done}/{total}")
            r["bar_fill"].place(relwidth=pct / 100)
            r["status"].configure(text=f"Đang tải chương… {done}/{total}",
                                  fg=FG_INFO)
        self.root.after(0, _do)

    def set_status(self, text, color=FG_SUCCESS):
        def _do():
            self.status_var.set(text)
            self.status_lbl.configure(fg=color)
        self.root.after(0, _do)

    # ── Settings panel ─────────────────────────────────────────────────────
    def _build_settings_panel(self, parent):
        """Tạo panel cài đặt (ẩn sẵn). Trả về Frame chưa pack."""
        panel = tk.Frame(parent, bg=BG_CARD,
                         highlightbackground=ACCENT2, highlightthickness=1)

        # ── Header ──
        hdr = tk.Frame(panel, bg=ACCENT2)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="⚙  Cài đặt nâng cao",
                 font=("Segoe UI", 10, "bold"), fg=FG_PRIMARY, bg=ACCENT2,
                 padx=14, pady=6).pack(side=tk.LEFT)
        tk.Label(hdr, text="Thay đổi sẽ có hiệu lực ngay sau khi lưu",
                 font=("Segoe UI", 8), fg="#ccccdd", bg=ACCENT2,
                 padx=6).pack(side=tk.LEFT)

        # ── Grid of settings ──
        grid = tk.Frame(panel, bg=BG_CARD, padx=16, pady=10)
        grid.pack(fill=tk.X)

        fields = [
            ("SLEEPTIME",         "⏱  Sleep Time (giây)",          str(SLEEPTIME),        "Chờ N giây khi server báo lỗi (4xx/5xx). Không ảnh hưởng tốc độ tải bình thường."),
            ("DELAY_MIN",         "⏳  Thời gian Delay tối thiểu", str(DELAY_MIN),        "Delay tối thiểu (giây) giữa các luồng tải để tránh Cloudflare block."),
            ("DELAY_MAX",         "⏳  Thời gian Delay tối đa",    str(DELAY_MAX),        "Delay tối đa (giây). Kịch bản sẽ lấy ngẫu nhiên giữa Min và Max."),
            ("LINE_SIZE",         "📏  Line Size",                   str(LINE_SIZE),         "Độ rộng dòng văn bản tối đa"),
            ("THREAD_NUM",        "🧵  Số luồng tải chương",         str(THREAD_NUM),        "Số thread tải chương song song (khuyến nghị: 4–16)"),
            ("DEFAULT_URLS",      "🌐  URL gốc mặc định",            DEFAULT_URLS,           "Domain mặc định khi dùng ID thay vì link đầy đủ"),
            ("DEFAULT_SAVE_FOLDER","💾  Thư mục lưu mặc định",       DEFAULT_SAVE_FOLDER,    "Thư mục lưu file EPUB đầu ra"),
        ]

        for row_i, (key, label_text, default, tooltip) in enumerate(fields):
            var = tk.StringVar(value=default)
            self._svar[key] = var

            # Label
            lbl = tk.Label(grid, text=label_text,
                           font=("Segoe UI", 9, "bold"), fg=FG_PRIMARY, bg=BG_CARD,
                           anchor=tk.W, width=28)
            lbl.grid(row=row_i, column=0, sticky=tk.W, pady=4)

            # Entry
            ent_frame = tk.Frame(grid, bg=ACCENT2, padx=1, pady=1)
            ent_frame.grid(row=row_i, column=1, sticky=tk.EW, padx=(8, 0), pady=4)
            ent = tk.Entry(ent_frame, textvariable=var,
                           font=("Consolas", 10), bg=BG_INPUT, fg=FG_PRIMARY,
                           insertbackground=ACCENT3, relief=tk.FLAT,
                           width=36)
            ent.pack(fill=tk.X, padx=4, pady=3)
            ent._key = key

            # Tooltip hint
            tip = tk.Label(grid, text=tooltip,
                           font=("Segoe UI", 7), fg=FG_SECONDARY, bg=BG_CARD,
                           anchor=tk.W)
            tip.grid(row=row_i, column=2, sticky=tk.W, padx=(10, 0))

        grid.columnconfigure(1, weight=1)

        # ── Buttons row ──
        btn_row = tk.Frame(panel, bg=BG_CARD, padx=16)
        btn_row.pack(fill=tk.X, pady=(0, 6))

        save_btn = self._make_button(
            btn_row, "💾  Lưu cài đặt", self._apply_settings,
            ACCENT, "#c0392b", font=("Segoe UI", 9, "bold"), padx=16, pady=5)
        save_btn.pack(side=tk.LEFT)

        reset_btn = self._make_button(
            btn_row, "↺  Mặc định", self._reset_settings,
            "#252540", "#353560", font=("Segoe UI", 9), padx=12, pady=5)
        reset_btn.pack(side=tk.LEFT, padx=(8, 0))

        # ── Dòng phân cách ──
        tk.Frame(panel, bg="#1e1e40", height=1).pack(fill=tk.X, padx=16, pady=(4, 0))

        # ── Khu vực đăng nhập Hako ──
        login_area = tk.Frame(panel, bg=BG_CARD, padx=16)
        login_area.pack(fill=tk.X, pady=(6, 10))

        # Label tiêu đề
        login_hdr = tk.Frame(login_area, bg=BG_CARD)
        login_hdr.pack(fill=tk.X, pady=(0, 6))
        tk.Frame(login_hdr, bg="#f39c12", width=3).pack(side=tk.LEFT, fill=tk.Y, padx=(0, 7))
        tk.Label(login_hdr, text="TÀI KHOẢN HAKO",
                 font=("Segoe UI", 8, "bold"), fg="#f39c12", bg=BG_CARD
                 ).pack(side=tk.LEFT)
        tk.Label(login_hdr,
                 text="  Dùng để tải truyện bị ẩn mà bạn là quản lý",
                 font=("Segoe UI", 8), fg=FG_SECONDARY, bg=BG_CARD
                 ).pack(side=tk.LEFT)

        # Row: trạng thái + nút
        login_row = tk.Frame(login_area, bg=BG_CARD)
        login_row.pack(fill=tk.X)

        # Badge trạng thái đăng nhập
        init_logged = bool(SESSION_COOKIES.get('ln_session'))
        self._login_status_text = tk.StringVar(
            value=("●  Đã đăng nhập" if init_logged else "○  Chưa đăng nhập"))
        self._login_status_color = FG_SUCCESS if init_logged else FG_SECONDARY
        self._login_status_lbl = tk.Label(
            login_row, textvariable=self._login_status_text,
            font=("Segoe UI", 9, "bold"),
            fg=self._login_status_color, bg=BG_CARD)
        self._login_status_lbl.pack(side=tk.LEFT, padx=(0, 14))

        login_btn = self._make_button(
            login_row, "🔑  Đăng nhập", self._open_login_dialog,
            "#1a4a1a", "#256625", font=("Segoe UI", 9, "bold"), padx=14, pady=5)
        login_btn.pack(side=tk.LEFT)

        logout_btn = self._make_button(
            login_row, "🚪  Đăng xuất", self._do_logout,
            "#2a1a1a", "#4a2020", font=("Segoe UI", 9), padx=12, pady=5)
        logout_btn.pack(side=tk.LEFT, padx=(8, 0))

        return panel

    def _toggle_settings(self):
        """Hiện/ẩn panel cài đặt — toggle cả container để không để lại khoảng trống."""
        gear_lbl = self._get_btn_label(self._gear_btn)
        if self._settings_visible:
            self._settings_panel.pack_forget()
            self._settings_container.pack_forget()
            self._settings_visible = False
            if gear_lbl:
                gear_lbl.configure(text="⚙  Cài đặt")
        else:
            # Chèn container TRƯỚC content pane
            self._settings_container.pack(fill=tk.X, padx=18,
                                          before=self._pane_ref)
            self._settings_panel.pack(fill=tk.X, pady=(4, 8))
            self._settings_visible = True
            if gear_lbl:
                gear_lbl.configure(text="✕  Đóng")

    def _apply_settings(self):
        """Áp dụng giá trị từ settings panel vào các biến global."""
        global SLEEPTIME, LINE_SIZE, THREAD_NUM, DEFAULT_URLS, DEFAULT_SAVE_FOLDER, DELAY_MIN, DELAY_MAX
        errors = []
        try:
            SLEEPTIME = int(self._svar["SLEEPTIME"].get())
        except ValueError:
            errors.append("SLEEPTIME phải là số nguyên")
        try:
            DELAY_MIN = float(self._svar["DELAY_MIN"].get())
        except ValueError:
            errors.append("DELAY_MIN phải là số thực")
        try:
            DELAY_MAX = float(self._svar["DELAY_MAX"].get())
        except ValueError:
            errors.append("DELAY_MAX phải là số thực")
        try:
            LINE_SIZE = int(self._svar["LINE_SIZE"].get())
        except ValueError:
            errors.append("LINE_SIZE phải là số nguyên")
        try:
            THREAD_NUM = int(self._svar["THREAD_NUM"].get())
        except ValueError:
            errors.append("THREAD_NUM phải là số nguyên")
        DEFAULT_URLS = self._svar["DEFAULT_URLS"].get().strip().rstrip("/")
        DEFAULT_SAVE_FOLDER = self._svar["DEFAULT_SAVE_FOLDER"].get().strip()

        if errors:
            self._append_log("⚠  Lỗi lưu cài đặt: " + " | ".join(errors), "warning")
        else:
            try:
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump({
                        "SLEEPTIME": SLEEPTIME,
                        "DELAY_MIN": DELAY_MIN,
                        "DELAY_MAX": DELAY_MAX,
                        "LINE_SIZE": LINE_SIZE,
                        "THREAD_NUM": THREAD_NUM,
                        "DEFAULT_URLS": DEFAULT_URLS,
                        "DEFAULT_SAVE_FOLDER": DEFAULT_SAVE_FOLDER
                    }, f, indent=4)
            except Exception as e:
                self._append_log(f"⚠  Lỗi trạng thái khi ghi tệp cài đặt: {e}", "warning")

            self._append_log(
                f"✅  Đã lưu toàn thủ công: Sleep={SLEEPTIME}s · Delay={DELAY_MIN}-{DELAY_MAX}s · "
                f"Threads={THREAD_NUM} · Folder='{DEFAULT_SAVE_FOLDER}'",
                "success"
            )

    def _reset_settings(self):
        """Khôi phục giá trị mặc định ban đầu vào entries."""
        defaults = {
            "SLEEPTIME":          "30",
            "DELAY_MIN":          "2.0",
            "DELAY_MAX":          "3.0",
            "LINE_SIZE":          "80",
            "THREAD_NUM":         "8",
            "DEFAULT_URLS":       "https://docln.sbs",
            "DEFAULT_SAVE_FOLDER":"raw",
        }
        for k, v in defaults.items():
            if k in self._svar:
                self._svar[k].set(v)
        self._append_log("↺  Đã khôi phục thông số chuẩn. Hãy nhấn 'Lưu cài đặt' để áp dụng.", "info")

    # ── Login dialog ────────────────────────────────────────────────────────
    def _open_login_dialog(self):
        """Mở cửa sổ đăng nhập Hako — hỗ trợ tự động và thủ công."""
        import webbrowser

        dlg = tk.Toplevel(self.root)
        dlg.title("Đăng nhập Hako")
        dlg.configure(bg=BG_DARK)
        dlg.resizable(False, True)
        dlg.grab_set()

        w, h = 500, 380
        sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
        dlg.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # ── Header ──
        hdr = tk.Frame(dlg, bg=ACCENT2)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🔑  Đăng nhập tài khoản Hako",
                 font=("Segoe UI", 11, "bold"), fg=FG_PRIMARY, bg=ACCENT2,
                 padx=16, pady=10).pack(side=tk.LEFT)

        # ── Tab bar ──
        tab_bar = tk.Frame(dlg, bg="#0a0a18")
        tab_bar.pack(fill=tk.X)

        tab_auto_lbl   = tk.Label(tab_bar, text="⚡  Tự động",   font=("Segoe UI", 9, "bold"),
                                  fg=FG_PRIMARY, bg=ACCENT2, padx=18, pady=6, cursor="hand2")
        tab_manual_lbl = tk.Label(tab_bar, text="✏  Nhập tay",  font=("Segoe UI", 9),
                                  fg=FG_SECONDARY, bg="#0a0a18", padx=18, pady=6, cursor="hand2")
        tab_auto_lbl.pack(side=tk.LEFT)
        tab_manual_lbl.pack(side=tk.LEFT)

        # ── Shared status bar ──
        msg_var = tk.StringVar()
        msg_lbl = tk.Label(dlg, textvariable=msg_var,
                           font=("Segoe UI", 8, "bold"), fg=FG_ERROR, bg=BG_DARK,
                           anchor=tk.W, wraplength=460, padx=20)
        msg_lbl.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 4))

        btn_bar = tk.Frame(dlg, bg=BG_DARK, padx=20, pady=8)
        btn_bar.pack(fill=tk.X, side=tk.BOTTOM)

        body = tk.Frame(dlg, bg=BG_DARK)
        body.pack(fill=tk.BOTH, expand=True)

        # ─────────────────────────────────────────
        # Pane TỰ ĐỘNG
        # ─────────────────────────────────────────
        pane_auto = tk.Frame(body, bg=BG_DARK, padx=24, pady=14)

        steps = [
            ("1", "Nhấn  \"🌐 Mở trang đăng nhập\"  — trang Hako mở trong trình duyệt"),
            ("2", "Đăng nhập bình thường (Chrome / Edge / Firefox) — KHÔNG cần đóng trình duyệt"),
            ("3", "Quay lại đây và nhấn  \"✔ Đã đăng nhập xong\""),
        ]
        for num, txt in steps:
            row = tk.Frame(pane_auto, bg=BG_DARK)
            row.pack(fill=tk.X, pady=4)
            tk.Label(row, text=num, font=("Segoe UI", 9, "bold"),
                     fg=BG_DARK, bg=ACCENT3, width=2, padx=4, pady=2).pack(side=tk.LEFT)
            tk.Label(row, text=f"  {txt}", font=("Segoe UI", 9),
                     fg=FG_PRIMARY, bg=BG_DARK, anchor=tk.W,
                     wraplength=420).pack(side=tk.LEFT, fill=tk.X, expand=True)

        note = tk.Label(pane_auto,
                        text="⚠  Nếu không lấy được cookie tự động, hãy dùng tab  ✏ Nhập tay",
                        font=("Segoe UI", 8), fg=FG_WARNING, bg=BG_DARK, anchor=tk.W)
        note.pack(fill=tk.X, pady=(10, 0))

        # ─────────────────────────────────────────
        # Pane NHẬP TAY
        # ─────────────────────────────────────────
        pane_manual = tk.Frame(body, bg=BG_DARK, padx=24, pady=14)

        guide_steps = [
            ("1", "Mở ln.hako.vn, đăng nhập, nhấn F12 → tab Application"),
            ("2", "Chọn Storage → Cookies → https://ln.hako.vn"),
            ("3", "Tìm dòng  ln_session  → copy toàn bộ cột Value"),
            ("4", "Paste vào ô bên dưới rồi nhấn  \"💾 Lưu cookie\""),
        ]
        for num, txt in guide_steps:
            row = tk.Frame(pane_manual, bg=BG_DARK)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=num, font=("Segoe UI", 9, "bold"),
                     fg=BG_DARK, bg="#f39c12", width=2, padx=4, pady=2).pack(side=tk.LEFT)
            tk.Label(row, text=f"  {txt}", font=("Segoe UI", 9),
                     fg=FG_PRIMARY, bg=BG_DARK, anchor=tk.W,
                     wraplength=420).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(pane_manual, text="Giá trị ln_session:",
                 font=("Segoe UI", 9, "bold"), fg=FG_PRIMARY, bg=BG_DARK,
                 anchor=tk.W).pack(fill=tk.X, pady=(10, 2))

        inp_frame = tk.Frame(pane_manual, bg=ACCENT2, padx=1, pady=1)
        inp_frame.pack(fill=tk.X)
        cookie_var = tk.StringVar()
        cookie_ent = tk.Entry(inp_frame, textvariable=cookie_var,
                              font=("Consolas", 9), bg=BG_INPUT, fg=FG_PRIMARY,
                              insertbackground=ACCENT3, relief=tk.FLAT)
        cookie_ent.pack(fill=tk.X, padx=4, pady=5)

        # ─────────────────────────────────────────
        # Tab switching logic
        # ─────────────────────────────────────────
        current_pane = [pane_auto]

        def _show_auto():
            current_pane[0].pack_forget()
            pane_auto.pack(fill=tk.BOTH, expand=True)
            current_pane[0] = pane_auto
            tab_auto_lbl.configure(bg=ACCENT2, fg=FG_PRIMARY, font=("Segoe UI", 9, "bold"))
            tab_manual_lbl.configure(bg="#0a0a18", fg=FG_SECONDARY, font=("Segoe UI", 9))
            # Swap buttons
            for w in btn_bar.winfo_children(): w.destroy()
            _build_auto_buttons()

        def _show_manual():
            current_pane[0].pack_forget()
            pane_manual.pack(fill=tk.BOTH, expand=True)
            current_pane[0] = pane_manual
            tab_manual_lbl.configure(bg=ACCENT2, fg=FG_PRIMARY, font=("Segoe UI", 9, "bold"))
            tab_auto_lbl.configure(bg="#0a0a18", fg=FG_SECONDARY, font=("Segoe UI", 9))
            for w in btn_bar.winfo_children(): w.destroy()
            _build_manual_buttons()
            cookie_ent.focus_set()

        tab_auto_lbl.bind("<Button-1>",   lambda e: _show_auto())
        tab_manual_lbl.bind("<Button-1>", lambda e: _show_manual())

        # ─────────────────────────────────────────
        # Hàm dùng chung: cập nhật badge sau khi lấy cookie thành công
        # ─────────────────────────────────────────
        def _on_success(source_name):
            if hasattr(self, '_login_status_text'):
                self._login_status_text.set("●  Đã đăng nhập")
                self._login_status_lbl.configure(fg=FG_SUCCESS)
            self._append_log(f"🔑  Đã lấy cookie từ {source_name}.", "success")
            dlg.after(1400, dlg.destroy)

        # ─────────────────────────────────────────
        # Buttons TAB AUTO
        # ─────────────────────────────────────────
        def _build_auto_buttons():
            # Lưu reference proc để terminate
            dlg._chrome_proc = None
            dlg._chrome_tmp_dir = None

            def _open_browser():
                import subprocess, tempfile, os
                
                msg_var.set("⏳  Đang tìm trình duyệt Chrome...")
                msg_lbl.configure(fg=FG_INFO)
                dlg.update()

                LOCALAPP = os.environ.get("LOCALAPPDATA", "")
                CHROME_PATHS = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.join(LOCALAPP, "Google", "Chrome", "Application", "chrome.exe"),
                    # Microsoft Edge (Chromium)
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                    # Brave Browser
                    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                    # Cốc Cốc
                    os.path.join(LOCALAPP, "CocCoc", "Browser", "Application", "browser.exe"),
                ]
                
                chrome_exe = next((p for p in CHROME_PATHS if os.path.isfile(p)), None)
                if not chrome_exe:
                    msg_var.set("❌  Không tìm thấy trình duyệt Chrome trên máy. Hãy dùng tab Nhập tay.")
                    msg_lbl.configure(fg=FG_ERROR)
                    return
                
                # Tạo thư mục profile rỗng để mở Chrome "sạch", không bị dính profile cũ
                dlg._chrome_tmp_dir = tempfile.mkdtemp(prefix="hako_chrome_")
                
                try:
                    dlg._chrome_proc = subprocess.Popen([
                        chrome_exe,
                        "--remote-debugging-port=9223",
                        "--remote-allow-origins=http://127.0.0.1:9223",
                        f"--user-data-dir={dlg._chrome_tmp_dir}",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "https://ln.hako.vn/login"
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    msg_var.set("⏳  Đã mở Chrome mới. Hãy đăng nhập rồi nhấn 'Đã đăng nhập xong'.")
                    msg_lbl.configure(fg=FG_INFO)
                except Exception as e:
                    msg_var.set(f"❌  Lỗi khi mở Chrome: {e}")
                    msg_lbl.configure(fg=FG_ERROR)

            def _grab_auto():
                msg_var.set("⏳  Đang đọc cookie từ trình duyệt...")
                msg_lbl.configure(fg=FG_INFO)
                ok_btn = confirm_ref[0].winfo_children()[0]
                ok_btn.configure(text="⏳  Đang xử lý...", cursor="arrow")
                dlg.update()
                
                def _worker():
                    ok, result = grab_cookies_from_browser(port=9223)
                    
                    def _update():
                        try:
                            if not dlg.winfo_exists():
                                return
                            if ok:
                                msg_var.set(f"✅  Thành công! Đã lấy cookie.")
                                msg_lbl.configure(fg=FG_SUCCESS)
                                _on_success("Chrome (tự động)")
                                # Đóng Chrome
                                if hasattr(dlg, '_chrome_proc') and dlg._chrome_proc:
                                    try:
                                        dlg._chrome_proc.terminate()
                                    except:
                                        pass
                            else:
                                msg_var.set(f"❌  {result}")
                                msg_lbl.configure(fg=FG_ERROR)
                                try:
                                    ok_btn.configure(text="✔  Đã đăng nhập xong", cursor="hand2")
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    dlg.after(0, _update)
                    
                import threading as _t
                _t.Thread(target=_worker, daemon=True).start()

            confirm_ref = [None]
            self._make_button(btn_bar, "🌐  Mở Chrome tự động", _open_browser,
                              "#0f3460", "#1a4a80",
                              font=("Segoe UI", 9, "bold"), padx=14, pady=7).pack(side=tk.LEFT)
            confirm_ref[0] = self._make_button(btn_bar, "✔  Đã đăng nhập xong", _grab_auto,
                              "#1a5c1a", "#237a23",
                              font=("Segoe UI", 9, "bold"), padx=14, pady=7)
            confirm_ref[0].pack(side=tk.LEFT, padx=(8, 0))
            self._make_button(btn_bar, "Hủy", dlg.destroy,
                              "#252540", "#353560",
                              font=("Segoe UI", 9), padx=12, pady=7).pack(side=tk.LEFT, padx=(8, 0))

        # ─────────────────────────────────────────
        # Buttons TAB NHẬP TAY
        # ─────────────────────────────────────────
        def _build_manual_buttons():
            def _save_manual():
                val = cookie_var.get().strip()
                if not val:
                    msg_var.set("❌  Vui lòng paste giá trị ln_session vào ô trên.")
                    msg_lbl.configure(fg=FG_ERROR)
                    return
                global SESSION_COOKIES
                SESSION_COOKIES['ln_session'] = val
                # Lưu file
                try:
                    existing = {}
                    if isfile(COOKIES_FILE):
                        with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                            existing = json.load(f)
                    existing['ln_session'] = val
                    with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                        json.dump(existing, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass
                try:
                    if hasattr(_tls, 'scraper'):
                        _tls.scraper.cookies.update(SESSION_COOKIES)
                except Exception:
                    pass
                msg_var.set("✅  Đã lưu cookie ln_session thành công!")
                msg_lbl.configure(fg=FG_SUCCESS)
                _on_success("nhập tay")

            self._make_button(btn_bar, "💾  Lưu cookie", _save_manual,
                              "#1a5c1a", "#237a23",
                              font=("Segoe UI", 9, "bold"), padx=14, pady=7).pack(side=tk.LEFT)
        def _close_dlg():
            try:
                if hasattr(dlg, '_chrome_proc') and dlg._chrome_proc:
                    dlg._chrome_proc.terminate()
            except Exception:
                pass
            try:
                if hasattr(dlg, '_chrome_tmp_dir') and dlg._chrome_tmp_dir:
                    import shutil
                    shutil.rmtree(dlg._chrome_tmp_dir, ignore_errors=True)
            except Exception:
                pass
            dlg.destroy()

        self._make_button(btn_bar, "Hủy", _close_dlg,
                          "#252540", "#353560",
                          font=("Segoe UI", 9), padx=12, pady=7).pack(side=tk.LEFT, padx=(8, 0))
        dlg.bind("<Return>", lambda e: _save_manual())

        # Hiện pane auto mặc định
        pane_auto.pack(fill=tk.BOTH, expand=True)
        _build_auto_buttons()
        dlg.bind("<Escape>", lambda e: _close_dlg())
        dlg.protocol("WM_DELETE_WINDOW", _close_dlg)

    def _do_logout(self):
        """Xóa cookie phiên đăng nhập."""
        global SESSION_COOKIES
        SESSION_COOKIES = {}
        # Xóa file cookies.json
        try:
            import os
            if isfile(COOKIES_FILE):
                os.remove(COOKIES_FILE)
        except Exception:
            pass
        # Reset scraper threads
        try:
            if hasattr(_tls, 'scraper'):
                del _tls.scraper
        except Exception:
            pass
        # Cập nhật badge
        if hasattr(self, '_login_status_text'):
            self._login_status_text.set("○  Chưa đăng nhập")
            self._login_status_lbl.configure(fg=FG_SECONDARY)
        self._append_log("🚪  Đã đăng xuất khỏi Hako.", "info")

    # ── Start download (called from button) ────────────────────────────────
    def _start_download(self):
        if self._is_downloading:
            return
        val = "" if self._placeholder_active else self.text_area.get("1.0", tk.END).strip()
        if not val:
            self._append_log("⚠  Bạn chưa nhập ID hoặc link!", "warning")
            return
        lines = [l.strip() for l in val.split("\n") if l.strip()]
        if not lines:
            self._append_log("⚠  Danh sách trống!", "warning")
            return

        self._is_downloading = True
        self._lock_buttons()
        self.text_area.configure(state=tk.DISABLED)
        self._init_progress_rows(lines)
        self.set_status("⬤  Đang tải…", FG_WARNING)

        # Chạy engine trong background thread
        t = threading.Thread(target=self._run_engine, args=(lines,), daemon=True)
        t.start()

    def _run_engine(self, lines):
        """Được gọi từ background thread."""
        if self._engine:
            self._engine.run_with_app(lines, self)
        # Khi xong, cập nhật UI trở lại main thread
        self.root.after(0, self._on_download_done)

    def _on_download_done(self):
        self._is_downloading = False
        self._unlock_buttons()
        self.text_area.configure(state=tk.NORMAL)
        self.set_status("⬤  Hoàn tất", FG_SUCCESS)
        self._append_log("─" * 72, "muted")
        self._append_log("✅  Đã hoàn thành tất cả!", "success")


class _LogRedirector:
    """Chuyển hướng stdout → log Text widget + per-novel buffer."""
    _RULES = [
        (("✅", "Hoàn thành", "✓ Image", "thành công", "Hoàn tất"), "success"),
        (("Error", "Lỗi", "✗", "Failed", "lỗi", "Không tìm thấy"),  "error"),
        (("retrying", "Warning", "Status 4", "Status 5"),            "warning"),
        (("Bắt đầu", "Đã kết nối", "BẮT ĐẦU"),                      "info"),
        (("Đang tải chương", "chap_", "Found", "Loading image"),     "chapter"),
        (("─", "----"),                                               "muted"),
    ]

    def __init__(self, widget, root, app=None):
        self.widget = widget
        self.root   = root
        self.app    = app
        self._buf   = ""
        self._lock  = threading.Lock()

    def write(self, text):
        with self._lock:
            self._buf += text
            lines_to_send = []
            while "\n" in self._buf:
                line, self._buf = self._buf.split("\n", 1)
                lines_to_send.append((line, getattr(_tls, 'novel_line', None)))
        for line, novel_line in lines_to_send:
            self.root.after(0, self._append, line, novel_line)

    def _append(self, line, novel_line=None):
        if not line.strip():
            return
        # Lọc từng bản cập nhật tqdm (dòng có \r hoặc chỉ chứa |█%)
        if line.startswith('\r') or ('%|' in line and 'it/s' in line):
            return
        tag = "muted"
        for keywords, t in self._RULES:
            if any(k in line for k in keywords):
                tag = t
                break
        if self.app and novel_line:
            # Route vào per-novel buffer
            self.app.append_novel_log(novel_line, line, tag)
        elif self.app:
            # Log toàn cục (không gắn truyện nào)
            self.app._all_logs.append((line, tag))
            if self.app._selected_novel is None:
                try:
                    self.widget.configure(state=tk.NORMAL)
                    self.widget.insert(tk.END, line + "\n", tag)
                    self.widget.see(tk.END)
                    self.widget.configure(state=tk.DISABLED)
                except Exception:
                    pass
        else:
            try:
                self.widget.configure(state=tk.NORMAL)
                self.widget.insert(tk.END, line + "\n", tag)
                self.widget.see(tk.END)
                self.widget.configure(state=tk.DISABLED)
            except Exception:
                pass

    def flush(self):
        pass


class UIManager:
    _app: 'HakoApp | None' = None

    @staticmethod
    def boot(engine):
        """Khởi động app window — block cho tới khi đóng cửa sổ."""
        UIManager._app = HakoApp(engine_ref=engine)

    @staticmethod
    def show_error(title, message):
        root = tk.Tk(); root.withdraw(); root.configure(bg=BG_DARK)
        messagebox.showerror(title, message); root.destroy()

    @staticmethod
    def show_info(title, message):
        root = tk.Tk(); root.withdraw(); root.configure(bg=BG_DARK)
        messagebox.showinfo(title, message); root.destroy()


class Utils:
    @staticmethod
    def re_url(ln_url, url):
        # Hỗ trợ URL chứa /truyen/ hoặc /ai-dich/
        if 'ln.hako.vn/truyen/' in ln_url:
            return 'https://ln.hako.vn' + url
        elif 'docln.net/truyen/' in ln_url:
            return 'https://docln.net' + url
        elif 'docln.net/ai-dich/' in ln_url: 
            return 'https://docln.net' + url 
        elif 'docln.sbs/truyen/' in ln_url:
            return 'https://docln.sbs' + url
        elif 'docln.sbs/ai-dich/' in ln_url: 
            return 'https://docln.sbs' + url 
        else:
            # Tự động thêm http nếu url tương đối bắt đầu bằng //
            if url.startswith('//'):
                return 'https:' + url
            # Thêm xử lý cho các trường hợp link đã là tuyệt đối
            if url.startswith('http'):
                return url
            return url

    @staticmethod
    def format_text(text):
        return text.strip().replace('\n', '')

    @staticmethod
    def format_filename(name):
        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for c in invalid_chars:
            name = name.replace(c, '')
        if len(name) > 180:
            name = name[:180]
        return name.strip()

    @staticmethod
    def get_image(image_url):
        """
        Tải ảnh từ URL, hỗ trợ nhiều domain và đuôi file khác nhau.
        """
        # Xử lý URL imgur không có đuôi file
        if 'imgur.com' in image_url and '.' not in image_url[-5:]:
            image_url += '.jpg'
        
        # Đảm bảo URL có protocol
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        
        try:
            # Thêm headers tốt hơn để tải ảnh từ nhiều nguồn
            img_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
                'Referer': 'https://docln.sbs/'
            }
            
            import requests
            req = requests.get(image_url, stream=True, headers=img_headers, timeout=30)
            if req.status_code == 200:
                image = Image.open(BytesIO(req.content)).convert('RGB')
                return image
            else:
                print(f'Can not get image (status {req.status_code}):', image_url)
                return None
        except Exception as e:
            print(f'Can not get image: {image_url} - Error: {e}')
            return None


class Volume:
    def __init__(self, volume_url='', soup=None):
        self.url = volume_url
        self.name = ''
        self.cover_img = ''
        self.num_chapter = 0
        self.chapter_list = {}
        self.soup = soup
        self.get_volume_info()

    def get_volume_info(self):
        if not self.soup:
            return
        vol_name_span = self.soup.find('span', 'volume-name')
        if vol_name_span:
            vol_name_a = vol_name_span.find('a')
            if vol_name_a:
                self.name = Utils.format_text(vol_name_a.text)
            else:
                self.name = Utils.format_text(vol_name_span.text)
        cover_div = self.soup.find('div', 'series-cover')
        if cover_div:
            style_attr = cover_div.find('div', 'img-in-ratio').get('style', '')
            found = re.findall(r"url\(['\"]?(.*?)['\"]?\)", style_attr)
            if found:
                self.cover_img = found[0]
        ul = self.soup.find('ul', 'list-chapters')
        if ul:
            chapter_li = ul.find_all('li')
            self.num_chapter = len(chapter_li)
            for li in chapter_li:
                a = li.find('a')
                if a:
                    chap_name = Utils.format_text(a.text)
                    chap_url = Utils.re_url(self.url, a.get('href'))
                    self.chapter_list[chap_name] = chap_url


class LNInfo:
    def __init__(self):
        self.name = ''
        self.other_names = []  # Tên khác
        self.url = ''
        self.num_vol = 0
        self.series_info = ''
        self.author = ''
        self.illustrator = ''  # Minh họa
        self.translator = ''  # Người dịch/đăng
        self.translation_group = ''  # Nhóm dịch
        self.summary = ''
        self.fact_item = ''
        self.volume_list = []

    def get_info_from_soup(self, ln_url, soup):
        self.url = ln_url
        
        # Lấy tên truyện
        name_tag = soup.find('span', 'series-name')
        if name_tag:
            self.name = Utils.format_text(name_tag.text)
        
        # Lấy tên khác từ info-item có label "Tên khác"
        info_items_all = soup.find_all('div', 'info-item')
        for item in info_items_all:
            label = item.find('span', 'info-name')
            if label and 'tên khác' in label.get_text().lower():
                value_span = item.find('span', 'info-value')
                if value_span:
                    self.other_names = [Utils.format_text(value_span.text)]
        
        # Lấy thông tin series từ series-information
        series_info_div = soup.find('div', 'series-information')
        if series_info_div:
            self.series_info = str(series_info_div)
            info_items = series_info_div.find_all('div', 'info-item')
            
            for item in info_items:
                # Lấy label (đầu tiêu đề) của mỗi info-item
                label = item.find('span', 'info-name')
                if not label:
                    label_text = item.get_text().lower()
                else:
                    label_text = label.get_text().lower()
                
                # Lấy giá trị
                value_tag = item.find('a') or item.find('span', 'info-value')
                if value_tag:
                    value = Utils.format_text(value_tag.text)
                else:
                    # Lấy text sau dấu :
                    text = item.get_text()
                    if ':' in text:
                        value = text.split(':', 1)[1].strip()
                    else:
                        value = ''
                
                # Phân loại thông tin
                if 'tác giả' in label_text or 'author' in label_text:
                    self.author = value
                elif 'minh họa' in label_text or 'illustrator' in label_text or 'họa sĩ' in label_text:
                    self.illustrator = value
        
        # Lấy người dịch/người đăng từ sidebar (.series-owner_name)
        owner_section = soup.find('div', 'series-owner-title')
        if owner_section:
            owner_link = owner_section.find('a', href=re.compile(r'/thanh-vien/'))
            if owner_link:
                self.translator = Utils.format_text(owner_link.text)
        
        # Lấy nhóm dịch từ sidebar (.fantrans-section)
        fantrans_section = soup.find('div', 'fantrans-section')
        if fantrans_section:
            group_value = fantrans_section.find('div', 'fantrans-value')
            if group_value:
                group_link = group_value.find('a')
                if group_link:
                    self.translation_group = Utils.format_text(group_link.text)
        
        # Lấy tóm tắt
        summary_div = soup.find('div', 'summary-content')
        if summary_div:
            self.summary = str(summary_div)
        
        # Lấy fact item
        fact_div = soup.find('div', 'fact-item')
        if fact_div:
            self.fact_item = str(fact_div)
        
        # Lấy danh sách volumes
        volume_sections = soup.find_all('section', 'volume-list')
        self.num_vol = len(volume_sections)
        for vs in volume_sections:
            vol_url = ''
            vol_cover_div = vs.find('div', 'volume-cover')
            if vol_cover_div:
                link_cover = vol_cover_div.find('a')
                if link_cover:
                    vol_url = Utils.re_url(self.url, link_cover.get('href'))
            
            # Nếu không tìm thấy link cover (ví dụ truyện bị ẩn/fake soup) thì tự fake 1 url để tránh lỗi
            if not vol_url:
                vol_url = self.url
                
            # Không cần tải lại volume nếu dùng fake_soup từ manage, truyền thẳng vs (volume_section) để parse
            vol_soup = BeautifulSoup(str(vs), bs4_html_parser)
            volume_obj = Volume(vol_url, vol_soup)
            self.volume_list.append(volume_obj)


# CSS cho phong cách đọc Light Novel
LN_READING_CSS = """
@page {
    margin: 1em;
}

body {
    font-family: "Times New Roman", "Noto Serif", "Source Han Serif", Georgia, serif;
    font-size: 1em;
    line-height: 1.8;
    text-align: justify;
    margin: 0;
    padding: 0 0.5em;
}

p {
    text-indent: 1.5em;
    margin: 0.8em 0;
}

/* Đoạn văn đầu tiên sau heading không thụt đầu dòng */
h1 + p, h2 + p, h3 + p, h4 + p {
    text-indent: 0;
}

h1, h2, h3, h4 {
    font-family: "Times New Roman", "Noto Serif", Georgia, serif;
    text-align: center;
    margin: 1.5em 0 1em 0;
    line-height: 1.4;
}

h1 {
    font-size: 1.8em;
    margin-top: 2em;
}

h2 {
    font-size: 1.5em;
}

h3 {
    font-size: 1.3em;
}

h4 {
    font-size: 1.2em;
    font-weight: bold;
}

/* Scene break - dấu phân cách cảnh */
.scene-break {
    text-align: center;
    margin: 2em 0;
    font-size: 1.2em;
    letter-spacing: 0.5em;
}

/* Hình ảnh */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
}

/* Ghi chú */
.note {
    font-size: 0.9em;
    font-style: italic;
    color: #555;
}

/* Căn giữa cho intro */
.intro-content {
    text-align: center;
}

.intro-content h1 {
    margin-top: 3em;
}

/* Thông tin truyện */
.novel-info {
    margin: 2em auto;
    text-align: left;
    max-width: 80%;
    padding: 1em;
    border-top: 1px solid #ccc;
    border-bottom: 1px solid #ccc;
}

.novel-info .info-line {
    text-indent: 0;
    margin: 0.5em 0;
    font-size: 0.95em;
}

.novel-info .info-line strong {
    color: #333;
}
"""


class EpubEngine:
    def __init__(self):
        self.book = None
        self.ln = None
        self.volume = None
        self.volume_index = 0
        self.ln_info_json_file = 'ln_info.json'
        self._app_ref = None      # HakoApp reference (set by Engine)
        self._novel_line = None   # line key for progress (set by Engine)

    def volume_title_for_metadata(self, vol_name, volume_index):
        """
        Luôn trả về tên volume gốc, không loại bỏ tiền tố.
        Do đó metadata và tên file sẽ là: "[Tên Truyện] - [Tên Tập]"
        """
        return vol_name.strip()

    def create_epub(self, ln, selected_volumes=None):
        self.ln = ln
        vol_map = {v.name: v for v in ln.volume_list}
        if not selected_volumes or "Tất cả" in selected_volumes:
            volumes_to_do = ln.volume_list
        else:
            volumes_to_do = [vol_map[name] for name in selected_volumes if name in vol_map]
        for idx, vol in enumerate(volumes_to_do, start=1):
            print("\n------------------------------------------\n")
            self.volume_index = idx
            self.volume = vol
            self.book = epub.EpubBook()
            self.bind_epub_book()
        self.save_json(ln)

    def bind_epub_book(self):
        # Thêm CSS styling
        style_item = epub.EpubItem(
            uid="style",
            file_name="style/main.css",
            media_type="text/css",
            content=LN_READING_CSS
        )
        self.book.add_item(style_item)
        
        intro_page = self.make_intro_page()
        self.book.add_item(intro_page)
        try:
            if self.volume.cover_img:
                req = check_available_request(self.volume.cover_img, steam=True)
                self.book.set_cover('cover.jpeg', req.content)
        except Exception:
            print("Error: Can't set cover image")
        self.book.spine = ['cover', intro_page, 'nav']
        self.make_chapter(app=self._app_ref, novel_line=self._novel_line)
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())
        final_vol_title = self.volume_title_for_metadata(self.volume.name, self.volume_index)
        if final_vol_title:
            title_metadata = f"{self.ln.name} - {final_vol_title}"
        else:
            title_metadata = f"{self.ln.name}"
        self.set_metadata(title_metadata, self.ln.author)
        # Xác định thư mục lưu theo DEFAULT_SAVE_FOLDER
        save_root = DEFAULT_SAVE_FOLDER.strip()
        novel_subfolder = Utils.format_filename(self.ln.name)
        if save_root:
            if not isdir(save_root):
                mkdir(save_root)
            epub_folder = join(save_root, novel_subfolder)
        else:
            epub_folder = novel_subfolder
        if not isdir(epub_folder):
            mkdir(epub_folder)
        # Tên file chỉ dùng tên tập (không có tên truyện)
        file_title = Utils.format_filename(final_vol_title) if final_vol_title else Utils.format_filename(self.ln.name)
        epub_file_name = file_title + ".epub"
        epub_path = join(epub_folder, epub_file_name)
        try:
            epub.write_epub(epub_path, self.book, {})
            print(f"✅ Đã tạo file EPUB: {epub_file_name}", end="\n")
        except Exception:
            print("Error: Can not write epub file!")

    def make_intro_page(self):
        # Xây dựng thông tin chi tiết
        info_lines = []
        
        # Tên khác
        if self.ln.other_names:
            other_names_str = ', '.join(self.ln.other_names)
            info_lines.append(f'<p class="info-line"><strong>Tên khác:</strong> {other_names_str}</p>')
        
        # Tác giả
        if self.ln.author:
            info_lines.append(f'<p class="info-line"><strong>Tác giả:</strong> {self.ln.author}</p>')
        
        # Minh họa
        if self.ln.illustrator:
            info_lines.append(f'<p class="info-line"><strong>Minh họa:</strong> {self.ln.illustrator}</p>')
        
        # Người dịch
        if self.ln.translator:
            info_lines.append(f'<p class="info-line"><strong>Người dịch:</strong> {self.ln.translator}</p>')
        
        # Nhóm dịch
        if self.ln.translation_group:
            info_lines.append(f'<p class="info-line"><strong>Nhóm dịch:</strong> {self.ln.translation_group}</p>')
        
        info_html = '\n            '.join(info_lines)
        
        content_html = f"""
        <html>
        <head>
            <link rel="stylesheet" type="text/css" href="style/main.css"/>
        </head>
        <body>
        <div class="intro-content">
            <h1>{self.ln.name}</h1>
            <h3>{self.volume.name}</h3>
            <div class="novel-info">
            {info_html}
            </div>
            {self.ln.summary}
        </div>
        </body>
        </html>
        """
        intro_page = epub.EpubHtml(uid='intro', file_name='intro.xhtml', title='Intro', content=content_html)
        intro_page.add_link(href='style/main.css', rel='stylesheet', type='text/css')
        return intro_page

    def set_metadata(self, title, author, lang='vi'):
        self.book.set_title(title)
        self.book.set_language(lang)
        self.book.add_author(author)

    def make_chapter(self, i=0, app=None, novel_line=None):
        chapter_urls_index = []
        for i, chapter_name in enumerate(self.volume.chapter_list.keys(), start=i):
            chapter_urls_index.append((i, chapter_name, self.volume.chapter_list[chapter_name]))
        total = len(chapter_urls_index)
        done_count = [0]  # mảng 1 phần tử để có thể sửa trong closure
        done_lock  = threading.Lock()

        def _wrapped(chap_data):
            result = self.make_chapter_content(chap_data)
            with done_lock:
                done_count[0] += 1
                n = done_count[0]
            print(f"Đang tải chương: {n}/{total}")
            if app and novel_line:
                app.update_chapter_progress(novel_line, n, total)
            return result

        pool = ThreadPool(THREAD_NUM)
        contents = []
        try:
            contents = list(pool.imap_unordered(_wrapped, chapter_urls_index))
            contents.sort(key=lambda x: x[0])
            contents = [c[1] for c in contents]
        except Exception:
            pass
        pool.close()
        pool.join()
        for c in contents:
            self.book.add_item(c)
            self.book.spine.append(c)
            self.book.toc.append(c)

    def make_chapter_content(self, chap_data):
        i, chap_name, chap_url = chap_data
        try:
            req = check_available_request(chap_url)
            soup = BeautifulSoup(req.text, bs4_html_parser)
            xhtml_file = f"chap_{i+1}.xhtml"
            chapter_title_tag = soup.find('div', 'title-top')
            if chapter_title_tag:
                h4 = chapter_title_tag.find('h4')
                if h4:
                    chap_name = h4.text.strip()
            
            chapter_content_div = soup.find('div', id='chapter-content')
            
            # --- Hỗ trợ tải truyện bị ẩn qua link /edit ---
            if not chapter_content_div and '/edit' in chap_url:
                textarea = soup.find('textarea', id='LN_Chapter_Content')
                if textarea:
                    import html
                    raw_html = textarea.get_text()
                    # HTML parser có sẵn của BeautifulSoup sẽ tự động parse nội dung này
                    fake_html = f'<div id="chapter-content">{raw_html}</div>'
                    chapter_content_div = BeautifulSoup(fake_html, bs4_html_parser).find('div')
                    print(f"        ✓ Lấy thành công nội dung chương bị ẩn qua /edit: {chap_name}")
            # ----------------------------------------------

            if chapter_content_div:
                # --- BẮT ĐẦU: Giải mã nội dung bị mã hóa (JS Anti-copy) ---
                protected_div = chapter_content_div.find('div', id='chapter-c-protected')
                if protected_div:
                    try:
                        import json
                        import base64
                        data_c = json.loads(protected_div.get('data-c', '[]'))
                        data_k = protected_div.get('data-k', '')
                        if data_c and data_k:
                            ordered = sorted(data_c, key=lambda x: int(x[:4]))
                            
                            decrypted_html = ""
                            for chunk in ordered:
                                chunk_data = chunk[4:]
                                # Javascript atob ignores padding, in python we must ensure it's padded
                                chunk_data = chunk_data.replace('=', '')
                                padding = 4 - (len(chunk_data) % 4)
                                if padding and padding != 4:
                                    chunk_data += '=' * padding
                                    
                                decoded = base64.b64decode(chunk_data)
                                
                                # JS resets XOR key index for each chunk!
                                decrypted = bytearray()
                                for j in range(len(decoded)):
                                    decrypted.append(decoded[j] ^ ord(data_k[j % len(data_k)]))
                                
                                decrypted_html += decrypted.decode('utf-8')
                                
                            dec_soup = BeautifulSoup(decrypted_html, bs4_html_parser)
                            protected_div.replace_with(dec_soup)
                    except Exception as e:
                        print(f"        ✗ Lỗi giải mã JS chapter:", e)
                # --- KẾT THÚC: Giải mã nội dung bị mã hóa ---

                # --- BẮT ĐẦU: Xóa banner quảng cáo ---
                banners_to_remove = chapter_content_div.find_all('a', href=re.compile(r"/truyen/\d+"))
                for banner in banners_to_remove:
                    if banner.find('img', src=re.compile("chapter-banners")):
                        banner.decompose()
                # --- KẾT THÚC: Xóa banner quảng cáo ---
                
                # --- BẮT ĐẦU: Xóa social media links ---
                # Tìm và xóa parent div của các link Discord/Facebook
                for a_tag in list(chapter_content_div.find_all('a', href=True)):
                    href = a_tag.get('href', '').lower()
                    if 'hako.vn/discord' in href or 'fb.com' in href or 'discord' in href or 'facebook' in href:
                        # Tìm parent div cao nhất chứa social links
                        current = a_tag
                        container_to_remove = None
                        
                        # Leo lên cây DOM để tìm div container
                        for _ in range(5):  # Tối đa 5 cấp
                            parent = current.parent
                            if parent is None:
                                break
                            if parent.name == 'div':
                                parent_class = parent.get('class', [])
                                if isinstance(parent_class, list):
                                    parent_class_str = ' '.join(parent_class)
                                else:
                                    parent_class_str = str(parent_class)
                                
                                # Nếu là div có class flex hoặc justify-center
                                if 'flex' in parent_class_str or 'justify-center' in parent_class_str:
                                    container_to_remove = parent
                                    break
                            current = parent
                        
                        # Xóa container hoặc thẻ a
                        if container_to_remove:
                            try:
                                container_to_remove.decompose()
                            except:
                                pass
                        else:
                            try:
                                a_tag.decompose()
                            except:
                                pass
                
                # Xóa các đoạn promotional
                for tag in list(chapter_content_div.find_all(['p', 'div', 'span'])):
                    try:
                        text = tag.get_text(strip=True).lower()
                        if 'hãy bình luận để ủng hộ' in text or 'ủng hộ người đăng' in text:
                            tag.decompose()
                    except:
                        pass
                # --- KẾT THÚC: Xóa social media links ---

                # Xử lý nội dung để có cấu trúc đẹp hơn
                processed_content = self.process_chapter_content(chapter_content_div)
                processed_content = self.process_images_in_content(processed_content, chapter_content_div, i+1)
                note_list = self.get_notes(soup)
                processed_content = self.replace_notes(processed_content, note_list)
            else:
                processed_content = ""
            
            # Tạo HTML hoàn chỉnh với CSS
            chapter_html = f"""
            <html>
            <head>
                <link rel="stylesheet" type="text/css" href="style/main.css"/>
            </head>
            <body>
                <h4>{chap_name}</h4>
                {processed_content}
            </body>
            </html>
            """
                
            epub_chap = epub.EpubHtml(uid=str(i+1), title=chap_name, file_name=xhtml_file, content=chapter_html)
            epub_chap.add_link(href='style/main.css', rel='stylesheet', type='text/css')
            return (i, epub_chap)
        except Exception as e:
            print("Error at chapter:", chap_url, e)
            return (i, epub.EpubHtml(uid=str(i+1), title="Error", file_name=f"chap_{i+1}.xhtml", content="<html><body><h1>Error</h1></body></html>"))


    def process_chapter_content(self, chapter_content_div):
        """
        Xử lý nội dung chương để có cấu trúc HTML tốt hơn.
        Chuyển đổi các đoạn văn thành thẻ <p> và xử lý dấu phân cách cảnh.
        """
        # Xóa các đoạn promotional text
        promotional_patterns = [
            'hãy bình luận để ủng hộ',
            'ủng hộ người đăng',
            'bình luận để ủng hộ',
        ]
        
        # Tìm và xóa các thẻ chứa promotional text
        for p_tag in chapter_content_div.find_all(['p', 'div', 'span']):
            text = p_tag.get_text(strip=True).lower()
            for pattern in promotional_patterns:
                if pattern in text:
                    p_tag.decompose()
                    break
        
        # Lấy HTML sau khi đã xóa promotional
        content_html = str(chapter_content_div)
        
        # Xử lý các dấu phân cách cảnh phổ biến trong light novel
        scene_break_patterns = [
            r'<p[^>]*>\s*[*◇◆☆★○●◎△▽▲▼]{3,}\s*</p>',
            r'<p[^>]*>\s*[\*\*\*]+\s*</p>',
        ]
        
        for pattern in scene_break_patterns:
            content_html = re.sub(
                pattern, 
                '<p class="scene-break">◇ ◇ ◇</p>', 
                content_html, 
                flags=re.IGNORECASE
            )
        
        return content_html
    
    def process_images_in_content(self, content, chapter_content_div, chap_id):
        """Xử lý hình ảnh trong nội dung"""
        img_tags = chapter_content_div.find_all('img')
        
        # Các pattern để skip (banner, quảng cáo)
        skip_patterns = [
            'chapter-banners',
            'hako.vn/ln/banner',
            'hako.vip/ln/banner',
            'i.hako.vn/ln/se',  # Series banner
            'i.hako.vip/ln/se',
            'i2.hako.vn/ln/se',
            'i2.hako.vip/ln/se',
        ]
        
        if img_tags:
            print(f"  Found {len(img_tags)} images in chapter {chap_id}")
            for idx, img_tag in enumerate(img_tags):
                img_url = img_tag.get('src')
                if not img_url:
                    # Thử lấy từ data-src (lazy loading)
                    img_url = img_tag.get('data-src') or img_tag.get('data-original')
                    if not img_url:
                        continue
                
                # Kiểm tra xem có phải banner không
                should_skip = False
                for pattern in skip_patterns:
                    if pattern in img_url:
                        should_skip = True
                        break
                
                if should_skip:
                    continue
                    
                try:
                    print(f"    Loading image {idx+1}: {img_url[:60]}...")
                    img = Utils.get_image(img_url)
                    if img:
                        b = BytesIO()
                        img.save(b, 'jpeg')
                        b_img = b.getvalue()
                        img_path = f"images/chapter_{chap_id}/image_{idx}.jpeg"
                        image_item = epub.EpubItem(
                            file_name=img_path,
                            media_type='image/jpeg',
                            content=b_img
                        )
                        self.book.add_item(image_item)
                        
                        # Thay thế URL trong content - xử lý cả dấu ngoặc đơn và kép
                        content = content.replace(f'src="{img_url}"', f'src="{img_path}"')
                        content = content.replace(f"src='{img_url}'", f"src='{img_path}'")
                        content = content.replace(f'src="{img_url}', f'src="{img_path}')
                        print(f"    ✓ Image loaded and added to EPUB")
                    else:
                        print(f"    ✗ Failed to load image")
                except Exception as e:
                    print(f"    ✗ Error loading image: {e}")
        return content

    def get_notes(self, soup):
        notes = {}
        note_div_list = soup.find_all('div', id=re.compile("^note"))
        for div in note_div_list:
            note_id = div.get('id')
            note_tag = f'[{note_id}]'
            note_content_span = div.find('span', class_='note-content_real')
            if note_content_span:
                note_text = note_content_span.text.strip()
                notes[note_tag] = f"(Note: {note_text})"
        return notes

    def replace_notes(self, html_text, note_list):
        for k, v in note_list.items():
            html_text = html_text.replace(k, v)
        return html_text

    def save_json(self, ln):
        try:
            with json_lock:
                if isfile(self.ln_info_json_file):
                    with open(self.ln_info_json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = {'ln_list': []}
            exist_idx = -1
            for i, item in enumerate(data['ln_list']):
                if item['ln_url'] == ln.url:
                    exist_idx = i
                    break
            if exist_idx == -1:
                new_ln = {
                    'ln_name': ln.name,
                    'ln_url': ln.url,
                    'num_vol': ln.num_vol,
                    'vol_list': []
                }
                for v in ln.volume_list:
                    vol_obj = {
                        'vol_name': v.name,
                        'num_chapter': v.num_chapter,
                        'chapter_list': list(v.chapter_list.keys())
                    }
                    new_ln['vol_list'].append(vol_obj)
                data['ln_list'].append(new_ln)
            else:
                existing_ln = data['ln_list'][exist_idx]
                existing_ln['ln_name'] = ln.name
                existing_ln['num_vol'] = ln.num_vol
                for v in ln.volume_list:
                    vol_exist = None
                    for ev in existing_ln['vol_list']:
                        if ev['vol_name'] == v.name:
                            vol_exist = ev
                            break
                    if vol_exist:
                        for c in v.chapter_list.keys():
                            if c not in vol_exist['chapter_list']:
                                vol_exist['chapter_list'].append(c)
                        vol_exist['num_chapter'] = len(vol_exist['chapter_list'])
                    else:
                        vol_obj = {
                            'vol_name': v.name,
                            'num_chapter': v.num_chapter,
                            'chapter_list': list(v.chapter_list.keys())
                        }
                        existing_ln['vol_list'].append(vol_obj)
            with open(self.ln_info_json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Error save_json:", e)


class Engine:
    def __init__(self):
        self.ln_info_json_file = 'ln_info.json'

    def check_valid_url(self, url):
        if url.isdigit():
            return True
        # Hỗ trợ link manage cho truyện bị ẩn: /action/series/{id}/manage
        if 'ln.hako.vn/action/series/' in url and '/manage' in url:
            return True
        if not any(s in url for s in ['ln.hako.vn/truyen/', 'docln.net/truyen/', 'docln.sbs/truyen/', 'docln.net/ai-dich/', 'docln.sbs/ai-dich/']):
            return False
        return True

    def extract_series_id(self, url):
        """Trích xuất series ID từ URL manage. VD: /action/series/26338/manage → 26338"""
        m = re.search(r'/action/series/(\d+)/manage', url)
        if m:
            return m.group(1)
        return None

    def resolve_manage_url(self, manage_url):
        """
        Với link /action/series/{id}/manage:
        1. Thử tải /truyen/{id} với cookie — nếu có volume-list thì dùng luôn
        2. Nếu không, parse trang manage để lấy danh sách volume/chương
        """
        series_id = self.extract_series_id(manage_url)
        if not series_id:
            return None, None

        if not manage_url.startswith('http'):
            manage_url = 'https://docln.sbs' + manage_url
            
        # Tự động thay thế tên miền bị nhà mạng VN chặn (ln.hako.vn) sang tên miền phụ (docln.sbs)
        manage_url = manage_url.replace('ln.hako.vn', 'docln.sbs').replace('docln.net', 'docln.sbs')
        
        # Lấy domain gốc (ln.hako.vn hoặc docln.sbs)
        from urllib.parse import urlparse
        parsed = urlparse(manage_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # Nếu nhập link /action/series/... không có /manage, tự động thêm
        if '/action/series/' in manage_url and not manage_url.endswith('/manage') and 'edit' not in manage_url:
            manage_url = f'{base_domain}/action/series/{series_id}/manage'

        if not SESSION_COOKIES:
            print("[Manage] ⚠ Truyện bị ẩn cần đăng nhập. Hãy đăng nhập trong app trước.")
            return None, None

        truyen_url = f'{base_domain}/truyen/{series_id}'

        print(f"[Manage] Thử tải trang truyện (với cookie): {truyen_url}")
        try:
            r1 = check_available_request(truyen_url, max_exception_retries=2)
            if r1.status_code == 200:
                s1 = BeautifulSoup(r1.text, bs4_html_parser)
                if s1.find('section', 'volume-list'):
                    print("[Manage] ✅ Cookie hợp lệ — tải được trang truyện bình thường.")
                    return truyen_url, s1
        except Exception as e:
            print(f"[Manage] Lỗi khi tải trang truyện: {e}")

        # Bước 2: Tải trang manage
        print(f"[Manage] Đang truy cập trang quản lý: {manage_url}")
        try:
            r = check_available_request(manage_url, max_exception_retries=3)
            if r.status_code != 200:
                print(f"[Manage] Lỗi HTTP {r.status_code}. Cookie có thể hết hạn.")
                return None, None

            soup = BeautifulSoup(r.text, bs4_html_parser)

            # Dump HTML ra file debug để xem cấu trúc
            try:
                with open('manage_debug.html', 'w', encoding='utf-8') as _f:
                    _f.write(r.text)
            except Exception:
                pass

            page_title = soup.find('title')
            page_title_text = page_title.get_text(strip=True) if page_title else '(không có title)'
            print(f"[Manage] Page title: {page_title_text}")
            if 'login' in r.url.lower() or 'đăng nhập' in page_title_text.lower():
                print("[Manage] ❌ Bị redirect về trang login! Cookie đã hết hạn hoặc không hợp lệ.")
                return None, None

            # Lấy tên truyện
            series_name = ''
            for sel in ['h1', 'h2', 'h2.text-3xl', '.series-name', 'title']:
                tag = soup.find(sel)
                if tag:
                    series_name = tag.get_text(strip=True)
                    if series_name:
                        break
            print(f"[Manage] Tên truyện (dự đoán): {series_name or '(chưa xác định)'}")

            # Phân tích danh sách volume & chương từ HTML manage
            fake_html_parts = [
                f'<html><body>',
                f'<span class="series-name">{series_name or "Unknown"}</span>',
                f'<div class="series-cover"><div class="img-in-ratio" style=""></div></div>'
            ]

            volumes_found = 0
            chapters_found = 0

            # Tìm tất cả các khối volume (thường có id dạng book-xxxx)
            for vol_div in soup.find_all('div', id=re.compile(r'^book-\d+')):
                # Tên volume
                vol_title_tag = vol_div.find(['h3', 'h4'])
                vol_name = vol_title_tag.get_text(strip=True) if vol_title_tag else f"Volume {volumes_found+1}"
                
                # Tìm list chương
                ul_tag = vol_div.find('ul', id=re.compile(r'^chapter-list-'))
                if not ul_tag:
                    continue

                volumes_found += 1
                fake_html_parts.append('<section class="volume-list">')
                fake_html_parts.append(f'<span class="volume-name"><a>{vol_name}</a></span>')
                fake_html_parts.append('<ul class="list-chapters">')

                for li in ul_tag.find_all('li', id=re.compile(r'^chapter-\d+')):
                    # Tên chương
                    chap_name_tag = li.find('div', class_=re.compile(r'font-medium text-gray-800'))
                    chap_name = chap_name_tag.get_text(strip=True) if chap_name_tag else f"Chapter {chapters_found+1}"
                    
                    # Ưu tiên lấy link Sửa chương (/edit) vì truyện bị ẩn thì link public (Xem chương) sẽ bị 404
                    chap_link_tag = None
                    for a in li.find_all('a', href=True):
                        if '/edit' in a['href']:
                            chap_link_tag = a
                            break
                    
                    # Fallback về link public (Xem chương) nếu không tìm thấy link sửa
                    if not chap_link_tag:
                        chap_link_tag = li.find('a', title="Xem chương")
                        if not chap_link_tag:
                            for a in li.find_all('a', href=True):
                                if '/truyen/' in a['href'] or '/doc-truyen/' in a['href']:
                                    chap_link_tag = a
                                    break
                                
                    if chap_link_tag:
                        href = chap_link_tag['href']
                        full_url = href if href.startswith('http') else f'{base_domain}{href}'
                        fake_html_parts.append(f'<li><a href="{full_url}">{chap_name}</a></li>')
                        chapters_found += 1

                fake_html_parts.append('</ul></section>')

            if chapters_found == 0:
                print("[Manage] ⚠ Không tìm thấy chương nào trong cấu trúc manage.")
                return None, None

            fake_html_parts.append('</body></html>')
            fake_html = "\n".join(fake_html_parts)
            
            fake_soup = BeautifulSoup(fake_html, bs4_html_parser)
            print(f"[Manage] ✅ Phân tích thành công {volumes_found} volume, {chapters_found} chương.")
            return manage_url, fake_soup

        except Exception as e:
            print(f"[Manage] Lỗi xử lý trang quản lý: {e}")
            import traceback
            traceback.print_exc()
            return None, None


    def run_with_app(self, lines, app: 'HakoApp'):
        """
        Chạy tải song song với real-time log vào HakoApp.
        Gọi từ background thread.
        """
        pool_size = min(len(lines), 4)
        print(f"─── BẮT ĐẦU TẢI {len(lines)} TRUYỆN (tối đa {pool_size} song song) ───")

        # Đánh dấu tất cả là "đang chờ"
        for line in lines:
            app.update_novel_status(line, "⏳", None, "Đang chờ…",
                                    FG_WARNING, FG_SECONDARY, progress=0)

        results_lock = threading.Lock()
        results = []

        def _worker(line):
            _tls.novel_line = line   # đánh dấu thread này đang xử lý truyện nào
            app.update_novel_status(line, "🔄", None, "Đang xử lý…",
                                    ACCENT3,  FG_INFO, progress=3)
            res = self.process_line(line, app)
            with results_lock:
                results.append(res)
            _tls.novel_line = None   # xóa sau khi xong
            return res

        pool = ThreadPool(pool_size)
        pool.map(_worker, lines)
        pool.close()
        pool.join()

        success_count = sum(1 for s, *_ in results if s)
        error_list    = [f"{l}: {m}" for s, l, m in results if not s]

        print(f"─── KẾT QUẢ: {success_count}/{len(lines)} truyện tải thành công ───")
        for err in error_list:
            print(f"✗ {err}")

    def process_line(self, line, app=None):
        urls_to_try = []
        is_manage_url = 'action/series/' in line and '/manage' in line

        if is_manage_url:
            # Link manage của truyện bị ẩn — xử lý đặc biệt
            urls_to_try = [line]
        elif line.isdigit():
            primary = f"{DEFAULT_URLS}/truyen/{line}"
            fallbacks = [
                f"https://docln.net/truyen/{line}",
                f"https://docln.sbs/truyen/{line}",
                f"https://ln.hako.vn/truyen/{line}",
            ]
            urls_to_try = [primary] + [u for u in fallbacks if u != primary]
        else:
            urls_to_try = [line]

        # ── Pha 1: Chọn domain ────────────────────────────────────────────────
        # Chỉ thử trang chính của truyện.
        # Đổi domain khi: 404 | không có volume-list | lỗi kết nối mạng.
        # KHÔNG đổi domain khi bị rate-limit (check_available_request tự chờ).
        chosen_url  = None
        chosen_soup = None
        error_msg   = ""

        # ── Xử lý đặc biệt: link manage (truyện bị ẩn) ───────────────────────
        if is_manage_url:
            if app:
                app.update_novel_status(line, "🔐", None, "Đang truy cập trang manage…",
                                        FG_WARNING, FG_WARNING, progress=5)
            chosen_url, chosen_soup = self.resolve_manage_url(line)
            if chosen_url is None:
                if app:
                    app.update_novel_status(line, "❌", None, "Không truy cập được trang manage",
                                            FG_ERROR, FG_ERROR, progress=100)
                return (False, line, "Không truy cập được trang manage. Kiểm tra cookies.json.")
        else:
            for url in urls_to_try:
                if not self.check_valid_url(url):
                    continue
                try:
                    print(f"Bắt đầu kiểm tra: {url}")
                    if app:
                        app.update_novel_status(line, "🔄", None, "Đang kết nối…",
                                                ACCENT3, FG_INFO, progress=5)
                    r = check_available_request(url, max_exception_retries=2)
                    if r.status_code == 404:
                        print(f"Không tìm thấy trang (404): {url}")
                        continue
                    soup = BeautifulSoup(r.text, bs4_html_parser)
                    if not soup.find('section', 'volume-list'):
                        print(f"Không tìm thấy danh sách tập: {url}")
                        continue
                    # Domain hợp lệ
                    chosen_url  = url
                    chosen_soup = soup
                    break
                except Exception as e:
                    error_msg = str(e)
                    print(f"Lỗi kết nối ban đầu {url}: {e} — thử domain khác…")

        if chosen_url is None:
            if app:
                app.update_novel_status(line, "❌", None, "Không kết nối được",
                                        FG_ERROR, FG_ERROR, progress=100)
            return (False, line, f"Không tìm thấy domain nào hoạt động. {error_msg}")

        # ── Pha 2: Tải toàn bộ từ domain đã chọn ────────────────────────────────────
        # Sau khi có domain, KHÔNG đổi domain nữa dù gặp lỗi.
        # Rate-limit → check_available_request tự chờ & retry trên cùng URL.
        try:
            print(f"Đã kết nối thành công: {chosen_url}")
            ln_info = LNInfo()
            ln_info.get_info_from_soup(chosen_url, chosen_soup)

            if app:
                app.update_novel_status(line, "📥", ln_info.name,
                                        f"Đang tải {ln_info.num_vol} tập…",
                                        ACCENT3, FG_INFO, progress=15)

            epub_engine = EpubEngine()
            epub_engine._app_ref    = app
            epub_engine._novel_line = line
            epub_engine.create_epub(ln_info, ["Tất cả"])
            print(f"Hoàn thành tải truyện: {ln_info.name}")

            if app:
                app.update_novel_status(line, "✅", ln_info.name,
                                        "✓ Xong!",
                                        FG_SUCCESS, FG_SUCCESS, progress=100)
            return (True, line, ln_info.name)

        except Exception as e:
            # Lỗi trong quá trình tải — KHÔNG thử domain khác
            error_msg = str(e)
            print(f"Lỗi khi tải truyện từ {chosen_url}: {e}")
            if app:
                app.update_novel_status(line, "❌", None, "Lỗi khi tải",
                                        FG_ERROR, FG_ERROR, progress=100)
            return (False, line, f"Lỗi tải: {error_msg}")

    def start(self):
        UIManager.boot(self)


if __name__ == "__main__":
    engine = Engine()
    engine.start()
