#!/usr/bin/env python3
"""Extract structured fields from local TXT, DOCX, PDF, PNG, JPG, and JPEG files.

Run without arguments to process ``file_types_samples`` and write
``extracted_data.json``.  PDF/image OCR uses optional local dependencies:

    python3 -m pip install pypdf pillow pytesseract pdf2image

Image OCR also needs the Tesseract executable. Scanned PDF OCR additionally
needs Poppler (``brew install tesseract poppler`` on macOS).
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


SUPPORTED_SUFFIXES = {".txt", ".docx", ".pdf", ".png", ".jpg", ".jpeg"}

FIELD_NAMES = """
surname forenames full_name national_insurance_number payroll_number employee_name
employee_number pay_date tax_period ni_category tax_year_end tax_code nic_table_letter
employer_name employer_address employer_paye_reference previous_employment_pay
previous_employment_tax this_employment_pay tax_deducted total_year_pay total_year_tax
earnings_at_lel earnings_lel_to_pt earnings_pt_to_uel employee_national_insurance
statutory_maternity_pay statutory_paternity_pay statutory_adoption_pay
shared_parental_pay student_loan_deductions postgraduate_loan_deductions taxable_pay_ytd
tax_paid_ytd ni_paid_ytd pension_ytd net_pay
""".split()

PAY_ROWS = {
    "In Previous Employment(s)": ("previous_employment_pay", "previous_employment_tax"),
    "In This Employment": ("this_employment_pay", "tax_deducted"),
    "TOTAL FOR THE YEAR": ("total_year_pay", "total_year_tax"),
}

YTD_FIELDS = {
    "Taxable Pay YTD": "taxable_pay_ytd",
    "Tax Paid YTD": "tax_paid_ytd",
    "NI Paid YTD - A": "ni_paid_ytd",
    "Pension YTD": "pension_ytd",
}

LABEL_FIELDS = {
    "Surname": "surname",
    "Sumame": "surname",
    "Forenames / Initials": "forenames",
    "Forenames": "forenames",
    "National Insurance No": "national_insurance_number",
    "National Insurance Number": "national_insurance_number",
    "NI No": "national_insurance_number",
    "NINo": "national_insurance_number",
    "Works / Payroll Number": "payroll_number",
    "Works/Payroll Number": "payroll_number",
    "Final Tax Code": "tax_code",
    "NIC Table Letter": "nic_table_letter",
    "Employer Name": "employer_name",
    "Employer Address": "employer_address",
    "Employer PAYE Reference": "employer_paye_reference",
    "Earnings at the LEL": "earnings_at_lel",
    "Earnings at the Lower Earnings Limit (LEL)": "earnings_at_lel",
    "Earnings LEL to PT": "earnings_lel_to_pt",
    "Earnings LEL to Primary Threshold (PT)": "earnings_lel_to_pt",
    "Earnings PT to UEL": "earnings_pt_to_uel",
    "Earnings PT to Upper Earnings Limit (UEL)": "earnings_pt_to_uel",
    "Employee's Contributions Due": "employee_national_insurance",
    "Statutory Maternity Pay (SMP)": "statutory_maternity_pay",
    "Statutory Paternity Pay (SPP)": "statutory_paternity_pay",
    "Statutory Adoption Pay (SAP)": "statutory_adoption_pay",
    "Shared Parental Pay (ShPP)": "shared_parental_pay",
    "Student Loan Deductions (Plan 1/2/4)": "student_loan_deductions",
    "Postgraduate Loan Deductions": "postgraduate_loan_deductions",
}

MONEY_FIELDS = {
    "earnings_at_lel",
    "earnings_lel_to_pt",
    "earnings_pt_to_uel",
    "employee_national_insurance",
    "statutory_maternity_pay",
    "statutory_paternity_pay",
    "statutory_adoption_pay",
    "shared_parental_pay",
    "student_loan_deductions",
    "postgraduate_loan_deductions",
}


def _require(module: str, install_hint: str) -> Any:
    try:
        return importlib.import_module(module)
    except ImportError as error:
        raise RuntimeError(f"Missing optional dependency '{module}'. Install it with: {install_hint}") from error


def _read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        document = ElementTree.fromstring(archive.read("word/document.xml"))
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs = ["".join(node.text or "" for node in paragraph.iter(f"{namespace}t"))
                  for paragraph in document.iter(f"{namespace}p")]
    return "\n".join(line for line in paragraphs if line.strip())


def _ocr_image(path: Path) -> str:
    image_module = _require("PIL.Image", "python3 -m pip install pillow pytesseract")
    ocr_module = _require("pytesseract", "python3 -m pip install pillow pytesseract")
    try:
        with image_module.open(path) as image:
            text = ocr_module.image_to_string(image, config="--psm 4")
            if "P60" not in text.upper():
                return text
            width, height = image.size
            employee_panel = image.crop((width * 0.17, height * 0.18, width * 0.41, height * 0.86))
            employee_text = ocr_module.image_to_string(employee_panel.resize((employee_panel.width * 3, employee_panel.height * 3)), config="--psm 6")
            return f"{employee_text}\n{text}"
    except ocr_module.TesseractNotFoundError as error:
        raise RuntimeError("Tesseract is not installed. On macOS run: brew install tesseract") from error


def _read_pdf(path: Path) -> tuple[str, str]:
    pypdf = _require("pypdf", "python3 -m pip install pypdf pdf2image pillow pytesseract")
    text = "\n".join(page.extract_text() or "" for page in pypdf.PdfReader(path).pages).strip()
    if text:
        return text, "pdf_text"

    pdf2image = _require("pdf2image", "python3 -m pip install pdf2image pillow pytesseract")
    ocr_module = _require("pytesseract", "python3 -m pip install pdf2image pillow pytesseract")
    try:
        pages = pdf2image.convert_from_path(path)
    except Exception as error:
        raise RuntimeError("Could not render scanned PDF. Install Poppler: brew install poppler") from error
    try:
        return "\n".join(ocr_module.image_to_string(page) for page in pages), "ocr_pdf"
    except ocr_module.TesseractNotFoundError as error:
        raise RuntimeError("Tesseract is not installed. On macOS run: brew install tesseract") from error


def read_document(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8"), "text"
    if suffix == ".docx":
        return _read_docx(path), "docx"
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix in {".png", ".jpg", ".jpeg"}:
        return _ocr_image(path), "ocr_image"
    raise ValueError(f"Unsupported file type: {suffix or '<none>'}")


def _normalise_label(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def _text_value(text: str, label: str) -> str | None:
    match = re.search(rf"(?m)^[^\w\n]*{re.escape(label)}\s*[:.]\s*(?:\n\s*)?(.+?)\s*$", text)
    return match.group(1).strip() if match else None


def _money(value: str | None) -> float | None:
    if not value:
        return None
    cleaned = value.replace(",", "").replace("£", "").strip()
    return float(cleaned) if re.fullmatch(r"-?\d+(?:\.\d{1,2})?", cleaned) else None


def _national_insurance_number(value: str) -> str:
    compact = re.sub(r"\s+", "", value.upper())
    match = re.search(r"([A-Z]{2})(\d{2})(\d{2})(\d{2})([A-Z])", compact)
    return " ".join(match.groups()) if match else value


def extract_fields(text: str) -> dict[str, Any]:
    """Return only values that appear in the source text; unknown values are null."""
    fields: dict[str, Any] = dict.fromkeys(FIELD_NAMES)
    fields["other_fields"] = {}

    for label, key in LABEL_FIELDS.items():
        value = _text_value(text, label)
        if value is not None and fields[key] is None:
            if key == "national_insurance_number":
                fields[key] = _national_insurance_number(value)
            else:
                fields[key] = _money(value) if key in MONEY_FIELDS else value

    for source_label, (pay_key, tax_key) in PAY_ROWS.items():
        match = re.search(
            rf"(?m)^\s*{re.escape(source_label)}\s*:?\s*(?:\n\s*)?([0-9,]+\.\d{{2}})\s*(?:\n\s*)?([0-9,]+\.\d{{2}})",
            text,
        )
        if match:
            fields[pay_key] = _money(match.group(1))
            fields[tax_key] = _money(match.group(2))

    tax_year = re.search(r"(?i)TAX\s+YEAR\s+TO[\s\S]{0,120}?([0-9]{1,2}\s+[A-Z]+\s+[0-9]{4})", text)
    if tax_year:
        fields["tax_year_end"] = tax_year.group(1).title()

    if fields["forenames"] and fields["surname"]:
        fields["full_name"] = f"{fields['forenames']} {fields['surname']}"

    payslip_patterns = {
        "employee_name": r"(?m)^\s*Employee Name\s*$\s*^\s*(.+?)\s*$",
        "employee_number": r"(?m)^\s*Employee No\.\s*$\s*^\s*(\S+)\s*$",
        "pay_date": r"(?m)^\s*Pay Date:\s*(\S+)\s*$",
        "national_insurance_number": r"(?m)^\s*NI Number\s*$\s*^\s*([A-Z]{2}\d{6}[A-Z])\s*$",
        "tax_code": r"(?m)^\s*Tax Code\s*$\s*^\s*(.+?)\s*$",
        "ni_category": r"(?m)^\s*NI Category\s*$\s*^\s*([A-Z])\s*$",
    }
    for key, pattern in payslip_patterns.items():
        match = re.search(pattern, text)
        if match:
            fields[key] = match.group(1).strip()

    tax_block = re.search(
        r"(?ms)^\s*NI Number\s*$\s*^\s*NI Category\s*$\s*^\s*(\d+)\s*$\s*^\s*(.+?)\s*$\s*^\s*([A-Z]{2}\d{6}[A-Z])\s*$\s*^\s*([A-Z])\s*$",
        text,
    )
    if tax_block:
        fields["tax_period"] = tax_block.group(1)
        fields["tax_code"] = tax_block.group(2).strip()
        fields["national_insurance_number"] = tax_block.group(3)
        fields["ni_category"] = tax_block.group(4)

    for label, key in YTD_FIELDS.items():
        match = re.search(rf"(?m)^\s*{re.escape(label)}\s+([0-9,]+\.\d{{2}})\s*$", text)
        if match:
            fields[key] = _money(match.group(1))
    net_pay = re.search(r"(?m)^\s*PAY\s+([0-9,]+\.\d{2})\s*$", text)
    if net_pay:
        fields["net_pay"] = _money(net_pay.group(1))

    known_labels = {_normalise_label(label) for label in LABEL_FIELDS | PAY_ROWS.keys()}
    for label, value in re.findall(r"(?m)^\s*([^:\n]+):\s*(\S.*?)\s*$", text):
        normalized = _normalise_label(label)
        if normalized and normalized not in known_labels and value:
            fields["other_fields"][normalized] = value.strip()
    return fields


def _document_type(text: str) -> str:
    upper = text.upper()
    if "P60" in upper and "END OF YEAR" in upper:
        return "p60"
    if "PAYSLIP" in upper or "PAY SLIP" in upper:
        return "payslip"
    return "generic"


def extract_file(path: Path) -> dict[str, Any]:
    try:
        text, method = read_document(path)
        return {
            "source_file": str(path),
            "document_type": _document_type(text),
            "extraction_method": method,
            "fields": extract_fields(text),
            "warnings": [],
        }
    except Exception as error:
        return {"source_file": str(path), "error": str(error)}


def input_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    return sorted(path for path in input_path.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract local document fields into JSON.")
    parser.add_argument("input", nargs="?", default="file_types_samples", help="A file or directory to process")
    parser.add_argument("--output", default="extracted_data.json", help="Destination JSON file")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"Input path does not exist: {input_path}")

    results = [extract_file(path) for path in input_files(input_path)]
    output_path = Path(args.output)
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(results)} result(s) to {output_path}")
    return 1 if any("error" in result for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
