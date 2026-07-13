#!/usr/bin/env python3
"""Local stdio MCP server for asynchronous image jobs.

Runs inside the Claude Science sandbox. It never reads the host CSSwitch
configuration or OAuth credentials; it only writes restricted job files.
"""

import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(os.environ.get("CODEX_IMAGE_JOB_ROOT", "/tmp/csswitch-codex-image-jobs"))
SUBMIT = ROOT / "submit"
JOBS = ROOT / "jobs"
ALLOWED_MODELS = {"gpt-image-1.5", "gpt-image-2"}


def send(value):
    sys.stdout.write(json.dumps(value, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)


def submit(prompt, model):
    if not prompt or len(prompt) > 12000:
        raise ValueError("A non-empty prompt of at most 12,000 characters is required")
    if model not in ALLOWED_MODELS:
        raise ValueError("Unsupported image model")
    if not SUBMIT.is_dir() or not JOBS.is_dir():
        raise RuntimeError("Codex image job bridge is not running")
    job_id = str(uuid.uuid4())
    atomic_json(SUBMIT / f"{job_id}.json", {"id": job_id, "prompt": prompt, "model": model})
    return job_id


def tools():
    image_input = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Detailed image-generation prompt."},
            "model": {"type": "string", "enum": sorted(ALLOWED_MODELS)},
        },
        "required": ["prompt"],
        "additionalProperties": False,
    }
    return [
        {"name": "generate_image", "description": "Submit an image job and return its job_id.", "inputSchema": image_input},
        {"name": "get_image_result", "description": "Poll a submitted image job by job_id.", "inputSchema": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"], "additionalProperties": False}},
        {"name": "image_bridge_status", "description": "Check whether the local image job bridge is ready.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    ]


def call_tool(name, args):
    if name == "image_bridge_status":
        if SUBMIT.is_dir() and JOBS.is_dir():
            return [{"type": "text", "text": "Codex image job bridge is ready"}]
        raise RuntimeError("Codex image job bridge is unavailable")
    if name == "generate_image":
        model = str(args.get("model", "gpt-image-1.5")).strip() or "gpt-image-1.5"
        job_id = submit(str(args.get("prompt", "")).strip(), model)
        return [{"type": "text", "text": f"Image job submitted: {job_id}. Call get_image_result with this job_id."}]
    if name == "get_image_result":
        job_id = str(args.get("job_id", "")).strip()
        try:
            uuid.UUID(job_id)
        except ValueError as exc:
            raise ValueError("Invalid job_id") from exc
        path = JOBS / f"{job_id}.json"
        if not path.exists():
            return [{"type": "text", "text": "Job is queued; call get_image_result again shortly."}]
        result = json.loads(path.read_text(encoding="utf-8"))
        if result.get("state") in {"queued", "running"}:
            return [{"type": "text", "text": "Job is still generating; call get_image_result again shortly."}]
        if result.get("state") == "failed":
            raise RuntimeError(str(result.get("error") or "Image generation failed"))
        image = result.get("b64_json", "")
        if result.get("state") != "succeeded" or not image:
            raise RuntimeError("Image job has an invalid result")
        return [
            {"type": "image", "data": image, "mimeType": "image/png"},
            {"type": "text", "text": f"Generated image saved to {result.get('path', '<configured output directory>')}."},
        ]
    raise ValueError(f"Unknown tool: {name}")


def dispatch(request):
    method, request_id = request.get("method"), request.get("id")
    if method == "initialize":
        protocol = request.get("params", {}).get("protocolVersion", "2025-03-26")
        return {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": protocol, "capabilities": {"tools": {}}, "serverInfo": {"name": "codex-image", "version": "example-1.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools()}}
    if method == "tools/call":
        try:
            params = request.get("params", {})
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": call_tool(params.get("name", ""), params.get("arguments", {}))}}
        except Exception as exc:
            return {"jsonrpc": "2.0", "id": request_id, "result": {"content": [{"type": "text", "text": str(exc)}], "isError": True}}
    if request_id is not None:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


for line in sys.stdin:
    try:
        reply = dispatch(json.loads(line))
        if reply is not None:
            send(reply)
    except Exception as exc:
        send({"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(exc)}})
