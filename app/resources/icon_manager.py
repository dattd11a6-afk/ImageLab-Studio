"""
ImageLab Studio - Central Vector SVG Icon Management System
Lucide-inspired minimalist line icon loader with multi-state caching and dynamic recoloring.

Design System:
- Normal stroke: #AAB7C7
- Hover / Active stroke: #60A5FA
- Pressed stroke: #3B82F6
- Disabled stroke: #586273
- Default viewBox: 24x24, stroke-width: 1.8-2.0
"""
from pathlib import Path
from typing import Optional, Dict, Tuple
import logging

from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray, QSize, Qt

logger = logging.getLogger(__name__)

# Thư mục gốc chứa các tệp SVG
ICONS_DIR = Path(__file__).resolve().parent / "icons"


class IconManager:
    """
    Quản lý tập trung toàn bộ vector SVG icons trong ứng dụng.
    Hỗ trợ:
    - Bộ nhớ đệm (Caching) chống tải lại file nhiều lần
    - Tự động sinh trạng thái Normal (#AAB7C7), Active/Hover (#60A5FA), Disabled (#586273)
    - Tùy chỉnh màu sắc và kích thước theo pixel
    - Cơ chế Fallback an toàn, tuyệt đối không làm crash ứng dụng
    """

    # Bảng màu chuẩn theo Design System
    COLOR_NORMAL = "#AAB7C7"
    COLOR_HOVER = "#60A5FA"
    COLOR_PRESSED = "#3B82F6"
    COLOR_DISABLED = "#586273"

    _icon_cache: Dict[Tuple[str, Optional[str], int], QIcon] = {}
    _pixmap_cache: Dict[Tuple[str, Optional[str], int], QPixmap] = {}
    _svg_content_cache: Dict[str, str] = {}

    @classmethod
    def _load_svg_text(cls, name: str) -> Optional[str]:
        """Đọc nội dung tệp SVG từ đĩa hoặc bộ nhớ đệm."""
        clean_name = name.lower().strip()
        if not clean_name.endswith(".svg"):
            clean_name += ".svg"

        if clean_name in cls._svg_content_cache:
            return cls._svg_content_cache[clean_name]

        svg_path = ICONS_DIR / clean_name
        if not svg_path.exists():
            logger.warning(f"[IconManager] Không tìm thấy file icon SVG: {svg_path}")
            return None

        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                content = f.read()
            cls._svg_content_cache[clean_name] = content
            return content
        except Exception as e:
            logger.error(f"[IconManager] Lỗi đọc SVG {clean_name}: {e}")
            return None

    @classmethod
    def _colorize_svg(cls, svg_text: str, color: str) -> str:
        """Thay thế màu nét vẽ (stroke) và màu tô đồng màu trong SVG."""
        # Nếu là logo có gradient nội tại (linearGradient), giữ nguyên không ghi đè
        if "linearGradient" in svg_text and "imagelab-logo" in svg_text:
            return svg_text

        # Thay thế stroke mặc định bằng màu chỉ định
        modified = svg_text.replace('stroke="#AAB7C7"', f'stroke="{color}"')
        modified = modified.replace("stroke='currentColor'", f'stroke="{color}"')
        modified = modified.replace('stroke="currentColor"', f'stroke="{color}"')
        # Thay thế fill nếu có
        modified = modified.replace('fill="#AAB7C7"', f'fill="{color}"')
        return modified

    @classmethod
    def get_pixmap(cls, name: str, color: Optional[str] = None, size: int = 24) -> QPixmap:
        """
        Trả về QPixmap vector kết xuất sắc nét theo kích thước và màu sắc.
        """
        cache_key = (name, color, size)
        if cache_key in cls._pixmap_cache:
            return cls._pixmap_cache[cache_key]

        svg_text = cls._load_svg_text(name)
        if not svg_text:
            # Fallback tạo một pixmap trong suốt
            pm = QPixmap(size, size)
            pm.fill(Qt.GlobalColor.transparent)
            return pm

        effective_color = color or cls.COLOR_NORMAL
        colored_svg = cls._colorize_svg(svg_text, effective_color)

        byte_array = QByteArray(colored_svg.encode("utf-8"))
        renderer = QSvgRenderer(byte_array)

        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        renderer.render(painter)
        painter.end()

        cls._pixmap_cache[cache_key] = pixmap
        return pixmap

    @classmethod
    def get(cls, name: str, color: Optional[str] = None, size: int = 24) -> QIcon:
        """
        Trả về QIcon đa trạng thái (Normal, Active, Disabled).
        Khi người dùng di chuột (Hover) hoặc nút bị disable, QIcon tự động hiển thị màu tương ứng.
        """
        cache_key = (name, color, size)
        if cache_key in cls._icon_cache:
            return cls._icon_cache[cache_key]

        icon = QIcon()

        if color:
            # Nếu người dùng chỉ định màu cụ thể, dùng màu đó cho mọi trạng thái
            pix_custom = cls.get_pixmap(name, color=color, size=size)
            icon.addPixmap(pix_custom, QIcon.Mode.Normal)
            icon.addPixmap(pix_custom, QIcon.Mode.Active)
            cls._icon_cache[cache_key] = icon
            return icon

        # Tự động tạo pixmap cho 3 trạng thái
        pix_normal = cls.get_pixmap(name, color=cls.COLOR_NORMAL, size=size)
        pix_active = cls.get_pixmap(name, color=cls.COLOR_HOVER, size=size)
        pix_disabled = cls.get_pixmap(name, color=cls.COLOR_DISABLED, size=size)

        icon.addPixmap(pix_normal, QIcon.Mode.Normal, QIcon.State.Off)
        icon.addPixmap(pix_active, QIcon.Mode.Active, QIcon.State.Off)
        icon.addPixmap(pix_active, QIcon.Mode.Normal, QIcon.State.On)  # Checked state
        icon.addPixmap(pix_disabled, QIcon.Mode.Disabled, QIcon.State.Off)

        cls._icon_cache[cache_key] = icon
        return icon

    @classmethod
    def clear_cache(cls):
        """Xóa sạch bộ nhớ đệm icon."""
        cls._icon_cache.clear()
        cls._pixmap_cache.clear()
        cls._svg_content_cache.clear()

