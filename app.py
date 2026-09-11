from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import yt_dlp
import tempfile
import os
import shutil


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
        print("ERRO YT-DLP INFO:", repr(e))

        raise HTTPException(
            status_code=400,
            detail="Não foi possível analisar este vídeo."
        )


@app.post("/video/download")
def download_video(
    data: VideoRequest,
    background_tasks: BackgroundTasks
):
    temp_dir = tempfile.mkdtemp(
        prefix="gerador_pro_"
    )

    try:
        output_template = os.path.join(
            temp_dir,
            "video.%(ext)s"
        )

        options = {
            "quiet": False,
            "no_warnings": False,
            "noplaylist": True,

            "format": (
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]"
                "/best[ext=mp4]"
                "/best"
            ),

            "merge_output_format": "mp4",

            "outtmpl": output_template,

            "extractor_args": {
                "youtube": {
                    "player_client": ["web", "android"]
                }
            }
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.extract_info(
                data.url,
                download=True
            )

        files = os.listdir(temp_dir)

        mp4_files = [
            file
            for file in files
            if file.lower().endswith(".mp4")
        ]

        if not mp4_files:
            raise Exception(
                "Arquivo MP4 não foi criado."
            )

        final_file = os.path.join(
            temp_dir,
            mp4_files[0]
        )

        background_tasks.add_task(
            shutil.rmtree,
            temp_dir,
            ignore_errors=True
        )

        return FileResponse(
            path=final_file,
            media_type="video/mp4",
            filename="video.mp4"
        )

    except Exception as e:
        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        print(
            "ERRO DOWNLOAD YT-DLP:",
            repr(e)
        )

        raise HTTPException(
            status_code=400,
            detail="Não foi possível baixar este vídeo."
        )


@app.post("/video/test-download")
def test_download(
    data: VideoRequest,
    background_tasks: BackgroundTasks
):
    temp_dir = tempfile.mkdtemp(
        prefix="yt_test_"
    )

    try:
        ydl_opts = {
            "format": (
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]"
                "/best[ext=mp4]"
                "/best"
            ),

            "outtmpl": os.path.join(
                temp_dir,
                "video_baixado.%(ext)s"
            ),

            "quiet": False,

            "nocheckcertificate": True,

            "noplaylist": True,

            "extractor_args": {
                "youtube": {
                    "player_client": ["web", "android"]
                }
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(
                [data.url]
            )

        files = os.listdir(
            temp_dir
        )

        mp4_files = [
            file
            for file in files
            if file.lower().endswith(".mp4")
        ]

        if not mp4_files:
            raise Exception(
                "O download terminou, mas nenhum MP4 foi encontrado."
            )

        final_file = os.path.join(
            temp_dir,
            mp4_files[0]
        )

        background_tasks.add_task(
            shutil.rmtree,
            temp_dir,
            ignore_errors=True
        )

        return FileResponse(
            path=final_file,
            media_type="video/mp4",
            filename="video_teste.mp4"
        )

    except Exception as e:
        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        print(
            "ERRO TESTE YT-DLP:",
            repr(e)
        )

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
