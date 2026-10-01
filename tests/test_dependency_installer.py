"""Optional dependency prompts without invoking pip or the network."""

import os
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from qgis.core import QgsApplication
    from qgis.PyQt.QtWidgets import QMessageBox, QWidget

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
    from wiscsims_tool_class.tools.dependencyInstaller import (
        DependencyInstaller,
        excel_dependency,
        python_process_environment,
        qgis_python_executable,
    )
    from wiscsims_tool_class.tools.imports.importTool import ImportTool
except ImportError:
    QgsApplication = None


@unittest.skipIf(QgsApplication is None, "QGIS Python bindings are unavailable")
class DependencyInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QgsApplication.instance() or QgsApplication([], True)

    def setUp(self):
        self.installer = DependencyInstaller()

    def test_excel_extensions_use_fixed_packages(self):
        self.assertEqual(excel_dependency("session.XLSX"), ("openpyxl", "openpyxl"))
        self.assertEqual(excel_dependency("session.xls"), ("xlrd", "xlrd"))
        self.assertIsNone(excel_dependency("session.csv"))

    def test_qgis_gui_executable_resolves_to_bundled_python(self):
        with tempfile.TemporaryDirectory() as directory:
            app = pathlib.Path(directory) / "QGIS"
            python = pathlib.Path(directory) / (
                f"python{sys.version_info.major}.{sys.version_info.minor}"
            )
            app.touch()
            python.touch()
            with patch.object(sys, "executable", str(app)):
                self.assertEqual(qgis_python_executable(), str(python))

    def test_missing_qgis_python_returns_an_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            sys, "executable", str(pathlib.Path(directory) / "QGIS")
        ), patch("wiscsims_tool_class.tools.dependencyInstaller.sys.prefix", directory), patch.dict(
            os.environ, {"PYTHONHOME": ""}
        ):
            with self.assertRaisesRegex(RuntimeError, "QGIS application itself cannot run pip"):
                qgis_python_executable()

    def test_normal_process_completion_is_not_treated_as_cancel(self):
        completed, output = self.installer._run_process(
            qgis_python_executable(),
            ["-c", "print('completed')"],
            "Testing process completion…",
        )
        self.assertTrue(completed)
        self.assertIn("completed", output)

    @unittest.skipUnless(
        sys.platform == "darwin"
        and pathlib.Path("/Applications/QGIS.app/Contents/MacOS/python3.12").is_file(),
        "macOS QGIS bundle is unavailable",
    )
    def test_macos_bundled_python_receives_pythonhome(self):
        python = "/Applications/QGIS.app/Contents/MacOS/python3.12"
        environment = python_process_environment(python)
        self.assertEqual(
            environment.value("PYTHONHOME"),
            "/Applications/QGIS.app/Contents/Frameworks",
        )

    @unittest.skipUnless(
        sys.platform == "darwin"
        and pathlib.Path("/Applications/QGIS.app/Contents/MacOS/python3.12").is_file(),
        "macOS QGIS bundle is unavailable",
    )
    def test_bundled_python_starts_when_parent_has_no_pythonhome(self):
        with patch.dict(os.environ, {"PYTHONHOME": ""}):
            completed, output = self.installer._run_process(
                qgis_python_executable(),
                ["-c", "import encodings; print('stdlib available')"],
                "Testing bundled Python…",
            )
        self.assertTrue(completed, output)
        self.assertIn("stdlib available", output)

    def test_available_module_does_not_prompt_or_install(self):
        with patch.object(self.installer, "module_available", return_value=True), patch.object(
            QMessageBox, "question"
        ) as question, patch.object(self.installer, "install_package") as install:
            self.assertTrue(self.installer.ensure_excel_reader("session.xlsx"))
        question.assert_not_called()
        install.assert_not_called()

    def test_declining_install_stops_without_running_pip(self):
        with patch.object(self.installer, "module_available", return_value=False), patch.object(
            QMessageBox, "question", return_value=QMessageBox.No
        ), patch.object(self.installer, "install_package") as install:
            self.assertFalse(self.installer.ensure_excel_reader("session.xls"))
        install.assert_not_called()

    def test_accepted_install_is_verified_before_success(self):
        with patch.object(
            self.installer, "module_available", side_effect=(False, True)
        ), patch.object(
            QMessageBox, "question", return_value=QMessageBox.Yes
        ), patch.object(
            QMessageBox, "information"
        ) as information, patch.object(
            self.installer, "install_package", return_value=(True, "installed")
        ) as install:
            self.assertTrue(self.installer.ensure_excel_reader("session.xlsx"))
        install.assert_called_once_with("openpyxl")
        information.assert_called_once()

    def test_failed_install_shows_pip_output(self):
        with patch.object(self.installer, "module_available", return_value=False), patch.object(
            QMessageBox, "question", return_value=QMessageBox.Yes
        ), patch.object(
            self.installer, "install_package", return_value=(False, "network unavailable")
        ), patch.object(QMessageBox, "warning") as warning:
            self.assertFalse(self.installer.ensure_excel_reader("session.xlsx"))
        self.assertIn("network unavailable", warning.call_args.args[2])

    def test_workbook_selection_stops_when_install_is_declined(self):
        controller = SimpleNamespace(
            prev_workbook_path="",
            dependency_installer=Mock(),
        )
        controller.dependency_installer.ensure_excel_reader.return_value = False
        with patch(
            "wiscsims_tool_class.tools.imports.importTool.QFileDialog.getOpenFileName",
            return_value=("session.xlsx", "Excel"),
        ), patch("wiscsims_tool_class.tools.imports.importTool.SumTableTool") as workbook:
            ImportTool.select_workbook(controller)
        controller.dependency_installer.ensure_excel_reader.assert_called_once_with("session.xlsx")
        workbook.assert_not_called()

    def test_workbook_selection_retries_after_successful_install(self):
        text_box = SimpleNamespace(setText=Mock(), setToolTip=Mock())
        dock = QWidget()
        dock.Tbx_Workbook = text_box
        controller = SimpleNamespace(
            prev_workbook_path="",
            dependency_installer=Mock(),
            dock=dock,
            xl=None,
            workbook_path="",
            read_workbook=ImportTool.read_workbook,
        )
        controller.dependency_installer.ensure_excel_reader.return_value = True
        loaded = SimpleNamespace(ws=object(), load_error=None, get_headers=Mock(), get_values=Mock())
        with patch(
            "wiscsims_tool_class.tools.imports.importTool.QFileDialog.getOpenFileName",
            return_value=("/tmp/session.xlsx", "Excel"),
        ), patch(
            "wiscsims_tool_class.tools.imports.importTool.SumTableTool",
            return_value=loaded,
        ) as workbook:
            ImportTool.select_workbook(controller)
        workbook.assert_called_once_with("/tmp/session.xlsx")
        self.assertIs(controller.xl, loaded)
        self.assertEqual(controller.prev_workbook_path, "/tmp/session.xlsx")
        text_box.setText.assert_called_once_with("session.xlsx")
        dock.deleteLater()


if __name__ == "__main__":
    unittest.main()
