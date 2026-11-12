"""
ImageLab Studio - Central Branding and Application Identity System
Single source of truth for application metadata, titles, descriptions, and icon paths.
"""
from pathlib import Path

# Thư mục gốc của ứng dụng (ImageLab_Studio2)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Thông tin định danh thương hiệu
APP_NAME = "ImageLab Studio"
APP_TITLE = "ImageLab Studio — Image Enhancement & Analysis"
APP_SUBTITLE = "Brightness · Contrast · Gamma · Histogram · Sobel"
APP_DESCRIPTION = "Professional Desktop Image Processing & Analysis Tool"
APP_VERSION = "2.0.0"
APP_ACADEMIC_PROJECT = "Đồ án Xử lý ảnh số - Đề tài 6: Điều chỉnh độ sáng và độ tương phản của ảnh"
APP_TECH_STACK = "Python 3.10+, PyQt6, OpenCV, NumPy, Matplotlib"

# Đường dẫn tài nguyên Logo và Icon
ICONS_DIR = BASE_DIR / "app" / "resources" / "icons"
APP_LOGO_PATH = ICONS_DIR / "imagelab-logo.svg"
APP_ICON_PATH = ICONS_DIR / "app-icon.svg"

