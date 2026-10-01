"""A mode selector sized to its current page, using the native font and style."""

from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtWidgets import QStyle, QStyleOptionTabWidgetFrame, QTabWidget


class ActivePageTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.currentChanged.connect(self.updateGeometry)

    def _frame_size(self):
        option = QStyleOptionTabWidgetFrame()
        self.initStyleOption(option)
        return self.style().sizeFromContents(QStyle.CT_TabWidget, option, QSize(0, 0), self)

    def _frame_height(self):
        return self.tabBar().sizeHint().height() + self._frame_size().height()

    def sizeHint(self):
        page = self.currentWidget()
        if page is None:
            return super().sizeHint()
        return QSize(super().sizeHint().width(), page.sizeHint().height() + self._frame_height())

    def minimumSizeHint(self):
        page = self.currentWidget()
        if page is None:
            return super().minimumSizeHint()
        return QSize(super().minimumSizeHint().width(), page.minimumSizeHint().height() + self._frame_height())

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        page = self.currentWidget()
        if page is None:
            return super().heightForWidth(width)
        border = self._frame_size().width()
        height = page.heightForWidth(max(0, width - border))
        if height < 0:
            height = page.sizeHint().height()
        return height + self._frame_height()
