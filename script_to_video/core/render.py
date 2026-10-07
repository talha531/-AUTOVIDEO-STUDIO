"""Scene Builder + Text & Captions + Transitions + FFmpeg Renderer."""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:  # optional
    arabic_reshaper = get_display = None

FPS = 25
SIZES = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (1024, 1024)}
GRADES = {"None": "", "Warm": "colorbalance=rs=.12:bs=-.12", "Cool": "colorbalance=rs=-.10:bs=.12",
          "Black & White": "hue=s=0", "Vivid": "eq=saturation=1.4:contrast=1.08",
          "Cinematic": "eq=contrast=1.12:saturation=0.9:brightness=-0.03"}
TRANSITIONS = {"None (cut)": None, "Fade": "fade", "Fade through black": "fadeblack",
               "Dissolve": "dissolve", "Slide left": "slideleft", "Wipe left": "wipeleft",
               "Circle open": "circleopen"}


def _run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-1500:])


def probe_duration(path):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    return float(o.stdout.strip())


# ---------- captions ----------
def _font(path, size):
    for c in ([path] if path else []) + [
            "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "DejaVuSans-Bold.ttf", "arial.ttf"]:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def caption_png(text, w, h, path, font_path=None, size=40, color="#ffffff",
                position="Bottom", rtl=False):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = _font(font_path, size)
    lines, cur = [], ""
    for wd in text.split():
        t = f"{cur} {wd}".strip()
        if cur and d.textlength(t, font=font) > w * 0.86:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    if cur:
        lines.append(cur)
    if rtl and arabic_reshaper:
        lines = [get_display(arabic_reshaper.reshape(l)) for l in lines]
    lh = int(size * 1.35)
    bh = lh * len(lines) + 30
    y0 = {"Bottom": int(h * 0.90) - bh, "Center": (h - bh) // 2, "Top": int(h * 0.08)}[position]
    y0 = max(y0, 0)
    d.rounded_rectangle((int(w * 0.05), y0, int(w * 0.95), y0 + bh), radius=18, fill=(0, 0, 0, 150))
    for k, l in enumerate(lines):
        d.text(((w - d.textlength(l, font=font)) / 2, y0 + 15 + k * lh), l, font=font, fill=color)
    img.save(path)
    return path


# ---------- scene clip ----------
def scene_clip(media, kind, dur, w, h, idx, kenburns, grade, caption, out):
    g = f",{GRADES[grade]}" if GRADES[grade] else ""
    pre = []
    if kind == "Photo" and kenburns:
        frames = max(int(dur * FPS), 1)
        step = 0.25 / frames
        z = (f"min(zoom+{step:.6f},1.25)" if idx % 2 == 0
             else f"if(eq(on,0),1.25,max(zoom-{step:.6f},1.0))")
        base = (f"[0:v]scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},"
                f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={w}x{h}:fps={FPS},setsar=1{g}[bg]")
    else:
        pre = ["-loop", "1", "-framerate", str(FPS)] if kind == "Photo" else ["-stream_loop", "-1"]
        base = (f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
                f"fps={FPS},setsar=1{g}[bg]")
    cmd = ["ffmpeg", "-y"] + pre + ["-i", media]
    if caption:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-i", caption]
        fg = base + ";[bg][1:v]overlay=0:0,format=yuv420p[v]"
    else:
        fg = base + ";[bg]format=yuv420p[v]"
    cmd += ["-filter_complex", fg, "-map", "[v]", "-t", f"{dur:.2f}", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-an", out]
    _run(cmd)
    return out


# ---------- assembly ----------
def voice_track(audios, durs, work, out):
    padded = []
    for i, (a, d) in enumerate(zip(audios, durs)):
        p = os.path.join(work, f"pad{i}.wav")
        _run(["ffmpeg", "-y", "-i", a, "-af", "apad", "-t", f"{d:.2f}", "-ar", "44100", "-ac", "2", p])
        padded.append(p)
    lst = os.path.join(work, "audio.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in padded)
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:a", "pcm_s16le", out])
    return out


def join_clips(clips, durs, trans, tdur, out):
    if len(clips) == 1 or not trans:
        lst = out + ".txt"
        with open(lst, "w") as f:
            f.writelines(f"file '{os.path.abspath(c)}'\n" for c in clips)
        _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264",
              "-preset", "veryfast", "-pix_fmt", "yuv420p", out])
        return out
    cmd = ["ffmpeg", "-y"]
    for c in clips:
        cmd += ["-i", c]
    fc, prev, acc = [], "[0:v]", 0.0
    for i in range(1, len(clips)):
        acc += durs[i - 1]
        lab = f"[x{i}]"
        fc.append(f"{prev}[{i}:v]xfade=transition={trans}:duration={tdur}:offset={acc:.3f}{lab}")
        prev = lab
    cmd += ["-filter_complex", ";".join(fc), "-map", prev, "-c:v", "libx264",
            "-preset", "veryfast", "-pix_fmt", "yuv420p", out]
    _run(cmd)
    return out


def mux(video, voice, out, music=None, music_vol=0.12):
    """voice may be None (silent video): music only, or no audio at all."""
    cmd = ["ffmpeg", "-y", "-i", video]
    if voice and music:
        cmd += ["-i", voice, "-stream_loop", "-1", "-i", music, "-filter_complex",
                f"[2:a]volume={music_vol}[m];[1:a][m]amix=inputs=2:duration=first[a]",
                "-map", "0:v", "-map", "[a]", "-c:a", "aac"]
    elif voice:
        cmd += ["-i", voice, "-map", "0:v", "-map", "1:a", "-c:a", "aac"]
    elif music:
        cmd += ["-stream_loop", "-1", "-i", music, "-filter_complex",
                f"[1:a]volume={max(music_vol, 0.4)}[a]",
                "-map", "0:v", "-map", "[a]", "-c:a", "aac"]
    else:
        cmd += ["-an"]
    cmd += ["-c:v", "copy", "-shortest", "-movflags", "+faststart", out]
    _run(cmd)
    return out