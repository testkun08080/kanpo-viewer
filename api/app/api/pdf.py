from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import FileResponse
import logging
import os


from ..schemas.pdf import PdfDownloadRequest
from ..services.simple_pdf_service import SimplePdfDownloadService
from ..core.security import verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter()
pdf_service = SimplePdfDownloadService()


async def cleanup_file(file_path: str):
    """バックグラウンドでファイルをクリーンアップ"""
    pdf_service.cleanup_temp_file(file_path)


@router.post("/download", response_class=FileResponse)
async def download_pdf(
    request: PdfDownloadRequest, background_tasks: BackgroundTasks, authenticated: bool = Depends(verify_api_key)
):
    """
    PDFをダウンロードしてクライアントに返すAPI

    Args:
        request: PDFダウンロードリクエスト（URL、ファイル名）
        background_tasks: バックグラウンドタスク（ファイルクリーンアップ用）

    Returns:
        FileResponse: PDFファイル
    """
    try:
        # PDFをダウンロード
        temp_file_path, file_size = pdf_service.download_pdf(str(request.url), request.filename)

        # ファイル名の決定（リクエストで指定されているか、サービスで決定されたもの）
        filename = request.filename or os.path.basename(temp_file_path)
        if not filename.endswith(".pdf"):
            filename += ".pdf"

        # バックグラウンドでファイルをクリーンアップするタスクを追加
        background_tasks.add_task(cleanup_file, temp_file_path)

        logger.info(f"Serving PDF file: {filename}, size: {file_size} bytes")

        # PDFファイルをクライアントに返す
        return FileResponse(
            path=temp_file_path,
            filename=filename,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}", "Content-Length": str(file_size)},
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        raise HTTPException(status_code=500, detail="PDF download failed")


@router.get("/download")
async def download_pdf(background_tasks: BackgroundTasks, url: str = Query(...), filename: str = Query(None)):
    try:
        temp_file_path, file_size = pdf_service.download_pdf(url, filename)
        if not filename:
            filename = os.path.basename(temp_file_path)
        if not filename.endswith(".pdf"):
            filename += ".pdf"

        background_tasks.add_task(os.remove, temp_file_path)

        return FileResponse(
            path=temp_file_path,
            filename=filename,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}", "Content-Length": str(file_size)},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="PDF download failed")


@router.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "service": "pdf_download"}
