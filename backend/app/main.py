from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.services.crawler import NaverCrawler
from app.services.tts_service import TTSService
from app.services.video_service import VideoService
from openai import AsyncOpenAI
import os
import subprocess

app = FastAPI(title="Blog2Shorts AI API Server", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

openai_client = AsyncOpenAI()

class URLRequest(BaseModel):
    url: str

class TTSRequest(BaseModel):
    hook: str
    body: str
    ending: str
    voice: str = "alloy"

class VideoRequest(BaseModel):
    images: list[str]
    template: str = "basic"
    settings: dict = None

@app.post("/api/tts")
async def generate_tts(payload: TTSRequest):
    try:
        os.makedirs("static", exist_ok=True)
        for f_name in ["speech_hook.mp3", "speech_body.mp3", "speech_ending.mp3", "speech.mp3"]:
            p = os.path.join("static", f_name)
            if os.path.exists(p): os.remove(p)

        if payload.voice == "none":
            return {"status": "success", "audio_url": "none"}
            
        # 🎯 [성우 복제 버그 완벽 해결] 명시적 보이스 매핑 매트릭스 구축
        # 허가되지 않은 ID가 들어와 무조건 alloy로 획일화되는 현상을 막고, 성격에 맞는 고유 음색을 매핑합니다.
        voice_matrix = {
            "alloy": "alloy",      # 나라 (20대 여성)
            "echo": "echo",        # 재민 (ASMR 남성)
            "onyx": "onyx",        # 민상 (스포츠 MC)
            "nova": "nova",        # 봄달 (브이로그 여성)
            "shimmer": "shimmer",  # 민우 (게임 캐스터)
            "fable": "fable",      # 보이스 아나운서
            "유진": "shimmer",     # ➕ 쇼핑 호스트 느낌의 화사하고 하이텐션인 Shimmer 매핑!
            "현우": "echo"         # ➕ 뉴스 아나운서 사양의 차분하고 정갈한 Echo 남성 매핑!
        }
        
        target_voice = voice_matrix.get(payload.voice, "alloy")

        tts_service = TTSService()
        
        await tts_service.generate_speech(payload.hook, target_voice)
        os.replace("static/speech.mp3", "static/speech_hook.mp3")
        
        await tts_service.generate_speech(payload.body, target_voice)
        os.replace("static/speech.mp3", "static/speech_body.mp3")
        
        await tts_service.generate_speech(payload.ending, target_voice)
        os.replace("static/speech.mp3", "static/speech_ending.mp3")
        
        concat_cmd = [
            "ffmpeg", "-y",
            "-i", "static/speech_hook.mp3",
            "-i", "static/speech_body.mp3",
            "-i", "static/speech_ending.mp3",
            "-filter_complex", "concat=n=3:v=0:a=1[a]",
            "-map", "[a]", "static/speech.mp3"
        ]
        subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return {
            "status": "success",
            "audio_url": "http://127.0.0.1:8000/static/speech.mp3"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tts")
async def generate_tts(payload: TTSRequest):
    try:
        # 임시 수집 디렉토리 생성 및 찌꺼기 파일 선행 청소
        os.makedirs("static", exist_ok=True)
        for f_name in ["speech_hook.mp3", "speech_body.mp3", "speech_ending.mp3", "speech.mp3"]:
            p = os.path.join("static", f_name)
            if os.path.exists(p): os.remove(p)

        # 🎯 [리뷰 결함 1-B 해결]: 사용자가 '자막 전용 모드'를 고르면 API 호출을 패스
        if payload.voice == "none":
            return {"status": "success", "audio_url": "none"}
            
        # 🎯 [리뷰 결함 2 해결]: 허가되지 않은 한국어 성우 이름 인젝션 방어 벨브
        allowed_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        target_voice = payload.voice if payload.voice in allowed_voices else "alloy"

        tts_service = TTSService()
        
        await tts_service.generate_speech(payload.hook, target_voice)
        os.replace("static/speech.mp3", "static/speech_hook.mp3")
        
        await tts_service.generate_speech(payload.body, target_voice)
        os.replace("static/speech.mp3", "static/speech_body.mp3")
        
        await tts_service.generate_speech(payload.ending, target_voice)
        os.replace("static/speech.mp3", "static/speech_ending.mp3")
        
        concat_cmd = [
            "ffmpeg", "-y",
            "-i", "static/speech_hook.mp3",
            "-i", "static/speech_body.mp3",
            "-i", "static/speech_ending.mp3",
            "-filter_complex", "concat=n=3:v=0:a=1[a]",
            "-map", "[a]", "static/speech.mp3"
        ]
        subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return {
            "status": "success",
            "audio_url": "http://127.0.0.1:8000/static/speech.mp3"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/video")
async def generate_video(payload: VideoRequest):
    try:
        video_service = VideoService()
        video_url = await video_service.generate_shorts_video(
            images=payload.images, 
            template=payload.template,
            settings=payload.settings
        )
        return {
            "status": "success",
            "video_url": f"http://127.0.0.1:8000{video_url}"
        }
    except FileNotFoundError as fnfe:
        raise HTTPException(status_code=400, detail=str(fnfe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))