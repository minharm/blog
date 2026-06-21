import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

# 테스트 대상 FastAPI 애플리케이션 장전
from app.main import app

client = TestClient(app)

@patch("app.main.NaverCrawler")
@patch("app.main.openai_client")  # 🎯 [버그 교정] 하위 속성이 아닌 최상위 오브젝트를 다이렉트로 패치
def test_1_analyze_blog_endpoint_contract(mock_openai_client, mock_crawler_class):
    """1단계: 블로그 크롤링 및 GPT 대본 분할 생성 계약 조건 검증"""
    # NaverCrawler Mocking
    mock_crawler = mock_crawler_class.return_value
    mock_crawler.extract_text = AsyncMock(return_value=("본문 내용 샘플", "테스트 제목", ["http://img1.jpg"]))

    # 🎯 OpenAI 하이브리드 중첩 모크 동적 빌드 (AttributeError 원천 차단)
    mock_chat_completion = AsyncMock()
    mock_chat_completion.choices = [MagicMock()]
    mock_chat_completion.choices[0].message.content = '{"hook": "테스트 훅", "body": "테스트 바디", "ending": "테스트 엔딩"}'
    
    # 족보 연결: 클라이언트 -> chat -> completions -> create 매핑 성공
    mock_openai_client.chat.completions.create = mock_chat_completion

    # API 요청 테스트 실행
    response = client.post("/api/analyze", json={"url": "https://blog.naver.com/test/123"})
    
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data, "🚨 동시성 격리를 위한 task_id 발급 레이어가 누락되었습니다!"
    assert data["script"]["hook"] == "테스트 훅"
    assert len(data["scenes"]) == 3


@patch("app.main.TTSService")
def test_2_generate_tts_endpoint_contract(mock_tts_class):
    """2단계: 격리 경로 주입형 비동기 TTS 엔진 호출 스펙 검증"""
    mock_tts = mock_tts_class.return_value
    mock_tts.generate_speech = AsyncMock(return_value="static/tasks/test-uuid/speech_hook.mp3")

    with patch("subprocess.run") as mock_subprocess:
        response = client.post("/api/tts", json={
            "task_id": "test-uuid-1234",
            "hook": "도입부",
            "body": "본문",
            "ending": "마무리",
            "voice": "echo"
        })
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "speech.mp3" in response.json()["audio_url"]


@patch("app.main.VideoService")
def test_3_generate_video_endpoint_contract(mock_video_class):
    """3단계: 멀티 이미지 및 BGM 세팅 송신 규격 검증"""
    mock_video = mock_video_class.return_value
    mock_video.generate_shorts_video = AsyncMock(return_value="/static/tasks/test-uuid/output.mp4")

    response = client.post("/api/video", json={
        "task_id": "test-uuid-1234",
        "images": ["http://img1.jpg", "http://img2.jpg"],
        "template": "mint",
        "settings": {
            "autoFx": True,
            "autoBgm": False,
            "bgmTrack": "track_02"
        }
    })
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "video_url" in response.json()