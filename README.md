# rickc-studio 🎵

**R!CKC LABS Virtual Music Studio** — 多模型 AI 音乐生成工具集。

```
rickclabs-OS (编排/打包)  ←→  rickc-studio (生成)
```

## 支持的模型

| Provider | 状态 | 模式 | 模型 | 免费? |
|----------|------|------|------|------|
| [ACE-Step 1.5](providers/ace/) | ✅ 已适配 | sync | ace-step-1.5 (LM + DiT) | ✅ |
| [Suno](providers/suno/) | ✅ 已适配 | async | suno_music (v4/v4.5, comfly proxy) | ❌ B0.5/次 |
| [MiniMax](providers/minimax/) | ✅ 已适配 | minimax | music-2.6-free | ✅ RPM=3 |
| Udio | 🔜 计划中 | — | — | — |

## 快速开始

```bash
# 1. 设置对应 provider 的 API Key
export ACE_MUSIC_API_KEY="your-key"        # ACE
export COMLFY_API_KEY="your-key"           # Suno via comfly
export MINIMAX_API_KEY="your-key"          # MiniMax

# 2. 同步生成 (ACE)
python scripts/generate.py --provider ace

# 3. 异步生成 (Suno — submit → poll → download)
python scripts/generate.py --provider suno --prompt "a dreamy lo-fi beat"

# 4. MiniMax 生成 (同步, hex/url 直接返回)
python scripts/generate.py --provider minimax \
  --prompt "独立民谣, 忧郁, 内省" \
  --lyrics "[Verse]\n街灯微亮晚风轻抚\n[Chorus]\n推开木门香气弥漫"

# 5. MiniMax 纯音乐
python scripts/generate.py --provider minimax \
  --prompt "Lo-Fi hip hop, chill, piano, Jazz guitar" \
  --params is_instrumental=true

# 6. MiniMax 自动生成歌词
python scripts/generate.py --provider minimax \
  --prompt "Upbeat pop, summer love, ukulele, female vocal" \
  --params lyrics_optimizer=true
```

输出保存到 `output/`，生成记录自动存档到 `archive/`。

## 项目结构

```
rickc-studio/
├── providers/           ← 每个模型一个目录
│   ├── ace/             ← ACE-Step 1.5 (sync)
│   │   ├── config.yaml
│   │   ├── prompt-spec.md
│   │   └── pitfalls.md
│   ├── suno/            ← Suno Music v4/v4.5 (async)
│   │   ├── config.yaml
│   │   └── prompt-spec.md
│   ├── minimax/         ← MiniMax music-2.6 (minimax: hex/url 同步)
│   │   ├── config.yaml
│   │   └── prompt-spec.md
│   └── _template/       ← 新 provider 照着复制
├── scripts/
│   └── generate.py      ← 通用生成入口（自动读 provider 配置）
├── spec/
│   └── skill.md         ← ACE 完整技能规范 (18 模块)
├── output/              ← 生成的音频（.gitignore）
├── archive/             ← 生成记录存档（.gitignore）
└── LICENSE
```

## Provider 模式

| 模式 | 流程 | 适用 |
|------|------|------|
| **sync** | POST → 接收 base64 音频 → 解码保存 | ACE-Step |
| **async** | submit → poll → download CDN 音频 | Suno |
| **minimax** | POST → 接收 hex/URL 音频 → 保存 | MiniMax |

## 添加新 Provider

```bash
cp -r providers/_template providers/riffusion
# 编辑 providers/riffusion/config.yaml (选择 sync/async/minimax 模式)
# 写一个 prompt-spec.md
# 搞定，generate.py 会自己发现它
```

## 架构设计

`generate.py` 不关心具体调用哪个 API。它只做：

1. 读取 `providers/<name>/config.yaml`
2. 按 `task.mode` 调度对应流程 (sync / async / minimax)
3. 保存音频 + 写入 archive 版本快照 + 更新 MANIFEST
4. 加新模型 = 加配置，不动代码

## License

MIT — R!CKC LABS
