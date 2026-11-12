"""
ImageLab Studio - Image Loader & Converter
Handles file loading with Unicode path support, validation, preview generation, and Qt QImage conversion.
"""
import os
from typing import Tuple, Optional
import numpy as np
import cv2
from PyQt6.QtGui import QImage, QPixmap


class ImageLoader:
    """
    Robust image loader supporting JPG, JPEG, PNG, BMP, TIFF with full Unicode path compatibility.
    """

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

    @classmethod
    def load_image(cls, file_path: str) -> np.ndarray:
        """
        Load an image from disk into a BGR uint8 NumPy array.
        Uses np.fromfile + cv2.imdecode to natively support non-ASCII and Unicode paths on Windows.

        Args:
            file_path: Absolute or relative path to image file.

        Returns:
            BGR uint8 numpy array.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file is unsupported or corrupt.
        """
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported format '{ext}'. Supported formats: {', '.join(sorted(cls.SUPPORTED_EXTENSIONS))}"
            )

        try:
            # Read bytes first to handle Windows Unicode/Vietnamese characters properly
            file_bytes = np.fromfile(file_path, dtype=np.uint8)
            if file_bytes is None or len(file_bytes) == 0:
                raise ValueError("File is empty (0 bytes)")

            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if image is None or image.size == 0:
                raise ValueError("Failed to decode image. File might be corrupted.")

            return image
        except Exception as e:
            if isinstance(e, (FileNotFoundError, ValueError)):
                raise e
            raise ValueError(f"Error loading image '{file_path}': {str(e)}")

    @staticmethod
    def create_preview_proxy(image: np.ndarray, max_dimension: int = 1920) -> Tuple[np.ndarray, float]:
        """
        Create a downscaled proxy copy for smooth interactive slider dragging
        if the original image exceeds max_dimension.

        Args:
            image: Original full-resolution image.
            max_dimension: Maximum allowed width or height for preview proxy.

        Returns:
            Tuple of (preview_image, scale_factor). scale_factor = 1.0 if not resized.
        """
        if image is None or image.size == 0:
            raise ValueError("Input image is invalid")

        h, w = image.shape[:2]
        max_side = max(h, w)

        if max_side <= max_dimension:
            return image.copy(), 1.0

        scale = max_dimension / float(max_side)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))

        # cv2.INTER_AREA is optimal for downsampling
        preview = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return preview, scale

    @staticmethod
    def numpy_to_qimage(image: np.ndarray) -> QImage:
        """
        Convert a NumPy image (BGR, Grayscale, or BGRA) into a QImage.
        Guarantees correct color representation (no inverted red/blue channels).
        """
        if image is None or image.size == 0:
            return QImage()

        # Handle grayscale (2D array)
        if len(image.shape) == 2:
            h, w = image.shape
            bytes_per_line = w
            # Format_Grayscale8 is standard for 8-bit gray
            # Make sure array is contiguous in C order
            contiguous = np.ascontiguousarray(image)
            qimage = QImage(
                contiguous.data,
                w,
                h,
                bytes_per_line,
                QImage.Format.Format_Grayscale8
            )
            return qimage.copy()  # Deep copy to ensure safety when NumPy memory is recycled

        # Handle 3-channel BGR
        elif len(image.shape) == 3 and image.shape[2] == 3:
            h, w, ch = image.shape
            # Convert BGR to RGB for Qt Format_RGB888
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            contiguous = np.ascontiguousarray(rgb_image)
            bytes_per_line = ch * w
            qimage = QImage(
                contiguous.data,
                w,
                h,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )
            return qimage.copy()

        # Handle 4-channel BGRA
        elif len(image.shape) == 3 and image.shape[2] == 4:
            h, w, ch = image.shape
            rgba_image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
            contiguous = np.ascontiguousarray(rgba_image)
            bytes_per_line = ch * w
            qimage = QImage(
                contiguous.data,
                w,
                h,
                bytes_per_line,
                QImage.Format.Format_RGBA8888
            )
            return qimage.copy()

        else:
            raise ValueError(f"Cannot convert image with shape {image.shape} to QImage")

    @classmethod
    def numpy_to_qpixmap(cls, image: np.ndarray) -> QPixmap:
        """
        Convert NumPy array directly to QPixmap.
        """
        qimage = cls.numpy_to_qimage(image)
        return QPixmap.fromImage(qimage)
