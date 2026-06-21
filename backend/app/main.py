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

@app.post("/api/analyze")
async def analyze_blog(payload: URLRequest):
    try:
        crawler = NaverCrawler()
        raw_text, title, images = await crawler.extract_text(payload.url)
        
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "너는 네이버 블로그 글을 유튜브 쇼츠용 프리미엄 대본으로 가공하는 전문 영상 기획자야. 반드시 제공된 텍스트 내용만을 기반으로 사실적이고 흥미진진한 1분 이내 분량의 대본을 작성해줘."},
                    {"role": "user", "content": f"블로그 제목: {title}\n본문 내용: {raw_text[:3000]}\n\n위 내용을 분석해서 다음 JSON 구조로만 답변해줘. 다른 설명은 생략해.\n{{'hook': '시청자의 이탈을 막는 강렬한 첫 문장', 'body': '핵심 정보 요약 및 디테일한 설명', 'ending': '마무리 및 구독/좋아요 유도 문구'}}"}
                ],
                response_format={"type": "json_object"}
            )
            import json
            ai_res = json.loads(response.choices[0].message.content)
            script = {
                "hook": ai_res.get("hook", f"📢 주목! 오늘 소개해드릴 대박 정보는 바로, '{title}' 입니다!"),
                "body": ai_res.get("body", "본문 내용을 아주 정밀하게 요약해 드릴게요. 집중해서 끝까지 봐주세요!"),
                "ending": ai_res.get("ending", "✨ 정보가 도움 되셨다면 구독과 좋아요 부탁드립니다!")
            }
        except Exception as ai_err:
            script = {
                "hook": f"📢 주목! 오늘 소개해드릴 대박 정보는 바로, '{title}' 입니다!",
                "body": f"본문 내용 요약: {raw_text[:120]}...",
                "ending": "✨ 이 정보가 도움이 되셨다면 구독과 좋아요 부탁드립니다!"
            }
        
        scenes = [
            {"id": 1, "time": "오디오 계측매핑", "desc": "인트로 파트", "script": script["hook"]},
            {"id": 2, "time": "오디오 계측매핑", "desc": "본문 핵심 파트", "script": script["body"]},
            {"id": 3, "time": "오디오 계측매핑", "desc": "엔딩 유도 파트", "script": script["ending"]}
        ]
        
        return {
            "status": "success",
            "title": title,
            "images": images,
            "script": script,
            "scenes": scenes
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
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