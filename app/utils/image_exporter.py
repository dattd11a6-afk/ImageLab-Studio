"""
ImageLab Studio - Image Exporter
Saves full-resolution processed images to disk with format-specific compression and Unicode path support.
"""
import os
from typing import Optional
import numpy as np
import cv2


class ImageExporter:
    """
    Handles saving and exporting images in various formats (PNG, JPEG, BMP, TIFF)
    at full resolution without compression artifacts unless requested.
    """

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

    @classmethod
    def save_image(
        cls,
        image: np.ndarray,
        file_path: str,
        jpeg_quality: int = 95,
        png_compression: int = 3
    ) -> bool:
        """
        Save image to disk using Unicode-safe encoding.

        Args:
            image: Processed uint8 image array (BGR or Grayscale).
            file_path: Destination path.
            jpeg_quality: Quality factor [1-100] for JPEG.
            png_compression: Compression level [0-9] for PNG.

        Returns:
            True if export succeeded.

        Raises:
            ValueError: If input image is invalid or extension unsupported.
            IOError: If writing to destination failed.
        """
        if image is None or image.size == 0:
            raise ValueError("Cannot save empty or invalid image")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported export format '{ext}'. Supported: {', '.join(sorted(cls.SUPPORTED_EXTENSIONS))}"
            )

        # Ensure parent directory exists
        parent_dir = os.path.dirname(os.path.abspath(file_path))
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        # Set up OpenCV encoder parameters
        params = []
        if ext in (".jpg", ".jpeg"):
            params = [int(cv2.IMWRITE_JPEG_QUALITY), int(np.clip(jpeg_quality, 1, 100))]
        elif ext == ".png":
            params = [int(cv2.IMWRITE_PNG_COMPRESSION), int(np.clip(png_compression, 0, 9))]
        elif ext in (".tif", ".tiff"):
            params = [int(cv2.IMWRITE_TIFF_COMPRESSION), 1]  # None / Deflate

        try:
            # Encode image to memory buffer
            success, buffer = cv2.imencode(ext, image, params)
            if not success or buffer is None:
                raise IOError(f"OpenCV failed to encode image to {ext}")

            # Write buffer directly to file (handles Windows Unicode paths)
            buffer.tofile(file_path)
            return True
        except Exception as e:
            if isinstance(e, (ValueError, IOError)):
                raise e
            raise IOError(f"Failed to write image to '{file_path}': {str(e)}")
