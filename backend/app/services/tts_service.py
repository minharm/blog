import inspect
import os
from openai import AsyncOpenAI

# 유튜브 쇼츠 느낌의 밝고 또렷한 톤 + 정확한 한국어 발음 지시 (gpt-4o-mini-tts 전용)
BRIGHT_INSTRUCTIONS = (
    "한국어 유튜브 쇼츠 내레이터처럼 밝고 친근하게, 적당한 에너지로 또박또박 읽어줘. "
    "발음은 정확하고 또렷하게, 끝맺음은 자연스럽게. 너무 빠르거나 단조롭지 않게, "
    "정보를 전달하듯 신뢰감 있게 말해줘."
)


class TTSService:
    def __init__(self):
        self.client = AsyncOpenAI()

    async def generate_speech(self, text: str, voice: str, output_path: str, instructions: str = None) -> str:
        """
        gpt-4o-mini-tts 로 음성 생성 (tts-1 대비 발음/표현력이 크게 향상).
        - instructions 로 '밝고 또렷한 유튜버 톤' 지정
        - 실패 시 tts-1-hd 로 자동 폴백
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        safe_text = (text or "").strip() or "음성 내용이 비어 있습니다."

        async def _create(model, with_instructions):
            kwargs = dict(model=model, voice=voice, input=safe_text, response_format="mp3")
            if with_instructions:
                kwargs["instructions"] = instructions or BRIGHT_INSTRUCTIONS
            return await self.client.audio.speech.create(**kwargs)

        try:
            response = await _create("gpt-4o-mini-tts", True)
        except Exception as e:
            print(f"⚠️ gpt-4o-mini-tts 실패({e}) → tts-1-hd 로 폴백")
            response = await _create("tts-1-hd", False)

        data = response.read()
        if inspect.isawaitable(data):
            data = await data
        with open(output_path, "wb") as f:
            f.write(data)
        return output_path
