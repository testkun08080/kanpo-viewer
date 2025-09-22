import urllib.request
import tempfile
import os
from typing import Tuple, Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class SimplePdfDownloadService:
    """標準ライブラリのみを使用したシンプルなPDFダウンロードサービス"""

    def __init__(self):
        self.max_file_size = 50 * 1024 * 1024  # 50MB制限
        self.timeout = 30  # 30秒タイムアウト

    def download_pdf(self, url: str, filename: Optional[str] = None) -> Tuple[str, int]:
        """
        PDFをダウンロードして一時ファイルとして保存

        Args:
            url: ダウンロードするPDFのURL
            filename: ファイル名（指定がない場合はURLから推測）

        Returns:
            Tuple[str, int]: (一時ファイルパス, ファイルサイズ)

        Raises:
            ValueError: 無効なURLまたはファイルサイズ制限超過
            urllib.error.URLError: HTTP通信エラー
        """
        # ファイル名の決定
        if not filename:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename or not filename.endswith('.pdf'):
                filename = 'download.pdf'

        # .pdf拡張子がない場合は追加
        if not filename.endswith('.pdf'):
            filename += '.pdf'

        try:
            # HTTPリクエストの準備
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (compatible; PDF-Downloader/1.0)')

            # URLを開く
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                # レスポンスステータスチェック
                if response.status != 200:
                    raise ValueError(f"HTTP error: {response.status}")

                # Content-Typeチェック（可能な場合）
                content_type = response.headers.get('content-type', '')
                if content_type and 'pdf' not in content_type.lower():
                    logger.warning(f"Content-Type is not PDF: {content_type}")

                # ファイルサイズチェック
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.max_file_size:
                    raise ValueError(f"File size too large: {content_length} bytes")

                # 一時ファイルに保存
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix='.pdf',
                    prefix='pdf_download_'
                )

                total_size = 0
                try:
                    with open(temp_file.name, 'wb') as f:
                        while True:
                            chunk = response.read(8192)
                            if not chunk:
                                break
                            total_size += len(chunk)
                            if total_size > self.max_file_size:
                                raise ValueError(f"File size exceeded limit: {total_size} bytes")
                            f.write(chunk)

                    logger.info(f"PDF downloaded successfully: {filename}, size: {total_size} bytes")
                    return temp_file.name, total_size

                except Exception as e:
                    # エラーが発生した場合は一時ファイルを削除
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
                    raise e

        except urllib.error.URLError as e:
            logger.error(f"URL error downloading PDF from {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading PDF from {url}: {e}")
            raise

    def cleanup_temp_file(self, temp_file_path: str) -> None:
        """一時ファイルをクリーンアップ"""
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up temporary file {temp_file_path}: {e}")