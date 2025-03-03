from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
import yt_dlp
import os
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Setting up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Data models for video response
class VideoFormat(BaseModel):
    format: str
    resolution: str
    url: str
    mime_type: Optional[str]  # Allow None for mime_type

class VideoDetails(BaseModel):
    title: str
    description: str
    duration: float
    size: float  # size in MB
    thumbnail: str

class VideoInfoResponse(BaseModel):
    formats: List[VideoFormat]
    resolutions: List[str]
    details: VideoDetails

# Route to render index page
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Route for getting video information
@app.get("/get_video_info", response_model=VideoInfoResponse)
async def get_video_info(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="YouTube URL is required")

    try:
        # yt-dlp options to extract video metadata
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'get_urls': True,
        }

        # Extract video information
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

        # Check if the video contains formats
        formats = info_dict.get('formats', [])
        if not formats:
            raise HTTPException(status_code=404, detail="No formats found for this video")

        # Gather available formats and resolutions
        video_details = []
        resolutions = set()
        for fmt in formats:
            if 'format_note' in fmt and 'width' in fmt and 'height' in fmt:
                resolution = f"{fmt['width']}x{fmt['height']}"
                resolutions.add(resolution)
                video_details.append(VideoFormat(
                    format=fmt['format_note'],
                    resolution=resolution,
                    url=fmt['url'],
                    mime_type=fmt.get('mime_type', None)  # Set mime_type to None if not found
                ))

        # Prepare video details
        details = VideoDetails(
            title=info_dict.get('title', 'Unknown Title'),
            description=info_dict.get('description', 'No description available'),
            duration=info_dict.get('duration', 0),
            size=info_dict.get('filesize_approx', 0) / (1024 * 1024),  # convert bytes to MB
            thumbnail=info_dict.get('thumbnail', '')
        )

        # Prepare final response
        return VideoInfoResponse(
            formats=video_details,
            resolutions=list(resolutions),
            details=details
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route for downloading video
@app.get("/download", response_class=FileResponse)
async def download_video(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="YouTube video URL is required")

    try:
        # Use yt-dlp to download the video
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)

        # Return the downloaded file as a response
        return FileResponse(filename, headers={"Content-Disposition": f"attachment; filename={info_dict['title']}.mp4"})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download the video: {str(e)}")

# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
