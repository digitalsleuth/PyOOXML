#!/usr/bin/env python3
"""
A Python3 port of the "OOXML Tools" browser extension by Atul Moglewar.
"""

import codecs
import datetime
import difflib
import hashlib
import html
import os
import re
import struct
import sys
import zipfile
import zlib
import base64
from xml.dom import minidom
from xml.parsers import expat

from PyQt6.QtCore import (
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
    QDialogButtonBox,
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
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "PyOOXML"
VERSION = "1.0.0"
GITHUB = "https://github.com/digitalsleuth/PyOOXML"
XML_EXTS = (".xml", ".rels", ".vml")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
OPEN_FILTER = (
    "OOXML documents (*.docx *.docm *.dotx *.dotm *.xlsx *.xlsm *.xltx *.xltm "
    "*.pptx *.pptm *.potx *.potm *.ppsx *.ppsm *.vsdx *.zip);;All files (*)"
)
PATH_ROLE = Qt.ItemDataRole.UserRole
_DECL_RE = re.compile(r"^\s*(<\?xml[^>]*\?>)")
_ENCODING_RE = re.compile(r"(?i)^(\s*<\?xml[^>]*?encoding\s*=\s*[\"'])[^\"']*")
REPORT_CONTEXT = 2
REPORT_MAX_ROWS = 2000
REPORT_ONE_SIDED_ROWS = 40
REPORT_DPI = 150
REPORT_BG = {"del": "#fbd0d0", "add": "#cdeed6", "chg": "#fff0b8", "pad": "#e8e8e8"}
REPORT_MARK = {"l": "#f08a8a", "r": "#6fcf8a"}
REPORT_STATUS = {
    "diff": ("Different", "#ffe08a"),
    "left": ("Only in left", "#f6b8b8"),
    "right": ("Only in right", "#b9e4c3"),
}
_TOKEN_RE = re.compile(r"\w+|\s+|[^\w\s]")
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


def is_xml_part(name):
    return name.lower().endswith(XML_EXTS)


def is_image_part(name):
    return name.lower().endswith(IMAGE_EXTS)


def human_size(size):
    value = float(size)
    for unit in ("bytes", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{int(value)} {unit}" if unit == "bytes" else f"{value:.1f} {unit}"
        value /= 1024


def normalize_name(name):
    return name.replace("\\", "/")


def inflate(method, compressed):
    if method == zipfile.ZIP_STORED:
        return compressed
    if method == zipfile.ZIP_DEFLATED:
        decoder = zlib.decompressobj(-15)
        raw = decoder.decompress(compressed)
        return raw if decoder.eof else None
    return None


def integrity_problem(raw, size, crc):
    problems = []
    computed = zlib.crc32(raw)
    if computed != crc:
        problems.append(f"CRC32 recorded 0x{crc:08X}, computed 0x{computed:08X}")
    if len(raw) != size:
        problems.append(f"size recorded {size}, decoded {len(raw)}")
    return "; ".join(problems) or None


def is_ole_file(path):
    try:
        with open(path, "rb") as fh:
            return fh.read(8) == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    except OSError:
        return False


def usable_xml(name, raw):
    return not is_xml_part(name) or validate_xml(decode_xml(raw)[0]) is None


class OOXMLPackage:

    def __init__(self, path):
        self.path = os.path.normpath(path)
        self.infos = []
        self.data = {}
        self.modified = set()
        self.recovered = {}
        self.skipped = {}
        self.salvaged = False
        self._header_index = None
        try:
            with zipfile.ZipFile(self.path) as zfile:
                self._read_directory(zfile)
        except zipfile.BadZipFile:
            self._salvage()
            if not self.data:
                raise

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def notes(self):
        notes = []
        unverified = sum(1 for p in self.recovered.values() if p)
        verified = len(self.recovered) - unverified
        if self.salvaged:
            notes.append(
                f"no usable central directory, {len(self.infos)} part(s) recovered "
                f"from their local file headers"
            )
        if verified:
            notes.append(
                f"{verified} part(s) with damaged zip headers recovered and "
                f"verified against their CRC32/size"
            )
        if unverified:
            notes.append(f"{unverified} part(s) recovered but UNVERIFIED")
        if self.skipped:
            notes.append(
                f"{len(self.skipped)} part(s) could not be read and will be "
                f"left out if the package is saved"
            )
        return notes

    @property
    def warnings(self):
        found = []
        if self.salvaged:
            found.append(
                (
                    "",
                    f"No usable central directory: {len(self.infos)} part(s) were "
                    f"recovered from their local file headers.",
                )
            )
        for part, problem in self.recovered.items():
            if problem:
                found.append(
                    (
                        part,
                        f"UNVERIFIED: failed its integrity check ({problem}). The "
                        f"content decoded completely but may be inaccurate.",
                    )
                )
            else:
                found.append(
                    (
                        part,
                        "Its zip headers were damaged. Recovered from the raw file "
                        "and verified against its CRC32/size.",
                    )
                )
        for part, reason in self.skipped.items():
            found.append(
                (
                    part,
                    f"Could not be read ({reason}). It is left out if the package is saved.",
                )
            )
        return found

    def _read_directory(self, zfile):
        seen = set()
        for info in zfile.infolist():
            name = normalize_name(info.filename)
            if name in seen:
                continue
            seen.add(name)
            raw = None
            if not name.endswith("/"):
                try:
                    raw = zfile.read(info)
                except Exception as e:
                    raw, problem = self._recover_member(info, name)
                    if raw is None:
                        self.skipped[name] = f"{e} (raw recovery failed: {problem})"
                        continue
                    self.recovered[name] = problem
            info.filename = name
            self.infos.append(info)
            if raw is not None:
                self.data[name] = raw

    def _offsets(self, info, name):
        yield info.header_offset
        for offset in self._index().get(name, []):
            if offset != info.header_offset:
                yield offset

    def _index(self):
        if self._header_index is None:
            self._header_index = {}
            with open(self.path, "rb") as fh:
                blob = fh.read()
            pos = 0
            while True:
                pos = blob.find(b"PK\x03\x04", pos)
                if pos == -1 or pos + 30 > len(blob):
                    break
                (namelen,) = struct.unpack("<H", blob[pos + 26 : pos + 28])
                end = pos + 30 + namelen
                try:
                    local = blob[pos + 30 : end].decode("utf-8")
                except UnicodeDecodeError:
                    local = None
                if local is not None and end <= len(blob):
                    self._header_index.setdefault(normalize_name(local), []).append(pos)
                pos += 4
        return self._header_index

    def _recover_member(self, info, name):
        reason = "no local file header was found"
        unverified = None
        with open(self.path, "rb") as fh:
            for offset in self._offsets(info, name):
                if offset < 0:
                    continue
                fh.seek(offset)
                head = fh.read(30)
                if len(head) < 30 or head[:4] != b"PK\x03\x04":
                    continue
                namelen, extralen = struct.unpack("<HH", head[26:30])
                fh.seek(offset + 30 + namelen + extralen)
                compressed = fh.read(info.compress_size)
                if len(compressed) != info.compress_size:
                    reason = f"its data at offset {offset} is truncated"
                    continue
                try:
                    raw = inflate(info.compress_type, compressed)
                except zlib.error as e:
                    reason = f"its data at offset {offset} does not decompress ({e})"
                    continue
                if raw is None:
                    reason = (
                        f"its data at offset {offset} is an incomplete stream "
                        f"or uses an unsupported compression method"
                    )
                    continue
                problem = integrity_problem(raw, info.file_size, info.CRC)
                if problem is None:
                    return raw, None
                if unverified is None and usable_xml(name, raw):
                    unverified = (raw, problem)
        return unverified or (None, reason)

    def _salvage(self):
        with open(self.path, "rb") as fh:
            blob = fh.read()
        pos = 0
        while pos + 30 <= len(blob) and blob[pos : pos + 4] == b"PK\x03\x04":
            version, flags, method, mtime, mdate, crc, csize, usize, nlen, elen = (
                struct.unpack("<HHHHHIIIHH", blob[pos + 4 : pos + 30])
            )
            if (flags & 0x08 and not csize) or csize == 0xFFFFFFFF:
                break
            name = normalize_name(
                blob[pos + 30 : pos + 30 + nlen].decode(
                    "utf-8" if flags & 0x800 else "cp437", "replace"
                )
            )
            start = pos + 30 + nlen + elen
            compressed = blob[start : start + csize]
            raw = None
            if len(compressed) == csize:
                try:
                    raw = inflate(method, compressed)
                except zlib.error:
                    pass
            problem = integrity_problem(raw, usize, crc) if raw is not None else None
            if raw is not None and problem and not usable_xml(name, raw):
                raw = None
            if raw is None:
                self.skipped[name] = "truncated or damaged data"
            elif name not in self.data and not name.endswith("/"):
                info = zipfile.ZipInfo(name)
                info.date_time = (
                    (mdate >> 9) + 1980,
                    (mdate >> 5) & 0xF,
                    mdate & 0x1F,
                    mtime >> 11,
                    (mtime >> 5) & 0x3F,
                    (mtime & 0x1F) * 2,
                )
                info.compress_type = method
                info.CRC, info.compress_size, info.file_size = crc, csize, usize
                self.infos.append(info)
                self.data[name] = raw
                if problem:
                    self.recovered[name] = problem
            if start + csize > len(blob):
                break
            pos = start + csize
        self.salvaged = bool(self.data)

    def set_data(self, part, data):
        self.data[part] = data
        self.modified.add(part)

    def save(self, dest):
        tmp = dest + ".tmp"
        with zipfile.ZipFile(tmp, "w") as zfile:
            for info in self.infos:
                zinfo = zipfile.ZipInfo(info.filename, info.date_time)
                zinfo.compress_type = info.compress_type
                zinfo.external_attr = info.external_attr
                zinfo.create_system = info.create_system
                zinfo.comment = info.comment
                zfile.writestr(
                    zinfo, b"" if info.is_dir() else self.data[info.filename]
                )
        os.replace(tmp, dest)
        self.path = dest
        self.modified.clear()


def decode_xml(raw):
    if raw.startswith(codecs.BOM_UTF8):
        return raw.decode("utf-8-sig", "replace"), "utf-8-sig"
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return raw.decode("utf-16", "replace"), "utf-16"
    m = re.match(rb"\s*<\?xml[^>]*?encoding\s*=\s*[\"']([\w.-]+)[\"']", raw)
    enc = m.group(1).decode("ascii") if m else "utf-8"
    try:
        return raw.decode(enc), enc
    except (LookupError, UnicodeDecodeError):
        return raw.decode("utf-8", "replace"), "utf-8"


def encode_xml(text, enc):
    try:
        return text.encode(enc)
    except (LookupError, UnicodeEncodeError):
        return text.encode("utf-8")


def _as_utf8_declared(text):
    return _ENCODING_RE.sub(r"\1utf-8", text, count=1)


def pretty_xml(text):
    try:
        dom = minidom.parseString(_as_utf8_declared(text).encode("utf-8"))
    except Exception:
        return text, False
    chunks = []
    m = _DECL_RE.match(text)
    if m:
        chunks.append(m.group(1))
    chunks.extend(node.toprettyxml(indent="  ") for node in dom.childNodes)
    lines = "\n".join(chunks).splitlines()
    return "\n".join(line for line in lines if line.strip()), True


def compact_xml(text):
    lines = text.splitlines()
    if not lines:
        return text
    out = lines[0]
    if _DECL_RE.match(out):
        out += "\n"
    for line in lines[1:]:
        line = line.strip()
        out += line if out.endswith((">", "\n")) else " " + line
    return out


def validate_xml(text):
    parser = expat.ParserCreate(namespace_separator=" ")
    try:
        parser.Parse(_as_utf8_declared(text).encode("utf-8"), True)
    except expat.ExpatError as e:
        return e.lineno, e.offset + 1, expat.ErrorString(e.code)
    return None


def hex_dump(data, limit=4096):
    rows = []
    for off in range(0, min(len(data), limit), 16):
        chunk = data[off : off + 16]
        hexpart = " ".join(f"{b:02x}" for b in chunk).ljust(47)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        rows.append(f"{off:08x}  {hexpart}  {text}")
    if len(data) > limit:
        rows.append(f"... {len(data) - limit} more bytes")
    return "\n".join(rows)


def part_text(raw):
    if raw is None:
        return ""
    return pretty_xml(decode_xml(raw)[0])[0]


def build_diff(left, right):
    a = part_text(left).splitlines()
    b = part_text(right).splitlines()
    res = {
        "ltext": [],
        "rtext": [],
        "llabel": [],
        "rlabel": [],
        "lkind": [],
        "rkind": [],
        "starts": [],
        "added": 0,
        "removed": 0,
        "changed": 0,
    }

    def put(side, text, label, kind):
        res[side + "text"].append(text)
        res[side + "label"].append(label)
        res[side + "kind"].append(kind)

    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag != "equal":
            res["starts"].append(len(res["ltext"]))
        if tag == "equal":
            for i, j in zip(range(i1, i2), range(j1, j2)):
                put("l", a[i], str(i + 1), "equal")
                put("r", b[j], str(j + 1), "equal")
            continue
        n = max(i2 - i1, j2 - j1)
        for k in range(n):
            i, j = i1 + k, j1 + k
            has_l, has_r = i < i2, j < j2
            kind_l = ("chg" if has_r else "del") if has_l else "pad"
            kind_r = ("chg" if has_l else "add") if has_r else "pad"
            put("l", a[i] if has_l else "", str(i + 1) if has_l else "", kind_l)
            put("r", b[j] if has_r else "", str(j + 1) if has_r else "", kind_r)
        if tag == "delete":
            res["removed"] += i2 - i1
        elif tag == "insert":
            res["added"] += j2 - j1
        else:
            res["changed"] += n
    return res


def is_dark_theme():
    return QApplication.palette().color(QPalette.ColorRole.Window).lightness() < 128


class XmlHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        dark = is_dark_theme()

        def fmt(color, bold=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.Weight.Bold)
            return f

        tag = fmt("#569cd6" if dark else "#1c4fa0")
        attr = fmt("#9cdcfe" if dark else "#7a3e9d")
        string = fmt("#ce9178" if dark else "#a31515")
        entity = fmt("#d7ba7d" if dark else "#a05a00")
        comment = fmt("#6a9955" if dark else "#2e7d32")
        self._rules = [
            (re.compile(r"</?[\w:.-]+|/?>"), tag),
            (re.compile(r"[\w:.-]+(?=\s*=)"), attr),
            (re.compile(r"&[\w#]+;"), entity),
            (re.compile(r"\"[^\"]*\"|'[^']*'"), string),
            (re.compile(r"<!--.*?-->|<\?.*?\?>"), comment),
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
        painter.setPen(self.palette().color(QPalette.ColorRole.PlaceholderText))
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


def tint(r, g, b, a=70):
    return QColor(r, g, b, a)


KIND_COLORS = {
    "del": tint(220, 60, 60),
    "add": tint(50, 170, 80),
    "chg": tint(225, 170, 30, 80),
    "pad": tint(128, 128, 128, 35),
}
STATUS = {
    "same": ("Identical", tint(50, 170, 80, 45)),
    "diff": ("Different", tint(220, 60, 60, 55)),
    "left": ("Only in left", tint(60, 120, 220, 55)),
    "right": ("Only in right", tint(60, 120, 220, 55)),
}


class DiffView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._starts = []
        self._cursor = -1

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

    def show_message(self, text, left_title="", right_title=""):
        self._starts, self._cursor = [], -1
        self.left_title.setText(left_title)
        self.right_title.setText(right_title)
        for editor in (self.left, self.right):
            editor.set_line_labels(None)
            editor.setPlainText("")
        self.summary.setText(text)

    def show_result(self, res, left_title, right_title):
        self._starts, self._cursor = res["starts"], -1
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
                bf.setBackground(QBrush(KIND_COLORS[kind]))
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
        self.image = QLabel()
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll = QScrollArea()
        scroll.setWidget(self.image)
        scroll.setWidgetResizable(True)
        self.info = QPlainTextEdit()
        self.info.setReadOnly(True)
        self.info.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.stack = QStackedWidget()
        for page in (self.empty, self.editor, scroll, self.info):
            self.stack.addWidget(page)

        right = QWidget()
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(0, 0, 0, 0)
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
        self.image.clear()
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
        elif is_image_part(part) and self._show_image(raw):
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

    def _show_image(self, raw):
        pixmap = QPixmap()
        if not pixmap.loadFromData(raw):
            return False
        self.image.setPixmap(pixmap)
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
                f"&nbsp;<a href='goto'>Go to error</a>"
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


def _esc(text, lead=True):
    text = html.escape(text, quote=False)
    if lead:
        text = re.sub(r"^ +", lambda m: "&nbsp;" * len(m.group()), text)
    return re.sub(r" {2,}", lambda m: "&nbsp;" * len(m.group()), text)


def _changed_ranges(a, b):
    ta, tb = _TOKEN_RE.findall(a), _TOKEN_RE.findall(b)
    offs = []
    for tokens in (ta, tb):
        pos = [0]
        for t in tokens:
            pos.append(pos[-1] + len(t))
        offs.append(pos)
    ra, rb = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
        None, ta, tb, autojunk=False
    ).get_opcodes():
        if tag == "equal":
            continue
        if i2 > i1:
            ra.append((offs[0][i1], offs[0][i2]))
        if j2 > j1:
            rb.append((offs[1][j1], offs[1][j2]))
    return ra, rb


def _line_html(text, ranges, mark):
    if not text:
        return "&nbsp;"
    out, pos = [], 0
    for start, end in ranges:
        if start > pos:
            out.append(_esc(text[pos:start], pos == 0))
        shown = html.escape(text[start:end], quote=False).replace(" ", "&nbsp;")
        out.append(f'<span style="background-color:{mark}">{shown}</span>')
        pos = end
    if pos < len(text):
        out.append(_esc(text[pos:], pos == 0))
    return "".join(out)


def _diff_row(res, i):
    ranges = {"l": [], "r": []}
    if res["lkind"][i] == "chg" and res["rkind"][i] == "chg":
        ranges["l"], ranges["r"] = _changed_ranges(res["ltext"][i], res["rtext"][i])
    cells = []
    for side in ("l", "r"):
        kind = res[side + "kind"][i]
        bg = REPORT_BG.get(kind, "#ffffff")
        num_bg = REPORT_BG.get(kind, "#f2f2f2")
        body = _line_html(res[side + "text"][i], ranges[side], REPORT_MARK[side])
        cells.append(
            f'<td width="3%" align="right" bgcolor="{num_bg}" style="color:#666666">'
            f'{res[side + "label"][i] or "&nbsp;"}</td>'
            f'<td width="46%" bgcolor="{bg}">{body}</td>'
        )
    return f'<tr>{cells[0]}<td width="2%">&nbsp;</td>{cells[1]}</tr>'


def _diff_table(name, status, res, left_name, right_name, limit):
    label, color = REPORT_STATUS[status]
    kinds = [
        "equal" if res["lkind"][i] == res["rkind"][i] == "equal" else "x"
        for i in range(len(res["lkind"]))
    ]
    keep = [False] * len(kinds)
    for i, k in enumerate(kinds):
        if k != "equal":
            for j in range(
                max(i - REPORT_CONTEXT, 0), min(i + REPORT_CONTEXT + 1, len(kinds))
            ):
                keep[j] = True
    if status != "diff":
        keep = [True] * len(kinds)
    blocks = len(res["starts"])
    head = f"{label}"
    if status == "diff":
        head += (
            f" - {blocks} difference block{'s' if blocks != 1 else ''}: "
            f"{res['added']} added, {res['removed']} removed, {res['changed']} changed"
        )
    out = [
        '<table width="100%" border="0" cellspacing="0" cellpadding="3"><thead>'
        f'<tr><th colspan="5" align="left" bgcolor="{color}" style="font-size:10pt">'
        f"{html.escape(name)} &nbsp;&nbsp; <span style='font-weight:normal'>"
        f"{html.escape(head)}</span></th></tr>"
        '<tr><th colspan="2" align="left" bgcolor="#d9d9d9">'
        f"{html.escape(left_name)}</th><th bgcolor=\"#d9d9d9\"></th>"
        '<th colspan="2" align="left" bgcolor="#d9d9d9">'
        f"{html.escape(right_name)}</th></tr></thead>"
    ]
    shown = gap = 0
    truncated_at = None
    for i, k in enumerate(kinds):
        if not keep[i]:
            gap += 1
            continue
        if gap:
            out.append(
                '<tr><td colspan="5" align="center" bgcolor="#f4f4f4" '
                f'style="color:#777777"><i>... {gap} unchanged line'
                f"{'s' if gap != 1 else ''} ...</i></td></tr>"
            )
            gap = 0
        if shown >= limit:
            truncated_at = i
            break
        out.append(_diff_row(res, i))
        shown += 1
    if truncated_at is not None:
        hidden = sum(1 for s in res["starts"] if s >= truncated_at)
        left_rows = len(kinds) - truncated_at
        out.append(
            '<tr><td colspan="5" align="center" bgcolor="#f4f4f4"><b>Output cut off '
            f"here: {left_rows} more rows ({hidden} difference block"
            f"{'s' if hidden != 1 else ''}) are not shown.</b></td></tr>"
        )
    elif gap:
        out.append(
            '<tr><td colspan="5" align="center" bgcolor="#f4f4f4" '
            f'style="color:#777777"><i>... {gap} unchanged line'
            f"{'s' if gap != 1 else ''} ...</i></td></tr>"
        )
    out.append("</table><p></p>")
    return "".join(out)


def _file_facts(pkg):
    size = digest = "unavailable"
    try:
        h = hashlib.sha256()
        with open(pkg.path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        digest, size = h.hexdigest(), human_size(os.path.getsize(pkg.path))
    except OSError:
        pass
    return size, digest


def report_part_diffs(rows, step=None):
    todo = [r for r in rows if r[3] != "same"]
    diffs = {}
    for i, (name, a, b, status) in enumerate(todo):
        if step and step(i, len(todo), name):
            return None
        diffs[name] = build_diff(a, b) if is_xml_part(name) else None
    return diffs


def build_report_html(left, right, rows, diffs, mono):
    counts = {k: 0 for k in STATUS}
    for r in rows:
        counts[r[3]] += 1
    facts = [_file_facts(left), _file_facts(right)]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    th = 'bgcolor="#d9d9d9" align="left"'
    out = [
        f'<body style="color:#000000"><h1 style="font-size:20pt">{APP_NAME} comparison report</h1>'
        f"<p>Generated {now} by {APP_NAME} v{VERSION}</p>"
        '<table width="100%" border="0" cellspacing="0" cellpadding="4">'
        f'<tr><td {th} width="12%"></td><th {th} width="44%">Left</th><th {th} width="44%">Right</th></tr>'
        f"<tr><td><b>File</b></td><td>{html.escape(left.name)}</td><td>{html.escape(right.name)}</td></tr>"
        f"<tr><td><b>Path</b></td><td>{html.escape(left.path)}</td><td>{html.escape(right.path)}</td></tr>"
        f"<tr><td><b>Size</b></td><td>{facts[0][0]}</td><td>{facts[1][0]}</td></tr>"
        f"<tr><td><b>SHA-256</b></td><td style=\"font-family:'{mono}'; font-size:7pt\">{facts[0][1]}</td>"
        f"<td style=\"font-family:'{mono}'; font-size:7pt\">{facts[1][1]}</td></tr></table>"
        f"<p>{len(rows)} parts compared: {counts['same']} identical, {counts['diff']} different, "
        f"{counts['left']} only in left, {counts['right']} only in right.</p>"
        '<table border="0" cellspacing="6" cellpadding="3"><tr><td><b>Key</b></td>'
        f'<td bgcolor="{REPORT_BG["del"]}">&nbsp;Removed (left only)&nbsp;</td>'
        f'<td bgcolor="{REPORT_BG["add"]}">&nbsp;Added (right only)&nbsp;</td>'
        f'<td bgcolor="{REPORT_BG["chg"]}">&nbsp;Changed line&nbsp;</td>'
        f'<td bgcolor="{REPORT_MARK["l"]}">&nbsp;Changed text, left&nbsp;</td>'
        f'<td bgcolor="{REPORT_MARK["r"]}">&nbsp;Changed text, right&nbsp;</td>'
        f'<td bgcolor="{REPORT_BG["pad"]}">&nbsp;No counterpart&nbsp;</td></tr></table>'
    ]
    notes = [
        (pkg.name, part, text)
        for pkg in (left, right)
        for part, text in pkg.warnings
    ]
    if notes:
        out.append("<h3>Warnings while opening the documents</h3><ul>")
        for name, part, text in notes:
            where = f" ({html.escape(part)})" if part else ""
            out.append(f"<li><b>{html.escape(name)}</b>{where}: {html.escape(text)}</li>")
        out.append("</ul>")

    differing = [r for r in rows if r[3] != "same"]
    if not differing:
        out.append(
            "<h2>No differences found. Every part is byte-for-byte identical.</h2>"
        )
        return "".join(out) + "</body>"

    out.append(
        "<h2>Parts that differ</h2>"
        '<table width="100%" border="0" cellspacing="0" cellpadding="3"><thead><tr>'
        f"<th {th} width='14%'>Status</th><th {th}>Part</th><th {th} width='9%'>Left</th>"
        f"<th {th} width='9%'>Right</th><th {th} width='34%'>Detail</th></tr></thead>"
    )
    for name, a, b, status in differing:
        res = diffs[name]
        label, color = REPORT_STATUS[status]
        if res is None:
            detail = "Not an XML part"
            if status == "diff":
                digests = [hashlib.sha256(x).hexdigest()[:12] for x in (a, b)]
                detail += f", contents differ (sha256 {digests[0]} vs {digests[1]})"
        elif status == "diff" and not res["starts"]:
            detail = "Bytes differ; formatted text is identical (whitespace or encoding)"
        elif status == "diff":
            detail = (
                f"{len(res['starts'])} block(s): {res['added']} added, "
                f"{res['removed']} removed, {res['changed']} changed"
            )
        else:
            detail = "Whole part is present on one side only"
        out.append(
            f'<tr><td bgcolor="{color}">{label}</td><td>{html.escape(name)}</td>'
            f"<td>{human_size(len(a)) if a is not None else '-'}</td>"
            f"<td>{human_size(len(b)) if b is not None else '-'}</td>"
            f"<td>{html.escape(detail)}</td></tr>"
        )
    out.append("</table>")

    shown = [
        r for r in differing
        if diffs[r[0]] is not None and (diffs[r[0]]["starts"] or r[3] != "diff")
    ]
    if shown:
        out.append(
            '<h2 style="page-break-before:always">Differences</h2>'
            f"<p>Only changed lines are shown, with {REPORT_CONTEXT} lines of context. "
            "Line numbers are those of the formatted (pretty-printed) XML.</p>"
            f"<div style=\"font-family:'{mono}'; font-size:7pt\">"
        )
        for name, a, b, status in shown:
            limit = REPORT_ONE_SIDED_ROWS if status != "diff" else REPORT_MAX_ROWS
            out.append(
                _diff_table(
                    name,
                    status,
                    diffs[name],
                    f"{left.name}" if a is not None else "(missing)",
                    f"{right.name}" if b is not None else "(missing)",
                    limit,
                )
            )
        out.append("</div>")
    return "".join(out) + "</body>"


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

    def _rebuild(self, *_):
        if not self.left_pkg:
            return
        self.header.setText(
            f"<b>{self.left_pkg.name}</b> &nbsp;vs&nbsp; <b>{self.right_pkg.name}</b>"
        )
        counts = {k: 0 for k in STATUS}
        self.tree.clear()
        for name, a, b, status in self._rows:
            counts[status] += 1
            if self.only_diffs.isChecked() and status == "same":
                continue
            label, color = STATUS[status]
            item = QTreeWidgetItem(
                [
                    label,
                    name,
                    human_size(len(a)) if a is not None else "-",
                    human_size(len(b)) if b is not None else "-",
                ]
            )
            item.setData(0, PATH_ROLE, name)
            for col in range(4):
                item.setBackground(col, QBrush(color))
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

    def _on_current_changed(self, cur, _prev):
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
            lambda tok, res, t=(left_title, right_title): self._diff_ready(tok, res, *t)
        )
        worker.finished.connect(lambda w=worker: self._workers.discard(w))
        self._workers.add(worker)
        worker.start()

    def _diff_ready(self, token, result, left_title, right_title):
        if token != self._token:
            return
        if isinstance(result, Exception):
            self.diff.show_message(
                f"Could not compute the diff: {result}", left_title, right_title
            )
        else:
            self.diff.show_result(result, left_title, right_title)


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


class CompareFileDialog(QFileDialog):

    def __init__(self, parent, title, directory, limit):
        super().__init__(parent, title, directory, OPEN_FILTER)
        self.limit = limit
        self.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        self.setFileMode(
            QFileDialog.FileMode.ExistingFiles
            if limit > 1
            else QFileDialog.FileMode.ExistingFile
        )
        self._hint_text = (
            "Select one or two documents (Ctrl or Shift to select two)."
            if limit > 1
            else "Select one document."
        )
        self.hint = QLabel(self._hint_text)
        grid = self.layout()
        grid.addWidget(self.hint, grid.rowCount(), 0, 1, grid.columnCount())
        for name in ("listView", "treeView"):
            view = self.findChild(QAbstractItemView, name)
            if view is not None:
                view.selectionModel().selectionChanged.connect(self._schedule_check)
        self.findChild(QLineEdit, "fileNameEdit").textChanged.connect(
            self._schedule_check
        )
        self._check()

    def _selected_count(self):
        for name in ("listView", "treeView"):
            view = self.findChild(QAbstractItemView, name)
            if view is not None and view.isVisibleTo(self):
                return len(view.selectionModel().selectedRows())
        return 0

    def _schedule_check(self, *_):
        QTimer.singleShot(0, self._check)

    def _check(self):
        too_many = self._selected_count() > self.limit
        button = self.findChild(QDialogButtonBox).button(
            QDialogButtonBox.StandardButton.Open
        )
        if button is not None and too_many:
            button.setEnabled(False)
        self.hint.setText(
            f"Only {self.limit} document(s) can be compared at once. Deselect the extras."
            if too_many
            else self._hint_text
        )
        self.hint.setStyleSheet("color: #cc0000;" if too_many else "")

    def accept(self):
        if len(self.selectedFiles()) > self.limit:
            QMessageBox.warning(
                self,
                "Too many documents",
                f"Please select no more than {self.limit} document(s).",
            )
            return
        super().accept()


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
        self.tabs = QTabWidget()
        self.tabs.addTab(self.viewer, "Viewer / Editor")
        self.tabs.addTab(self.compare, "Compare")
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
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(action("&About", self.about))

        self.viewer.changed.connect(self._update_title)
        self.viewer.changed.connect(self._update_actions)
        self._update_actions()
        self.statusBar().showMessage("Open a document, or drop one onto the window.")

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
        self._refresh_warnings()

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

    def _pick_documents(self, title, directory, limit):
        dialog = CompareFileDialog(self, title, directory, limit)
        if dialog.exec() != QFileDialog.DialogCode.Accepted:
            return []
        return [os.path.normpath(f) for f in dialog.selectedFiles()]

    def compare_dialog(self):
        start = os.path.dirname(self.viewer.pkg.path) if self.viewer.pkg else ""
        files = self._pick_documents("Choose one or two documents to compare", start, 2)
        if len(files) == 1:
            more = self._pick_documents(
                f"Compare {os.path.basename(files[0])} with...",
                os.path.dirname(files[0]),
                1,
            )
            files += more
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
    win = MainWindow()
    win.show()
    paths = [a for a in argv[1:] if os.path.isfile(a)]
    if len(paths) == 1:
        win.open_document(paths[0])
    elif len(paths) >= 2:
        win.compare_documents(paths[0], paths[1])
    return app.exec()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
