import os
import subprocess
import httpx
import json
import uuid

class VideoService:
    def __init__(self):
        self.static_dir = "static"
        # 테스크 저장용 폴더 생성
        self.tasks_base_dir = os.path.join(self.static_dir, "tasks")
        os.makedirs(self.tasks_base_dir, exist_ok=True)

    def _get_duration(self, file_path) -> float:
        """FFprobe 기반 밀리초 단위 정밀 오디오 분석 엔진"""
        if not os.path.exists(file_path): return 0.0
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", file_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(json.loads(res.stdout)["format"]["duration"])
        except Exception as e:
            print(f"[FFprobe 경고] 오디오 길이 계측 실패, 기본값 대체: {e}")
            return 4.0

    def _wrap_text(self, text, max_chars=16) -> str:
        """가로 해상도를 벗어나지 않도록 글자를 자동 줄바꿈 처리"""
        if not text: return ""
        words = text.split()
        lines, current = [], ""
        for word in words:
            if len(current) + len(word) + 1 <= max_chars:
                current += (" " if current else "") + word
            else:
                lines.append(current)
                current = word
        if current: lines.append(current)
        return "\n".join(lines)

    async def generate_shorts_video(self, images: list[str], template: str = "basic", settings: dict = None) -> str:
        safe_settings = settings or {}

        # 🎯 해결책 1: 동시 요청 격리를 위한 세션 ID 발급 및 폴더 생성
        session_id = str(uuid.uuid4())
        task_dir = os.path.join(self.tasks_base_dir, session_id)
        os.makedirs(task_dir, exist_ok=True)

        # 최종 결과물 mp4 파일명 유니크 지정
        final_output_path = os.path.join(self.static_dir, f"output_{session_id}.mp4")
        
        p_hook = "static/speech_hook.mp3"
        p_body = "static/speech_body.mp3"
        p_ending = "static/speech_ending.mp3"

        d_hook = self._get_duration(p_hook) or 4.0
        d_body = self._get_duration(p_body) or 8.0
        d_ending = self._get_duration(p_ending) or 4.0
        total_duration = d_hook + d_body + d_ending

        # 이미지 소스 실시간 수집 및 로컬라이징
        local_images = []
        async with httpx.AsyncClient() as client:
            for idx, img_url in enumerate(images):
                if img_url.startswith("blob:") or not img_url.startswith("http"): continue
                try:
                    resp = await client.get(img_url, headers={"User-Agent":"Mozilla"}, timeout=5.0)
                    if resp.status_code == 200:
                        path = os.path.join(task_dir, f"img_{idx}.jpg")
                        with open(path, "wb") as f: f.write(resp.content)
                        local_images.append(path)
                except: pass

        if not local_images:
            fb = os.path.join(task_dir, "fb.jpg")
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x020617:s=720x1280", "-vframes", "1", fb], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            local_images.append(fb)

        # 타임라인 이미지 균등 분배 트랙 연산
        img_count = len(local_images)
        if img_count == 1:
            arr_hook, arr_body, arr_ending = [local_images[0]], [local_images[0]], [local_images[0]]
        elif img_count == 2:
            arr_hook, arr_body, arr_ending = [local_images[0]], [local_images[1]], [local_images[1]]
        else:
            arr_hook = [local_images[0]]
            arr_ending = [local_images[-1]]
            arr_body = local_images[1:-1]

        dur_hook_img = d_hook / len(arr_hook)
        dur_body_img = d_body / len(arr_body)
        dur_ending_img = d_ending / len(arr_ending)

        mapped_inputs = []
        v_filters = ""
        v_concat = ""
        idx_v = 0

        for img in arr_hook:
            mapped_inputs.extend(["-loop", "1", "-t", f"{dur_hook_img:.3f}", "-i", img])
            v_filters += f"[{idx_v}:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1[v{idx_v}];"
            v_concat += f"[v{idx_v}]"
            idx_v += 1
        for img in arr_body:
            mapped_inputs.extend(["-loop", "1", "-t", f"{dur_body_img:.3f}", "-i", img])
            v_filters += f"[{idx_v}:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1[v{idx_v}];"
            v_concat += f"[v{idx_v}]"
            idx_v += 1
        for img in arr_ending:
            mapped_inputs.extend(["-loop", "1", "-t", f"{dur_ending_img:.3f}", "-i", img])
            v_filters += f"[{idx_v}:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1[v{idx_v}];"
            v_concat += f"[v{idx_v}]"
            idx_v += 1

        v_concat += f"concat=n={idx_v}:v=1:a=0[v_base]"

        # 🎯 해결책 2: 드라이브 문자(D:) 충돌을 완벽하게 해결하기 위해 상대 경로(Relative Path) 기법 도입
        # 파일 경로에 콜론(:)을 완전히 배제하여 FFmpeg 구문 분석기 크래시를 차단합니다.
        f_hook_txt = f"static/tasks/{session_id}/hook.txt"
        f_body_txt = f"static/tasks/{session_id}/body.txt"
        f_ending_txt = f"static/tasks/{session_id}/ending.txt"

        with open(os.path.join(task_dir, "hook.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("hook_text", "")))
        with open(os.path.join(task_dir, "body.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("body_text", "")))
        with open(os.path.join(task_dir, "ending.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("ending_text", "")))

        # 디자인 템플릿 환경 변수 수신
        c_size = safe_settings.get("fontSize", 42)
        c_line1 = safe_settings.get("colorLine1", "#FFFFFF").replace("#", "0x")
        c_line2 = safe_settings.get("colorLine2", "#FFD400").replace("#", "0x")
        c_channel = safe_settings.get("channelName", "SuperShorts")

        st_body = d_hook
        st_ending = d_hook + d_body

        # 고도화된 슬라이딩 모션 그래픽 타임 앵커 배치
        motion_hook = f"y='if(lt(t,0.3), h-100-((t/0.3)*180), h-280)'"
        motion_body = f"y='if(lt(t-{st_body},0.3), h-100-(((t-{st_body})/0.3)*180), h-280)'"
        motion_ending = f"y='if(lt(t-{st_ending},0.3), h-100-(((t-{st_ending})/0.3)*180), h-280)'"

        graphic_filter = (
            f"{v_filters}{v_concat};"
            f"[v_base]drawtext=text='@{c_channel}':x=(w-tw)/2:y=80:fontsize=26:fontcolor=white@0.4,"
            f"drawtext=textfile='{f_hook_txt}':{motion_hook}:x=(w-tw)/2:fontsize={c_size}:fontcolor={c_line1}:box=1:boxcolor=black@0.6:boxborderw=20:enable='between(t,0,{st_body})',"
            f"drawtext=textfile='{f_body_txt}':{motion_body}:x=(w-tw)/2:fontsize={c_size}:fontcolor={c_line2}:box=1:boxcolor=black@0.6:boxborderw=20:enable='between(t,{st_body},{st_ending})',"
            f"drawtext=textfile='{f_ending_txt}':{motion_ending}:x=(w-tw)/2:fontsize={c_size}:fontcolor={c_line1}:box=1:boxcolor=black@0.6:boxborderw=20:enable='between(t,{st_ending},{total_duration})'[v_final]"
        )

        # 🎯 해결책 3: 오디오 결합 인덱스 매칭을 고정 이미지 수(img_count)가 아닌, 실제 장전된 인풋 총 수(idx_v) 기준으로 일치 교정
        cmd = [
            "ffmpeg", "-y",
            *mapped_inputs,
            "-i", p_hook, "-i", p_body, "-i", p_ending,
            "-filter_complex", f"[{idx_v}:a][{idx_v+1}:a][{idx_v+2}:a]concat=n=3:v=0:a=1[a_merged]; {graphic_filter}",
            "-map", "[v_final]", "-map", "[a_merged]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            final_output_path
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_log = stderr.decode('utf-8', errors='ignore')
            print(f"[FFmpeg 치명적 렌더링 에러]: {error_log}")
            raise Exception("FFmpeg 미디어 타임라인 빌드 중 결함이 발생했습니다.")

        return f"/static/output_{session_id}.mp4"