from pydantic import BaseModel, HttpUrl
from typing import Optional


class PdfDownloadRequest(BaseModel):
    """PDFダウンロードリクエストスキーマ"""
    url: HttpUrl
    filename: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                "filename": "document.pdf"
            }
        }
    }