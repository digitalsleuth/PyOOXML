import hashlib
import html
import os
import re
import sys
import zipfile
import base64

from PyQt6.QtCore import (
    QEvent,
    QMarginsF,
    QRect,
    QRectF,
    QSize,
    QSizeF,
    Qt,
    QThread,
    QTimer,
    QUrl,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAbstractTextDocumentLayout,
    QAction,
    QActionGroup,
    QBrush,
    QColor,
    QDesktopServices,
    QFont,
    QFontDatabase,
    QIcon,
    QKeySequence,
    QPageLayout,
    QPageSize,
    QPainter,
    QPalette,
    QPdfWriter,
    QPixmap,
    QSyntaxHighlighter,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextOption,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pyooxml import themes
from pyooxml.pyooxml import (
    APP_NAME,
    GITHUB,
    SEARCH_MAX_HITS,
    VERSION,
    build_diff,
    build_report_html,
    compact_xml,
    compile_query,
    decode_xml,
    encode_xml,
    hex_dump,
    human_size,
    image_metadata,
    is_image_part,
    is_ole_file,
    is_xml_part,
    OOXMLPackage,
    pretty_xml,
    report_part_diffs,
    search_documents,
    validate_xml,
)
OPEN_FILTER = (
    "OOXML documents (*.docx *.docm *.dotx *.dotm *.xlsx *.xlsm *.xltx *.xltm "
    "*.pptx *.pptm *.potx *.potm *.ppsx *.ppsm *.vsdx *.zip);;All files (*)"
)
PATH_ROLE = Qt.ItemDataRole.UserRole
HIT_ROLE = Qt.ItemDataRole.UserRole + 1
REPORT_DPI = 150
IMAGE_ZOOM_STEP = 1.25
IMAGE_FIT_MARGIN = 24
IMAGE_VALUE_LIMIT = 300
STATUS_LABELS = {
    "same": "Identical",
    "diff": "Different",
    "left": "Only in left",
    "right": "Only in right",
}
__fingerprint__ = """
AAABAAIAMDAAAAEAIACoJQAAJgAAABAQAAABACAAaAQAAM4lAAAoAAAAMAAAAGAAAAABACAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAC9hGcXr4JvPgAAAAAAAAAAwoJYDrZ+V2qwgWEDAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAC/hGd/uIRsVgAAAAC9gmJPqH1n/Zp8bn+hh4UBwYBUH7N6UPCnelWY
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAMWKcAy+h29Juot5BQAAAAC/hGV7s4Bm+6t/aaGpgW4KpX1o
VpZ4ZfaReGaGAAAAALB7UUCjdk74nHdRcwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMOGajm7g2n3sIFt4KmB
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
"""


class XmlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.set_colors(themes.highlightColors()["syntax"])

    def set_colors(self, colors):
        def fmt(key):
            f = QTextCharFormat()
            f.setForeground(colors[key])
            return f

        self._rules = [
            (re.compile(r"</?[\w:.-]+|/?>"), fmt("tag")),
            (re.compile(r"[\w:.-]+(?=\s*=)"), fmt("attr")),
            (re.compile(r"&[\w#]+;"), fmt("entity")),
            (re.compile(r"\"[^\"]*\"|'[^']*'"), fmt("string")),
            (re.compile(r"<!--.*?-->|<\?.*?\?>"), fmt("comment")),
        ]

    def highlightBlock(self, text):
        for rx, f in self._rules:
            for m in rx.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), f)


class _Gutter(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QSize(self._editor.gutter_width(), 0)

    def paintEvent(self, event):
        self._editor.paint_gutter(event)


class CodeEditor(QPlainTextEdit):

    def __init__(self, parent=None, read_only=False):
        super().__init__(parent)
        self.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setReadOnly(read_only)
        self._labels = None
        self._gutter = _Gutter(self)
        self._highlighter = XmlHighlighter(self.document())
        self.blockCountChanged.connect(self._update_gutter_width)
        self.updateRequest.connect(self._update_gutter)
        self._update_gutter_width()
        self.apply_colors()

    def apply_colors(self):
        # keep the selection looking the same when the editor loses focus; only
        # these two roles are overridden, so everything else follows the theme
        app_palette, own = QApplication.palette(), QPalette()
        for role in (QPalette.ColorRole.Highlight, QPalette.ColorRole.HighlightedText):
            own.setColor(
                QPalette.ColorGroup.Inactive,
                role,
                app_palette.color(QPalette.ColorGroup.Active, role),
            )
        self.setPalette(own)
        self._gutter_color = themes.highlightColors()["gutter"]
        self._gutter.update()

    def refresh_theme(self):
        self.apply_colors()
        # rehighlighting must not make an unedited part look edited
        modified = self.document().isModified()
        self._highlighter.set_colors(themes.highlightColors()["syntax"])
        self._highlighter.rehighlight()
        self.document().setModified(modified)

    def set_line_labels(self, labels):
        self._labels = labels
        self._update_gutter_width()
        self._gutter.update()

    def gutter_width(self):
        if self._labels is not None:
            digits = max((len(s) for s in self._labels), default=1)
        else:
            digits = len(str(max(1, self.blockCount())))
        return 12 + self.fontMetrics().horizontalAdvance("9") * max(digits, 2)

    def _update_gutter_width(self, *_):
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def _update_gutter(self, rect, dy):
        if dy:
            self._gutter.scroll(0, dy)
        else:
            self._gutter.update(0, rect.y(), self._gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_gutter_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._gutter.setGeometry(
            QRect(cr.left(), cr.top(), self.gutter_width(), cr.height())
        )

    def paint_gutter(self, event):
        painter = QPainter(self._gutter)
        painter.fillRect(event.rect(), self.palette().color(QPalette.ColorRole.Window))
        painter.setPen(self._gutter_color)
        block = self.firstVisibleBlock()
        n = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + round(self.blockBoundingRect(block).height())
        height = self.fontMetrics().height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                if self._labels is None:
                    label = str(n + 1)
                else:
                    label = self._labels[n] if n < len(self._labels) else ""
                painter.drawText(
                    0,
                    top,
                    self._gutter.width() - 6,
                    height,
                    Qt.AlignmentFlag.AlignRight,
                    label,
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            n += 1

    def select_match(self, line, col, length):
        block = self.document().findBlockByNumber(max(line - 1, 0))
        if not block.isValid():
            return False
        room = max(block.length() - 1, 0)
        col = min(max(col, 0), room)
        cursor = QTextCursor(block)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, col)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, min(length, room - col)
        )
        mark = QTextEdit.ExtraSelection()
        mark.cursor = cursor
        mark.format.setBackground(QColor("#ffd24d"))
        mark.format.setForeground(QColor("#000000"))
        self.setExtraSelections([mark])
        start = QTextCursor(cursor)
        start.setPosition(cursor.selectionStart())
        self.setTextCursor(start)
        self.centerCursor()
        self.setFocus()
        return True

    def marked_text(self):
        marks = self.extraSelections()
        return marks[0].cursor.selectedText() if marks else ""

    def setPlainText(self, text):
        self.setExtraSelections([])
        super().setPlainText(text)

    def goto(self, line, column=1):
        block = self.document().findBlockByNumber(max(line - 1, 0))
        cursor = QTextCursor(block)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.MoveAnchor,
            min(max(column - 1, 0), block.length() - 1),
        )
        self.setTextCursor(cursor)
        self.centerCursor()
        self.setFocus()


class Worker(QThread):

    done = pyqtSignal(int, object)

    def __init__(self, token, fn, *args):
        super().__init__()
        self._token, self._fn, self._args = token, fn, args

    def run(self):
        try:
            result = self._fn(*self._args)
        except Exception as e:
            result = e
        self.done.emit(self._token, result)


class DiffView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._starts = []
        self._cursor = -1
        self._labels = {"l": [], "r": []}
        self._result = None

        self.left_title, self.right_title = QLabel(), QLabel()
        for title in (self.left_title, self.right_title):
            title.setStyleSheet("font-weight: bold; padding: 2px 4px;")
        self.left = CodeEditor(read_only=True)
        self.right = CodeEditor(read_only=True)
        self.summary = QLabel()
        self.summary.setStyleSheet("padding: 2px 4px;")

        def column(title, editor):
            box = QWidget()
            lay = QVBoxLayout(box)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(0)
            lay.addWidget(title)
            lay.addWidget(editor)
            return box

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(column(self.left_title, self.left))
        splitter.addWidget(column(self.right_title, self.right))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.summary)
        layout.addWidget(splitter, 1)

        for a, b in ((self.left, self.right), (self.right, self.left)):
            a.verticalScrollBar().valueChanged.connect(b.verticalScrollBar().setValue)
            a.horizontalScrollBar().valueChanged.connect(
                b.horizontalScrollBar().setValue
            )

    def show_match(self, side, line, col, length):
        """Select a match on the numbered line of one side and scroll both panes to it."""
        try:
            row = self._labels[side].index(str(line))
        except ValueError:
            return False
        target = self.left if side == "l" else self.right
        for editor in (self.left, self.right):
            if editor is target:
                editor.select_match(row + 1, col, length)
            else:
                editor.setTextCursor(QTextCursor(editor.document().findBlockByNumber(row)))
                editor.centerCursor()
        return True

    def refresh_theme(self):
        for editor, side in ((self.left, "l"), (self.right, "r")):
            editor.refresh_theme()
            if self._result:
                self._paint(editor, self._result[side + "kind"])

    def show_message(self, text, left_title="", right_title=""):
        self._starts, self._cursor = [], -1
        self._labels = {"l": [], "r": []}
        self._result = None
        self.left_title.setText(left_title)
        self.right_title.setText(right_title)
        for editor in (self.left, self.right):
            editor.set_line_labels(None)
            editor.setPlainText("")
        self.summary.setText(text)

    def show_result(self, res, left_title, right_title):
        self._starts, self._cursor = res["starts"], -1
        self._labels = {"l": res["llabel"], "r": res["rlabel"]}
        self._result = res
        self.left_title.setText(left_title)
        self.right_title.setText(right_title)
        for editor, side in ((self.left, "l"), (self.right, "r")):
            editor.setPlainText("\n".join(res[side + "text"]))
            editor.set_line_labels(res[side + "label"])
            self._paint(editor, res[side + "kind"])
            editor.moveCursor(QTextCursor.MoveOperation.Start)
        if self._starts:
            self.summary.setText(
                f"{len(self._starts)} difference blocks: {res['added']} lines added, "
                f"{res['removed']} removed, {res['changed']} changed"
            )
            self.step(True)
        else:
            self.summary.setText("The parts are identical once formatted.")

    @staticmethod
    def _paint(editor, kinds):
        colors = themes.highlightColors()["kinds"]
        doc = editor.document()
        cursor = QTextCursor(doc)
        cursor.beginEditBlock()
        block = doc.begin()
        for kind in kinds:
            if not block.isValid():
                break
            if kind != "equal":
                cursor.setPosition(block.position())
                bf = QTextBlockFormat()
                bf.setBackground(QBrush(colors[kind]))
                cursor.setBlockFormat(bf)
            block = block.next()
        cursor.endEditBlock()

    def step(self, forward):
        if not self._starts:
            return
        self._cursor = (self._cursor + (1 if forward else -1)) % len(self._starts)
        row = self._starts[self._cursor]
        for editor in (self.left, self.right):
            cursor = QTextCursor(editor.document().findBlockByNumber(row))
            editor.setTextCursor(cursor)
            editor.centerCursor()


class MetadataTree(QTreeWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Property", "Value"])
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setUniformRowHeights(True)

    def set_groups(self, groups):
        self.clear()
        for title, rows in groups:
            if not rows:
                continue
            head = QTreeWidgetItem(self, [title])
            font = head.font(0)
            font.setBold(True)
            head.setFont(0, font)
            for key, value in rows:
                tip = getattr(value, "tip", None)
                value = str(value)
                shown = " ".join(value.split())
                if len(shown) > IMAGE_VALUE_LIMIT:
                    shown = shown[:IMAGE_VALUE_LIMIT] + "..."
                item = QTreeWidgetItem(head, [key, shown])
                item.setData(1, Qt.ItemDataRole.UserRole, value)
                item.setToolTip(1, tip or value[:2000])
            head.setExpanded(True)
        self.resizeColumnToContents(0)
        self.refresh_theme()

    def refresh_theme(self):
        warning = QBrush(themes.highlightColors()["warning"])
        for i in range(self.topLevelItemCount()):
            head = self.topLevelItem(i)
            for j in range(head.childCount()):
                value = head.child(j).data(1, Qt.ItemDataRole.UserRole)
                if value.startswith(("WARNING", "UNVERIFIED")):
                    head.child(j).setForeground(1, warning)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Copy):
            lines = []
            for i in range(self.topLevelItemCount()):
                head = self.topLevelItem(i)
                if head.isSelected():
                    lines.append(head.text(0))
                for j in range(head.childCount()):
                    item = head.child(j)
                    if item.isSelected():
                        lines.append(f"{item.text(0)}\t{item.data(1, Qt.ItemDataRole.UserRole)}")
            QApplication.clipboard().setText("\n".join(lines))
        else:
            super().keyPressEvent(event)


class ImageView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._zoom = None
        self._note = ""

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll = QScrollArea()
        self.scroll.setWidget(self.label)
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.viewport().installEventFilter(self)

        self.zoom_out_btn = QPushButton("-")
        self.zoom_in_btn = QPushButton("+")
        self.fit_btn = QPushButton("Fit")
        self.actual_btn = QPushButton("100%")
        self.zoom_label = QLabel()
        for button in (self.zoom_out_btn, self.zoom_in_btn):
            button.setFixedWidth(32)
        self.zoom_out_btn.setToolTip("Zoom out")
        self.zoom_in_btn.setToolTip("Zoom in (Ctrl + mouse wheel also zooms)")
        self.fit_btn.setToolTip("Scale the image to fit the window")
        self.actual_btn.setToolTip("Show the image at its actual size")
        self.zoom_out_btn.clicked.connect(lambda: self._step(1 / IMAGE_ZOOM_STEP))
        self.zoom_in_btn.clicked.connect(lambda: self._step(IMAGE_ZOOM_STEP))
        self.fit_btn.clicked.connect(self._fit)
        self.actual_btn.clicked.connect(lambda: self._set_zoom(1.0))

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Zoom:"))
        bar.addWidget(self.zoom_out_btn)
        bar.addWidget(self.zoom_label)
        bar.addWidget(self.zoom_in_btn)
        bar.addWidget(self.fit_btn)
        bar.addWidget(self.actual_btn)
        bar.addStretch(1)
        top = QWidget()
        lay = QVBoxLayout(top)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(bar)
        lay.addWidget(self.scroll, 1)

        self.meta = MetadataTree()
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(top)
        self.splitter.addWidget(self.meta)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.splitter)
        self._render()

    def clear(self):
        self._pixmap, self._zoom, self._note = None, None, ""
        self.meta.clear()
        self._render()

    def show_image(self, pixmap, groups, note=""):
        self._pixmap = pixmap if pixmap is not None and not pixmap.isNull() else None
        self._note = note
        self._zoom = None
        self.meta.set_groups(groups)
        self._render()

    def scale(self):
        if self._pixmap is None:
            return 1.0
        if self._zoom is not None:
            return self._zoom
        view = self.scroll.viewport().size()
        if view.width() < 32 or view.height() < 32:
            return 1.0
        return min(
            1.0,
            (view.width() - IMAGE_FIT_MARGIN) / self._pixmap.width(),
            (view.height() - IMAGE_FIT_MARGIN) / self._pixmap.height(),
        )

    def _render(self):
        has_image = self._pixmap is not None
        for button in (self.zoom_out_btn, self.zoom_in_btn, self.fit_btn, self.actual_btn):
            button.setEnabled(has_image)
        if not has_image:
            self.label.clear()
            self.label.setText(self._note)
            self.zoom_label.setText("")
            return
        scale = self.scale()
        self.zoom_label.setText(f"{round(scale * 100)}%")
        if abs(scale - 1.0) < 1e-9:
            self.label.setPixmap(self._pixmap)
        else:
            self.label.setPixmap(
                self._pixmap.scaled(
                    max(1, round(self._pixmap.width() * scale)),
                    max(1, round(self._pixmap.height() * scale)),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

    def _set_zoom(self, value):
        self._zoom = min(max(value, 0.05), 8.0)
        self._render()

    def _step(self, factor):
        self._set_zoom(self.scale() * factor)

    def _fit(self):
        self._zoom = None
        self._render()

    def eventFilter(self, obj, event):
        if obj is self.scroll.viewport():
            if event.type() == QEvent.Type.Resize and self._zoom is None:
                self._render()
            elif (
                event.type() == QEvent.Type.Wheel
                and self._pixmap is not None
                and event.modifiers() & Qt.KeyboardModifier.ControlModifier
            ):
                self._step(IMAGE_ZOOM_STEP if event.angleDelta().y() > 0 else 1 / IMAGE_ZOOM_STEP)
                return True
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        super().showEvent(event)
        if self._zoom is None:
            self._render()


class ViewerTab(QWidget):
    changed = pyqtSignal()
    message = pyqtSignal(str)

    PAGE_EMPTY, PAGE_EDITOR, PAGE_IMAGE, PAGE_INFO = range(4)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pkg = None
        self._part = None
        self._enc = "utf-8"
        self._error = None
        self._suppress = False

        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter parts...")
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(self._apply_filter)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Part", "Size"])
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.currentItemChanged.connect(self._on_current_changed)

        left = QWidget()
        lay = QVBoxLayout(left)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.filter)
        lay.addWidget(self.tree)

        self.part_label = QLabel("Open a document to see its parts")
        self.part_label.setStyleSheet("font-weight: bold;")
        self.change_label = QLabel()
        self.banner = QLabel()
        self.banner.setTextFormat(Qt.TextFormat.RichText)
        self.banner.setStyleSheet(
            "background: #fff4c2; color: #5a4300; padding: 4px 8px; border: 1px solid #e0c870;"
        )
        self.banner.linkActivated.connect(self._goto_error)
        self.banner.hide()

        self.editor = CodeEditor(read_only=True)
        self.editor.document().modificationChanged.connect(
            self._on_modification_changed
        )
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setCheckable(True)
        self.edit_btn.setToolTip("Allow the content of this part to be edited")
        self.edit_btn.clicked.connect(self._toggle_edit)
        self.save_btn = QPushButton("Save Part")
        self.save_btn.setToolTip("Keep the edited content of this part in the package")
        self.save_btn.clicked.connect(lambda: self.save_part())
        self.edit_btn.setEnabled(False)
        self.save_btn.hide()
        self.editor.textChanged.connect(lambda: self._validate_timer.start())
        self._validate_timer = QTimer(self, singleShot=True, interval=600)
        self._validate_timer.timeout.connect(self._validate)

        self.empty = QLabel("Select a part to view its content")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_view = ImageView()
        self.info = QPlainTextEdit()
        self.info.setReadOnly(True)
        self.info.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.stack = QStackedWidget()
        for page in (self.empty, self.editor, self.image_view, self.info):
            self.stack.addWidget(page)

        right = QWidget()
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(4, 0, 0, 0)
        head = QHBoxLayout()
        head.addWidget(self.part_label, 1)
        head.addWidget(self.change_label)
        head.addWidget(self.save_btn)
        head.addWidget(self.edit_btn)
        rlay.addLayout(head)
        rlay.addWidget(self.banner)
        rlay.addWidget(self.stack, 1)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([280, 760])
        outer = QHBoxLayout(self)
        outer.addWidget(splitter)

    def load(self, pkg):
        self.pkg, self._part = pkg, None
        self.stack.setCurrentIndex(self.PAGE_EMPTY)
        self.banner.hide()
        self.change_label.clear()
        self.part_label.setText("Select a part to view its content")
        self.filter.clear()
        self.editor.setReadOnly(True)
        self._populate()
        self._update_buttons()
        self.changed.emit()

    def unload(self):
        self.pkg, self._part, self._error = None, None, None
        self.stack.setCurrentIndex(self.PAGE_EMPTY)
        self.tree.clear()
        self.filter.clear()
        self.banner.hide()
        self.change_label.clear()
        self.part_label.setText("Open a document to see its parts")
        self.editor.setReadOnly(True)
        self.editor.setPlainText("")
        self.editor.document().setModified(False)
        self.info.setPlainText("")
        self.image_view.clear()
        self._update_buttons()
        self.changed.emit()

    def _populate(self):
        self._suppress = True
        self.tree.clear()
        style = self.style()
        folder_icon = style.standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        file_icon = style.standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        folders = {}
        for name in sorted(self.pkg.data, key=str.lower):
            parts = name.split("/")
            parent = self.tree.invisibleRootItem()
            for i, piece in enumerate(parts[:-1]):
                key = "/".join(parts[: i + 1])
                if key not in folders:
                    item = QTreeWidgetItem(parent, [piece])
                    item.setIcon(0, folder_icon)
                    folders[key] = item
                parent = folders[key]
            item = QTreeWidgetItem(
                parent, [self._label(name), human_size(len(self.pkg.data[name]))]
            )
            if name in self.pkg.recovered:
                item.setToolTip(0, self._recovery_text(name))
            item.setIcon(0, file_icon)
            item.setData(0, PATH_ROLE, name)
            item.setTextAlignment(1, Qt.AlignmentFlag.AlignRight)
        self.tree.expandAll()
        self.tree.resizeColumnToContents(1)
        self._suppress = False

    def _file_items(self):
        stack = [self.tree.invisibleRootItem()]
        while stack:
            node = stack.pop()
            for i in range(node.childCount()):
                child = node.child(i)
                stack.append(child)
                if child.data(0, PATH_ROLE):
                    yield child

    def _item_for(self, part):
        return next(
            (i for i in self._file_items() if i.data(0, PATH_ROLE) == part), None
        )

    def show_match(self, part, line, col, length):
        item = self._item_for(part)
        if not item:
            return False
        if item.isHidden():
            self.filter.clear()
        self.tree.setCurrentItem(item)
        self.tree.scrollToItem(item)
        if self._part != part or self.stack.currentIndex() != self.PAGE_EDITOR:
            return False
        return self.editor.select_match(line, col, length)

    def _apply_filter(self, text):
        needle = text.lower().strip()

        def visit(node):
            visible = False
            for i in range(node.childCount()):
                child = node.child(i)
                path = child.data(0, PATH_ROLE)
                show = (needle in path.lower()) if path else visit(child)
                child.setHidden(not show)
                visible = visible or show
            return visible

        visit(self.tree.invisibleRootItem())

    def _label(self, part):
        name = part.rsplit("/", 1)[-1]
        if self.pkg.recovered.get(part):
            name += " (unverified)"
        return name + (" *" if part in self.pkg.modified else "")

    def _recovery_text(self, part):
        problem = self.pkg.recovered[part]
        if problem:
            return (
                f"UNVERIFIED: recovered from the raw file but failed its integrity "
                f"check ({problem}). The content decoded completely but may be "
                f"inaccurate."
            )
        return (
            "Recovered from the raw file after its zip headers failed to read; "
            "verified against its recorded CRC32/size."
        )

    def _show_recovery_note(self):
        if self._part in self.pkg.recovered and self.pkg.recovered[self._part]:
            self.banner.setText(self._recovery_text(self._part))
            self.banner.show()
        else:
            self.banner.hide()

    def _mark_item(self, part):
        item = self._item_for(part)
        if item:
            edited = part in self.pkg.modified
            item.setText(0, self._label(part))
            font = item.font(0)
            font.setBold(edited)
            item.setFont(0, font)

    def _editor_dirty(self):
        return (
            self._part is not None
            and self.stack.currentIndex() == self.PAGE_EDITOR
            and self.editor.document().isModified()
        )

    def _update_buttons(self):
        on_editor = (
            self._part is not None and self.stack.currentIndex() == self.PAGE_EDITOR
        )
        self.edit_btn.setEnabled(on_editor)
        self.edit_btn.setChecked(on_editor and not self.editor.isReadOnly())
        self.save_btn.setVisible(self._editor_dirty())

    def _toggle_edit(self, checked):
        if checked:
            self.editor.setReadOnly(False)
            self.editor.setFocus()
        elif self._editor_dirty():
            if self._resolve_dirty_editor():
                self._show_part(self._part)
            else:
                self.edit_btn.setChecked(True)
                return
        else:
            self.editor.setReadOnly(True)
        self._update_buttons()

    def _on_current_changed(self, cur, prev):
        if self._suppress or not self.pkg:
            return
        part = cur.data(0, PATH_ROLE) if cur else None
        if part == self._part:
            return
        if self._editor_dirty() and not self._resolve_dirty_editor():
            self._suppress = True
            self.tree.setCurrentItem(prev)
            self._suppress = False
            return
        if part:
            self._show_part(part)

    def _resolve_dirty_editor(self):
        box = QMessageBox(
            QMessageBox.Icon.Question,
            "Unsaved changes",
            f"Save changes to {self._part.rsplit('/', 1)[-1]}?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            self,
        )
        choice = box.exec()
        if choice == QMessageBox.StandardButton.Save:
            return self.save_part()
        return choice == QMessageBox.StandardButton.Discard

    def _show_part(self, part):
        self._part = part
        raw = self.pkg.data[part]
        self.part_label.setText(part)
        self.change_label.setText("Edited" if part in self.pkg.modified else "")
        self.banner.hide()
        self.editor.setReadOnly(True)
        if is_xml_part(part):
            text, self._enc = decode_xml(raw)
            shown, ok = pretty_xml(text)
            self.editor.setPlainText(shown)
            self.editor.document().setModified(False)
            self.editor.moveCursor(QTextCursor.MoveOperation.Start)
            self.stack.setCurrentIndex(self.PAGE_EDITOR)
            self._validate()
        elif is_image_part(part) and self._show_image(part, raw):
            pass
        else:
            self.info.setPlainText(
                f"Cannot display the content of {part}\n"
                f"{len(raw)} bytes, sha256 {hashlib.sha256(raw).hexdigest()}\n\n"
                + hex_dump(raw)
            )
            self.stack.setCurrentIndex(self.PAGE_INFO)
        if not is_xml_part(part):
            self._show_recovery_note()
        self._update_buttons()
        self.changed.emit()

    def _show_image(self, part, raw):
        pixmap = QPixmap()
        decoded = pixmap.loadFromData(raw)
        kind, groups = image_metadata(self.pkg, part, raw, pixmap.size() if decoded else None)
        if not decoded and kind is None:
            return False
        note = "" if decoded else "The image data could not be decoded, so only its metadata is shown."
        self.image_view.show_image(pixmap if decoded else None, groups, note)
        self.stack.setCurrentIndex(self.PAGE_IMAGE)
        return True

    def _validate(self):
        if self.stack.currentIndex() != self.PAGE_EDITOR:
            return
        err = validate_xml(self.editor.toPlainText())
        if err:
            line, col, msg = err
            self._error = err
            self.banner.setText(
                f"XML error on line {line} at column {col}: {msg} "
                f"&nbsp;<a href='goto' style='color:#0b3d91'>Go to error</a>"
            )
            self.banner.show()
        else:
            self._error = None
            self._show_recovery_note()

    def _goto_error(self, _link):
        if self._error:
            self.editor.goto(self._error[0], self._error[1])

    def _on_modification_changed(self, modified):
        if self.stack.currentIndex() == self.PAGE_EDITOR:
            self.change_label.setText(
                "Unsaved changes*"
                if modified
                else ("Saved" if self._part in self.pkg.modified else "")
            )
        self._update_buttons()
        self.changed.emit()

    def save_part(self):
        if not self._editor_dirty():
            return True
        text = self.editor.toPlainText()
        err = validate_xml(text)
        if err:
            line, col, msg = err
            box = QMessageBox(
                QMessageBox.Icon.Warning,
                "XML error",
                f"Error on line {line} at column {col}: {msg}",
                parent=self,
            )
            save_anyway = box.addButton(
                "Save Anyway", QMessageBox.ButtonRole.DestructiveRole
            )
            goto = box.addButton("Go to Error", QMessageBox.ButtonRole.ActionRole)
            box.addButton(QMessageBox.StandardButton.Cancel)
            box.exec()
            if box.clickedButton() is goto:
                self.editor.goto(line, col)
                return False
            if box.clickedButton() is not save_anyway:
                return False
        self.pkg.set_data(self._part, encode_xml(compact_xml(text), self._enc))
        self.editor.document().setModified(False)
        self._mark_item(self._part)
        self.message.emit(f"Saved {self._part} (not yet written to a file)")
        self.changed.emit()
        return True

    def extract_part(self):
        if not (self.pkg and self._part):
            return
        default = os.path.join(
            os.path.dirname(self.pkg.path), self._part.rsplit("/", 1)[-1]
        )
        dest, _ = QFileDialog.getSaveFileName(self, "Extract part", default)
        if dest:
            dest = os.path.normpath(dest)
            with open(dest, "wb") as fh:
                fh.write(self.pkg.data[self._part])
            self.message.emit(f"Extracted {self._part} to {dest}")

    def save_package_as(self):
        if not self.pkg:
            return False
        if self._editor_dirty() and not self.save_part():
            return False
        stem, ext = os.path.splitext(self.pkg.path)
        dest, _ = QFileDialog.getSaveFileName(
            self, "Save package as", f"{stem}_edited{ext}", OPEN_FILTER
        )
        if not dest:
            return False
        dest = os.path.normpath(dest)
        try:
            self.pkg.save(dest)
        except OSError as e:
            QMessageBox.critical(self, APP_NAME, f"Could not write the file:\n{e}")
            return False
        for item in self._file_items():
            self._mark_item(item.data(0, PATH_ROLE))
        self.change_label.clear()
        self.message.emit(f"Wrote {dest}")
        self.changed.emit()
        return True

    def can_discard(self):
        if not self.pkg:
            return True
        if self._editor_dirty() and not self._resolve_dirty_editor():
            return False
        if self.pkg.modified:
            box = QMessageBox(
                QMessageBox.Icon.Question,
                "Unsaved package",
                "Edited parts have not been written to a file.",
                parent=self,
            )
            save = box.addButton(
                "Save Package As...", QMessageBox.ButtonRole.AcceptRole
            )
            discard = box.addButton("Discard", QMessageBox.ButtonRole.DestructiveRole)
            box.addButton(QMessageBox.StandardButton.Cancel)
            box.exec()
            if box.clickedButton() is save:
                return self.save_package_as()
            return box.clickedButton() is discard
        return True

    def is_dirty(self):
        return bool(self.pkg) and (self._editor_dirty() or bool(self.pkg.modified))


def write_report_pdf(path, left, right, rows, step=None):
    diffs = report_part_diffs(rows, step)
    if diffs is None:
        return False
    mono = "Consolas"
    if mono not in QFontDatabase.families():
        mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family()
    body = build_report_html(left, right, rows, diffs, mono)

    writer = QPdfWriter(path)
    writer.setTitle(f"{left.name} vs {right.name}")
    writer.setCreator(f"{APP_NAME} v{VERSION}")
    writer.setResolution(REPORT_DPI)
    writer.setPageLayout(
        QPageLayout(
            QPageSize(QPageSize.PageSizeId.Letter),
            QPageLayout.Orientation.Landscape,
            QMarginsF(36, 36, 36, 36),
            QPageLayout.Unit.Point,
        )
    )
    footer = round(REPORT_DPI * 0.3)
    width, page_h = writer.width(), writer.height() - footer

    doc = QTextDocument()
    doc.documentLayout().setPaintDevice(writer)
    doc.setDefaultFont(
        QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    )
    font = doc.defaultFont()
    font.setPointSize(9)
    doc.setDefaultFont(font)
    option = QTextOption()
    option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
    doc.setDefaultTextOption(option)
    doc.setPageSize(QSizeF(width, page_h))
    doc.setHtml(body)

    painter = QPainter()
    if not painter.begin(writer):
        raise OSError(f"Cannot write to {path}")
    try:
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Text, QColor("black"))
        small = QFont(font)
        small.setPointSize(8)
        pages = doc.pageCount()
        for n in range(pages):
            if n:
                writer.newPage()
            painter.save()
            painter.setClipRect(QRectF(0, 0, width, page_h))
            painter.translate(0, -n * page_h)
            ctx = QAbstractTextDocumentLayout.PaintContext()
            ctx.palette = palette
            ctx.clip = QRectF(0, n * page_h, width, page_h)
            doc.documentLayout().draw(painter, ctx)
            painter.restore()
            painter.setFont(small)
            painter.setPen(QColor("#666666"))
            area = QRectF(0, page_h, width, footer)
            align = Qt.AlignmentFlag.AlignVCenter
            painter.drawText(
                area,
                align | Qt.AlignmentFlag.AlignLeft,
                f"{APP_NAME} v{VERSION}   {left.name}  vs  {right.name}",
            )
            painter.drawText(
                area, align | Qt.AlignmentFlag.AlignRight, f"Page {n + 1} of {pages}"
            )
    finally:
        painter.end()
    return True



class CompareTab(QWidget):
    message = pyqtSignal(str)
    swapped = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.left_pkg = self.right_pkg = None
        self._rows = []
        self._token = 0
        self._workers = set()
        self._shown_part = None
        self._pending = None

        self.header = QLabel("Use File > Compare Documents... to choose two documents.")
        self.swap = QPushButton("Swap sides")
        self.swap.clicked.connect(self.swap_sides)
        self.export_btn = QPushButton("Export PDF...")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_report)
        self.only_diffs = QCheckBox("Differences only")
        self.only_diffs.toggled.connect(self._rebuild)
        prev_btn, next_btn = QPushButton("Previous difference"), QPushButton(
            "Next difference"
        )
        prev_btn.clicked.connect(lambda: self.diff.step(False))
        next_btn.clicked.connect(lambda: self.diff.step(True))
        prev_btn.setShortcut(QKeySequence("Shift+F3"))
        next_btn.setShortcut(QKeySequence("F3"))

        bar = QHBoxLayout()
        bar.addWidget(self.header, 1)
        bar.addWidget(self.only_diffs)
        bar.addWidget(self.swap)
        bar.addWidget(self.export_btn)
        bar.addWidget(prev_btn)
        bar.addWidget(next_btn)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Status", "Part", "Left", "Right"])
        self.tree.setRootIsDecorated(False)
        self.tree.currentItemChanged.connect(self._on_current_changed)
        self.diff = DiffView()
        self.diff.show_message("Select a part to see how it differs.")

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.tree)
        splitter.addWidget(self.diff)
        splitter.setSizes([260, 460])
        layout = QVBoxLayout(self)
        layout.addLayout(bar)
        layout.addWidget(splitter, 1)

    def clear(self):
        self._token += 1
        self.left_pkg = self.right_pkg = None
        self._rows = []
        self._shown_part = self._pending = None
        self.export_btn.setEnabled(False)
        self.tree.clear()
        self.header.setText("Use File > Compare Documents... to choose two documents.")
        self.diff.show_message("Select a part to see how it differs.")

    def export_report(self):
        if not self.left_pkg:
            return
        stem = lambda p: os.path.splitext(p.name)[0]
        default = os.path.join(
            os.path.dirname(self.left_pkg.path),
            f"{stem(self.left_pkg)} vs {stem(self.right_pkg)}.pdf",
        )
        path, _ = QFileDialog.getSaveFileName(
            self, "Export comparison report", default, "PDF files (*.pdf)"
        )
        if not path:
            return
        path = os.path.normpath(path if path.lower().endswith(".pdf") else path + ".pdf")
        progress = QProgressDialog("Building the report...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(500)

        def step(i, n, name):
            progress.setValue(int(90 * i / max(n, 1)))
            progress.setLabelText(f"Comparing {name}")
            QApplication.processEvents()
            return progress.wasCanceled()

        try:
            done = write_report_pdf(
                path, self.left_pkg, self.right_pkg, self._rows, step
            )
        except OSError as e:
            progress.close()
            QMessageBox.critical(
                self, "Could not write the report", f"{path}\n\n{e}"
            )
            return
        progress.close()
        if not done:
            return
        self.message.emit(f"Report written to {path}")
        box = QMessageBox(
            QMessageBox.Icon.Question,
            "Report exported",
            f"The report was written to:\n{path}\n\nOpen it now?",
            QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Close,
            self,
        )
        box.setDefaultButton(QMessageBox.StandardButton.Open)
        if (
            box.exec() == QMessageBox.StandardButton.Open
            and not QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        ):
            QMessageBox.warning(
                self, "Could not open the report", f"No application found to open:\n{path}"
            )

    def set_packages(self, left, right):
        self.left_pkg, self.right_pkg = left, right
        self.export_btn.setEnabled(True)
        names = sorted(set(left.data) | set(right.data), key=str.lower)
        self._rows = []
        for name in names:
            a, b = left.data.get(name), right.data.get(name)
            if a is None:
                status = "right"
            elif b is None:
                status = "left"
            else:
                status = "same" if a == b else "diff"
            self._rows.append((name, a, b, status))
        self._rebuild()

    def swap_sides(self):
        if self.left_pkg:
            self.set_packages(self.right_pkg, self.left_pkg)
            self.swapped.emit()

    def refresh_theme(self):
        self.diff.refresh_theme()
        # recolour in place, so the selected part stays selected
        colors = themes.highlightColors()["status"]
        statuses = {name: status for name, _, _, status in self._rows}
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            brush = QBrush(colors[statuses[item.data(0, PATH_ROLE)]])
            for col in range(4):
                item.setBackground(col, brush)

    def _rebuild(self, *_):
        if not self.left_pkg:
            return
        self.header.setText(
            f"<b>{self.left_pkg.name}</b> &nbsp;vs&nbsp; <b>{self.right_pkg.name}</b>"
        )
        counts = {k: 0 for k in STATUS_LABELS}
        colors = themes.highlightColors()["status"]
        self.tree.clear()
        for name, a, b, status in self._rows:
            counts[status] += 1
            if self.only_diffs.isChecked() and status == "same":
                continue
            item = QTreeWidgetItem(
                [
                    STATUS_LABELS[status],
                    name,
                    human_size(len(a)) if a is not None else "-",
                    human_size(len(b)) if b is not None else "-",
                ]
            )
            item.setData(0, PATH_ROLE, name)
            for col in range(4):
                item.setBackground(col, QBrush(colors[status]))
            self.tree.addTopLevelItem(item)
        for col in (0, 2, 3):
            self.tree.resizeColumnToContents(col)
        self.message.emit(
            f"{len(self._rows)} parts: {counts['same']} identical, {counts['diff']} different, "
            f"{counts['left']} only in left, {counts['right']} only in right"
        )
        if self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(0))
        else:
            self.diff.show_message("No parts to show.")

    def _find_item(self, part):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.data(0, PATH_ROLE) == part:
                return item
        return None

    def show_match(self, pkg, part, line, col, length):
        """Jump to a search hit on the numbered line of the part's left or right side."""
        side = "l" if pkg is self.left_pkg else "r"
        item = self._find_item(part)
        if item is None and self.only_diffs.isChecked():
            self.only_diffs.setChecked(False)
            item = self._find_item(part)
        if item is None:
            return False
        self._pending = (side, line, col, length, part)
        if self.tree.currentItem() is not item:
            self.tree.setCurrentItem(item)
        elif self._shown_part == part:
            self._apply_pending()
        self.tree.scrollToItem(item)
        return True

    def _apply_pending(self):
        side, line, col, length, _ = self._pending
        self._pending = None
        self.diff.show_match(side, line, col, length)

    def _on_current_changed(self, cur, _prev):
        self._shown_part = None
        if self._pending and (not cur or cur.data(0, PATH_ROLE) != self._pending[4]):
            self._pending = None
        if not cur:
            return
        name = cur.data(0, PATH_ROLE)
        _, a, b, status = next(r for r in self._rows if r[0] == name)
        left_title = f"{self.left_pkg.name}/{name}" if a is not None else "(missing)"
        right_title = f"{self.right_pkg.name}/{name}" if b is not None else "(missing)"
        if not is_xml_part(name):
            if status == "same":
                note = "Identical (not an XML part)."
            else:
                digests = [
                    hashlib.sha256(x).hexdigest()[:16] if x is not None else "-"
                    for x in (a, b)
                ]
                note = (
                    f"Not an XML part, so no text diff. Sizes: "
                    f"{human_size(len(a)) if a is not None else '-'} vs "
                    f"{human_size(len(b)) if b is not None else '-'}; "
                    f"sha256: {digests[0]} vs {digests[1]}"
                )
            self.diff.show_message(note, left_title, right_title)
            return
        self._token += 1
        self.diff.show_message("Computing differences...", left_title, right_title)
        worker = Worker(self._token, build_diff, a, b)
        worker.done.connect(
            lambda tok, res, t=(left_title, right_title, name): self._diff_ready(
                tok, res, *t
            )
        )
        worker.finished.connect(lambda w=worker: self._workers.discard(w))
        self._workers.add(worker)
        worker.start()

    def _diff_ready(self, token, result, left_title, right_title, name=None):
        if token != self._token:
            return
        if isinstance(result, Exception):
            self.diff.show_message(
                f"Could not compute the diff: {result}", left_title, right_title
            )
        else:
            self.diff.show_result(result, left_title, right_title)
            self._shown_part = name
            if self._pending and self._pending[4] == name:
                self._apply_pending()


class WarningsTab(QWidget):
    activated = pyqtSignal(object, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Document", "Part", "Warning"])
        self.tree.setRootIsDecorated(False)
        self.tree.setWordWrap(True)
        self.tree.itemActivated.connect(self._on_activated)
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)

    def set_rows(self, rows):
        self.tree.clear()
        for pkg, part, text in rows:
            item = QTreeWidgetItem([pkg.name, part, text])
            item.setToolTip(0, pkg.path)
            item.setData(0, PATH_ROLE, (pkg, part))
            self.tree.addTopLevelItem(item)
        for col in (0, 1):
            self.tree.resizeColumnToContents(col)

    def _on_activated(self, item, _col):
        pkg, part = item.data(0, PATH_ROLE)
        if part:
            self.activated.emit(pkg, part)


class HitDelegate(QStyledItemDelegate):
    """Paints the match column from HTML so the hit itself is highlighted."""

    def paint(self, painter, option, index):
        html_text = index.data(HIT_ROLE)
        if index.column() != 3 or not html_text:
            return super().paint(painter, option, index)
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)
        selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        role = QPalette.ColorRole.HighlightedText if selected else QPalette.ColorRole.Text
        # an unfocused selection has its own background, so it needs its own text colour
        group = (
            QPalette.ColorGroup.Active
            if opt.state & QStyle.StateFlag.State_Active
            else QPalette.ColorGroup.Inactive
        )
        doc = QTextDocument()
        doc.setDefaultFont(opt.font)
        doc.setDocumentMargin(0)
        wrap = QTextOption()
        wrap.setWrapMode(QTextOption.WrapMode.NoWrap)
        doc.setDefaultTextOption(wrap)
        doc.setHtml(f'<span style="color:{opt.palette.color(group, role).name()}">{html_text}</span>')
        painter.save()
        painter.translate(opt.rect.left() + 4, opt.rect.top() + (opt.rect.height() - doc.size().height()) / 2)
        painter.setClipRect(QRectF(0, 0, opt.rect.width() - 4, opt.rect.height()))
        doc.drawContents(painter)
        painter.restore()


class SearchTab(QWidget):
    activated = pyqtSignal(object, str, int, int, int)

    ALL = -1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pkgs = []
        self._token = 0
        self._workers = set()

        self.query = QLineEdit()
        self.query.setPlaceholderText("Word or phrase to find")
        self.query.setClearButtonEnabled(True)
        self.find_btn = QPushButton("Find All")
        self.case = QCheckBox("Match case")
        self.word = QCheckBox("Whole word")
        self.regex = QCheckBox("Regular expression")
        self.text_only = QCheckBox("Text only")
        self.text_only.setToolTip(
            "Search the document text instead of the XML source, so a word split "
            "across several runs is still found. Each match is reported at the line "
            "where its text starts."
        )
        self.scope = QComboBox()
        self.summary = QLabel()
        self.summary.setWordWrap(True)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Document", "Part", "Line", "Match"])
        self.tree.setRootIsDecorated(False)
        self.tree.setUniformRowHeights(True)
        self.tree.setItemDelegate(HitDelegate(self.tree))
        self.tree.itemActivated.connect(self._on_activated)

        top = QHBoxLayout()
        top.addWidget(self.query, 1)
        top.addWidget(self.find_btn)
        opts = QHBoxLayout()
        for box in (self.case, self.word, self.regex, self.text_only):
            opts.addWidget(box)
        opts.addStretch(1)
        opts.addWidget(QLabel("Search in:"))
        opts.addWidget(self.scope)
        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addLayout(opts)
        layout.addWidget(self.summary)
        layout.addWidget(self.tree, 1)

        self.query.returnPressed.connect(self.run)
        self.find_btn.clicked.connect(self.run)
        self.set_documents([])

    def _label(self, pkg):
        if len(self._pkgs) == 2 and pkg in self._pkgs:
            return f"{('Left', 'Right')[self._pkgs.index(pkg)]}: {pkg.name}"
        return pkg.name

    def set_documents(self, pkgs):
        if {id(p) for p in pkgs} != {id(p) for p in self._pkgs}:
            self.clear_results()
        chosen = self.scope.currentData()
        keep = self._pkgs[chosen] if chosen not in (None, self.ALL) else None
        self._pkgs = list(pkgs)
        self.scope.clear()
        self.scope.addItem("All open documents", self.ALL)
        for i, pkg in enumerate(self._pkgs):
            self.scope.addItem(self._label(pkg), i)
        self.scope.setCurrentIndex(
            self._pkgs.index(keep) + 1 if keep in self._pkgs else 0
        )
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setText(0, self._label(item.data(0, PATH_ROLE)[0]))
        for widget in (self.query, self.find_btn, self.case, self.word, self.regex, self.text_only, self.scope):
            widget.setEnabled(bool(self._pkgs))
        if not self._pkgs:
            self.summary.setText("Open or compare documents to search them.")
        elif not self.tree.topLevelItemCount():
            self.summary.setText("")

    def clear_results(self):
        self._token += 1
        self.tree.clear()
        self.summary.setText("")

    def focus_query(self, text=None):
        if text:
            self.query.setText(text)
        self.query.setFocus()
        self.query.selectAll()

    def run(self):
        text = self.query.text()
        if not text or not self._pkgs:
            return
        try:
            rx = compile_query(
                text, self.case.isChecked(), self.word.isChecked(), self.regex.isChecked()
            )
        except re.error as e:
            self.summary.setText(f"Invalid regular expression: {e}")
            return
        chosen = self.scope.currentData()
        targets = self._pkgs if chosen in (None, self.ALL) else [self._pkgs[chosen]]
        jobs = [
            [(n, raw) for n, raw in sorted(p.data.items(), key=lambda kv: kv[0].lower()) if is_xml_part(n)]
            for p in targets
        ]
        self._token += 1
        self.tree.clear()
        self.summary.setText("Searching...")
        worker = Worker(self._token, search_documents, jobs, rx, self.text_only.isChecked())
        worker.done.connect(lambda tok, res, t=targets: self._done(tok, res, t))
        worker.finished.connect(lambda w=worker: self._workers.discard(w))
        self._workers.add(worker)
        worker.start()

    def _done(self, token, result, targets):
        if token != self._token:
            return
        if isinstance(result, Exception):
            self.summary.setText(f"The search failed: {result}")
            return
        hits, truncated = result
        self.tree.setUpdatesEnabled(False)
        for doc, part, line, col, length, snippet in hits:
            pkg = targets[doc]
            plain = re.sub(r"<[^>]+>", "", snippet)
            item = QTreeWidgetItem([self._label(pkg), part, str(line), html.unescape(plain)])
            item.setToolTip(0, pkg.path)
            item.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setData(0, PATH_ROLE, (pkg, part, line, col, length))
            item.setData(3, HIT_ROLE, snippet)
            self.tree.addTopLevelItem(item)
        self.tree.setUpdatesEnabled(True)
        for col in (0, 1, 2):
            self.tree.resizeColumnToContents(col)
        parts = {(id(targets[h[0]]), h[1]) for h in hits}
        if not hits:
            self.summary.setText("No matches.")
            return
        text = f"{len(hits)} match{'es' if len(hits) != 1 else ''} in {len(parts)} part{'s' if len(parts) != 1 else ''}"
        if len(targets) > 1:
            counts = [sum(1 for h in hits if targets[h[0]] is p) for p in targets]
            text += " (" + ", ".join(f"{self._label(p)}: {c}" for p, c in zip(targets, counts)) + ")"
        if truncated:
            text += f". Only the first {SEARCH_MAX_HITS} matches are shown; refine the search to see the rest."
        self.summary.setText(text)

    def _on_activated(self, item, _col):
        self.activated.emit(*item.data(0, PATH_ROLE))


class PathLabel(QLabel):
    SEPARATOR = "   vs   "

    def __init__(self, parent=None):
        super().__init__(parent)
        self._paths = []
        self.hide()

    def set_paths(self, paths):
        self._paths = list(paths)
        self.setToolTip("\n".join(self._paths))
        self.setVisible(bool(self._paths))
        self._elide()
        self.updateGeometry()

    def _full_text(self):
        return self.SEPARATOR.join(self._paths)

    def sizeHint(self):
        return QSize(
            self.fontMetrics().horizontalAdvance(self._full_text()) + 12,
            super().sizeHint().height(),
        )

    def minimumSizeHint(self):
        return QSize(0, super().minimumSizeHint().height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._elide()

    def _elide(self):
        if not self._paths:
            self.setText("")
            return
        metrics = self.fontMetrics()
        count = len(self._paths)
        gaps = metrics.horizontalAdvance(self.SEPARATOR) * (count - 1)
        avail = max(self.width() - 12 - gaps, 40 * count)
        natural = [metrics.horizontalAdvance(p) for p in self._paths]
        even = avail // count
        if sum(natural) <= avail:
            shares = natural
        else:
            spare = sum(even - w for w in natural if w < even)
            longer = sum(1 for w in natural if w >= even)
            shares = [w if w < even else even + spare // longer for w in natural]
        self.setText(
            self.SEPARATOR.join(
                metrics.elidedText(p, Qt.TextElideMode.ElideMiddle, share)
                for p, share in zip(self._paths, shares)
            )
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.resize(1200, 760)
        self.setAcceptDrops(True)

        self.viewer = ViewerTab()
        self.compare = CompareTab()
        self.warnings = WarningsTab()
        self.warnings.activated.connect(self._goto_warning_part)
        self.search = SearchTab()
        self.search.activated.connect(self._goto_match)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.viewer, "Viewer / Editor")
        self.tabs.addTab(self.compare, "Compare")
        self.tabs.addTab(self.search, "Search")
        self.setCentralWidget(self.tabs)
        self.viewer.message.connect(self.statusBar().showMessage)
        self.compare.message.connect(self.statusBar().showMessage)
        self._active_packages = []
        self.path_label = PathLabel()
        self.statusBar().addPermanentWidget(self.path_label)
        self.compare.swapped.connect(self._compare_swapped)

        def action(text, slot, shortcut=None):
            act = QAction(text, self)
            act.triggered.connect(slot)
            if shortcut:
                act.setShortcut(QKeySequence(shortcut))
            return act

        self.save_part_action = action("&Save Part", self.viewer.save_part, "Ctrl+S")
        self.save_package_action = action(
            "Save Package &As...", self.save_package_as, "Ctrl+Shift+S"
        )
        self.extract_action = action("&Extract Part...", self.viewer.extract_part)
        self.report_action = action(
            "Export Compare &Report (PDF)...", self.compare.export_report
        )
        self.close_action = action("&Close File(s)", self.close_files, "Ctrl+W")

        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(action("&Open...", self.open_dialog, "Ctrl+O"))
        file_menu.addAction(
            action("&Compare Documents...", self.compare_dialog, "Ctrl+D")
        )
        file_menu.addSeparator()
        file_menu.addAction(self.save_part_action)
        file_menu.addAction(self.save_package_action)
        file_menu.addAction(self.extract_action)
        file_menu.addAction(self.report_action)
        file_menu.addSeparator()
        file_menu.addAction(self.close_action)
        file_menu.addSeparator()
        file_menu.addAction(action("&Quit", self.close, "Ctrl+Q"))
        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(action("&Find in Document(s)...", self.find, "Ctrl+F"))
        theme_menu = self.menuBar().addMenu("&View").addMenu("&Theme")
        self.theme_actions = QActionGroup(self)
        for name in (themes.CLASSIC_NAME, *themes.availableThemes()):
            act = QAction(name, self, checkable=True)
            act.setChecked(name == themes.currentThemeName())
            act.triggered.connect(lambda _, n=name: self.set_theme(n))
            self.theme_actions.addAction(act)
            theme_menu.addAction(act)
            if name == themes.CLASSIC_NAME:
                theme_menu.addSeparator()
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(action("&About", self.about))

        self.viewer.changed.connect(self._update_title)
        self.viewer.changed.connect(self._update_actions)
        self._update_actions()
        self.statusBar().showMessage("Open a document, or drop one onto the window.")

    def set_theme(self, name):
        applied = themes.applyTheme(name)
        themes.saveThemeName(applied)
        for act in self.theme_actions.actions():
            act.setChecked(act.text() == applied)
        self.refresh_theme()

    def refresh_theme(self):
        self.viewer.editor.refresh_theme()
        self.viewer.image_view.meta.refresh_theme()
        self.compare.refresh_theme()

    def _update_actions(self):
        loaded = self.viewer.pkg is not None
        self.save_part_action.setEnabled(loaded)
        self.save_package_action.setEnabled(loaded)
        self.extract_action.setEnabled(loaded and self.viewer._part is not None)
        self.report_action.setEnabled(self.compare.left_pkg is not None)
        self.close_action.setEnabled(loaded or self.compare.left_pkg is not None)

    def close_files(self):
        if not self.viewer.can_discard():
            return False
        self.compare.clear()
        self.viewer.unload()
        self._active_packages = []
        self._refresh_views()
        self.tabs.setCurrentWidget(self.viewer)
        self._update_actions()
        self.statusBar().showMessage("Open a document, or drop one onto the window.")
        return True

    def _update_title(self):
        pkg = self.viewer.pkg
        star = " *" if self.viewer.is_dirty() else ""
        title = f"{APP_NAME} v{VERSION}"
        self.setWindowTitle(f"{pkg.name}{star} - {title}" if pkg else title)

    def _compare_swapped(self):
        self._active_packages = [self.compare.left_pkg, self.compare.right_pkg]
        self._refresh_views()

    def _refresh_views(self):
        self.path_label.set_paths([pkg.path for pkg in self._active_packages])
        self.search.set_documents(self._active_packages)
        self._refresh_warnings()

    def find(self):
        current = self.tabs.currentWidget()
        panes = [QApplication.focusWidget()]
        if current is self.viewer:
            panes.append(self.viewer.editor)
        elif current is self.compare:
            panes += [self.compare.diff.left, self.compare.diff.right]
        selected = next(
            (
                p.textCursor().selectedText()
                for p in panes
                if isinstance(p, QPlainTextEdit) and p.textCursor().hasSelection()
            ),
            "",
        )
        self.tabs.setCurrentWidget(self.search)
        self.search.focus_query(selected if selected and len(selected) < 200 else None)

    def _goto_match(self, pkg, part, line, col, length):
        if pkg is self.viewer.pkg:
            self.tabs.setCurrentWidget(self.viewer)
            if self.viewer._editor_dirty():
                self.statusBar().showMessage(
                    "This part has unsaved edits, so the match may not line up exactly."
                )
            self.viewer.show_match(part, line, col, length)
        elif pkg in (self.compare.left_pkg, self.compare.right_pkg):
            self.tabs.setCurrentWidget(self.compare)
            self.compare.show_match(pkg, part, line, col, length)
        else:
            self.statusBar().showMessage("That document is no longer open.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "path_label"):
            self.path_label.setMaximumWidth(max(self.width() // 2, 200))

    def _refresh_warnings(self):
        rows, seen = [], set()
        for pkg in self._active_packages:
            for part, text in pkg.warnings:
                if (pkg.path, part, text) not in seen:
                    seen.add((pkg.path, part, text))
                    rows.append((pkg, part, text))
        index = self.tabs.indexOf(self.warnings)
        if not rows:
            if index != -1:
                self.tabs.removeTab(index)
            return
        self.warnings.set_rows(rows)
        title = (
            f"Warning ({len(rows)})" if len(rows) == 1 else f"Warnings ({len(rows)})"
        )
        if index == -1:
            self.tabs.addTab(self.warnings, title)
        else:
            self.tabs.setTabText(index, title)

    def _goto_warning_part(self, pkg, part):
        item = self.viewer._item_for(part) if pkg is self.viewer.pkg else None
        if item:
            self.tabs.setCurrentWidget(self.viewer)
            self.viewer.tree.setCurrentItem(item)

    def save_package_as(self):
        saved = self.viewer.save_package_as()
        self._refresh_views()
        return saved

    def _load_package(self, path):
        path = os.path.normpath(path)
        try:
            return OOXMLPackage(path)
        except (zipfile.BadZipFile, OSError) as e:
            if is_ole_file(path):
                reason = "This is an OLE compound file, not a zip package."
            else:
                reason = f"This does not look like an OOXML (zip) file.\n{e}"
            QMessageBox.critical(self, "Error opening file", f"{path}\n\n{reason}")
            return None

    def open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open document", "", OPEN_FILTER)
        if path:
            self.open_document(path)

    def open_document(self, path):
        if not self.viewer.can_discard():
            return
        pkg = self._load_package(path)
        if pkg:
            self.compare.clear()
            self.viewer.load(pkg)
            self.tabs.setCurrentWidget(self.viewer)
            self.statusBar().showMessage(
                "; ".join([f"{len(pkg.data)} parts", *pkg.notes])
            )
            self._active_packages = [pkg]
            self._refresh_views()
            self._update_actions()

    def compare_dialog(self):
        start = os.path.dirname(self.viewer.pkg.path) if self.viewer.pkg else ""
        # the native dialog can't limit the selection, so check it afterwards
        while True:
            chosen, _ = QFileDialog.getOpenFileNames(
                self, "Choose one or two documents to compare", start, OPEN_FILTER
            )
            files = [os.path.normpath(f) for f in chosen]
            if len(files) <= 2:
                break
            QMessageBox.warning(
                self,
                "Too many documents",
                f"{len(files)} documents were selected. Please select no more than two.",
            )
            start = os.path.dirname(files[0])
        if len(files) == 1:
            second, _ = QFileDialog.getOpenFileName(
                self,
                f"Compare {os.path.basename(files[0])} with...",
                os.path.dirname(files[0]),
                OPEN_FILTER,
            )
            if second:
                files.append(os.path.normpath(second))
        if len(files) == 2:
            self.compare_documents(files[0], files[1])

    def compare_documents(self, left, right):
        a, b = self._load_package(left), self._load_package(right)
        if a and b:
            self.compare.clear()
            self.compare.set_packages(a, b)
            self.tabs.setCurrentWidget(self.compare)
            self._active_packages = [a, b]
            self._refresh_views()
            self._update_actions()

    def about(self):
        QMessageBox.about(
            self,
            f"{APP_NAME} v{VERSION}",
            f"<b>{APP_NAME} v{VERSION}</b><br>View, edit and compare OOXML packages.<br><br>"
            "A Python 3 port of the OOXML Tools browser extension by Atul Moglewar.<br>"
            "Created by Corey Forman (digitalsleuth).<br><br>"
            f'<a href="{GITHUB}">View the source on GitHub</a>',
        )

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if len(paths) == 1:
            self.open_document(paths[0])
        elif len(paths) >= 2:
            self.compare_documents(paths[0], paths[1])

    def closeEvent(self, event):
        if self.viewer.can_discard():
            event.accept()
        else:
            event.ignore()


def main(argv=None):
    argv = sys.argv if argv is None else argv
    app = QApplication(argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(f"{APP_NAME} v{VERSION}")
    icon = QPixmap()
    icon.loadFromData(base64.b64decode(__fingerprint__))
    app.setWindowIcon(QIcon(icon))
    themes.applyTheme(themes.savedThemeName())
    win = MainWindow()
    win.show()
    paths = [a for a in argv[1:] if os.path.isfile(a)]
    if len(paths) == 1:
        win.open_document(paths[0])
    elif len(paths) >= 2:
        win.compare_documents(paths[0], paths[1])
    return app.exec()
