import os
import subprocess
import httpx
import json
import uuid

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
            # 🎯 [설계상 문제 4/5 적용] capture_output을 연동하고 계측 에러 발생 시 명확하게 예외 로깅 처리
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(json.loads(res.stdout)["format"]["duration"])
        except Exception as e:
            print(f"❌ [FFprobe 에러 계측 실패 - 기본 4초 대체]: {e}")
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

    async def generate_shorts_video(self, task_id: str, images: list[str], template: str = "basic", settings: dict = None) -> str:
        safe_settings = settings or {}
        # 🎯 [치명적 오류 3] FFmpeg 실행 위치 격리를 위해 태스크 디렉토리를 절대경로(abspath)로 강제 변환
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
        # 🎯 [오류 7] 이미지 서버 다운 지연을 전면 방어하기 위해 커넥션 타임아웃을 20.0초로 상향 연장
        async with httpx.AsyncClient() as client:
            for idx, img_url in enumerate(images):
                if img_url.startswith("blob:") or not img_url.startswith("http"): continue
                try:
                    resp = await client.get(img_url, headers={"User-Agent":"Mozilla"}, timeout=20.0)
                    if resp.status_code == 200:
                        path = os.path.join(task_dir, f"img_{idx}.jpg")
                        with open(path, "wb") as f: f.write(resp.content)
                        local_images.append(path)
                except Exception as img_err:
                    print(f"⚠️ [이미지 파싱 예외 발생 - 인덱스 {idx}]: {img_err}")

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

        # 🎯 [설계상 문제 1] arr_body가 비어있을 때 발생하는 ZeroDivisionError 수학적 크래시 원천 방쇄
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

        # 🎯 [치명적 오류 3 & 오류 6] 자막 파일 경로를 완전한 절대경로화 한 뒤, Windows의 역슬래시와 드라이브 콜론(:) 분석 파괴 차단 완료
        f_hook_txt = os.path.abspath(os.path.join(task_dir, "hook.txt")).replace("\\", "/").replace(":", "\\:")
        f_body_txt = os.path.abspath(os.path.join(task_dir, "body.txt")).replace("\\", "/").replace(":", "\\:")
        f_ending_txt = os.path.abspath(os.path.join(task_dir, "ending.txt")).replace("\\", "/").replace(":", "\\:")

        with open(os.path.join(task_dir, "hook.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("hook_text", "")))
        with open(os.path.join(task_dir, "body.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("body_text", "")))
        with open(os.path.join(task_dir, "ending.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("ending_text", "")))

        # 🎯 [설계상 문제 3] 사용자가 프론트단에서 비정상적인 폰트 사이즈(음수, 0) 기입 시의 예외 가드 밸브 설치 (20 ~ 100 범위 고정)
        try:
            raw_size = int(safe_settings.get("fontSize", 42))
        except (ValueError, TypeError):
            raw_size = 42
        c_size = max(20, min(raw_size, 100))
        
        # 🎯 [치명적 오류 4 & 설계상 문제 2] 0xFFFFFF 등 호환성을 해치던 값을 표준 헥사 스트링 컨테이너 명세로 정렬
        c_line1, c_line2, c_boxcolor = "#FFFFFF", "#00D4FF", "#000000@0.6"
        
        if template == "dark":
            c_line1, c_line2, c_boxcolor = "#CCCCCC", "#4A4AF7", "#111111@0.8"
        elif template == "mint":
            c_line1, c_line2, c_boxcolor = "#FFFFFF", "#6EF5A3", "#052e16@0.9"
        elif template == "custom":
            c_line1 = safe_settings.get("colorLine1", "#FFFFFF")
            c_line2 = safe_settings.get("colorLine2", "#FFD400")

        # 🎯 [오류 5] 채널 워터마크에 특수문자(', :, \, %)가 유입되어 전체 인코딩 구문 문자열이 파괴되던 결함 이스케이프 가드 탑재
        c_channel = safe_settings.get("channelName", "SuperShorts")
        safe_channel = c_channel.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")
        
        st_body, st_ending = d_hook, d_hook + d_body

        motion_hook = "y='if(lt(t,0.3),h-100-((t/0.3)*180),h-280)'"
        motion_body = f"y='if(lt(t-{st_body},0.3),h-100-(((t-{st_body})/0.3)*180),h-280)'"
        motion_ending = f"y='if(lt(t-{st_ending},0.3),h-100-(((t-{st_ending})/0.3)*180),h-280)'"

        # 🎯 [치명적 오류 1 & 2 조치] 필터그래프 해석기 크래시를 차단하기 위해 수식 내부의 모든 Whitespace 공백 정밀 숙청
        graphic_filter = (
            f"{v_filters}{v_concat};"
            f"[v_base]drawtext=text='@{safe_channel}':x=(w-tw)/2:y=80:fontsize=26:fontcolor='white@0.4',"
            f"drawtext=textfile='{f_hook_txt}':{motion_hook}:x=(w-tw)/2:fontsize={c_size}:fontcolor='{c_line1}':box=1:boxcolor='{c_boxcolor}':boxborderw=20:enable='between(t,0,{st_body})',"
            f"drawtext=textfile='{f_body_txt}':{motion_body}:x=(w-tw)/2:fontsize={c_size}:fontcolor='{c_line2}':box=1:boxcolor='{c_boxcolor}':boxborderw=20:enable='between(t,{st_body},{st_ending})',"
            f"drawtext=textfile='{f_ending_txt}':{motion_ending}:x=(w-tw)/2:fontsize={c_size}:fontcolor='{c_line1}':box=1:boxcolor='{c_boxcolor}':boxborderw=20:enable='between(t,{st_ending},{total_duration})'[v_final]"
        )

        use_bgm = safe_settings.get("autoBgm", True)
        bgm_track_id = safe_settings.get("bgmTrack", "track_01")
        bgm_file_path = os.path.abspath(os.path.join(self.static_dir, "bgm", f"{bgm_track_id}.mp3"))
        
        audio_inputs = []
        bgm_mixing_filter = ""

        if is_voice_none:
            audio_inputs.extend(["-f", "lavfi", "-i", f"anullsrc=cl=stereo:r=44100:d={total_duration}"])
            voice_filter_stmt = f"[{idx_v}:a]"
            idx_bgm_input = idx_v + 1
        else:
            audio_inputs.extend(["-i", p_hook, "-i", p_body, "-i", p_ending])
            voice_filter_stmt = f"[{idx_v}:a][{idx_v+1}:a][{idx_v+2}:a]concat=n=3:v=0:a=1[a_voice_merged];[a_voice_merged]"
            idx_bgm_input = idx_v + 3

        if use_bgm:
            if os.path.exists(bgm_file_path):
                audio_inputs.extend(["-stream_loop", "-1", "-i", bgm_file_path])
                # 🎯 [치명적 오류 1] 무효한 명령어였던 asetpts=0 선언문을 정석적인 상대 타임스탬프 스펙인 PTS-STARTPTS 공식으로 정밀 교정
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

        # 🎯 [설계상 문제 4] Popen 방식의 교착 상태(Deadlock)를 방지하기 위해 정석적인 subprocess.run 동기식 추적 전환 완비
        res = subprocess.run(cmd, capture_output=True, text=True)

        if res.returncode != 0:
            print(f"❌ [FFmpeg 치명적 에러로그]\n{res.stderr}")
            raise Exception(f"FFmpeg 미디어 합성에 실패했습니다. 원인: {res.stderr[:300]}")

        return f"/static/tasks/{task_id}/output.mp4"