import os
from openai import AsyncOpenAI

class TTSService:
    def __init__(self):
        # OpenAI 비동기 클라이언트 바인딩
        self.client = AsyncOpenAI()

    async def generate_speech(self, text: str, voice: str, output_path: str) -> str:
        """
        [상용 레이스 컨디션 방어 사양]
        임시 static/speech.mp3 공용 버퍼를 거치지 않고, 
        요청 세션별 격리 경로(output_path)로 고품질 TTS 오디오 트랙을 다이렉트 스트리밍 저장합니다.
        """
        # 저장될 격리 테스크 폴더 선행 검증 및 강제 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # OpenAI 최신 표준 스펙 오디오 엔진 호출
        response = await self.client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )

        # 비비동기 주파수 바이너리 버퍼 로드 후 동시성 가드 다이렉트 파일링
        audio_content = await response.read()
        with open(output_path, "wb") as f:
            f.write(audio_content)

        return output_path