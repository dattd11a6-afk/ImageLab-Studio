"""
ImageLab Studio - SVG Icons Compatibility Bridge
Cung cấp khả năng tương thích ngược (Backward Compatibility) với các phiên bản cũ,
chuyển tiếp toàn bộ yêu cầu sang IconManager tập trung trong app.resources.icon_manager.
"""
from PyQt6.QtGui import QIcon, QPixmap
from app.resources.icon_manager import IconManager


def get_window_expand_icon(color: str = "#60A5FA", size: int = 20) -> QIcon:
    """Trả về icon phóng to cửa sổ (expand)."""
    return IconManager.get("expand", color=color, size=size)


def get_window_restore_icon(color: str = "#60A5FA", size: int = 20) -> QIcon:
    """Trả về icon khôi phục cửa sổ (collapse)."""
    return IconManager.get("collapse", color=color, size=size)


def get_layout_balanced_icon(color: str = "#60A5FA", size: int = 20) -> QIcon:
    """Trả về icon bố cục cân bằng (sliders/compare)."""
    return IconManager.get("sliders", color=color, size=size)

