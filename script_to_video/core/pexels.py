"""Pexels client: photo search, video search, auto pick, media cache (with retry)."""
import os
import time
import requests

BASE = "https://api.pexels.com"
ORIENT = {"16:9": "landscape", "9:16": "portrait", "1:1": "square"}


def _get(key, path, params, tries=3):
    last = None
    for attempt in range(tries):
        try:
            r = requests.get(BASE + path, headers={"Authorization": key},
                             params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            last = e
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status in (401, 403):  # wrong API key: retrying will not help
                raise
            time.sleep(1.5 * (attempt + 1))
    raise last


def search_photos(key, query, aspect, n=8):
    j = _get(key, "/v1/search", {"query": query, "per_page": n, "orientation": ORIENT[aspect]})
    return [{"id": p["id"], "thumb": p["src"]["medium"], "url": p["src"]["large2x"],
             "by": p["photographer"]} for p in j.get("photos", [])]


def search_videos(key, query, aspect, width, n=8):
    j = _get(key, "/videos/search", {"query": query, "per_page": n, "orientation": ORIENT[aspect]})
    items = []
    for v in j.get("videos", []):
        files = [f for f in v["video_files"] if f.get("file_type") == "video/mp4" and f.get("width")]
        if not files:
            continue
        best = min(files, key=lambda f: abs(f["width"] - width))
        items.append({"id": v["id"], "thumb": v["image"], "url": best["link"],
                      "duration": v.get("duration", 0), "by": v["user"]["name"]})
    return items


def search(key, query, kind, aspect, width):
    fn = search_photos if kind == "Photo" else (lambda k, q, a: search_videos(k, q, a, width))
    items = fn(key, query, aspect)
    if not items and " " in query:  # broaden to the first word
        items = fn(key, query.split()[0], aspect)
    return items


def auto_pick(key, scene, mode, aspect, width, used, variant=0):
    """Automatically choose the best visual for a scene.
    mode: Photo | Video | Mixed (video first, photo fallback).
    `used` is a set of (kind, id) so the same media is not reused across scenes."""
    kinds = {"Photo": ["Photo"], "Video": ["Video", "Photo"], "Mixed": ["Video", "Photo"]}[mode]
    first_word = scene["keywords"].split()[0] if scene["keywords"].split() else ""
    queries = [q for q in [scene["keywords"], scene.get("broad", ""), first_word, "nature"] if q]
    for kind in kinds:
        for q in queries:
            try:
                items = search(key, q, kind, aspect, width)
            except requests.RequestException:
                continue
            fresh = [it for it in items if (kind, it["id"]) not in used]
            if fresh:
                it = fresh[variant % len(fresh)]
                used.add((kind, it["id"]))
                return it, kind
    raise RuntimeError(f"No Pexels result for scene: {scene['keywords']}")


def download(item, kind, cache="media_cache", tries=5):
    """Download with retries; a broken connection never leaves a corrupt file in the cache."""
    os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, f"{kind.lower()}_{item['id']}" + (".jpg" if kind == "Photo" else ".mp4"))
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    tmp = path + ".part"
    last = None
    for attempt in range(tries):
        try:
            with requests.get(item["url"], stream=True, timeout=(15, 60)) as r:
                r.raise_for_status()
                expected = int(r.headers.get("Content-Length", 0))
                size = 0
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 16):
                        f.write(chunk)
                        size += len(chunk)
            if expected and size != expected:
                raise IOError(f"Incomplete download: {size} of {expected} bytes")
            os.replace(tmp, path)
            return path
        except Exception as e:  # IncompleteRead, timeouts, connection resets
            last = e
            if os.path.exists(tmp):
                os.remove(tmp)
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Could not download media after {tries} tries: {last}")