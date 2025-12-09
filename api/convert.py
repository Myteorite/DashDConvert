# api/convert.py
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from io import BytesIO
from docx import Document as DocxDocument
from PyPDF2 import PdfReader
from fpdf import FPDF
import tempfile
import shutil
import os
from pathlib import Path

router = APIRouter()

def docx_to_text(path: str) -> str:
    doc = DocxDocument(path)
    return "\n".join(p.text for p in doc.paragraphs)

def pdf_to_text(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def text_to_pdf_bytes(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.splitlines():
        pdf.multi_cell(0, 6, line)
    b = BytesIO()
    pdf.output(b)
    return b.getvalue()

def text_to_docx_bytes(text: str) -> bytes:
    doc = DocxDocument()
    for line in text.splitlines():
        doc.add_paragraph(line)
    b = BytesIO()
    doc.save(b)
    b.seek(0)
    return b.read()

@router.post("/convert")
async def convert(file: UploadFile = File(...), to_format: str = Form(...)):
    filename = Path(file.filename).name
    suffix = Path(filename).suffix.lower()

    with tempfile.TemporaryDirectory() as tmp:
        in_path = os.path.join(tmp, filename)
        with open(in_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # extract text
        if suffix == ".docx":
            text = docx_to_text(in_path)
        elif suffix == ".pdf":
            text = pdf_to_text(in_path)
        else:
            with open(in_path, "r", encoding="utf8", errors="ignore") as fr:
                text = fr.read()

        # output
        if to_format == "txt":
            out = text.encode()
            out_name = filename.replace(suffix, ".txt")
            media = "text/plain"

        elif to_format == "pdf":
            out = text_to_pdf_bytes(text)
            out_name = filename.replace(suffix, ".pdf")
            media = "application/pdf"

        elif to_format == "docx":
            out = text_to_docx_bytes(text)
            out_name = filename.replace(suffix, ".docx")
            media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        else:
            return {"error": "Format tidak didukung"}

        return StreamingResponse(BytesIO(out),
                                 media_type=media,
                                 headers={"Content-Disposition": f'attachment; filename="{out_name}"'})
