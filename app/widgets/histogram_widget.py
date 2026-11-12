"""
ImageLab Studio - Histogram Widget
Matplotlib FigureCanvas displaying 256-bin Grayscale Histograms
with Mean/Median vertical indicators and integrated quantitative optical metrics.
"""
import os
import tempfile
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib_imagelab"))

from typing import Optional, Dict, Any
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QRadioButton, QButtonGroup, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from app.styles.dark_theme import THEME_COLORS


class HistogramWidget(QWidget):
    """
    Renders 256-bin intensity histograms comparing Original and Adjusted images on a shared axis.
    Displays:
    - 256-bin Grayscale curves for Original (Dashed gray) vs Adjusted (Vibrant blue)
    - Vertical Mean and Median markers
    - Summary quantitative optical statistics table (Mean, Median, Std, Min, Max, Dark %, Highlight %, Black/White Clipping)
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

        self.hist_orig: Optional[np.ndarray] = None
        self.hist_adj: Optional[np.ndarray] = None
        self.stats_orig: Optional[Dict[str, float]] = None
        self.stats_adj: Optional[Dict[str, float]] = None
        self.mean_orig: float = 0.0
        self.mean_adj: float = 0.0
        self.median_orig: float = 0.0
        self.median_adj: float = 0.0

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 8, 8, 12)
        layout.setSpacing(8)

        # Header bar
        header = QHBoxLayout()
        header.setContentsMargins(4, 2, 4, 2)

        title = QLabel("BIỂU ĐỒ PHÂN BỐ MỨC XÁM (HISTOGRAM 256 BINS)")
        title.setStyleSheet(f"font-weight: bold; color: {THEME_COLORS['primary']}; font-size: 11px; letter-spacing: 0.5px;")
        header.addWidget(title)
        header.addStretch()

        self.rb_count = QRadioButton("Số lượng pixel (Count)")
        self.rb_count.setChecked(True)
        self.rb_count.setStyleSheet("color: #F1F5F9; font-size: 11px;")

        self.rb_norm = QRadioButton("Tần suất chuẩn hóa (Normalized)")
        self.rb_norm.setStyleSheet("color: #F1F5F9; font-size: 11px;")

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.rb_count, 0)
        self.mode_group.addButton(self.rb_norm, 1)
        self.mode_group.idClicked.connect(self._on_mode_toggled)

        header.addWidget(self.rb_count)
        header.addWidget(self.rb_norm)
        layout.addLayout(header)

        # Matplotlib Figure Canvas
        self.figure = Figure(figsize=(5.5, 3.2), dpi=100)
        self.figure.patch.set_facecolor(THEME_COLORS["sidebar"])

        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        self.canvas.setMinimumHeight(240)
        layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot(111)
        self._setup_axes()

        # Quantitative Summary Table for Histogram
        table_lbl = QLabel("BẢNG THỐNG KÊ QUANG HỌC HISTOGRAM")
        table_lbl.setStyleSheet(f"font-weight: bold; color: {THEME_COLORS['accent_hover']}; font-size: 11px; margin-top: 4px;")
        layout.addWidget(table_lbl)

        self.table_stats = QTableWidget()
        self.table_stats.setColumnCount(4)
        self.table_stats.setHorizontalHeaderLabels([
            "Chỉ số quang học (Metric)",
            "Ảnh gốc",
            "Ảnh đã chỉnh",
            "Độ lệch (Δ)"
        ])
        self.table_stats.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_stats.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table_stats.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table_stats.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table_stats.setColumnWidth(1, 95)
        self.table_stats.setColumnWidth(2, 95)
        self.table_stats.setColumnWidth(3, 95)
        self.table_stats.verticalHeader().setVisible(False)
        self.table_stats.verticalHeader().setDefaultSectionSize(30)
        self.table_stats.setAlternatingRowColors(True)
        self.table_stats.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_stats.setFixedHeight(275)
        layout.addWidget(self.table_stats)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _setup_axes(self):
        """Configure dark styling on Matplotlib axes."""
        self.ax.set_facecolor(THEME_COLORS["panel"])
        self.ax.set_xlim(0, 255)
        self.ax.tick_params(colors=THEME_COLORS["text_secondary"], labelsize=9)
        self.ax.grid(True, linestyle="--", alpha=0.2, color="#475569")

        for spine in self.ax.spines.values():
            spine.set_color(THEME_COLORS["border"])

        self.ax.set_xlabel("Mức xám Pixel Intensity (0 – 255)", color=THEME_COLORS["text_secondary"], fontsize=9, labelpad=4)
        y_label = "Số lượng Pixel (Count)" if self.rb_count.isChecked() else "Tần suất (Frequency)"
        self.ax.set_ylabel(y_label, color=THEME_COLORS["text_secondary"], fontsize=9, labelpad=4)
        self.figure.tight_layout(pad=1.2)

    def update_histograms(
        self,
        hist_orig: np.ndarray,
        hist_adj: np.ndarray,
        stats_orig: Optional[Dict[str, float]] = None,
        stats_adj: Optional[Dict[str, float]] = None
    ):
        """Update histogram plot data and redraw canvas."""
        self.hist_orig = hist_orig
        self.hist_adj = hist_adj
        self.stats_orig = stats_orig
        self.stats_adj = stats_adj

        if stats_orig:
            self.mean_orig = stats_orig.get("mean", 0.0)
            self.median_orig = stats_orig.get("median", 0.0)
        if stats_adj:
            self.mean_adj = stats_adj.get("mean", 0.0)
            self.median_adj = stats_adj.get("median", 0.0)

        self.redraw_plot()
        self._update_table()

    def _on_mode_toggled(self, _id: int):
        self.redraw_plot()

    def redraw_plot(self):
        """Redraw histogram curves and reference markers."""
        self.ax.clear()
        self._setup_axes()

        if self.hist_orig is None or self.hist_adj is None:
            self.ax.text(
                128, 0.5, "Mở ảnh để quan sát Histogram",
                color=THEME_COLORS["text_muted"],
                horizontalalignment='center',
                verticalalignment='center',
                transform=self.ax.get_xaxis_transform()
            )
            self.canvas.draw_idle()
            return

        x = np.arange(256)
        y_orig = self.hist_orig.astype(np.float64)
        y_adj = self.hist_adj.astype(np.float64)

        if self.rb_norm.isChecked():
            sum_o = np.sum(y_orig)
            sum_a = np.sum(y_adj)
            if sum_o > 0:
                y_orig = y_orig / sum_o
            if sum_a > 0:
                y_adj = y_adj / sum_a

        # 1. Original Histogram (Muted Slate Outline & faint fill)
        self.ax.plot(
            x, y_orig,
            color=THEME_COLORS["histogram_orig"],
            linewidth=1.2,
            linestyle="--",
            label="Ảnh gốc (Original)",
            alpha=0.75
        )
        self.ax.fill_between(x, y_orig, 0, color=THEME_COLORS["histogram_orig"], alpha=0.10)

        # 2. Adjusted Histogram (Vibrant Sky Blue Outline & fill)
        self.ax.plot(
            x, y_adj,
            color=THEME_COLORS["histogram_adj"],
            linewidth=1.8,
            label="Ảnh đã chỉnh (Adjusted)"
        )
        self.ax.fill_between(x, y_adj, 0, color=THEME_COLORS["histogram_adj"], alpha=0.25)

        # 3. Reference Lines: Mean & Median
        if self.mean_orig > 0:
            self.ax.axvline(
                self.mean_orig, color="#94A3B8", linestyle=":", linewidth=1.0, alpha=0.7,
                label=f"Mean Gốc: {self.mean_orig:.1f}"
            )
        if self.mean_adj > 0:
            self.ax.axvline(
                self.mean_adj, color="#60A5FA", linestyle="-.", linewidth=1.2, alpha=0.9,
                label=f"Mean Chỉnh: {self.mean_adj:.1f}"
            )
        if self.median_adj > 0 and abs(self.median_adj - self.mean_adj) > 2.0:
            self.ax.axvline(
                self.median_adj, color="#FBBF24", linestyle="--", linewidth=1.0, alpha=0.7,
                label=f"Median Chỉnh: {self.median_adj:.0f}"
            )

        max_y = max(float(np.max(y_orig)), float(np.max(y_adj)), 1e-4)
        self.ax.set_ylim(0, max_y * 1.15)

        legend = self.ax.legend(
            loc="upper right",
            facecolor=THEME_COLORS["panel"],
            edgecolor=THEME_COLORS["border"],
            fontsize=8,
            labelcolor=THEME_COLORS["text_primary"]
        )
        legend.get_frame().set_alpha(0.85)

        self.figure.tight_layout(pad=1.2)
        self.canvas.draw()

    def _update_table(self):
        """Populate quantitative summary table with Phase 3 metrics."""
        if not self.stats_orig or not self.stats_adj:
            return

        so = self.stats_orig
        sa = self.stats_adj

        rows = [
            ("Mean (Cường độ sáng trung bình)", so["mean"], sa["mean"], sa["mean"] - so["mean"], "float"),
            ("Median (Giá trị trung vị mức xám)", so["median"], sa["median"], sa["median"] - so["median"], "int"),
            ("Standard Deviation (Độ lệch chuẩn σ)", so["std"], sa["std"], sa["std"] - so["std"], "float"),
            ("Min / Max Intensity (Dải cực trị)", f"{int(so['min'])} / {int(so['max'])}", f"{int(sa['min'])} / {int(sa['max'])}", sa["dynamic_range"] - so["dynamic_range"], "range"),
            ("Dark Pixels (<30 mức xám)", so["dark_pct"], sa["dark_pct"], sa["dark_pct"] - so["dark_pct"], "pct"),
            ("Highlight Pixels (>225 mức xám)", so["highlight_pct"], sa["highlight_pct"], sa["highlight_pct"] - so["highlight_pct"], "pct"),
            ("Black Clipping (Bết tối mức 0)", so["clip_black_pct"], sa["clip_black_pct"], sa["clip_black_pct"] - so["clip_black_pct"], "pct"),
            ("White Clipping (Cháy sáng mức 255)", so["clip_white_pct"], sa["clip_white_pct"], sa["clip_white_pct"] - so["clip_white_pct"], "pct"),
        ]

        self.table_stats.setRowCount(len(rows))
        for r_idx, (name, v_o, v_a, d_val, f_type) in enumerate(rows):
            item_name = QTableWidgetItem(name)
            item_name.setForeground(Qt.GlobalColor.white)
            self.table_stats.setItem(r_idx, 0, item_name)

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
            else:  # range
                str_o = str(v_o)
                str_a = str(v_a)
                str_d = f"ΔRange: {int(d_val):+d}"

            item_o = QTableWidgetItem(str_o)
            item_o.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_stats.setItem(r_idx, 1, item_o)

            item_a = QTableWidgetItem(str_a)
            item_a.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_a.setForeground(Qt.GlobalColor.cyan)
            self.table_stats.setItem(r_idx, 2, item_a)

            item_d = QTableWidgetItem(str_d)
            item_d.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if isinstance(d_val, (int, float)):
                if abs(d_val) < 1e-4:
                    item_d.setForeground(Qt.GlobalColor.gray)
                elif d_val > 0:
                    item_d.setForeground(Qt.GlobalColor.green)
                else:
                    item_d.setForeground(Qt.GlobalColor.yellow)
            self.table_stats.setItem(r_idx, 3, item_d)
