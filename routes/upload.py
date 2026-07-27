"""
Vision AI v2.0 - Upload/YouTube Router
======================================
YouTube video format fetching and download functionality.
Uses yt-dlp for extraction with proper error handling.
"""

import json
import time
import re  # 🔥 Added for URL validation
import logging
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, status, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/upload", tags=["YouTube"])
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger("vision-ai")  # 🔥 Added logging

# ==========================================================
# CONFIGURATION (Fixed: No circular import from main)
# ==========================================================
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

MAX_DOWNLOAD_TIMEOUT = 300  # 5 minutes
MAX_FORMAT_TIMEOUT = 45     # 45 seconds

# ==========================================================
# REQUEST/RESPONSE MODELS
# ==========================================================
class FormatResponse(BaseModel):
    status: str
    title: str
    combined_formats: list
    video_formats: list
    audio_formats: list

class DownloadResponse(BaseModel):
    status: str
    filename: str
    file_size_mb: float
    download_url: str

# ==========================================================
# YT-DLP HELPERS
# ==========================================================
def run_ytdlp(args: list, timeout: int) -> subprocess.CompletedProcess:
    """Run yt-dlp with given arguments and timeout."""
    cmd = ["yt-dlp"] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

def parse_formats(info: dict) -> dict:
    """Parse yt-dlp format info into categorized lists."""
    combined_formats = []
    video_formats = []
    audio_formats = []

    for fmt in info.get("formats", []):
        if not fmt.get("format_id"):
            continue

        entry = {
            "format_id": fmt["format_id"],
            "ext": fmt.get("ext", "unknown"),
            "filesize": fmt.get("filesize") or fmt.get("filesize_approx", 0),
            "height": fmt.get("height", 0),
            "abr": fmt.get("abr", 0),
            "vcodec": fmt.get("vcodec", "none"),
            "acodec": fmt.get("acodec", "none"),
            "quality": fmt.get("format_note", "N/A"),
            "fps": fmt.get("fps", 0),
        }

        # Categorize format
        has_video = entry["height"] > 0 and entry["vcodec"] != "none"
        has_audio = entry["acodec"] != "none" and entry["abr"] > 0

        if has_video and has_audio:
            combined_formats.append(entry)
        elif has_video:
            video_formats.append(entry)
        elif has_audio:
            audio_formats.append(entry)

    # Sort by quality
    combined_formats.sort(key=lambda x: (x["height"], x["abr"]), reverse=True)
    video_formats.sort(key=lambda x: x["height"], reverse=True)
    audio_formats.sort(key=lambda x: x["abr"], reverse=True)

    return {
        "combined_formats": combined_formats,
        "video_formats": video_formats,
        "audio_formats": audio_formats,
    }

# 🔥 Added YouTube URL validator
def is_valid_youtube_url(url: str) -> bool:
    patterns = [
        r"(https?://)?(www\.)?youtube\.com/watch\?v=[a-zA-Z0-9_-]+",
        r"(https?://)?(www\.)?youtu\.be/[a-zA-Z0-9_-]+",
    ]
    return any(re.match(p, url) for p in patterns)

# ==========================================================
# ROUTES
# ==========================================================
@router.get("/formats", response_model=FormatResponse)
@limiter.limit("10/minute")
async def get_video_formats(
    request: Request, 
    url: str = Query(..., description="YouTube video URL")
):
    if not url or not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL provided")

    # 🔥 Added YouTube URL validation
    if not is_valid_youtube_url(url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube URL"
        )

    logger.info(f"Format fetch requested for: {url}")

    try:
        args = [
            "--no-check-certificate",
            "--no-warnings",
            "--dump-json",
            "--format-sort", "res,codec:av1,ext,abr",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "--add-header", "Referer:https://www.youtube.com",
            "--extractor-args", "youtube:player_client=android",
            url,
        ]

        result = run_ytdlp(args, MAX_FORMAT_TIMEOUT)

        if result.returncode != 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": f"Failed to fetch formats: {result.stderr}"}
            )

        info = json.loads(result.stdout)
        formats = parse_formats(info)

        return FormatResponse(
            status="success",
            title=info.get("title", "Untitled"),
            **formats,
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Format fetch timed out")
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid response from video service")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/download", response_model=DownloadResponse)
@limiter.limit("5/minute")
async def download_media(
    request: Request, 
    url: str = Query(..., description="Video URL"), 
    format_id: str = Query(..., description="Format ID from /formats")
):
    if not url or not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL")
    if not format_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Format ID is required")

    # 🔥 Added YouTube URL validation
    if not is_valid_youtube_url(url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube URL"
        )

    logger.info(f"Download requested for: {url} (format: {format_id})")

    try:
        timestamp = int(time.time())
        temp_filename = f"media_{timestamp}.%(ext)s"
        out_path = str(DOWNLOAD_DIR / temp_filename)

        args = [
            "--no-check-certificate",
            "--no-warnings",
            "-f", format_id,
            "-o", out_path,
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "--extractor-args", "youtube:player_client=android",
            url,
        ]

        result = run_ytdlp(args, MAX_DOWNLOAD_TIMEOUT)

        downloaded_files = list(DOWNLOAD_DIR.glob(f"media_{timestamp}.*"))
        if not downloaded_files:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Download failed - file not found")

        file_path = downloaded_files[0]
        file_size = file_path.stat().st_size
        file_size_mb = round(file_size / (1024 * 1024), 2)

        base_url = str(request.base_url).rstrip("/")
        download_url = f"{base_url}/downloads/{file_path.name}"

        return DownloadResponse(
            status="success",
            filename=file_path.name,
            file_size_mb=file_size_mb,
            download_url=download_url,
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Download timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Download error: {str(e)}")