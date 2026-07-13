#!/usr/bin/env python3
"""Host-side watcher for local asynchronous Codex image jobs.

Keep this process on the host, not in the Claude Science sandbox. It reads a
local CSSwitch profile solely to obtain the proxy credential at request time;
the credential is never written to a job file or returned through MCP.
"""

import base64
import json
import os
import signal
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(os.environ.get("CODEX_IMAGE_JOB_ROOT", "/tmp/csswitch-codex-image-jobs"))
SUBMIT, WORKING, JOBS = ROOT / "submit", ROOT / "working", ROOT / "jobs"
CONFIG = Path(os.environ.get("CSSWITCH_CONFIG_PATH", Path.home() / ".csswitch" / "config.json"))
API_URL = os.environ.get("CODEX_IMAGE_PROXY_URL", "http://127.0.0.1:8317/v1/images/generations")
OUTPUT = Path(os.environ.get("CODEX_IMAGE_OUTPUT_DIR", ROOT / "output"))
PROFILE_NAME = os.environ.get("CODEX_IMAGE_PROFILE_NAME", "")
ALLOWED_MODELS = {"gpt-image-1.5", "gpt-image-2"}
MAX_AGE_SECONDS = 1800


def validate_local_api_url():
    parsed = urllib.parse.urlparse(API_URL)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("CODEX_IMAGE_PROXY_URL must be an HTTP loopback URL")


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)


def prepare():
    os.umask(0o077)
    for directory in (ROOT, SUBMIT, WORKING, JOBS):
        directory.mkdir(parents=True, exist_ok=True)
        directory.chmod(0o700)


def proxy_key():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    for profile in config.get("profiles", []):
        name_matches = not PROFILE_NAME or profile.get("name") == PROFILE_NAME
        if name_matches and profile.get("base_url", "").startswith("http://127.0.0.1:") and profile.get("api_key"):
            return str(profile["api_key"])
    raise RuntimeError("No local CSSwitch loopback proxy profile with an API key was found")


def generate(job):
    body = json.dumps({"model": job["model"], "prompt": job["prompt"], "size": "1024x1024", "output_format": "png"}).encode()
    request = urllib.request.Request(API_URL, data=body, method="POST", headers={"Authorization": f"Bearer {proxy_key()}", "Content-Type": "application/json"})
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=300) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"Image endpoint returned HTTP {exc.code}: {detail}") from exc
    image = (payload.get("data") or [{}])[0].get("b64_json", "")
    if not image:
        raise RuntimeError("Image endpoint did not return image data")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT / f"codex-image-{time.strftime('%Y%m%d-%H%M%S')}.png"
    destination.write_bytes(base64.b64decode(image))
    return image, str(destination)


def run_job(path):
    try:
        job = json.loads(path.read_text(encoding="utf-8"))
        job_id = job.get("id")
        if not isinstance(job_id, str) or path.name != f"{job_id}.json":
            raise ValueError("Invalid image job request")
        prompt, model = job.get("prompt"), job.get("model")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 12000 or model not in ALLOWED_MODELS:
            raise ValueError("Invalid image job")
        atomic_json(JOBS / path.name, {"id": job_id, "state": "running"})
        image, destination = generate(job)
        atomic_json(JOBS / path.name, {"id": job_id, "state": "succeeded", "b64_json": image, "path": destination})
    except Exception as exc:
        job_id = locals().get("job", {}).get("id")
        if isinstance(job_id, str):
            atomic_json(JOBS / f"{job_id}.json", {"id": job_id, "state": "failed", "error": str(exc)[:500]})
    finally:
        path.unlink(missing_ok=True)


def claim(path):
    target = WORKING / path.name
    try:
        os.replace(path, target)
    except FileNotFoundError:
        return
    if os.fork() == 0:
        run_job(target)
        os._exit(0)


def sweep():
    cutoff = time.time() - MAX_AGE_SECONDS
    for directory in (SUBMIT, WORKING, JOBS):
        for path in directory.glob("*.json"):
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
            except FileNotFoundError:
                pass
    for path in OUTPUT.glob("codex-image-*.png"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
        except FileNotFoundError:
            pass


def main():
    validate_local_api_url()
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    prepare()
    last_sweep = 0
    while True:
        for path in SUBMIT.glob("*.json"):
            claim(path)
        if time.time() - last_sweep > 60:
            sweep()
            last_sweep = time.time()
        time.sleep(0.15)


if __name__ == "__main__":
    main()
