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


def youtube_options_base():
    return {
        "quiet": False,
        "no_warnings": False,
        "noplaylist": True,
        "extractor_args": {
            "youtube": {
                "player_client": [
                    "ios",
                    "android",
                    "web_embedded"
                ]
            }
        }
    }


@app.post("/video/info")
def video_info(data: VideoRequest):
    try:
        options = youtube_options_base()

        options.update({
            "skip_download": True
        })

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
        print(
            "ERRO YT-DLP INFO:",
            repr(e)
        )

        raise HTTPException(
            status_code=400,
            detail=str(e)
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

        options = youtube_options_base()

        options.update({
            "format": (
                "bestvideo[height<=720][ext=mp4]"
                "+bestaudio[ext=m4a]"
                "/best[height<=720][ext=mp4]"
                "/best"
            ),
            "merge_output_format": "mp4",
            "outtmpl": output_template
        })

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                data.url,
                download=True
            )

            print(
                "DOWNLOAD FINALIZADO:",
                info.get("id")
            )

        files = os.listdir(temp_dir)

        print(
            "ARQUIVOS GERADOS:",
            files
        )

        mp4_files = [
            file
            for file in files
            if file.lower().endswith(".mp4")
        ]

        if not mp4_files:
            raise Exception(
                "Nenhum arquivo MP4 foi criado."
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
            detail=str(e)
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
        output_template = os.path.join(
            temp_dir,
            "video_teste.%(ext)s"
        )

        options = youtube_options_base()

        options.update({
            "format": (
                "bestvideo[height<=720][ext=mp4]"
                "+bestaudio[ext=m4a]"
                "/best[height<=720][ext=mp4]"
                "/best"
            ),
            "merge_output_format": "mp4",
            "outtmpl": output_template
        })

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([
                data.url
            ])

        files = os.listdir(temp_dir)

        print(
            "ARQUIVOS DO TESTE:",
            files
        )

        mp4_files = [
            file
            for file in files
            if file.lower().endswith(".mp4")
        ]

        if not mp4_files:
            raise Exception(
                "O download terminou, "
                "mas nenhum MP4 foi encontrado."
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
