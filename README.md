# PyOOXML

## Overview
#### Purpose
View, edit and compare the parts inside OOXML packages (docx, xlsx, pptx and related formats), including damaged documents that other tools refuse to open.

PyOOXML is a Python 3 / PyQt6 port of the "OOXML Tools" browser extension by Atul Moglewar.

#### Installation
Install from the GitHub repository:
```
python3 -m pip install git+https://github.com/digitalsleuth/PyOOXML
```
PyQt6 is installed automatically. Then launch it with:
```
pyooxml
```

To run from a clone of the repository instead:
```
python3 -m pip install PyQt6
python3 -m pyooxml.pyooxml
```

#### Usage
Documents can be passed on the command line, chosen from the File menu, or dropped onto the window.
```
pyooxml                      # start empty
pyooxml document.docx        # view one document
pyooxml old.docx new.docx    # compare two documents
```

Supported files: `.docx .docm .dotx .dotm .xlsx .xlsm .xltx .xltm .pptx .pptm .potx .potm .ppsx .ppsm .vsdx .zip`

### Viewer / Editor
- Browse every part of the package in a tree, with a filter box to find parts quickly.
- XML parts are pretty-printed with syntax highlighting and line numbers, and checked for well-formedness.
- Images (PNG, JPEG, GIF, BMP) are scaled to fit the pane, with zoom buttons (**-**, **+**, **Fit**, **100%**) and Ctrl + mouse wheel. A metadata table underneath lists:
  - **General:** file size, format detected from the content (and a warning if the extension doesn't match it), dimensions, MD5, SHA-1, SHA-256, the relationships that reference the image (or a warning if it is orphaned), and any recovery status.
  - **Format details:** colour type and bit depth, resolution, PNG chunks, `tIME` and text chunks, JPEG encoding and comments, GIF frames and loop count, BMP header fields.
  - **EXIF and XMP:** camera make and model, software, dates, exposure settings, GPS position and altitude, creator tool, and similar fields.
  - **Anomalies:** CRC errors, a missing end marker, and extra data after the end of the image are shown in red.

  A damaged image that cannot be drawn still shows its metadata. Select rows and press Ctrl+C to copy them.
- Other binary parts show their size, SHA-256 and a hex dump of the first 4 KB.
- The right-hand pane is read-only until you click **Edit**. Once the content changes, a **Save Part** button appears.
- **File > Save Package As...** writes the package, including your edits, to a new file. **File > Extract Part...** saves the selected part on its own.

### Compare
**File > Compare Documents...** (Ctrl+D) accepts one or two documents. If you choose only one, you are prompted for the second. If you choose more than two, you are asked to choose again. Use **Swap sides** if the two documents land on the opposite sides from the ones you wanted.

- Every part is listed as Identical, Different, Only in left or Only in right. **Differences only** hides the identical ones.
- Selecting a part shows a side-by-side diff of the formatted XML, jumping straight to the first difference. Use **Previous difference** (Shift+F3) and **Next difference** (F3) to move between them.
- **Swap sides** exchanges the left and right documents.
- **Export PDF...** (also under the File menu) writes a landscape report containing only the differences, with changed lines highlighted and the exact changed words marked. It also records the full path, size and SHA-256 of both files, and any warnings raised while opening them. When the export finishes you are asked whether to open the file.

### Search
**Edit > Find in Document(s)...** (Ctrl+F) opens the **Search** tab. If text is selected in an editor pane, it is used as the starting query. Press Enter or **Find All** to search.

- With one document open, only that document is searched. After a comparison, **Search in** can limit the search to the left document, the right document, or both. Results are labelled Left or Right.
- Every XML part is searched, and each result shows the part, the line number and the match in context.
- Options: **Match case**, **Whole word**, **Regular expression** (Python syntax) and **Text only**.
- By default the XML source is searched, exactly as it is shown in the editor, so tags, attribute values and namespaces can be found. **Text only** searches the document text instead. Word often splits a word across several runs (`Jac` + `ques`), and only Text only will find it.
- Double-click a result (or press Enter on it) to jump to it. The match is highlighted in the Viewer, or in the left or right pane of the Compare tab. If the part is hidden by **Differences only**, that filter is switched off first.
- Results show the saved content of each part. Unsaved edits in the editor are not searched. At most 5000 matches are listed.
- Results are cleared whenever the open documents change.

### Themes
**View > Theme** switches the colour theme, and the choice is remembered between sessions.

- **Classic** (the default) is the plain system look, following your operating system's light or dark setting.
- The other themes are Atom One, Blender, Catppuccin (Frappe, Latte, Macchiato, Mocha), Dracula, GitHub Dark, GitHub Light, Modern Dark, Modern Light, Monokai, Nord and One Dark Two.
- XML syntax colours, diff and search highlights, selections and warnings are adjusted for each theme so that text stays readable on whatever is behind it.
- The PDF report always uses its own colours on a white page.

### Damaged and unusual documents
PyOOXML opens documents whose zip structure is broken, for example files written by other applications that store `\` instead of `/` in part names, or files with a damaged central directory. Parts are recovered from the raw zip data and verified against their CRC32 and size. Parts that cannot be verified are still shown, but are marked **UNVERIFIED**.

Anything unusual that was recovered is listed on a **Warnings** tab, which appears only when there is something to report. Encrypted or IRM-protected documents (OLE compound files) are detected and reported rather than failing with a zip error.

The full path of each loaded file is shown in the status bar.

## Building an executable
A PyInstaller spec is included. From the repository root:
```
python3 -m pip install pyinstaller
pyinstaller pyooxml.spec
```
The executable is written to `dist/` as `pyooxml-v<version>.exe`.

When the version changes, update `VERSION` in `pyooxml/pyooxml.py`, `__version__` in `pyooxml.spec` and the version fields in `version.txt`.

## Source layout
| File | Contents |
| --- | --- |
| `pyooxml/pyooxml.py` | Package reading and recovery, XML handling, comparison, search, image metadata and the report content. It does not need Qt. |
| `pyooxml/gui.py` | The PyQt6 interface and PDF output. |
| `pyooxml/themes.py` | Theme selection and the readability adjustments. |
| `pyooxml/_vendor/qt_themes/` | Colour schemes from qt-themes. |

## Third-Party Software
The colour schemes in `pyooxml/_vendor/qt_themes/` are from [qt-themes](https://pypi.org/project/qt-themes/) 0.4.1, copyright Beat Reichenbach, under the MIT License. See [pyooxml/_vendor/qt_themes/LICENSE](pyooxml/_vendor/qt_themes/LICENSE).
