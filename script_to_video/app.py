import os
import tempfile

import streamlit as st

from core import analyzer, pexels, render, tts

st.set_page_config(page_title="Script to Video", page_icon="🎬", layout="wide")
ss = st.session_state
for k, v in {"scenes": [], "final": None, "variant": 0, "stats": {}}.items():
    ss.setdefault(k, v)

# ================= Styling =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700&family=DM+Sans:wght@400;500;600&display=swap');
html, body, .stApp, [data-testid="stSidebar"] { font-family: 'DM Sans', 'Segoe UI', sans-serif; }
.hero-title, h2, h3 { font-family: 'Outfit', 'Segoe UI', sans-serif !important; letter-spacing: -0.01em; }
.block-container { padding-top: 1.6rem; max-width: 1280px; }
.hero { background: #12263A; color: #F4F7FA; border-radius: 18px; padding: 28px 32px 24px; margin-bottom: 22px; }
.hero-title { font-size: 2.2rem; font-weight: 700; line-height: 1.15; margin: 0 0 8px 0; }
.hero-sub { font-size: 1.05rem; color: #B9C7D6; margin: 0 0 18px 0; max-width: 62ch; }
.steps { display: flex; flex-wrap: wrap; gap: 10px; list-style: none; padding: 0; margin: 0; }
.steps li { display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.09); border-radius: 999px; padding: 6px 14px 6px 6px; font-size: 0.92rem; }
.steps li b { display: inline-flex; width: 24px; height: 24px; align-items: center; justify-content: center; border-radius: 50%; background: #2BB3D1; color: #12263A; font-size: 0.8rem; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; }
[data-testid="stBaseButton-primary"], button[kind="primary"] { font-weight: 600; font-size: 1.05rem; padding: 0.7rem 1rem; border-radius: 12px; }
[data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #D5E0EA; border-radius: 12px; padding: 12px 16px; }
.hint { color: #4A6176; font-size: 0.9rem; margin-top: -4px; }
:focus-visible { outline: 3px solid #2BB3D1 !important; outline-offset: 2px; }
@media (max-width: 640px) { .hero { padding: 20px; } .hero-title { font-size: 1.6rem; } }
</style>
""", unsafe_allow_html=True)

# ================= Sidebar =================
with st.sidebar:
    st.markdown("### Setup")
    groq_key = st.text_input("Groq API key", type="password", value=os.getenv("GROQ_API_KEY", ""),
                             help="Free key from console.groq.com").strip()
    pexels_key = st.text_input("Pexels API key", type="password", value=os.getenv("PEXELS_API_KEY", ""),
                               help="Free key from pexels.com/api").strip()
    st.caption(("✅ Groq key added" if groq_key else "⚠️ Groq key missing") + "  \n" +
               ("✅ Pexels key added" if pexels_key else "⚠️ Pexels key missing"))
    with st.expander("AI model"):
        model = st.selectbox("Model", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant",
                                       "openai/gpt-oss-120b", "openai/gpt-oss-20b"])
        temperature = st.slider("Creativity (temperature)", 0.0, 1.5, 0.6, 0.05)
    with st.expander("Output format"):
        aspect = st.selectbox("Aspect ratio", list(render.SIZES),
                              help="16:9 for YouTube, 9:16 for Shorts and Reels, 1:1 for posts")
    with st.expander("Music and fonts"):
        music_file = st.file_uploader("Background music", type=["mp3", "wav", "m4a"])
        music_vol = st.slider("Music volume", 0.0, 0.5, 0.12, 0.01)
        font_file = st.file_uploader("Caption font (.ttf) for Urdu, Hindi, Arabic", type=["ttf", "otf"])

W, H = render.SIZES[aspect]

# ================= Header =================
st.markdown(
    '<div class="hero"><div class="hero-title">Turn a script into a finished video</div>'
    '<p class="hero-sub">Paste your words. The app plans the scenes, finds matching footage, '
    'records the voice and edits everything together.</p>'
    '<ol class="steps"><li><b>1</b>Script</li><li><b>2</b>Scenes</li><li><b>3</b>Footage</li>'
    '<li><b>4</b>Voice</li><li><b>5</b>Video</li></ol></div>', unsafe_allow_html=True)

left, right = st.columns([1.15, 1], gap="large")

# ---------- right column: settings (defined first so the left column can use them) ----------
with right:
    with st.container(border=True):
        st.markdown("### Look and sound")
        tab_voice, tab_vis, tab_style = st.tabs(["🎙️ Voice", "🖼️ Footage", "✨ Style"])
        with tab_voice:
            voice_on = st.toggle("Include voiceover", True,
                                 help="Turn off for a silent video with captions")
            language = st.selectbox("Language", list(tts.VOICES))
            v1, v2 = st.columns(2)
            gender = v1.radio("Voice", ["Male", "Female"], horizontal=True, disabled=not voice_on)
            voice_style = v2.selectbox("Style", list(tts.STYLES), disabled=not voice_on)
            speed_choice = st.radio("Speaking speed", list(tts.SPEEDS), index=2, horizontal=True,
                                    disabled=not voice_on)
            speed = tts.SPEEDS[speed_choice]
            if not voice_on:
                st.info("Silent mode: captions stay on so viewers can read the story.")
        with tab_vis:
            visual_mode = st.radio("Footage type", ["Mixed", "Photo", "Video"], horizontal=True,
                                   help="Mixed uses video clips and falls back to photos")
            cut_every = st.slider("Change footage every (seconds)", 4, 15, 8)
            kenburns = st.checkbox("Slow zoom on photos", True)
        with tab_style:
            trans_name = st.selectbox("Transition", list(render.TRANSITIONS), index=1)
            grade = st.selectbox("Color look", list(render.GRADES))
            captions_on = st.checkbox("Show captions", True, disabled=not voice_on)
            if not voice_on:
                captions_on = True

# ---------- left column: script ----------
with left:
    with st.container(border=True):
        st.markdown("### Your script")
        script = st.text_area("Script", height=250, label_visibility="collapsed",
                              placeholder="Paste only the spoken words. Leave out timestamps, "
                                          "[S1] tags and (On screen: ...) notes.")
        words = len(script.split())
        if words and voice_on:
            st.markdown(f'<div class="hint">{words} words, about {words / (150 * speed):.1f} min '
                        f'of voiceover at {speed_choice}</div>', unsafe_allow_html=True)
        elif words:
            st.markdown(f'<div class="hint">{words} words, about {words / 2.8 / 60:.1f} min '
                        f'of reading time</div>', unsafe_allow_html=True)
        length_choice = st.radio("Video length", ["Auto", "2 min", "3 min", "4 min", "5 min",
                                                  "6 min", "8 min", "10 min"], horizontal=True,
                                 help="Auto matches the voice. A longer choice adds footage time after each scene.")
        target_min = 0 if length_choice == "Auto" else int(length_choice.split()[0])


def generate(reanalyze: bool) -> bool:
    if not groq_key or not pexels_key:
        st.error("Add both API keys in the sidebar to continue.")
        return False
    if reanalyze and not script.strip():
        st.error("Paste a script first.")
        return False
    work = tempfile.mkdtemp(prefix="s2v_")
    font_path = None
    if font_file:
        font_path = os.path.join(work, "font.ttf")
        with open(font_path, "wb") as f:
            f.write(font_file.getvalue())
    trans = render.TRANSITIONS[trans_name]
    tdur = 0.5
    try:
        with st.status("Making your video...", expanded=True) as status:
            if reanalyze:
                st.write("🧠 Reading the script and planning scenes...")
                ss.scenes = analyzer.analyze(groq_key, model, temperature, script, language)
                ss.variant = 0
                st.write(f"✅ {len(ss.scenes)} scenes planned")
            n = len(ss.scenes)

            audios, adur = [], []
            for i, sc in enumerate(ss.scenes):
                if voice_on:
                    st.write(f"🎙️ Recording voice {i+1} of {n} at {speed_choice}")
                    a = tts.synthesize(sc["narration"], os.path.join(work, f"a{i}.mp3"),
                                       language, gender, voice_style, speed)
                    audios.append(a)
                    adur.append(render.probe_duration(a))
                else:
                    adur.append(max(len(sc["narration"].split()) / 2.8, 2.5))
            speech = sum(adur)
            label = "Narration" if voice_on else "Reading time"
            extra = 0.5
            if target_min > 0:
                target = target_min * 60
                if target > speech + 0.5 * n:
                    extra = (target - speech) / n
                else:
                    st.warning(f"{label} alone is already {speech/60:.1f} min, longer than "
                               f"{target_min} min. Using the natural length.")
            durs = [max(a + extra, 2.0) for a in adur]
            st.write(f"⏱️ {label} {speech:.0f}s, video {sum(durs):.0f}s")

            used, clips, seg_durs = set(), [], []
            for i, sc in enumerate(ss.scenes):
                k_seg = max(1, round(durs[i] / cut_every))
                seg_d = durs[i] / k_seg
                queries = [sc["keywords"]] + sc.get("alts", [])
                st.write(f"🎬 Finding footage for scene {i+1} of {n} ({k_seg} shot{'s' if k_seg > 1 else ''})")
                cap = None
                if captions_on:
                    cap = render.caption_png(sc["narration"], W, H,
                                             os.path.join(work, f"c{i}.png"),
                                             font_path, 40 if W > H else 34, "#ffffff",
                                             "Bottom", rtl=language in tts.RTL)
                shown = []
                for j in range(k_seg):
                    q = dict(sc)
                    q["keywords"] = queries[j % len(queries)]
                    item, kind = pexels.auto_pick(pexels_key, q, visual_mode, aspect, W,
                                                  used, ss.variant)
                    shown.append(f"{kind}: {q['keywords']}")
                    media = pexels.download(item, kind)
                    last = (i == n - 1 and j == k_seg - 1)
                    pad = tdur if (trans and not last) else 0
                    clips.append(render.scene_clip(media, kind, seg_d + pad, W, H, len(clips),
                                                   kenburns, grade, cap,
                                                   os.path.join(work, f"v{i}_{j}.mp4")))
                    seg_durs.append(seg_d)
                sc["visual"] = " | ".join(shown)

            st.write("🎞️ Editing everything together...")
            t = min(tdur, min(seg_durs) * 0.5)
            vid = render.join_clips(clips, seg_durs, trans, t, os.path.join(work, "video.mp4"))
            voice = (render.voice_track(audios, durs, work, os.path.join(work, "voice.wav"))
                     if voice_on else None)
            music = None
            if music_file:
                music = os.path.join(work, "music" + os.path.splitext(music_file.name)[1])
                with open(music, "wb") as f:
                    f.write(music_file.getvalue())
            final = render.mux(vid, voice, os.path.join(work, "final.mp4"), music, music_vol)
            ss.stats = {"scenes": n, "seconds": render.probe_duration(final),
                        "mode": "With voice" if voice_on else "Silent + captions", "size": aspect}
            status.update(label="Your video is ready", state="complete")
        with open(final, "rb") as f:
            ss.final = f.read()
        return True
    except Exception as e:
        st.error(f"Something went wrong: {e}")
        return False


# ================= Generate =================
ready = bool(groq_key and pexels_key and script.strip())
if not ready:
    need = [x for x, ok in [("Groq key", groq_key), ("Pexels key", pexels_key),
                            ("a script", script.strip())] if not ok]
    st.caption("To start, add: " + ", ".join(need) + ".")
if st.button("🚀 Create video", type="primary", use_container_width=True):
    generate(reanalyze=True)

# ================= Result =================
if ss.final:
    st.markdown("### Your video")
    s = ss.stats
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Scenes", s.get("scenes", "-"))
    secs = int(s.get("seconds", 0))
    m2.metric("Length", f"{secs // 60}:{secs % 60:02d}")
    m3.metric("Audio", s.get("mode", "-"))
    m4.metric("Format", s.get("size", "-"))

    tab_v, tab_s = st.tabs(["▶️ Preview", "🗂️ Scenes"])
    with tab_v:
        st.video(ss.final)
        b1, b2, b3 = st.columns(3)
        b1.download_button("⬇️ Download MP4", ss.final, "final.mp4", "video/mp4",
                           use_container_width=True)
        if b2.button("🔄 Try different footage", use_container_width=True,
                     help="Keeps the same scenes and voice settings, picks new clips"):
            ss.variant += 1
            if generate(reanalyze=False):
                st.rerun()
        b3.link_button("▶️ Upload to YouTube", "https://www.youtube.com/upload",
                       use_container_width=True)
    with tab_s:
        for i, sc in enumerate(ss.scenes, 1):
            with st.container(border=True):
                st.markdown(f"**Scene {i}**")
                st.write(sc["narration"])
                st.caption(sc.get("visual", ""))