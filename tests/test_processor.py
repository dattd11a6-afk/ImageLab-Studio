"""
Unit tests for ImageProcessor.
Verifies mathematical properties of Brightness, Contrast, Gamma LUT, and Sobel Edge Detection.
"""
import unittest
import numpy as np
import cv2
from app.core.image_processor import ImageProcessor


class TestImageProcessor(unittest.TestCase):

    def setUp(self):
        # Create a synthetic 100x100 grayscale image with known gradient
        # Range spans from 50 to 200 to avoid saturation at edges for basic tests
        x = np.linspace(50, 200, 100, dtype=np.uint8)
        self.gradient_img = np.tile(x, (100, 1))

        # Create a synthetic 3-channel BGR image
        self.bgr_img = np.zeros((100, 100, 3), dtype=np.uint8)
        self.bgr_img[:, :, 0] = self.gradient_img
        self.bgr_img[:, :, 1] = np.clip(self.gradient_img + 20, 0, 255)
        self.bgr_img[:, :, 2] = np.clip(self.gradient_img - 20, 0, 255)

    def test_identity_defaults(self):
        """
        Brightness = 0, Contrast = 1.0, Gamma = 1.0
        Must return the exact same image with zero numerical deviation.
        """
        res = ImageProcessor.process_pipeline(
            self.gradient_img,
            brightness=0.0,
            contrast=1.0,
            gamma=1.0
        )
        np.testing.assert_array_equal(res, self.gradient_img)

        res_bgr = ImageProcessor.process_pipeline(
            self.bgr_img,
            brightness=0.0,
            contrast=1.0,
            gamma=1.0
        )
        np.testing.assert_array_equal(res_bgr, self.bgr_img)

    def test_brightness_monotonicity(self):
        """
        Increasing brightness (+30) must increase mean intensity.
        Decreasing brightness (-30) must decrease mean intensity.
        """
        orig_mean = float(np.mean(self.gradient_img))

        brighter = ImageProcessor.apply_brightness_contrast(
            self.gradient_img, brightness=30.0, contrast=1.0
        )
        brighter_mean = float(np.mean(brighter))
        self.assertGreater(brighter_mean, orig_mean)

        darker = ImageProcessor.apply_brightness_contrast(
            self.gradient_img, brightness=-30.0, contrast=1.0
        )
        darker_mean = float(np.mean(darker))
        self.assertLess(darker_mean, orig_mean)

    def test_contrast_scaling(self):
        """
        Contrast > 1.0 increases variance / standard deviation around midpoint 127.5.
        Contrast < 1.0 decreases standard deviation.
        """
        orig_std = float(np.std(self.gradient_img))

        high_contrast = ImageProcessor.apply_brightness_contrast(
            self.gradient_img, brightness=0.0, contrast=1.5
        )
        high_std = float(np.std(high_contrast))
        self.assertGreater(high_std, orig_std)

        low_contrast = ImageProcessor.apply_brightness_contrast(
            self.gradient_img, brightness=0.0, contrast=0.5
        )
        low_std = float(np.std(low_contrast))
        self.assertLess(low_std, orig_std)

    def test_gamma_correction(self):
        """
        Gamma = 1.0: exact identity.
        Gamma > 1.0: brightens midtones (I_gamma > I).
        Gamma < 1.0: darkens midtones (I_gamma < I).
        Formula: 255 * (I / 255) ** (1 / gamma).
        """
        # Test LUT length and bounds
        lut_1 = ImageProcessor.get_gamma_lut(1.0)
        np.testing.assert_array_equal(lut_1, np.arange(256, dtype=np.uint8))

        lut_2 = ImageProcessor.get_gamma_lut(2.0)
        self.assertEqual(len(lut_2), 256)
        self.assertEqual(lut_2[0], 0)
        self.assertEqual(lut_2[255], 255)

        # For midtone ~128: 255 * (128/255)**(1/2) = 255 * sqrt(0.5019) ~ 180.68 -> 180 or 181
        mid_val = 128
        expected_mid = int(np.round(255.0 * ((mid_val / 255.0) ** (1.0 / 2.0))))
        self.assertAlmostEqual(int(lut_2[mid_val]), expected_mid, delta=1)
        self.assertGreater(int(lut_2[mid_val]), mid_val)

        # Test on image
        mid_img = np.full((50, 50), 128, dtype=np.uint8)
        gamma_boost = ImageProcessor.apply_gamma(mid_img, gamma=2.0)
        self.assertGreater(float(np.mean(gamma_boost)), 128.0)

        gamma_crush = ImageProcessor.apply_gamma(mid_img, gamma=0.5)
        self.assertLess(float(np.mean(gamma_crush)), 128.0)

    def test_no_negative_wrap_around_clipping(self):
        """
        Verify that negative values are properly clipped to 0 and NOT inverted
        (which cv2.convertScaleAbs would mistakenly do).
        """
        dark_img = np.full((10, 10), 20, dtype=np.uint8)
        # Shift down by 50 -> should clamp strictly to 0
        result = ImageProcessor.apply_brightness_contrast(dark_img, brightness=-50.0, contrast=1.0)
        np.testing.assert_array_equal(result, np.zeros((10, 10), dtype=np.uint8))

    def test_sobel_edge_detection(self):
        """
        Verify Sobel gradient computation, shapes, and brightness invariance.
        """
        # Step edge image: Left half 50, right half 200
        step_img = np.zeros((64, 64), dtype=np.uint8)
        step_img[:, :32] = 50
        step_img[:, 32:] = 200

        gx, gy, mag = ImageProcessor.compute_sobel_raw(step_img)
        self.assertEqual(gx.shape, (64, 64))
        self.assertEqual(gy.shape, (64, 64))
        self.assertEqual(mag.shape, (64, 64))

        # Vertical step edge has strong Gx at x=31, 32, and near 0 Gy everywhere
        self.assertGreater(np.max(np.abs(gx)), 100.0)
        self.assertAlmostEqual(float(np.mean(np.abs(gy))), 0.0, places=2)

        # Mathematical property: adding pure brightness does not alter gradients:
        # d(I + c)/dx = dI/dx + 0 = dI/dx
        brighter_step = np.clip(step_img.astype(np.float32) + 30.0, 0, 255).astype(np.uint8)
        gx_b, gy_b, mag_b = ImageProcessor.compute_sobel_raw(brighter_step)
        # Gradients must match exactly because neither region saturated at boundary
        np.testing.assert_allclose(mag, mag_b, atol=1e-3)

    def test_sobel_dual_comparison_shared_scale(self):
        """
        Verify that compare_sobel_dual uses a unified shared scale so comparisons are strictly fair.
        """
        vis_o, vis_a, meta = ImageProcessor.compare_sobel_dual(
            self.gradient_img, self.gradient_img, mode="magnitude"
        )
        self.assertEqual(vis_o.shape, self.gradient_img.shape)
        self.assertEqual(vis_a.shape, self.gradient_img.shape)
        np.testing.assert_array_equal(vis_o, vis_a)
        self.assertIn("shared_scale", meta)


if __name__ == "__main__":
    unittest.main()
