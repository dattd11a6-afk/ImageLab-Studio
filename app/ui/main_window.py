"""
ImageLab Studio - Main Application Window
Coordinates UI layout, menu bar, toolbar, image pipeline, debouncing, undo/redo history, and status bar.
"""
import os
import time
from typing import Optional, List, Tuple, Dict, Any
import numpy as np

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFileDialog, QMessageBox, QStatusBar,
    QLabel, QToolBar, QDialog, QTextBrowser, QPushButton
)

from app.core.image_processor import ImageProcessor
from app.core.image_analyzer import ImageAnalyzer
from app.utils.image_loader import ImageLoader
from app.utils.image_exporter import ImageExporter
from app.ui.image_viewer import ImageViewer, ViewMode
from app.ui.control_panel import ControlPanel
from app.ui.analysis_panel import AnalysisPanel
from app.ui.analysis_window import AnalysisSubWindow
from app.widgets.histogram_widget import HistogramWidget
from app.widgets.statistics_widget import StatisticsWidget
from app.widgets.sobel_analysis_widget import SobelAnalysisWidget
from app.styles.dark_theme import THEME_COLORS
from app.config.branding import (
    APP_NAME, APP_TITLE, APP_SUBTITLE, APP_DESCRIPTION,
    APP_VERSION, APP_ACADEMIC_PROJECT, APP_TECH_STACK
)
from app.resources.icon_manager import IconManager


class MainWindow(QMainWindow):
    """
    Cửa sổ chính của ứng dụng ImageLab Studio.
    Điều phối toàn bộ chu trình xử lý ảnh:
    - Quản lý trạng thái ảnh gốc và ảnh sau khi điều chỉnh
    - Đồng bộ hóa các thanh trượt tham số (Brightness, Contrast, Gamma)
    - Kích hoạt pipeline xử lý tối ưu hóa vectorization trên CPU
    - Cập nhật thời gian thực cho Viewport và 3 cửa sổ phân tích độc lập
    - Quản lý ngăn xếp lịch sử Hoàn tác / Làm lại (Undo / Redo)
    """

    def __init__(self):
        super().__init__()
        # Cấu hình tiêu đề chuẩn và icon nhận diện thương hiệu độc quyền
        self.setWindowTitle(APP_TITLE)
        self.setWindowIcon(IconManager.get("imagelab-logo", size=32))
        self.resize(1400, 880)
        self.setMinimumSize(1000, 650)

        # Trạng thái ảnh kỹ thuật số
        self.current_filepath: Optional[str] = None
        self.original_full_image: Optional[np.ndarray] = None  # Ảnh gốc độ phân giải đầy đủ
        self.preview_image: Optional[np.ndarray] = None        # Ảnh preview proxy tối ưu tốc độ kéo slider
        self.preview_scale_factor: float = 1.0
        self.adjusted_preview_image: Optional[np.ndarray] = None

        # Ngăn xếp lịch sử Undo / Redo lưu bộ ba tham số (brightness, contrast, gamma)
        self.undo_stack: List[Tuple[float, float, float]] = []
        self.redo_stack: List[Tuple[float, float, float]] = []
        self.current_params: Tuple[float, float, float] = (0.0, 1.0, 1.0)
        self.is_history_navigating: bool = False

        # Timer khử rung (Debounce 35ms ~ 30fps) giúp kéo slider mượt mà không nghẽn CPU
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(35)
        self.debounce_timer.timeout.connect(self._execute_pipeline)

        # Timer ghi nhận trạng thái vào Undo stack (300ms sau khi người dùng dừng tay)
        self.history_commit_timer = QTimer(self)
        self.history_commit_timer.setSingleShot(True)
        self.history_commit_timer.setInterval(300)
        self.history_commit_timer.timeout.connect(self._commit_current_state_to_history)

        # Bộ đệm lưu trữ kết quả phân tích để cập nhật cho các cửa sổ độc lập
        self.last_comparison_data: Optional[Dict[str, Any]] = None
        self.last_sobel_components: Optional[Dict[str, Any]] = None

        self._init_ui()
        self._init_analysis_windows()
        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()

        # Khởi tạo trạng thái mặc định đầu tiên vào Undo stack
        self.undo_stack.append(self.current_params)
        self._update_undo_redo_actions()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Horizontal Splitter dividing Viewport (Left) and Tools/Panels (Right)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setHandleWidth(1)
        self.main_splitter.setChildrenCollapsible(False)

        # 1. Left Viewport
        self.image_viewer = ImageViewer(self)
        self.image_viewer.viewModeChanged.connect(self._on_view_mode_changed)
        self.main_splitter.addWidget(self.image_viewer)

        # 2. Right Sidebar: Structured Studio Console
        # Dedicated Control Panel (Top) + Analysis Panel (Bottom)
        self.sidebar_widget = QWidget(self)
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(6)

        # Top Section: Dedicated Control Panel (NO QScrollArea!)
        self.control_panel = ControlPanel(self)
        self.control_panel.parametersChanged.connect(self._on_parameters_changed)
        self.control_panel.resetAllRequested.connect(self.reset_parameters)
        sidebar_layout.addWidget(self.control_panel)

        # Bottom Section: Tabbed Analysis & Diagnostics Panel
        self.analysis_panel = AnalysisPanel(self)
        self.analysis_panel.sobelThresholdChanged.connect(self._on_sobel_threshold_changed)
        sidebar_layout.addWidget(self.analysis_panel, stretch=1)

        self.main_splitter.addWidget(self.sidebar_widget)

        # Analysis workspace receives priority width by default (850px); viewport 550px
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([550, 850])

        main_layout.addWidget(self.main_splitter)

    def _init_analysis_windows(self):
        """Initialize the 3 dedicated floating analysis windows with full resize capability."""
        # 1. Independent Floating Histogram Window (840x580)
        self.win_histogram_widget = HistogramWidget()
        self.win_histogram = AnalysisSubWindow(
            title="Phân tích Histogram 256 Bins",
            icon_name="histogram",
            content_widget=self.win_histogram_widget,
            default_width=840,
            default_height=580,
            parent=self
        )

        # 2. Independent Floating Statistics & Diagnostic Window (720x820)
        self.win_statistics_widget = StatisticsWidget()
        self.win_statistics = AnalysisSubWindow(
            title="Bảng Thống kê & Chẩn đoán Quang học",
            icon_name="statistics",
            content_widget=self.win_statistics_widget,
            default_width=720,
            default_height=820,
            parent=self
        )

        # 3. Independent Floating Sobel Analysis Window (1180x800)
        self.win_sobel_widget = SobelAnalysisWidget()
        self.win_sobel_widget.thresholdChanged.connect(self._on_sobel_threshold_changed)
        self.win_sobel = AnalysisSubWindow(
            title="Phân tích Chi tiết Biên Sobel (8 ô ma trận)",
            icon_name="sobel-edge",
            content_widget=self.win_sobel_widget,
            default_width=1180,
            default_height=800,
            parent=self
        )

        # Connect pop-out requests from AnalysisPanel
        self.analysis_panel.popoutHistogramRequested.connect(self.open_histogram_window)
        self.analysis_panel.popoutStatisticsRequested.connect(self.open_statistics_window)
        self.analysis_panel.popoutSobelRequested.connect(self.open_sobel_window)

    def open_histogram_window(self):
        if self.last_comparison_data:
            self.win_histogram_widget.update_histograms(
                hist_orig=self.last_comparison_data.get("hist_original"),
                hist_adj=self.last_comparison_data.get("hist_adjusted"),
                stats_orig=self.last_comparison_data.get("stats_original"),
                stats_adj=self.last_comparison_data.get("stats_adjusted")
            )
            if hasattr(self.win_histogram_widget, "canvas"):
                self.win_histogram_widget.canvas.draw()
        self.win_histogram.show_and_activate()
        self.statusbar.showMessage("Đã mở cửa sổ Phân tích Histogram độc lập (Kéo mép phóng to/nhỏ tùy ý hoặc nhấn F11).", 4000)

    def open_statistics_window(self):
        if self.last_comparison_data:
            self.win_statistics_widget.update_statistics(self.last_comparison_data)
        self.win_statistics.show_and_activate()
        self.statusbar.showMessage("Đã mở cửa sổ Bảng Thống kê & Chẩn đoán độc lập (Kéo mép phóng to/nhỏ tùy ý hoặc nhấn F11).", 4000)

    def open_sobel_window(self):
        if self.last_sobel_components:
            self.win_sobel_widget.update_sobel_data(self.last_sobel_components)
        self.win_sobel.show_and_activate()
        self.statusbar.showMessage("Đã mở cửa sổ Phân tích Biên Sobel độc lập (Kéo mép phóng to/nhỏ tùy ý hoặc nhấn F11).", 4000)

    def _create_actions(self):
        # File Actions
        self.action_open = QAction("Mở ảnh (Open Image)...", self)
        self.action_open.setIcon(IconManager.get("open-image", size=20))
        self.action_open.setShortcut(QKeySequence("Ctrl+O"))
        self.action_open.triggered.connect(self.open_image_dialog)

        self.action_save = QAction("Lưu ảnh (Save As)...", self)
        self.action_save.setIcon(IconManager.get("save-image", size=20))
        self.action_save.setShortcut(QKeySequence("Ctrl+S"))
        self.action_save.triggered.connect(self.save_image_dialog)
        self.action_save.setEnabled(False)

        self.action_export_png = QAction("Xuất PNG chất lượng cao...", self)
        self.action_export_png.setIcon(IconManager.get("export-image", size=20))
        self.action_export_png.triggered.connect(lambda: self.save_image_dialog(force_ext=".png"))
        self.action_export_png.setEnabled(False)

        self.action_export_jpg = QAction("Xuất JPEG tiêu chuẩn...", self)
        self.action_export_jpg.setIcon(IconManager.get("export-image", size=20))
        self.action_export_jpg.triggered.connect(lambda: self.save_image_dialog(force_ext=".jpg"))
        self.action_export_jpg.setEnabled(False)

        self.action_exit = QAction("Thoát", self)
        self.action_exit.setIcon(IconManager.get("close", size=20))
        self.action_exit.setShortcut(QKeySequence("Ctrl+Q"))
        self.action_exit.triggered.connect(self.close)

        # Edit Actions
        self.action_undo = QAction("Hoàn tác (Undo)", self)
        self.action_undo.setIcon(IconManager.get("undo", size=20))
        self.action_undo.setShortcut(QKeySequence("Ctrl+Z"))
        self.action_undo.triggered.connect(self.undo)
        self.action_undo.setEnabled(False)

        self.action_redo = QAction("Làm lại (Redo)", self)
        self.action_redo.setIcon(IconManager.get("redo", size=20))
        self.action_redo.setShortcut(QKeySequence("Ctrl+Y"))
        self.action_redo.triggered.connect(self.redo)
        self.action_redo.setEnabled(False)

        self.action_reset = QAction("Khôi phục mặc định (Reset)", self)
        self.action_reset.setIcon(IconManager.get("reset", size=20))
        self.action_reset.setShortcut(QKeySequence("Ctrl+Shift+R"))
        self.action_reset.triggered.connect(self.reset_parameters)

        # View Actions
        self.action_fit = QAction("Khung nhìn vừa màn hình (Fit)", self)
        self.action_fit.setIcon(IconManager.get("fit-screen", size=20))
        self.action_fit.setShortcut(QKeySequence("Ctrl+0"))
        self.action_fit.triggered.connect(self.image_viewer._on_fit)

        self.action_100 = QAction("Kích thước thực 100% (1:1)", self)
        self.action_100.setIcon(IconManager.get("actual-size", size=20))
        self.action_100.setShortcut(QKeySequence("Ctrl+1"))
        self.action_100.triggered.connect(self.image_viewer._on_actual)

        # 3 Deep Analysis Domain Actions (Dedicated Floating Resizable Windows)
        self.action_show_hist = QAction("Histogram 256 Bins", self)
        self.action_show_hist.setIcon(IconManager.get("histogram", size=20))
        self.action_show_hist.setShortcut(QKeySequence("F2"))
        self.action_show_hist.setToolTip(
            "<b>Phân tích Histogram 256 Bins (F2)</b><br>"
            "Mở cửa sổ biểu đồ phân bố mức xám độc lập.<br>"
            "<i>Kéo mép phóng to/nhỏ tùy ý hoặc nhấn F11 để mở toàn màn hình.</i>"
        )
        self.action_show_hist.triggered.connect(self.open_histogram_window)

        self.action_show_stats = QAction("Thống kê & Chẩn đoán", self)
        self.action_show_stats.setIcon(IconManager.get("statistics", size=20))
        self.action_show_stats.setShortcut(QKeySequence("F3"))
        self.action_show_stats.setToolTip(
            "<b>Bảng Thống kê & Chẩn đoán (F3)</b><br>"
            "Mở cửa sổ bảng chỉ số quang học và nhận định thuật toán độc lập.<br>"
            "<i>Kéo mép phóng to/nhỏ tùy ý để xem trọn vẹn toàn bộ bảng số liệu.</i>"
        )
        self.action_show_stats.triggered.connect(self.open_statistics_window)

        self.action_show_sobel = QAction("Phân tích biên Sobel", self)
        self.action_show_sobel.setIcon(IconManager.get("sobel-edge", size=20))
        self.action_show_sobel.setShortcut(QKeySequence("F4"))
        self.action_show_sobel.setToolTip(
            "<b>Phân tích Biên Sobel Chuyên sâu (F4)</b><br>"
            "Mở cửa sổ ma trận 8 ô trực quan hóa chi tiết đạo hàm Gx, Gy, Gradient Magnitude và bản đồ biên nhị phân.<br>"
            "<i>Phóng to toàn màn hình để kiểm tra chi tiết cấu trúc biên ảnh.</i>"
        )
        self.action_show_sobel.triggered.connect(self.open_sobel_window)

        # Help Actions
        self.action_about = QAction("Giới thiệu Đồ án & ImageLab", self)
        self.action_about.setIcon(IconManager.get("info", size=20))
        self.action_about.triggered.connect(self.show_about_dialog)

        self.action_docs = QAction("Tài liệu thuật toán toán học", self)
        self.action_docs.setIcon(IconManager.get("help", size=20))
        self.action_docs.triggered.connect(self.show_docs_dialog)

    def _create_menus(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.action_open)
        file_menu.addAction(self.action_save)
        file_menu.addSeparator()
        file_menu.addAction(self.action_export_png)
        file_menu.addAction(self.action_export_jpg)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self.action_undo)
        edit_menu.addAction(self.action_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_reset)

        # View Menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.action_fit)
        view_menu.addAction(self.action_100)
        view_menu.addSeparator()
        view_menu.addAction(self.action_show_hist)
        view_menu.addAction(self.action_show_stats)
        view_menu.addAction(self.action_show_sobel)

        # Help Menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.action_about)
        help_menu.addAction(self.action_docs)

    def _create_toolbar(self):
        toolbar = QToolBar("Main Controls", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # Brand Container với SVG Logo sắc nét
        brand_widget = QWidget(self)
        brand_layout = QHBoxLayout(brand_widget)
        brand_layout.setContentsMargins(4, 2, 10, 2)
        brand_layout.setSpacing(8)

        logo_label = QLabel(self)
        logo_label.setPixmap(IconManager.get_pixmap("imagelab-logo", size=24))
        brand_layout.addWidget(logo_label)

        title_label = QLabel(APP_NAME, self)
        title_label.setStyleSheet(f"font-weight: bold; color: {THEME_COLORS['primary']}; font-size: 13px; letter-spacing: 0.5px;")
        brand_layout.addWidget(title_label)

        toolbar.addWidget(brand_widget)

        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_save)
        toolbar.addSeparator()
        toolbar.addAction(self.action_undo)
        toolbar.addAction(self.action_redo)
        toolbar.addAction(self.action_reset)
        toolbar.addSeparator()
        toolbar.addAction(self.action_fit)
        toolbar.addAction(self.action_100)

        # 3 Dedicated Deep Analysis Actions with clear icons
        toolbar.addSeparator()
        lbl_analysis = QLabel(" Phân tích: ")
        lbl_analysis.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 500;")
        toolbar.addWidget(lbl_analysis)

        toolbar.addAction(self.action_show_hist)
        toolbar.addAction(self.action_show_stats)
        toolbar.addAction(self.action_show_sobel)

    def _create_statusbar(self):
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.lbl_status_file = QLabel("Chưa mở ảnh")
        self.lbl_status_res = QLabel("Kích thước: -- x --")
        self.lbl_status_format = QLabel("Định dạng: --")
        self.lbl_status_perf = QLabel("Độ trễ xử lý: 0.0 ms (CPU)")

        self.statusbar.addWidget(self.lbl_status_file, 2)
        self.statusbar.addPermanentWidget(self.lbl_status_res, 1)
        self.statusbar.addPermanentWidget(self.lbl_status_format, 1)
        self.statusbar.addPermanentWidget(self.lbl_status_perf, 1)

    # -------------------------------------------------------------
    # Image Operations
    # -------------------------------------------------------------
    def open_image_dialog(self):
        """Show Open File dialog."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn ảnh cần xử lý",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp);;All Files (*)"
        )
        if file_path:
            self.load_image_file(file_path)

    def load_image_file(self, file_path: str):
        """Load image from disk and setup workspace."""
        try:
            image = ImageLoader.load_image(file_path)
            self.original_full_image = image
            self.current_filepath = file_path

            # Create preview proxy for fast responsive sliders if image is very large
            self.preview_image, self.preview_scale_factor = ImageLoader.create_preview_proxy(image, max_dimension=1920)

            # Update status bar
            h, w = image.shape[:2]
            channels = image.shape[2] if len(image.shape) == 3 else 1
            filename = os.path.basename(file_path)
            self.lbl_status_file.setText(f"Tệp: {filename}")
            self.lbl_status_res.setText(f"Độ phân giải: {w} × {h} px")
            self.lbl_status_format.setText(f"Kênh màu: {channels}ch (uint8)")

            # Enable save actions
            self.action_save.setEnabled(True)
            self.action_export_png.setEnabled(True)
            self.action_export_jpg.setEnabled(True)

            # Reset sliders and history for new image
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.current_params = (0.0, 1.0, 1.0)
            self.undo_stack.append(self.current_params)
            self._update_undo_redo_actions()

            self.control_panel.set_values(0.0, 1.0, 1.0, block_signals=True)

            # Run full pipeline and fit viewport
            self._execute_pipeline()
            self.image_viewer.canvas.fit_to_screen()
            QTimer.singleShot(60, self.image_viewer.canvas.fit_to_screen)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi mở ảnh", f"Không thể đọc file ảnh:\n{str(e)}")

    def save_image_dialog(self, force_ext: Optional[str] = None):
        """Export image at full original resolution applying the exact parameter pipeline."""
        if self.original_full_image is None:
            QMessageBox.warning(self, "Cảnh báo", "Chưa có ảnh nào được tải để xuất.")
            return

        default_dir = os.path.dirname(self.current_filepath) if self.current_filepath else ""
        orig_name, orig_ext = os.path.splitext(os.path.basename(self.current_filepath or "enhanced_image.png"))
        suggested_name = f"{orig_name}_enhanced{force_ext or orig_ext}"
        default_path = os.path.join(default_dir, suggested_name)

        filter_str = "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;Bitmap (*.bmp);;TIFF Image (*.tif *.tiff)"
        if force_ext == ".png":
            filter_str = "PNG Image (*.png)"
        elif force_ext in (".jpg", ".jpeg"):
            filter_str = "JPEG Image (*.jpg *.jpeg)"

        dest_path, _ = QFileDialog.getSaveFileName(self, "Xuất ảnh sau xử lý", default_path, filter_str)
        if not dest_path:
            return

        try:
            # Recompute at FULL RESOLUTION using exact parameters
            b, c, g = self.current_params
            full_enhanced = ImageProcessor.process_pipeline(
                self.original_full_image,
                brightness=b,
                contrast=c,
                gamma=g
            )

            success = ImageExporter.save_image(full_enhanced, dest_path)
            if success:
                QMessageBox.information(
                    self,
                    "Xuất thành công",
                    f"Ảnh đã được lưu thành công tại:\n{dest_path}\n"
                    f"Độ phân giải đầy đủ: {full_enhanced.shape[1]} × {full_enhanced.shape[0]} px."
                )
        except Exception as e:
            QMessageBox.critical(self, "Lỗi xuất ảnh", f"Không thể lưu file ảnh:\n{str(e)}")

    # -------------------------------------------------------------
    # Processing Pipeline & Debounce Execution
    # -------------------------------------------------------------
    def _on_parameters_changed(self, brightness: float, contrast: float, gamma: float):
        """Called immediately whenever any slider moves."""
        self.current_params = (brightness, contrast, gamma)
        # Restart debounce timer to throttle CPU computation during fast dragging
        self.debounce_timer.start()
        # Restart history timer to commit snapshot once slider stops
        self.history_commit_timer.start()

    def _execute_pipeline(self):
        """
        Executes enhancement pipeline on preview proxy:
        Original Preview -> Brightness + Contrast -> Gamma -> Adjusted Preview -> Analysis & Edge Detection.
        """
        if self.preview_image is None:
            return

        t0 = time.perf_counter()
        b, c, g = self.current_params

        # Step 1 & 2: Process image through pipeline
        self.adjusted_preview_image = ImageProcessor.process_pipeline(
            self.preview_image,
            brightness=b,
            contrast=c,
            gamma=g
        )

        # Step 3: Compute Sobel 8-tile components and unified metadata
        sobel_thresh = self.analysis_panel.get_sobel_threshold()
        sobel_components = ImageProcessor.compute_all_sobel_components(
            self.preview_image,
            self.adjusted_preview_image,
            threshold=sobel_thresh
        )

        # Step 4: Perform full comparative analysis
        comparison_data = ImageAnalyzer.compare_images(
            self.preview_image,
            self.adjusted_preview_image,
            sobel_threshold=sobel_thresh
        )

        # Lưu trữ bộ đệm để các cửa sổ phân tích độc lập luôn nhận được dữ liệu mới nhất
        self.last_comparison_data = comparison_data
        self.last_sobel_components = sobel_components

        # Step 5: Update Viewport
        self.image_viewer.set_images(self.preview_image, self.adjusted_preview_image)
        self.image_viewer.set_sobel_images(sobel_components["mag_orig"], sobel_components["mag_adj"])

        # Step 6: Update Analysis Workspace (Histogram, Sobel 8-Tile Grid, and Statistics)
        self.analysis_panel.update_analysis_data(comparison_data, sobel_components)

        # Step 7: Đồng bộ hóa dữ liệu thời gian thực tới 3 cửa sổ phân tích độc lập
        if hasattr(self, "win_histogram_widget") and self.win_histogram_widget is not None:
            self.win_histogram_widget.update_histograms(
                hist_orig=comparison_data.get("hist_original"),
                hist_adj=comparison_data.get("hist_adjusted"),
                stats_orig=comparison_data.get("stats_original"),
                stats_adj=comparison_data.get("stats_adjusted")
            )
        if hasattr(self, "win_statistics_widget") and self.win_statistics_widget is not None:
            self.win_statistics_widget.update_statistics(comparison_data)
        if hasattr(self, "win_sobel_widget") and self.win_sobel_widget is not None:
            self.win_sobel_widget.update_sobel_data(sobel_components)

        # Measure performance latency
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        self.lbl_status_perf.setText(f"Độ trễ xử lý: {elapsed_ms:.1f} ms (CPU Vectorized)")

    def _on_sobel_threshold_changed(self, threshold: float):
        """Called when Sobel threshold changes."""
        self._execute_pipeline()

    def _on_view_mode_changed(self, mode: ViewMode):
        """Handle view mode switches."""
        pass

    # -------------------------------------------------------------
    # State & Undo / Redo Management
    # -------------------------------------------------------------
    def _commit_current_state_to_history(self):
        """Commit current parameter state to undo stack when idle."""
        if self.is_history_navigating:
            return

        if not self.undo_stack or self.undo_stack[-1] != self.current_params:
            self.undo_stack.append(self.current_params)
            self.redo_stack.clear()
            self._update_undo_redo_actions()

    def undo(self):
        """Undo last parameter adjustment."""
        if len(self.undo_stack) <= 1:
            return

        self.is_history_navigating = True
        current = self.undo_stack.pop()
        self.redo_stack.append(current)

        prev = self.undo_stack[-1]
        self.current_params = prev
        self.control_panel.set_values(prev[0], prev[1], prev[2], block_signals=True)
        self._execute_pipeline()

        self.is_history_navigating = False
        self._update_undo_redo_actions()

    def redo(self):
        """Redo previously undone parameter adjustment."""
        if not self.redo_stack:
            return

        self.is_history_navigating = True
        nxt = self.redo_stack.pop()
        self.undo_stack.append(nxt)

        self.current_params = nxt
        self.control_panel.set_values(nxt[0], nxt[1], nxt[2], block_signals=True)
        self._execute_pipeline()

        self.is_history_navigating = False
        self._update_undo_redo_actions()

    def reset_parameters(self):
        """Reset all parameters to default (0, 1.0, 1.0)."""
        defaults = (0.0, 1.0, 1.0)
        if self.current_params == defaults:
            return

        self.control_panel.set_values(0.0, 1.0, 1.0, block_signals=True)
        self.current_params = defaults
        self._execute_pipeline()
        self._commit_current_state_to_history()

    def _update_undo_redo_actions(self):
        self.action_undo.setEnabled(len(self.undo_stack) > 1)
        self.action_redo.setEnabled(len(self.redo_stack) > 0)

    # -------------------------------------------------------------
    # Dialogs & Documentation
    # -------------------------------------------------------------
    def show_about_dialog(self):
        """Hiển thị hộp thoại giới thiệu đồ án và thông tin nhận diện thương hiệu."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Giới thiệu - {APP_NAME}")
        dialog.resize(560, 480)
        layout = QVBoxLayout(dialog)

        # Header with Logo & Brand
        header = QHBoxLayout()
        logo_lbl = QLabel(dialog)
        logo_lbl.setPixmap(IconManager.get_pixmap("imagelab-logo", size=48))
        header.addWidget(logo_lbl)

        info_box = QVBoxLayout()
        title_lbl = QLabel(APP_NAME, dialog)
        title_lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {THEME_COLORS['primary']};")
        subtitle_lbl = QLabel(f"Phiên bản {APP_VERSION} · {APP_SUBTITLE}", dialog)
        subtitle_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
        info_box.addWidget(title_lbl)
        info_box.addWidget(subtitle_lbl)
        header.addLayout(info_box)
        header.addStretch()
        layout.addLayout(header)

        text = QTextBrowser()
        text.setOpenExternalLinks(True)
        text.setHtml(f"""
            <hr style='border: 1px solid #303743;'/>
            <p><b>Mục tiêu:</b> {APP_DESCRIPTION}</p>
            <p><b>Đồ án môn học:</b> {APP_ACADEMIC_PROJECT}</p>
            <p><b>Công nghệ cốt lõi:</b> {APP_TECH_STACK}</p>
            <h4 style='color: #8B5CF6; margin-bottom: 4px;'>Tính năng chuyên sâu:</h4>
            <ul style='margin-top: 4px; line-height: 1.5;'>
                <li><b>Độ sáng & Độ tương phản có tâm 127.5:</b> <code>I_out = clip(α · (I - 127.5) + 127.5 + β, 0, 255)</code></li>
                <li><b>Hiệu chỉnh Gamma LUT:</b> Tăng tốc tính toán qua bảng tra cứu trước 256 phần tử.</li>
                <li><b>Phân tích Histogram 256 Bins:</b> Trực quan hóa tần suất và so sánh trên cùng hệ trục.</li>
                <li><b>Phát hiện biên Sobel:</b> Ma trận 8 ô so sánh Gx, Gy, Gradient Magnitude và bản đồ biên nhị phân trên thang đo chuẩn hóa công bằng.</li>
                <li><b>Cửa sổ phân tích độc lập:</b> Cho phép phóng to/thu nhỏ tùy ý hoặc toàn màn hình.</li>
                <li><b>Bộ biểu tượng Vector SVG:</b> Thiết kế Lucide-inspired hiện đại, đồng nhất 100%.</li>
            </ul>
        """)
        layout.addWidget(text)

        btn_close = QPushButton("Đóng", dialog)
        btn_close.setIcon(IconManager.get("close", size=16))
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        dialog.exec()

    def show_docs_dialog(self):
        """Hiển thị tài liệu toán học và cơ sở lý thuyết thuật toán."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Tài liệu thuật toán toán học - {APP_NAME}")
        dialog.resize(620, 500)
        layout = QVBoxLayout(dialog)

        text = QTextBrowser()
        text.setHtml("""
            <h3 style='color: #60A5FA;'>Cơ sở lý thuyết & Công thức toán học</h3>
            <hr style='border: 1px solid #303743;'/>
            <p><b>1. Biến đổi Tuyến tính Độ sáng & Độ tương phản có tâm bảo toàn:</b></p>
            <pre style='background: #191D24; padding: 8px; border-radius: 4px; color: #34D399;'>
I_out(x, y) = clip(α · (I_orig(x, y) - 127.5) + 127.5 + β, 0, 255)
Trong đó:
  - α: Hệ số tương phản (Contrast gain), dải [0.0, 3.0]
  - β: Độ dịch chuyển độ sáng (Brightness offset), dải [-100, 100]
  - 127.5: Tâm mức xám trung bình giúp mở rộng tương phản đều về hai phía
  - clip: Giới hạn nghiêm ngặt điểm ảnh trong đoạn uint8 [0, 255]
            </pre>

            <p><b>2. Hiệu chỉnh Gamma Phi tuyến qua bảng tra cứu LUT:</b></p>
            <pre style='background: #191D24; padding: 8px; border-radius: 4px; color: #34D399;'>
I_gamma = 255 · (I / 255)^(1 / γ)
Tối ưu hóa: Bảng tra cứu trước LUT gồm 256 giá trị, độ phức tạp O(1)/pixel.
            </pre>

            <p><b>3. Toán tử Gradient phát hiện biên Sobel:</b></p>
            <pre style='background: #191D24; padding: 8px; border-radius: 4px; color: #34D399;'>
Gx = Sobel_x(I, 3x3, CV_32F)
Gy = Sobel_y(I, 3x3, CV_32F)
|G| = sqrt(Gx² + Gy²)

Định lý bất biến quang học:
∇(I + β) = ∇I  (Độ sáng không làm thay đổi cường độ biên)
∇(α · I) = α · ∇I (Độ tương phản khuếch đại tuyến tính độ dốc biên)
            </pre>
        """)
        layout.addWidget(text)

        btn_close = QPushButton("Đóng", dialog)
        btn_close.setIcon(IconManager.get("close", size=16))
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        dialog.exec()

    def showEvent(self, event):
        super().showEvent(event)
        self.main_splitter.setSizes([550, 850])

