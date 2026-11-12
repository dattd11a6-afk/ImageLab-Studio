"""
Unit tests for ImageLoader and ImageExporter.
Verifies file reading, saving, roundtrip integrity, and Unicode path handling.
"""
import os
import tempfile
import unittest
import numpy as np
from app.utils.image_loader import ImageLoader
from app.utils.image_exporter import ImageExporter


class TestImageIO(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_img = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_load_png_roundtrip(self):
        """
        Verify that saving a PNG image and loading it back yields the exact same pixel matrix (lossless).
        """
        out_path = os.path.join(self.temp_dir, "test_output.png")
        success = ImageExporter.save_image(self.sample_img, out_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(out_path))

        loaded = ImageLoader.load_image(out_path)
        self.assertEqual(loaded.shape, self.sample_img.shape)
        np.testing.assert_array_equal(loaded, self.sample_img)

    def test_unicode_path_handling(self):
        """
        Verify that saving and loading files with Vietnamese characters works without errors.
        """
        unicode_path = os.path.join(self.temp_dir, "ảnh_thử_nghiệm_độ_sáng.png")
        success = ImageExporter.save_image(self.sample_img, unicode_path)
        self.assertTrue(success)

        loaded = ImageLoader.load_image(unicode_path)
        np.testing.assert_array_equal(loaded, self.sample_img)

    def test_preview_proxy_downsampling(self):
        """
        Verify downsampling logic for large images.
        """
        large_img = np.zeros((3000, 4000, 3), dtype=np.uint8)
        preview, scale = ImageLoader.create_preview_proxy(large_img, max_dimension=1920)
        self.assertEqual(max(preview.shape[:2]), 1920)
        self.assertLess(scale, 1.0)


if __name__ == "__main__":
    unittest.main()
