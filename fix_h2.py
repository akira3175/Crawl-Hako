import zipfile
import os
import shutil
import re
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

# Đảm bảo in unicode ra terminal windows không bị lỗi
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def process_html_content(content):
    # 1. Xóa dòng đầu tiên (thường là thẻ <h1..6> nằm ngay sau <body>) vì nó trùng với tên chap trong menu
    # Sử dụng Regex để tìm thẻ Heading đầu tiên ngay sau <body>
    content = re.sub(
        r'(<body[^>]*>)\s*<h[1-6][^>]*>[\s\S]*?</h[1-6]>', 
        r'\1', 
        content, 
        count=1, 
        flags=re.IGNORECASE
    )

    # 2. Đổi <h2> thành <p> để ghi chú trở thành chữ bình thường
    content = re.sub(r'<h2\b', '<p', content, flags=re.IGNORECASE)
    content = re.sub(r'</h2>', '</p>', content, flags=re.IGNORECASE)

    return content

def fix_epub(epub_path):
    if not os.path.exists(epub_path):
        print(f"File not found: {epub_path}")
        return False

    print(f"Processing file: {epub_path}")
    
    # Tạo đường dẫn file backup
    backup_path = epub_path + ".bak"
    shutil.copy2(epub_path, backup_path)
    print(f"Backup created at: {backup_path}")

    # Tạo thư mục tạm để giải nén EPUB
    temp_dir = epub_path + "_temp"
    os.makedirs(temp_dir, exist_ok=True)

    has_changed = False
    try:
        # Giải nén
        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Tránh sửa file nav.xhtml vì đây là file mục lục (nếu sửa thẻ H nó có thể mất mục lục)
        # Tuy nhiên script của ta thay h2 bằng p vẫn giữ được text. Để an toàn, chỉ sửa chap.
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(('.html', '.xhtml', '.htm')):
                    # Bỏ qua file mục lục epub3
                    if file.lower() == 'nav.xhtml':
                        continue
                        
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    new_content = process_html_content(content)

                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f" - Mofified: {file}")
                        has_changed = True

        # Đóng gói lại EPUB
        if has_changed:
            with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zip_ref.write(file_path, arcname)
            print("=> EPUB updated successfully!")
            return True
        else:
            print("=> No changes needed in this file.")
            os.remove(backup_path)
            return False
            
    finally:
        # Dọn dẹp thư mục tạm
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def select_and_process():
    root = tk.Tk()
    root.withdraw() # Ẩn cửa sổ chính
    
    file_paths = filedialog.askopenfilenames(
        title="Chọn các file EPUB cần sửa",
        filetypes=[("EPUB Files", "*.epub"), ("All Files", "*.*")]
    )
    
    if not file_paths:
        print("Đã hủy chọn file.")
        return
        
    success_count = 0
    for path in file_paths:
        if fix_epub(path):
            success_count += 1
            
    messagebox.showinfo(
        "Hoàn tất", 
        f"Đã xử lý xong!\nCập nhật thành công: {success_count}/{len(file_paths)} file."
    )

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Nếu chạy qua dòng lệnh và có truyền file
        for arg in sys.argv[1:]:
            fix_epub(arg)
    else:
        # Nếu click đúp trực tiếp, mở hộp thoại chọn file
        select_and_process()
