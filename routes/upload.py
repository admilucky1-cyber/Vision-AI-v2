from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import subprocess
import json
import time
from pathlib import Path
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/upload", tags=["Upload"])
limiter = Limiter(key_func=get_remote_address)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# ================================================================
# FORMATS ENDPOINT
# ================================================================
@router.get("/formats")
@limiter.limit("10/minute")
async def get_universal_formats(request: Request, url: str):
    try:
        cmd = [
            "yt-dlp",
            "--no-check-certificate",
            "--no-warnings",
            "--dump-json",
            "--format-sort", "res,codec:av1,ext,abr",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "--add-header", "Referer:https://www.youtube.com",
            "--extractor-args", "youtube:player_client=android",
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)

        if result.returncode != 0:
            return {"status": "error", "message": "Failed to fetch formats"}

        info = json.loads(result.stdout)
        
        combined_formats = []
        video_formats = []
        audio_formats = []

        for f in info.get('formats', []):
            if not f.get('format_id'):
                continue

            entry = {
                "format_id": f['format_id'],
                "ext": f.get('ext', 'unknown'),
                "filesize": f.get('filesize') or f.get('filesize_approx', 0),
                "height": f.get('height', 0),
                "abr": f.get('abr', 0),
                "vcodec": f.get('vcodec', 'none'),
                "acodec": f.get('acodec', 'none'),
                "quality": f.get('format_note', 'N/A')
            }

            if entry['height'] > 0 and entry['vcodec'] != 'none' and entry['acodec'] != 'none':
                combined_formats.append(entry)
            elif entry['height'] > 0 and entry['vcodec'] != 'none':
                video_formats.append(entry)
            elif entry['vcodec'] == 'none' and entry['acodec'] != 'none' and entry['abr'] > 0:
                audio_formats.append(entry)

        combined_formats.sort(key=lambda x: x['height'], reverse=True)
        video_formats.sort(key=lambda x: x['height'], reverse=True)
        audio_formats.sort(key=lambda x: x['abr'], reverse=True)

        return {
            "status": "success",
            "title": info.get('title', 'Untitled'),
            "combined_formats": combined_formats,
            "video_formats": video_formats,
            "audio_formats": audio_formats,
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


# ================================================================
# DOWNLOAD ENDPOINT - FIXED
# ================================================================
@router.get("/download")
@limiter.limit("5/minute")
async def download_universal_media(request: Request, url: str, format_id: str):
    try:
        if not format_id:
            raise HTTPException(status_code=400, detail="Format ID required")

        temp_filename = f"media_{int(time.time())}.%(ext)s"
        out_path = str(DOWNLOAD_DIR / temp_filename)

        args = [
            "yt-dlp", "--no-check-certificate", "--no-warnings",
            "-f", format_id, "-o", out_path, url,
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "--extractor-args", "youtube:player_client=android"
        ]

        subprocess.run(args, timeout=300)

        downloaded_files = list(DOWNLOAD_DIR.glob(f"*{Path(out_path).stem}*"))
        if not downloaded_files:
            raise HTTPException(404, "Download failed")

        file_path = downloaded_files[0]
        base_url = str(request.base_url).rstrip('/')

        return {
            "status": "success",
            "filename": file_path.name,
            "file_size_mb": round(file_path.stat().st_size / (1024*1024), 2),
            "download_url": f"{base_url}/downloads/{file_path.name}"
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})