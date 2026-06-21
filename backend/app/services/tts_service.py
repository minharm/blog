import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class TTSService:
    def __init__(self):
        # 환경 변수에서 OpenAI API Key 로드
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API Key가 .env 파일에 설정되지 않았습니다.")
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_speech(self, text: str, voice: str = "alloy") -> str:
        """
        텍스트 대본을 받아 static 폴더 내에 speech.mp3 파일을 생성하고 주소를 반환합니다.
        """
        os.makedirs("static", exist_ok=True)
        output_path = os.path.join("static", "speech.mp3")

        # OpenAI 오디오 생성 API 호출
        response = await self.client.audio.speech.create(
            model="tts-1",
            voice=voice,  # alloy, echo, fable, onyx, nova, shimmer 중 택 1
            input=text
        )

        # 바이너리 파일 비동기 스트리밍 저장
        with open(output_path, "wb") as f:
            f.write(response.content)

        return "/static/speech.mp3"