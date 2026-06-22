"""
OpenAI 연동 진단 스크립트.
backend 폴더에서 실행하세요:   python test_openai.py
- .env의 OPENAI_API_KEY 인식 여부
- GPT(대본) 호출 성공 여부
- TTS(음성) 호출 성공 여부 + 실제 mp3 생성까지 확인
"""
import os
import asyncio
import inspect

from dotenv import load_dotenv
load_dotenv()

key = os.getenv("OPENAI_API_KEY")
print("1) OPENAI_API_KEY 인식:", "✅ 있음 (" + key[:7] + "...)" if key else "❌ 없음 — backend/.env 에 OPENAI_API_KEY=... 를 넣으세요")

if not key:
    raise SystemExit("키가 없어 더 진행할 수 없습니다.")

from openai import AsyncOpenAI
client = AsyncOpenAI()

async def main():
    # 2) GPT 호출 테스트
    try:
        r = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "한 단어로만 대답해: 안녕"}],
        )
        print("2) GPT(gpt-4o) 호출: ✅ 성공 →", r.choices[0].message.content.strip())
    except Exception as e:
        print("2) GPT 호출: ❌ 실패 →", repr(e))

    # 3) TTS 호출 테스트 (실제 파일 생성)
    try:
        resp = await client.audio.speech.create(model="tts-1", voice="alloy", input="테스트 음성입니다.")
        data = resp.read()
        if inspect.isawaitable(data):
            data = await data
        with open("test_tts.mp3", "wb") as f:
            f.write(data)
        size = os.path.getsize("test_tts.mp3")
        ok = "✅ 성공" if size > 1000 else "⚠️ 파일이 너무 작음"
        print(f"3) TTS(tts-1) 호출: {ok} → test_tts.mp3 ({size:,} bytes)")
    except Exception as e:
        print("3) TTS 호출: ❌ 실패 →", repr(e))
        print("   (흔한 원인: 크레딧 소진 / 키 권한 / 결제수단 미등록 / 네트워크 차단)")

asyncio.run(main())
