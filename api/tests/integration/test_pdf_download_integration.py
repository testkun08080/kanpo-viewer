"""
Integration tests for PDF download functionality
"""
import pytest
import requests
import tempfile
import os
from urllib.parse import urlparse


class TestPdfDownloadIntegration:
    """Integration tests that use real HTTP requests"""

    @pytest.mark.integration
    def test_download_real_pdf(self, test_client):
        """Test downloading a real PDF from the internet"""
        # Use a reliable test PDF
        request_data = {
            "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
            "filename": "integration_test.pdf"
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "integration_test.pdf" in response.headers.get("content-disposition", "")

        # Verify we got actual PDF content
        content = response.content
        assert content.startswith(b"%PDF")
        assert len(content) > 1000  # Should be a reasonable size

    @pytest.mark.integration
    def test_download_without_filename(self, test_client):
        """Test downloading without specifying filename"""
        request_data = {
            "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

        # Should have a default filename
        content_disposition = response.headers.get("content-disposition", "")
        assert ".pdf" in content_disposition

    @pytest.mark.integration
    def test_download_nonexistent_url(self, test_client):
        """Test downloading from non-existent URL"""
        request_data = {
            "url": "https://httpbin.org/status/404"
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        # Should return an error
        assert response.status_code in [400, 500]

    @pytest.mark.integration
    def test_download_non_pdf_content(self, test_client):
        """Test downloading non-PDF content"""
        request_data = {
            "url": "https://httpbin.org/json",
            "filename": "not_a_pdf.pdf"
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        # Should still work but may trigger content type warning
        # The service downloads any content if the URL responds
        assert response.status_code == 200

    @pytest.mark.integration
    def test_timeout_handling(self, test_client):
        """Test timeout handling with slow server"""
        # httpbin.org/delay/X delays response by X seconds
        request_data = {
            "url": "https://httpbin.org/delay/35",  # Exceeds 30s timeout
            "filename": "timeout_test.pdf"
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        # Should timeout and return error
        assert response.status_code in [400, 500]

    @pytest.mark.integration
    def test_health_endpoint_integration(self, test_client):
        """Test health endpoint in integration context"""
        response = test_client.get("/api/pdf/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pdf_download"


class TestPdfServiceIntegration:
    """Integration tests for the PDF service directly"""

    @pytest.mark.integration
    def test_service_download_real_pdf(self):
        """Test the service can download a real PDF"""
        from app.services.simple_pdf_service import SimplePdfDownloadService

        service = SimplePdfDownloadService()
        url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

        try:
            temp_path, size = service.download_pdf(url, "test_download.pdf")

            # Verify file exists and has content
            assert os.path.exists(temp_path)
            assert size > 0

            # Verify it's a PDF
            with open(temp_path, 'rb') as f:
                content = f.read(4)
                assert content == b'%PDF'

        finally:
            # Cleanup
            if 'temp_path' in locals() and os.path.exists(temp_path):
                service.cleanup_temp_file(temp_path)

    @pytest.mark.integration
    def test_service_file_size_limit(self):
        """Test file size limiting with a small limit"""
        from app.services.simple_pdf_service import SimplePdfDownloadService

        service = SimplePdfDownloadService()
        service.max_file_size = 1024  # Set very small limit

        url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"

        with pytest.raises(ValueError, match="File size exceeded limit"):
            service.download_pdf(url)

    @pytest.mark.integration
    def test_service_invalid_url(self):
        """Test service with invalid URL"""
        from app.services.simple_pdf_service import SimplePdfDownloadService
        import urllib.error

        service = SimplePdfDownloadService()
        url = "https://nonexistent-domain-12345.com/file.pdf"

        with pytest.raises(urllib.error.URLError):
            service.download_pdf(url)


class TestEndToEndWorkflow:
    """End-to-end workflow tests"""

    @pytest.mark.integration
    def test_complete_download_workflow(self, test_client):
        """Test complete download workflow from request to cleanup"""
        # 1. Health check
        health_response = test_client.get("/api/pdf/health")
        assert health_response.status_code == 200

        # 2. Download PDF
        download_request = {
            "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
            "filename": "workflow_test.pdf"
        }

        download_response = test_client.post(
            "/api/pdf/download",
            json=download_request
        )

        assert download_response.status_code == 200
        assert len(download_response.content) > 0

        # 3. Verify content
        content = download_response.content
        assert content.startswith(b"%PDF")

        # Background cleanup happens automatically
        # We can't directly test it in this context

    @pytest.mark.integration
    def test_api_info_endpoint(self, test_client):
        """Test API information endpoint"""
        response = test_client.get("/api/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert "health" in data["endpoints"]
        assert "download" in data["endpoints"]