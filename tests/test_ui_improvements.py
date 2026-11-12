"""
Test suite verifying the latest UI improvements:
- ControlPanel direct layout without QScrollArea
- StatisticsWidget 100% Vietnamese labels and spacious scrolling
- Image canvas stationary stability during parameter changes
"""
import os
import unittest
import numpy as np

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication, QScrollArea
from app.ui.main_window import MainWindow
from app.ui.control_panel import ControlPanel
from app.widgets.statistics_widget import StatisticsWidget
from app.core.image_analyzer import ImageAnalyzer


class TestUIImprovements(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.window.load_image_file("samples/test_pattern.png")

    def tearDown(self):
        self.window.close()

    def test_control_panel_has_no_scroll_area(self):
        """
        Verify that ControlPanel does NOT use a QScrollArea,
        allowing all sliders to be directly and immediately accessible.
        """
        scroll_areas = self.window.control_panel.findChildren(QScrollArea)
        self.assertEqual(len(scroll_areas), 0, "ControlPanel must not contain any QScrollArea")

        # Verify sliders exist directly
        self.assertIsNotNone(self.window.control_panel.slider_brightness)
        self.assertIsNotNone(self.window.control_panel.slider_contrast)
        self.assertIsNotNone(self.window.control_panel.slider_gamma)

    def test_statistics_table_vietnamese_labels(self):
        """
        Verify that the statistics dashboard displays 100% Vietnamese labels and headers.
        """
        table = self.window.analysis_panel.statistics_widget.table
        self.assertGreaterEqual(table.rowCount(), 10)

        # Check headers
        headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
        self.assertIn("Ảnh gốc", headers[1])
        self.assertIn("Ảnh đã chỉnh", headers[2])

        # Check metric row labels in Vietnamese
        row_0 = table.item(0, 0).text()
        self.assertIn("Cường độ sáng", row_0)

        row_1 = table.item(1, 0).text()
        self.assertIn("Độ tương phản", row_1)

        row_clipping = table.item(7, 0).text()
        self.assertIn("bão hòa", row_clipping.lower())

    def test_image_stays_stationary_during_slider_updates(self):
        """
        Verify that adjusting sliders does NOT alter canvas zoom_factor or pan_offset (stays stationary).
        """
        initial_zoom = self.window.image_viewer.canvas.zoom_factor
        initial_pan = self.window.image_viewer.canvas.pan_offset

        # Adjust brightness, contrast, gamma
        self.window.control_panel.set_values(35.0, 1.60, 1.45)
        self.window._execute_pipeline()

        # Canvas zoom and pan MUST remain strictly stationary!
        self.assertEqual(self.window.image_viewer.canvas.zoom_factor, initial_zoom)
        self.assertEqual(self.window.image_viewer.canvas.pan_offset, initial_pan)

    def test_independent_deep_analysis_windows(self):
        """
        Verify that 3 independent floating analysis windows exist with icons and can be opened.
        """
        # 1. Histogram Window
        self.assertIsNotNone(self.window.win_histogram)
        self.assertEqual(self.window.win_histogram.icon_name, "histogram")
        self.window.open_histogram_window()
        self.assertTrue(self.window.win_histogram.isVisible())
        self.window.win_histogram.hide()

        # 2. Statistics Window
        self.assertIsNotNone(self.window.win_statistics)
        self.assertEqual(self.window.win_statistics.icon_name, "statistics")
        self.window.open_statistics_window()
        self.assertTrue(self.window.win_statistics.isVisible())
        self.window.win_statistics.hide()

        # 3. Sobel Edge Window
        self.assertIsNotNone(self.window.win_sobel)
        self.assertEqual(self.window.win_sobel.icon_name, "sobel-edge")
        self.window.open_sobel_window()
        self.assertTrue(self.window.win_sobel.isVisible())
        self.window.win_sobel.hide()

    def test_ui_tooltips_and_unclipped_labels(self):
        """
        Verify that top view mode buttons have rich tooltips and concise, unclipped labels.
        """
        iv = self.window.image_viewer
        # Labels are concise (no long bracketed text causing cut-off)
        self.assertIn("Song song", iv.btn_side.text())
        self.assertIn("Rèm trượt", iv.btn_split.text())
        self.assertIn("Xem ảnh sửa", iv.btn_single.text())
        self.assertIn("So sánh biên", iv.btn_sobel.text())

        # Tooltips exist and are comprehensive
        self.assertGreater(len(iv.btn_side.toolTip()), 10)
        self.assertGreater(len(iv.btn_split.toolTip()), 10)
        self.assertGreater(len(iv.btn_single.toolTip()), 10)
        self.assertGreater(len(iv.btn_sobel.toolTip()), 10)
        self.assertGreater(len(iv.btn_fit.toolTip()), 10)
        self.assertGreater(len(iv.btn_actual.toolTip()), 10)


if __name__ == "__main__":
    unittest.main()
