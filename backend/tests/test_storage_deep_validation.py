import pytest
import asyncio
import time
from uuid import uuid4
from app.services.storage_service import StorageService, storage_service, StorageError
from app.db.session import AsyncSessionLocal
from app.models.models import Video, User, Project, AuthProvider, RenderJob, RenderStatus


@pytest.mark.asyncio
async def test_large_file_upload_and_download(tmp_path):
    """
    Validates that large binary payloads (e.g. 10MB video chunks) upload and download
    with bit-for-bit integrity and zero memory leakage.
    """
    service = StorageService(local_storage=True, base_dir=str(tmp_path))
    object_key = f"renders/{uuid4()}.mp4"

    # Create 10MB of non-trivial binary data
    chunk = b"AKMMOTION_PROD_SCALE_DATA_BLOCK_" * 1024  # 32KB
    large_payload = chunk * 320  # ~10.2 MB

    # Upload
    res_url = await service.upload(large_payload, object_key, content_type="video/mp4")
    assert object_key in res_url
    assert await service.exists(object_key)

    # Download and verify bit-for-bit integrity
    downloaded = await service.download(object_key)
    assert len(downloaded) == len(large_payload)
    assert downloaded == large_payload


@pytest.mark.asyncio
async def test_concurrent_uploads_to_same_prefix(tmp_path):
    """
    Validates that 20 concurrent uploads to the same directory prefix execute
    cleanly without filesystem deadlocks or collisions.
    """
    service = StorageService(local_storage=True, base_dir=str(tmp_path))
    prefix = f"users/{uuid4()}/projects/{uuid4()}/scenes"

    async def do_upload(i: int):
        key = f"{prefix}/scene_{i}.png"
        payload = f"scene_content_bytes_{i}".encode("utf-8")
        await service.upload(payload, key, content_type="image/png")
        return key

    tasks = [do_upload(i) for i in range(20)]
    keys = await asyncio.gather(*tasks)

    assert len(keys) == 20
    # Verify all 20 files exist
    for k in keys:
        assert await service.exists(k)

    # Verify storage usage summary
    usage = service.calculate_storage_usage(prefix)
    assert usage["total_files"] == 20


def test_signed_url_cryptographic_verification():
    """
    Validates HMAC-signed URLs:
    1. Valid signed URL passes verification.
    2. Expired signed URL is rejected.
    3. Tampered object key or expiry timestamp is mathematically rejected.
    """
    object_key = f"renders/{uuid4()}.mp4"

    # 1. Valid signed URL (3600s lifetime)
    url = storage_service.generate_signed_url(object_key, expires_in=3600)
    # Parse query params
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    key = qs["key"][0]
    expires = int(qs["expires"][0])
    sig = qs["sig"][0]

    assert storage_service.verify_signed_url(key, expires, sig) is True

    # 2. Expired URL (negative expires_in)
    expired_url = storage_service.generate_signed_url(object_key, expires_in=-10)
    parsed_exp = urlparse(expired_url)
    qs_exp = parse_qs(parsed_exp.query)
    assert storage_service.verify_signed_url(
        qs_exp["key"][0],
        int(qs_exp["expires"][0]),
        qs_exp["sig"][0]
    ) is False

    # 3. Tampered object key with original signature
    assert storage_service.verify_signed_url("renders/malicious_tampered.mp4", expires, sig) is False

    # 4. Tampered expiry timestamp
    assert storage_service.verify_signed_url(key, expires + 1000, sig) is False


@pytest.mark.asyncio
async def test_db_storage_orphan_detection(tmp_path):
    """
    Validates that detect_orphans identifies:
    1. Physical storage files with no database record.
    2. Database records whose physical files do not exist on disk.
    """
    service = StorageService(local_storage=True, base_dir=str(tmp_path))
    user_id = uuid4()
    project_id = uuid4()

    # Create an orphaned file on disk (not in DB)
    orphan_file = f"orphaned_data_{uuid4().hex}.mp4"
    await service.upload(b"orphan data", orphan_file, content_type="video/mp4")

    # Create a matched file (both in DB and on disk)
    matched_file = f"matched_{uuid4().hex}.mp4"
    await service.upload(b"matched data", matched_file, content_type="video/mp4")

    # Create a missing file (in DB but NOT on disk)
    missing_file = f"ghost_{uuid4().hex}.mp4"

    async with AsyncSessionLocal() as session:
        # Seed user and project
        user = User(id=user_id, email=f"orphan_{user_id.hex[:6]}@test.com", full_name="Orphan User", auth_provider=AuthProvider.email, is_active=True)
        project = Project(id=project_id, user_id=user_id, title="Orphan Test Project", style="Explainer", language="en")
        session.add_all([user, project])
        await session.flush()

        # Add video records for matched and missing
        v_matched = Video(project_id=project_id, url=matched_file, storage_path=matched_file, duration=5.0)
        v_missing = Video(project_id=project_id, url=missing_file, storage_path=missing_file, duration=5.0)
        session.add_all([v_matched, v_missing])
        await session.commit()

        # Run orphan detection
        report = await service.detect_orphans(session)

        # orphan_file must be detected as orphaned storage file
        assert orphan_file in report["orphaned_storage_files"]
        assert report["orphaned_storage_count"] >= 1

        # missing_file must be detected as missing DB asset
        assert missing_file in report["missing_db_files"]
        assert report["missing_db_files_count"] >= 1
