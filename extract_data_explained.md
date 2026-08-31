# `extract_data.py` explained

This guide explains every meaningful line in `extract_data.py` as it exists
today. Blank lines do not run any code: they only make the script easier to
read. Indentation is important in Python because it shows which lines belong
inside a function, loop, `if`, `try`, or `except` block.

## What the script does

You run this command:

```bash
python3 extract_data.py
```

The script reads every supported file in `file_types_samples`, extracts fields
that it can identify, and rewrites `extracted_data.json`. It does **not** guess:
missing values are written as JSON `null`, and a file problem is written as an
`error` message for that file.

## Lines 1–23: introduction and imported tools

| Line(s) | Explanation |
| --- | --- |
| 1 | Tells macOS/Linux to run the script with Python 3 when the file is made executable. It is optional when you run `python3 extract_data.py`. |
| 2–11 | A documentation string. It describes the supported file types, default input/output files, and optional OCR requirements. It does not run extraction logic. |
| 13 | Enables modern type hints such as `list[str]` on older supported Python versions. It has no effect on the extracted data. |
| 15 | Imports `argparse`, which reads command-line options such as `--output`. |
| 16 | Imports `importlib`, used to load optional libraries only when a PDF or image needs them. |
| 17 | Imports `json`, which writes the final JSON file. |
| 18 | Imports `re`, Python’s regular-expression tool. Regular expressions find labels such as `Surname:` in text. |
| 19 | Imports `sys`, used to return the script’s final exit code. |
| 20 | Imports `zipfile`. A DOCX file is really a ZIP archive containing XML files. |
| 21 | Imports `Path`, a safer way to work with filenames and folders. |
| 22 | Imports `Any`, used only in type hints for JSON values that may be text, numbers, lists, or dictionaries. |
| 23 | Imports `ElementTree`, which reads XML inside a DOCX file. |

## Lines 26–89: configuration, not extraction logic

These constants make the rest of the program shorter. Changing them changes
which fields are recognised, without changing the extraction functions.

| Line(s) | Explanation |
| --- | --- |
| 26 | Lists the allowed filename extensions. Files with another extension are ignored when scanning a directory. |
| 28 | Starts one multi-line string containing every JSON field name. |
| 29–36 | Each word is a JSON key. The script starts each of these fields at `None`, which becomes JSON `null`. Splitting this list saves many repetitive lines while keeping all output keys stable. |
| 37 | `.split()` turns the multi-line text into a Python list of field names. |
| 39 | Starts the P60 pay-row map. |
| 40 | Maps the previous-employment row to its two JSON pay/tax keys. |
| 41 | Maps the current-employment row to its two JSON pay/tax keys. |
| 42 | Maps the annual-total row to its two JSON pay/tax keys. |
| 43 | Ends that map. |
| 45 | Starts the map for year-to-date payslip amounts. |
| 46 | Maps `Taxable Pay YTD` to the JSON key `taxable_pay_ytd`. |
| 47 | Maps `Tax Paid YTD` to `tax_paid_ytd`. |
| 48 | Maps `NI Paid YTD - A` to `ni_paid_ytd`. |
| 49 | Maps `Pension YTD` to `pension_ytd`. |
| 50 | Ends that map. |
| 52 | Starts the main map of source-document labels to JSON field names. |
| 53 | Converts the document label `Surname` into the `surname` JSON field. |
| 54 | Converts `Forenames / Initials` into `forenames`. |
| 55–56 | Accepts either common spelling of the National Insurance label and stores both in the same `national_insurance_number` field. |
| 57 | Maps a payroll number label to `payroll_number`. |
| 58–62 | Map the tax code, NI table letter, and employer details to matching JSON fields. |
| 63–68 | Accept short and long P60 label variants for the three National Insurance earnings bands. |
| 69 | Maps the employee NI contribution amount. |
| 70–73 | Map the four statutory payment labels. |
| 74–75 | Map student and postgraduate loan deductions. |
| 76 | Ends the label map. |
| 78 | Starts the set of fields that must be converted from text to a number. |
| 79–88 | Each listed field is an amount of money. The set lets one later rule decide whether to call `_money`. |
| 89 | Ends the money-field set. |

## Lines 92–105: optional libraries and DOCX reading

| Line(s) | Explanation |
| --- | --- |
| 92 | Defines `_require`, a private helper. The leading underscore means it is for this script’s internal use. |
| 93 | Begins a protected attempt to import a library. |
| 94 | Loads and returns the requested library when it is installed. |
| 95 | Catches only the error meaning that the library is not installed. |
| 96 | Raises a readable error showing the exact install command. `from error` keeps the original technical cause available for debugging. |
| 99 | Defines `_read_docx`, which returns all readable DOCX text. |
| 100 | Opens the DOCX ZIP archive and closes it automatically afterwards. |
| 101 | Reads the Word XML document and turns it into an XML tree. |
| 102 | Stores Word’s XML namespace prefix, needed to find paragraph and text tags correctly. |
| 103–104 | Builds a list of paragraph strings. For every Word paragraph it joins every text fragment; the second line continues the same list expression. |
| 105 | Removes empty paragraphs and joins the remaining paragraphs with newline characters. |

## Lines 108–133: OCR and PDF reading

| Line(s) | Explanation |
| --- | --- |
| 108 | Defines `_ocr_image`, which converts an image into text with OCR. |
| 109 | Loads Pillow’s image reader only when image OCR is needed. |
| 110 | Loads the Python adapter that calls the Tesseract OCR program. |
| 111 | Starts code that may fail if Tesseract is unavailable. |
| 112 | Opens the image safely and calls the opened image `image`. |
| 113 | Sends that image to Tesseract and returns its recognised text. |
| 114 | Catches Tesseract’s specific “program not found” error. |
| 115 | Replaces it with a plain-language macOS installation instruction. |
| 118 | Defines `_read_pdf`, which returns both the PDF text and how it was obtained. |
| 119 | Loads `pypdf`, the library used for PDFs that already contain selectable text. |
| 120 | Reads text from every page, substitutes an empty string for empty pages, joins the pages, and trims leading/trailing whitespace. |
| 121 | Checks whether native PDF text was found. |
| 122 | Returns that text with the method name `pdf_text`; this is more accurate than OCR. |
| 124 | Loads `pdf2image` only when the PDF appears to be scanned. |
| 125 | Loads the Tesseract adapter for scanned-PDF OCR. |
| 126 | Starts rendering the PDF pages into images. |
| 127 | Converts the PDF pages to images using Poppler. |
| 128 | Catches a rendering failure, commonly a missing Poppler installation. |
| 129 | Raises a helpful message explaining how to install Poppler. |
| 130 | Starts the OCR stage after page rendering succeeds. |
| 131 | OCRs every rendered page, joins their text, and labels the method `ocr_pdf`. |
| 132 | Catches a missing Tesseract engine. |
| 133 | Raises the user-friendly Tesseract instruction. |

## Lines 136–162: choose a reader and clean values

| Line(s) | Explanation |
| --- | --- |
| 136 | Defines the public reader used for any single file. |
| 137 | Gets the lowercase extension, for example `.PDF` becomes `.pdf`. |
| 138–139 | For a text file, reads UTF-8 text directly and reports the method as `text`. |
| 140–141 | For a DOCX file, calls the DOCX reader and reports `docx`. |
| 142–143 | For a PDF, calls `_read_pdf`; it already returns text and a method. |
| 144–145 | For PNG/JPG/JPEG, OCRs the image and reports `ocr_image`. |
| 146 | Stops with a clear error when the file extension is unsupported. |
| 149 | Defines `_normalise_label`, used for consistent fallback JSON keys. |
| 150 | Lowercases a label, replaces punctuation/spaces with underscores, and removes underscores at each end. Example: `Pay Date` becomes `pay_date`. |
| 153 | Defines `_text_value`, which finds a labelled value in extracted text. |
| 154 | Searches for `label: value`, allowing whitespace and a value on the next line. `re.escape` makes labels safe to search literally. |
| 155 | Returns the captured value without surrounding spaces, or `None` if it is missing. |
| 158 | Defines `_money`, which safely converts money text to a Python number. |
| 159–160 | Immediately returns `None` when no value was supplied. |
| 161 | Removes thousands commas, pound symbols, and surrounding spaces. |
| 162 | Converts only a valid numeric value to `float`; otherwise returns `None` rather than crashing or guessing. |

## Lines 165–227: extract named fields

| Line(s) | Explanation |
| --- | --- |
| 165 | Defines the main field-extraction function. It accepts plain text from any reader. |
| 166 | Documents the important rule: only source values are returned; unavailable values stay null. |
| 167 | Creates every field from `FIELD_NAMES` with value `None`. This replaces a long, repetitive dictionary while producing the same JSON keys. |
| 168 | Adds a separate empty dictionary for additional recognised label/value pairs. |
| 170 | Loops through every standard document-label mapping. |
| 171 | Attempts to find the value after that label. |
| 172 | Continues only when a real value was found. |
| 173 | Stores a number for money fields and text for all other standard fields. |
| 175 | Loops through the three two-number P60 pay rows. |
| 176–179 | Searches for the row label and captures its pay amount and tax amount, allowing values to be on one or two lines. |
| 180 | Continues only when the pair of amounts was found. |
| 181 | Saves the first captured amount under the row’s pay key. |
| 182 | Saves the second captured amount under the row’s tax key. |
| 184 | Looks for a tax-year ending date near the `TAX YEAR TO` heading. The 120-character allowance handles different P60 layouts. |
| 185 | Continues only when that date exists. |
| 186 | Stores the date in title case, for example `5 April 2024`. |
| 188 | Checks that both forenames and surname were extracted. |
| 189 | Joins them into the convenient `full_name` field. |
| 191 | Starts special patterns for the supplied payslip’s layout. |
| 192 | Finds the employee name printed on the following line. |
| 193 | Finds the employee number on the following line. |
| 194 | Finds the pay date after `Pay Date:`. |
| 195 | Finds a National Insurance number when it follows the `NI Number` label directly. |
| 196 | Finds a tax code when it follows `Tax Code` directly. |
| 197 | Finds the NI category when it follows `NI Category` directly. |
| 198 | Ends the payslip-pattern map. |
| 199 | Loops through each payslip field pattern. |
| 200 | Searches the payslip text with the current pattern. |
| 201 | Continues only if that pattern matched. |
| 202 | Saves the matched value after removing extra spaces. |
| 204–207 | Search for the supplied payslip’s four-column NI/tax block: tax period, tax code, NI number, and NI category. This handles its table layout, where simple label/value patterns do not work. |
| 208 | Continues when that entire table block was found. |
| 209 | Stores the first table value as the tax period. |
| 210 | Stores the second table value as the tax code. |
| 211 | Stores the third table value as the NI number. |
| 212 | Stores the fourth table value as the NI category. |
| 214 | Loops through the four year-to-date payslip labels. |
| 215 | Finds the money value after each year-to-date label. |
| 216 | Continues only when the label/value pair exists. |
| 217 | Converts and stores the money amount. |
| 218 | Searches for the payslip’s net-pay amount. |
| 219 | Continues only when net pay was found. |
| 220 | Converts and stores net pay. |
| 222 | Builds a set of known labels so they are not repeated inside `other_fields`. |
| 223 | Finds every remaining single-line `Label: Value` pair in the document. |
| 224 | Converts that remaining label into a safe JSON key. |
| 225 | Keeps only non-empty labels not already handled as standard fields. |
| 226 | Stores the fallback value in `other_fields`. |
| 227 | Returns the completed field dictionary. |

## Lines 230–277: result records and command-line execution

| Line(s) | Explanation |
| --- | --- |
| 230 | Defines the document-type classifier. |
| 231 | Converts text to uppercase once, so matching ignores letter case. |
| 232 | Checks for the identifying P60 words. |
| 233 | Returns `p60` when both are present. |
| 234 | Checks either common spelling of payslip. |
| 235 | Returns `payslip` when found. |
| 236 | Uses `generic` for another supported document type. |
| 239 | Defines extraction for one file, including safe error handling. |
| 240 | Starts a protected operation: a bad file will not stop the rest of a folder. |
| 241 | Reads the source text and records the reader method. |
| 242 | Starts the normal JSON record. |
| 243 | Records the exact source path. |
| 244 | Adds the detected document type. |
| 245 | Adds the extraction method, such as `text`, `docx`, `pdf_text`, or OCR. |
| 246 | Adds all extracted structured fields. |
| 247 | Creates the warnings list; it is currently empty but keeps the output format ready for future warnings. |
| 248 | Ends the normal JSON record. |
| 249 | Catches any exception raised while processing that one file. |
| 250 | Returns an error record instead of failing the whole batch. |
| 253 | Defines the function that turns a file or folder input into a list of files. |
| 254 | Checks whether the input is one file rather than a folder. |
| 255 | Returns that single file in a list. |
| 256 | Otherwise recursively finds supported files, sorts them, and returns the list. |
| 259 | Defines `main`, the function that runs when you use the command. `argv` enables automated tests or another program to supply arguments. |
| 260 | Creates the command-line argument parser and its help text. |
| 261 | Adds an optional input argument; if omitted, it uses `file_types_samples`. |
| 262 | Adds `--output`; if omitted, it writes `extracted_data.json`. |
| 263 | Reads the supplied command-line arguments. |
| 265 | Converts the input text to a `Path` object. |
| 266 | Checks that the supplied input actually exists. |
| 267 | Shows a clear command-line error and stops if it does not. |
| 269 | Extracts every selected input file and puts the results in a list. |
| 270 | Converts the output filename to a `Path`. |
| 271 | Writes formatted UTF-8 JSON followed by one newline. `ensure_ascii=False` keeps names and symbols readable. |
| 272 | Tells you how many result records were written and where. |
| 273 | Returns success (`0`) only when no result has an `error`; otherwise returns `1` so automated tools know something needs attention. |
| 276 | Checks whether this file was run directly rather than imported by another Python program. |
| 277 | Runs `main` and passes its status code back to the operating system. |

## What was made smaller

The refactor reduced `extract_data.py` from 306 lines to 277 lines without
removing fields or supported formats. The biggest improvement is lines 28–37:
one list of field names now creates the same `null`-initialised JSON fields that
previously required a large repeated dictionary. Lines 39–50 also centralise
repeated P60 and payslip mappings so the extraction loop can reuse them.

The remaining longer areas are purposeful: PDF/DOCX/image readers need different
libraries, and the P60/payslip patterns handle real differences in their layouts.
