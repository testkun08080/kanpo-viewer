"""
Unit tests for API endpoints
"""
import pytest
import json
from unittest.mock import patch, Mock
from fastapi import status


class TestPdfApiEndpoints:
    """Test cases for PDF API endpoints"""

    def test_health_endpoint(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/api/pdf/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pdf_download"

    def test_root_endpoint(self, test_client):
        """Test root API endpoint"""
        response = test_client.get("/api/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Kanpo PDF Download API"
        assert "endpoints" in data
        assert "/api/pdf/health" in data["endpoints"]["health"]
        assert "/api/pdf/download" in data["endpoints"]["download"]

    @patch('app.api.pdf.pdf_service')
    def test_download_pdf_success(self, mock_service, test_client, temp_pdf_file):
        """Test successful PDF download"""
        # Mock the service to return our test file
        mock_service.download_pdf.return_value = (temp_pdf_file, 1234)

        request_data = {
            "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
            "filename": "test_document.pdf"
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/pdf"
        assert "test_document.pdf" in response.headers.get("content-disposition", "")

        # Verify service was called correctly
        mock_service.download_pdf.assert_called_once_with(
            request_data["url"],
            request_data["filename"]
        )

    @patch('app.api.pdf.pdf_service')
    def test_download_pdf_without_filename(self, mock_service, test_client, temp_pdf_file):
        """Test PDF download without specifying filename"""
        mock_service.download_pdf.return_value = (temp_pdf_file, 1234)

        request_data = {
            "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/pdf"

        # Verify service was called with None filename
        mock_service.download_pdf.assert_called_once_with(
            request_data["url"],
            None
        )

    def test_download_pdf_invalid_url(self, test_client):
        """Test PDF download with invalid URL"""
        request_data = {
            "url": "not-a-valid-url",
            "filename": "test.pdf"
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.api.pdf.pdf_service')
    def test_download_pdf_service_error(self, mock_service, test_client):
        """Test PDF download when service raises error"""
        mock_service.download_pdf.side_effect = ValueError("File too large")

        request_data = {
            "url": "https://example.com/large.pdf"
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "File too large" in data["detail"]

    @patch('app.api.pdf.pdf_service')
    def test_download_pdf_unexpected_error(self, mock_service, test_client):
        """Test PDF download with unexpected error"""
        mock_service.download_pdf.side_effect = Exception("Unexpected error")

        request_data = {
            "url": "https://example.com/document.pdf"
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["detail"] == "PDF download failed"

    def test_download_pdf_missing_url(self, test_client):
        """Test PDF download without URL"""
        request_data = {
            "filename": "test.pdf"
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_download_pdf_empty_request(self, test_client):
        """Test PDF download with empty request"""
        response = test_client.post("/api/pdf/download", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_download_pdf_invalid_json(self, test_client):
        """Test PDF download with invalid JSON"""
        response = test_client.post(
            "/api/pdf/download",
            data="invalid json",
            headers={"content-type": "application/json"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.api.pdf.pdf_service')
    def test_background_cleanup_called(self, mock_service, test_client, temp_pdf_file):
        """Test that background cleanup is scheduled"""
        mock_service.download_pdf.return_value = (temp_pdf_file, 1234)

        request_data = {
            "url": "https://example.com/document.pdf"
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK

        # Note: Background tasks are executed after response,
        # so we can't directly test cleanup call in this context


class TestApiValidation:
    """Test API request validation"""

    def test_url_validation_scheme(self, test_client):
        """Test URL scheme validation"""
        request_data = {
            "url": "ftp://example.com/file.pdf"
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        # Pydantic HttpUrl should reject non-HTTP(S) schemes
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_filename_type_validation(self, test_client):
        """Test filename type validation"""
        request_data = {
            "url": "https://example.com/document.pdf",
            "filename": 123  # Should be string
        }

        response = test_client.post(
            "/api/pdf/download",
            json=request_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY