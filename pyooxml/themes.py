"""
Theme selection for the GUI: builds a QPalette and a QMenu/QMenuBar
stylesheet from a vendored qt_themes.Theme, and persists the chosen one.
"""

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QAbstractScrollArea, QApplication, QProxyStyle, QStyle

from pyooxml._vendor.qt_themes import Theme, get_themes, update_palette

SETTINGS_ORGANIZATION = "digitalsleuth"
SETTINGS_APPLICATION = "PyOOXML"
THEME_KEY = "appearance/theme"

CLASSIC_NAME = "Classic"
MIN_CONTRAST = 4.5
# coloured XML text on top of a diff highlight
MIN_ON_HIGHLIGHT = 3.0
NAME_WORDS = {"github": "GitHub"}

# the theme in use (None is Classic), plus the style and palette to go back to
_active = {"theme": None, "style": None, "palette": None}

def _relativeLuminance(color: QColor) -> float:
    def linear(channel):
        c = channel / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = linear(color.red()), linear(color.green()), linear(color.blue())
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrastRatio(a: QColor, b: QColor) -> float:
    lumA, lumB = _relativeLuminance(a), _relativeLuminance(b)
    lighter, darker = max(lumA, lumB), min(lumA, lumB)
    return (lighter + 0.05) / (darker + 0.05)


def _bestContrastText(background: QColor, candidates) -> QColor:
    """Whichever of 'candidates' reads best against 'background', instead of
    guessing from the background's own brightness: that guess picks the
    wrong one for several themes (e.g. GitHub Light, Modern Light), making
    selected text nearly unreadable."""
    return max(candidates, key=lambda candidate: _contrastRatio(background, candidate))


def compositeColor(top: QColor, bottom: QColor, alpha: float) -> QColor:
    return QColor(
        *(
            round(t * alpha + b * (1 - alpha))
            for t, b in zip(top.getRgb()[:3], bottom.getRgb()[:3])
        )
    )


def readableColor(color: QColor, backgrounds, minimum=MIN_CONTRAST) -> QColor:
    def worst(candidate):
        return min(_contrastRatio(candidate, bg) for bg in backgrounds)

    if worst(color) >= minimum:
        return QColor(color)
    # shift toward white or black, keeping as much of the hue as possible
    pole = max((QColor("white"), QColor("black")), key=worst)
    for step in range(1, 20):
        mixed = compositeColor(pole, color, step / 20)
        if worst(mixed) >= minimum:
            return mixed
    return pole


def _tintColor(hue: QColor, base: QColor, needs, strength: float) -> QColor:
    # a highlight background, weakened until each (text colour, minimum) in
    # 'needs' stays readable on it, but never so far that it disappears
    tint = compositeColor(hue, base, strength)
    while strength > 0.14 and any(_contrastRatio(fg, tint) < low for fg, low in needs):
        strength -= 0.02
        tint = compositeColor(hue, base, strength)
    return tint


def _displayName(name):
    return " ".join(NAME_WORDS.get(word, word.title()) for word in name.split("_"))


def availableThemes():
    """{display name: Theme}, sorted, for every vendored built-in theme."""
    return dict(sorted((_displayName(name), theme) for name, theme in get_themes().items()))


def settings():
    return QSettings(
        QSettings.Format.IniFormat,
        QSettings.Scope.UserScope,
        SETTINGS_ORGANIZATION,
        SETTINGS_APPLICATION,
    )


def savedThemeName():
    name = settings().value(THEME_KEY)
    return name if isinstance(name, str) else CLASSIC_NAME


def saveThemeName(name):
    store = settings()
    store.setValue(THEME_KEY, name)
    store.sync()


def _selectedTextColor(theme: Theme) -> QColor:
    return readableColor(
        _bestContrastText(
            theme.primary, (theme.text, theme.mantle, theme.crust, theme.base)
        ),
        [theme.primary],
    )


def buildPalette(theme: Theme) -> QPalette:
    palette = QPalette()
    update_palette(palette, theme)
    role, group = QPalette.ColorRole, QPalette.ColorGroup
    base, alternate = palette.color(role.Base), palette.color(role.AlternateBase)
    window = palette.color(role.Window)
    # spare contrast on editor text leaves room for highlight backgrounds
    readable = {
        role.Text: readableColor(theme.text, [base, alternate], 6.0),
        role.WindowText: readableColor(theme.text, [window]),
        role.ButtonText: readableColor(theme.text, [palette.color(role.Button)]),
        role.ToolTipText: readableColor(theme.overlay2, [palette.color(role.ToolTipBase)]),
        role.PlaceholderText: readableColor(theme.overlay1, [base, window], 3.0),
        role.Link: readableColor(theme.secondary, [base, window]),
        role.LinkVisited: readableColor(theme.secondary, [base, window]),
    }
    for state in (group.Active, group.Inactive):
        for key, color in readable.items():
            palette.setColor(state, key, color)
    palette.setColor(group.Active, role.HighlightedText, _selectedTextColor(theme))
    for state, minimum in ((group.Inactive, MIN_CONTRAST), (group.Disabled, 3.0)):
        background = palette.color(state, role.Highlight)
        palette.setColor(
            state, role.HighlightedText, readableColor(theme.text, [background], minimum)
        )
    return palette


def menuStylesheet(theme: Theme | None) -> str:
    if theme is None:
        return ""
    dark = theme.is_dark_theme()
    base = theme.mantle if dark else theme.crust
    background = base.name()
    border = theme.surface1.name()
    text = readableColor(theme.text, [base]).name()
    disabled = readableColor(theme.overlay1, [base], 2.5).name()
    highlight = theme.primary.name()
    highlightText = _selectedTextColor(theme).name()
    return f"""
QMenu {{
    background-color: {background}; color: {text}; border: 1px solid {border}; margin: 0;
}}
QMenu::item {{
    background-color: {background}; color: {text}; margin: 0; padding: 4px 20px 4px 20px;
}}
QMenu::item:selected {{
    background-color: {highlight}; color: {highlightText}; margin: 0; padding: 4px 20px 4px 20px;
}}
QMenu::item:disabled {{
    background-color: {background}; color: {disabled};
}}
QMenu::separator {{
    height: 1px; background: {border}; margin: 4px 8px;
}}
QMenuBar {{
    background-color: {background}; color: {text};
}}
QMenuBar::item {{
    background-color: {background}; color: {text};
}}
QMenuBar::item:selected {{
    background-color: {highlight}; color: {highlightText};
}}
"""


class ThemeStyle(QProxyStyle):
    # Fusion, with fixes for the themes
    def __init__(self, outline: QColor):
        super().__init__("fusion")
        self.outline = outline

    def sizeFromContents(self, kind, option, size, widget=None):
        result = super().sizeFromContents(kind, option, size, widget)
        # unselected tab labels are drawn lower, which cuts off letters like "g"
        if kind == QStyle.ContentsType.CT_TabBarTab:
            result.setHeight(result.height() + 6)
        return result

    # the checkbox outline all but vanishes on light themes
    def drawPrimitive(self, element, option, painter, widget=None):
        super().drawPrimitive(element, option, painter, widget)
        if element != QStyle.PrimitiveElement.PE_IndicatorCheckBox:
            return
        color = QColor(self.outline)
        if not option.state & QStyle.StateFlag.State_Enabled:
            color.setAlpha(110)
        painter.save()
        painter.setPen(color)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(option.rect.adjusted(0, 0, -1, -1))
        painter.restore()


def applyTheme(name):
    app = QApplication.instance()
    if _active["style"] is None:
        _active["style"] = app.style().objectName()
        _active["palette"] = QPalette(app.palette())
    theme = availableThemes().get(name)
    leaving = _active["theme"] is not None
    _active["theme"] = theme
    # switching styles leaves the background fill of existing lists and editors
    # wrong, so note the native setting now and set it ourselves afterwards
    areas = [w for w in app.allWidgets() if isinstance(w, QAbstractScrollArea)]
    if theme is not None and not leaving:
        for area in areas:
            area.setProperty("nativeFill", area.viewport().autoFillBackground())
    if theme is not None:
        palette = buildPalette(theme)
        app.setStyleSheet("")
        app.setStyle(
            ThemeStyle(
                readableColor(
                    theme.overlay1,
                    [
                        palette.color(QPalette.ColorRole.Window),
                        palette.color(QPalette.ColorRole.Base),
                    ],
                    3.0,
                )
            )
        )
        app.setPalette(palette)
    elif leaving:
        app.setStyleSheet("")
        app.setStyle(_active["style"])
        app.setPalette(_active["palette"])
    app.setStyleSheet(menuStylesheet(theme))
    for area in areas:
        if theme is not None:
            area.viewport().setAutoFillBackground(True)
        elif leaving and area.property("nativeFill") is not None:
            area.viewport().setAutoFillBackground(area.property("nativeFill"))
    return name if theme is not None else CLASSIC_NAME


def currentThemeName():
    for name, theme in availableThemes().items():
        if theme == _active["theme"]:
            return name
    return CLASSIC_NAME


def highlightColors():
    # every colour drawn over a themed background, checked against what is behind it
    palette = QApplication.palette()
    role = QPalette.ColorRole
    theme = _active["theme"]
    base, window = palette.color(role.Base), palette.color(role.Window)

    def solid(color, background):
        return compositeColor(color, background, color.alphaF())

    # the Windows 11 style's alternate row colour is mostly transparent
    alternate = solid(palette.color(role.AlternateBase), base)
    text = solid(palette.color(role.Text), base)
    if theme is not None:
        red, green, yellow, blue = theme.red, theme.green, theme.yellow, theme.blue
        grey, warning = theme.overlay1, theme.red
        syntax = {
            "tag": theme.blue,
            "attr": theme.magenta,
            "string": theme.orange,
            "entity": theme.cyan,
            "comment": theme.green,
        }
    else:
        red, green = QColor(220, 60, 60), QColor(50, 170, 80)
        yellow, blue = QColor(225, 170, 30), QColor(60, 120, 220)
        grey, warning = QColor(128, 128, 128), QColor("#d9534f")
        syntax = {
            key: QColor(on_dark if base.lightness() < 128 else on_light)
            for key, on_dark, on_light in (
                ("tag", "#569cd6", "#1c4fa0"),
                ("attr", "#9cdcfe", "#7a3e9d"),
                ("string", "#ce9178", "#a31515"),
                ("entity", "#d7ba7d", "#a05a00"),
                ("comment", "#6a9955", "#2e7d32"),
            )
        }
    syntax = {key: readableColor(color, [base]) for key, color in syntax.items()}
    needs = [(text, MIN_CONTRAST)] + [(c, MIN_ON_HIGHLIGHT) for c in syntax.values()]
    kinds = {
        key: _tintColor(hue, base, needs, strength)
        for key, hue, strength in (
            ("del", red, 0.3),
            ("add", green, 0.3),
            ("chg", yellow, 0.3),
            ("pad", grey, 0.15),
        )
    }
    status = {
        key: _tintColor(hue, base, [(text, MIN_CONTRAST)], 0.25)
        for key, hue in (("same", green), ("diff", red), ("left", blue), ("right", blue))
    }
    return {
        "syntax": {
            key: readableColor(color, [base, *kinds.values()], MIN_ON_HIGHLIGHT)
            for key, color in syntax.items()
        },
        "kinds": kinds,
        "status": status,
        "gutter": readableColor(
            solid(palette.color(role.PlaceholderText), window), [window], 3.0
        ),
        "warning": readableColor(warning, [base, alternate]),
    }
