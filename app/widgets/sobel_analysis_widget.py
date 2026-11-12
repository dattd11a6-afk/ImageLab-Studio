"""
ImageLab Studio - Dedicated Sobel Edge Analysis Workspace
Implements full 8-tile comparative analysis:
1. Original Grayscale vs 2. Adjusted Grayscale
3. Original Sobel X vs 4. Adjusted Sobel X
5. Original Sobel Y vs 6. Adjusted Sobel Y
7. Original Gradient Magnitude vs 8. Adjusted Gradient Magnitude
With unified shared scaling, quantitative edge metrics, and mathematical explanations.
"""
from typing import Optional, Dict, Any
import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QSlider, QDoubleSpinBox, QGroupBox,
    QFrame, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox
)
from app.utils.image_loader import ImageLoader
from app.styles.dark_theme import THEME_COLORS


class ImageTile(QFrame):
    """Visual preview tile showing a single image component with label and subtitle."""
    def __init__(self, title: str, subtitle: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_COLORS['panel']};
                border: 1px solid {THEME_COLORS['border']};
                border-radius: 6px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Header with Title
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"color: {THEME_COLORS['primary']}; font-weight: bold; font-size: 11px;")
        layout.addWidget(self.title_lbl)

        # Image Canvas
        self.img_lbl = QLabel()
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_lbl.setMinimumSize(180, 130)
        self.img_lbl.setStyleSheet("background-color: #0d0f12; border-radius: 4px;")
        layout.addWidget(self.img_lbl, stretch=1)

        # Subtitle / Metric Readout
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 10px;")
        layout.addWidget(self.sub_lbl)

    def set_image(self, img_np: Optional[np.ndarray], metric_text: str = ""):
        if metric_text:
            self.sub_lbl.setText(metric_text)

        if img_np is None or img_np.size == 0:
            self.img_lbl.clear()
            self.img_lbl.setText("Chưa có dữ liệu")
            return

        pix = ImageLoader.numpy_to_qpixmap(img_np)
        scaled_pix = pix.scaled(
            self.img_lbl.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.img_lbl.setPixmap(scaled_pix)


class SobelAnalysisWidget(QWidget):
    """
    Dedicated Sobel Edge Analysis Workspace:
    - Complete 8-grid comparative visual tiles
    - Quantitative Edge Metrics table (Mean Gradient, Max Gradient, Edge Density, Strong Edge %)
    - Unified fair scale information and theoretical explanation
    """
    thresholdChanged = pyqtSignal(float)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.cached_components: Optional[Dict[str, Any]] = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 16)
        content_layout.setSpacing(12)

        # 1. Header & Threshold Control Bar
        control_box = QGroupBox("ĐIỀU KHIỂN PHÁT HIỆN BIÊN SOBEL & NGƯỠNG (THRESHOLD)")
        control_layout = QVBoxLayout(control_box)
        control_layout.setContentsMargins(10, 12, 10, 10)
        control_layout.setSpacing(8)

        row_thresh = QHBoxLayout()
        row_thresh.addWidget(QLabel("Ngưỡng biên (Edge Threshold):"))

        self.slider_thresh = QSlider(Qt.Orientation.Horizontal)
        self.slider_thresh.setRange(5, 200)
        self.slider_thresh.setValue(50)
        self.slider_thresh.valueChanged.connect(self._on_slider_thresh_changed)
        row_thresh.addWidget(self.slider_thresh, stretch=1)

        self.spin_thresh = QDoubleSpinBox()
        self.spin_thresh.setRange(5.0, 200.0)
        self.spin_thresh.setValue(50.0)
        self.spin_thresh.setDecimals(1)
        self.spin_thresh.setMinimumWidth(80)
        self.spin_thresh.valueChanged.connect(self._on_spin_thresh_changed)
        row_thresh.addWidget(self.spin_thresh)

        control_layout.addLayout(row_thresh)
        content_layout.addWidget(control_box)

        # 2. Complete 8-Tile Visual Comparative Grid
        grid_title = QLabel("KHU VỰC ĐỐI CHIẾU ĐA THÀNH PHẦN SOBEL (8 Ô TRỰC QUAN)")
        grid_title.setStyleSheet(f"color: {THEME_COLORS['primary']}; font-weight: bold; font-size: 12px; letter-spacing: 0.5px;")
        content_layout.addWidget(grid_title)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)

        # Row 1: Grayscale Images (1 & 2)
        self.tile_gray_orig = ImageTile("1. ẢNH GỐC (GRAYSCALE)", "Mức xám gốc")
        self.tile_gray_adj = ImageTile("2. ẢNH ĐÃ CHỈNH (GRAYSCALE)", "Mức xám đã xử lý")
        grid_layout.addWidget(self.tile_gray_orig, 0, 0)
        grid_layout.addWidget(self.tile_gray_adj, 0, 1)

        # Row 2: Sobel X Derivatives (3 & 4)
        self.tile_gx_orig = ImageTile("3. SOBEL X GỐC (Gx - DỌC)", "Đạo hàm theo trục X")
        self.tile_gx_adj = ImageTile("4. SOBEL X ĐÃ CHỈNH (Gx - DỌC)", "Đạo hàm theo trục X")
        grid_layout.addWidget(self.tile_gx_orig, 1, 0)
        grid_layout.addWidget(self.tile_gx_adj, 1, 1)

        # Row 3: Sobel Y Derivatives (5 & 6)
        self.tile_gy_orig = ImageTile("5. SOBEL Y GỐC (Gy - NGANG)", "Đạo hàm theo trục Y")
        self.tile_gy_adj = ImageTile("6. SOBEL Y ĐÃ CHỈNH (Gy - NGANG)", "Đạo hàm theo trục Y")
        grid_layout.addWidget(self.tile_gy_orig, 2, 0)
        grid_layout.addWidget(self.tile_gy_adj, 2, 1)

        # Row 4: Gradient Magnitude (7 & 8)
        self.tile_mag_orig = ImageTile("7. ĐỘ LỚN GRADIENT GỐC (|G|)", "Cường độ biên tổng hợp")
        self.tile_mag_adj = ImageTile("8. ĐỘ LỚN GRADIENT ĐÃ CHỈNH (|G|)", "Cường độ biên tổng hợp")
        grid_layout.addWidget(self.tile_mag_orig, 3, 0)
        grid_layout.addWidget(self.tile_mag_adj, 3, 1)

        content_layout.addLayout(grid_layout)

        # 3. Quantitative Edge Statistics Table
        table_title = QLabel("BẢNG ĐỊNH LƯỢNG CHỈ SỐ BIÊN SOBEL")
        table_title.setStyleSheet(f"color: {THEME_COLORS['accent_hover']}; font-weight: bold; font-size: 12px; letter-spacing: 0.5px; margin-top: 6px;")
        content_layout.addWidget(table_title)

        self.table_sobel = QTableWidget()
        self.table_sobel.setColumnCount(4)
        self.table_sobel.setHorizontalHeaderLabels([
            "Chỉ số biên (Sobel Metric)",
            "Ảnh gốc",
            "Ảnh đã chỉnh",
            "Độ lệch (Δ)"
        ])
        self.table_sobel.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_sobel.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table_sobel.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_sobel.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table_sobel.setColumnWidth(1, 95)
        self.table_sobel.setColumnWidth(2, 95)
        self.table_sobel.setColumnWidth(3, 95)
        self.table_sobel.verticalHeader().setVisible(False)
        self.table_sobel.verticalHeader().setDefaultSectionSize(32)
        self.table_sobel.setAlternatingRowColors(True)
        self.table_sobel.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_sobel.setFixedHeight(160)
        content_layout.addWidget(self.table_sobel)

        # 4. In-depth Academic Explanation Card
        theory_frame = QFrame()
        theory_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_COLORS['panel']};
                border: 1px solid {THEME_COLORS['border']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        theory_layout = QVBoxLayout(theory_frame)
        theory_layout.setContentsMargins(12, 10, 12, 10)
        theory_layout.setSpacing(6)

        title_th = QLabel("QUY LUẬT TOÁN HỌC & ĐỊNH LÝ BẤT BIẾN GRADIENT BIÊN:")
        title_th.setStyleSheet(f"color: {THEME_COLORS['primary']}; font-weight: bold; font-size: 11px;")
        theory_layout.addWidget(title_th)

        desc_th = QLabel(
            "• <b>Định lý bất biến độ sáng:</b> ∇(I + β) = ∇I + 0 = ∇I. Khi chưa bị bão hòa (clipping), "
            "phép cộng độ sáng đơn thuần KHÔNG làm thay đổi đạo hàm hay độ lớn biên Sobel. Tăng sáng không làm tăng chi tiết biên.<br>"
            "• <b>Hệ số Contrast α:</b> Khuếch đại gradient trực tiếp ∇(α · I) = α · ∇I. Tăng contrast làm tăng độ dốc biên.<br>"
            "• <b>Hiệu chỉnh Gamma:</b> Tác động phi tuyến lên đạo hàm (dI^γ/dx = γ·I^(γ-1)·dI/dx), nén/giãn dải gradient phụ thuộc cường độ vùng ảnh.<br>"
            "• <b>Nguyên tắc chuẩn hóa công bằng:</b> Cả 8 ô hiển thị đều sử dụng CÙNG MỘT THANG CƯỜNG ĐỘ chung duy nhất."
        )
        desc_th.setWordWrap(True)
        desc_th.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 11px; line-height: 1.5;")
        theory_layout.addWidget(desc_th)

        content_layout.addWidget(theory_frame)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def get_threshold(self) -> float:
        return float(self.spin_thresh.value())

    def update_sobel_data(self, sobel_components: Dict[str, Any]):
        """Update all 8 visual tiles and quantitative statistics."""
        self.cached_components = sobel_components

        # 1. Update Visual Tiles
        self.tile_gray_orig.set_image(sobel_components["gray_orig"], f"Mean: {np.mean(sobel_components['gray_orig']):.1f}")
        self.tile_gray_adj.set_image(sobel_components["gray_adj"], f"Mean: {np.mean(sobel_components['gray_adj']):.1f}")

        self.tile_gx_orig.set_image(sobel_components["sobel_x_orig"], f"Max: {np.max(np.abs(sobel_components['raw_gx_orig'])):.1f}")
        self.tile_gx_adj.set_image(sobel_components["sobel_x_adj"], f"Max: {np.max(np.abs(sobel_components['raw_gx_adj'])):.1f}")

        self.tile_gy_orig.set_image(sobel_components["sobel_y_orig"], f"Max: {np.max(np.abs(sobel_components['raw_gy_orig'])):.1f}")
        self.tile_gy_adj.set_image(sobel_components["sobel_y_adj"], f"Max: {np.max(np.abs(sobel_components['raw_gy_adj'])):.1f}")

        self.tile_mag_orig.set_image(sobel_components["mag_orig"], f"Mean |G|: {sobel_components['mean_gradient_orig']:.1f}")
        self.tile_mag_adj.set_image(sobel_components["mag_adj"], f"Mean |G|: {sobel_components['mean_gradient_adj']:.1f}")

        # 2. Calculate edge metrics
        thresh = sobel_components["threshold"]
        mag_o = sobel_components["raw_mag_orig"]
        mag_a = sobel_components["raw_mag_adj"]
        total_p = mag_o.size

        mean_o = sobel_components["mean_gradient_orig"]
        mean_a = sobel_components["mean_gradient_adj"]
        max_o = sobel_components["max_gradient_orig"]
        max_a = sobel_components["max_gradient_adj"]

        dens_o = (np.count_nonzero(mag_o >= thresh) / total_p) * 100.0
        dens_a = (np.count_nonzero(mag_a >= thresh) / total_p) * 100.0

        strong_o = (np.count_nonzero(mag_o >= 100.0) / total_p) * 100.0
        strong_a = (np.count_nonzero(mag_a >= 100.0) / total_p) * 100.0

        rows = [
            ("Độ lớn Gradient trung bình (Mean |G|)", mean_o, mean_a, mean_a - mean_o, "float"),
            ("Độ lớn Gradient tối đa (Max |G|)", max_o, max_a, max_a - max_o, "float"),
            (f"Mật độ điểm biên (|G| ≥ {thresh:.0f})", dens_o, dens_a, dens_a - dens_o, "pct"),
            ("Tỷ lệ biên mạnh (|G| ≥ 100)", strong_o, strong_a, strong_a - strong_o, "pct"),
        ]

        self.table_sobel.setRowCount(len(rows))
        for r_idx, (name, v_o, v_a, d_val, f_type) in enumerate(rows):
            item_name = QTableWidgetItem(name)
            item_name.setForeground(Qt.GlobalColor.white)
            self.table_sobel.setItem(r_idx, 0, item_name)

            str_o = f"{v_o:.2f}" if f_type == "float" else f"{v_o:.2f}%"
            str_a = f"{v_a:.2f}" if f_type == "float" else f"{v_a:.2f}%"
            str_d = f"{d_val:+.2f}" if f_type == "float" else f"{d_val:+.2f}%"

            item_o = QTableWidgetItem(str_o)
            item_o.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_sobel.setItem(r_idx, 1, item_o)

            item_a = QTableWidgetItem(str_a)
            item_a.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_a.setForeground(Qt.GlobalColor.cyan)
            self.table_sobel.setItem(r_idx, 2, item_a)

            item_d = QTableWidgetItem(str_d)
            item_d.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if abs(d_val) < 1e-4:
                item_d.setForeground(Qt.GlobalColor.gray)
            elif d_val > 0:
                item_d.setForeground(Qt.GlobalColor.green)
            else:
                item_d.setForeground(Qt.GlobalColor.yellow)
            self.table_sobel.setItem(r_idx, 3, item_d)

    def _on_slider_thresh_changed(self, val: int):
        self.spin_thresh.blockSignals(True)
        self.spin_thresh.setValue(float(val))
        self.spin_thresh.blockSignals(False)
        self.thresholdChanged.emit(float(val))

    def _on_spin_thresh_changed(self, val: float):
        self.slider_thresh.blockSignals(True)
        self.slider_thresh.setValue(int(round(val)))
        self.slider_thresh.blockSignals(False)
        self.thresholdChanged.emit(val)
