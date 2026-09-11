from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI(
    title="Gerador Pro Video API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VideoRequest(BaseModel):
    url: str


@app.get("/")
def home():
    return {
        "success": True,
        "status": "online",
        "service": "Gerador Pro Video API"
    }


@app.get("/health")
def health():
    return {
        "success": True,
        "status": "healthy"
    }


@app.post("/video/info")
def video_info(data: VideoRequest):
    try:
        options = {
            "quiet": False,
            "no_warnings": False,
            "skip_download": True,
            "noplaylist": True,

            "extractor_args": {
                "youtube": {
                    "player_client": ["web", "android"]
                }
            }
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                data.url,
                download=False
            )

        return {
            "success": True,
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "webpage_url": info.get("webpage_url"),
            "extractor": info.get("extractor")
        }

    except Exception as e:
        print("ERRO YT-DLP:", repr(e))

        raise HTTPException(
            status_code=400,
            detail="Não foi possível analisar este vídeo."
        )
