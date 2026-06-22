import os
import subprocess
import httpx
import json
import re

class VideoService:
    FPS = 30  # 출력 프레임레이트 (켄번스 모션 계산 기준)

    def __init__(self):
        self.static_dir = "static"
        self.tasks_base_dir = os.path.join(self.static_dir, "tasks")
        os.makedirs(self.tasks_base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.static_dir, "bgm"), exist_ok=True)
        # 한글 폰트 폴더 선행 생성 (여기에 .ttf 파일을 넣어두면 됩니다)
        os.makedirs(os.path.join(self.static_dir, "fonts"), exist_ok=True)

    def _get_duration(self, file_path) -> float:
        if not os.path.exists(file_path): return 0.0
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", file_path]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(json.loads(res.stdout)["format"]["duration"])
        except Exception as e:
            print(f"⚠️ [FFprobe 계측 실패]: {e}")
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

    def ffmpeg_escape_path(self, path: str) -> str:
        # Windows 경로의 역슬래시(\)와 드라이브 콜론(C:)을 FFmpeg 필터 문법에 맞게 이스케이프
        return path.replace("\\", "/").replace(":", "\\:")

    def _resolve_font_path(self):
        """
        한글 자막용 폰트를 순서대로 탐색합니다.
        1) 프로젝트 번들 폰트 (static/fonts/ 안의 .ttf / .otf)  ← 가장 권장
        2) 윈도우 기본 한글 폰트 (맑은 고딕 등)
        3) 리눅스/맥 한글 폰트
        하나도 못 찾으면 None을 반환하고, 이 경우 시스템 기본 폰트로 폴백합니다.
        """
        bundle_dir = os.path.join(self.static_dir, "fonts")
        if os.path.isdir(bundle_dir):
            for fname in sorted(os.listdir(bundle_dir)):
                if fname.lower().endswith((".ttf", ".otf", ".ttc")):
                    return os.path.abspath(os.path.join(bundle_dir, fname))

        candidates = [
            r"C:\Windows\Fonts\malgun.ttf",        # 맑은 고딕 (Windows 기본)
            r"C:\Windows\Fonts\malgunbd.ttf",      # 맑은 고딕 Bold
            r"C:\Windows\Fonts\gulim.ttc",         # 굴림
            r"C:\Windows\Fonts\batang.ttc",        # 바탕
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",  # macOS
        ]
        for path in candidates:
            if os.path.exists(path):
                return os.path.abspath(path)
        return None

    def _kenburns_segment(self, idx: int, dur: float, zoom_in: bool) -> str:
        """
        정지 이미지 한 장에 '켄번스 효과'(미세한 줌)를 입혀 720x1280 영상 세그먼트로 만듭니다.
        - 입력은 -loop 없이 단일 이미지로 넣고, zoompan이 d(프레임수)만큼 직접 프레임을 생성합니다.
          (-loop 1 + zoompan을 함께 쓰면 길이가 폭주하는 함정이 있어 의도적으로 분리)
        - 줌 전에 고해상도(3배)로 업스케일해 줌 진행 시 픽셀 떨림(jitter)을 방지합니다.
        - zoom_in=True면 서서히 확대, False면 확대 상태에서 서서히 축소 → 장면마다 번갈아 적용해 단조로움 제거.
        """
        frames = max(1, round(dur * self.FPS))
        if zoom_in:
            z = "min(zoom+0.0010,1.25)"
        else:
            z = "if(eq(on,0),1.25,max(zoom-0.0010,1.0))"
        return (
            f"[{idx}:v]scale=2160:3840:force_original_aspect_ratio=increase,"
            f"crop=2160:3840,zoompan=z='{z}':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=720x1280:fps={self.FPS},setsar=1[v{idx}];"
        )

    async def generate_shorts_video(self, task_id: str, images: list, template: str = "basic", settings: dict = None) -> dict:
        safe_settings = settings or {}
        images = images or []

        task_dir = os.path.abspath(os.path.join(self.tasks_base_dir, task_id))
        os.makedirs(task_dir, exist_ok=True)

        out_filename = "output.mp4"
        p_hook = "speech_hook.mp3"
        p_body = "speech_body.mp3"
        p_ending = "speech_ending.mp3"

        abs_p_hook = os.path.join(task_dir, p_hook)
        abs_p_body = os.path.join(task_dir, p_body)
        abs_p_ending = os.path.join(task_dir, p_ending)

        is_voice_none = not (os.path.exists(abs_p_hook) and os.path.exists(abs_p_body) and os.path.exists(abs_p_ending))

        if is_voice_none:
            d_hook = max(4.0, len(safe_settings.get("hook_text") or "") * 0.18)
            d_body = max(6.5, len(safe_settings.get("body_text") or "") * 0.18)
            d_ending = max(4.0, len(safe_settings.get("ending_text") or "") * 0.18)
        else:
            d_hook = self._get_duration(abs_p_hook) or 4.0
            d_body = self._get_duration(abs_p_body) or 7.0
            d_ending = self._get_duration(abs_p_ending) or 4.0

        total_duration = d_hook + d_body + d_ending

        local_images = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for idx, img_url in enumerate(images):
                if img_url.startswith("blob:") or not img_url.startswith("http"): continue
                try:
                    resp = await client.get(img_url, headers={"User-Agent": "Mozilla"}, timeout=20.0)
                    if resp.status_code == 200:
                        filename = f"img_{idx}.jpg"
                        path = os.path.join(task_dir, filename)
                        with open(path, "wb") as f: f.write(resp.content)
                        local_images.append(filename)
                except Exception as e:
                    print(f"❌ 이미지 다운로드 에러: {e}")

        if not local_images:
            fb_filename = "fb.jpg"
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x020617:s=720x1280", "-vframes", "1", os.path.join(task_dir, fb_filename)], capture_output=True)
            local_images.append(fb_filename)

        img_count = len(local_images)
        if img_count == 1:
            arr_hook, arr_body, arr_ending = [local_images[0]], [local_images[0]], [local_images[0]]
        elif img_count == 2:
            arr_hook, arr_body, arr_ending = [local_images[0]], [local_images[1]], [local_images[1]]
        else:
            arr_hook = [local_images[0]]
            arr_ending = [local_images[-1]]
            arr_body = local_images[1:-1]

        dur_hook_img = d_hook / max(1, len(arr_hook))
        dur_body_img = d_body / max(1, len(arr_body))
        dur_ending_img = d_ending / max(1, len(arr_ending))

        mapped_inputs = []
        v_filters = ""
        v_concat = ""
        idx_v = 0

        # 🚨 [핵심 업그레이드] 정지 슬라이드 → 켄번스(줌) 모션 세그먼트로 변경
        # 입력은 -loop 없이 단일 이미지로 넣고, zoompan이 길이를 직접 생성합니다.
        for img in arr_hook:
            mapped_inputs.extend(["-i", img])
            v_filters += self._kenburns_segment(idx_v, dur_hook_img, zoom_in=(idx_v % 2 == 0))
            v_concat += f"[v{idx_v}]"
            idx_v += 1
        for img in arr_body:
            mapped_inputs.extend(["-i", img])
            v_filters += self._kenburns_segment(idx_v, dur_body_img, zoom_in=(idx_v % 2 == 0))
            v_concat += f"[v{idx_v}]"
            idx_v += 1
        for img in arr_ending:
            mapped_inputs.extend(["-i", img])
            v_filters += self._kenburns_segment(idx_v, dur_ending_img, zoom_in=(idx_v % 2 == 0))
            v_concat += f"[v{idx_v}]"
            idx_v += 1

        v_concat += f"concat=n={idx_v}:v=1:a=0[v_base]"

        with open(os.path.join(task_dir, "hook.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("hook_text") or ""))
        with open(os.path.join(task_dir, "body.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("body_text") or ""))
        with open(os.path.join(task_dir, "ending.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("ending_text") or ""))

        try:
            raw_size = int(safe_settings.get("fontSize") or 42)
        except (ValueError, TypeError):
            raw_size = 42
        c_size = max(20, min(raw_size, 100))

        # FFmpeg 파서를 고장내는 헥사코드(0x, #)를 배제하고 영문 색상 이름으로 하드코딩
        c_line1, c_line2, c_boxcolor = "white", "cyan", "black@0.6"
        if template == "dark":
            c_line1, c_line2, c_boxcolor = "white", "blue", "black@0.8"
        elif template == "mint":
            c_line1, c_line2, c_boxcolor = "white", "green", "black@0.9"
        elif template == "custom":
            c_line1 = "white"
            c_line2 = "yellow"

        c_channel = safe_settings.get("channelName") or "SuperShorts"
        safe_channel = re.sub(r"[^a-zA-Z0-9가-힣 _\-]", "", c_channel)
        safe_channel = safe_channel or "SuperShorts"

        st_body, st_ending = d_hook, d_hook + d_body

        motion_hook = "if(lt(t\\,0.3)\\,h-100-((t/0.3)*180)\\,h-280)"
        motion_body = f"if(lt(t-{st_body}\\,0.3)\\,h-100-(((t-{st_body})/0.3)*180)\\,h-280)"
        motion_ending = f"if(lt(t-{st_ending}\\,0.3)\\,h-100-(((t-{st_ending})/0.3)*180)\\,h-280)"

        # 한글 자막이 □(네모)로 깨지는 문제 방지: 한글 글리프가 포함된 폰트를 명시적으로 지정
        font_path = self._resolve_font_path()
        if font_path:
            font_arg = f"fontfile='{self.ffmpeg_escape_path(font_path)}':"
            print(f"✅ [자막 폰트 적용]: {font_path}")
        else:
            font_arg = ""
            print("⚠️ [경고] 한글 폰트를 찾지 못했습니다. backend/static/fonts/ 폴더에 NanumGothic.ttf 같은 한글 폰트를 넣어주세요.")

        graphic_filter = (
            f"{v_filters}{v_concat};"
            f"[v_base]drawtext={font_arg}text='@{safe_channel}':x=(w-tw)/2:y=80:fontsize=26:fontcolor=white@0.4,"
            f"drawtext={font_arg}textfile=hook.txt:x=(w-tw)/2:y={motion_hook}:fontsize={c_size}:fontcolor={c_line1}:box=1:boxcolor={c_boxcolor}:boxborderw=20:enable='between(t,0,{st_body})',"
            f"drawtext={font_arg}textfile=body.txt:x=(w-tw)/2:y={motion_body}:fontsize={c_size}:fontcolor={c_line2}:box=1:boxcolor={c_boxcolor}:boxborderw=20:enable='between(t,{st_body},{st_ending})',"
            f"drawtext={font_arg}textfile=ending.txt:x=(w-tw)/2:y={motion_ending}:fontsize={c_size}:fontcolor={c_line1}:box=1:boxcolor={c_boxcolor}:boxborderw=20:enable='between(t,{st_ending},{total_duration})'[v_final]"
        )

        use_bgm = safe_settings.get("autoBgm", True)
        bgm_track_id = safe_settings.get("bgmTrack") or "track_01"
        bgm_file_path = os.path.abspath(os.path.join(self.static_dir, "bgm", f"{bgm_track_id}.mp3"))

        audio_inputs = []
        bgm_mixing_filter = ""
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
            "-r", str(self.FPS),
            "-t", f"{total_duration:.2f}",
            out_filename
        ]

        res = subprocess.run(cmd, capture_output=True, cwd=task_dir)

        if res.returncode != 0:
            err_log = res.stderr.decode('utf-8', errors='replace') if res.stderr else "알 수 없는 에러"
            print("\n" + "=" * 60)
            print("🚨 [FFmpeg 실행 명령어]")
            print(" ".join(cmd))
            print("=" * 60)
            print("🚨 [FFmpeg 에러 원인]")
            print(err_log)
            print("=" * 60 + "\n")
            raise Exception(f"FFmpeg 합성 실패\n에러: {err_log[:400]}")

        return {"video_url": f"/static/tasks/{task_id}/{out_filename}"}
