"""Import progress must remain visible and leave no worker/dialog after errors."""

import os
import pathlib
import sys
import threading
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from qgis.core import QgsApplication
    from qgis.PyQt.QtCore import QTimer, Qt
    from qgis.PyQt.QtTest import QTest

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from wiscsims_tool_class.tools.operationProgress import OperationProgress
except ImportError:
    QgsApplication = None


@unittest.skipIf(QgsApplication is None, "QGIS Python bindings are unavailable")
class OperationProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], True)

    def tearDown(self):
        self.app.processEvents()

    def test_background_work_keeps_gui_events_running_and_progress_on_gui_thread(self):
        gui_thread = threading.get_ident()
        gui_event = threading.Event()
        painted_threads = []
        with OperationProgress(None, "Read Excel Workbook") as progress:
            self.assertTrue(progress.dialog.isVisible())
            original = progress.dialog.setLabelText

            def record_paint(text):
                painted_threads.append(threading.get_ident())
                original(text)

            def read(report):
                self.assertNotEqual(threading.get_ident(), gui_thread)
                report("Reading worksheet rows…", 100, 250)
                if not gui_event.wait(2):
                    raise RuntimeError("GUI event loop did not run during reading")
                report("Reading worksheet rows…", 250, 250)
                return "loaded"

            QTimer.singleShot(0, gui_event.set)
            with patch.object(progress.dialog, "setLabelText", side_effect=record_paint):
                self.assertEqual(progress.run_in_background(read), "loaded")
            self.assertIn("250 / 250", progress.dialog.labelText())
            self.assertEqual(set(painted_threads), {gui_thread})
        self.assertFalse(progress.dialog.isVisible())

    def test_worker_error_closes_progress_and_propagates_to_caller(self):
        def fail(_report):
            raise ValueError("Unreadable worksheet")

        with self.assertRaisesRegex(ValueError, "Unreadable worksheet"):
            with OperationProgress(None, "Read Excel Workbook") as progress:
                progress.run_in_background(fail)
        self.assertFalse(progress.dialog.isVisible())

    def test_close_and_escape_do_not_enable_duplicate_import_during_operation(self):
        with OperationProgress(None, "Import Excel Data") as progress:
            progress.dialog.close()
            QTest.keyClick(progress.dialog, Qt.Key_Escape)
            self.assertTrue(progress.dialog.isVisible())
        self.assertFalse(progress.dialog.isVisible())
