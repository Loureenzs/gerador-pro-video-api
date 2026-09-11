from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import yt_dlp
import tempfile
import os
import shutil
import subprocess


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Gerador Pro Video API",
    version="2.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MODELOS
# ============================================================

class VideoRequest(BaseModel):
    url: str


class RenderRequest(BaseModel):
    trailerUrl: str

    # Canvas vertical 720p
    canvasWidth: int = Field(
        default=720,
        ge=360,
        le=1080
    )

    canvasHeight: int = Field(
        default=1280,
        ge=640,
        le=1920
    )

    # Posição do trailer
    x: int = Field(
        default=0,
        ge=-1080,
        le=1080
    )

    y: int = Field(
        default=300,
        ge=-1920,
        le=1920
    )

    # Tamanho do trailer 16:9
    width: int = Field(
        default=720,
        ge=100,
        le=1080
    )

    height: int = Field(
        default=405,
        ge=100,
        le=1080
    )

    # Corte opcional
    startTime: float = Field(
        default=0,
        ge=0
    )

    endTime: float | None = Field(
        default=None,
        ge=0
    )


# ============================================================
# CONFIGURAÇÃO YT-DLP
# ============================================================

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


# ============================================================
# BAIXAR TRAILER
# ============================================================

def baixar_trailer(url: str, pasta: str):

    output_template = os.path.join(
        pasta,
        "trailer.%(ext)s"
    )

    options = youtube_options_base()

    options.update({
        "format": (
            "bestvideo[height<=720][ext=mp4]"
            "+bestaudio[ext=m4a]"
            "/best[height<=720][ext=mp4]"
            "/best[height<=720]"
            "/best"
        ),
        "merge_output_format": "mp4",
        "outtmpl": output_template
    })

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(
            url,
            download=True
        )

    arquivos = os.listdir(pasta)

    print(
        "ARQUIVOS BAIXADOS:",
        arquivos
    )

    mp4_files = [
        arquivo
        for arquivo in arquivos
        if arquivo.lower().endswith(".mp4")
    ]

    if not mp4_files:
        raise Exception(
            "Nenhum arquivo MP4 foi criado pelo yt-dlp."
        )

    arquivo_final = os.path.join(
        pasta,
        mp4_files[0]
    )

    return arquivo_final, info


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "success": True,
        "status": "online",
        "service": "Gerador Pro Video API",
        "version": "2.2.0",
        "download": "max 720p",
        "render": "720x1280"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "success": True,
        "status": "healthy"
    }


# ============================================================
# INFO DO VÍDEO
# ============================================================

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


# ============================================================
# DOWNLOAD SIMPLES 720P
# ============================================================

@app.post("/video/download")
def download_video(
    data: VideoRequest,
    background_tasks: BackgroundTasks
):

    temp_dir = tempfile.mkdtemp(
        prefix="gerador_pro_"
    )

    try:

        final_file, info = baixar_trailer(
            data.url,
            temp_dir
        )

        print(
            "DOWNLOAD FINALIZADO:",
            info.get("id")
        )

        background_tasks.add_task(
            shutil.rmtree,
            temp_dir,
            ignore_errors=True
        )

        return FileResponse(
            path=final_file,
            media_type="video/mp4",
            filename="video-720p.mp4"
        )

    except Exception as e:

        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        print(
            "ERRO DOWNLOAD:",
            repr(e)
        )

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ============================================================
# TESTE DOWNLOAD 720P
# ============================================================

@app.post("/video/test-download")
def test_download(
    data: VideoRequest,
    background_tasks: BackgroundTasks
):

    temp_dir = tempfile.mkdtemp(
        prefix="yt_test_"
    )

    try:

        final_file, info = baixar_trailer(
            data.url,
            temp_dir
        )

        print(
            "TESTE DOWNLOAD OK:",
            info.get("id")
        )

        background_tasks.add_task(
            shutil.rmtree,
            temp_dir,
            ignore_errors=True
        )

        return FileResponse(
            path=final_file,
            media_type="video/mp4",
            filename="video-teste-720p.mp4"
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


# ============================================================
# RENDER VERTICAL 720x1280
# ============================================================

@app.post("/video/render")
def render_video(
    data: RenderRequest,
    background_tasks: BackgroundTasks
):

    temp_dir = tempfile.mkdtemp(
        prefix="render_gerador_pro_"
    )

    try:

        print("")
        print("=======================================")
        print("NOVO RENDER")
        print("=======================================")

        print(
            "Trailer:",
            data.trailerUrl
        )

        print(
            "Canvas:",
            data.canvasWidth,
            "x",
            data.canvasHeight
        )

        print(
            "Tamanho trailer:",
            data.width,
            "x",
            data.height
        )

        print(
            "Posição:",
            data.x,
            data.y
        )

        print(
            "Tempo:",
            data.startTime,
            "até",
            data.endTime
        )


        # ====================================================
        # VALIDAR TEMPO
        # ============================================================

        if (
            data.endTime is not None
            and data.endTime <= data.startTime
        ):
            raise Exception(
                "endTime precisa ser maior que startTime."
            )


        # ====================================================
        # BAIXAR TRAILER
        # ============================================================

        trailer_file, info = baixar_trailer(
            data.trailerUrl,
            temp_dir
        )

        print(
            "TRAILER BAIXADO:",
            trailer_file
        )


        # ====================================================
        # ARQUIVO FINAL
        # ============================================================

        output_file = os.path.join(
            temp_dir,
            "gerador-pro-final-720x1280.mp4"
        )


        # ====================================================
        # DURAÇÃO
        # ============================================================

        duration = None

        if data.endTime is not None:
            duration = (
                data.endTime
                -
                data.startTime
            )


        # ====================================================
        # FILTER COMPLEX
        # ============================================================

        filter_complex = (
            f"[0:v]"
            f"scale={data.width}:{data.height}:"
            f"force_original_aspect_ratio=decrease,"
            f"pad="
            f"{data.width}:"
            f"{data.height}:"
            f"(ow-iw)/2:"
            f"(oh-ih)/2:"
            f"black"
            f"[trailer];"

            f"color="
            f"c=black:"
            f"s={data.canvasWidth}x{data.canvasHeight}:"
            f"r=30"
        )

        if duration is not None:

            filter_complex += (
                f":d={duration}"
            )

        filter_complex += (
            f"[background];"

            f"[background]"
            f"[trailer]"
            f"overlay="
            f"x={data.x}:"
            f"y={data.y}:"
            f"eof_action=pass"
            f"[video]"
        )


        # ====================================================
        # COMANDO FFMPEG
        # ============================================================

        command = [
            "ffmpeg",
            "-y"
        ]


        # Começar em determinado tempo
        if data.startTime > 0:

            command.extend([
                "-ss",
                str(data.startTime)
            ])


        command.extend([
            "-i",
            trailer_file
        ])


        command.extend([

            "-filter_complex",
            filter_complex,

            "-map",
            "[video]",

            "-map",
            "0:a?",

            # Vídeo
            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-crf",
            "23",

            "-pix_fmt",
            "yuv420p",

            "-r",
            "30",

            # Áudio
            "-c:a",
            "aac",

            "-b:a",
            "128k",

            # Compatibilidade web
            "-movflags",
            "+faststart"
        ])


        # Limite de duração
        if duration is not None:

            command.extend([
                "-t",
                str(duration)
            ])


        command.append(
            output_file
        )


        # ====================================================
        # LOG DO COMANDO
        # ============================================================

        print("")
        print("========== COMANDO FFMPEG ==========")
        print(
            " ".join(command)
        )
        print("====================================")
        print("")


        # ====================================================
        # EXECUTAR FFMPEG
        # ============================================================

        resultado = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )


        # ====================================================
        # ERRO FFMPEG
        # ============================================================

        if resultado.returncode != 0:

            print("")
            print(
                "========== FFMPEG STDERR =========="
            )

            print(
                resultado.stderr
            )

            print(
                "==================================="
            )
            print("")

            raise Exception(
                "FFmpeg não conseguiu processar o vídeo."
            )


        # ====================================================
        # VERIFICAR ARQUIVO
        # ============================================================

        if not os.path.exists(
            output_file
        ):

            raise Exception(
                "O vídeo final não foi criado."
            )


        tamanho = os.path.getsize(
            output_file
        )


        print("")
        print(
            "RENDER CONCLUÍDO COM SUCESSO"
        )

        print(
            "Arquivo:",
            output_file
        )

        print(
            "Tamanho:",
            tamanho,
            "bytes"
        )


        # ====================================================
        # LIMPEZA
        # ============================================================

        background_tasks.add_task(
            shutil.rmtree,
            temp_dir,
            ignore_errors=True
        )


        # ====================================================
        # RETORNAR MP4
        # ============================================================

        return FileResponse(
            path=output_file,
            media_type="video/mp4",
            filename="gerador-pro-720x1280.mp4"
        )


    except Exception as e:

        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        print(
            "ERRO RENDER:",
            repr(e)
        )

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
