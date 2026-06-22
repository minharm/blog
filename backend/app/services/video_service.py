import os
import re
import json
import subprocess
import httpx


class VideoService:
    # ---- 캔버스 / 레이아웃 (레퍼런스: 상단 제목 + 가운데 이미지 카드 + 하단 자막) ----
    W, H = 1080, 1920
    FPS = 30
    CARD_W, CARD_H = 1000, 1080
    CARD_X, CARD_Y = 40, 470
    MAX_DURATION = 30.0
    TITLE_MAX = 86      # 제목 최대 글자크기
    TITLE_MIN = 46      # 제목 최소 글자크기
    SIDE_MARGIN = 70    # 제목 좌우 여백

    def __init__(self):
        self.static_dir = "static"
        self.tasks_base_dir = os.path.join(self.static_dir, "tasks")
        os.makedirs(self.tasks_base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.static_dir, "bgm"), exist_ok=True)
        os.makedirs(os.path.join(self.static_dir, "fonts"), exist_ok=True)

    # ---------------- 유틸 ----------------
    def _get_duration(self, file_path) -> float:
        if not os.path.exists(file_path):
            return 0.0
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", file_path]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(json.loads(res.stdout)["format"]["duration"])
        except Exception as e:
            print(f"⚠️ [FFprobe 계측 실패]: {e}")
            return 4.0

    def ffmpeg_escape_path(self, path: str) -> str:
        return path.replace("\\", "/").replace(":", "\\:")

    @staticmethod
    def _char_units(ch: str) -> float:
        """글자 폭 추정 (한글=1.0, 영문/숫자=0.55, 공백=0.4)."""
        if ch == " ":
            return 0.4
        o = ord(ch)
        if o >= 0x1100:   # 한글/CJK
            return 1.0
        return 0.55

    def _line_units(self, line: str) -> float:
        return sum(self._char_units(c) for c in line)

    def _wrap_by_units(self, text: str, max_units: float):
        """단어 단위로 max_units 폭에 맞춰 줄바꿈."""
        words = (text or "").split()
        lines, cur, cur_u = [], "", 0.0
        for w in words:
            wu = self._line_units(w) + (0.4 if cur else 0)
            if cur and cur_u + wu > max_units:
                lines.append(cur)
                cur, cur_u = w, self._line_units(w)
            else:
                cur += (" " if cur else "") + w
                cur_u += wu
        if cur:
            lines.append(cur)
        return lines or [""]

    def _fit_title(self, text: str):
        """
        제목이 화면을 벗어나지 않도록 글자크기를 자동 계산하고 줄바꿈한다.
        반환: (lines:list[str], fontsize:int)
        """
        text = (text or "").strip()
        if not text:
            return [""], self.TITLE_MAX
        usable = self.W - self.SIDE_MARGIN * 2
        total_u = self._line_units(text)
        # 2줄 기준으로 필요한 크기 추정 후, 실제로 안 넘칠 때까지 줄여가며 확정
        for size in range(self.TITLE_MAX, self.TITLE_MIN - 1, -2):
            max_units = usable / size
            lines = self._wrap_by_units(text, max_units)
            if len(lines) <= 3 and all(self._line_units(l) * size <= usable for l in lines):
                return lines, size
        # 최소 크기로도 안 되면 최소 크기 + 강제 줄바꿈
        size = self.TITLE_MIN
        lines = self._wrap_by_units(text, usable / size)
        return lines[:4], size

    def _caption_chunks(self, text: str):
        """본문을 '짧은 한 입' 단위로 쪼갠다 (레퍼런스처럼 자막이 짧게 자주 바뀜)."""
        text = (text or "").strip()
        if not text:
            return []
        # 문장부호 + 길이 기준으로 분할
        rough = re.split(r'(?<=[.!?。,])\s+', text)
        chunks = []
        for part in rough:
            part = part.strip().rstrip(",")
            if not part:
                continue
            # 너무 길면 단어 단위로 ~16자 폭으로 추가 분할
            for line in self._wrap_by_units(part, 16):
                if line.strip():
                    chunks.append(line.strip())
        return chunks

    def _resolve_fonts(self, family: str):
        fdir = os.path.join(self.static_dir, "fonts")
        # (제목용 가장 굵은 파일, 자막용 보통 파일)
        family_map = {
            "Pretendard":   (["Pretendard-Black.ttf", "Pretendard-ExtraBold.ttf", "Pretendard-Bold.ttf"], "Pretendard-Regular.ttf"),
            "GmarketSans":  (["GmarketSansTTFBold.ttf"], "GmarketSansTTFMedium.ttf"),
            "BlackHanSans": (["BlackHanSans-Regular.ttf"], "BlackHanSans-Regular.ttf"),
            "NanumGothic":  (["NanumGothicExtraBold.ttf", "NanumGothicBold.ttf"], "NanumGothic.ttf"),
            "Jalnan":       (["Jalnan2TTF.ttf", "JalnanGothicTTF.ttf"], "Jalnan2TTF.ttf"),
        }

        def find(name):
            if not name:
                return None
            p = os.path.join(fdir, name)
            return os.path.abspath(p) if os.path.exists(p) else None

        bold = reg = None
        if family in family_map:
            for cand in family_map[family][0]:
                bold = bold or find(cand)
            reg = find(family_map[family][1])

        # 폴더 안에서 가장 굵은(Black>ExtraBold>Bold) 폰트를 제목용으로 자동 선택
        if os.path.isdir(fdir):
            ttfs = [f for f in os.listdir(fdir) if f.lower().endswith((".ttf", ".otf", ".ttc"))]
            def heaviest(files):
                order = ["black", "extrabold", "heavy", "bold", "semibold", "medium", "regular"]
                best, best_rank = None, 999
                for f in sorted(files):
                    low = f.lower()
                    rank = next((i for i, k in enumerate(order) if k in low), 500)
                    if rank < best_rank:
                        best, best_rank = f, rank
                return os.path.abspath(os.path.join(fdir, best)) if best else None
            anybold = heaviest(ttfs)
            anyreg = os.path.abspath(os.path.join(fdir, sorted(ttfs)[0])) if ttfs else None
            bold = bold or anybold
            reg = reg or anyreg

        for p in [r"C:\Windows\Fonts\malgunbd.ttf", r"C:\Windows\Fonts\malgun.ttf",
                  "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                  "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
                  "/System/Library/Fonts/AppleSDGothicNeo.ttc"]:
            if os.path.exists(p):
                bold = bold or os.path.abspath(p)
                reg = reg or os.path.abspath(p)
        return bold, reg

    def _kenburns_card(self, idx: int, dur: float, zoom_in: bool) -> str:
        frames = max(1, round(dur * self.FPS))
        up_w, up_h = self.CARD_W * 3, self.CARD_H * 3
        z = "min(zoom+0.0012,1.28)" if zoom_in else "if(eq(on,0),1.28,max(zoom-0.0012,1.0))"
        return (
            f"[{idx}:v]scale={up_w}:{up_h}:force_original_aspect_ratio=increase,"
            f"crop={up_w}:{up_h},zoompan=z='{z}':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={self.CARD_W}x{self.CARD_H}:fps={self.FPS},setsar=1[v{idx}];"
        )

    # ---------------- 메인 ----------------
    async def generate_shorts_video(self, task_id: str, images: list, template: str = "basic", settings: dict = None) -> dict:
        s = settings or {}
        images = images or []
        task_dir = os.path.abspath(os.path.join(self.tasks_base_dir, task_id))
        os.makedirs(task_dir, exist_ok=True)
        out_filename = "output.mp4"

        ap_hook = os.path.join(task_dir, "speech_hook.mp3")
        ap_body = os.path.join(task_dir, "speech_body.mp3")
        ap_ending = os.path.join(task_dir, "speech_ending.mp3")
        is_voice_none = not (os.path.exists(ap_hook) and os.path.exists(ap_body) and os.path.exists(ap_ending))

        hook_text = (s.get("hook_text") or "").strip()
        body_text = (s.get("body_text") or "").strip()
        ending_text = (s.get("ending_text") or "").strip()

        voice_speed = 1.0
        if is_voice_none:
            d_hook = max(2.5, len(hook_text) * 0.16)
            d_body = max(5.0, len(body_text) * 0.16)
            d_ending = max(2.5, len(ending_text) * 0.16)
            total = d_hook + d_body + d_ending
            if total > self.MAX_DURATION:
                f = self.MAX_DURATION / total
                d_hook, d_body, d_ending = d_hook * f, d_body * f, d_ending * f
                total = self.MAX_DURATION
            print("ℹ️ 음성 파일이 없어 무음(자막 전용)으로 생성합니다. 음성을 넣으려면 Step3에서 성우를 선택하세요.")
        else:
            dh = self._get_duration(ap_hook) or 3.0
            db = self._get_duration(ap_body) or 6.0
            de = self._get_duration(ap_ending) or 3.0
            voice_total = dh + db + de
            # ✅ [요청 3] 음성이 30초보다 길면 자동으로 빠르게(최대 1.8배) 재생해 영상 길이에 맞춤
            if voice_total > self.MAX_DURATION:
                voice_speed = min(voice_total / self.MAX_DURATION, 1.8)
                print(f"⏩ 음성이 {voice_total:.1f}초로 길어 {voice_speed:.2f}배속으로 자동 조절합니다.")
            d_hook, d_body, d_ending = dh / voice_speed, db / voice_speed, de / voice_speed
            total = d_hook + d_body + d_ending
            if total > self.MAX_DURATION:
                total = self.MAX_DURATION
        st_body = d_hook
        st_ending = d_hook + d_body

        # ---- 이미지 다운로드 (선택 순서 유지) ----
        local_images = []
        async with httpx.AsyncClient(follow_redirects=True) as client:
            for idx, img_url in enumerate(images):
                if not img_url or img_url.startswith("blob:") or not img_url.startswith("http"):
                    continue
                try:
                    r = await client.get(img_url, headers={"User-Agent": "Mozilla"}, timeout=20.0)
                    if r.status_code == 200:
                        fn = f"img_{idx}.jpg"
                        with open(os.path.join(task_dir, fn), "wb") as f:
                            f.write(r.content)
                        local_images.append(fn)
                except Exception as e:
                    print(f"❌ 이미지 다운로드 에러: {e}")
        if not local_images:
            fb = "fb.jpg"
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x111111:s={self.CARD_W}x{self.CARD_H}", "-vframes", "1", os.path.join(task_dir, fb)], capture_output=True)
            local_images.append(fb)

        n = len(local_images)
        seg_dur = total / n
        mapped_inputs, v_filters, v_concat = [], "", ""
        for i, img in enumerate(local_images):
            mapped_inputs.extend(["-i", img])
            v_filters += self._kenburns_card(i, seg_dur, zoom_in=(i % 2 == 0))
            v_concat += f"[v{i}]"
        v_concat += f"concat=n={n}:v=1:a=0[cards]"
        v_pad = f"[cards]pad={self.W}:{self.H}:{self.CARD_X}:{self.CARD_Y}:black[v_base]"
        idx_after_imgs = n

        # ---- 제목: 자동 맞춤 줄바꿈 + 글자크기 ----
        title_lines, title_size = self._fit_title(hook_text)
        for i, ln in enumerate(title_lines):
            with open(os.path.join(task_dir, f"title_{i}.txt"), "w", encoding="utf-8") as f:
                f.write(ln)

        # ---- 자막: 짧은 청크 (본문 → 엔딩 순서로 전체 구간 채움) ----
        body_chunks = self._caption_chunks(body_text)
        end_chunks = self._caption_chunks(ending_text)
        for i, c in enumerate(body_chunks):
            with open(os.path.join(task_dir, f"cb_{i}.txt"), "w", encoding="utf-8") as f:
                f.write(c)
        for i, c in enumerate(end_chunks):
            with open(os.path.join(task_dir, f"ce_{i}.txt"), "w", encoding="utf-8") as f:
                f.write(c)

        # ---- 색상 / 폰트 ----
        point = {"basic": "yellow", "dark": "yellow", "mint": "#34d399",
                 "sunset": "orange", "ocean": "#22d3ee"}.get(template, "yellow")
        if template == "custom" and s.get("colorLine2"):
            point = s.get("colorLine2")
        point = point.replace("#", "0x") if point.startswith("#") else point

        family = s.get("fontFamily") or "Pretendard"
        f_bold, f_reg = self._resolve_fonts(family)
        bold_arg = f"fontfile='{self.ffmpeg_escape_path(f_bold)}':" if f_bold else ""
        reg_arg = f"fontfile='{self.ffmpeg_escape_path(f_reg)}':" if f_reg else ""
        if not f_bold:
            print("⚠️ static/fonts/ 에 한글 폰트가 없어 시스템 폰트로 폴백합니다.")

        try:
            cap_size = int(s.get("fontSize") or 66)
        except (ValueError, TypeError):
            cap_size = 66
        cap_size = max(52, min(cap_size, 96))

        # (요청 1: 채널명 워터마크 표시는 제거)
        draw = []

        # 제목 (상시): 1번째 줄 흰색, 나머지 포인트색, 화면 안에 들어오도록 자동 크기
        line_h = int(title_size * 1.22)
        block_h = line_h * len(title_lines)
        title_top = max(70, (self.CARD_Y - 60 - block_h) // 2 + 20)
        for i in range(len(title_lines)):
            color = "white" if i == 0 else point
            y = title_top + i * line_h
            draw.append(
                f"drawtext={bold_arg}textfile=title_{i}.txt:x=(w-tw)/2:y={y}:fontsize={title_size}:"
                f"fontcolor={color}:borderw=7:bordercolor=black:shadowcolor=black@0.5:shadowx=0:shadowy=4"
            )

        # 하단 자막: 카드 아래 검은 띠 중앙, 짧게 자주 교체 + 그림자로 또렷하게
        cap_y = self.CARD_Y + self.CARD_H + 90
        nb, ne = len(body_chunks), len(end_chunks)

        # ✅ [요청 2] 자막을 글자 수에 비례해 배분 → 말하는 속도와 더 잘 맞음
        def _weighted_windows(chunks, t0, t1):
            if not chunks:
                return []
            weights = [max(1, len(c)) for c in chunks]
            wsum = sum(weights)
            span = t1 - t0
            out, acc = [], t0
            for i, w in enumerate(chunks):
                seg = span * weights[i] / wsum
                a, b = acc, (t1 if i == len(chunks) - 1 else acc + seg)
                out.append((a, b))
                acc = b
            return out

        for i, (a, b) in enumerate(_weighted_windows(body_chunks, st_body, st_ending)):
            draw.append(
                f"drawtext={reg_arg}textfile=cb_{i}.txt:x=(w-tw)/2:y={cap_y}:fontsize={cap_size}:"
                f"fontcolor=white:borderw=5:bordercolor=black:shadowcolor=black@0.55:shadowx=0:shadowy=3:"
                f"enable='between(t,{a:.2f},{b:.2f})'"
            )
        for i, (a, b) in enumerate(_weighted_windows(end_chunks, st_ending, total)):
            draw.append(
                f"drawtext={reg_arg}textfile=ce_{i}.txt:x=(w-tw)/2:y={cap_y}:fontsize={cap_size}:"
                f"fontcolor=white:borderw=5:bordercolor=black:shadowcolor=black@0.55:shadowx=0:shadowy=3:"
                f"enable='between(t,{a:.2f},{b:.2f})'"
            )

        graphic = f"{v_filters}{v_concat};{v_pad};[v_base]" + ",".join(draw) + "[v_final]"

        # ---- 오디오 (음성 + BGM) ----
        use_bgm = s.get("autoBgm", True)
        bgm_id = s.get("bgmTrack") or "track_01"
        bgm_path = os.path.abspath(os.path.join(self.static_dir, "bgm", f"{bgm_id}.mp3"))
        audio_inputs = []
        aidx = idx_after_imgs

        bgm_ok = use_bgm and os.path.exists(bgm_path)

        if is_voice_none:
            # 음성 없음: BGM이 메인 오디오 (또는 완전 무음)
            if bgm_ok:
                audio_inputs.extend(["-stream_loop", "-1", "-i", bgm_path])
                amix = f"[{aidx}:a]volume=0.8,asetpts=PTS-STARTPTS[a_final];"
                print(f"🎵 BGM 적용(메인): {bgm_path}")
            else:
                audio_inputs.extend(["-f", "lavfi", "-i", f"anullsrc=cl=stereo:r=44100:d={total}"])
                amix = f"[{aidx}:a]anull[a_final];"
                if use_bgm:
                    print(f"⚠️ BGM 파일 없음: {bgm_path}\n   → backend/static/bgm/ 에 {bgm_id}.mp3 를 넣어야 배경음악이 나옵니다.")
        else:
            # 음성 있음: 음성 1.0 + BGM 0.16 합성 (normalize=0 으로 음성이 작아지지 않게)
            audio_inputs.extend(["-i", "speech_hook.mp3", "-i", "speech_body.mp3", "-i", "speech_ending.mp3"])
            voice_stmt = f"[{aidx}:a][{aidx+1}:a][{aidx+2}:a]concat=n=3:v=0:a=1,atempo={voice_speed:.4f}[a_voice];"
            if bgm_ok:
                audio_inputs.extend(["-stream_loop", "-1", "-i", bgm_path])
                bgm_in = aidx + 3
                amix = (f"{voice_stmt}"
                        f"[{bgm_in}:a]volume=0.16,asetpts=PTS-STARTPTS[a_bgm];"
                        f"[a_voice][a_bgm]amix=inputs=2:duration=first:normalize=0:dropout_transition=0[a_final];")
                print(f"🎵 음성 + BGM 합성: {bgm_path}")
            else:
                amix = f"{voice_stmt}[a_voice]anull[a_final];"
                if use_bgm:
                    print(f"⚠️ BGM 파일 없음: {bgm_path} (음성만 출력)")

        cmd = [
            "ffmpeg", "-y",
            *mapped_inputs, *audio_inputs,
            "-filter_complex", f"{amix}{graphic}",
            "-map", "[v_final]", "-map", "[a_final]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-r", str(self.FPS), "-t", f"{total:.2f}",
            out_filename,
        ]
        res = subprocess.run(cmd, capture_output=True, cwd=task_dir)
        if res.returncode != 0:
            err = res.stderr.decode("utf-8", errors="replace") if res.stderr else "알 수 없는 에러"
            print("\n" + "=" * 60 + "\n🚨 [FFmpeg 명령어]\n" + " ".join(cmd))
            print("=" * 60 + "\n🚨 [FFmpeg 에러]\n" + err + "\n" + "=" * 60)
            raise Exception(f"FFmpeg 합성 실패\n{err[:400]}")

        return {"video_url": f"/static/tasks/{task_id}/{out_filename}"}
