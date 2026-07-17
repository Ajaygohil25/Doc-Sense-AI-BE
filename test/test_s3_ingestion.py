import asyncio
from pathlib import Path

import pytest

from app.rag import ingest as ingest_module


def run_executor_inline(monkeypatch):
    loop = asyncio.get_running_loop()

    def run_in_executor(_executor, callback, *args):
        future = loop.create_future()
        try:
            future.set_result(callback(*args))
        except Exception as error:
            future.set_exception(error)
        return future

    monkeypatch.setattr(loop, "run_in_executor", run_in_executor)


class FakeS3Service:
    def __init__(self, content: bytes = b"%PDF-1.7\n%%EOF", download_succeeds: bool = True):
        self.content = content
        self.download_succeeds = download_succeeds
        self.download_path = None
        self.object_name = None

    def download_file(self, object_name, file_path):
        self.object_name = object_name
        self.download_path = Path(file_path)
        if not self.download_succeeds:
            return False
        self.download_path.write_bytes(self.content)
        return True


@pytest.mark.asyncio
async def test_pdf_source_downloads_s3_object_to_temporary_file_and_cleans_it(monkeypatch):
    run_executor_inline(monkeypatch)
    fake_s3 = FakeS3Service()
    monkeypatch.setattr(ingest_module, "S3Service", lambda: fake_s3, raising=False)

    async with ingest_module.pdf_source(None, "uploads/document.pdf") as resolved_path:
        resolved = Path(resolved_path)
        assert resolved.exists()
        assert resolved.read_bytes() == fake_s3.content
        assert fake_s3.object_name == "uploads/document.pdf"

    assert fake_s3.download_path is not None
    assert not fake_s3.download_path.exists()


@pytest.mark.asyncio
async def test_pdf_source_cleans_temporary_file_when_s3_download_fails(monkeypatch):
    run_executor_inline(monkeypatch)
    fake_s3 = FakeS3Service(download_succeeds=False)
    monkeypatch.setattr(ingest_module, "S3Service", lambda: fake_s3, raising=False)

    with pytest.raises(RuntimeError, match="Failed to download PDF from S3"):
        async with ingest_module.pdf_source(None, "uploads/missing.pdf"):
            pass

    assert fake_s3.download_path is not None
    assert not fake_s3.download_path.exists()
