"""
ImageLab Studio - Analysis Workspace Panel
Không gian làm việc phân tích chuyên sâu tích hợp 3 lĩnh vực quang học:
- 1. Phân tích Histogram 256 Bins (Biểu đồ phân bố mức xám & dải động)
- 2. Bảng thống kê định lượng & Nhận định quy luật xử lý ảnh
- 3. Phân tích phát hiện biên Sobel (Ma trận 8 ô so sánh Gradient và bản đồ biên)

Hỗ trợ:
- Vector SVG Icon đồng nhất theo Design System cho từng tab
- Cơ chế bật mở cửa sổ riêng (Pop-out & Resizable) giải phóng khỏi bố cục cố định
- Đồng bộ hóa dữ liệu thời gian thực không độ trễ
"""
from typing import Optional, Dict, Any
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QFrame
)
from app.widgets.histogram_widget import HistogramWidget
from app.widgets.sobel_analysis_widget import SobelAnalysisWidget
from app.widgets.statistics_widget import StatisticsWidget
from app.styles.dark_theme import THEME_COLORS
from app.resources.icon_manager import IconManager


class AnalysisPanel(QWidget):
    """
    Bảng điều khiển không gian phân tích đa tab kết hợp khả năng tách cửa sổ nổi độc lập:
    - Tab 1: Histogram (256 Bins & Thống kê quang học)
    - Tab 2: Bảng chỉ số tổng hợp & Chẩn đoán lý thuyết
    - Tab 3: Phân tích biên Sobel (8 ô trực quan & Chỉ số biên)
    """
    sobelThresholdChanged = pyqtSignal(float)
    popoutHistogramRequested = pyqtSignal()
    popoutSobelRequested = pyqtSignal()
    popoutStatisticsRequested = pyqtSignal()
    panelExpanded = pyqtSignal()
    panelRestored = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Thanh tiêu đề với nút mở nhanh cửa sổ độc lập cho tab đang chọn
        header_bar = QFrame(self)
        header_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_COLORS['panel']};
                border: 1px solid {THEME_COLORS['border']};
                border-radius: 6px;
                padding: 2px 4px;
            }}
        """)
        h_layout = QHBoxLayout(header_bar)
        h_layout.setContentsMargins(6, 4, 6, 4)
        h_layout.setSpacing(6)

        title_lbl = QLabel("PHÂN TÍCH CHUYÊN SÂU")
        title_lbl.setStyleSheet(f"font-weight: bold; color: {THEME_COLORS['primary']}; font-size: 11px; letter-spacing: 0.5px;")
        h_layout.addWidget(title_lbl)

        h_layout.addStretch()

        # Nút mở cửa sổ độc lập với Vector SVG Icon
        self.btn_popout_active = QPushButton("Phóng to cửa sổ riêng")
        self.btn_popout_active.setIcon(IconManager.get("expand", size=16))
        self.btn_popout_active.setObjectName("resetBtn")
        self.btn_popout_active.setToolTip(
            "<b>Mở khu vực phân tích này ra cửa sổ độc lập (F2 / F3 / F4)</b><br>"
            "Cho phép phóng to, thu nhỏ tùy ý hoặc toàn màn hình mà không bị gò bó trong dashboard."
        )
        self.btn_popout_active.clicked.connect(self._on_popout_clicked)
        h_layout.addWidget(self.btn_popout_active)

        main_layout.addWidget(header_bar)

        self.tabs = QTabWidget()

        # Tab 1: Histogram 256 Bins & Optical Metrics (Icon panel: SVG 18px)
        self.histogram_widget = HistogramWidget()
        self.tabs.addTab(
            self.histogram_widget,
            IconManager.get("histogram", size=18),
            "Histogram"
        )
        self.tabs.setTabToolTip(0, "Biểu đồ phân bố mức xám 256 bins (Phím tắt F2 để mở cửa sổ riêng)")

        # Tab 2: Comprehensive Statistics & Diagnostics Dashboard (Icon panel: SVG 18px)
        self.statistics_widget = StatisticsWidget()
        self.tabs.addTab(
            self.statistics_widget,
            IconManager.get("statistics", size=18),
            "Thống kê & Chẩn đoán"
        )
        self.tabs.setTabToolTip(1, "Bảng chỉ số quang học và nhận định thuật toán (Phím tắt F3 để mở cửa sổ riêng)")

        # Tab 3: Sobel Edge Analysis Workspace (8-Tile Visual Grid) (Icon panel: SVG 18px)
        self.sobel_analysis_widget = SobelAnalysisWidget()
        self.sobel_analysis_widget.thresholdChanged.connect(self.sobelThresholdChanged)
        self.tabs.addTab(
            self.sobel_analysis_widget,
            IconManager.get("sobel-edge", size=18),
            "Phân tích biên Sobel"
        )
        self.tabs.setTabToolTip(2, "Ma trận 8 ô trực quan hóa chi tiết đạo hàm và biên Sobel (Phím tắt F4 để mở cửa sổ riêng)")

        self.tabs.currentChanged.connect(self._on_tab_changed)

        main_layout.addWidget(self.tabs)

    def _on_tab_changed(self, index: int):
        """Cập nhật nhãn nút mở riêng tương ứng với tab đang được chọn."""
        tab_names = ["Histogram", "Thống kê", "Sobel"]
        if 0 <= index < len(tab_names):
            self.btn_popout_active.setText(f"Mở riêng {tab_names[index]}")
            self.btn_popout_active.setIcon(IconManager.get("expand", size=16))

    def _on_popout_clicked(self):
        """Phát tín hiệu mở cửa sổ nổi độc lập tương ứng."""
        idx = self.tabs.currentIndex()
        if idx == 0:
            self.popoutHistogramRequested.emit()
        elif idx == 1:
            self.popoutStatisticsRequested.emit()
        elif idx == 2:
            self.popoutSobelRequested.emit()

    def update_analysis_data(
        self,
        comparison_data: Dict[str, Any],
        sobel_components: Optional[Dict[str, Any]] = None
    ):
        """
        Cập nhật toàn bộ số liệu mới từ pipeline xử lý ảnh tới cả 3 tab:
        1. Cập nhật đường cong Histogram và các mốc chỉ số trung bình.
        2. Cập nhật bảng chỉ số quang học và nhận định lý thuyết.
        3. Cập nhật 8 ô ma trận trực quan hóa biên Sobel.
        """
        hist_orig = comparison_data.get("hist_original")
        hist_adj = comparison_data.get("hist_adjusted")
        stats_orig = comparison_data.get("stats_original")
        stats_adj = comparison_data.get("stats_adjusted")

        # 1. Cập nhật tab Histogram
        self.histogram_widget.update_histograms(
            hist_orig=hist_orig,
            hist_adj=hist_adj,
            stats_orig=stats_orig,
            stats_adj=stats_adj
        )

        # 2. Cập nhật tab Thống kê định lượng & Chẩn đoán
        self.statistics_widget.update_statistics(comparison_data)

        # 3. Cập nhật tab Phân tích biên Sobel (8 ô trực quan & số liệu biên)
        if sobel_components:
            self.sobel_analysis_widget.update_sobel_data(sobel_components)

    def get_sobel_threshold(self) -> float:
        """Lấy giá trị ngưỡng nhị phân hóa biên Sobel hiện tại."""
        return self.sobel_analysis_widget.get_threshold()
