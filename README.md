# Hako2Ebook — Light Novel Downloader

Công cụ tải và chuyển đổi light novel từ **ln.hako.vn**, **docln.net**, và **docln.sbs** sang định dạng **EPUB** chuẩn, tối ưu hóa để hiển thị trên các thiết bị e-reader.

---

## Tính năng nổi bật

- **Giao diện đồ họa trực quan**: Được thiết kế hiện đại (dark-mode), thao tác dễ dàng không cần sử dụng dòng lệnh.
- **Tải bộ đệm song song**: Tối đa 4 truyện đồng thời, với 8 luồng tải dữ liệu song song cho mỗi truyện giúp gia tăng tốc độ hiệu quả.
- **Quản lý phiên bản tự động**: Sử dụng `cloudscraper` khởi tạo theo ngữ cảnh trình duyệt thông minh để đồng bộ hóa User-Agent và TLS fingerprint, tránh lỗi chặn Cloudflare.
- **Cơ chế Fallback thông minh**: Tự động chuyển đổi giữa hệ thống tên miền `docln.sbs -> docln.net -> ln.hako.vn` khi gặp sự cố mạng hoặc không thể truy cập.
- **Cơ chế chống Rate-Limit động**: Tránh bị nhận diện IP/Fingerprint thông qua các tham số giới hạn yêu cầu thông minh, kết hợp thời gian nghỉ ngẫu nhiên (micro-delay) giữa các kết nối.
- **Giải mã chống trộm**: Tích hợp module xử lý script tự động giải mã cấu trúc XOR và Base64 của website.
- **Nhúng và tối ưu ảnh**: Tải, xử lý và tích hợp hình ảnh nội tuyến (inline embedding) một cách tự động vào các dòng nội dung tương ứng của EPUB.
- **Lọc tạp âm nội dung**: Tự động lược bỏ các quảng cáo, liên kết chuyển hướng cộng đồng (Discord/Facebook) và chuỗi văn bản không phù hợp.
- **Lưu metadata**: Thu thập và ghi luồng thông tin truyện vào file `ln_info.json` sau mỗi tiến trình tải.

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

## Cơ chế Kháng phân tích và Tránh lỗi (Anti Rate-Limit)

| Hệ thống xử lý | Giải pháp kỹ thuật tích hợp |
|---|---|
| **TLS/SSL Fingerprint Context** | Quản lý độc lập theo ngữ cảnh thiết bị của `cloudscraper` để đồng bộ hóa User-Agent và TLS Cipher Suite. Tránh bị Cloudflare flag IP là auto bot. |
| **Thread Isolation** | Thiết lập Cloudscraper Session riêng biệt và độc lập ở từng không gian thread tải. |
| **Cơ chế Jitter/Micro-Delay** | Xây dựng độ trễ ngẫu nhiên (0.5s - 1.5s) cho các kết nối liên tiếp nhằm mô phỏng thói quen lướt trang thực tế và giảm tỉ lệ bị chặn địa chỉ IP mạng. |
| **Error Handling (Quản trị Lỗi mạng)** | Tự tạo vòng lặp xoay Session và xóa bộ nhớ cache cookie ở các thời gian rảnh rỗi chờ máy chủ hạ nhiệt từ 5s đến 10s khi gặp lỗi bị chặn liên tục trên giao thức trả về từ mã trạng thái HTTP (HTTP Status 403, 429). |

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
