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
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(json.loads(res.stdout)["format"]["duration"])
        except: return 4.0

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
        task_dir = os.path.join(self.tasks_base_dir, task_id)
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
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x020617:s=720x1280", "-vframes", "1", fb], stdout=subprocess.PIPE)
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

        f_hook_txt = f"static/tasks/{task_id}/hook.txt"
        f_body_txt = f"static/tasks/{task_id}/body.txt"
        f_ending_txt = f"static/tasks/{task_id}/ending.txt"

        with open(os.path.join(task_dir, "hook.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("hook_text", "")))
        with open(os.path.join(task_dir, "body.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("body_text", "")))
        with open(os.path.join(task_dir, "ending.txt"), "w", encoding="utf-8") as f: f.write(self._wrap_text(safe_settings.get("ending_text", "")))

        c_size = safe_settings.get("fontSize", 42)
        c_line1, c_line2, c_boxcolor = "0xFFFFFF", "0x00D4FF", "0x000000@0.6"
        
        if template == "dark":
            c_line1, c_line2, c_boxcolor = "0xCCCCCC", "0x4A4AF7", "0x111111@0.8"
        elif template == "mint":
            c_line1, c_line2, c_boxcolor = "0xFFFFFF", "0x6EF5A3", "0x052e16@0.9"
        elif template == "custom":
            c_line1 = safe_settings.get("colorLine1", "#FFFFFF").replace("#", "0x")
            c_line2 = safe_settings.get("colorLine2", "#FFD400").replace("#", "0x")

        c_channel = safe_settings.get("channelName", "SuperShorts")
        st_body, st_ending = d_hook, d_hook + d_body

        # 🎯 [핵심 교정 완비] 수식의 콤마가 필터 분기문으로 오해받지 않도록 값 전체를 싱글 쿼테이션(')으로 엄격 격리
        motion_hook = "y='if(lt(t,0.3),h-100-((t/0.3)*180),h-280)'"
        motion_body = f"y='if(lt(t-{st_body},0.3),h-100-(((t-{st_body})/0.3)*180),h-280)'"
        motion_ending = f"y='if(lt(t-{st_ending},0.3),h-100-(((t-{st_ending})/0.3)*180),h-280)'"

        graphic_filter = (
            f"{v_filters}{v_concat};"
            f"[v_base]drawtext=text='@{c_channel}':x=(w-tw)/2:y=80:fontsize=26:fontcolor=white@0.4,"
            f"drawtext=textfile='{f_hook_txt}':{motion_hook}:x=(w-tw)/2:fontsize={c_size}:fontcolor={c_line1}:box=1:boxcolor={c_boxcolor}:boxborderw=20:enable='between(t,0,{st_body})',"
            f"drawtext=textfile='{f_body_txt}':{motion_body}:x=(w-tw)/2:fontsize={c_size}:fontcolor={c_line2}:box=1:boxcolor={c_boxcolor}:boxborderw=20:enable='between(t,{st_body},{st_ending})',"
            f"drawtext=textfile='{f_ending_txt}':{motion_ending}:x=(w-tw)/2:fontsize={c_size}:fontcolor={c_line1}:box=1:boxcolor={c_boxcolor}:boxborderw=20:enable='between(t,{st_ending},{total_duration})'[v_final]"
        )

        use_bgm = safe_settings.get("autoBgm", True)
        bgm_track_id = safe_settings.get("bgmTrack", "track_01")
        bgm_file_path = f"static/bgm/{bgm_track_id}.mp3"
        
        audio_inputs = []
        bgm_mixing_filter = ""

        if is_voice_none:
            audio_inputs.extend(["-f", "lavfi", "-i", f"anullsrc=cl=stereo:r=44100:d={total_duration}"])
            voice_filter_stmt = f"[{idx_v}:a]"
            idx_bgm_input = idx_v + 1
        else:
            audio_inputs.extend(["-i", p_hook, "-i", p_body, "-i", p_ending])
            voice_filter_stmt = f"[{idx_v}:a][{idx_v+1}:a][{idx_v+2}:a]concat=n=3:v=0:a=1[a_voice_merged]; [a_voice_merged]"
            idx_bgm_input = idx_v + 3

        if use_bgm:
            if os.path.exists(bgm_file_path):
                audio_inputs.extend(["-stream_loop", "-1", "-i", bgm_file_path])
                bgm_filter_stmt = f"[{idx_bgm_input}:a]volume=0.15,asetpts=0[bgm_fixed];"
            else:
                audio_inputs.extend(["-f", "lavfi", "-i", f"anullsrc=cl=stereo:r=44100:d={total_duration}"])
                bgm_filter_stmt = f"[{idx_bgm_input}:a]volume=0.0,asetpts=0[bgm_fixed];"
            
            bgm_mixing_filter = f"{voice_filter_stmt}anull[a_src]; {bgm_filter_stmt} [a_src][bgm_fixed]amix=inputs=2:duration=first[a_final];"
        else:
            bgm_mixing_filter = f"{voice_filter_stmt}anull[a_final];"

        cmd = [
            "ffmpeg", "-y",
            *mapped_inputs,
            *audio_inputs,
            "-filter_complex", f"{bgm_mixing_filter} {graphic_filter}",
            "-map", "[v_final]", "-map", "[a_final]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-t", f"{total_duration:.2f}",
            final_output_path
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_log = stderr.decode('utf-8', errors='ignore')
            print(f"❌ [FFmpeg 치명적 에러로그]\n{error_log}")
            raise Exception("FFmpeg 미디어 합성에 실패했습니다.")

        return f"/static/output_{session_id}.mp4"