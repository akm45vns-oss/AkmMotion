import os
import socket
import ipaddress
import urllib.parse
from typing import Tuple, Optional, List
import httpx


class SSRFSecurityError(ValueError):
    """Raised when a download URL fails SSRF safety validation."""
    pass


class DownloadError(RuntimeError):
    """Raised when media download fails due to network, size, or HTTP error."""
    pass


def is_safe_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Strict SSRF validation:
    - Scheme must be http or https
    - Hostname must be present and resolve only to public IPv4/IPv6 addresses
    - Blocks RFC1918, loopback, link-local, multicast, cloud metadata (169.254.169.254),
      and reserved ranges.
    """
    if not url or not isinstance(url, str):
        return False, "URL is empty or invalid"

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        return False, f"URL parse error: {e}"

    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Forbidden scheme: '{parsed.scheme}'. Only http and https are permitted."

    hostname = (parsed.hostname or "").lower().strip()
    if not hostname:
        return False, "Missing hostname"

    # Reject cloud metadata hostnames directly
    blocked_hostnames = {
        "metadata.google.internal",
        "metadata.local",
        "instance-data",
        "localhost",
    }
    if hostname in blocked_hostnames or hostname.endswith(".localhost"):
        return False, f"Forbidden hostname: {hostname}"

    # Disallow userinfo credentials in URL (e.g. http://user:pass@host)
    if parsed.username or parsed.password:
        return False, "Userinfo credentials embedded in URL are forbidden."

    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)

    # Resolve all IPs for the hostname to prevent DNS rebinding / mixed-interface tricks
    try:
        addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
        ips = [entry[4][0] for entry in addr_info]
    except (socket.gaierror, socket.herror) as e:
        return False, f"Could not resolve host '{hostname}': {e}"
    except Exception as e:
        return False, f"DNS resolution error: {e}"

    if not ips:
        return False, f"Host '{hostname}' resolved to 0 IP addresses"

    for ip_str in ips:
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, f"Invalid resolved IP format: {ip_str}"

        # Strict IP blocklist
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
            or str(ip).startswith("169.254.")  # AWS/GCP/Azure link-local metadata
            or str(ip) in ("0.0.0.0", "255.255.255.255", "::1", "::")
        ):
            return False, f"Resolved IP {ip_str} is private, loopback, or cloud metadata (SSRF blocked)."

    return True, None


DEFAULT_ALLOWED_MEDIA_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "video/x-matroska",
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/ogg",
    "audio/aac",
    "application/octet-stream",
]


async def secure_download_media(
    url: str,
    dest_path: Optional[str] = None,
    max_bytes: int = 50 * 1024 * 1024,  # 50MB max default
    timeout_sec: float = 20.0,
    allowed_content_types: Optional[List[str]] = None,
    max_redirects: int = 3
) -> bytes:
    """
    Downloads external media safely:
    - Pre-validates URL before initial fetch (blocking SSRF, private IPs, metadata)
    - Validates scheme on all redirects (blocking file://, ftp://, gopher://)
    - Detects and prevents redirect loops
    - Explicitly inspects and validates every redirect hop with DNS re-verification
    - Enforces granular connect, read, write, and pool timeouts
    - Validates Content-Type header against permitted media types
    - TRULY BOUNDED: streams response chunks (64KB) and aborts immediately when
      incremental counter exceeds max_bytes, preventing OOM / memory exhaustion
    - Safely cleans up partial files on disk if size limit or timeout is exceeded
    """
    current_url = url
    redirect_count = 0
    visited_urls = {current_url}

    target_types = allowed_content_types if allowed_content_types is not None else DEFAULT_ALLOWED_MEDIA_TYPES

    timeouts = httpx.Timeout(
        timeout=timeout_sec,
        connect=min(5.0, timeout_sec),
        read=timeout_sec,
        write=10.0,
        pool=5.0
    )

    async with httpx.AsyncClient(timeout=timeouts, follow_redirects=False) as client:
        while True:
            # 1. SSRF Safety Check on current URL
            safe, err = is_safe_url(current_url)
            if not safe:
                raise SSRFSecurityError(f"SSRF violation for URL '{current_url}': {err}")

            try:
                # Use streaming request to avoid buffering response into memory
                resp_ctx = client.stream("GET", current_url)
                resp = await resp_ctx.__aenter__()
            except Exception as exc:
                raise DownloadError(f"Network error initiating download for '{current_url}': {exc}")

            # 2. Redirect Handling
            if resp.status_code in (301, 302, 303, 307, 308):
                await resp_ctx.__aexit__(None, None, None)
                redirect_count += 1
                if redirect_count > max_redirects:
                    raise DownloadError(f"Too many redirects ({redirect_count}) for URL '{url}'")

                location = resp.headers.get("Location")
                if not location:
                    raise DownloadError(f"Redirect status {resp.status_code} with no Location header.")

                # Resolve relative redirect URLs against current_url
                next_url = urllib.parse.urljoin(current_url, location)

                # Scheme validation: strictly block file://, ftp://, gopher://, etc.
                next_scheme = urllib.parse.urlparse(next_url).scheme.lower()
                if next_scheme not in ("http", "https"):
                    raise SSRFSecurityError(f"Forbidden redirect scheme '{next_scheme}' in '{next_url}'")

                # Detect redirect loops
                if next_url in visited_urls:
                    raise DownloadError(f"Redirect loop detected: '{next_url}' was visited multiple times.")
                visited_urls.add(next_url)

                # Validate next_url before following!
                next_safe, next_err = is_safe_url(next_url)
                if not next_safe:
                    raise SSRFSecurityError(f"SSRF redirect violation to '{next_url}': {next_err}")

                current_url = next_url
                continue

            # 3. Check HTTP Status
            if resp.status_code != 200:
                await resp_ctx.__aexit__(None, None, None)
                raise DownloadError(f"HTTP {resp.status_code} error downloading '{current_url}'")

            # 4. Content Type check
            if target_types:
                ct = (resp.headers.get("Content-Type") or "").lower().split(";")[0].strip()
                if ct and not any(allowed in ct for allowed in target_types):
                    await resp_ctx.__aexit__(None, None, None)
                    raise DownloadError(f"Unacceptable Content-Type '{ct}' for URL '{current_url}'")

            # 5. Check Content-Length if present
            cl = resp.headers.get("Content-Length")
            if cl and cl.isdigit() and int(cl) > max_bytes:
                await resp_ctx.__aexit__(None, None, None)
                raise DownloadError(f"Content-Length exceeds maximum allowed ({cl} > {max_bytes} bytes)")

            # 6. Stream chunks with hard byte counter enforcement
            chunks = []
            total_bytes = 0
            file_handle = None

            if dest_path:
                os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
                file_handle = open(dest_path, "wb")

            try:
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        raise DownloadError(
                            f"Downloaded content exceeded limit of {max_bytes} bytes "
                            f"(aborted at {total_bytes} bytes)"
                        )
                    if file_handle:
                        file_handle.write(chunk)
                    else:
                        chunks.append(chunk)
            except Exception:
                if file_handle:
                    file_handle.close()
                    file_handle = None
                    if os.path.isfile(dest_path):
                        try:
                            os.remove(dest_path)
                        except OSError:
                            pass
                raise
            finally:
                if file_handle:
                    file_handle.close()
                await resp_ctx.__aexit__(None, None, None)

            return b"".join(chunks) if not dest_path else b""

