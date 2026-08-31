# How to run the data extractor

## 1. Open the terminal in VS Code

In VS Code, select **Terminal → New Terminal**. A terminal panel opens at the
bottom of the window.

## 2. Go to the project folder

Copy and paste this command, then press Return:

```bash
cd ~/Desktop/dataExtraction
```

## 3. Run the included sample files

```bash
python3 extract_data.py
```

This processes all supported files in `file_types_samples` and writes the
results to `extracted_data.json`.

## 4. Process your own folder of files

1. Create a folder in this project, for example `new_files`.
2. Put your PDF, DOCX, TXT, PNG, JPG, or JPEG files inside that folder.
3. Run:

```bash
python3 extract_data.py new_files --output new_results.json
```

Open `new_results.json` in VS Code to see the extracted values.

## 5. Process one file only

Replace the filename with your own file:

```bash
python3 extract_data.py new_files/my_document.pdf --output result.json
```

## Supported file types

- `.txt`
- `.docx`
- `.pdf`
- `.png`
- `.jpg`
- `.jpeg`

## Useful notes

- The script writes `null` when it cannot reliably find a value. It does not
  guess.
- Image and scanned-PDF extraction uses Tesseract OCR. It is now installed on
  this Mac.
- Use this command to display all command options:

```bash
python3 extract_data.py --help
```
