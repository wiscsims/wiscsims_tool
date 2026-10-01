"""Show import stages while keeping workbook I/O off the GUI thread."""

from time import monotonic

from qgis.PyQt.QtCore import QEventLoop, QObject, QThread, Qt, pyqtSignal, pyqtSlot
from qgis.PyQt.QtWidgets import QApplication, QDialog, QLabel, QProgressBar, QVBoxLayout


class _ProgressDialog(QDialog):
    """Keep the modal dialog open until an operation with no cancel completes."""

    finishing = False

    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.label = QLabel("Preparing…", self)
        self.label.setWordWrap(True)
        self.bar = QProgressBar(self)
        self.bar.setRange(0, 0)
        layout.addWidget(self.label)
        layout.addWidget(self.bar)

    def setLabelText(self, text):
        self.label.setText(text)
        self.adjustSize()

    def labelText(self):
        return self.label.text()

    def closeEvent(self, event):
        if self.finishing:
            super().closeEvent(event)
        else:
            event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)

    def reject(self):
        if self.finishing:
            super().reject()


class _Worker(QThread):
    progress = pyqtSignal(str, int, int)

    def __init__(self, operation):
        super().__init__()
        self.operation = operation
        self.result = None
        self.error = None

    def run(self):
        try:
            self.result = self.operation(self.progress.emit)
        except Exception as error:
            self.error = error


class OperationProgress(QObject):
    """A modal status dialog owned and updated by the GUI thread.

    Workbook reading can run in a worker. QGIS layer access stays on the
    GUI thread, with paint events processed between preparation steps.
    """

    def __init__(self, parent, title):
        super().__init__(parent)
        self.dialog = _ProgressDialog(parent)
        self.dialog.setWindowTitle(title)
        self.dialog.setWindowModality(Qt.ApplicationModal)
        self._last_update = 0
        self._stage = None
        self._background = False

    def __enter__(self):
        self.dialog.show()
        QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
        return self

    def __exit__(self, *_args):
        self.dialog.finishing = True
        self.dialog.close()
        self.dialog.deleteLater()
        self.deleteLater()

    @pyqtSlot(str, int, int)
    def update(self, label, completed=0, total=0):
        # Throttle row updates, but always display a new stage and completion.
        now = monotonic()
        if label == self._stage and completed != total and now - self._last_update < 0.05:
            return
        self._stage = label
        self._last_update = now
        text = f"{label}\n{completed:,} / {total:,}" if total else label
        self.dialog.setLabelText(text)
        self.dialog.bar.setRange(0, total)
        self.dialog.bar.setValue(completed)
        if not self._background:
            QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)

    def run_in_background(self, operation):
        """Run Python-only I/O; propagate results/errors after the worker exits."""
        worker = _Worker(operation)
        event_loop = QEventLoop()
        worker.progress.connect(self.update)
        worker.finished.connect(event_loop.quit)
        self._background = True
        worker.start()
        event_loop.exec_()
        self._background = False
        worker.wait()
        result, error = worker.result, worker.error
        worker.deleteLater()
        if error is not None:
            raise error
        return result
