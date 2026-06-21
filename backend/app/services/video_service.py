import os
import subprocess

class VideoService:
    def __init__(self):
        self.audio_path = os.path.join("static", "speech.mp3")
        self.output_path = os.path.join("static", "output.mp4")
        self.frame_path = os.path.join("static", "frame.png") # 영상 테두리용 이미지

    async def generate_shorts_video(self, template="basic") -> str:
        if not os.path.exists(self.audio_path):
            raise FileNotFoundError("음성 파일이 생성되지 않았습니다.")

        # 기본 배경 설정
        input_args = ["-f", "lavfi", "-i", "color=c=0x020617:s=720x1280:d=15"]
        
        # 템플릿(프레임)이 있으면 오버레이 명령 추가
        filter_complex = "[0:v]scale=720:1280[bg]"
        if os.path.exists(self.frame_path):
            input_args.extend(["-i", self.frame_path])
            filter_complex = "[0:v][1:v]overlay=0:0[bg]"

        cmd = [
            "ffmpeg", "-y",
            *input_args,
            "-i", self.audio_path,
            "-filter_complex", f"{filter_complex}",
            "-c:v", "libx264", "-c:a", "aac", "-shortest",
            self.output_path
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()
        
        if process.returncode != 0:
            raise Exception("FFmpeg 렌더링 실패")
        return "/static/output.mp4"