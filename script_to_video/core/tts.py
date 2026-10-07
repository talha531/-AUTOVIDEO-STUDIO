"""Voice Manager: language -> gender -> voice -> style -> speed -> TTS (edge-tts, free)."""
import asyncio
import edge_tts

VOICES = {
    "English (US)": {"Male": "en-US-GuyNeural", "Female": "en-US-AriaNeural"},
    "English (UK)": {"Male": "en-GB-RyanNeural", "Female": "en-GB-SoniaNeural"},
    "Urdu": {"Male": "ur-PK-AsadNeural", "Female": "ur-PK-UzmaNeural"},
    "Hindi": {"Male": "hi-IN-MadhurNeural", "Female": "hi-IN-SwaraNeural"},
    "Arabic": {"Male": "ar-SA-HamedNeural", "Female": "ar-SA-ZariyahNeural"},
    "Spanish": {"Male": "es-ES-AlvaroNeural", "Female": "es-ES-ElviraNeural"},
    "French": {"Male": "fr-FR-HenriNeural", "Female": "fr-FR-DeniseNeural"},
    "German": {"Male": "de-DE-ConradNeural", "Female": "de-DE-KatjaNeural"},
}
# style -> (rate offset in %, pitch)
STYLES = {"Natural": (0, "+0Hz"), "Calm": (-10, "-2Hz"),
          "Energetic": (12, "+2Hz"), "Deep narrator": (-5, "-4Hz")}
# speed button label -> speed multiplier
SPEEDS = {"0.75x": 0.75, "0.9x": 0.9, "1x": 1.0, "1.1x": 1.1, "1.25x": 1.25, "1.5x": 1.5}
RTL = {"Urdu", "Arabic"}


async def _run(text, voice, rate, pitch, path):
    await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(path)


def synthesize(text, path, language, gender, style, speed=1.0):
    """speed: 1.0 = normal, 0.75 = slower, 1.5 = faster."""
    offset, pitch = STYLES[style]
    pct = round((1 + offset / 100) * speed * 100 - 100)
    pct = max(-90, min(100, pct))
    voice = VOICES[language][gender]
    for attempt in range(2):
        try:
            asyncio.run(_run(text, voice, f"{pct:+d}%", pitch, path))
            return path
        except Exception:
            if attempt == 1:
                raise
    return path