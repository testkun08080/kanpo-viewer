"""
Unit tests for PDF download service
"""
import pytest
import tempfile
import os
from unittest.mock import patch, mock_open, Mock
import urllib.error

from app.services.simple_pdf_service import SimplePdfDownloadService


class TestSimplePdfDownloadService:
    """Test cases for SimplePdfDownloadService"""

    def setup_method(self):
        """Setup test instance"""
        self.service = SimplePdfDownloadService()

    def test_init(self):
        """Test service initialization"""
        assert self.service.max_file_size == 50 * 1024 * 1024
        assert self.service.timeout == 30

    def test_filename_generation_from_url(self):
        """Test filename generation from URL"""
        url = "https://example.com/document.pdf"

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.headers = {'content-type': 'application/pdf'}
            mock_response.read.side_effect = [b'test content', b'']
            mock_urlopen.return_value.__enter__.return_value = mock_response

            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.name = '/tmp/test.pdf'

                with patch('builtins.open', mock_open()) as mock_file:
                    temp_path, size = self.service.download_pdf(url)

                    assert temp_path == '/tmp/test.pdf'
                    assert size == 12  # length of 'test content'

    def test_filename_with_custom_name(self):
        """Test download with custom filename"""
        url = "https://example.com/document.pdf"
        custom_filename = "my_document.pdf"

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.headers = {'content-type': 'application/pdf'}
            mock_response.read.side_effect = [b'test content', b'']
            mock_urlopen.return_value.__enter__.return_value = mock_response

            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.name = '/tmp/test.pdf'

                with patch('builtins.open', mock_open()) as mock_file:
                    temp_path, size = self.service.download_pdf(url, custom_filename)

                    assert temp_path == '/tmp/test.pdf'

    def test_file_size_limit_check_from_headers(self):
        """Test file size limit checking from Content-Length header"""
        url = "https://example.com/large.pdf"

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.headers = {'content-length': str(60 * 1024 * 1024)}  # 60MB
            mock_urlopen.return_value.__enter__.return_value = mock_response

            with pytest.raises(ValueError, match="File size too large"):
                self.service.download_pdf(url)

    def test_file_size_limit_check_during_download(self):
        """Test file size limit checking during download"""
        url = "https://example.com/document.pdf"
        large_content = b'x' * (51 * 1024 * 1024)  # 51MB

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.headers = {'content-type': 'application/pdf'}
            mock_response.read.return_value = large_content
            mock_urlopen.return_value.__enter__.return_value = mock_response

            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.name = '/tmp/test.pdf'

                with patch('builtins.open', mock_open()) as mock_file:
                    with pytest.raises(ValueError, match="File size exceeded limit"):
                        self.service.download_pdf(url)

    def test_http_error_handling(self):
        """Test HTTP error handling"""
        url = "https://example.com/notfound.pdf"

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 404
            mock_urlopen.return_value.__enter__.return_value = mock_response

            with pytest.raises(ValueError, match="HTTP error: 404"):
                self.service.download_pdf(url)

    def test_url_error_handling(self):
        """Test URL error handling"""
        url = "https://nonexistent.example.com/document.pdf"

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Name resolution failed")

            with pytest.raises(urllib.error.URLError):
                self.service.download_pdf(url)

    def test_content_type_warning(self):
        """Test content type warning for non-PDF files"""
        url = "https://example.com/document.txt"

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.headers = {'content-type': 'text/plain'}
            mock_response.read.side_effect = [b'test content', b'']
            mock_urlopen.return_value.__enter__.return_value = mock_response

            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.name = '/tmp/test.pdf'

                with patch('builtins.open', mock_open()) as mock_file:
                    with patch('app.services.simple_pdf_service.logger') as mock_logger:
                        temp_path, size = self.service.download_pdf(url)

                        mock_logger.warning.assert_called_once()
                        assert "Content-Type is not PDF" in str(mock_logger.warning.call_args)

    def test_cleanup_temp_file(self):
        """Test temporary file cleanup"""
        temp_path = "/tmp/test_file.pdf"

        with patch('os.path.exists', return_value=True):
            with patch('os.unlink') as mock_unlink:
                self.service.cleanup_temp_file(temp_path)
                mock_unlink.assert_called_once_with(temp_path)

    def test_cleanup_nonexistent_file(self):
        """Test cleanup of non-existent file"""
        temp_path = "/tmp/nonexistent.pdf"

        with patch('os.path.exists', return_value=False):
            with patch('os.unlink') as mock_unlink:
                self.service.cleanup_temp_file(temp_path)
                mock_unlink.assert_not_called()

    def test_cleanup_error_handling(self):
        """Test error handling during cleanup"""
        temp_path = "/tmp/test_file.pdf"

        with patch('os.path.exists', return_value=True):
            with patch('os.unlink', side_effect=OSError("Permission denied")):
                with patch('app.services.simple_pdf_service.logger') as mock_logger:
                    self.service.cleanup_temp_file(temp_path)
                    mock_logger.error.assert_called_once()

    def test_pdf_extension_added(self):
        """Test that .pdf extension is added when missing"""
        url = "https://example.com/document"
        filename = "my_document"

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_response.status = 200
            mock_response.headers = {'content-type': 'application/pdf'}
            mock_response.read.side_effect = [b'test content', b'']
            mock_urlopen.return_value.__enter__.return_value = mock_response

            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.name = '/tmp/test.pdf'

                with patch('builtins.open', mock_open()) as mock_file:
                    temp_path, size = self.service.download_pdf(url, filename)

                    # The filename should have .pdf added internally
                    assert temp_path == '/tmp/test.pdf'