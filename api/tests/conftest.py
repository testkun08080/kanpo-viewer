"""
Test configuration and fixtures for Kanpo PDF API
"""
import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app


@pytest.fixture(scope="module")
def test_client():
    """
    Create a test client for the FastAPI application.
    Share a single client across the entire test module.
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture
def temp_pdf_file():
    """Create a temporary PDF file for testing"""
    # Simple PDF content (minimal valid PDF)
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj

xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
181
%%EOF"""

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix='.pdf',
        prefix='test_'
    )
    temp_file.write(pdf_content)
    temp_file.close()

    yield temp_file.name

    # Cleanup
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


@pytest.fixture
def sample_urls():
    """Sample URLs for testing"""
    return {
        "valid_pdf": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "invalid_url": "not-a-valid-url",
        "non_existent": "https://example.com/nonexistent.pdf"
    }


@pytest.fixture
def test_requests():
    """Sample test requests"""
    return {
        "valid_with_filename": {
            "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
            "filename": "test_document.pdf"
        },
        "valid_without_filename": {
            "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
        },
        "invalid_url": {
            "url": "not-a-url",
            "filename": "test.pdf"
        }
    }
