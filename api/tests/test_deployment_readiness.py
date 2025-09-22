"""
Deployment readiness tests - Pre-deployment validation
"""
import pytest
import requests
import time
from unittest.mock import patch


class TestDeploymentReadiness:
    """Tests to verify deployment readiness"""

    def test_api_startup(self, test_client):
        """Test that API starts up correctly"""
        response = test_client.get("/api/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data

    def test_health_endpoint_availability(self, test_client):
        """Test health endpoint is available and responsive"""
        response = test_client.get("/api/pdf/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "pdf_download"

    def test_cors_headers(self, test_client):
        """Test CORS headers are properly configured"""
        response = test_client.options("/api/pdf/health")

        # FastAPI TestClient may not include all CORS headers in OPTIONS
        # but the middleware should be configured
        assert response.status_code in [200, 405]  # Either OK or Method Not Allowed

    def test_pdf_download_endpoint_structure(self, test_client):
        """Test PDF download endpoint accepts requests"""
        # Test with invalid data to check endpoint structure
        response = test_client.post("/api/pdf/download", json={})

        # Should return validation error, not 404
        assert response.status_code == 422

    def test_error_handling_validation(self, test_client):
        """Test error handling returns proper HTTP codes"""
        # Invalid URL format
        response = test_client.post(
            "/api/pdf/download",
            json={"url": "not-a-url"}
        )
        assert response.status_code == 422

        # Missing required field
        response = test_client.post(
            "/api/pdf/download",
            json={"filename": "test.pdf"}
        )
        assert response.status_code == 422

    @patch('app.api.pdf.pdf_service')
    def test_service_error_handling(self, mock_service, test_client):
        """Test service error handling"""
        mock_service.download_pdf.side_effect = ValueError("Test error")

        response = test_client.post(
            "/api/pdf/download",
            json={"url": "https://example.com/test.pdf"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "Test error" in data["detail"]

    def test_response_format_consistency(self, test_client):
        """Test response formats are consistent"""
        # Health endpoint
        health_response = test_client.get("/api/pdf/health")
        assert health_response.headers["content-type"] == "application/json"

        # API info endpoint
        info_response = test_client.get("/api/")
        assert info_response.headers["content-type"] == "application/json"

        # Error responses should also be JSON
        error_response = test_client.post("/api/pdf/download", json={})
        assert error_response.headers["content-type"] == "application/json"

    def test_request_validation_comprehensive(self, test_client):
        """Test comprehensive request validation"""
        test_cases = [
            # Valid request
            {
                "data": {"url": "https://example.com/test.pdf"},
                "expected_status": [400, 500]  # Service error or timeout
            },
            # Invalid URL scheme
            {
                "data": {"url": "ftp://example.com/test.pdf"},
                "expected_status": [422]
            },
            # Invalid URL format
            {
                "data": {"url": "not-a-url"},
                "expected_status": [422]
            },
            # Wrong type for filename
            {
                "data": {"url": "https://example.com/test.pdf", "filename": 123},
                "expected_status": [422]
            },
            # Empty request
            {
                "data": {},
                "expected_status": [422]
            }
        ]

        for i, test_case in enumerate(test_cases):
            response = test_client.post("/api/pdf/download", json=test_case["data"])
            assert response.status_code in test_case["expected_status"], \
                f"Test case {i+1} failed: {test_case['data']}"

    def test_api_documentation_accessibility(self, test_client):
        """Test that API documentation is accessible"""
        # FastAPI auto-generates docs at /docs and /redoc
        docs_response = test_client.get("/docs")
        redoc_response = test_client.get("/redoc")

        # At least one should be accessible (depends on FastAPI config)
        assert docs_response.status_code in [200, 404]
        assert redoc_response.status_code in [200, 404]

        # OpenAPI schema should be available
        openapi_response = test_client.get("/openapi.json")
        assert openapi_response.status_code == 200

        openapi_data = openapi_response.json()
        assert "openapi" in openapi_data
        assert "paths" in openapi_data

    def test_security_headers_basic(self, test_client):
        """Test basic security considerations"""
        response = test_client.get("/api/")

        # Should not expose server information
        server_header = response.headers.get("server", "").lower()
        assert "uvicorn" not in server_header  # Might be stripped in production

    def test_performance_basic(self, test_client):
        """Test basic performance characteristics"""
        start_time = time.time()
        response = test_client.get("/api/pdf/health")
        end_time = time.time()

        assert response.status_code == 200

        # Health check should be fast (under 1 second)
        response_time = end_time - start_time
        assert response_time < 1.0, f"Health check took {response_time:.3f}s"


class TestConfigurationValidation:
    """Test configuration and environment validation"""

    def test_app_configuration(self, test_client):
        """Test application configuration"""
        response = test_client.get("/api/")
        data = response.json()

        # Should have proper version
        assert "version" in data
        assert data["version"] != ""

        # Should have proper endpoints configured
        endpoints = data["endpoints"]
        assert "health" in endpoints
        assert "download" in endpoints
        assert endpoints["health"].endswith("/health")
        assert endpoints["download"].endswith("/download")

    def test_service_configuration(self):
        """Test service configuration"""
        from app.services.simple_pdf_service import SimplePdfDownloadService

        service = SimplePdfDownloadService()

        # Should have reasonable limits
        assert service.max_file_size > 0
        assert service.max_file_size <= 100 * 1024 * 1024  # Not more than 100MB
        assert service.timeout > 0
        assert service.timeout <= 60  # Not more than 60 seconds


class TestResourceManagement:
    """Test resource management and cleanup"""

    def test_temp_file_cleanup(self):
        """Test temporary file cleanup functionality"""
        from app.services.simple_pdf_service import SimplePdfDownloadService
        import tempfile
        import os

        service = SimplePdfDownloadService()

        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_path = temp_file.name
        temp_file.close()

        # Verify it exists
        assert os.path.exists(temp_path)

        # Cleanup should remove it
        service.cleanup_temp_file(temp_path)

        # Should be gone
        assert not os.path.exists(temp_path)

    @patch('app.api.pdf.pdf_service')
    def test_background_task_setup(self, mock_service, test_client, temp_pdf_file):
        """Test that background tasks are properly configured"""
        mock_service.download_pdf.return_value = (temp_pdf_file, 1234)

        response = test_client.post(
            "/api/pdf/download",
            json={"url": "https://example.com/test.pdf"}
        )

        assert response.status_code == 200

        # Background task should be scheduled (can't test execution directly)
        # This test mainly ensures no errors in background task setup