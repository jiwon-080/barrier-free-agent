import datetime
from pathlib import Path

try:
    import pdfplumber
    _PDFPLUMBER = True
except ImportError:
    _PDFPLUMBER = False

try:
    import pypdf
    _PYPDF = True
except ImportError:
    _PYPDF = False


def pdf_to_markdown(uploaded_file, domain: str) -> str:
    """PDF 파일 객체(Streamlit UploadedFile)를 마크다운 문자열로 변환."""
    text = _extract_text(uploaded_file)
    today = datetime.date.today().isoformat()
    title = Path(uploaded_file.name).stem

    return f"""---
title: {title}
domain: {domain}
tags: []
source: {uploaded_file.name}
last_updated: {today}
importance: medium
---

{text.strip()}

## 관련 항목
"""


def _extract_text(uploaded_file) -> str:
    raw = uploaded_file.read()

    if _PDFPLUMBER:
        import io
        import pdfplumber
        pages = []
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
        return "\n\n".join(pages)

    if _PYPDF:
        import io
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(raw))
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n\n".join(pages)

    return "⚠️ PDF 파싱 라이브러리 없음. `pip install pdfplumber` 또는 `pip install pypdf` 실행 후 재시도하세요."
