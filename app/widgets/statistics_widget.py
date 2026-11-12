"""
ImageLab Studio - Statistics Dashboard Widget (Bảng điều khiển Thống kê & Chẩn đoán Quang học)
Trực quan hóa hệ thống chỉ số quang học định lượng, bảng đối chiếu trước - sau với độ lệch Delta (Δ),
bố cục thông thoáng chống chồng chéo, thanh cuộn mượt mà và nhận định chẩn đoán 100% bằng tiếng Việt chuẩn học thuật.
"""
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from app.styles.dark_theme import THEME_COLORS
from app.resources.icon_manager import IconManager


class MetricCard(QFrame):
    """
    Thẻ tóm tắt chỉ số quang học quan trọng (KPI Card):
    Hiển thị tên chỉ số, giá trị hiện tại của ảnh đã chỉnh và độ lệch Delta (Δ).
    """
    def __init__(self, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_COLORS['panel']};
                border: 1px solid {THEME_COLORS['border']};
                border-radius: 8px;
                padding: 6px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        self.title_lbl = QLabel(title.upper(), self)
        self.title_lbl.setStyleSheet(f"color: {THEME_COLORS['text_secondary']}; font-size: 10px; font-weight: bold;")
        layout.addWidget(self.title_lbl)

        val_row = QHBoxLayout()
        val_row.setSpacing(8)
        self.value_lbl = QLabel("--", self)
        self.value_lbl.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-size: 18px; font-weight: bold;")
        val_row.addWidget(self.value_lbl)

        self.delta_lbl = QLabel("", self)
        self.delta_lbl.setStyleSheet("font-size: 12px; font-weight: bold;")
        val_row.addWidget(self.delta_lbl)
        val_row.addStretch()

        layout.addLayout(val_row)

    def set_values(self, current_str: str, delta_val: Optional[float] = None, unit: str = ""):
        """
        Cập nhật chuỗi giá trị hiển thị và gán màu sắc trực quan cho độ lệch Delta.

        Args:
            current_str (str): Giá trị đo lường hiện tại dạng chuỗi.
            delta_val (Optional[float]): Độ lệch Delta (Δ = Adjusted - Original).
            unit (str): Đơn vị đo lường (ví dụ: "%", "").
        """
        self.value_lbl.setText(current_str)
        if delta_val is not None:
            if abs(delta_val) < 1e-4:
                self.delta_lbl.setText("±0.0")
                self.delta_lbl.setStyleSheet(f"color: {THEME_COLORS['text_muted']}; font-size: 11px;")
            elif delta_val > 0:
                self.delta_lbl.setText(f"+{delta_val:.2f}{unit}")
                self.delta_lbl.setStyleSheet(f"color: {THEME_COLORS['success']}; font-size: 11px; font-weight: bold;")
            else:
                self.delta_lbl.setText(f"{delta_val:.2f}{unit}")
                self.delta_lbl.setStyleSheet(f"color: {THEME_COLORS['primary']}; font-size: 11px; font-weight: bold;")
        else:
            self.delta_lbl.setText("")


class DiagnosticCard(QFrame):
    """
    Thẻ nhận định khoa học chuyên sâu với Vector SVG icon chuẩn phong cách Lucide:
    Trình bày từng luận điểm toán học quang học kèm nhãn trạng thái trực quan.
    """
    def __init__(self, icon_name: str, title: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_COLORS['panel']};
                border: 1px solid {THEME_COLORS['border']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        # Vector SVG icon 18px theo quy chuẩn thiết kế panel
        self.icon_lbl = QLabel(self)
        self.icon_lbl.setPixmap(IconManager.get_pixmap(icon_name, size=18, color=THEME_COLORS['accent']))
        header_row.addWidget(self.icon_lbl)

        self.title_lbl = QLabel(title, self)
        self.title_lbl.setStyleSheet(f"color: {THEME_COLORS['primary']}; font-size: 12px; font-weight: bold;")
        header_row.addWidget(self.title_lbl)

        self.badge_lbl = QLabel("", self)
        self.badge_lbl.setStyleSheet("font-size: 11px; font-weight: bold; padding: 2px 8px; border-radius: 4px;")
        header_row.addStretch()
        header_row.addWidget(self.badge_lbl)
        layout.addLayout(header_row)

        self.content_lbl = QLabel("Chưa tải ảnh để phân tích.", self)
        self.content_lbl.setWordWrap(True)
        self.content_lbl.setStyleSheet(f"color: {THEME_COLORS['text_primary']}; font-size: 12px; line-height: 1.5;")
        layout.addWidget(self.content_lbl)

    def set_content(self, text: str, badge_text: str = "", badge_color: str = ""):
        """
        Cập nhật nội dung nhận định và huy hiệu phân loại trạng thái.

        Args:
            text (str): Nội dung phân tích chẩn đoán.
            badge_text (str): Văn bản trên huy hiệu (ví dụ: "Tối ưu", "Cảnh báo").
            badge_color (str): Mã màu hex đại diện trạng thái.
        """
        self.content_lbl.setText(text)
        if badge_text:
            self.badge_lbl.setText(badge_text)
            self.badge_lbl.setStyleSheet(
                f"background-color: {badge_color}; color: #FFFFFF; "
                "font-size: 10px; font-weight: bold; padding: 2px 8px; border-radius: 4px;"
            )
            self.badge_lbl.setVisible(True)
        else:
            self.badge_lbl.setVisible(False)


class StatisticsWidget(QWidget):
    """
    Bảng điều khiển Thống kê & Chẩn đoán Quang học toàn diện:
    - 100% thuật ngữ tiếng Việt chuẩn giáo trình Xử lý ảnh số.
    - Bảng số liệu đối chiếu rộng rãi, cố định chiều rộng cột chống hiện tượng giật rung layout.
    - Cuộn thông thoáng (QScrollArea) đảm bảo không bao giờ bị cắt chữ hay đè vỡ khối trên mọi độ phân giải.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Khung cuộn mượt mà bảo toàn khoảng trống thoáng đãng
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 16)
        content_layout.setSpacing(14)

        # 1. Hàng thẻ tóm tắt nhanh 4 chỉ số chủ chốt (KPI Cards)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(8)

        self.card_mean = MetricCard("Độ sáng trung bình (Mean)")
        self.card_std = MetricCard("Độ tương phản (Std)")
        self.card_clip = MetricCard("Bão hòa Clipping")
        self.card_edge = MetricCard("Mật độ biên Sobel")

        cards_layout.addWidget(self.card_mean)
        cards_layout.addWidget(self.card_std)
        cards_layout.addWidget(self.card_clip)
        cards_layout.addWidget(self.card_edge)
        content_layout.addLayout(cards_layout)

        # 2. Bảng đối chiếu chi tiết 11 chỉ số quang học (100% tiếng Việt)
        table_title = QLabel("BẢNG CHỈ SỐ QUANG HỌC VÀ THỐNG KÊ CHI TIẾT", self)
        table_title.setStyleSheet(
            f"color: {THEME_COLORS['primary']}; font-size: 12px; "
            "font-weight: bold; letter-spacing: 0.5px; margin-top: 4px;"
        )
        content_layout.addWidget(table_title)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Chỉ số quang học (Metric)",
            "Ảnh gốc",
            "Ảnh đã chỉnh",
            "Độ lệch (Δ)"
        ])

        # Cột 0 giãn tự do; Cột 1, 2, 3 có chiều rộng cố định 95px chống giật layout khi số liệu nhảy
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 95)
        self.table.setColumnWidth(2, 95)
        self.table.setColumnWidth(3, 95)

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)  # Chiều cao hàng thông thoáng 34px
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Chiều cao cố định phù hợp 11 dòng dữ liệu + thanh tiêu đề
        self.table.setFixedHeight(410)
        content_layout.addWidget(self.table)

        # 3. Phân vùng nhận định và phân tích quy luật xử lý ảnh (Vector SVG Icons)
        diag_title = QLabel("NHẬN ĐỊNH VÀ PHÂN TÍCH QUY LUẬT XỬ LÝ ẢNH", self)
        diag_title.setStyleSheet(
            f"color: {THEME_COLORS['accent_hover']}; font-size: 12px; "
            "font-weight: bold; letter-spacing: 0.5px; margin-top: 6px;"
        )
        content_layout.addWidget(diag_title)

        # 4 Thẻ nhận định chuyên sâu độc lập với Vector SVG Icons
        self.card_diag_bright = DiagnosticCard("brightness", "Xu hướng dịch chuyển độ sáng (Histogram Shift)")
        content_layout.addWidget(self.card_diag_bright)

        self.card_diag_contrast = DiagnosticCard("contrast", "Phân bố tương phản & Độ rộng phân tán (Dispersion)")
        content_layout.addWidget(self.card_diag_contrast)

        self.card_diag_clipping = DiagnosticCard("diagnostics", "Bảo toàn chi tiết & Mức độ bão hòa (Clipping)")
        content_layout.addWidget(self.card_diag_clipping)

        self.card_diag_sobel = DiagnosticCard("sobel-edge", "Bản chất toán học Gradient Sobel & Bất biến quang học")
        content_layout.addWidget(self.card_diag_sobel)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def update_statistics(self, comparison_data: Dict[str, Any]):
        """
        Nạp dữ liệu vào bảng so sánh, làm mới các thẻ KPI và cập nhật các nhận định sư phạm.

        Args:
            comparison_data (Dict[str, Any]): Gói dữ liệu tính toán từ ImageAnalyzer.compare_images().
        """
        s_orig = comparison_data["stats_original"]
        s_adj = comparison_data["stats_adjusted"]
        sob_orig = comparison_data["sobel_original"]
        sob_adj = comparison_data["sobel_adjusted"]
        deltas = comparison_data["deltas"]
        diag = comparison_data["diagnosis"]

        # 1. Cập nhật các thẻ KPI trên cùng
        self.card_mean.set_values(f"{s_adj['mean']:.1f}", deltas["delta_mean"])
        self.card_std.set_values(f"{s_adj['std']:.1f}", deltas["delta_std"])

        clip_pct = s_adj["clip_total_pct"]
        clip_color = THEME_COLORS["success"] if clip_pct < 1.0 else (
            THEME_COLORS["warning"] if clip_pct < 8.0 else THEME_COLORS["danger"]
        )
        self.card_clip.set_values(f"{clip_pct:.1f}%", deltas["delta_clipping"], "%")
        self.card_clip.value_lbl.setStyleSheet(f"color: {clip_color}; font-size: 18px; font-weight: bold;")

        self.card_edge.set_values(f"{sob_adj['edge_density']:.1f}%", deltas["delta_edge_density"], "%")

        # 2. Định nghĩa cấu trúc 11 hàng chỉ số quang học tiếng Việt
        rows = [
            ("Cường độ sáng trung bình (Mean μ)", s_orig["mean"], s_adj["mean"], deltas["delta_mean"], "float"),
            ("Độ tương phản / Độ lệch chuẩn (Std σ)", s_orig["std"], s_adj["std"], deltas["delta_std"], "float"),
            ("Mức xám nhỏ nhất (Min Intensity)", s_orig["min"], s_adj["min"], s_adj["min"] - s_orig["min"], "int"),
            ("Mức xám lớn nhất (Max Intensity)", s_orig["max"], s_adj["max"], s_adj["max"] - s_orig["max"], "int"),
            ("Dải động quang học (Dynamic Range)", s_orig["dynamic_range"], s_adj["dynamic_range"], deltas["delta_dynamic_range"], "int"),
            ("Tỷ lệ điểm ảnh vùng tối (<30)", s_orig["dark_pct"], s_adj["dark_pct"], s_adj["dark_pct"] - s_orig["dark_pct"], "pct"),
            ("Tỷ lệ điểm ảnh vùng sáng (>225)", s_orig["highlight_pct"], s_adj["highlight_pct"], s_adj["highlight_pct"] - s_orig["highlight_pct"], "pct"),
            ("Tỷ lệ bão hòa clipping (0 hoặc 255)", s_orig["clip_total_pct"], s_adj["clip_total_pct"], deltas["delta_clipping"], "pct"),
            ("Độ bất định thông tin (Shannon Entropy)", s_orig["entropy"], s_adj["entropy"], deltas["delta_entropy"], "entropy"),
            ("Độ lớn Gradient Sobel trung bình", sob_orig["mean_gradient"], sob_adj["mean_gradient"], deltas["delta_mean_gradient"], "float"),
            ("Mật độ điểm biên Sobel (Edge Density)", sob_orig["edge_density"], sob_adj["edge_density"], deltas["delta_edge_density"], "pct"),
        ]

        self.table.setRowCount(len(rows))
        for r_idx, (name_vn, v_o, v_a, d_val, f_type) in enumerate(rows):
            # Cột 0: Tên chỉ số tiếng Việt
            item_name = QTableWidgetItem(name_vn)
            item_name.setForeground(Qt.GlobalColor.white)
            self.table.setItem(r_idx, 0, item_name)

            # Cột 1 & 2: Định dạng số liệu hiển thị
            if f_type == "float":
                str_o = f"{v_o:.2f}"
                str_a = f"{v_a:.2f}"
                str_d = f"{d_val:+.2f}"
            elif f_type == "int":
                str_o = f"{int(v_o)}"
                str_a = f"{int(v_a)}"
                str_d = f"{int(d_val):+d}"
            elif f_type == "pct":
                str_o = f"{v_o:.2f}%"
                str_a = f"{v_a:.2f}%"
                str_d = f"{d_val:+.2f}%"
            else:  # entropy
                str_o = f"{v_o:.3f}"
                str_a = f"{v_a:.3f}"
                str_d = f"{d_val:+.3f}"

            item_o = QTableWidgetItem(str_o)
            item_o.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r_idx, 1, item_o)

            item_a = QTableWidgetItem(str_a)
            item_a.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_a.setForeground(Qt.GlobalColor.cyan)
            self.table.setItem(r_idx, 2, item_a)

            item_d = QTableWidgetItem(str_d)
            item_d.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if abs(d_val) < 1e-4:
                item_d.setForeground(Qt.GlobalColor.gray)
            elif d_val > 0:
                item_d.setForeground(Qt.GlobalColor.green)
            else:
                item_d.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(r_idx, 3, item_d)

        # 3. Cập nhật các khối nhận định sư phạm
        self.card_diag_bright.set_content(diag['brightness_note'])
        self.card_diag_contrast.set_content(diag['contrast_note'])

        status_text = diag.get("clipping_status", "Optimal")
        status_map = {
            "Optimal": ("Tối ưu (0% mất chi tiết)", THEME_COLORS["success"]),
            "Good": ("Bình thường", THEME_COLORS["success"]),
            "Warning": ("Cảnh báo clipping", THEME_COLORS["warning"]),
            "Danger": ("Nguy hiểm / Bết sáng", THEME_COLORS["danger"])
        }
        b_txt, b_color = status_map.get(status_text, ("Tối ưu", THEME_COLORS["success"]))
        self.card_diag_clipping.set_content(diag['clipping_note'], badge_text=b_txt, badge_color=b_color)

        self.card_diag_sobel.set_content(diag['sobel_note'])
