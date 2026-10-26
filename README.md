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

Pip install forthcoming!

#### Usage
Documents can be passed on the command line, chosen from the File menu, or drag-and-dropped onto the window.
```
pyooxml                      # start empty
pyooxml document.docx        # view one document
pyooxml old.docx new.docx    # compare two documents
```

Supported files: `.docx .docm .dotx .dotm .xlsx .xlsm .xltx .xltm .pptx .pptm .potx .potm .ppsx .ppsm .vsdx .zip`

### Viewer / Editor
- Browse every part of the package in a tree, with a filter box to find parts quickly.
- XML parts are pretty-printed with syntax highlighting and line numbers, and checked for well-formedness.
- Images are displayed. Other binary parts show their size, SHA-256 and a hex dump of the first 4 KB.
- The right-hand pane is read-only until you click **Edit**. Once the content changes, a **Save Part** button appears.
- **File > Save Package As...** writes the package, including your edits, to a new file. **File > Extract Part...** saves the selected part on its own.

### Compare
**File > Compare Documents...** (Ctrl+D) accepts one or two documents. If you choose only one, you are prompted for the second.

- Every part is listed as Identical, Different, Only in left or Only in right. **Differences only** hides the identical ones.
- Selecting a part shows a side-by-side diff of the formatted XML. Use **Previous difference** (Shift+F3) and **Next difference** (F3) to move between them, or simply scroll.
- **Swap sides** exchanges the left and right documents, matters mostly for order of activity.
- **Export PDF...** (also under the File menu) writes a landscape report containing only the differences, with changed lines highlighted and the exact changed values marked. It also records the full path, size and SHA-256 of both files, and any warnings raised while opening them.

### Damaged and unusual documents
PyOOXML opens most documents whose zip structure is broken, for example files written by other applications that store `\` instead of `/` in part names, or files with a damaged central directory. Parts are recovered from the raw zip data and verified against their CRC32 and size. Parts that cannot be verified are still shown, but are marked **UNVERIFIED**.

Anything unusual that was recovered is listed on the **Warnings** tab, which appears only when there is something to report. Encrypted or IRM-protected documents (OLE compound files) are detected and reported rather than failing with a zip error.

### Original Source

This tool is based on the work originally developed by Atul Moglewar, and their Chrome Browser Extension "OOXML Tools". This particular version is no longer available, but I used a previous copy to reverse-engineer and improve upon its features.
