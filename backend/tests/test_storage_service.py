import pytest
import os
import time
from uuid import uuid4
from app.services.storage_service import StorageService, StorageError


@pytest.fixture
def storage_service_instance(tmp_path):
    """Provides an isolated StorageService instance pointing to a temporary directory."""
    return StorageService(local_storage=True, base_dir=str(tmp_path))


@pytest.mark.asyncio
async def test_storage_upload_and_download(storage_service_instance):
    test_key = f"tests/{uuid4()}/sample.mp4"
    sample_data = b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41"

    # Upload
    signed_url = await storage_service_instance.upload(sample_data, test_key, content_type="video/mp4")
    assert "/api/v1/storage/media?key=" in signed_url
    assert "sig=" in signed_url

    # Check exists
    exists = await storage_service_instance.exists(test_key)
    assert exists is True

    # Download
    downloaded = await storage_service_instance.download(test_key)
    assert downloaded == sample_data


@pytest.mark.asyncio
async def test_storage_delete(storage_service_instance):
    test_key = f"tests/{uuid4()}/to_delete.png"
    sample_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

    await storage_service_instance.upload(sample_data, test_key, content_type="image/png")
    assert await storage_service_instance.exists(test_key) is True

    deleted = await storage_service_instance.delete(test_key)
    assert deleted is True
    assert await storage_service_instance.exists(test_key) is False


@pytest.mark.asyncio
async def test_storage_path_traversal_prevention(storage_service_instance):
    with pytest.raises(StorageError) as exc_info:
        await storage_service_instance.upload(b"malicious", "../../../etc/passwd", content_type="text/plain")
    assert "Invalid object key" in str(exc_info.value) or "traversal" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_storage_mime_type_validation(storage_service_instance):
    with pytest.raises(StorageError) as exc_info:
        storage_service_instance.validate_file(b"bad binary", content_type="application/x-executable")
    assert "not an authorized media format" in str(exc_info.value)


@pytest.mark.asyncio
async def test_signed_url_verification(storage_service_instance):
    test_key = "users/123/projects/456/renders/job.mp4"
    url = storage_service_instance.generate_signed_url(test_key, expires_in=60)
    assert "sig=" in url and "expires=" in url

    # Parse query params
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    expires = int(params["expires"][0])
    signature = params["sig"][0]

    # Valid signature check
    assert storage_service_instance.verify_signed_url(test_key, expires, signature) is True

    # Tampered key should fail
    assert storage_service_instance.verify_signed_url("tampered_key.mp4", expires, signature) is False

    # Tampered signature should fail
    assert storage_service_instance.verify_signed_url(test_key, expires, "tampered_signature") is False

    # Expired timestamp should fail
    past_timestamp = int(time.time()) - 10
    assert storage_service_instance.verify_signed_url(test_key, past_timestamp, signature) is False


@pytest.mark.asyncio
async def test_storage_usage_calculation(storage_service_instance):
    test_key = f"tests/{uuid4()}/data.mp4"
    data = b"0" * 1024  # 1 KB
    await storage_service_instance.upload(data, test_key, content_type="video/mp4")

    usage = storage_service_instance.calculate_storage_usage()
    assert usage["total_files"] >= 1
    assert usage["total_bytes"] >= 1024
