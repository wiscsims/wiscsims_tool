"""Install optional Python packages after explicit user confirmation."""

import importlib
import os
import site
import sys
from pathlib import Path

from qgis.PyQt.QtCore import QEventLoop, QProcess, QProcessEnvironment, Qt
from qgis.PyQt.QtWidgets import QMessageBox, QProgressDialog


EXCEL_DEPENDENCIES = {
    ".xlsx": ("openpyxl", "openpyxl"),
    ".xls": ("xlrd", "xlrd"),
}


def excel_dependency(path):
    """Return the import and package names required for an Excel path."""
    suffix = path.lower().rsplit(".", 1)[-1]
    return EXCEL_DEPENDENCIES.get(f".{suffix}")


def qgis_python_executable():
    """Find the Python interpreter used by QGIS instead of its GUI executable."""
    executable = Path(sys.executable)
    if executable.name.lower().startswith("python") and executable.is_file():
        return str(executable)

    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    candidates = [
        executable.with_name(f"python{version}"),
        executable.with_name("python3"),
        executable.with_name("python.exe"),
        Path(sys.prefix) / "bin" / f"python{version}",
        Path(sys.prefix) / "bin" / "python3",
        Path(sys.prefix) / "python.exe",
    ]
    python_home = os.environ.get("PYTHONHOME")
    if python_home:
        home = Path(python_home)
        candidates.extend(
            [
                home / "bin" / f"python{version}",
                home / "bin" / "python3",
                home / "python.exe",
                home.parent / "MacOS" / f"python{version}",
            ]
        )

    for candidate in candidates:
        if candidate.is_file() and candidate.name.lower().startswith("python"):
            return str(candidate)
    raise RuntimeError(
        "Could not find the Python interpreter used by QGIS. "
        "The QGIS application itself cannot run pip."
    )


def python_process_environment(python):
    """Build the environment needed to start QGIS's bundled Python."""
    environment = QProcessEnvironment.systemEnvironment()
    executable = Path(python)
    if sys.platform == "darwin" and executable.parent.name == "MacOS":
        frameworks = executable.parent.parent / "Frameworks"
        if frameworks.is_dir():
            environment.insert("PYTHONHOME", str(frameworks))
    return environment


class DependencyInstaller:
    """Prompt for and install a known optional dependency with pip."""

    def __init__(self, parent=None):
        self.parent = parent

    @staticmethod
    def module_available(module_name):
        try:
            importlib.import_module(module_name)
        except ImportError:
            return False
        return True

    def ensure_excel_reader(self, path):
        dependency = excel_dependency(path)
        if dependency is None:
            return True
        module_name, package_name = dependency
        return self.ensure(
            module_name,
            package_name,
            f"Reading {path.rsplit('.', 1)[-1].upper()} workbooks",
        )

    def ensure(self, module_name, package_name, purpose):
        if self.module_available(module_name):
            return True

        answer = QMessageBox.question(
            self.parent,
            "Install Required Python Module",
            f"{purpose} requires the Python module “{module_name}”, but it is not installed.\n\n"
            "Install it automatically now? An internet connection is required. "
            "The module will be installed for the current user.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if answer != QMessageBox.Yes:
            return False

        installed, details = self.install_package(package_name)
        importlib.invalidate_caches()
        if installed and self.module_available(module_name):
            QMessageBox.information(
                self.parent,
                "Python Module Installed",
                f"The Python module “{module_name}” was installed successfully.",
            )
            return True

        message = details.strip() or "pip completed, but the module still cannot be imported."
        message = message[-4000:]
        QMessageBox.warning(
            self.parent,
            "Python Module Installation Failed",
            f"Could not install “{package_name}”.\n\n{message}",
        )
        return False

    def install_package(self, package_name):
        """Run pip while keeping the QGIS event loop responsive."""
        try:
            python = qgis_python_executable()
        except RuntimeError as error:
            return False, str(error)

        installed, output = self._run_process(
            python,
            [
                "-m",
                "pip",
                "install",
                "--user",
                "--disable-pip-version-check",
                "--no-input",
                package_name,
            ],
            f"Installing {package_name}…",
        )
        if not installed:
            return False, output

        # Usually present already, but make a newly created user site visible
        # immediately without requiring QGIS to restart.
        user_site = site.getusersitepackages()
        if user_site not in sys.path:
            sys.path.append(user_site)
        return True, output

    def _run_process(self, program, arguments, label):
        """Run a cancellable process without treating normal dialog close as cancel."""
        process = QProcess(self.parent)
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.setProcessEnvironment(python_process_environment(program))
        progress = QProgressDialog(
            label,
            "Cancel",
            0,
            0,
            self.parent,
        )
        progress.setWindowTitle("Installing Python Module")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)

        event_loop = QEventLoop()
        canceled = {"value": False}

        def cancel():
            # QProgressDialog emits canceled() when close() is called after a
            # successful run. Only a click while the process is active is a
            # real cancellation request.
            if process.state() == QProcess.NotRunning:
                return
            canceled["value"] = True
            process.kill()

        progress.canceled.connect(cancel)
        process.finished.connect(lambda *_args: event_loop.quit())
        process.errorOccurred.connect(lambda *_args: event_loop.quit())
        process.start(program, arguments)
        if not process.waitForStarted(5000):
            progress.close()
            return False, process.errorString()
        progress.show()
        event_loop.exec_()
        progress.canceled.disconnect(cancel)
        progress.close()

        output = bytes(process.readAll()).decode("utf-8", errors="replace")
        if canceled["value"]:
            return False, "Installation was canceled."
        if process.exitStatus() != QProcess.NormalExit or process.exitCode() != 0:
            return False, output
        return True, output
