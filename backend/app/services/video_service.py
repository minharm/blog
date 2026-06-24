import os
import re
import json
import subprocess
import httpx


class VideoService:
    W, H = 1080, 1920
    FPS = 30
    CARD_W, CARD_H = 1000, 1220
    CARD_X, CARD_Y = 40, 395
    MAX_DURATION = 30.0
    TITLE_MAX = 110
    TITLE_MIN = 46
    SIDE_MARGIN = 70
    XFADE = 0.5  # 장면 전환 길이(초)

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
            return 3.0

    def ffmpeg_escape_path(self, path: str) -> str:
        return path.replace("\\", "/").replace(":", "\\:")

    @staticmethod
    def _char_units(ch: str) -> float:
        if ch == " ":
            return 0.4
        return 1.0 if ord(ch) >= 0x1100 else 0.55

    def _line_units(self, line: str) -> float:
        return sum(self._char_units(c) for c in line)

    def _wrap_by_units(self, text: str, max_units: float):
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
        text = (text or "").strip()
        if not text:
            return [""], self.TITLE_MAX
        usable = self.W - self.SIDE_MARGIN * 2
        for size in range(self.TITLE_MAX, self.TITLE_MIN - 1, -2):
            lines = self._wrap_by_units(text, usable / size)
            if len(lines) <= 3 and all(self._line_units(l) * size <= usable for l in lines):
                return lines, size
        size = self.TITLE_MIN
        return self._wrap_by_units(text, usable / size)[:4], size

    def _caption_chunks(self, text: str):
        text = (text or "").strip()
        if not text:
            return []
        rough = re.split(r'(?<=[.!?。,])\s+', text)
        chunks = []
        for part in rough:
            part = part.strip().rstrip(",")
            if not part:
                continue
            for line in self._wrap_by_units(part, 16):
                if line.strip():
                    chunks.append(line.strip())
        return chunks

    def _resolve_fonts(self, family: str):
        fdir = os.path.join(self.static_dir, "fonts")
        family_map = {
            "Pretendard":   (["Pretendard-Black.ttf", "Pretendard-ExtraBold.ttf", "Pretendard-Bold.ttf"], "Pretendard-Regular.ttf"),
            "GmarketSans":  (["GmarketSansTTFBold.ttf"], "GmarketSansTTFMedium.ttf"),
            "BlackHanSans": (["BlackHanSans-Regular.ttf"], "BlackHanSans-Regular.ttf"),
            "NanumGothic":  (["NanumGothicExtraBold.ttf", "NanumGothicBold.ttf"], "NanumGothic.ttf"),
            "Jalnan":       (["Jalnan2TTF.ttf", "JalnanGothicTTF.ttf"], "Jalnan2TTF.ttf"),
        }

        def find(name):
            p = os.path.join(fdir, name) if name else None
            return os.path.abspath(p) if p and os.path.exists(p) else None

        bold = reg = None
        if family in family_map:
            for cand in family_map[family][0]:
                bold = bold or find(cand)
            reg = find(family_map[family][1])

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
            bold = bold or heaviest(ttfs)
            reg = reg or (os.path.abspath(os.path.join(fdir, sorted(ttfs)[0])) if ttfs else None)

        for p in [r"C:\Windows\Fonts\malgunbd.ttf", r"C:\Windows\Fonts\malgun.ttf",
                  "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                  "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
                  "/System/Library/Fonts/AppleSDGothicNeo.ttc"]:
            if os.path.exists(p):
                bold = bold or os.path.abspath(p)
                reg = reg or os.path.abspath(p)
        return bold, reg

    def _kenburns_card(self, idx: int, dur: float, zoom_in: bool, sharpen: bool) -> str:
        frames = max(1, round(dur * self.FPS))
        up_w, up_h = self.CARD_W * 3, self.CARD_H * 3
        z = "min(zoom+0.0012,1.28)" if zoom_in else "if(eq(on,0),1.28,max(zoom-0.0012,1.0))"
        # ✅ [요청 4] 선명도 보정(언샤프) — 저화질 이미지를 또렷하게
        sharp = ",unsharp=5:5:1.0:5:5:0.0" if sharpen else ""
        return (
            f"[{idx}:v]scale={up_w}:{up_h}:force_original_aspect_ratio=increase,"
            f"crop={up_w}:{up_h},zoompan=z='{z}':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={self.CARD_W}x{self.CARD_H}:fps={self.FPS}"
            f"{sharp},setsar=1,format=yuv420p[v{idx}];"
        )

    # ---------------- 메인 ----------------
    async def generate_shorts_video(self, task_id: str, images: list, template: str = "basic", settings: dict = None) -> dict:
        s = settings or {}
        images = images or []
        task_dir = os.path.abspath(os.path.join(self.tasks_base_dir, task_id))
        os.makedirs(task_dir, exist_ok=True)
        out_filename = "output.mp4"

        hook_text = (s.get("hook_text") or "").strip()
        body_text = (s.get("body_text") or "").strip()
        ending_text = (s.get("ending_text") or "").strip()

        # ====== 오디오/자막 타이밍 결정 ======
        # 1) 문장별 음성 매니페스트가 있으면 그걸로 100% 싱크
        manifest_path = os.path.join(task_dir, "captions.json")
        seg_audio = []      # (file, dur)
        caption_windows = []  # (text, a, b) 하단 자막
        voice_speed = 1.0
        use_manifest = False

        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    segs = json.load(f).get("segments", [])
                segs = [seg for seg in segs if os.path.exists(os.path.join(task_dir, seg["file"]))]
                if segs:
                    durs = [self._get_duration(os.path.join(task_dir, seg["file"])) for seg in segs]
                    voice_total = sum(durs)
                    if voice_total > self.MAX_DURATION:
                        voice_speed = min(voice_total / self.MAX_DURATION, 1.35)
                        print(f"⏩ 음성 {voice_total:.1f}초 → {voice_speed:.2f}배속으로 30초에 맞춤")
                    cum = 0.0
                    for seg, d in zip(segs, durs):
                        a = cum
                        cum += d / voice_speed
                        b = cum
                        seg_audio.append(seg["file"])
                        if seg["role"] in ("body", "ending"):
                            caption_windows.append((seg["text"], a, b))
                    total = min(cum, self.MAX_DURATION)
                    use_manifest = True
                    print(f"🎙️ 문장별 음성 {len(segs)}개로 자막 싱크 적용")
            except Exception as e:
                print(f"⚠️ 매니페스트 처리 실패, 추정 모드로 전환: {e}")

        # 2) 매니페스트 없음(자막 전용) → 길이 추정 + 글자수 비례 자막
        if not use_manifest:
            d_hook = max(2.5, len(hook_text) * 0.16)
            d_body = max(5.0, len(body_text) * 0.16)
            d_ending = max(2.5, len(ending_text) * 0.16)
            total = d_hook + d_body + d_ending
            if total > self.MAX_DURATION:
                f = self.MAX_DURATION / total
                d_hook, d_body, d_ending, total = d_hook * f, d_body * f, d_ending * f, self.MAX_DURATION
            st_body, st_ending = d_hook, d_hook + d_body
            bchunks = self._caption_chunks(body_text)
            echunks = self._caption_chunks(ending_text)

            def _weighted(chunks, t0, t1):
                if not chunks:
                    return []
                wsum = sum(max(1, len(c)) for c in chunks)
                out, acc = [], t0
                for i, c in enumerate(chunks):
                    seg = (t1 - t0) * max(1, len(c)) / wsum
                    a, b = acc, (t1 if i == len(chunks) - 1 else acc + seg)
                    out.append((c, a, b))
                    acc = b
                return out
            caption_windows = _weighted(bchunks, st_body, st_ending) + _weighted(echunks, st_ending, total)
            print("ℹ️ 음성 없음(자막 전용). 음성을 넣으려면 Step3에서 성우를 선택하세요.")

        # ====== 이미지 다운로드 (선택 순서 유지) ======
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

        # ====== 장면 전환(xfade) + 켄번스 ======
        sharpen = bool(s.get("upscale", True))
        n = len(local_images)
        X = self.XFADE
        if n > 1:
            D = (total + (n - 1) * X) / n
            if D < X * 1.6:
                X = max(0.2, (total / n) * 0.35)
                D = (total + (n - 1) * X) / n
        else:
            D = total

        mapped_inputs, v_filters = [], ""
        for i, img in enumerate(local_images):
            mapped_inputs.extend(["-i", img])
            v_filters += self._kenburns_card(i, D, zoom_in=(i % 2 == 0), sharpen=sharpen)

        if n == 1:
            cards_label, v_chain = "v0", ""
        else:
            v_chain, prev = "", "v0"
            for k in range(1, n):
                off = k * (D - X)
                out = f"x{k}"
                v_chain += f"[{prev}][v{k}]xfade=transition=fade:duration={X:.3f}:offset={off:.3f}[{out}];"
                prev = out
            cards_label = prev
        v_pad = f"[{cards_label}]pad={self.W}:{self.H}:{self.CARD_X}:{self.CARD_Y}:black[v_base]"
        idx_after_imgs = n

        # ====== 제목 ======
        title_lines, title_size = self._fit_title(hook_text)
        for i, ln in enumerate(title_lines):
            with open(os.path.join(task_dir, f"title_{i}.txt"), "w", encoding="utf-8") as f:
                f.write(ln)

        # ====== 자막 파일은 글자크기 확정 후 폭에 맞춰 줄바꿈하여 작성 (아래에서 처리) ======

        # ====== 색상 / 폰트 ======
        point = {"basic": "yellow", "dark": "yellow", "mint": "#34d399",
                 "sunset": "orange", "ocean": "#22d3ee"}.get(template, "yellow")
        if template == "custom" and s.get("colorLine2"):
            point = s.get("colorLine2")
        point = point.replace("#", "0x") if point.startswith("#") else point

        family = s.get("fontFamily") or "Pretendard"
        f_bold, f_reg = self._resolve_fonts(family)
        bold_arg = f"fontfile='{self.ffmpeg_escape_path(f_bold)}':" if f_bold else ""
        if not f_bold:
            print("⚠️ static/fonts/ 에 한글 폰트가 없어 시스템 폰트로 폴백합니다.")

        try:
            cap_size = int(s.get("fontSize") or 74)
        except (ValueError, TypeError):
            cap_size = 74
        cap_size = max(58, min(cap_size, 104))

        # ✅ [요청 1] 자막은 무조건 1줄. 폭을 넘으면 줄바꿈 대신 글자 크기를 자동으로 줄여 한 줄에 맞춤
        usable_cap = self.W - 90
        cap_sizes = []
        for i, (txt, _a, _b) in enumerate(caption_windows):
            one_line = " ".join((txt or "").split())  # 줄바꿈/중복 공백 제거 → 1줄
            u = self._line_units(one_line) or 1
            size_i = min(cap_size, int(usable_cap / u))
            size_i = max(40, size_i)  # 너무 작아지지 않게 하한
            cap_sizes.append(size_i)
            with open(os.path.join(task_dir, f"cap_{i}.txt"), "w", encoding="utf-8") as f:
                f.write(one_line)

        # ====== drawtext (제목 + 애니메이션 자막) ======
        draw = []
        line_h = int(title_size * 1.22)
        block_h = line_h * len(title_lines)
        title_top = max(70, (self.CARD_Y - 60 - block_h) // 2 + 20)
        # 제목: 시작 0.3초 페이드인
        title_alpha = "alpha='if(lt(t\\,0.3)\\,t/0.3\\,1)'"
        for i in range(len(title_lines)):
            color = "white" if i == 0 else point
            y = title_top + i * line_h
            draw.append(
                f"drawtext={bold_arg}textfile=title_{i}.txt:x=(w-tw)/2:y={y}:fontsize={title_size}:"
                f"fontcolor={color}:borderw=7:bordercolor=black:shadowcolor=black@0.5:shadowx=0:shadowy=4:{title_alpha}"
            )

        # ✅ [요청 2] 자막 강조 애니메이션: 등장 시 페이드인 + 살짝 위로 슬라이드
        cap_y = self.CARD_Y + self.CARD_H + 45
        for i, (_txt, a, b) in enumerate(caption_windows):
            size_i = cap_sizes[i]
            dur = "0.18"
            alpha = f"alpha='if(lt(t-{a:.2f}\\,{dur})\\,(t-{a:.2f})/{dur}\\,1)'"
            yexpr = f"y='{cap_y}+28*(1-min(max((t-{a:.2f})/{dur}\\,0)\\,1))'"
            draw.append(
                f"drawtext={bold_arg}textfile=cap_{i}.txt:x=(w-tw)/2:{yexpr}:fontsize={size_i}:"
                f"fontcolor=white:borderw=5:bordercolor=black:shadowcolor=black@0.55:shadowx=0:shadowy=3:"
                f"{alpha}:enable='between(t,{a:.2f},{b:.2f})'"
            )

        graphic = f"{v_filters}{v_chain}{v_pad};[v_base]" + ",".join(draw) + "[v_final]"

        # ====== 오디오 ======
        use_bgm = s.get("autoBgm", True)
        bgm_id = s.get("bgmTrack") or "track_01"
        bgm_path = os.path.abspath(os.path.join(self.static_dir, "bgm", f"{bgm_id}.mp3"))
        audio_inputs = []
        aidx = idx_after_imgs
        bgm_ok = use_bgm and os.path.exists(bgm_path)

        if use_manifest and seg_audio:
            for fn in seg_audio:
                audio_inputs.extend(["-i", fn])
            labels = "".join(f"[{aidx+i}:a]" for i in range(len(seg_audio)))
            voice_stmt = f"{labels}concat=n={len(seg_audio)}:v=0:a=1,atempo={voice_speed:.4f}[a_voice];"
            bgm_in = aidx + len(seg_audio)
            if bgm_ok:
                audio_inputs.extend(["-stream_loop", "-1", "-i", bgm_path])
                amix = (f"{voice_stmt}[{bgm_in}:a]volume=0.20,asetpts=PTS-STARTPTS[a_bgm];"
                        f"[a_voice][a_bgm]amix=inputs=2:duration=first:normalize=0:dropout_transition=0[a_final];")
                print(f"🎵 음성 + BGM 합성: {bgm_path}")
            else:
                amix = f"{voice_stmt}[a_voice]anull[a_final];"
        else:
            if bgm_ok:
                audio_inputs.extend(["-stream_loop", "-1", "-i", bgm_path])
                amix = f"[{aidx}:a]volume=0.8,asetpts=PTS-STARTPTS[a_final];"
                print(f"🎵 BGM 적용(메인): {bgm_path}")
            else:
                audio_inputs.extend(["-f", "lavfi", "-i", f"anullsrc=cl=stereo:r=44100:d={total}"])
                amix = f"[{aidx}:a]anull[a_final];"
                if use_bgm:
                    print(f"⚠️ BGM 파일 없음: {bgm_path} → backend/static/bgm/ 에 {bgm_id}.mp3 를 넣으세요.")

        # 최종 음량 정규화 (참고 영상 수준의 큰 소리로)
        amix = amix + "[a_final]loudnorm=I=-15:TP=-1.5:LRA=11[a_out];"

        cmd = [
            "ffmpeg", "-y",
            *mapped_inputs, *audio_inputs,
            "-filter_complex", f"{amix}{graphic}",
            "-map", "[v_final]", "-map", "[a_out]",
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
