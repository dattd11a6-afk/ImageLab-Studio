"""
Unit tests for ImageAnalyzer.
Verifies histogram bin sums, statistical equations, clipping detection, and comparative diagnostics.
"""
import unittest
import numpy as np
from app.core.image_analyzer import ImageAnalyzer


class TestImageAnalyzer(unittest.TestCase):

    def setUp(self):
        # 128x128 synthetic test image
        np.random.seed(42)
        self.test_img = np.random.randint(10, 245, (128, 128), dtype=np.uint8)

    def test_histogram_sum_equals_pixel_count(self):
        """
        Theorem: The sum of all 256 histogram bins must equal the total number of pixels W x H.
        """
        hist = ImageAnalyzer.compute_histogram_256(self.test_img)
        self.assertEqual(len(hist), 256)
        self.assertEqual(int(np.sum(hist)), 128 * 128)

    def test_intensity_statistics_correctness(self):
        """
        Verify mean, min, max, std computed matches NumPy ground truth.
        """
        stats = ImageAnalyzer.compute_intensity_stats(self.test_img)
        self.assertAlmostEqual(stats["mean"], float(np.mean(self.test_img)), places=4)
        self.assertAlmostEqual(stats["std"], float(np.std(self.test_img)), places=4)
        self.assertEqual(stats["min"], float(np.min(self.test_img)))
        self.assertEqual(stats["max"], float(np.max(self.test_img)))
        self.assertEqual(stats["total_pixels"], 128 * 128)

    def test_clipping_detection(self):
        """
        Verify detection of under-exposure clipping (0) and over-exposure clipping (255).
        """
        clipped_img = self.test_img.copy()
        # Set 100 pixels to 0, and 200 pixels to 255
        clipped_img[:10, :10] = 0     # 100 pixels
        clipped_img[:10, 10:30] = 255 # 200 pixels

        stats = ImageAnalyzer.compute_intensity_stats(clipped_img)
        total_p = 128 * 128
        expected_under = (100 / total_p) * 100.0
        expected_over = (200 / total_p) * 100.0

        self.assertAlmostEqual(stats["clip_under_pct"], expected_under, places=2)
        self.assertAlmostEqual(stats["clip_over_pct"], expected_over, places=2)
        self.assertAlmostEqual(stats["clip_black_pct"], expected_under, places=2)
        self.assertAlmostEqual(stats["clip_white_pct"], expected_over, places=2)
        self.assertAlmostEqual(stats["clip_total_pct"], expected_under + expected_over, places=2)
        self.assertIn("median", stats)

    def test_comparative_deltas(self):
        """
        Verify delta calculations when adjusting brightness.
        """
        # Create brighter image
        brighter = np.clip(self.test_img.astype(np.float32) + 25.0, 0, 255).astype(np.uint8)
        comparison = ImageAnalyzer.compare_images(self.test_img, brighter)

        deltas = comparison["deltas"]
        self.assertGreater(deltas["delta_mean"], 20.0)
        self.assertIn("brightness_note", comparison["diagnosis"])
        self.assertIn("PHẢI", comparison["diagnosis"]["brightness_note"])

    def test_sobel_statistics(self):
        """
        Verify Sobel edge statistics computation on known step image.
        """
        step = np.zeros((100, 100), dtype=np.uint8)
        step[:, 50:] = 255

        from app.core.image_processor import ImageProcessor
        _, _, mag = ImageProcessor.compute_sobel_raw(step)
        sobel_stats = ImageAnalyzer.compute_sobel_stats(mag, threshold=50.0)

        self.assertGreater(sobel_stats["edge_density"], 0.0)
        self.assertLess(sobel_stats["edge_density"], 10.0)  # Edge is only 1-2 pixels wide along x=50
        self.assertGreater(sobel_stats["max_gradient"], 200.0)


if __name__ == "__main__":
    unittest.main()
