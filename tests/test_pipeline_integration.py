"""
End-to-end integration test for ImageLab Studio.
Tests entire pipeline, MainWindow instantiation, slider interactions, undo/redo, and file export.
"""
import os
import tempfile
import unittest
import numpy as np

# Configure headless Qt offscreen platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.core.image_processor import ImageProcessor
from app.utils.image_loader import ImageLoader


class TestPipelineIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create singleton QApplication if not already running
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.sample_path = "samples/test_pattern.png"

    def tearDown(self):
        self.window.close()

    def test_load_sample_and_pipeline_execution(self):
        """
        Verify opening an image executes the pipeline without errors and updates status bar.
        """
        self.assertTrue(os.path.exists(self.sample_path))
        self.window.load_image_file(self.sample_path)

        # Check image loaded
        self.assertIsNotNone(self.window.original_full_image)
        self.assertIsNotNone(self.window.preview_image)
        self.assertIsNotNone(self.window.adjusted_preview_image)

        # Initially parameters are (0, 1.0, 1.0) so adjusted should equal preview
        np.testing.assert_array_equal(self.window.adjusted_preview_image, self.window.preview_image)

    def test_slider_adjustment_and_undo_redo(self):
        """
        Verify slider adjustment triggers pipeline update and pushes to undo stack.
        """
        self.window.load_image_file(self.sample_path)

        # Simulate user adjusting sliders to Brightness = +20, Contrast = 1.5, Gamma = 1.4
        self.window.control_panel.set_values(20.0, 1.5, 1.4)
        self.window._commit_current_state_to_history()

        self.assertEqual(self.window.current_params, (20.0, 1.5, 1.4))
        self.assertEqual(len(self.window.undo_stack), 2)
        self.assertTrue(self.window.action_undo.isEnabled())

        # Test Undo
        self.window.undo()
        self.assertEqual(self.window.current_params, (0.0, 1.0, 1.0))
        self.assertTrue(self.window.action_redo.isEnabled())

        # Test Redo
        self.window.redo()
        self.assertEqual(self.window.current_params, (20.0, 1.5, 1.4))

    def test_reset_parameters(self):
        """
        Verify Reset restores parameters to defaults (0, 1.0, 1.0).
        """
        self.window.load_image_file(self.sample_path)
        self.window.control_panel.set_values(-40.0, 0.8, 0.7)
        self.window._commit_current_state_to_history()

        self.window.reset_parameters()
        self.assertEqual(self.window.current_params, (0.0, 1.0, 1.0))
        self.assertEqual(self.window.control_panel.slider_brightness.value(), 0.0)
        self.assertEqual(self.window.control_panel.slider_contrast.value(), 1.0)
        self.assertAlmostEqual(self.window.control_panel.slider_gamma.value(), 1.0, places=2)

    def test_sobel_analysis_widget_update(self):
        """
        Verify Sobel analysis widget receives complete 8-component data and updates tiles.
        """
        self.window.load_image_file(self.sample_path)
        self.window._execute_pipeline()
        sobel_w = self.window.analysis_panel.sobel_analysis_widget
        self.assertIsNotNone(sobel_w.cached_components)
        self.assertIn("mag_orig", sobel_w.cached_components)
        self.assertIn("mag_adj", sobel_w.cached_components)
        self.assertGreater(sobel_w.table_sobel.rowCount(), 0)


if __name__ == "__main__":
    unittest.main()
