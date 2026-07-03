# rickc-studio 🎵

**R!CKC LABS Virtual Music Studio** — 多模型 AI 音乐生成工具集。

```
rickclabs-OS (编排/打包)  ←→  rickc-studio (生成)
```

## 支持的模型

| Provider | 状态 | 模式 | 模型 |
|----------|------|------|------|
| [ACE-Step 1.5](providers/ace/) | ✅ 已适配 | sync | ace-step-1.5 (LM + DiT) |
| [Suno](providers/suno/) | ✅ 已适配 | async | suno_music (v4/v4.5, comfly proxy) |
| Udio | 🔜 计划中 | — | — |

## 快速开始

```bash
# 1. 设置对应 provider 的 API Key
export ACE_MUSIC_API_KEY="your-key"        # ACE
export COMLFY_API_KEY="your-key"           # Suno via comfly

# 2. 同步生成 (ACE — 提交即返回音频)
python scripts/generate.py --provider ace

# 3. 异步生成 (Suno — submit → poll → download)
python scripts/generate.py --provider suno --prompt "a dreamy lo-fi beat"
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

## 添加新 Provider

```bash
cp -r providers/_template providers/riffusion
# 编辑 providers/riffusion/config.yaml (选择 sync/async)
# 写一个 prompt-spec.md
# 搞定，generate.py 会自己发现它
```

## 架构设计

`generate.py` 不关心具体调用哪个 API。它只做：

1. 读取 `providers/<name>/config.yaml`
2. 按 `task.mode` 调度同步/异步流程
3. 同步: base64 解码保存 | 异步: CDN 下载
4. 写入 archive 版本快照 + 更新 MANIFEST

加新模型 = 加配置，不动代码。

## License

MIT — R!CKC LABS
