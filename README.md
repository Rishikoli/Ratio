# Ratio — Financial Document Intelligence & Gap Detector (Desktop Engine)

Ratio is an offline, privacy-first financial statement extraction and mathematical audit engine designed for CA firms and financial professionals.

## How to Run on Windows

1. Extract `Ratio_Desktop_Engine.zip` to your computer.
2. Double-click `run_ratio_windows.bat`.
3. The Ratio interface will open automatically in your browser at `http://localhost:8000`.

## How to Build Standalone EXE (Optional)

If you want to package Ratio into a standalone `.exe` without requiring Python on client PCs:
1. Open Command Prompt / PowerShell in this directory.
2. Run:
   ```cmd
   python build_windows.py
   ```
3. The standalone application folder will be created at `dist/Ratio/`.

## Key Features
- **Neural OCR Parsing**: Powered by RapidOCR (PP-OCRv4 ONNX).
- **Interactive Review & Edit Grid**: Edit misread numbers directly in the browser with live mathematical re-validation.
- **Missing Page & Gap Detector**: Automatically alerts if bank statement pages are missing or balance gaps exist.
- **Smart Exports**: Direct export to Tally XML vouchers and formatted Excel (.xlsx) workbooks.
