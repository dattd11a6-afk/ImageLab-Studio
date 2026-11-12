"""
ImageLab Studio – Image Brightness, Contrast & Gamma Enhancement
Đồ án môn Xử lý ảnh số - Đề tài 6: Điều chỉnh độ sáng và độ tương phản của ảnh.
Điểm khởi chạy ứng dụng chính (Main Application Entry Point).
"""
import sys
import os
import tempfile

# Cấu hình thư mục tạm an toàn có quyền ghi cho Matplotlib trước khi import
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_imagelab"))

# Đảm bảo đường dẫn gốc của project luôn nằm đầu danh sách sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from app.config.branding import APP_NAME, APP_TITLE
from app.resources.icon_manager import IconManager
from app.ui.main_window import MainWindow
from app.styles.dark_theme import DARK_STYLESHEET


def main():
    """
    Hàm khởi chạy chính của ImageLab Studio:
    1. Thiết lập các cờ hỗ trợ màn hình độ phân giải cao (High-DPI).
    2. Khởi tạo đối tượng QApplication và nạp icon thương hiệu chính.
    3. Áp dụng font chữ Segoe UI và bộ stylesheet giao diện Dark Theme.
    4. Khởi tạo và hiển thị cửa sổ chính MainWindow.
    """
    # Kích hoạt tính năng co giãn giao diện mượt mà trên màn hình 2K/4K (High-DPI)
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_TITLE)
    app.setOrganizationName("DigitalImageProcessing")

    # Đặt icon thương hiệu độc quyền cho toàn bộ tiến trình ứng dụng
    app.setWindowIcon(IconManager.get("imagelab-logo", size=32))

    # Cấu hình phông chữ mặc định chuẩn Segoe UI phong cách hiện đại
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)

    # Áp dụng bộ giao diện Dark Creative Studio toàn cục
    app.setStyleSheet(DARK_STYLESHEET)

    # Khởi tạo cửa sổ chính
    window = MainWindow()

    # Hỗ trợ mở ảnh trực tiếp nếu đường dẫn ảnh được truyền qua đối số dòng lệnh
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        window.load_image_file(sys.argv[1])

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
