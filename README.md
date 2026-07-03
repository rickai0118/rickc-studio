# rickc-studio 🎵

**R!CKC LABS Virtual Music Studio** — 多模型 AI 音乐生成工具集。

```
rickclabs-OS (编排/打包)  ←→  rickc-studio (生成)
```

## 支持的模型

| Provider | 状态 | 模型 |
|----------|------|------|
| [ACE-Step 1.5](providers/ace/) | ✅ 已适配 | ace-step-1.5 (LM + DiT) |
| Suno | 🔜 计划中 | — |
| Udio | 🔜 计划中 | — |
| Riffusion | 🔜 计划中 | — |

## 快速开始

```bash
# 1. 设置对应 provider 的 API Key
export ACE_MUSIC_API_KEY="your-key"

# 2. 生成音乐
python scripts/generate.py --provider ace
```

输出保存到 `output/`，生成记录自动存档到 `archive/`。

## 项目结构

```
rickc-studio/
├── providers/           ← 每个模型一个目录
│   ├── ace/             ← ACE-Step 1.5
│   │   ├── config.yaml      模型参数 & API 端点
│   │   ├── prompt-spec.md   标签 / 歌词规范
│   │   └── pitfalls.md      避坑指南
│   └── _template/       ← 新 provider 照着复制
├── scripts/
│   └── generate.py      ← 通用生成入口（自动读 provider 配置）
├── spec/
│   └── skill.md         ← ACE 完整技能规范 (18 模块)
├── output/              ← 生成的音频（.gitignore）
├── archive/             ← 生成记录存档（.gitignore）
└── LICENSE
```

## 添加新 Provider

```bash
cp -r providers/_template providers/suno
# 编辑 providers/suno/config.yaml
# 写一个 prompt-spec.md
# 搞定，generate.py 会自己发现它
```

## 架构设计

`generate.py` 不关心具体调用哪个 API。它只做四件事：

1. 读取 `providers/<name>/config.yaml`
2. 按 config 拼装 API 请求
3. 发送 → 接收 base64 音频 → 解码保存
4. 写入 archive 版本快照

加新模型 = 加配置，不动代码。

## License

MIT — R!CKC LABS
