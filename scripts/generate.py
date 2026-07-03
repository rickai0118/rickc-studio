#!/usr/bin/env python3
"""
rickc-studio — Multi-Provider AI Music Generator

用法:
    python scripts/generate.py --provider ace
    python scripts/generate.py --provider ace --params bpm=120,key="D minor"

架构:
    不关心具体调用哪个 API。只从 providers/<name>/config.yaml
    读取配置 → 拼装请求 → 发送 → 解码保存 → 存档。
    加新模型 = 在 providers/ 下加一个目录，不动代码。
"""

import argparse, json, base64, os, subprocess, sys, datetime
from pathlib import Path
import yaml  # pip install pyyaml

ROOT = Path(__file__).resolve().parent.parent
PROVIDERS_DIR = ROOT / "providers"
OUTPUT_DIR = ROOT / "output"
ARCHIVE_DIR = ROOT / "archive"

OUTPUT_DIR.mkdir(exist_ok=True)
ARCHIVE_DIR.mkdir(exist_ok=True)


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
    """从环境变量读取 API Key"""
    auth = config["auth"]
    key = os.environ.get(auth["env_key"], "")
    if not key:
        print(f"❌ 请设置 {auth['env_key']} 环境变量")
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
        # 查询参数在 build_url 中处理
        return {"Content-Type": "application/json"}
    else:
        print(f"❌ 不支持的认证类型: {auth_type}")
        sys.exit(1)


def generate(config: dict, args: argparse.Namespace):
    """通用生成流程"""
    defaults = config.get("defaults", {})
    name = config["name"]

    # 合并参数覆盖
    bpm = args.params.get("bpm", defaults.get("bpm", 120))
    key = args.params.get("key", defaults.get("key", "C major"))
    duration = args.params.get("duration", defaults.get("duration", 240))
    fmt = args.params.get("format", defaults.get("format", "mp3"))
    thinking = args.params.get("thinking", defaults.get("thinking", False))

    # 加载提示内容
    tags_file = PROVIDERS_DIR / args.provider / "prompt_spec.md"
    tags = ""
    if tags_file.exists():
        tags = tags_file.read_text(encoding="utf-8")

    # 组装 prompt（ACE 模式：tags + lyrics → 合并到一个 message）
    prompt_config = config.get("prompt", {})
    lyrics = getattr(args, "lyrics", "") or "(instrumental)"
    if prompt_config.get("tags_required"):
        prompt = f"{tags}\n\n{lyrics}"
    else:
        prompt = lyrics

    # 拼装请求体
    body = {
        "messages": [{"role": "user", "content": prompt}],
        "audio_config": {
            "duration": duration,
            "bpm": bpm,
            "key": key,
            "format": fmt,
        },
        "thinking": thinking,
    }

    api_key = get_api_key(config)
    headers = build_headers(config, api_key)
    endpoint = config["endpoint"]

    # 版本号 & 存档
    existing = len([f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".json") and f != "MANIFEST.json"])
    version = existing + 1
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    slug = args.slug or f"generated_{timestamp}"
    archive_fname = f"{slug}-v{version:03d}-{timestamp}.json"

    print(f"🎵 {name}")
    print(f"   BPM: {bpm} | Key: {key} | Duration: {duration}s | Format: {fmt}")
    print(f"   Prompt: {len(prompt)} chars, {len(lyrics.splitlines())} lyric lines")
    print(f"   Generating...")

    result = subprocess.run(
        ["curl", "-s", "-X", "POST", endpoint,
         "-H", f"Authorization: Bearer {api_key}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(body, ensure_ascii=False)],
        capture_output=True, text=True, timeout=300
    )

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

    # 写入存档
    archive_path = ARCHIVE_DIR / archive_fname
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(archive_record, f, ensure_ascii=False, indent=2)

    # 更新 MANIFEST
    update_manifest()

    if "content" in d["choices"][0]["message"]:
        print(f"\n📝 {d['choices'][0]['message']['content']}")

    print(f"\n📁 Archive: {archive_path}")
    print(f"📊 MANIFEST updated")


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
                })
        except Exception:
            pass
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"total": len(entries), "entries": entries}, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="rickc-studio — Multi-Provider AI Music Generator")
    parser.add_argument("--provider", "-p", required=True, help=f"Provider 名称 (可用: {list_providers()})")
    parser.add_argument("--slug", "-s", default="", help="输出文件名前缀")
    parser.add_argument("--params", default="", help="覆写参数: bpm=120,key=D minor,duration=180")
    parser.add_argument("--lyrics", "-l", default="", help="歌词内容 (或用 --lyrics-file)")
    parser.add_argument("--lyrics-file", default="", help="从文件读取歌词")
    parser.add_argument("--list", action="store_true", help="列出所有可用 provider")

    args = parser.parse_args()

    if args.list:
        print(f"可用 providers: {list_providers()}")
        return

    # 解析 --params
    params = {}
    if args.params:
        for item in args.params.split(","):
            item = item.strip()
            if "=" in item:
                k, v = item.split("=", 1)
                params[k.strip()] = v.strip().strip('"').strip("'")
    args.params = params

    # 解析 key/duration 为 int
    if "duration" in params:
        params["duration"] = int(params["duration"])
    if "bpm" in params:
        params["bpm"] = int(params["bpm"])
    if "thinking" in params:
        params["thinking"] = params["thinking"].lower() in ("true", "1", "yes")

    # 读取歌词
    if args.lyrics_file:
        with open(args.lyrics_file, "r", encoding="utf-8") as f:
            args.lyrics = f.read()

    config = load_provider(args.provider)
    generate(config, args)


if __name__ == "__main__":
    main()
