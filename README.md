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

## Key Features & High-Efficiency Core
- **Ultra-Lightweight Footprint (< 170 MB RAM)**: Specifically optimized to run smoothly on low-spec 8 GB RAM office laptops without lagging Windows or requiring expensive GPUs.
- **Lightning-Fast Neural OCR (200ms / Page)**: Powered by RapidOCR (PP-OCRv4 ONNX) with multi-core parallel page processing.
- **Mathematical Self-Healing Engine**: Automatically audits `Prev Balance - Debit + Credit = Current Balance` and auto-corrects minor OCR misreads in real-time.
- **3D Perspective & Illumination Preprocessor**: Flattens angled mobile passbook photos and strips heavy shadows cast by phones or hands.
- **Interactive Review & Edit Grid**: Inline editing of numbers directly in the browser with real-time recalculation.
- **Missing Page & Balance Gap Detector**: Automatically flags missing pages and closing balance discrepancies.
- **Smart Exports**: One-click direct export to Tally XML vouchers and formatted multi-tab Excel (.xlsx) workbooks.
