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
import posixpath
import re
import struct
import sys
import zipfile
import zlib
import bisect
import functools
from xml.dom import minidom
from xml.parsers import expat

APP_NAME = "PyOOXML"
VERSION = "1.1.0"
GITHUB = "https://github.com/digitalsleuth/PyOOXML"
XML_EXTS = (".xml", ".rels", ".vml")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
SEARCH_MAX_HITS = 5000
SNIPPET_CONTEXT = 60
_DECL_RE = re.compile(r"^\s*(<\?xml[^>]*\?>)")
_ENCODING_RE = re.compile(r"(?i)^(\s*<\?xml[^>]*?encoding\s*=\s*[\"'])[^\"']*")
REPORT_CONTEXT = 2
REPORT_MAX_ROWS = 2000
REPORT_BG = {"del": "#fbd0d0", "add": "#cdeed6", "chg": "#fff0b8", "pad": "#e8e8e8"}
REPORT_MARK = {"l": "#f08a8a", "r": "#6fcf8a"}
REPORT_STATUS = {
    "diff": ("Different", "#ffe08a"),
    "left": ("Only in left", "#f6b8b8"),
    "right": ("Only in right", "#b9e4c3"),
}
_TOKEN_RE = re.compile(r"\w+|\s+|[^\w\s]")
_TEXT_RE = re.compile(r">([^<>]*)<")
_PARA_END_RE = re.compile(r"</(?:[\w.-]+:)?(?:p|tr|row|si|comment)>")
_BREAK_RE = re.compile(r"<(?:[\w.-]+:)?(?:tab|br|cr)\b")
_XMP_RE = re.compile(
    r"<(?:xmp|xap|photoshop|dc|exif|tiff):(CreatorTool|CreateDate|ModifyDate|MetadataDate"
    r"|DateCreated|creator|rights|title|Make|Model)\b[^>]*>(.*?)</",
    re.S,
)
_XMP_ATTR_RE = re.compile(
    r'(?:xmp|xap|photoshop|dc|exif|tiff):'
    r'(CreatorTool|CreateDate|ModifyDate|MetadataDate|DateCreated|Make|Model)="([^"]*)"'
)
_RELATIONSHIP_RE = re.compile(r"<Relationship\b[^>]*>")
_ATTRIBUTE_RE = re.compile(r'([\w:]+)\s*=\s*"([^"]*)"')
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
IMAGE_FORMATS = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".gif": "GIF",
    ".bmp": "BMP",
}
IMAGE_HEX_LIMIT = 256
PNG_COLOR_TYPES = {
    0: "Grayscale",
    2: "RGB",
    3: "Indexed colour",
    4: "Grayscale with alpha",
    6: "RGB with alpha",
}
JPEG_SOF = {
    0xC0: "Baseline DCT",
    0xC1: "Extended sequential DCT",
    0xC2: "Progressive DCT",
    0xC3: "Lossless",
    0xC5: "Differential sequential DCT",
    0xC6: "Differential progressive DCT",
    0xC7: "Differential lossless",
    0xC9: "Arithmetic sequential DCT",
    0xCA: "Arithmetic progressive DCT",
    0xCB: "Arithmetic lossless",
}
JPEG_COMPONENTS = {1: "Grayscale", 3: "YCbCr / RGB", 4: "CMYK / YCCK"}
BMP_COMPRESSION = {
    0: "None (BI_RGB)",
    1: "RLE 8-bit",
    2: "RLE 4-bit",
    3: "Bit fields",
    4: "JPEG",
    5: "PNG",
}
TIFF_TYPES = {
    1: (1, "B"),
    2: (1, None),
    3: (2, "H"),
    4: (4, "I"),
    5: (8, "II"),
    6: (1, "b"),
    7: (1, None),
    8: (2, "h"),
    9: (4, "i"),
    10: (8, "ii"),
    11: (4, "f"),
    12: (8, "d"),
}
EXIF_TAGS = {
    0x010E: "Image description",
    0x010F: "Camera make",
    0x0110: "Camera model",
    0x0112: "Orientation",
    0x011A: "X resolution",
    0x011B: "Y resolution",
    0x0128: "Resolution unit",
    0x0131: "Software",
    0x0132: "Date/time modified",
    0x013B: "Artist",
    0x8298: "Copyright",
}
EXIF_SUB_TAGS = {
    0x829A: "Exposure time",
    0x829D: "F-number",
    0x8827: "ISO speed",
    0x9000: "Exif version",
    0x9003: "Date/time original",
    0x9004: "Date/time digitized",
    0x920A: "Focal length",
    0x9286: "User comment",
    0xA002: "Exif image width",
    0xA003: "Exif image height",
    0xA420: "Image unique ID",
    0xA430: "Camera owner",
    0xA431: "Body serial number",
    0xA433: "Lens make",
    0xA434: "Lens model",
    0xA435: "Lens serial number",
}
EXIF_ORIENTATIONS = {
    1: "Normal",
    2: "Mirrored horizontally",
    3: "Rotated 180",
    4: "Mirrored vertically",
    5: "Mirrored, rotated 270 clockwise",
    6: "Rotated 90 clockwise",
    7: "Mirrored, rotated 90 clockwise",
    8: "Rotated 270 clockwise",
}


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


def sniff_image(raw):
    if raw.startswith(PNG_SIGNATURE):
        return "PNG"
    if raw.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if raw[:6] in (b"GIF87a", b"GIF89a"):
        return "GIF"
    if raw[:2] == b"BM":
        return "BMP"
    if raw[:4] in (b"II*\x00", b"MM\x00*"):
        return "TIFF"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "WebP"
    return None


def _ratio(pair):
    return pair[0] / pair[1] if pair[1] else None


def _tiff_value(order, kind, count, data):
    size, code = TIFF_TYPES[kind]
    if kind == 2:
        return data.rstrip(b"\0").decode("utf-8", "replace")
    if code is None:
        return bytes(data)
    values = struct.unpack_from(order + code * count, data)
    if len(code) == 2:
        values = list(zip(values[0::2], values[1::2]))
    return values[0] if len(values) == 1 else list(values)


def _format_exif(tag, value):
    if isinstance(value, tuple) and len(value) == 2:
        value = _ratio(value)
    if tag == 0x9286 and isinstance(value, bytes):
        return value[8:].decode("utf-8", "replace").strip("\0 ")
    if tag in (0x9000,) and isinstance(value, bytes):
        return value.decode("ascii", "replace")
    if tag == 0x829A and value:
        return f"1/{round(1 / value)} s" if value < 1 else f"{value:g} s"
    if tag == 0x829D and value:
        return f"f/{value:g}"
    if tag == 0x920A and value:
        return f"{value:g} mm"
    if tag == 0x0112:
        return EXIF_ORIENTATIONS.get(value, str(value))
    if tag == 0x0128:
        return {2: "inches", 3: "centimetres"}.get(value, str(value))
    if isinstance(value, bytes):
        return value[:32].hex()
    if isinstance(value, list):
        return ", ".join(
            f"{_ratio(v):g}" if isinstance(v, tuple) and _ratio(v) is not None else str(v)
            for v in value[:16]
        )
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _degrees(parts, ref):
    if not isinstance(parts, list) or len(parts) != 3:
        return None
    d, m, s = (_ratio(p) for p in parts)
    if None in (d, m, s):
        return None
    sign = -1 if ref in ("S", "W") else 1
    return sign * (d + m / 60 + s / 3600)


def exif_rows(tiff):
    order = {b"II": "<", b"MM": ">"}.get(tiff[:2])
    if not order or struct.unpack_from(order + "H", tiff, 2)[0] != 42:
        return []

    def read(offset):
        found = {}
        if not 0 < offset <= len(tiff) - 2:
            return found, 0
        total = struct.unpack_from(order + "H", tiff, offset)[0]
        for i in range(min(total, 512)):
            at = offset + 2 + 12 * i
            if at + 12 > len(tiff):
                break
            tag, kind, count = struct.unpack_from(order + "HHI", tiff, at)
            if kind not in TIFF_TYPES:
                continue
            size = TIFF_TYPES[kind][0] * count
            start = at + 8 if size <= 4 else struct.unpack_from(order + "I", tiff, at + 8)[0]
            if size > 65536 or start + size > len(tiff):
                continue
            found[tag] = _tiff_value(order, kind, count, tiff[start : start + size])
        after = offset + 2 + 12 * total
        nxt = struct.unpack_from(order + "I", tiff, after)[0] if after + 4 <= len(tiff) else 0
        return found, nxt

    first, nxt = read(struct.unpack_from(order + "I", tiff, 4)[0])
    sub = read(first[0x8769])[0] if isinstance(first.get(0x8769), int) else {}
    gps = read(first[0x8825])[0] if isinstance(first.get(0x8825), int) else {}
    thumb = read(nxt)[0] if nxt else {}
    rows = [(name, _format_exif(tag, first[tag])) for tag, name in EXIF_TAGS.items() if tag in first]
    rows += [(name, _format_exif(tag, sub[tag])) for tag, name in EXIF_SUB_TAGS.items() if tag in sub]
    lat = _degrees(gps.get(2), gps.get(1))
    lon = _degrees(gps.get(4), gps.get(3))
    if lat is not None and lon is not None:
        rows.append(("GPS position", f"{lat:.6f}, {lon:.6f}"))
    if isinstance(gps.get(6), tuple) and _ratio(gps[6]) is not None:
        below = gps.get(5) == b"\x01" or gps.get(5) == 1
        rows.append(("GPS altitude", f"{'-' if below else ''}{_ratio(gps[6]):.1f} m"))
    if isinstance(gps.get(7), list) and len(gps[7]) == 3:
        h, m, s = (_ratio(p) or 0 for p in gps[7])
        rows.append(("GPS date/time (UTC)", f"{gps.get(29, '')} {int(h):02d}:{int(m):02d}:{int(s):02d}".strip()))
    if thumb and (0x0201 in thumb or 0x0111 in thumb):
        rows.append(("Embedded thumbnail", "Yes"))
    return rows


def xmp_rows(text):
    rows = []
    for tag, value in _XMP_RE.findall(text) + _XMP_ATTR_RE.findall(text):
        value = re.sub(r"<[^>]+>", " ", value).strip()
        if value:
            rows.append((tag, " ".join(value.split())))
    return list(dict.fromkeys(rows))


def _metadata_groups(exif, xmp):
    groups = []
    if exif:
        try:
            groups.append(("EXIF", exif_rows(exif)))
        except (struct.error, ValueError, IndexError) as e:
            groups.append(("EXIF", [("Could not read", f"{type(e).__name__}: {e}")]))
    if xmp:
        groups.append(("XMP", xmp_rows(xmp)))
    return groups


class HoverText(str):

    def __new__(cls, text, tip):
        obj = super().__new__(cls, text)
        obj.tip = tip
        return obj


def _comment_row(data):
    text = data.rstrip(b"\0")
    try:
        decoded = text.decode("utf-8")
    except UnicodeDecodeError:
        decoded = text.decode("latin-1")
    if all(c.isprintable() or c in "\t\r\n" for c in decoded):
        return ("Comment", decoded.strip())
    shown = " ".join(f"{b:02x}" for b in data[:IMAGE_HEX_LIMIT])
    tip = f"Binary data, {len(data)} bytes"
    if len(data) > IMAGE_HEX_LIMIT:
        shown += f" ... (first {IMAGE_HEX_LIMIT} of {len(data)} bytes)"
    return ("Comment (hex dump)", HoverText(shown, tip))


def _run_names(names):
    counts = {}
    for name in names:
        counts[name] = counts.get(name, 0) + 1
    return ", ".join(f"{n} x{c}" if c > 1 else n for n, c in counts.items())


def png_info(raw):
    size, rows, text, exif, xmp = None, [], [], None, None
    names, bad, pos, end = [], [], 8, None
    while pos + 8 <= len(raw):
        length, kind = struct.unpack_from(">I4s", raw, pos)
        body = raw[pos + 8 : pos + 8 + length]
        name = kind.decode("ascii") if kind.isalpha() else kind.hex()
        names.append(name)
        whole = pos + 12 + length <= len(raw)
        if whole and zlib.crc32(kind + body) != struct.unpack_from(">I", raw, pos + 8 + length)[0]:
            bad.append(name)
        if name == "IHDR" and len(body) >= 13:
            w, h, depth, color, _, _, interlace = struct.unpack_from(">IIBBBBB", body)
            size = (w, h)
            rows += [
                ("Colour type", PNG_COLOR_TYPES.get(color, str(color))),
                ("Bit depth", f"{depth} bits per channel"),
                ("Interlace", "Adam7" if interlace else "None"),
            ]
        elif name == "pHYs" and len(body) >= 9:
            x, y, unit = struct.unpack_from(">IIB", body)
            rows.append(("Resolution", f"{x * 0.0254:.0f} x {y * 0.0254:.0f} DPI" if unit == 1 else f"{x} x {y} (unit unknown)"))
        elif name == "tIME" and len(body) >= 7:
            y, mo, d, h, mi, s = struct.unpack_from(">HBBBBB", body)
            rows.append(("Last modified (tIME)", f"{y:04d}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d} UTC"))
        elif name == "gAMA" and len(body) >= 4:
            rows.append(("Gamma", f"{struct.unpack_from('>I', body)[0] / 100000:g}"))
        elif name == "sRGB" and body:
            rows.append(("sRGB rendering intent", ["Perceptual", "Relative colorimetric", "Saturation", "Absolute colorimetric"][body[0] % 4]))
        elif name == "iCCP":
            rows.append(("ICC profile", body.split(b"\0", 1)[0].decode("latin-1")))
        elif name == "acTL" and len(body) >= 8:
            frames, plays = struct.unpack_from(">II", body)
            rows.append(("Animation", f"{frames} frames, {'loops forever' if plays == 0 else f'{plays} plays'}"))
        elif name == "eXIf":
            exif = body
        elif name in ("tEXt", "zTXt", "iTXt"):
            key, _, rest = body.partition(b"\0")
            key = key.decode("latin-1")
            if name == "tEXt":
                value = rest.decode("latin-1")
            elif name == "zTXt":
                value = zlib.decompressobj().decompress(rest[1:], 65536).decode("utf-8", "replace")
            else:
                flag, rest = rest[0], rest[2:]
                _, _, rest = rest.partition(b"\0")
                _, _, rest = rest.partition(b"\0")
                if flag:
                    rest = zlib.decompressobj().decompress(rest, 65536)
                value = rest.decode("utf-8", "replace")
            if key == "XML:com.adobe.xmp":
                xmp = value
            else:
                text.append((key, value))
        pos += 12 + length
        if name == "IEND":
            end = pos
        if name == "IEND" or not whole:
            break
    rows.append(("Chunks", _run_names(names)))
    if bad:
        rows.append(("Chunk CRC errors", f"WARNING: {', '.join(bad)}"))
    if end is None:
        rows.append(("Structure", "WARNING: no IEND chunk, so the image is truncated or damaged"))
    elif end < len(raw):
        rows.append(("Data after IEND", f"WARNING: {len(raw) - end} bytes of extra data at offset {end}"))
    groups = [("PNG", rows)]
    if text:
        groups.append(("Text chunks", text))
    return size, groups + _metadata_groups(exif, xmp)


def jpeg_info(raw):
    size, rows, comments, exif, xmp, notes = None, [], [], None, None, []
    pos = 2
    while pos + 4 <= len(raw) and raw[pos] == 0xFF:
        marker = raw[pos + 1]
        if marker == 0xFF:
            pos += 1
            continue
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if marker == 0xD9:
            break
        length = struct.unpack_from(">H", raw, pos + 2)[0]
        seg = raw[pos + 4 : pos + 2 + length]
        if marker in JPEG_SOF and len(seg) >= 6:
            precision, h, w, count = struct.unpack_from(">BHHB", seg)
            size = (w, h)
            rows += [
                ("Encoding", JPEG_SOF[marker]),
                ("Precision", f"{precision} bits"),
                ("Components", f"{count} ({JPEG_COMPONENTS.get(count, 'unknown')})"),
            ]
        elif marker == 0xE0 and seg.startswith(b"JFIF\0") and len(seg) >= 12:
            units, xd, yd = struct.unpack_from(">BHH", seg, 7)
            unit = {0: "aspect ratio", 1: "DPI", 2: "dots per cm"}.get(units, "unknown unit")
            rows.append(("JFIF", f"version {seg[5]}.{seg[6]:02d}, density {xd} x {yd} ({unit})"))
        elif marker == 0xE1 and seg.startswith(b"Exif\0\0"):
            exif = seg[6:]
        elif marker == 0xE1 and seg.startswith(b"http://ns.adobe.com/xap/1.0/\0"):
            xmp = seg[29:].decode("utf-8", "replace")
        elif marker == 0xE2 and seg.startswith(b"ICC_PROFILE\0"):
            notes.append("ICC colour profile")
        elif marker == 0xED and seg.startswith(b"Photoshop 3.0\0"):
            notes.append("Photoshop / IPTC data")
        elif marker == 0xEE and seg.startswith(b"Adobe"):
            notes.append("Adobe segment")
        elif marker == 0xFE:
            comments.append(bytes(seg))
        if marker == 0xDA:
            break
        pos += 2 + length
    eoi = raw.rfind(b"\xff\xd9")
    if eoi == -1:
        rows.append(("Structure", "WARNING: no end-of-image marker, so the image is truncated or damaged"))
    elif eoi + 2 < len(raw):
        extra = len(raw) - eoi - 2
        rows.append(
            (
                "Data after EOI",
                f"{'WARNING: ' if extra > 3 else ''}{extra} bytes of extra data at offset {eoi + 2}",
            )
        )
    if notes:
        rows.append(("Also contains", ", ".join(notes)))
    groups = [("JPEG", rows)]
    if comments:
        groups.append(("Comments", [_comment_row(c) for c in comments]))
    return size, groups + _metadata_groups(exif, xmp)


def gif_info(raw):
    w, h, flags, background, _ = struct.unpack_from("<HHBBB", raw, 6)
    pos = 13 + (3 * (2 << (flags & 7)) if flags & 0x80 else 0)
    frames, comments, loops, end = 0, [], None, None
    while pos < len(raw):
        block = raw[pos]
        if block == 0x3B:
            end = pos + 1
            break
        if block == 0x21 and pos + 2 < len(raw):
            label, pos, parts = raw[pos + 1], pos + 2, []
            while pos < len(raw) and raw[pos]:
                parts.append(raw[pos + 1 : pos + 1 + raw[pos]])
                pos += 1 + raw[pos]
            pos += 1
            if label == 0xFE:
                comments.append(b"".join(parts))
            elif label == 0xFF and len(parts) > 1 and parts[0].startswith(b"NETSCAPE") and len(parts[1]) >= 3:
                loops = struct.unpack_from("<H", parts[1], 1)[0]
        elif block == 0x2C and pos + 10 < len(raw):
            frames += 1
            local = raw[pos + 9]
            pos += 10 + (3 * (2 << (local & 7)) if local & 0x80 else 0) + 1
            while pos < len(raw) and raw[pos]:
                pos += 1 + raw[pos]
            pos += 1
        else:
            break
    rows = [
        ("Version", raw[3:6].decode("ascii")),
        ("Logical screen", f"{w} x {h}"),
        ("Colour table", f"global, {2 << (flags & 7)} colours" if flags & 0x80 else "none (local tables only)"),
        ("Frames", str(frames)),
    ]
    if loops is not None:
        rows.append(("Animation loops", "forever" if loops == 0 else str(loops)))
    if end is None:
        rows.append(("Structure", "WARNING: no trailer block, so the image is truncated or damaged"))
    elif end < len(raw):
        rows.append(("Data after trailer", f"WARNING: {len(raw) - end} bytes of extra data at offset {end}"))
    groups = [("GIF", rows)]
    if comments:
        groups.append(("Comments", [_comment_row(c) for c in comments]))
    return (w, h), groups


def bmp_info(raw):
    declared, offset = struct.unpack_from("<I4xI", raw, 2)
    header = struct.unpack_from("<I", raw, 14)[0]
    if header == 12:
        w, h, _, bpp = struct.unpack_from("<HHHH", raw, 18)
        compression, xppm, yppm = None, 0, 0
    else:
        w, h, _, bpp, compression, _, xppm, yppm = struct.unpack_from("<iiHHIIii", raw, 18)
    rows = [
        ("Header", f"{header} bytes"),
        ("Bits per pixel", str(bpp)),
        ("Row order", "bottom-up" if h > 0 else "top-down"),
    ]
    if compression is not None:
        rows.append(("Compression", BMP_COMPRESSION.get(compression, str(compression))))
    if xppm and yppm:
        rows.append(("Resolution", f"{xppm * 0.0254:.0f} x {yppm * 0.0254:.0f} DPI"))
    rows.append(("Pixel data offset", str(offset)))
    if declared != len(raw):
        rows.append(("File size field", f"WARNING: declares {declared} bytes but the file is {len(raw)} bytes"))
    return (w, abs(h)), [("BMP", rows)]


def image_references(pkg, part):
    found = []
    for name in sorted(pkg.data):
        if not name.lower().endswith(".rels"):
            continue
        folder, _, leaf = name.rpartition("/")
        base = folder[: -len("_rels")].rstrip("/") if folder.endswith("_rels") else folder
        source = posixpath.join(base, leaf[: -len(".rels")]) if leaf != ".rels" else ""
        for tag in _RELATIONSHIP_RE.findall(decode_xml(pkg.data[name])[0]):
            attrs = dict(_ATTRIBUTE_RE.findall(tag))
            target = attrs.get("Target", "")
            if not target or attrs.get("TargetMode") == "External":
                continue
            target = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(base, target))
            if target.lower() == part.lower():
                found.append(f"{source or '(package root)'} ({attrs.get('Id', '?')})")
    return found


def image_metadata(pkg, part, raw, decoded_size=None):
    kind = sniff_image(raw)
    ext = os.path.splitext(part)[1].lower()
    expected = IMAGE_FORMATS.get(ext)
    general = [
        ("Part", part),
        ("File size", f"{len(raw):,} bytes ({human_size(len(raw))})"),
        ("Format", f"{kind} (from the file content)" if kind else "Not recognised as an image"),
    ]
    if kind and expected and kind != expected:
        general.append(("Extension", f"WARNING: {ext} should be {expected}, but the content is {kind}"))
    elif kind:
        general.append(("Extension", f"{ext} (matches the content)"))
    else:
        general.append(("Extension", f"WARNING: {ext} but the content is not a known image format"))
    groups, size = [], None
    parsers = {"PNG": png_info, "JPEG": jpeg_info, "GIF": gif_info, "BMP": bmp_info}
    if kind in parsers:
        try:
            size, groups = parsers[kind](raw)
        except (struct.error, ValueError, IndexError, zlib.error) as e:
            groups = [(kind, [("Could not read the header", f"{type(e).__name__}: {e}")])]
    if size is None and decoded_size is not None and not decoded_size.isEmpty():
        size = (decoded_size.width(), decoded_size.height())
    if size:
        general.append(("Dimensions", f"{size[0]} x {size[1]} pixels"))
    for label, algo in (("MD5", hashlib.md5), ("SHA-1", hashlib.sha1), ("SHA-256", hashlib.sha256)):
        general.append((label, algo(raw).hexdigest()))
    refs = image_references(pkg, part)
    general += [("Referenced by", r) for r in refs] or [
        ("Referenced by", "WARNING: no relationship points at this image (orphaned)")
    ]
    if part in pkg.recovered:
        problem = pkg.recovered[part]
        general.append(
            ("Recovery", f"WARNING: UNVERIFIED, recovered but failed its integrity check ({problem})")
            if problem
            else ("Recovery", "Recovered from damaged zip headers and verified against its CRC32/size")
        )
    return kind, [("General", general)] + groups


def part_text(raw):
    if raw is None:
        return ""
    return pretty_xml(decode_xml(raw)[0])[0]


@functools.lru_cache(maxsize=16)
def formatted_lines(raw):
    return tuple(part_text(raw).splitlines())


def compile_query(query, case=False, whole=False, regex=False):
    pattern = query if regex else re.escape(query)
    if whole:
        pattern = rf"(?<!\w)(?:{pattern})(?!\w)"
    return re.compile(pattern, 0 if case else re.IGNORECASE)


def _snippet(text, start, end):
    """HTML for a match with some context; the match is highlighted."""

    def flat(s):
        return html.escape(re.sub(r"\s+", " ", s))

    a, b = max(start - SNIPPET_CONTEXT, 0), min(end + SNIPPET_CONTEXT, len(text))
    return (
        ("..." if a else "")
        + flat(text[a:start].lstrip())
        + f'<span style="background-color:#ffd24d; color:#000000">{flat(text[start:end])}</span>'
        + flat(text[end:b])
        + ("..." if b < len(text) else "")
    )


def search_part(raw, rx, text_only=False, limit=SEARCH_MAX_HITS):
    """Matches as (line, column, length, html) on the formatted XML lines."""
    lines = formatted_lines(raw)
    hits = []
    if not text_only:
        for n, line in enumerate(lines, 1):
            for m in rx.finditer(line):
                if m.end() > m.start():
                    hits.append(
                        (n, m.start(), m.end() - m.start(), _snippet(line, m.start(), m.end()))
                    )
                    if len(hits) >= limit:
                        return hits
        return hits

    # text only: join the character data so words split across runs still match
    pieces, segs, starts, pos = [], [], [], 0

    def add(text, line, col, raw_len, exact):
        nonlocal pos
        starts.append(pos)
        segs.append((line, col, raw_len, len(text), exact))
        pieces.append(text)
        pos += len(text)

    # parts without paragraphs (properties, comments lists) keep each element apart
    paragraphs = any(_PARA_END_RE.search(line) for line in lines)
    for n, line in enumerate(lines, 1):
        found = False
        for m in _TEXT_RE.finditer(line):
            if m.group(1):
                found = True
                text = html.unescape(m.group(1))
                add(text, n, m.start(1), len(m.group(1)), len(text) == len(m.group(1)))
                if not paragraphs:
                    add("\n", n, 0, 0, True)
        if not found and "<" not in line and ">" not in line and line.strip():
            text = html.unescape(line.strip())
            add(text, n, len(line) - len(line.lstrip()), len(line.strip()), text == line.strip())
            if not paragraphs:
                add("\n", n, 0, 0, True)
        if _BREAK_RE.search(line):
            add(" ", n, 0, 0, True)
        if _PARA_END_RE.search(line):
            add("\n", n, 0, 0, True)
    stream = "".join(pieces)
    for m in rx.finditer(stream):
        if m.end() == m.start():
            continue
        i = bisect.bisect_right(starts, m.start()) - 1
        line, col, raw_len, text_len, exact = segs[i]
        offset = m.start() - starts[i]
        if exact:
            col, length = col + offset, min(m.end() - m.start(), text_len - offset)
        else:
            length = raw_len
        hits.append((line, col, max(length, 0), _snippet(stream, m.start(), m.end())))
        if len(hits) >= limit:
            break
    return hits


def search_documents(jobs, rx, text_only, limit=SEARCH_MAX_HITS):
    """jobs: one [(part name, raw bytes)] list per document; returns (hits, truncated)."""
    out = []
    for doc, parts in enumerate(jobs):
        for name, raw in parts:
            room = limit - len(out)
            if room <= 0:
                return out, True
            for line, col, length, snippet in search_part(raw, rx, text_only, room + 1):
                if len(out) >= limit:
                    return out, True
                out.append((doc, name, line, col, length, snippet))
    return out, False


def build_diff(left, right):
    a = formatted_lines(left)
    b = formatted_lines(right)
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
    counts = {"same": 0, "diff": 0, "left": 0, "right": 0}
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
            limit = 40 if status != "diff" else REPORT_MAX_ROWS
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


def main(argv=None):
    from pyooxml import gui

    return gui.main(argv)


if __name__ == "__main__":
    if not __package__ and not getattr(sys, "frozen", False):
        # run as a script: import from the folder above, so "pyooxml" is the package
        sys.path[0] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main())
