# 📚 Hako2Ebook — Light Novel Downloader

Tải truyện từ **ln.hako.vn**, **docln.net**, **docln.sbs** và xuất thành file **EPUB** chuẩn, sẵn sàng đọc trên mọi e-reader.

---

## ✨ Tính năng

- 🖥️ **Giao diện đồ hoạ** — dark-mode cyberpunk, không cần gõ lệnh
- ⚡ **Tải song song** — tối đa 4 truyện cùng lúc, mỗi truyện dùng 8 thread tải chương
- 🔄 **User-Agent rotation** — 13 UA khác nhau (Chrome / Firefox / Safari / Edge trên Windows, macOS, Linux) xoay vòng round-robin giữa các thread để tránh rate-limit
- 🌐 **Domain fallback** — tự động thử `docln.sbs → docln.net → ln.hako.vn` nếu domain chính không phản hồi
- 🔓 **Giải mã nội dung bảo vệ** — tự động giải mã XOR + Base64 của cơ chế anti-copy JS
- 🖼️ **Nhúng ảnh inline** — tải và nhúng ảnh minh họa trực tiếp vào EPUB
- 🗑️ **Lọc rác** — xoá banner quảng cáo, link Discord/Facebook, promotional text
- 📝 **Lưu metadata** — lưu thông tin truyện vào `ln_info.json` sau khi tải
- ⚙️ **Cài đặt runtime** — chỉnh sleep time, số luồng, domain mặc định, thư mục lưu ngay trên giao diện

---

## 🖼️ Giao diện

```
┌─────────────────────────────────────────────────────┐
│  HAKO2EBOOK  v2.0.5          [⚙ Cài đặt]           │
├─────────────────────────────────────────────────────┤
│  LINK TRUYỆN (mỗi dòng một link hoặc ID)            │
│  ┌─────────────────────────────────────────────┐    │
│  │ https://ln.hako.vn/truyen/12345             │    │
│  │ 67890                                       │    │
│  └─────────────────────────────────────────────┘    │
│  [📋 Paste]  [🗑 Xóa]            [▶ Bắt đầu tải]   │
├────────────────┬────────────────────────────────────┤
│  TIẾN ĐỘ       │  NHẬT KÝ CHI TIẾT                  │
│  ⏳ Truyện A   │  Bắt đầu kiểm tra: ...             │
│  ✅ Truyện B   │  Đang tải chương: 8/24             │
└────────────────┴────────────────────────────────────┘
```

---

## 🚀 Cài đặt & Chạy

### Yêu cầu

- Python 3.10+

### Cài thư viện

```bash
pip install -r requirements.txt
```

### Chạy

```bash
python hako2ebook.py
```

### Đóng gói thành `.exe` (tuỳ chọn)

```bash
pip install pyinstaller
pyinstaller --onefile hako2ebook.py
# File exe nằm ở: dist/hako2ebook.exe
```

---

## 📖 Cách dùng

1. Chạy `hako2ebook.py`
2. Dán link hoặc ID truyện vào ô nhập liệu (mỗi dòng một link)
3. Nhấn **▶ Bắt đầu tải**
4. Theo dõi tiến độ real-time trên giao diện
5. File EPUB lưu tại thư mục `raw/<Tên truyện>/`

### Định dạng hỗ trợ

| Dạng nhập | Ví dụ |
|---|---|
| Link đầy đủ Hako | `https://ln.hako.vn/truyen/12345` |
| Link đầy đủ Docln | `https://docln.net/truyen/12345` |
| Link AI dịch | `https://docln.sbs/ai-dich/67890` |
| Chỉ ID số | `12345` |

---

## ⚙️ Cài đặt nâng cao (trong app)

| Tuỳ chọn | Mặc định | Mô tả |
|---|---|---|
| Sleep Time | `30` giây | Thời gian chờ khi server báo lỗi 4xx/5xx |
| Số luồng tải chương | `8` | Thread song song cho từng truyện |
| URL gốc mặc định | `https://docln.sbs` | Domain dùng khi chỉ nhập ID |
| Thư mục lưu | `raw` | Thư mục đầu ra của EPUB |

---

## 📁 Cấu trúc thư mục đầu ra

```
raw/
└── Tên Truyện/
    ├── Tập 1.epub
    ├── Tập 2.epub
    └── ...
ln_info.json        ← metadata tất cả truyện đã tải
```

---

## 🛡️ Cơ chế tránh rate-limit

| Cơ chế | Chi tiết |
|---|---|
| **UA Rotation** | 13 User-Agent (Chrome/Firefox/Safari/Edge × Win/macOS/Linux) phân phối round-robin giữa các thread |
| **Per-thread session** | Mỗi thread có session `cloudscraper` riêng biệt |
| **Cloudflare bypass** | `cloudscraper` tự động xử lý JS challenge |
| **Auto retry** | Lỗi mạng: retry 5 lần × 5 giây; Rate-limit: chờ 30 giây rồi thử lại |
| **Domain fallback** | Tự chuyển domain nếu một domain bị block |

---

## 📦 Dependencies

| Package | Vai trò |
|---|---|
| `cloudscraper` | Bypass Cloudflare, giả lập trình duyệt |
| `requests` | Tải ảnh |
| `beautifulsoup4` | Parse HTML |
| `ebooklib` | Tạo file EPUB |
| `Pillow` | Xử lý và convert ảnh |
| `tqdm` | Progress bar |

---

## 📄 License

Dự án cá nhân, chỉ dùng cho mục đích học tập và đọc offline cá nhân.  
Vui lòng không phân phối nội dung có bản quyền.
