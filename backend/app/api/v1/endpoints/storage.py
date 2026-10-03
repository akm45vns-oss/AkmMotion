import os
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.services.storage_service import storage_service, StorageError

router = APIRouter(prefix="/storage", tags=["Storage & Media"])


@router.get("/media")
async def get_media_asset(
    key: str = Query(..., description="Storage object key"),
    expires: int = Query(..., description="Signature expiration timestamp"),
    sig: str = Query(..., description="HMAC-SHA256 signature")
):
    """
    Serves stored assets using cryptographically verified short-lived signed URLs.
    Validates HMAC-SHA256 signature, prevents path traversal, and checks expiration.
    """
    if not storage_service.verify_signed_url(key, expires, sig):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Signed media URL is invalid, tampered with, or expired."
        )

    try:
        exists = await storage_service.exists(key)
        if not exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requested asset not found in storage."
            )

        local_path = storage_service._get_local_path(key)
        metadata = await storage_service.get_metadata(key)

        return FileResponse(
            path=local_path,
            media_type=metadata.get("content_type", "application/octet-stream"),
            filename=os.path.basename(key),
            headers={"Accept-Ranges": "bytes"}
        )
    except StorageError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
