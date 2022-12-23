from PyQt6.QtWidgets import QStyle, QCommonStyle
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

from jparty.utils import DynamicLabel, add_shadow


class JPartyStyle(QCommonStyle):
    PM_dict = {
        QStyle.PixelMetric.PM_LayoutBottomMargin: 0,
        QStyle.PixelMetric.PM_LayoutLeftMargin: 0,
        QStyle.PixelMetric.PM_LayoutRightMargin: 0,
        QStyle.PixelMetric.PM_LayoutTopMargin: 0,
        QStyle.PixelMetric.PM_LayoutHorizontalSpacing: 0,
        QStyle.PixelMetric.PM_LayoutVerticalSpacing: 0,
    }
    SH_dict = {
        QStyle.StyleHint.SH_Button_FocusPolicy: 0,
    }

    def pixelMetric(self, key, *args, **kwargs):
        return JPartyStyle.PM_dict.get(key, super().pixelMetric(key, *args, **kwargs))

    def styleHint(self, key, *args, **kwargs):
        return JPartyStyle.SH_dict.get(key, super().styleHint(key, *args, **kwargs))


class MyLabel(DynamicLabel):
    def __init__(self, text, initialSize, parent=None):
        super().__init__(text, initialSize, parent)
        self.font().setBold(True)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        add_shadow(self)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor("white"))
        self.setPalette(palette)

        self.show()
