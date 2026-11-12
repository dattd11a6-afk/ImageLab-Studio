"""
ImageLab Studio - Custom Labeled Slider Widget
Thành phần thanh trượt kết hợp ô nhập số chính xác và nút khôi phục độc lập.
Thiết kế hai hàng (Two-Row Layout) chuyên nghiệp, loại bỏ hoàn toàn hiện tượng chồng đè giao diện.
"""
from typing import Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QDoubleSpinBox, QPushButton
)
from app.resources.icon_manager import IconManager


class LabeledSlider(QWidget):
    """
    Thành phần điều khiển tham số quang học hai tầng:
    - Tầng 1 (Header Row): Biểu tượng + Tiêu đề (Bên trái) | Ô nhập số QDoubleSpinBox (80px) + Nút Reset SVG (Bên phải).
    - Tầng 2 (Slider Row): Thanh trượt QSlider chiếm 100% chiều ngang, kéo mượt mà.

    Cơ chế đồng bộ hóa hai chiều (Bidirectional Sync):
    - Khi kéo QSlider: Chuyển đổi giá trị int sang float theo multiplier, chặn tạm thời tín hiệu
      (blockSignals) của QDoubleSpinBox để tránh tạo vòng lặp đệ quy tín hiệu (Signal Feedback Loop).
    - Khi thay đổi QDoubleSpinBox: Cập nhật vị trí con trượt QSlider tương ứng.
    """
    valueChanged = pyqtSignal(float)

    def __init__(
        self,
        title: str,
        min_val: float,
        max_val: float,
        default_val: float,
        step: float = 1.0,
        decimals: int = 0,
        unit: str = "",
        icon_name: Optional[str] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.default_val = float(default_val)
        self.step = float(step)
        self.decimals = int(decimals)
        self.unit = unit
        self.icon_name = icon_name

        # Hệ số nhân ánh xạ giá trị số thực float sang miền số nguyên int của QSlider
        # Ví dụ: decimals=2 -> multiplier=100 (giá trị 1.45 thành 145 trên thanh trượt)
        self.multiplier = 10 ** self.decimals

        self._init_ui(title)

    def _init_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 8)
        layout.setSpacing(5)

        # Hàng 1 (Header Row): Tiêu đề và icon bên trái, ô nhập số và nút Reset bên phải
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        # Biểu tượng SVG nhận diện tham số (nếu có)
        if self.icon_name:
            icon_lbl = QLabel(self)
            icon_lbl.setPixmap(IconManager.get_pixmap(self.icon_name, size=16))
            header_layout.addWidget(icon_lbl)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: 600; color: #F1F5F9; font-size: 12px;")
        header_layout.addWidget(self.title_label, stretch=1)

        # Ô nhập số chính xác QDoubleSpinBox (cố định tối thiểu 80px, không bị co ép)
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(self.min_val, self.max_val)
        self.spinbox.setSingleStep(self.step)
        self.spinbox.setDecimals(self.decimals)
        self.spinbox.setValue(self.default_val)
        self.spinbox.setMinimumWidth(80)
        self.spinbox.setAlignment(Qt.AlignmentFlag.AlignRight)
        if self.unit:
            self.spinbox.setSuffix(f" {self.unit}")
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        header_layout.addWidget(self.spinbox)

        # Nút khôi phục Reset với Vector SVG Icon xoay ngược (Quy chuẩn icon nút nhỏ: SVG 16px)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setIcon(IconManager.get("reset", size=16))
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.setToolTip(f"Khôi phục {title} về mặc định ({self.default_val}{self.unit})")
        self.reset_btn.clicked.connect(self.reset_to_default)
        header_layout.addWidget(self.reset_btn)

        layout.addLayout(header_layout)

        # Hàng 2 (Slider Row): Thanh trượt chiếm trọn 100% chiều rộng khung
        slider_layout = QHBoxLayout()
        slider_layout.setContentsMargins(0, 0, 0, 0)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        slider_min = int(round(self.min_val * self.multiplier))
        slider_max = int(round(self.max_val * self.multiplier))
        self.slider.setRange(slider_min, slider_max)
        self.slider.setSingleStep(max(1, int(round(self.step * self.multiplier))))
        self.slider.setValue(int(round(self.default_val * self.multiplier)))
        self.slider.valueChanged.connect(self._on_slider_changed)
        slider_layout.addWidget(self.slider)

        layout.addLayout(slider_layout)

    def value(self) -> float:
        """Lấy giá trị hiện tại của tham số dưới dạng số thực float."""
        return float(self.spinbox.value())

    def setValue(self, val: float):
        """
        Gán giá trị mới cho tham số có kẹp biên bảo vệ và đồng bộ hai điều khiển.
        Sử dụng blockSignals để ngăn chặn phát sinh tín hiệu lặp không cần thiết.
        """
        clamped = max(self.min_val, min(self.max_val, float(val)))
        if abs(self.value() - clamped) < 1e-5:
            return

        self.spinbox.blockSignals(True)
        self.slider.blockSignals(True)

        self.spinbox.setValue(clamped)
        self.slider.setValue(int(round(clamped * self.multiplier)))

        self.spinbox.blockSignals(False)
        self.slider.blockSignals(False)

        self.valueChanged.emit(clamped)

    def reset_to_default(self):
        """Khôi phục tham số về giá trị mặc định ban đầu."""
        self.setValue(self.default_val)

    def _on_slider_changed(self, int_val: int):
        """Xử lý sự kiện khi người dùng kéo thanh trượt QSlider."""
        float_val = int_val / self.multiplier
        if self.decimals == 0:
            float_val = round(float_val)

        # Chặn tín hiệu của spinbox khi cập nhật từ slider để tránh phản hồi kép
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(float_val)
        self.spinbox.blockSignals(False)

        self.valueChanged.emit(float_val)

    def _on_spinbox_changed(self, float_val: float):
        """Xử lý sự kiện khi người dùng nhập số trực tiếp vào QDoubleSpinBox."""
        int_val = int(round(float_val * self.multiplier))

        # Chặn tín hiệu của slider khi cập nhật từ spinbox
        self.slider.blockSignals(True)
        self.slider.setValue(int_val)
        self.slider.blockSignals(False)

        self.valueChanged.emit(float_val)
