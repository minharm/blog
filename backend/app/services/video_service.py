import os
import subprocess
import httpx
import json
import uuid
import re

class VideoService:
    def __init__(self):
        self.static_dir = "static"
        self.tasks_base_dir = os.path.join(self.static_dir, "tasks")
        os.makedirs(self.tasks_base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.static_dir, "bgm"), exist_ok=True)

    def _get_duration(self, file_path) -> float:
        if not os.path.exists(file_path): return 0.0
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", file_path]
            # 🎯 [설계상 문제 4 적용] 대용량 버퍼 교착방지를 위해 동기식 run 및 capture_output 전환
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(json.loads(res.stdout)["format"]["duration"])
        except Exception as e:
            print(f"⚠️ [FFprobe 계측 실패 - 기본 4초 대체]: {e}")
            return 4.0

    def _wrap_text(self, text, max_chars=16) -> str:
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

    # 🎯 [2순위 & 6순위 오류 해결] Windows 절대경로 콜론(:) 및 백슬래시 오인을 차단하는 전용 이스케이프 헬퍼
    def ffmpeg_escape_path(self, path: str) -> str:
        return path.replace("\\", "/").replace(":", "\\:")

    async def generate_shorts_video(self, task_id: str, images: list[str], template: str = "basic", settings: dict = None) -> str:
        safe_settings = settings or {}
        
        # 🎯 [1순위 오류 해결] 실행 위치와 상관없이 오동작하지 않도록 절대경로(abspath) 선행 확정
        task_dir = os.path.abspath(os.path.join(self.tasks_base_dir, task_id))
        os.makedirs(task_dir, exist_ok=True)

        final_output_path = os.path.join(task_dir, "output.mp4")
        
        p_hook = os.path.join(task_dir, "speech_hook.mp3")
        p_body = os.path.join(task_dir, "speech_body.mp3")
        p_ending = os.path.join(task_dir, "speech_ending.mp3")

        is_voice_none = not (os.path.exists(p_hook) and os.path.exists(p_body) and os.path.exists(p_ending))
        
        if is_voice_none:
            d_hook = max(4.0, len(safe_settings.get("hook_text", "")) * 0.18)
            d_body = max(6.5, len(safe_settings.get("body_text", "")) * 0.18)
            d_ending = max(4.0, len(safe_settings.get("ending_text", "")) * 0.18)
        else:
            d_hook = self._get_duration(p_hook) or 4.0
            d_body = self._get_duration(p_body) or 7.0
            d_ending = self._get_duration(p_ending) or 4.0
            
        total_duration = d_hook + d_body + d_ending

        local_images = []
        # 🎯 [오류 7 적용] 네트워크 지연으로 인한 꿀럭임 방지를 위해 타임아웃 20초 확보
        async with httpx.AsyncClient() as client:
            for idx, img_url in enumerate(images):
                if img_url.startswith("blob:") or not img_url.startswith("http"): continue
                try:
                    resp = await client.get(img_url, headers={"User-Agent":"Mozilla"}, timeout=20.0)
                    if resp.status_code == 200:
                        path = os.path.join(task_dir, f"img_{idx}.jpg")
                        with open(path, "wb") as f: f.write(resp.content)
                        local_images.append(path)
                except: pass

        if not local_images:
            fb = os.path.join(task_dir, "fb.jpg")
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x020617:s=720x1280", "-vframes", "1", fb], capture_output=True)
            local_images.append(fb)

        img_count = len(local_images)
        if img_count == 1:
            arr_hook, arr_body, arr_ending = [local_images[0]], [local_images[0]], [local_images[0]]
        elif img_count == 2:
            arr_hook, arr_body, arr_ending = [local_images[0]], [local_images[1]], [local_images[1]]
        else:
            arr_hook = [local_images[0]]
            arr_ending = [local_images[-1]]
            arr_body = local_images[1:-1]

        # 🎯 [설계상 문제 1 적용] 제로 디비전 방어 벨브 수립
        dur_hook_img = d_hook / max(1, len(arr_hook))
        dur_body_img = d_body / max(1, len(arr_body))
        dur_ending_img = d_ending / max(1, len(arr_ending))

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

        # 🎯 [1순위 & 2순위 오류 해결] 파일 경로를 완벽한 절대경로로 치환 후 콜론(:) 이스케이프 가드 전사 처리
        f_hook_txt = self.ffmpeg_escape_path(os.path.join(task_dir, "hook.txt"))
        f_body_txt = self.ffmpeg_escape_path(os.path.join(task_dir, "body.txt"))
        f_ending_txt = self.ffmpeg_escape_path(os.path.join(task_dir, "ending.txt"))

        with open(os.path.join(task_dir, "hook.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("hook_text", "")))
        with open(os.path.join(task_dir, "body.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("body_text", "")))
        with open(os.path.join(task_dir, "ending.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("ending_text", "")))

        # 🎯 [설계상 문제 3 적용] fontSize의 비정상 마이너스 유입 차단 가드
        try:
            raw_size = int(safe_settings.get("fontSize", 42))
        except (ValueError, TypeError):
            raw_size = 42
        c_size = max(20, min(raw_size, 100))
        
        # 🎯 [3순위 오류 & 설계상 문제 2 해결] 구형 및 프리미엄 FFmpeg 엔진 전수가 호환되는 표준 컬러 변환 명세 적용 (샵 제거 후 0x 마운트)
        c_line1 = safe_settings.get("colorLine1", "#FFFFFF").replace("#", "0x")
        c_line2 = safe_settings.get("colorLine2", "#00D4FF").replace("#", "0x")
        c_boxcolor = "0x000000@0.6"
        
        if template == "dark":
            c_line1, c_line2, c_boxcolor = "0xCCCCCC", "0x4A4AF7", "0x111111@0.8"
        elif template == "mint":
            c_line1, c_line2, c_boxcolor = "0xFFFFFF", "0x6EF5A3", "0x052e16@0.9"

        # 🎯 [4순위 오류 해결] 특수기호 유입 시 문자열 파싱 붕괴를 원천 차단하는 정규식 알파뉴메릭 가운딩
        c_channel = safe_settings.get("channelName", "SuperShorts")
        safe_channel = re.sub(r"[^a-zA-Z0-9가-힣 _\-]", "", c_channel)
        
        st_body, st_ending = d_hook, d_hook + d_body

        # 🎯 [5순위 오류 해결] y='if(...)' 내부 인라인 홑따옴표 중첩 버그 소멸을 위해, 구문 할당에서 y=를 배제하고 순수 수식 밸류만 사출
        motion_hook = "if(lt(t,0.3),h-100-((t/0.3)*180),h-280)"
        motion_body = f"if(lt(t-{st_body},0.3),h-100-(((t-{st_body})/0.3)*180),h-280)"
        motion_ending = f"if(lt(t-{st_ending},0.3),h-100-(((t-{st_ending})/0.3)*180),h-280)"

        # 🎯 [5순위 오류 해결] 안정적인 표준 인코딩 동선인 x -> y -> 옵션 정렬 기법 전사 이식 및 공백 전수 제거
        graphic_filter = (
            f"{v_filters}{v_concat};"
            f"[v_base]drawtext=text='@{safe_channel}':x=(w-tw)/2:y=80:fontsize=26:fontcolor='{c_line1}@0.4',"
            f"drawtext=textfile='{f_hook_txt}':x=(w-tw)/2:y='{motion_hook}':fontsize={c_size}:fontcolor='{c_line1}':box=1:boxcolor='{c_boxcolor}':boxborderw=20:enable='between(t,0,{st_body})',"
            f"drawtext=textfile='{f_body_txt}':x=(w-tw)/2:y='{motion_body}':fontsize={c_size}:fontcolor='{c_line2}':box=1:boxcolor='{c_boxcolor}':boxborderw=20:enable='between(t,{st_body},{st_ending})',"
            f"drawtext=textfile='{f_ending_txt}':x=(w-tw)/2:y='{motion_ending}':fontsize={c_size}:fontcolor='{c_line1}':box=1:boxcolor='{c_boxcolor}':boxborderw=20:enable='between(t,{st_ending},{total_duration})'[v_final]"
        )

        use_bgm = safe_settings.get("autoBgm", True)
        bgm_track_id = safe_settings.get("bgmTrack", "track_01")
        bgm_file_path = os.path.abspath(os.path.join(self.static_dir, "bgm", f"{bgm_track_id}.mp3"))
        
        audio_inputs = []
        bgm_mixing_filter = ""

        # 🎯 [6순위 오류 해결] 비디오 입력 갯수(idx_v) 변동에 종속되지 않도록, 오디오 시작 인덱스를 가변 변수로 정밀 격리 추적
        audio_start_idx = idx_v

        if is_voice_none:
            audio_inputs.extend(["-f", "lavfi", "-i", f"anullsrc=cl=stereo:r=44100:d={total_duration}"])
            voice_filter_stmt = f"[{audio_start_idx}:a]"
            idx_bgm_input = audio_start_idx + 1
        else:
            audio_inputs.extend(["-i", p_hook, "-i", p_body, "-i", p_ending])
            voice_filter_stmt = f"[{audio_start_idx}:a][{audio_start_idx+1}:a][{audio_start_idx+2}:a]concat=n=3:v=0:a=1[a_voice_merged];[a_voice_merged]"
            idx_bgm_input = audio_start_idx + 3

        if use_bgm:
            if os.path.exists(bgm_file_path):
                audio_inputs.extend(["-stream_loop", "-1", "-i", bgm_file_path])
                bgm_filter_stmt = f"[{idx_bgm_input}:a]volume=0.15,asetpts=PTS-STARTPTS[bgm_fixed];"
            else:
                audio_inputs.extend(["-f", "lavfi", "-i", f"anullsrc=cl=stereo:r=44100:d={total_duration}"])
                bgm_filter_stmt = f"[{idx_bgm_input}:a]volume=0.0,asetpts=PTS-STARTPTS[bgm_fixed];"
            
            bgm_mixing_filter = f"{voice_filter_stmt}anull[a_src];{bgm_filter_stmt}[a_src][bgm_fixed]amix=inputs=2:duration=first[a_final];"
        else:
            bgm_mixing_filter = f"{voice_filter_stmt}anull[a_final];"

        cmd = [
            "ffmpeg", "-y",
            *mapped_inputs,
            *audio_inputs,
            "-filter_complex", f"{bgm_mixing_filter}{graphic_filter}",
            "-map", "[v_final]", "-map", "[a_final]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-t", f"{total_duration:.2f}",
            final_output_path
        ]

        # 🎯 [설계상 문제 4 적용] 좀비 프로세스 교착을 막기 위해 run 표준 명세 작동
        res = subprocess.run(cmd, capture_output=True, text=True)

        # 🎯 [7순위 해결] No such filter 장착 여부를 포함하여, 터졌을 때의 stderr 바이너리 원인을 전수 사출하도록 예외 처리 고도화
        if res.returncode != 0:
            print(f"❌ [FFmpeg 치명적 렌더링 에러 디버그로그]\n{res.stderr}")
            raise Exception(f"FFmpeg 미디어 합성이 거부되었습니다. 원인 스트림: {res.stderr[:400]}")

        return f"/static/tasks/{task_id}/output.mp4"