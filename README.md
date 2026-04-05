# Hako2Ebook — Light Novel Downloader

Công cụ tải và chuyển đổi light novel từ **ln.hako.vn**, **docln.net**, và **docln.sbs** sang định dạng **EPUB** chuẩn, tối ưu hóa để hiển thị trên các thiết bị e-reader.

---

## Tính năng nổi bật

- **Giao diện trực quan & Log thời gian thực**: Thiết kế màu tối (Dark Cyberpunk) kết hợp theo dõi chi tiết toàn bộ tiến trình tải độc lập ở từng truyện.
- **Tải bộ đệm song song**: Tối đa 4 truyện đồng thời, với 8 luồng tải dữ liệu song song cho mỗi truyện giúp gia tăng tốc độ hiệu quả.
- **Xoay tua IP tự động (Proxy Rotation)**: Hỗ trợ nạp và xoay proxy liên tục khi bị máy chủ khóa mạng, xóa tan rào cản IP từ hệ thống Cloudflare.
- **Mặt nạ thiết bị đa dạng (User-Agent Masking)**: Giả lập đến hàng chục User Profile mô phỏng thiết bị thực tế trên Desktop (Windows, macOS) lẫn Mobile (iOS, Android).
- **Trình bảo lưu TLS Fingerprint**: Tự động ánh xạ bộ thư viện Cipher của luồng HTTP Client để giữ độ uy tín tương ứng với thông số phần cứng User-Agent cấp ra.
- **Cơ chế Fallback thông minh**: Tự động khôi phục và chuyển đổi chéo tên miền `docln.sbs -> docln.net -> ln.hako.vn` cho chung luồng khóa ID truyện.
- **Giải mã chống trộm**: Tích hợp module xử lý script tự động giải mã cấu trúc XOR và Base64 che giấu dữ liệu đang áp dụng.
- **Nhúng và xử lý ảnh nội tuyến**: Tốc độ tải và khôi phục mã hóa ảnh thẳng vào cấu trúc cấu tạo EPUB theo dòng.
- **Lọc tạp âm và quảng cáo**: Tự động sàng lọc chuỗi văn bản rác, điều hướng Discord hay banner rác dư thừa để cho ra ấn phẩm eBook sạch sẽ.

---

## Cài đặt và Khởi chạy

### Yêu cầu hệ thống
- Tương thích với hệ điều hành Windows, macOS, Linux.
- Yêu cầu môi trường Python 3.10 trở lên.

### Thiết lập môi trường

Cài đặt các gói thư viện phụ thuộc:

```bash
pip install -r requirements.txt
```

### Chạy trực tiếp qua Source Code

```bash
python hako2ebook.py
```

### Đóng gói thành tệp thực thi (Standalone Binary / .exe)

Bạn có thể tự đóng gói nếu không muốn cài đặt các gói phụ thuộc Python trong những lần làm việc tiếp theo:

```bash
pip install pyinstaller
pyinstaller --onefile hako2ebook.py
```

*Tệp thực thi sau khi hoàn tất sẽ nằm ở thư mục `dist/hako2ebook.exe`.*

---

## Hướng dẫn sử dụng

1. Khởi động ứng dụng thông qua file `hako2ebook.py` hoặc `.exe`.
2. Truyền liên kết hoặc định dạng ID truyện theo dòng ở khung nhập liệu.
3. Bấm **Bắt đầu tải** và theo dõi tiến trình thực thi qua giao diện console tích hợp.
4. Tệp tin EPUB hoàn chỉnh được tự động lưu theo cấu trúc thư mục dạng `raw/<Tên Truyện>/`.

| Định dạng liên kết hỗ trợ | Ví dụ mẫu |
|---|---|
| Domain Hako chính thức | `https://ln.hako.vn/truyen/12345` |
| Domain Docln chuẩn | `https://docln.net/truyen/12345` |
| Link định dạng AI Text | `https://docln.sbs/ai-dich/67890` |
| Chuỗi Number/ID | `12345` |

---

## Cấu hình hệ thống (Advanced Settings)

Quản lý cài đặt có thể được cấu hình ngay trên giao diện của ứng dụng. Bất kì thay đổi nào đều có hiệu lực ngay lập tức đối với hệ thống.

| Thuộc tính tham số | Thiết lập mặc định | Mô tả kỹ thuật |
|---|---|---|
| Chu kỳ nghỉ (Sleep Time) | `30` (giây) | Biên độ độ trễ chờ khi hệ thống máy chủ bị quá tải (phản hồi 4xx/5xx). |
| Bộ hạn mức luồng tải | `8` | Số luồng truy vấn dữ liệu song song được thực thi đồng bộ với mỗi phiên tải. |
| URL gốc mặc định | `https://docln.sbs` | Endpoint sẽ được ưu tiên khởi chạy truy vấn trước nếu chỉ nhập dạng ID. |
| Thư mục Workspace | `raw` | Tên thư mục nội bộ cho tiến trình đóng gói và lưu xuất tập tin EPUB. |

---

## Thiết lập xoay tua địa chỉ IP (Auto Proxy Rotation)

Để cải tiến độ ổn định khi tải xuống khối lượng lớn dữ liệu, bạn có thể thiết lập Proxy để đổi liên tục bằng cách:
1. Tạo một tập tin dòng lệnh mang tên **`proxies.txt`** trong cùng cấp thư mục gốc với file chạy script.
2. Liệt kê mỗi dãy giao thức Proxy bạn sở hữu trên từng dòng riêng biệt. Hỗ trợ định dạng chuẩn mở: `http://IP:PORT` hoặc `http://USERNAME:PASSWORD@IP:PORT`
> Khi hệ thống khởi động và quét thấy rào cản tập tin này, tiến trình tải sẽ tự động ngẫu nhiên thiết lập mỗi cấu hình Connection vào một điểm Proxy độc lập, đảm nhiệm luân phiên xoay vòng và ngắt tải khi bị máy chủ Cloudflare giới hạn truy vấn cấp bách.

---

## Cơ chế Kháng phân tích và Tránh lỗi (Anti Rate-Limit)

| Hệ thống xử lý | Giải pháp kỹ thuật tích hợp |
|---|---|
| **Giả lập User-Agent đa thiết bị** | Mở rộng kho chuẩn nhận diện với hàng chục Profile gồm cả nền tảng Desktop (Windows, macOS, Linux) lẫn Mobile (Android, iOS) được thay đổi liên tục. |
| **Bảo lưu TLS/SSL Fingerprint** | Kết hợp xen kẽ ngẫu nhiên quy chuẩn Cipher gốc của thư viện `cloudscraper` để đánh lừa lớp quét bot của cấu trúc Fireware Cloudflare. |
| **Xoay tua địa chỉ IP (Proxy)** | Tích hợp load pool IP linh động từ `proxies.txt`. Nếu IP hiện tại bị cấm, bộ làm mới sẽ hủy bỏ session, phân tích mã lỗi (429/403) và tiếp tục gán kết nối sang IP Proxy mới hoàn toàn tự động. |
| **Cách ly không gian (Thread Isolation)** | Thiết lập từng Session Cookie riêng biệt và mã nhận diện Header phân mảnh chéo độc quyền ở mỗi luồng hệ thống tải đồng bộ. |
| **Giả lập Jitter/Micro-Delay** | Thực thi delay trễ khoảng ngẫu nhiên 0.5s - 1.5s cho các kết nối liên tiếp nhằm mô phỏng thói quen lướt thẻ Web chuẩn xác của người dùng thực. |
| **Khôi phục vòng lặp (Error Handling)**| Tự tạo vòng lặp Retry khôi phục nhịp độ từ 5-10s chờ máy chủ hạ nhiệt để phản pháo trực diện các lỗi mạng 429 Too Many Requests. |

---

## Cấu trúc lưu trữ dữ liệu

Danh mục hệ thống cấu trúc hiển thị như sau:

```text
/
├── hako2ebook.py
├── requirements.txt
├── ln_info.json                (Tệp cấu trúc metadata thống kê chung)
└── raw/
    └── [Tên truyện]/
        ├── Tập 1.epub          (Sản phẩm tải biên dịch hoàn thiện)
        └── Tập 2.epub
```

---

## Danh mục Thư viện Mở rộng (Dependencies)

| Gói thư viện / Module | Mô tả nghiệp vụ tham chiếu |
|---|---|
| `cloudscraper` | Xử lý vượt CAPTCHA cục bộ Cloudflare, giả lập cấu hình và ngữ cảnh mạng ảo. |
| `requests` | Thực thi các tập lệnh liên kết HTTP, xử lý Stream tải File tĩnh. |
| `beautifulsoup4` | Khai báo và phân tách hệ thống node cấu trúc HTML DOM trả về của trang. |
| `ebooklib` | Công cụ định dạng HTML sang file lưu trữ phân chia chương mã nguồn EPUB. |
| `Pillow` | Xử lý hình ảnh, thu phóng và chuyển đổi Bitmap sang các tệp tin JPG/PNG nén. |
| `tqdm` | Hiện thanh báo cáo quá trình chạy tải xuống tại các phiên bản dòng lệnh Terminal cũ. |

---

## Bản quyền

Dự án này là thiết kế mở phục vụ quá trình học tập cấu trúc phần mềm Python và đáp ứng tiện ích cá nhân để duyệt tài liệu ngoại tuyến. Toàn bộ thông tin hoặc hình thức nội dung tải xuống đều phụ thuộc bản quyền lưu hành của nhà phát hành web, dịch giả hoặc tác giả tương ứng. Vui lòng thiết lập ý thức tham gia mạng chung không lạm dụng phân phối sai mục đích sở hữu trí tuệ cá nhân.
