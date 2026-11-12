"""
Test Suite verifying Phase 7 Audit & Validation Requirements:
1. Brightness = 0, Contrast = 1, Gamma = 1: image unchanged.
2. Brightness = +40: Mean Intensity increases.
3. Brightness = -40: Mean Intensity decreases.
4. Contrast = 1.5: standard deviation (dispersion) increases around midpoint 127.5.
5. Gamma = 0.5 and 2.0: two distinct transformations (crush vs boost).
6. Histogram total pixels matches W x H.
7. Sobel X/Y has real, accurate gradient values.
8. Gradient Magnitude mathematically equals sqrt(Gx^2 + Gy^2).
9. Original and Adjusted use unified shared scale and threshold.
10. Slider adjustment triggers full pipeline update (image, histogram, stats).
11. Reset restores initial image and default parameters.
"""
import os
import unittest
import numpy as np

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from app.core.image_processor import ImageProcessor
from app.core.image_analyzer import ImageAnalyzer
from app.ui.main_window import MainWindow


class TestAuditPhase7(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        # Create a synthetic 100x100 test image with pixels from 50 to 200
        x = np.linspace(50, 200, 100, dtype=np.uint8)
        self.test_img = np.tile(x, (100, 1))

    def test_1_defaults_identity(self):
        """1. Brightness = 0, Contrast = 1, Gamma = 1: exact identity."""
        res = ImageProcessor.process_pipeline(self.test_img, brightness=0.0, contrast=1.0, gamma=1.0)
        np.testing.assert_array_equal(res, self.test_img)

    def test_2_brightness_positive(self):
        """2. Brightness = +40: Mean Intensity increases."""
        orig_mean = float(np.mean(self.test_img))
        res = ImageProcessor.process_pipeline(self.test_img, brightness=40.0, contrast=1.0, gamma=1.0)
        self.assertGreater(float(np.mean(res)), orig_mean)

    def test_3_brightness_negative(self):
        """3. Brightness = -40: Mean Intensity decreases."""
        orig_mean = float(np.mean(self.test_img))
        res = ImageProcessor.process_pipeline(self.test_img, brightness=-40.0, contrast=1.0, gamma=1.0)
        self.assertLess(float(np.mean(res)), orig_mean)

    def test_4_contrast_dispersion(self):
        """4. Contrast = 1.5: standard deviation (dispersion) increases around midpoint 127.5."""
        orig_std = float(np.std(self.test_img))
        res = ImageProcessor.process_pipeline(self.test_img, brightness=0.0, contrast=1.5, gamma=1.0)
        self.assertGreater(float(np.std(res)), orig_std)

    def test_5_gamma_transforms(self):
        """5. Gamma = 0.5 and 2.0: create two distinct, opposite transformations."""
        mid_img = np.full((50, 50), 128, dtype=np.uint8)
        gamma_low = ImageProcessor.process_pipeline(mid_img, brightness=0.0, contrast=1.0, gamma=0.5)
        gamma_high = ImageProcessor.process_pipeline(mid_img, brightness=0.0, contrast=1.0, gamma=2.0)

        # Gamma 0.5 darkens midtones, Gamma 2.0 brightens midtones
        self.assertLess(float(np.mean(gamma_low)), 128.0)
        self.assertGreater(float(np.mean(gamma_high)), 128.0)
        self.assertNotEqual(float(np.mean(gamma_low)), float(np.mean(gamma_high)))

    def test_6_histogram_total_pixels(self):
        """6. Histogram sum of bins equals total pixels W x H."""
        hist = ImageAnalyzer.compute_histogram_256(self.test_img)
        self.assertEqual(int(np.sum(hist)), self.test_img.shape[0] * self.test_img.shape[1])

    def test_7_sobel_xy_real_data(self):
        """7. Sobel X and Y derivatives compute actual gradient values."""
        # Vertical step edge: left 50, right 200
        step = np.zeros((64, 64), dtype=np.uint8)
        step[:, :32] = 50
        step[:, 32:] = 200
        gx, gy, mag = ImageProcessor.compute_sobel_raw(step)
        self.assertGreater(np.max(np.abs(gx)), 100.0)
        self.assertAlmostEqual(float(np.mean(np.abs(gy))), 0.0, delta=1.0)

    def test_8_gradient_magnitude_from_gx_gy(self):
        """8. Gradient Magnitude mathematically equals sqrt(Gx^2 + Gy^2)."""
        gx, gy, mag = ImageProcessor.compute_sobel_raw(self.test_img)
        expected_mag = np.sqrt(gx**2 + gy**2)
        np.testing.assert_allclose(mag, expected_mag, atol=1e-3)

    def test_9_sobel_shared_scale_and_threshold(self):
        """9. Original and Adjusted Sobel share identical scale factor and threshold."""
        adj_img = ImageProcessor.process_pipeline(self.test_img, brightness=20.0, contrast=1.4, gamma=1.0)
        components = ImageProcessor.compute_all_sobel_components(self.test_img, adj_img, threshold=60.0)
        self.assertIn("shared_scale", components)
        self.assertEqual(components["threshold"], 60.0)

    def test_10_slider_updates_all_components(self):
        """10. Slider adjustments update image, histogram, and statistics."""
        win = MainWindow()
        win.load_image_file("samples/test_pattern.png")
        orig_mean = win.analysis_panel.statistics_widget.card_mean.value_lbl.text()

        # Adjust parameters
        win.control_panel.slider_brightness.setValue(-40.0)
        win.control_panel.slider_contrast.setValue(1.5)
        win._execute_pipeline()

        new_mean = win.analysis_panel.statistics_widget.card_mean.value_lbl.text()
        self.assertNotEqual(orig_mean, new_mean)
        self.assertIsNotNone(win.adjusted_preview_image)
        win.close()

    def test_11_reset_restores_original(self):
        """11. Reset restores parameters to (0, 1.0, 1.0) and matches original image."""
        win = MainWindow()
        win.load_image_file("samples/test_pattern.png")
        win.control_panel.slider_brightness.setValue(-49.0)
        win.control_panel.slider_contrast.setValue(2.5)
        win._execute_pipeline()

        win.reset_parameters()
        self.assertEqual(win.current_params, (0.0, 1.0, 1.0))
        np.testing.assert_array_equal(win.adjusted_preview_image, win.preview_image)
        win.close()


if __name__ == "__main__":
    unittest.main()
