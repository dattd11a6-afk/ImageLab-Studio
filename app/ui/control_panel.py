"""
ImageLab Studio - Control Panel
Dedicated parameter enhancement console for Brightness, Contrast (Centered 0.0-3.0), and Gamma.
Direct layout without QScrollArea for immediate, unhindered adjustment.
"""
from typing import Optional, Dict
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QPushButton, QFrame
)
from app.widgets.slider_widget import LabeledSlider
from app.styles.dark_theme import THEME_COLORS
from app.resources.icon_manager import IconManager


class ControlPanel(QWidget):
    """
    Dedicated control panel for image brightness, contrast, and gamma parameters:
    - Brightness: [-100, +100], default 0.0
    - Contrast (alpha): [0.00, 3.00], default 1.00
    - Gamma: [0.10, 3.00], default 1.00
    """
    parametersChanged = pyqtSignal(float, float, float)
    resetAllRequested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 6, 10, 6)
        main_layout.setSpacing(6)

        # Main Container Frame for visual separation
        container = QFrame(self)
        container.setObjectName("panelFrame")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(12, 8, 12, 10)
        container_layout.setSpacing(8)

        # Header Row
        header = QHBoxLayout()
        title = QLabel("◈ ĐIỀU CHỈNH THÔNG SỐ (ENHANCEMENT)")
        title.setStyleSheet(
            f"font-weight: bold; color: {THEME_COLORS['primary']}; "
            "font-size: 12px; letter-spacing: 0.5px;"
        )
        header.addWidget(title)
        header.addStretch()

        self.btn_reset_all_top = QPushButton("Khôi phục mặc định")
        self.btn_reset_all_top.setIcon(IconManager.get("reset", size=16))
        self.btn_reset_all_top.setObjectName("resetBtn")
        self.btn_reset_all_top.setToolTip("Khôi phục toàn bộ tham số về mặc định (B: 0, C: 1.0, G: 1.0)")
        self.btn_reset_all_top.clicked.connect(self.reset_all)
        header.addWidget(self.btn_reset_all_top)

        container_layout.addLayout(header)

        # 1. Core Adjustment Sliders
        sliders_box = QGroupBox("CÁC THUẬT TOÁN ĐIỀU CHỈNH CỐT LÕI")
        sliders_layout = QVBoxLayout(sliders_box)
        sliders_layout.setContentsMargins(10, 12, 10, 8)
        sliders_layout.setSpacing(6)

        # Brightness Slider (-100 to +100, default 0, step 1)
        self.slider_brightness = LabeledSlider(
            title="Độ sáng (Brightness - Beta)",
            min_val=-100.0,
            max_val=100.0,
            default_val=0.0,
            step=1.0,
            decimals=0,
            unit="",
            icon_name="brightness"
        )
        self.slider_brightness.setToolTip(
            "<b>Độ sáng (Brightness - β)</b><br>"
            "Cộng/trừ trực tiếp hằng số β vào toàn bộ ma trận pixel: <i>I_out = clip(I_in + β, 0, 255)</i>.<br>"
            "Làm sáng hoặc tối toàn ảnh, dịch chuyển toàn bộ phổ Histogram sang phải hoặc trái."
        )
        self.slider_brightness.valueChanged.connect(self._on_value_changed)
        sliders_layout.addWidget(self.slider_brightness)

        # Contrast Slider (0.00 to 3.00, default 1.00, step 0.05, 2 decimals)
        self.slider_contrast = LabeledSlider(
            title="Độ tương phản (Contrast - Alpha)",
            min_val=0.00,
            max_val=3.00,
            default_val=1.00,
            step=0.05,
            decimals=2,
            unit="",
            icon_name="contrast"
        )
        self.slider_contrast.setToolTip(
            "<b>Độ tương phản (Contrast - α)</b><br>"
            "Khuếch đại độ dốc quanh tâm mức xám trung bình 127.5: <i>I_out = clip(α · (I_in - 127.5) + 127.5, 0, 255)</i>.<br>"
            "Tăng khoảng cách giữa vùng sáng và vùng tối, kéo giãn độ rộng phổ Histogram."
        )
        self.slider_contrast.valueChanged.connect(self._on_value_changed)
        sliders_layout.addWidget(self.slider_contrast)

        # Gamma Slider (0.10 to 3.00, default 1.00, step 0.05, 2 decimals)
        self.slider_gamma = LabeledSlider(
            title="Hiệu chỉnh Gamma (Gamma LUT)",
            min_val=0.10,
            max_val=3.00,
            default_val=1.00,
            step=0.05,
            decimals=2,
            unit="",
            icon_name="gamma"
        )
        self.slider_gamma.setToolTip(
            "<b>Hiệu chỉnh Gamma (Gamma - γ)</b><br>"
            "Biến đổi phi tuyến theo hàm lũy thừa qua bảng tra cứu LUT: <i>I_out = 255 · (I_in / 255)^(1/γ)</i>.<br>"
            "Nâng sáng vùng bóng tối mà không làm cháy vùng sáng, giữ nguyên hai đầu dải động [0, 255]."
        )
        self.slider_gamma.valueChanged.connect(self._on_value_changed)
        sliders_layout.addWidget(self.slider_gamma)

        container_layout.addWidget(sliders_box)

        # 2. Quick Presets Row (Vector SVG Icons, No Emoji)
        presets_box = QGroupBox("THIẾT LẬP NHANH (PRESETS)")
        presets_layout = QHBoxLayout(presets_box)
        presets_layout.setContentsMargins(8, 12, 8, 8)
        presets_layout.setSpacing(6)

        self.btn_preset_auto = QPushButton("Tăng tương phản")
        self.btn_preset_auto.setIcon(IconManager.get("preset-contrast", size=16))
        self.btn_preset_auto.setToolTip("<b>Tăng độ tương phản</b><br>Tương phản α = 1.50, Độ sáng β = 0, Gamma γ = 1.00.")
        self.btn_preset_auto.clicked.connect(lambda: self.apply_preset(0.0, 1.50, 1.00))
        presets_layout.addWidget(self.btn_preset_auto)

        self.btn_preset_shadow = QPushButton("Nâng vùng tối")
        self.btn_preset_shadow.setIcon(IconManager.get("preset-shadows", size=16))
        self.btn_preset_shadow.setToolTip("<b>Nâng sáng vùng bóng tối</b><br>Tương phản α = 1.10, Độ sáng β = +15, Gamma γ = 1.40.")
        self.btn_preset_shadow.clicked.connect(lambda: self.apply_preset(15.0, 1.10, 1.40))
        presets_layout.addWidget(self.btn_preset_shadow)

        self.btn_preset_highkey = QPushButton("High Key")
        self.btn_preset_highkey.setIcon(IconManager.get("preset-high-key", size=16))
        self.btn_preset_highkey.setToolTip("<b>Phong cách High Key (Tươi sáng)</b><br>Tương phản α = 1.20, Độ sáng β = +25, Gamma γ = 1.20.")
        self.btn_preset_highkey.clicked.connect(lambda: self.apply_preset(25.0, 1.20, 1.20))
        presets_layout.addWidget(self.btn_preset_highkey)

        self.btn_preset_lowkey = QPushButton("Low Key")
        self.btn_preset_lowkey.setIcon(IconManager.get("preset-low-key", size=16))
        self.btn_preset_lowkey.setToolTip("<b>Phong cách Low Key (Huyền bí)</b><br>Tương phản α = 1.35, Độ sáng β = -25, Gamma γ = 0.85.")
        self.btn_preset_lowkey.clicked.connect(lambda: self.apply_preset(-25.0, 1.35, 0.85))
        presets_layout.addWidget(self.btn_preset_lowkey)

        container_layout.addWidget(presets_box)

        main_layout.addWidget(container)

    def get_values(self) -> Dict[str, float]:
        """Return current values as a dictionary."""
        return {
            "brightness": self.slider_brightness.value(),
            "contrast": self.slider_contrast.value(),
            "gamma": self.slider_gamma.value()
        }

    def set_values(self, brightness: float, contrast: float, gamma: float, block_signals: bool = False):
        """Set all slider values."""
        if block_signals:
            self.slider_brightness.blockSignals(True)
            self.slider_contrast.blockSignals(True)
            self.slider_gamma.blockSignals(True)

        self.slider_brightness.setValue(brightness)
        self.slider_contrast.setValue(contrast)
        self.slider_gamma.setValue(gamma)

        if block_signals:
            self.slider_brightness.blockSignals(False)
            self.slider_contrast.blockSignals(False)
            self.slider_gamma.blockSignals(False)

    def apply_preset(self, b: float, c: float, g: float):
        """Apply preset configuration."""
        self.set_values(b, c, g)

    def reset_all(self):
        """Reset all parameters to default values."""
        self.slider_brightness.reset_to_default()
        self.slider_contrast.reset_to_default()
        self.slider_gamma.reset_to_default()
        self.resetAllRequested.emit()

    def _on_value_changed(self, _val: float):
        b = self.slider_brightness.value()
        c = self.slider_contrast.value()
        g = self.slider_gamma.value()
        self.parametersChanged.emit(b, c, g)
