"""AI Script Analyzer + Scene Generator (Groq): script -> scene list with visual keywords.
The model decides how many scenes the script needs."""
import json
import re
from groq import Groq

HARD_CAP = 40  # safety limit only; the model decides the real number

SYSTEM = """You are a video editor. Split the script into scenes for a stock-footage video.
YOU decide how many scenes are needed from the script's length and content:
- one scene per distinct idea, moment or location change
- each scene should last about 5-10 seconds when spoken (roughly 12-30 words)
- a short script gets few scenes, a long script gets many; never skip or invent content
Return ONLY JSON:
{"title": str, "scenes": [{"narration": str, "keywords": str, "alts": [str, str, str], "broad": str}]}
Rules:
- narration: spoken text of the scene, written in {language}. Keep the original meaning and order; translate if needed. Together the scenes must cover the whole script.
- keywords: 2-5 ENGLISH words for a Pexels search showing LITERALLY what the narration talks about. Name concrete, filmable objects, people or places (e.g. "pill bottles pharmacy shelf", "doctor writing prescription", "hospital corridor"). Never use abstract words like "definition", "regulation", "concept", "law text".
- alts: 3 other ENGLISH searches for the same scene, each showing a DIFFERENT visual (different object, angle or setting), also concrete and literal.
- broad: ONE general concrete English word for the scene (fallback search, e.g. "pharmacy", "hospital", "doctor")."""


def _fallback(script):
    sents = [s for s in re.split(r"(?<=[.!?۔])\s+", script.strip()) if s]
    out = []
    for i in range(0, len(sents), 2):
        chunk = " ".join(sents[i:i + 2])
        out.append({"narration": chunk,
                    "keywords": " ".join(chunk.split()[:3]) or "nature",
                    "alts": [], "broad": "nature"})
    return out[:HARD_CAP]


def _parse(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0))


def analyze(api_key, model, temperature, script, language):
    client = Groq(api_key=api_key)
    system = SYSTEM.replace("{language}", language)
    try:
        resp = client.chat.completions.create(
            model=model, temperature=temperature,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": script}])
        raw = _parse(resp.choices[0].message.content)["scenes"]
        scenes = []
        for s in raw:
            narration = str(s.get("narration", "")).strip()
            if not narration:
                continue
            keywords = str(s.get("keywords", "")).strip() or " ".join(narration.split()[:3])
            alts = [str(a).strip() for a in (s.get("alts") or []) if str(a).strip()][:3]
            scenes.append({"narration": narration, "keywords": keywords,
                           "alts": alts, "broad": str(s.get("broad", "")).strip()})
        scenes = scenes[:HARD_CAP]
        assert scenes
        return scenes
    except Exception:
        return _fallback(script)