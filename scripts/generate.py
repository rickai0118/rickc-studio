#!/usr/bin/env python3
"""
rickc-studio — Multi-Provider AI Music Generator

用法:
    python scripts/generate.py --provider ace
    python scripts/generate.py --provider suno --prompt "a lo-fi chill beat"
    python scripts/generate.py --provider ace --params bpm=120,key="D minor"

架构:
    不关心具体调用哪个 API。只从 providers/<name>/config.yaml
    读取配置 → 拼装请求 → 发送 → 解码保存 → 存档。
    加新模型 = 在 providers/ 下加一个目录，不动代码。

支持模式:
    sync  — 提交即返回音频 (ACE-Step)
    async — submit → poll → download (Suno via comfly)
"""

import argparse, json, base64, os, subprocess, sys, datetime, time, urllib.request
from pathlib import Path
import yaml  # pip install pyyaml

ROOT = Path(__file__).resolve().parent.parent
PROVIDERS_DIR = ROOT / "providers"
OUTPUT_DIR = ROOT / "output"
ARCHIVE_DIR = ROOT / "archive"

OUTPUT_DIR.mkdir(exist_ok=True)
ARCHIVE_DIR.mkdir(exist_ok=True)


# ──────────────────────────────────────────────────────────
#  Provider 加载 & 鉴权
# ──────────────────────────────────────────────────────────

def load_provider(name: str) -> dict:
    """加载 provider 配置"""
    config_path = PROVIDERS_DIR / name / "config.yaml"
    if not config_path.exists():
        print(f"❌ Provider '{name}' 不存在。可用: {list_providers()}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def list_providers() -> str:
    """列出所有可用 provider"""
    providers = [
        d.name for d in PROVIDERS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "config.yaml").exists()
    ]
    return ", ".join(providers) if providers else "(none)"


def get_api_key(config: dict) -> str:
    """从环境变量读取 API Key (兼容 env_key / env_var)"""
    auth = config["auth"]
    env_var = auth.get("env_var") or auth.get("env_key", "")
    if not env_var:
        print(f"❌ Provider 配置中未指定 auth.env_var 或 auth.env_key")
        sys.exit(1)
    key = os.environ.get(env_var, "")
    if not key:
        print(f"❌ 请设置 {env_var} 环境变量")
        sys.exit(1)
    return key


def build_headers(config: dict, api_key: str) -> dict:
    """根据 provider 配置拼装请求头"""
    auth = config["auth"]
    auth_type = auth.get("type", "bearer")
    if auth_type == "bearer":
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    elif auth_type == "api-key-header":
        header_name = auth.get("header_name", "X-API-Key")
        return {header_name: api_key, "Content-Type": "application/json"}
    elif auth_type == "api-key-query":
        return {"Content-Type": "application/json"}
    else:
        print(f"❌ 不支持的认证类型: {auth_type}")
        sys.exit(1)


def build_endpoint_url(config: dict, key: str = "submit") -> str:
    """拼装完整的 endpoint URL"""
    ep = config["endpoint"]
    base = ep["base"].rstrip("/")
    path = ep.get(key, "")
    return f"{base}{path}"


# ──────────────────────────────────────────────────────────
#  Sync 模式: ACE-Step 等 (提交即返回 base64 音频)
# ──────────────────────────────────────────────────────────

def generate_sync(config: dict, prompt: str, args: argparse.Namespace):
    """同步生成流程 (ACE 模式)"""
    name = config["name"]
    defaults = config.get("defaults", {})

    bpm = int(args.params.get("bpm", defaults.get("bpm", 120)))
    key = args.params.get("key", defaults.get("key", "C major"))
    duration = int(args.params.get("duration", defaults.get("duration", 240)))
    fmt = args.params.get("format", defaults.get("format", "mp3"))
    thinking_type = args.params.get("thinking", str(defaults.get("thinking", "disabled")))

    body = {
        "messages": [{"role": "user", "content": prompt}],
        "audio_config": {
            "duration": duration,
            "bpm": bpm,
            "key": key,
            "format": fmt,
        },
        "thinking": thinking_type,
    }

    api_key = get_api_key(config)
    headers = build_headers(config, api_key)
    url = build_endpoint_url(config, "generate")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    slug = args.slug or f"generated_{timestamp}"

    existing = len([f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".json") and f != "MANIFEST.json"])
    version = existing + 1
    archive_fname = f"{slug}-v{version:03d}-{timestamp}.json"

    print(f"🎵 {name} (sync)")
    print(f"   BPM: {bpm} | Key: {key} | Duration: {duration}s | Format: {fmt}")
    print(f"   Prompt: {len(prompt)} chars")
    print(f"   Generating...")

    curl_cmd = [
        "curl", "-s", "-X", "POST", url,
        "-H", f"Authorization: {headers.get('Authorization', 'unset')}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(body, ensure_ascii=False),
    ]
    result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0:
        print(f"❌ curl error: {result.stderr}")
        sys.exit(1)

    d = json.loads(result.stdout)

    if "error" in d:
        print(f"❌ API error: {json.dumps(d['error'], ensure_ascii=False, indent=2)}")
        sys.exit(1)
    if "choices" not in d:
        print(f"❌ Unexpected response (no choices): {json.dumps(d, ensure_ascii=False)[:500]}")
        sys.exit(1)

    audios = d["choices"][0]["message"]["audio"]
    print(f"✅ Got {len(audios)} audio file(s)")

    archive_record = {
        "provider": args.provider,
        "version": version,
        "timestamp": timestamp,
        "bpm": bpm, "key": key, "duration": duration,
        "prompt": prompt[:500],
        "output_files": [],
    }

    for i, a in enumerate(audios):
        b64 = a["audio_url"]["url"].split(",", 1)[1]
        suffix = f"_{i}" if len(audios) > 1 else ""
        fname = OUTPUT_DIR / f"{slug}{suffix}.{fmt}"
        with open(fname, "wb") as f:
            f.write(base64.b64decode(b64))
        size_kb = os.path.getsize(fname) / 1024
        print(f"   → {fname} ({size_kb:.0f} KB)")
        archive_record["output_files"].append(str(fname))

    archive_path = ARCHIVE_DIR / archive_fname
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(archive_record, f, ensure_ascii=False, indent=2)

    update_manifest()

    if "content" in d["choices"][0]["message"]:
        print(f"\n📝 {d['choices'][0]['message']['content']}")

    print(f"\n📁 Archive: {archive_path}")
    print(f"📊 MANIFEST updated")


# ──────────────────────────────────────────────────────────
#  MiniMax 模式: 同步返回 hex 或 URL, 无需轮询
# ──────────────────────────────────────────────────────────

def generate_minimax(config: dict, args: argparse.Namespace):
    """MiniMax 音乐生成 (同步: 提交 → 直接返回 hex/url)"""
    name = config["name"]
    model = config.get("model", "music-2.6-free")
    audio_setting = config.get("audio_setting", {})

    # 拼装请求体
    body = {"model": model}

    # prompt: 纯音乐时必填, 有歌词时可选
    prompt = args.prompt or args.params.get("prompt", "")
    body["prompt"] = prompt

    # lyrics
    lyrics = args.lyrics or args.params.get("lyrics", "")
    if lyrics:
        body["lyrics"] = lyrics

    # is_instrumental
    is_instrumental = args.params.get("is_instrumental", "false").lower() in ("true", "1", "yes")
    if is_instrumental:
        body["is_instrumental"] = True

    # lyrics_optimizer
    lyrics_optimizer = args.params.get("lyrics_optimizer", "false").lower() in ("true", "1", "yes")
    if lyrics_optimizer:
        body["lyrics_optimizer"] = True

    # output_format
    output_fmt = args.params.get("output_format", "url")
    body["output_format"] = output_fmt

    # aigc_watermark
    aigc_watermark = args.params.get("aigc_watermark", "false").lower() in ("true", "1", "yes")
    if aigc_watermark:
        body["aigc_watermark"] = True

    # audio_setting
    body["audio_setting"] = {
        "sample_rate": int(args.params.get("sample_rate", audio_setting.get("sample_rate", 44100))),
        "bitrate": int(args.params.get("bitrate", audio_setting.get("bitrate", 256000))),
        "format": args.params.get("format", audio_setting.get("format", "mp3")),
        "channel": int(args.params.get("channel", audio_setting.get("channel", 2))),
    }

    api_key = get_api_key(config)
    headers = build_headers(config, api_key)
    url = build_endpoint_url(config, "generate")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    slug = args.slug or f"minimax_{timestamp}"

    print(f"🎵 {name} (minimax / {model})")
    if prompt:
        print(f"   Prompt: \"{prompt[:120]}{'…' if len(prompt) > 120 else ''}\"")
    if lyrics:
        print(f"   Lyrics: {len(lyrics)} chars")
    print(f"   Instrumental: {is_instrumental}")
    print(f"   Output format: {output_fmt}")
    print(f"   Generating...")

    result = subprocess.run(
        ["curl", "-s", "-X", "POST", url,
         "-H", f"Authorization: Bearer {api_key}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(body, ensure_ascii=False)],
        capture_output=True, text=True, timeout=120,
    )

    if result.returncode != 0:
        print(f"❌ curl error: {result.stderr}")
        sys.exit(1)

    d = json.loads(result.stdout)

    # 检查返回
    base_resp = d.get("base_resp", {})
    if base_resp.get("status_code", -1) != 0:
        err_msg = base_resp.get("status_msg", "unknown error")
        print(f"❌ API error ({base_resp.get('status_code')}): {err_msg}")
        print(f"   Full: {json.dumps(d, ensure_ascii=False)[:500]}")
        sys.exit(1)

    data = d.get("data", {})
    extra = d.get("extra_info", {})

    audio_hex = data.get("audio", "")
    audio_url = data.get("audio_url", "")

    if not audio_hex and not audio_url:
        print(f"❌ No audio in response: {json.dumps(d, ensure_ascii=False)[:500]}")
        sys.exit(1)

    duration_ms = extra.get("music_duration", 0)
    sample_rate = extra.get("music_sample_rate", 0)
    channels = extra.get("music_channel", 0)
    bitrate = extra.get("bitrate", 0)
    music_size = extra.get("music_size", 0)
    fmt = body["audio_setting"]["format"]

    print(f"✅ Generated!")
    print(f"   Duration: {duration_ms / 1000:.1f}s | {sample_rate}Hz | {channels}ch | {bitrate // 1000}kbps")

    # URL 格式: audio 字段直接是 URL 字符串
    if audio_hex.startswith("http"):
        audio_url = audio_hex
        audio_hex = ""

    # 保存
    fname = OUTPUT_DIR / f"{slug}.{fmt}"

    if audio_hex:
        # hex 格式直接解码
        audio_bytes = bytes.fromhex(audio_hex)
        with open(fname, "wb") as f:
            f.write(audio_bytes)
    elif audio_url:
        # URL 格式下载
        print(f"   Downloading {audio_url}...")
        try:
            urllib.request.urlretrieve(audio_url, str(fname))
        except Exception as e:
            print(f"   ❌ Download failed: {e}")
            sys.exit(1)

    size_kb = os.path.getsize(fname) / 1024
    print(f"   → {fname} ({size_kb:.0f} KB)")

    # 存档
    existing = len([f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".json") and f != "MANIFEST.json"])
    version = existing + 1
    archive_fname = f"{slug}-v{version:03d}-{timestamp}.json"

    archive_record = {
        "provider": args.provider,
        "model": model,
        "version": version,
        "timestamp": timestamp,
        "prompt": prompt[:500],
        "lyrics": lyrics[:500] if lyrics else "",
        "is_instrumental": is_instrumental,
        "duration_ms": duration_ms,
        "sample_rate": sample_rate,
        "channels": channels,
        "bitrate": bitrate,
        "music_size": music_size,
        "output_format": output_fmt,
        "output_file": str(fname),
    }

    archive_path = ARCHIVE_DIR / archive_fname
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(archive_record, f, ensure_ascii=False, indent=2)

    update_manifest()
    print(f"\n📁 Archive: {archive_path}")
    print(f"📊 MANIFEST updated (v{version})")


# ──────────────────────────────────────────────────────────
#  Async 模式: Suno via comfly (submit → poll → download)
# ──────────────────────────────────────────────────────────

def generate_async(config: dict, args: argparse.Namespace):
    """异步生成流程 (Suno 模式)"""
    name = config["name"]
    task_cfg = config.get("task", {})
    params_cfg = config.get("params", {})

    poll_interval = task_cfg.get("poll_interval_sec", 8)
    max_wait = task_cfg.get("max_wait_sec", 300)
    songs_per_gen = task_cfg.get("songs_per_gen", 2)

    api_key = get_api_key(config)
    headers = build_headers(config, api_key)

    # 拼装请求体 (Suno 用 gpt_description_prompt)
    # 注意: comfly 层转发的额外字段 (model, make_instrumental=false 等)
    # 可能触发 Suno 侧 423 风控。仅发送有效字段。
    gpt_prompt = args.prompt or args.lyrics or "(instrumental lo-fi)"
    body = {"gpt_description_prompt": gpt_prompt}

    # 只在明确需要时添加可选字段
    make_instrumental = args.params.get("make_instrumental", "false").lower() in ("true", "1", "yes")
    if make_instrumental:
        body["make_instrumental"] = True

    print(f"🎵 {name} (async)")
    print(f"   Prompt: \"{body.get('gpt_description_prompt', '')[:120]}...\"")

    # ── Step 1: Submit ──
    submit_url = build_endpoint_url(config, "submit")
    print(f"   Submitting...")
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", submit_url,
         "-H", f"Authorization: {headers.get('Authorization', 'unset')}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(body, ensure_ascii=False)],
        capture_output=True, text=True, timeout=60,
    )

    if result.returncode != 0:
        print(f"❌ Submit error: {result.stderr}")
        sys.exit(1)

    submit_resp = json.loads(result.stdout)
    if submit_resp.get("code") != "success":
        print(f"❌ Submit failed: {json.dumps(submit_resp, ensure_ascii=False)[:500]}")
        sys.exit(1)

    task_id = submit_resp["data"]
    if not isinstance(task_id, str):
        task_id = submit_resp.get("data", {}).get("task_id", "")
    print(f"   Task ID: {task_id}")

    # ── Step 2: Poll ──
    fetch_path = config["endpoint"]["fetch"].replace("{task_id}", task_id)
    fetch_url = f"{config['endpoint']['base'].rstrip('/')}{fetch_path}"

    print(f"   Polling (every {poll_interval}s, timeout {max_wait}s)...")
    started = time.time()
    final_data = None

    while time.time() - started < max_wait:
        time.sleep(poll_interval)
        result = subprocess.run(
            ["curl", "-s",
             "-H", f"Authorization: {headers.get('Authorization', 'unset')}",
             fetch_url],
            capture_output=True, text=True, timeout=30,
        )
        poll_resp = json.loads(result.stdout)
        if poll_resp.get("code") != "success":
            elapsed = int(time.time() - started)
            print(f"   [{elapsed}s] ⚠️  Poll error, retrying...")
            continue

        data = poll_resp["data"]
        status = data.get("status", "")
        progress = data.get("progress", "")
        elapsed = int(time.time() - started)
        print(f"   [{elapsed}s] {status} {progress}")

        if status == "SUCCESS":
            final_data = data
            break
    else:
        print(f"❌ Timeout ({max_wait}s). Task {task_id} may still be processing.")
        print(f"   手动轮询: curl -H 'Authorization: Bearer $COMLFY_API_KEY' {fetch_url}")
        sys.exit(1)

    if not final_data:
        print(f"❌ No data returned after poll loop.")
        sys.exit(1)

    songs = final_data.get("data", [])
    if not songs:
        print(f"❌ No songs in response: {json.dumps(final_data, ensure_ascii=False)[:500]}")
        sys.exit(1)

    print(f"✅ Got {len(songs)} song(s)")

    # ── Step 3: Download ──
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    existing = len([f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".json") and f != "MANIFEST.json"])
    version = existing + 1
    slug = args.slug or f"suno_{timestamp}"

    archive_record = {
        "provider": args.provider,
        "version": version,
        "timestamp": timestamp,
        "task_id": task_id,
        "prompt": body.get("gpt_description_prompt", "")[:500],
        "songs": [],
        "output_files": [],
    }

    for i, song in enumerate(songs):
        song_id = song.get("id", f"unknown_{i}")
        title = song.get("title", "Untitled")
        audio_url = song.get("audio_url", "")
        tags = song.get("tags", "")
        duration_sec = song.get("duration", 0)
        metadata = song.get("metadata", {})

        print(f"\n   Song {i+1}: \"{title}\"")
        print(f"      ID: {song_id}")
        print(f"      Duration: {duration_sec:.1f}s")
        print(f"      Tags: {tags[:150]}...")

        suffix = f"_{i}" if len(songs) > 1 else ""
        fname = OUTPUT_DIR / f"{slug}{suffix}.mp3"

        if audio_url:
            print(f"      Downloading {audio_url}...")
            try:
                urllib.request.urlretrieve(audio_url, str(fname))
                size_kb = os.path.getsize(fname) / 1024
                print(f"      → {fname} ({size_kb:.0f} KB)")
            except Exception as e:
                print(f"      ❌ Download failed: {e}")
                continue
        else:
            print(f"      ⚠️  No audio_url in response, skipping.")
            continue

        archive_record["output_files"].append(str(fname))
        archive_record["songs"].append({
            "title": title,
            "id": song_id,
            "duration": duration_sec,
            "tags": tags[:300],
            "file": str(fname),
        })

    archive_fname = f"{slug}-v{version:03d}-{timestamp}.json"
    archive_path = ARCHIVE_DIR / archive_fname
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(archive_record, f, ensure_ascii=False, indent=2)

    update_manifest()
    print(f"\n📁 Archive: {archive_path}")
    print(f"📊 MANIFEST updated (v{version})")


# ──────────────────────────────────────────────────────────
#  Manifest
# ──────────────────────────────────────────────────────────

def update_manifest():
    """更新生成记录索引"""
    manifest_path = ARCHIVE_DIR / "MANIFEST.json"
    entries = []
    for f in sorted(ARCHIVE_DIR.glob("*.json")):
        if f.name == "MANIFEST.json":
            continue
        try:
            with open(f, "r", encoding="utf-8") as mf:
                e = json.load(mf)
                entries.append({
                    "version": e.get("version", "?"),
                    "timestamp": e.get("timestamp", "?"),
                    "provider": e.get("provider", "?"),
                    "bpm": e.get("bpm", "?"),
                    "key": e.get("key", "?"),
                    "task_id": e.get("task_id", ""),
                })
        except Exception:
            pass
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"total": len(entries), "entries": entries}, f, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────────────────────
#  Prompt 组装 (ACE 模式: tags + lyrics)
# ──────────────────────────────────────────────────────────

def build_prompt_sync(config: dict, args: argparse.Namespace) -> str:
    """ACE 模式: 加载 tags + lyrics"""
    prompt_config = config.get("prompt", {})
    tags = ""
    if prompt_config.get("tags_required"):
        tags_file = PROVIDERS_DIR / args.provider / "prompt_spec.md"
        if tags_file.exists():
            tags = tags_file.read_text(encoding="utf-8")
    lyrics = args.lyrics or "(instrumental)"
    if prompt_config.get("tags_required"):
        return f"{tags}\n\n{lyrics}"
    return lyrics


# ──────────────────────────────────────────────────────────
#  Entry
# ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="rickc-studio — Multi-Provider AI Music Generator")
    parser.add_argument("--provider", "-p", default="", help=f"Provider 名称 (可用: {list_providers()})")
    parser.add_argument("--slug", "-s", default="", help="输出文件名前缀")
    parser.add_argument("--params", default="", help="覆写参数: bpm=120,key=D minor,duration=180")
    parser.add_argument("--prompt", default="", help="自然语言提示 (Suno 模式)")
    parser.add_argument("--lyrics", "-l", default="", help="歌词内容 (或用 --lyrics-file)")
    parser.add_argument("--lyrics-file", default="", help="从文件读取歌词")
    parser.add_argument("--list", action="store_true", help="列出所有可用 provider")

    args = parser.parse_args()

    if args.list:
        print(f"可用 providers: {list_providers()}")
        return

    if not args.provider:
        parser.error("--provider/-p 是必需的 (或用 --list 查看可用 provider)")

    # 解析 --params
    params = {}
    if args.params:
        for item in args.params.split(","):
            item = item.strip()
            if "=" in item:
                k, v = item.split("=", 1)
                params[k.strip()] = v.strip().strip('"').strip("'")
    args.params = params

    # 数值转换
    for int_field in ("duration", "bpm"):
        if int_field in params:
            params[int_field] = int(params[int_field])

    # 读取歌词文件
    if args.lyrics_file:
        with open(args.lyrics_file, "r", encoding="utf-8") as f:
            args.lyrics = f.read()

    config = load_provider(args.provider)
    task_mode = config.get("task", {}).get("mode", "sync")

    if task_mode == "async":
        generate_async(config, args)
    elif task_mode == "minimax":
        generate_minimax(config, args)
    else:
        prompt = build_prompt_sync(config, args)
        generate_sync(config, prompt, args)


if __name__ == "__main__":
    main()
