from tempfile import SpooledTemporaryFile

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from app.utils import validations


def make_upload(
    content: bytes,
    *,
    filename: str = "document.pdf",
    content_type: str = "application/pdf",
) -> UploadFile:
    file_object = SpooledTemporaryFile()
    file_object.write(content)
    file_object.seek(0)
    return UploadFile(
        file_object,
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


@pytest.mark.asyncio
async def test_pdf_validation_accepts_case_insensitive_extension_and_rewinds_stream():
    upload = make_upload(b"%PDF-1.7\ncontent\n%%EOF", filename="REPORT.PDF")

    assert await validations.is_valid_file(upload) is True
    assert upload.file.tell() == 0


@pytest.mark.asyncio
async def test_pdf_validation_rejects_non_pdf_extension_and_rewinds_stream():
    upload = make_upload(b"%PDF-1.7\n%%EOF", filename="document.txt")

    with pytest.raises(HTTPException, match="PDF file extension") as exc_info:
        await validations.is_valid_file(upload)

    assert exc_info.value.status_code == 400
    assert upload.file.tell() == 0


@pytest.mark.asyncio
async def test_pdf_validation_rejects_non_pdf_content_type_and_rewinds_stream():
    upload = make_upload(
        b"%PDF-1.7\n%%EOF",
        content_type="application/octet-stream",
    )

    with pytest.raises(HTTPException, match="content type must be application/pdf") as exc_info:
        await validations.is_valid_file(upload)

    assert exc_info.value.status_code == 400
    assert upload.file.tell() == 0


@pytest.mark.asyncio
async def test_pdf_validation_rejects_missing_pdf_signature_and_rewinds_stream():
    upload = make_upload(b"This is not a PDF")

    with pytest.raises(HTTPException, match="valid PDF signature") as exc_info:
        await validations.is_valid_file(upload)

    assert exc_info.value.status_code == 400
    assert upload.file.tell() == 0


@pytest.mark.asyncio
async def test_pdf_validation_rejects_files_over_configured_limit_and_rewinds_stream(monkeypatch):
    monkeypatch.setattr(validations, "MAX_PDF_SIZE_BYTES", 8, raising=False)
    upload = make_upload(b"%PDF-1234")

    with pytest.raises(HTTPException, match="maximum allowed size is 20 MB") as exc_info:
        await validations.is_valid_file(upload)

    assert exc_info.value.status_code == 413
    assert upload.file.tell() == 0
