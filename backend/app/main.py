from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.services.crawler import NaverCrawler
from app.services.tts_service import TTSService
from app.services.video_service import VideoService
from openai import AsyncOpenAI
import os
import uuid
import json

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Blog2Shorts AI Production Server", version="5.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

openai_client = AsyncOpenAI()

class URLRequest(BaseModel):
    url: str

class TTSRequest(BaseModel):
    task_id: str  
    hook: str
    body: str
    ending: str
    voice: str = "alloy"

class VideoRequest(BaseModel):
    task_id: str  
    images: list[str]
    template: str = "basic"
    settings: dict = None


@app.post("/api/analyze")
async def analyze_blog(payload: URLRequest):
    try:
        crawler = NaverCrawler()
        raw_text, title, images = await crawler.extract_text(payload.url)
        
        task_id = str(uuid.uuid4())
        os.makedirs(os.path.join(STATIC_DIR, "tasks", task_id), exist_ok=True)

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "너는 네이버 블로그 글을 유튜브 쇼츠 대본으로 만드는 전문 기획자야. 제공된 본문 내용만 사실대로 사용하고, 30초 이내 분량으로 짧고 임팩트 있게 작성해."},
                    {"role": "user", "content": f"블로그 제목: {title}\n본문 내용: {raw_text[:3000]}\n\n위 내용으로 약 30초 분량의 쇼츠 대본을 만들어. 아래 JSON 구조로만 응답하고 다른 설명은 빼.\n규칙:\n- hook: 영상 맨 위에 크게 들어갈 '제목'. 공백 포함 18자 이내의 짧고 강한 카피. 완전한 문장 금지(예: '주말 가볼만한 곳, 의왕 레일바이크'). 절대 길게 쓰지 마.\n- body: 성우가 읽을 핵심 내레이션. 짧은 문장 5~6개로 끊어서 자연스럽게. 전체 합쳐 공백 포함 110~140자(약 20초 분량)로 작성해. 너무 길면 음성이 빨라지니 이 분량을 꼭 지켜. 본문의 구체적 정보(가격, 위치, 팁 등)를 담아.\n- ending: 저장/구독을 유도하는 짧은 한 문장(20자 이내).\n{{'hook': '18자 이내 짧은 제목', 'body': '짧은 문장 5~6개, 총 110~140자', 'ending': '짧은 마무리'}}"}
                ],
                response_format={"type": "json_object"}
            )
            ai_res = json.loads(response.choices[0].message.content)
            script = {
                "hook": ai_res.get("hook", title[:18]),
                "body": ai_res.get("body", "본문 내용을 아주 알차게 요약해 드릴게요. 집중해서 끝까지 봐주세요!"),
                "ending": ai_res.get("ending", "이 정보가 도움이 되셨다면 구독과 좋아요 부탁드립니다!")
            }
        except Exception:
            script = {
                "hook": title[:18],
                "body": f"{raw_text[:130]}",
                "ending": "구독과 좋아요 부탁드려요!"
            }
        
        scenes = [
            {"id": 1, "time": "자동 싱크 매핑", "desc": "인트로 파트", "script": script["hook"]},
            {"id": 2, "time": "자동 싱크 매핑", "desc": "본문 핵심 파트", "script": script["body"]},
            {"id": 3, "time": "자동 싱크 매핑", "desc": "엔딩 유도 파트", "script": script["ending"]}
        ]
        
        return {
            "status": "success",
            "task_id": task_id,
            "title": title,
            "images": images,
            "script": script,
            "scenes": scenes
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


import re as _re


def _split_sentences(text: str, max_len: int = 26):
    """대본을 문장(필요 시 쉼표) 단위의 짧은 자막 청크로 분할."""
    text = (text or "").strip()
    if not text:
        return []
    parts = _re.split(r'(?<=[.!?。])\s+', text)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) <= max_len:
            out.append(p)
            continue
        # 길면 쉼표 단위로 추가 분할
        sub = _re.split(r'(?<=[,、])\s*', p)
        buf = ""
        for x in sub:
            x = x.strip()
            if not x:
                continue
            if buf and len(buf) + len(x) > max_len:
                out.append(buf.strip())
                buf = x
            else:
                buf = (buf + " " + x).strip() if buf else x
        if buf:
            out.append(buf.strip())
    return out


@app.post("/api/tts")
async def generate_tts(payload: TTSRequest):
    """
    문장별 음성 생성 + 타이밍 매니페스트(captions.json).
    - hook/body/ending을 문장 단위로 쪼개 각각 mp3로 만들고
    - 순서/역할/파일명을 captions.json에 기록 → video_service가 이걸로 자막을 100% 싱크.
    """
    try:
        import json as _json
        task_dir = os.path.join(STATIC_DIR, "tasks", payload.task_id)
        os.makedirs(task_dir, exist_ok=True)

        # 이전 매니페스트/음성 정리 (재생성 대비)
        for f in os.listdir(task_dir):
            if f.startswith("speech_seg_") or f in ("captions.json", "speech.mp3",
                                                    "speech_hook.mp3", "speech_body.mp3", "speech_ending.mp3"):
                try:
                    os.remove(os.path.join(task_dir, f))
                except OSError:
                    pass

        if payload.voice == "none":
            return {"status": "success", "audio_url": "none"}

        allowed_voices = ["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"]
        target_voice = payload.voice if payload.voice in allowed_voices else "coral"
        tts_service = TTSService()

        # 내레이션 세그먼트 구성: hook(제목, 1개) → body 문장들 → ending 문장들
        segments = []
        if (payload.hook or "").strip():
            segments.append({"role": "hook", "text": payload.hook.strip()})
        for sent in _split_sentences(payload.body):
            segments.append({"role": "body", "text": sent})
        for sent in _split_sentences(payload.ending):
            segments.append({"role": "ending", "text": sent})

        if not segments:
            segments.append({"role": "body", "text": "내용이 비어 있습니다."})

        manifest = []
        seg_files = []
        for i, seg in enumerate(segments):
            fn = f"speech_seg_{i:02d}.mp3"
            await tts_service.generate_speech(seg["text"], target_voice, os.path.join(task_dir, fn))
            manifest.append({"i": i, "role": seg["role"], "text": seg["text"], "file": fn})
            seg_files.append(os.path.join(task_dir, fn))

        # 미리듣기용 전체 음성 합치기 (speech.mp3)
        import subprocess
        p_master = os.path.join(task_dir, "speech.mp3")
        if seg_files:
            inputs = []
            for f in seg_files:
                inputs.extend(["-i", f])
            n = len(seg_files)
            subprocess.run(
                ["ffmpeg", "-y", *inputs, "-filter_complex", f"concat=n={n}:v=0:a=1[a]", "-map", "[a]", p_master],
                capture_output=True,
            )

        with open(os.path.join(task_dir, "captions.json"), "w", encoding="utf-8") as f:
            _json.dump({"segments": manifest, "voice": target_voice}, f, ensure_ascii=False)

        return {
            "status": "success",
            "audio_url": f"http://127.0.0.1:8000/static/tasks/{payload.task_id}/speech.mp3",
            "segments": len(manifest),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/video")
async def generate_video(payload: VideoRequest):
    try:
        video_service = VideoService()
        result = await video_service.generate_shorts_video(
            task_id=payload.task_id,
            images=payload.images, 
            template=payload.template,
            settings=payload.settings
        )
        
        # 🚨 [개발자님의 예상이 완벽히 적중한 방어선!] 
        # result가 None으로 넘어오거나 dict가 아닐 경우의 인덱싱 에러를 완전히 차단합니다.
        if not result or not isinstance(result, dict) or "video_url" not in result:
            raise Exception("비디오 생성 결과값이 올바르지 않습니다.")

        return {
            "status": "success",
            "video_url": f"http://127.0.0.1:8000{result['video_url']}"
        }
    except FileNotFoundError as fnfe:
        raise HTTPException(status_code=400, detail=str(fnfe))
    except Exception as e:
        # 이 부분이 프론트엔드의 error.message 로 넘어갑니다!
        raise HTTPException(status_code=500, detail=str(e))