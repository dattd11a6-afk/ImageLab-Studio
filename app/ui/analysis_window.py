"""
ImageLab Studio - Dedicated Floating / Resizable Analysis Window
Cửa sổ phân tích độc lập với kích thước lớn, tự do co giãn hoặc phóng to toàn màn hình.
Loại bỏ hoàn toàn sự gò bó, chật chội của bố cục dashboard cố định.

Hỗ trợ:
- Tích hợp trọn bộ Vector SVG Icon (Lucide-inspired)
- Phóng to toàn màn hình (Maximize / F11) và thu nhỏ linh hoạt
- Đồng bộ hóa thời gian thực (Real-time Sync) với luồng xử lý ảnh
"""
from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame
)
from app.styles.dark_theme import THEME_COLORS
from app.resources.icon_manager import IconManager


class AnalysisSubWindow(QWidget):
    """
    Cửa sổ phân tích chuyên sâu độc lập (Top-level Window).
    Cho phép người dùng kéo giãn các cạnh mép tùy ý hoặc chuyển sang toàn màn hình (F11).
    """
    windowClosed = pyqtSignal()

    def __init__(
        self,
        title: str,
        icon_name: str,
        content_widget: QWidget,
        default_width: int = 900,
        default_height: int = 650,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent, Qt.WindowType.Window)
        self.icon_name = icon_name
        self.clean_title = title
        # Đặt tiêu đề súc tích, tránh lặp lại thương hiệu do Windows tự động ghép với tên cửa sổ cha
        self.setWindowTitle(title)
        self.setWindowIcon(IconManager.get(icon_name, size=24))
        self.resize(default_width, default_height)
        self.setMinimumSize(480, 360)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME_COLORS['background']};
                color: {THEME_COLORS['text_primary']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Thanh tiêu đề phụ bên trong cửa sổ
        header_frame = QFrame(self)
        header_frame.setObjectName("panelFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(10)

        # Biểu tượng SVG chuyên dụng cho từng loại phân tích
        icon_lbl = QLabel(self)
        icon_lbl.setPixmap(IconManager.get_pixmap(icon_name, color=THEME_COLORS['primary'], size=20))
        header_layout.addWidget(icon_lbl)

        # Tiêu đề khu vực phân tích
        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet(f"font-weight: bold; color: {THEME_COLORS['primary']}; font-size: 13px; letter-spacing: 0.5px;")
        header_layout.addWidget(title_lbl)

        header_layout.addStretch()

        # Nút chuyển đổi Toàn màn hình / Khôi phục kích thước
        self.btn_fullscreen = QPushButton("Phóng to tối đa")
        self.btn_fullscreen.setIcon(IconManager.get("expand", size=16))
        self.btn_fullscreen.setToolTip("Phóng to toàn màn hình / Khôi phục kích thước (F11)")
        self.btn_fullscreen.clicked.connect(self.toggle_maximize)
        header_layout.addWidget(self.btn_fullscreen)

        # Nút đóng cửa sổ
        btn_close = QPushButton("Đóng")
        btn_close.setIcon(IconManager.get("close", size=16))
        btn_close.setToolTip("Đóng cửa sổ này (Esc)")
        btn_close.clicked.connect(self.hide)
        header_layout.addWidget(btn_close)

        layout.addWidget(header_frame)

        # Nhúng thành phần phân tích thực tế
        self.content_widget = content_widget
        layout.addWidget(self.content_widget, stretch=1)

    def toggle_maximize(self):
        """Chuyển đổi linh hoạt giữa chế độ toàn màn hình và cửa sổ thông thường."""
        if self.isMaximized():
            self.showNormal()
            self.btn_fullscreen.setText("Phóng to tối đa")
            self.btn_fullscreen.setIcon(IconManager.get("expand", size=16))
        else:
            self.showMaximized()
            self.btn_fullscreen.setText("Thu nhỏ cửa sổ")
            self.btn_fullscreen.setIcon(IconManager.get("collapse", size=16))

    def show_and_activate(self):
        """Hiển thị cửa sổ, đưa lên trên cùng và tập trung tiêu điểm."""
        self.show()
        self.raise_()
        self.activateWindow()
        if hasattr(self.content_widget, "redraw_plot"):
            self.content_widget.redraw_plot()
        if hasattr(self.content_widget, "canvas") and hasattr(self.content_widget.canvas, "draw"):
            self.content_widget.canvas.draw()

    def keyPressEvent(self, event):
        """Xử lý các phím tắt nhanh thuận tiện khi phân tích ảnh."""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key.Key_F11:
            self.toggle_maximize()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.windowClosed.emit()
        super().closeEvent(event)
