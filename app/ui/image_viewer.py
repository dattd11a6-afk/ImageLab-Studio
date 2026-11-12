"""
ImageLab Studio - Professional Image Viewer
Supports Side-by-Side, Interactive Split Curtain, and Sobel Edge Comparison modes
with stationary fixed-anchor rendering, synchronized panning, zooming, and strict viewport clipping.
"""
from enum import Enum
from typing import Optional, Tuple
import numpy as np
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont, QPen, QBrush, QWheelEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QButtonGroup
)
from app.utils.image_loader import ImageLoader
from app.styles.dark_theme import THEME_COLORS
from app.resources.icon_manager import IconManager


class ViewMode(Enum):
    SIDE_BY_SIDE = "side_by_side"
    SPLIT_CURTAIN = "split_curtain"
    SINGLE_TOGGLE = "single_toggle"
    SOBEL_COMPARE = "sobel_compare"


class InteractiveCanvas(QWidget):
    """
    High-performance QPainter viewport with:
    - Fixed-anchor stationary rendering: Slider adjustments NEVER move or distort image geometry
    - Strict pane clipping: Pixels NEVER bleed across viewports or break UI blocks
    - Smooth sub-pixel precision drawing with anti-aliasing
    - Synchronized dual-viewport panning & zooming
    """
    zoomChanged = pyqtSignal(float)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Image data (QPixmap for GPU-accelerated blitting)
        self.pixmap_orig: Optional[QPixmap] = None
        self.pixmap_adj: Optional[QPixmap] = None
        self.pixmap_sobel_orig: Optional[QPixmap] = None
        self.pixmap_sobel_adj: Optional[QPixmap] = None

        # View mode
        self.view_mode = ViewMode.SIDE_BY_SIDE
        self.show_original_override = False

        # Stationary Zoom & Pan State (Guaranteed fixed during slider adjustments)
        self.zoom_factor = 1.0
        self.pan_offset = QPointF(0.0, 0.0)
        self.is_panning = False
        self.last_mouse_pos = QPointF()

        # Split Curtain Slider position (normalized 0.0 to 1.0)
        self.split_pos = 0.5
        self.is_dragging_split = False

        self.setStyleSheet(f"background-color: {THEME_COLORS['background']};")

    def set_images(self, orig_np: Optional[np.ndarray], adj_np: Optional[np.ndarray]):
        """Update source and processed image pixmaps without touching zoom or pan."""
        # Convert pixmaps
        if orig_np is not None:
            # Only recreate original pixmap if not already present or shape changed
            if self.pixmap_orig is None or self.pixmap_orig.width() != orig_np.shape[1] or self.pixmap_orig.height() != orig_np.shape[0]:
                self.pixmap_orig = ImageLoader.numpy_to_qpixmap(orig_np)
        else:
            self.pixmap_orig = None

        if adj_np is not None:
            self.pixmap_adj = ImageLoader.numpy_to_qpixmap(adj_np)
        else:
            self.pixmap_adj = None

        self.update()

    def set_sobel_images(self, sobel_orig_np: Optional[np.ndarray], sobel_adj_np: Optional[np.ndarray]):
        """Update Sobel edge comparison pixmaps."""
        if sobel_orig_np is not None:
            if self.pixmap_sobel_orig is None or self.pixmap_sobel_orig.width() != sobel_orig_np.shape[1]:
                self.pixmap_sobel_orig = ImageLoader.numpy_to_qpixmap(sobel_orig_np)
        else:
            self.pixmap_sobel_orig = None

        if sobel_adj_np is not None:
            self.pixmap_sobel_adj = ImageLoader.numpy_to_qpixmap(sobel_adj_np)
        else:
            self.pixmap_sobel_adj = None

        self.update()

    def set_view_mode(self, mode: ViewMode):
        self.view_mode = mode
        self.update()

    def fit_to_screen(self):
        """Fit image cleanly into available viewport preserving aspect ratio completely."""
        ref_pix = self.pixmap_orig or self.pixmap_adj
        if ref_pix is None or ref_pix.isNull():
            return

        vw = float(self.width())
        vh = float(self.height())
        iw = float(ref_pix.width())
        ih = float(ref_pix.height())

        if iw <= 0 or ih <= 0 or vw <= 0 or vh <= 0:
            return

        if self.view_mode in (ViewMode.SIDE_BY_SIDE, ViewMode.SOBEL_COMPARE):
            pane_w = vw / 2.0
            # Generous margin so image never touches boundaries
            available_w = max(10.0, pane_w - 30.0)
            available_h = max(10.0, vh - 30.0)
        else:
            available_w = max(10.0, vw - 30.0)
            available_h = max(10.0, vh - 30.0)

        scale_w = available_w / iw
        scale_h = available_h / ih

        # Use min to fit the ENTIRE image within both dimensions without cropping
        self.zoom_factor = max(0.02, min(scale_w, scale_h, 1.0))
        self.pan_offset = QPointF(0.0, 0.0)
        self.zoomChanged.emit(self.zoom_factor)
        self.update()

    def reset_zoom(self):
        """Reset zoom to 100% (1:1)."""
        self.zoom_factor = 1.0
        self.pan_offset = QPointF(0.0, 0.0)
        self.zoomChanged.emit(self.zoom_factor)
        self.update()

    def zoom_in(self):
        self._apply_zoom(1.20)

    def zoom_out(self):
        self._apply_zoom(0.833)

    def _apply_zoom(self, multiplier: float):
        new_zoom = max(0.02, min(10.0, self.zoom_factor * multiplier))
        self.zoom_factor = new_zoom
        self.zoomChanged.emit(self.zoom_factor)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = self.width()
        h = self.height()

        # Fill background
        painter.fillRect(0, 0, w, h, QColor(THEME_COLORS["background"]))

        if self.pixmap_orig is None and self.pixmap_adj is None:
            painter.setPen(QColor(THEME_COLORS["text_muted"]))
            painter.setFont(QFont("Segoe UI", 13))
            msg = "Nhấn 'Ctrl + O' hoặc chọn 'File → Mở ảnh' để bắt đầu chỉnh sửa"
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, msg)
            return

        if self.view_mode == ViewMode.SIDE_BY_SIDE:
            self._paint_side_by_side(painter, w, h, self.pixmap_orig, self.pixmap_adj, "ORIGINAL (ẢNH GỐC)", "EDITED (ĐÃ CHỈNH)")
        elif self.view_mode == ViewMode.SOBEL_COMPARE:
            self._paint_side_by_side(painter, w, h, self.pixmap_sobel_orig, self.pixmap_sobel_adj, "SOBEL ORIGINAL", "SOBEL EDITED")
        elif self.view_mode == ViewMode.SPLIT_CURTAIN:
            self._paint_split_curtain(painter, w, h)
        elif self.view_mode == ViewMode.SINGLE_TOGGLE:
            pix = self.pixmap_orig if self.show_original_override else self.pixmap_adj
            label = "ORIGINAL (HOLDING SPACE)" if self.show_original_override else "EDITED (ĐÃ CHỈNH)"
            self._paint_single_view(painter, w, h, pix, label)

    def _paint_side_by_side(
        self,
        painter: QPainter,
        w: int,
        h: int,
        pix_left: Optional[QPixmap],
        pix_right: Optional[QPixmap],
        label_left: str,
        label_right: str
    ):
        pane_w = w // 2

        # Draw vertical separator line between the two panes
        painter.setPen(QPen(QColor(THEME_COLORS["border"]), 1))
        painter.drawLine(pane_w, 0, pane_w, h)

        # Draw Left Pane with STRICT CLIPPING
        painter.save()
        painter.setClipRect(0, 0, pane_w, h)
        if pix_left and not pix_left.isNull():
            self._draw_centered_pixmap(painter, pix_left, 0.0, 0.0, float(pane_w), float(h))
            self._draw_badge(painter, 16, 16, label_left, QColor(71, 85, 105, 220))
        painter.restore()

        # Draw Right Pane with STRICT CLIPPING
        painter.save()
        painter.setClipRect(pane_w, 0, w - pane_w, h)
        if pix_right and not pix_right.isNull():
            self._draw_centered_pixmap(painter, pix_right, float(pane_w), 0.0, float(w - pane_w), float(h))
            self._draw_badge(painter, pane_w + 16, 16, label_right, QColor(37, 99, 235, 230))
        painter.restore()

    def _paint_split_curtain(self, painter: QPainter, w: int, h: int):
        if self.pixmap_orig is None or self.pixmap_adj is None:
            return

        iw = self.pixmap_orig.width() * self.zoom_factor
        ih = self.pixmap_orig.height() * self.zoom_factor
        cx = (w - iw) / 2.0 + self.pan_offset.x()
        cy = (h - ih) / 2.0 + self.pan_offset.y()
        dest_rect = QRectF(cx, cy, iw, ih)
        src_rect = QRectF(0.0, 0.0, float(self.pixmap_orig.width()), float(self.pixmap_orig.height()))

        split_x = int(round(w * self.split_pos))

        # Clip and draw Left side: Original Image
        painter.save()
        painter.setClipRect(0, 0, split_x, h)
        painter.drawPixmap(dest_rect, self.pixmap_orig, src_rect)
        painter.restore()

        # Clip and draw Right side: Adjusted Image
        painter.save()
        painter.setClipRect(split_x, 0, w - split_x, h)
        painter.drawPixmap(dest_rect, self.pixmap_adj, src_rect)
        painter.restore()

        # Draw Split Divider Line
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.drawLine(split_x, 0, split_x, h)

        # Draw Handle Circle
        handle_y = h // 2
        painter.setBrush(QBrush(QColor(THEME_COLORS["primary"])))
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.drawEllipse(QPoint(split_x, handle_y), 14, 14)

        # Arrows inside handle
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.drawText(QRect(split_x - 10, handle_y - 10, 20, 20), Qt.AlignmentFlag.AlignCenter, "◄►")

        # Badges
        self._draw_badge(painter, 16, 16, "ORIGINAL", QColor(71, 85, 105, 220))
        self._draw_badge(painter, w - 100, 16, "EDITED", QColor(37, 99, 235, 230))

    def _paint_single_view(self, painter: QPainter, w: int, h: int, pix: Optional[QPixmap], label: str):
        if pix and not pix.isNull():
            painter.save()
            painter.setClipRect(0, 0, w, h)
            self._draw_centered_pixmap(painter, pix, 0.0, 0.0, float(w), float(h))
            badge_color = QColor(71, 85, 105, 220) if "ORIGINAL" in label else QColor(37, 99, 235, 230)
            self._draw_badge(painter, 16, 16, label, badge_color)
            painter.restore()

    def _draw_centered_pixmap(self, painter: QPainter, pix: QPixmap, vx: float, vy: float, vw: float, vh: float):
        """Draw pixmap centered in rectangle (vx, vy, vw, vh) using sub-pixel float precision."""
        iw = pix.width() * self.zoom_factor
        ih = pix.height() * self.zoom_factor
        cx = vx + (vw - iw) / 2.0 + self.pan_offset.x()
        cy = vy + (vh - ih) / 2.0 + self.pan_offset.y()

        dest_rect = QRectF(cx, cy, iw, ih)
        src_rect = QRectF(0.0, 0.0, float(pix.width()), float(pix.height()))
        painter.drawPixmap(dest_rect, pix, src_rect)

    def _draw_badge(self, painter: QPainter, x: int, y: int, text: str, bg_color: QColor):
        painter.save()
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)

        badge_w = len(text) * 8 + 18
        badge_h = 24
        rect = QRect(x, y, badge_w, badge_h)

        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 4, 4)

        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()

    # Event Handlers
    def wheelEvent(self, event: QWheelEvent):
        """Smooth zooming via mouse wheel."""
        delta = event.angleDelta().y()
        if delta > 0:
            self._apply_zoom(1.15)
        elif delta < 0:
            self._apply_zoom(0.87)
        event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.view_mode == ViewMode.SPLIT_CURTAIN:
                split_x = int(round(self.width() * self.split_pos))
                if abs(event.position().x() - split_x) < 20:
                    self.is_dragging_split = True
                    return

            self.is_panning = True
            self.last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging_split and self.view_mode == ViewMode.SPLIT_CURTAIN:
            new_pos = event.position().x() / float(self.width())
            self.split_pos = max(0.02, min(0.98, new_pos))
            self.update()
            return

        if self.is_panning:
            diff = event.position() - self.last_mouse_pos
            self.pan_offset += diff
            self.last_mouse_pos = event.position()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = False
            self.is_dragging_split = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.show_original_override = True
            self.update()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.show_original_override = False
            self.update()
        else:
            super().keyReleaseEvent(event)


class ImageViewer(QWidget):
    """
    Main Image Viewport Container with top tool controls:
    - View Mode Switcher (Side-by-Side, Split Curtain, Single, Sobel)
    - Zoom In (+), Zoom Out (-), Fit to Screen, 1:1 Actual Size
    - Zoom indicator readout
    """
    viewModeChanged = pyqtSignal(ViewMode)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar above viewport
        bar = QFrame()
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_COLORS['sidebar']};
                border-bottom: 1px solid {THEME_COLORS['border']};
                padding: 2px 8px;
            }}
        """)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(6, 4, 6, 4)
        bar_layout.setSpacing(8)

        lbl_mode = QLabel("Chế độ xem:")
        lbl_mode.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 500;")
        bar_layout.addWidget(lbl_mode)

        self.btn_side = QPushButton("Song song")
        self.btn_side.setIcon(IconManager.get("compare", size=18))
        self.btn_side.setCheckable(True)
        self.btn_side.setChecked(True)
        self.btn_side.setToolTip("<b>Chế độ xem Song song (Side-by-Side)</b><br>Hiển thị ảnh gốc (Original) bên trái và ảnh đã chỉnh sửa (Edited) bên phải để so sánh trực quan toàn cảnh.")

        self.btn_split = QPushButton("Rèm trượt")
        self.btn_split.setIcon(IconManager.get("split-view", size=18))
        self.btn_split.setCheckable(True)
        self.btn_split.setToolTip("<b>Chế độ Rèm trượt (Split Curtain)</b><br>Kéo đường phân cách dọc trên ảnh để so sánh trực tiếp trước và sau tại cùng một vị trí pixel.")

        self.btn_single = QPushButton("Xem ảnh sửa")
        self.btn_single.setIcon(IconManager.get("single-view", size=18))
        self.btn_single.setCheckable(True)
        self.btn_single.setToolTip("<b>Chế độ Xem ảnh sửa (Single View)</b><br>Hiển thị ảnh đã xử lý.<br><i>Mẹo:</i> Nhấn và giữ phím <b>[Space]</b> bất kỳ lúc nào để chuyển nhanh sang xem ảnh gốc.")

        self.btn_sobel = QPushButton("So sánh biên")
        self.btn_sobel.setIcon(IconManager.get("sobel-compare", size=18))
        self.btn_sobel.setCheckable(True)
        self.btn_sobel.setToolTip("<b>Chế độ So sánh biên (Sobel Compare)</b><br>Hiển thị bản đồ biên độ dốc Sobel của ảnh gốc và ảnh đã chỉnh sửa cạnh nhau.")

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.btn_side, 0)
        self.mode_group.addButton(self.btn_split, 1)
        self.mode_group.addButton(self.btn_single, 2)
        self.mode_group.addButton(self.btn_sobel, 3)
        self.mode_group.idClicked.connect(self._on_mode_clicked)

        bar_layout.addWidget(self.btn_side)
        bar_layout.addWidget(self.btn_split)
        bar_layout.addWidget(self.btn_single)
        bar_layout.addWidget(self.btn_sobel)

        bar_layout.addStretch()

        # Zoom Controls with Vector SVG Icons
        self.btn_zoom_out = QPushButton()
        self.btn_zoom_out.setIcon(IconManager.get("zoom-out", size=16))
        self.btn_zoom_out.setToolTip("<b>Thu nhỏ (Zoom Out)</b><br>Giảm tỉ lệ hiển thị ảnh (Ctrl + Cuộn chuột xuống).")
        self.btn_zoom_out.setFixedWidth(30)
        self.btn_zoom_out.clicked.connect(self._on_zoom_out)
        bar_layout.addWidget(self.btn_zoom_out)

        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setToolTip("<b>Tỉ lệ phóng đại hiện tại của khung nhìn</b>")
        self.lbl_zoom.setStyleSheet("color: #F1F5F9; font-weight: bold; font-size: 11px; min-width: 45px;")
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar_layout.addWidget(self.lbl_zoom)

        self.btn_zoom_in = QPushButton()
        self.btn_zoom_in.setIcon(IconManager.get("zoom-in", size=16))
        self.btn_zoom_in.setToolTip("<b>Phóng to (Zoom In)</b><br>Tăng tỉ lệ hiển thị ảnh (Ctrl + Cuộn chuột lên).")
        self.btn_zoom_in.setFixedWidth(30)
        self.btn_zoom_in.clicked.connect(self._on_zoom_in)
        bar_layout.addWidget(self.btn_zoom_in)

        self.btn_fit = QPushButton("Vừa khung")
        self.btn_fit.setIcon(IconManager.get("fit-screen", size=16))
        self.btn_fit.setToolTip("<b>Vừa khung nhìn (Fit to Screen - Ctrl+0)</b><br>Tự động điều chỉnh kích thước ảnh vừa khít toàn bộ khung hiển thị mà không bị mất góc.")
        self.btn_fit.clicked.connect(self._on_fit)
        bar_layout.addWidget(self.btn_fit)

        self.btn_actual = QPushButton("1:1")
        self.btn_actual.setIcon(IconManager.get("actual-size", size=16))
        self.btn_actual.setToolTip("<b>Kích thước thực 100% (1:1 - Ctrl+1)</b><br>Hiển thị ảnh theo đúng độ phân giải điểm ảnh gốc (1 pixel ảnh = 1 pixel màn hình).")
        self.btn_actual.clicked.connect(self._on_actual)
        bar_layout.addWidget(self.btn_actual)

        layout.addWidget(bar)

        # Interactive Canvas Viewport
        self.canvas = InteractiveCanvas(self)
        self.canvas.zoomChanged.connect(self._on_canvas_zoom_changed)
        layout.addWidget(self.canvas, stretch=1)

    def set_images(self, orig_np: Optional[np.ndarray], adj_np: Optional[np.ndarray]):
        self.canvas.set_images(orig_np, adj_np)

    def set_sobel_images(self, sobel_orig_np: Optional[np.ndarray], sobel_adj_np: Optional[np.ndarray]):
        self.canvas.set_sobel_images(sobel_orig_np, sobel_adj_np)

    def _on_mode_clicked(self, btn_id: int):
        modes = [
            ViewMode.SIDE_BY_SIDE,
            ViewMode.SPLIT_CURTAIN,
            ViewMode.SINGLE_TOGGLE,
            ViewMode.SOBEL_COMPARE
        ]
        chosen = modes[btn_id]
        self.canvas.set_view_mode(chosen)
        self.viewModeChanged.emit(chosen)

    def _on_zoom_in(self):
        self.canvas.zoom_in()

    def _on_zoom_out(self):
        self.canvas.zoom_out()

    def _on_fit(self):
        self.canvas.fit_to_screen()

    def _on_actual(self):
        self.canvas.reset_zoom()

    def _on_canvas_zoom_changed(self, zoom: float):
        self.lbl_zoom.setText(f"{int(round(zoom * 100))}%")
