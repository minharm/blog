import inspect
import os
from openai import AsyncOpenAI


class TTSService:
    def __init__(self):
        # OPENAI_API_KEY 환경변수를 자동으로 읽어 비동기 클라이언트 생성
        self.client = AsyncOpenAI()

    async def generate_speech(self, text: str, voice: str, output_path: str) -> str:
        """
        텍스트를 음성(mp3)으로 변환해 output_path에 저장.

        ⚠️ 버그 수정:
        예전 코드는 `audio_content = await response.read()` 였는데,
        설치된 openai 라이브러리 버전에서는 response.read()가 코루틴이 아니라
        이미 bytes를 바로 반환해서 "object bytes can't be used in 'await' expression"
        에러가 났습니다. 아래처럼 반환값이 awaitable일 때만 await 하도록 처리하면
        라이브러리 버전에 상관없이 안전하게 동작합니다.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 빈 텍스트면 OpenAI가 에러를 내므로 최소 한 글자 보장
        safe_text = (text or "").strip() or "음성 내용이 비어 있습니다."

        response = await self.client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=safe_text,
        )

        # read()가 bytes(동기)이든 코루틴(비동기)이든 모두 처리
        data = response.read()
        if inspect.isawaitable(data):
            data = await data

        with open(output_path, "wb") as f:
            f.write(data)

        return output_path
