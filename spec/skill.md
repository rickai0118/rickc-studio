---
name: ace-step-music-prompting
description: ACE-Step 1.5 音乐生成完整规范 — Tags标签系统、Lyrics结构、Suno→ACE翻译规则、生成前检查清单、故障排除。双脑架构（LM+DiT）提示词规则。用 ACE Music API 或 ACE-Step 模型生成音乐时加载。
category: mlops/models
---

# ACE-Step 1.5 音乐生成提示规则

ACE-Step 与 Suno/Udio 的提示系统**完全不同**。ACE 使用 **Tags + Lyrics 分离结构**，由双脑架构（5Hz LM 策划器 + DiT 执行器）驱动，而非自然语言描述。

## 双脑架构速览

```
用户Tags → [5Hz LM 策划器] → 语义蓝图 → [DiT 执行器] → 音频
              ↓                    ↓
         CoT推理元数据          CFG控制遵循度
         优化Caption              shift控制细节/语义
         结构规划                 8步蒸馏极速出片
```

- **LM (thinking=true)**：AI 帮你扩展模糊描述，适合快速出 demo
- **No LM (thinking=false)**：你成为策划者，适合精确控制（Cover/Repaint 模式）
- **Turbo (8步)**：日常使用，速度快，创意丰富
- **XL Turbo (8步)**：更高质量，标签更敏感，小众风格混合可能翻车
- **SFT (50步)**：细节最丰富，支持 CFG 调参

## Tags 标签系统（核心）

### 标签公式
```
[Genre], [Mood], [2-3具体乐器], [Vocal Type], [Production Style], [NNN bpm]
```

Tags 以逗号分隔，顺序有语义优先级（向前权重高于后）。

### Tags 维度
| 维度 | 示例值 | 说明 |
|------|--------|------|
| **Genre（必首位）** | `lo-fi hip-hop`, `progressive techno`, `chamber folk` | 锚定一切 |
| **Mood** | `melancholic`, `energetic`, `dark`, `hopeful` | 情绪基调 |
| **Instruments** | `grand piano`, `upright bass`, `brushed drums` | 用具体乐器名，不用形容词 |
| **Vocal** | `female vocals`, `male rap vocals`, `no vocals`, `choir ooh` | 人声类型 |
| **Production** | `hi-fi`, `lo-fi`, `dusty`, `wide stereo`, `cinematic` | 混音/空间感 |
| **Texture** | `analog warmth`, `tape saturation`, `vinyl crackle` | 模拟质感 |
| **Dynamics** | `compressed`, `sidechain pumping` | 动态处理 |
| **BPM** | `88 bpm`, `134 bpm` | 双写：Tags + `bpm` 参数都要设 |

### ✅ 正确 vs ❌ 错误
```text
# ✅ 标签格式
lo-fi hip-hop, dusty drums, vinyl crackle, upright bass, male rap vocals, warm, 88 bpm

# ❌ 自然语言（Suno 风格）
"A beautiful lo-fi hip-hop track with dusty drums and vinyl crackle"
```

### 三大翻车点
1. **自然语言当 Tags** — 必须逗号分隔关键词
2. **BPM 不匹配风格** — techno 设 70 bpm（对应 128-140）
3. **no vocals + 写歌词** — 混淆信号，产生诡异无词人声

## Lyrics 歌词结构

Lyrics = 歌曲时间线脚本，用章节标记控制结构：

```
[intro]           器乐导奏
[verse]           主歌
[pre-chorus]      预副歌（张力建立）
[chorus]          副歌/高潮 — 重复
[bridge]          桥接/对比段
[inst]            器乐独奏/间奏
[build-up]        渐强（电子乐）
[drop]            高潮释放（EDM）
[breakdown]       能量减退
[outro]           尾奏
```

### 纯器乐
```text
Tags: progressive techno, dark, driving, analog modular synth, no vocals, 134 bpm
Lyrics: [intro] [inst] [build-up] [drop] [breakdown] [build-up] [drop] [outro]
bpm: 134
```

## API 调用模式

### Mode 1: Tagged（推荐）
```
messages: <prompt>tags</prompt>\n<lyrics>歌词</lyrics>
```

### Mode 2: Sample Mode（AI 自动写词曲）
```json
{"sample_mode": true, "messages": [{"content": "upbeat pop about summer"}]}
```

### Mode 3: Lyrics Only
只给歌词，AI 自动生成风格。

### Mode 4: Separate
`lyrics` 字段写词，`messages` 写 prompt。

## 关键参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `thinking` | false | true=LM策划器介入，自动扩展模糊描述 |
| `use_cot_caption` | true | CoT 优化标签描述 |
| `use_cot_language` | true | CoT 自动检测语言 |
| `guidance_scale` | 7.0 | 仅 SFT/Base，越高越严格遵循 prompt |
| `sample_mode` | false | AI 自动生成 prompt + lyrics |
| `use_format` | false | LLM 增强 prompt/lyrics |

## BPM + 拍号速查

| 风格 | BPM 范围 | 常见拍号 | 备注 |
|---|---|---|---|
| Ambient / Drone | 30–60 | 4/4 | 最慢，自由节奏 |
| Ballad / Acoustic | 60–80 | 4/4 或 3/4 | 情歌常用3/4华尔兹 |
| Slow Jazz | 60–90 | 4/4 或 3/4 | Swing 感 |
| Lo-fi Hip-hop | 70–90 | **2/4** | 半速 feel |
| R&B | 80–100 | 4/4 | 80-90 慵懒，90-100 律动 |
| Hip-hop / Trap | 85–100 | 4/4 | Half-time 130-145 |
| Synthwave | 90–110 | 4/4 | 复古 80s |
| Pop | 100–120 | 4/4 | 最通用的节奏 |
| Funk / Disco | 100–120 | 4/4 | 切分感 |
| House | 120–128 | 4/4 | Four-on-the-floor |
| Techno | 128–140 | 4/4 | 工业感 |
| EDM / Dubstep | 128–140 | 4/4 | Build-up + Drop |
| Rock | 120–140 | 4/4 | 鼓点厚重 |
| Metal | 140–180 | 4/4 | 双踩底鼓 |
| Punk | 160–200 | 4/4 | 极快 |
| Drum and Bass | 170–180 | 4/4 | 碎拍 |
| Waltz / 三拍子 | 90–180 | **3/4 或 6/8** | 华尔兹特色 |
| 进行曲 March | 100–120 | **2/4** | 军乐感 |

### Negative Styles 用法

Negative Styles 排除不需要的元素，防止 AI "自作主张"：

| 想要的感觉 | Negative Styles 写什么 |
|---|---|
| 纯器乐，不要人声 | `vocals, singing, vocal` |
| 不要电子元素 | `electronic, synth, edm` |
| 不要重金属 | `heavy metal, screaming, distorted guitar` |
| 要干净的制作 | `lo-fi, noisy, distorted, muddy` |
| 要现代感 | `vintage, retro, old-fashioned` |
| 不要太快 | `fast tempo, upbeat, energetic` |
| 不要太伤感 | `sad, melancholic, depressing` |

---

## 🎵 Suno → ACE 翻译规则

ACE-Step 不能直接接收 Suno 风格的自然语言提示词。以下是系统化翻译流程。

### 翻译流程

```
Suno输入 → ①提取核心元素 → ②转Tags格式 → ③重建Lyrics结构 → ④验证BPM/流派匹配 → ⑤生成前检查清单
```

### 翻译示例

**Suno 输入：**
> "A melancholic post-rock song with building crescendos, clean electric guitar, and soft male vocals, about losing someone you love"

**① 核心元素：** 流派 post-rock | 情绪 melancholic | 乐器 clean electric guitar | 人声 soft male vocals | 主题 loss

**② Tags：**
```
post-rock, melancholic, clean electric guitar, soft male vocals, building crescendos, wide stereo, atmospheric, 75 bpm
```

**③ Lyrics：**
```
[intro]
[verse] I trace the outline where you stood / A ghost of warmth in empty rooms
[chorus] And I'm still reaching through the silence / For a hand I'll never hold again
[verse] The photographs don't capture this / The weight of absence in the air
[chorus] And I'm still reaching through the silence / For a hand I'll never hold again
[bridge] Maybe someday the sharpness fades / Into something I can carry
[outro]
```

**④ 验证：** post-rock ✓ BPM 75 ∈ [60-80] ✓ 所有结构标签可用 ✓

### 翻译速查

| Suno元素 | ACE Tags |
|---|---|
| "upbeat pop song" | `pop, upbeat, synth, catchy, 120 bpm` |
| "sad piano ballad" | `piano ballad, melancholic, felt piano, intimate, female vocals, 68 bpm` |
| "heavy metal with screaming" | `metal, aggressive, distorted guitar, screaming vocals, double bass drum, 180 bpm` |
| "lo-fi study beats" | `lo-fi hip-hop, chill, jazzy, rhodes piano, vinyl crackle, no vocals, 80 bpm` |
| "epic orchestral trailer" | `cinematic, epic hybrid trailer, taiko drums, low brass swell, choir, no vocals, 90 bpm` |
| "EDM festival banger" | `progressive house, energetic, synth lead, 909 drums, sidechain pumping, 128 bpm` |
| "jazz club late night" | `jazz, smoky, saxophone solo, upright bass, brushed drums, warm, 100 bpm` |
| "Chinese guzheng ancient" | `traditional Chinese, guzheng, erhu, bamboo flute, ethereal, 60 bpm` |
| "R&B love song" | `R&B, romantic, smooth, electric piano, 808 bass, male vocals, falsetto, 75 bpm` |
| "synthwave night drive" | `synthwave, nostalgic, analog synth, gated reverb drums, arpeggio bass, no vocals, 100 bpm` |
| "K-pop girl group" | `K-pop, energetic, synth, trap beat, female vocals, layered harmonies, polished, 120 bpm` |
| "acoustic campfire" | `folk, warm, acoustic guitar, harmonica, group vocals, intimate, 90 bpm` |
| "dark ambient horror" | `dark ambient, haunting, sustained drone, granular texture, distant choir, sub rumble, no vocals, 55 bpm` |

### 参数对照

| Suno 风格参数 | ACE 实现 |
|---|---|
| 风格描述 | Tags 第一位 + Mood |
| `tempo: 120` | Tags 末尾 `120 bpm` **+** `--bpm 120` |
| `key: "C major"` | `--key "C major"` |
| `vocals: "female"` | Tags: `female vocals` |
| `instrumental: true` | Tags: `no vocals` 或 `instrumental` |
| `duration` | `--duration N`（秒） |
| 无歌词/AI写词 | `--sample-mode` |
| 有已有歌词 | 写入 `<lyrics>` 并加结构标签 |

### 翻译原则

1. **永远先提取流派** — 流派是 Tags 的锚，决定一切
2. **形容词变名词** — "sad" → `melancholic`, "fast" → 具体 BPM 数字
3. **描述变乐器** — "warm sound" → `analog warmth` + `tape saturation`
4. **一句话拆成结构** — "about losing someone" → 写成具体歌词 + 分配到 verse/chorus/bridge
5. **BPM 必须从风格推导** — Suno 不写 BPM，ACE 必须写（参考 BPM 速查表）

## 与 Suno 的核心差异

| | Suno / Udio | ACE-Step 1.5 |
|---|---|---|
| 提示格式 | 自然语言一句话 | Tags + Lyrics 分离 |
| 设计哲学 | 一键生成 | 人本生成（迭代协作） |
| 架构 | 端到端 | LM策划器 + DiT执行器 |
| 控制精度 | 粗粒度 | 每个维度独立调控 |
| 迭代能力 | 重新生成 | Cover/Repaint/Extract/Lego |
| 生成速度 | 较慢 | 8步蒸馏极速（2秒/A100） |
| 开源 | 闭源 | MIT 开源，可本地运行 |

## Windows 环境调用示例

```bash
# Windows MINGW64: 用 curl + python 管道，不用 generate.sh（依赖 python3 不可用）
curl -s -X POST "https://api.acemusic.ai/v1/chat/completions" \
  -H "Authorization: Bearer $ACE_MUSIC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages":[{"content":"lo-fi hip-hop, dusty drums, vinyl crackle, male vocals, warm, 88 bpm\n\n[verse] Late night coding\n[chorus] Keep pushing through"}],
    "audio_config":{"duration":30,"vocal_language":"en"}
  }' | python -c "
import sys, json, base64
d = json.load(sys.stdin)
b64 = d['choices'][0]['message']['audio'][0]['audio_url']['url'].split(',',1)[1]
with open('output.mp3','wb') as f: f.write(base64.b64decode(b64))
print('Saved: output.mp3')
"
```

## 🖥️ ACE Music 官网控制面板参数（UI ↔ API 映射）

基于官网实际截图分析（ACE-Step V1.5 XL Turbo 界面）。

### 模式切换选项卡

| UI 控件 | 说明 |
|---|---|
| **Simple** | 简单模式，一句话+AI自动补全所有参数 |
| **Custom** | 自定义模式，手动控制所有参数（推荐进阶用户） |
| **Remix** | 混音模式，基于上传的参考音频重新生成 |
| **Edit** | 编辑模式，对已有音频局部修改（Repaint） |

### Prompt 主输入区

| UI 控件 | 类型 | 说明 |
|---|---|---|
| **Prompt** | 大文本框 | 输入 Tags 标签 + Lyrics 歌词，支持结构标记 |
| **[Clear]** | 按钮 | 清空 Prompt 内容 |

Prompt 内结构示例（来自官网）：
```
[lntro]（氛围铺底）
[Verse 1] ...
[Pre-Chorus] ...
[Chorus] ...
[Outro]（呼应开头）
[End]
```

并可包含 **细化表演指令**，如：
```
clear perfect-pitch and intimate conversational catch-phrase 
phrasing but bouncy rhythmic delivery throughout,
Mid-proximity conversational in verses with light slap-back delay,
Close-mic forward in pre-chorus,
Chest-voice stomping presence in chorus...
```

### General / 常规设置

| UI 控件 | API 参数 | 默认值 | 可选值/范围 |
|---|---|---|---|
| **Duration** | `audio_config.duration` | Auto | **10s–240s** 手动输入 |
| **[Auto] [Clear]** | — | — | Auto=AI自动决定时长，Clear=恢复Auto |
| **Tempo** | `audio_config.bpm` | Auto | **30–200 bpm** 手动输入 |
| **[Auto] [Clear]** | — | — | Auto=AI根据风格自动推断BPM |
| **Time Signature** | `audio_config.time_signature` | Auto | **2 / 3 / 4 / 6** |
| **[Auto] [Clear]** | — | — | 拍号：2=二拍子, 3=华尔兹, 4=最常见的4/4, 6=6/8复合拍 |
| **Key** | `audio_config.key` | Auto > | 调性下拉（C~B + Major/Minor） |
| **[Auto] [>] [Clear]** | — | — | `>` 展开完整调性列表，Auto=AI自动匹配 |
| **Negative Styles** | `negative_styles` | 空 | 排除的风格关键词（逗号分隔），如 `heavy metal, screaming` |
| **[Clear]** | — | — | 清空排除列表 |

### Reference Audio / 参考音频

| UI 控件 | 说明 |
|---|---|
| **Cloud** 选项卡 | 从云端上传参考音频 → 用于 Remix/Cover 模式 |
| **Local** 选项卡 | 从本地上传参考音频 |
| **Upload Reference Audio** | 上传按钮/拖拽区 |

### Advance Options / 高级选项

| UI 控件 | API 参数 | 说明 |
|---|---|---|
| **Thinking: Creative** | `thinking: true` + creative模式 | AI创意策划模式 — 根据Prompt自动扩展、联想、补全细节 |
| **Thinking: Robust** | `thinking: true` + robust模式 | AI稳健策划模式 — 更严格遵循Prompt，少自由发挥 |
| **[Reset All]** | — | 一键恢复所有参数到默认值 |

### 底部操作

| UI 控件 | 说明 |
|---|---|
| **[Generate]** 按钮 | 提交生成请求，所有参数一起发送 |

### Let it fade... / 尾奏描述

Prompt 区域底部可见 `Let it fade...` 尾奏描述区，支持类似：
```
(Percussion replaced by vinyl breath... into street silence)
```
的细化场景描述。`[End]` 标记结束。

---

## 🗣️ 模糊自然语言引导创作流程

用户常给出模糊描述如 _"我想做一首夏天的歌"_ / _"帮我写个悲伤的"_ / _"来个抖音神曲"_

**禁止行为：** 直接塞给API。必须先走引导流程。

### 引导对话模板

```
用户输入（任意自然语言）
        ↓
第一步：选择模式 → Simple（速成）/ Custom（精控）/ Remix（混音）
        ↓
第二步：确认情绪与场景 → 推导流派+推荐BPM+拍号
第三步：确认乐器（具体名称）和 Negative Styles（排除项）
第四步：确认人声类型 → 是否需要上传参考音频
第五步：确认是否写歌词/让AI写/纯器乐
第六步：确认时长、调性（可建议默认值）和 Thinking 模式（Creative/Robust）
第七步：输出 Tags + Lyrics + 全部参数 → 走生成前检查清单 → 调用 API
```

### 分步问卷

**① 模式选择**
> "你想要哪种创作方式？"
> - 💨 **Simple** → 一句话描述，AI 搞定一切 → 用 `sample_mode: true`
> - 🎛️ **Custom** → 精确控制每个参数 → 走以下完整问卷
> - 🔄 **Remix** → 基于已有音频重新编曲 → 需要上传参考音频 → 走 Remix 流程

**② 情绪 → 流派推导**
> "这首歌想要什么感觉？"
> - 😢 悲伤/治愈 → Ballad (60-80 BPM) / Lo-fi (70-90) / Ambient (50-70)
> - 🔥 热血/励志 → Rock (120-140) / Pop Rock (110-130) / Epic Trailer (80-100)
> - 💃 快乐/舞动 → Pop (100-120) / House (120-128) / Funk (100-115)
> - 🌙 安静/放松 → Lo-fi (70-90) / Acoustic (80-100) / Jazz (90-110)
> - 🎮 电子/未来 → Synthwave (90-110) / Cyberpunk (120-140) / EDM (128-140)
> - 🏮 古风/中国风 → 传统中国风 (60-90) / 国风电子 (100-120)
> - ⚡ 抖音/短视频 → Pop (110-130) / Hip-hop (85-100) / EDM (128-140)
> - 🎸 摇滚/金属 → Rock (120-140) / Metal (140-180) / Punk (160-200)

**② 流派 + 乐器确认**
> "那就 [流派]，[BPM范围]。需要特定乐器吗？"
> - 不指定 → 用流派标配乐器自动补全
> - 用户指定 → 写入Tags（具体乐器名，不用形容词）

**③ 人声确认**
> "需要人声吗？"
> - 需要人声 → "男声还是女声？唱法风格？" → `male/female vocals, [风格]`
> - 纯音乐 → Tags加 `no vocals` 或 `instrumental`；Lyrics只写结构标签无文本
> - AI自己写词 → 启用 `sample_mode: true` 或 `thinking: true`

**④ 歌词决策**
> "你有歌词吗，还是我帮你写/让AI生成？"
> - 用户有词 → 分配结构标签（[verse]/[chorus]等），补全段落标记
> - 让AI写 → Tags中补充主题关键词 + 启用 `thinking: true`
> - AI全自动 → `sample_mode: true`，一句描述即可

**⑤ 验证确认**
> "确认一下：流派=[x], BPM=[y], 人声=[z], 时长=[30s], 调性=[默认C Major]。可以吗？"

### 快速引导速查（常用场景）

| 用户说 | 推导 | Tags | BPM | 拍号 | 调性建议 |
|---|---|---|---|---|---|
| "来首适合下雨天听的" | Lo-fi / Ballad | `lo-fi hip-hop, melancholic, rhodes piano, vinyl crackle, rain ambience, no vocals` | 75 | 2/4 | C Minor |
| "做个抖音卡点视频BGM" | Pop / EDM | `pop, energetic, synth bass, 808 drums, catchy hook, female vocals, compressed` | 128 | 4/4 | A Minor |
| "写一首告白的歌" | Acoustic Pop / R&B | `acoustic pop, romantic, fingerstyle吉他, soft male vocals, intimate, warm` | 85 | 4/4 | G Major |
| "来个燃的，运动用的" | Rock / EDM | `rock, energetic, distorted guitar, driving drums, male vocals, stadium reverb` | 140 | 4/4 | E Minor |
| "中国风，武侠那种" | 传统中国风 | `traditional Chinese, guzheng, erhu, dizi flute, cinematic, no vocals` | 75 | 4/4 | D Minor |
| "晚上开车听的" | Synthwave / Chill | `synthwave, nostalgic, analog synth, arpeggio bass, gated reverb drums, no vocals` | 95 | 4/4 | F Minor |
| "催眠曲/助眠" | Ambient / Drone | `ambient, calming, sustained pad, soft piano, binaural, no vocals` | 55 | 4/4 | C Major |
| "婚礼用的" | Classical / Acoustic | `classical, romantic, string quartet, piano, hopeful, no vocals` | 80 | 3/4 | F Major |
| "游戏BGM，战斗场景" | Epic Hybrid | `epic hybrid, taiko drums, brass stabs, distorted synth, choir, no vocals` | 140 | 4/4 | D Minor |
| "咖啡馆背景" | Jazz / Bossa Nova | `jazz, chill, saxophone, upright bass, brushed drums, warm, no vocals` | 95 | 4/4 | C Major |
| "华尔兹/圆舞曲" | Waltz | `waltz, elegant, string orchestra, piano, romantic, no vocals` | 120 | **3/4** | D Major |
| "进行曲" | March | `march, military drums, brass, triumphant, no vocals` | 108 | **2/4** | C Major |

### Sample Mode 使用时机

```
不需要复杂控 → 用 sample_mode: true
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"帮我随便生成一首歌"
"有什么好听的推荐吗"  
"来点音乐，什么风格都行"  
→ messages: "upbeat pop with summer vibes"
→ sample_mode: true
→ 不传Tags，不传Lyrics
```

## 🔴 生成前质量检查清单

每次提交生成请求前，逐项确认。任何一项不通过 = **不要生成**，先修：

### Tags 检查
- [ ] Tags 是逗号分隔关键词？（不是自然语言句子）
- [ ] Tags 5-12 个？（太少=模型乱发挥，太多=互相矛盾）
- [ ] 流派（Genre）放在 Tags 第一位？
- [ ] 乐器用具体名称（`grand piano`）而非形容词（`beautiful`）？
- [ ] 人声类型明确？（`female vocals` / `male rap vocals` / `no vocals` / `choir` / 省略=默认）

### BPM 检查
- [ ] BPM 写在 Tags 末尾（`88 bpm`）？
- [ ] BPM 传了 `--bpm` 参数？（必须双写）
- [ ] BPM 30–200 范围内？
- [ ] BPM 与流派匹配？（参考上方 BPM 速查表 — techno 不能是 70）

### 拍号 + Negative Styles + 时长检查
- [ ] 拍号匹配流派？（4/4 通用；3/4 或 6/8 华尔兹；2/4 进行曲/Lo-fi）
- [ ] 不想要的元素写了 Negative Styles？（纯器乐→排除 `vocals, singing`；不要电子→排除 `electronic, synth`）
- [ ] Duration 10s–240s 范围内？不确定用 Auto
- [ ] Remix/Edit 模式已上传参考音频？

### Lyrics 检查
- [ ] 歌词使用了结构标签引导段落（`[verse]` / `[chorus]` / `[bridge]` 等）？
- [ ] 纯器乐时 Lyrics 只有结构标签无歌词文本？
- [ ] 纯器乐时 Tags 已标注 `no vocals` 或 `instrumental`？
- [ ] ⚠️ 没有出现 Tags 写 `no vocals` + Lyrics 写有词文本的矛盾组合？

### 语言检查
- [ ] 非英文歌词指定了 `--language`（zh/ja/ko/等）？
- [ ] 歌词语言与 Tags 中的风格一致？（中文歌词 + `K-pop` = 矛盾）

### 风格内部一致性
- [ ] 情绪（Mood）与流派匹配？（`energetic` + `ballad` = 矛盾）
- [ ] 制作标签（hi-fi/lo-fi）与年代标签（90s/2020s）不冲突？
- [ ] 小众混合风格不超过「一主+一修」？（如 `darkwave + witch house` 可能翻车）

## 🕳️ Suno → ACE 避坑指南（实战累计）

> ACE 不是 Suno 的平替——它对复杂提示词的容忍度远低于 Suno，但对简单专注的指令表现更好。
> 系统性差异对照见 `references/suno-vs-ace-gap.md`。

### 已踩坑并修复的案例

#### 坑 #1：多流派标签导致声部分层飘移 {#pitfall-multi-genre}

**症状**：人声和伴奏不在同一图层，像两个调同时播放。

**案例**：`lo-fi vapor-dance, liquid garage, late-night house`（三流派同存）

**原因**：ACE 的双脑架构（LM 策划器 + DiT 执行器）对流派标签极其敏感。多个流派标签会被 LM 理解为"同时满足三种风格的声部分别叠加"，而非"融合一种风格"。

**修复**：选一个主流派，其余降级为修饰词。`三流派` → `lo-fi house`（v1→v2 BPM 142→115）

**教训**：Tags 的流派位只放一个词，多样性靠 Mood / Production 维度实现。

---

#### 坑 #2：BPM 与流派氛围打架 {#pitfall-bpm}

**症状**：伴奏节奏骨架偏快/偏慢，和歌词情绪割裂。

**案例**：`lo-fi ... 142 bpm`（lo-fi 区间 70-90，142 是 drum & bass）

**原因**：BPM 不仅影响速度，还影响 LM 策划器输出的整个节奏编排——包括鼓组模式、和弦密度、旋律步长。lo-fi + 142 BPM 会让 LM 输出 DnB 骨架 + lo-fi 音色 = 四不像。

**修复**：115 BPM（lo-fi house 折中点——House 节奏 + lo-fi 氛围）

**教训**：BPM 必须同时匹配 Tags 第一位流派和 Mood，不能只看 Suno 原文照搬。

---

#### 坑 #3：多 Key 转调在单次生成中崩溃 {#pitfall-multi-key}

**症状**：Bridge 段开始音高迷路，Chorus 喊不上去。

**案例**：`E minor (verse) → G major (chorus) → Em7b5 (bridge) → E minor (outro)`

**原因**：Suno 可以处理段落间的转调，但 ACE XL Turbo 的一次生成中，LM 策划器只能规划一个全局调性蓝图。多 Key 标记会引发 DiT 执行器在段落切换时产生谐波冲突。

**修复**：锁死一个 Key（E minor），让 ACE 自己推算情绪起伏，不要显式指定转调。

**教训**：需要多 Key 转调时，用 Remix/Edit 模式分段生成 + 拼接，或等 SFT 模型（50步）。

---

#### 坑 #4：演出指令过重压倒 Harmony {#pitfall-over-engineered}

**症状**：混音细节很足（delay/reverb/filter），但旋律本身苍白（`solune vari... amorphis...` 这些无词拟声都没唱出来）。

**案例**：15 行详细混音指令 vs 1 行旋律提示

**原因**：ACE 的 LM 策划器 token 预算有限——繁重的混音指令消费了大量 tokens，"主旋律应该怎么唱"的核心信号被稀释。

**修复**：精简到 1-2 行核心要点（`Soft intimate female vocal, light reverb. Steady house kick, vinyl warmth.`）

**教训**：perf hints 控制在 3 行以内。混音细节用 Tags 中的 Production/Timbre 维度传递，不要全写进 prompt。

---

#### 坑 #5：Suno 特效包装词在 ACE 中不可用 {#pitfall-suno-isms}

**症状**：`(anticipation)` / `[Energy: Low → Build]` / `[Non-lexical vocalise bounce marker: ...]` 等 Suno 专属指令被 ACE 照单全收但效果诡异。

**案例**：v1 中保留了 `[Energy: HIGH]` 和 `*[mid-proximity female vocal]*` 等 Suno 格式 → ACE 输出人声忽大忽小、动态不连贯。

**修复**：全部替换为 ACE 兼容的结构标签 + 简化描述。

**教训**：Suno 特有语法不跨平台兼容——翻译时必须清除：
- `[Energy: ...]` → ❌ 删除
- `(anticipation)` → ❌ 删除
- `*[...]*` 包裹 → ❌ 拆除，提取核心信息写入 perf hints
- `[Non-lexical vocalise marker: ...]` → ❌ 拆除，拟声词直接写进歌词行

### 防坑总则

| 原 则 | 说明 |
|---|---|
| **一流派原则** | Tags 第一位只放一个流派词，其余降级为修饰 |
| **BPM 不照搬** | Suno 的 BPM 可能是风格描述，ACE 必须查 BPM 速查表验证 |
| **Key 只写一个** | 需要转调 = Remix/Edit 分段生成，不做单次多调 |
| **指令 3 行上限** | perf hints 不超过 3 行，混音细节交给 Tags |
| **清除 Suno 方言** | `[Energy]` / `(anticipation)` / `*[...]*` 全部清理 |
| **无词拟声直接写** | `nae nae viora` 直接写入歌词行，不需要包裹标签 |
| **先简后繁** | 第一版用最简单 Tags 验证方向 ✓ → 再逐步加细节 |

| 症状 | 最可能原因 | 修复方法 |
|---|---|---|---|
| 输出风格完全跑偏 | Tags 用了自然语言而非逗号分隔关键词 | 重写 Tags 为标签格式，从流派开始 |
| BPM 明显不对 | Tags 写了 BPM 但没有传 `--bpm` 参数 | 夹带 `--bpm` 参数双写 |
| 有诡异的"啊——"无词人声 | Tags 写了 `no vocals` 但 Lyrics 里有歌词文本 | 去掉歌词 或 去掉 `no vocals`，二选一 |
| 编曲单调、细节不够 | Tags 太少（<5个），模型只有模糊方向 | 补充乐器、制作、空间标签到 8-10 个 |
| 混音发糊、没有立体感 | 缺少制作/空间标签 | 加 `hi-fi` / `polished` / `wide stereo` |
| 慢速风格失败（爵士、后摇、氛围） | Turbo 蒸馏偏向快节奏风格 | ① 启用 `use_cot_caption` ② 用 SFT 模型 + `guidance_scale` ③ 降低期望值 |
| 混合小众风格输出怪异 | 多流派标签冲突（如 `darkwave, witch house, phonk`） | 选择一个主流派 + 最多一个修饰 |
| 人声唱出奇怪语言 | 未指定 `--language` 或与歌词语言不一致 | 设置 `--language` 匹配歌词语言 |
| 歌曲时长不符 | duration 设 300s，XL Turbo 在长格式上可能失序 | 长格式用 SFT 模型，或分段生成 |
| 输出"配方感"重、缺人情味 | Tags 太精确，没给模型创意空间 | 减少标签至 6-8 个，启用 Thinking: Creative |
| 节奏感不对/3拍子变4拍 | 未设拍号，AI默认 4/4 | 华尔兹设 Time Signature=3，进行曲设 Time Signature=2 |
| 出现不想要的元素（人声/电子） | 未设 Negative Styles | 用 Negative Styles 排除（逗号分隔，如 `vocals, electronic`） |
| Remix/Edit 效果差 | 没上传参考音频或上传了低质量音频 | 上传高质量 WAV/MP3 参考音频，Cloud 或 Local 选项卡 |
| 每次生成 AI 都忽略提示词 | 用了 Base 模型但 `guidance_scale` 设太低了 | 提高 `guidance_scale` 到 10-15 |

## 完整 API 调用模板（Windows MINGW64 用）

```bash
# 步骤1: 确认 Key 已加载
echo "$ACE_MUSIC_API_KEY" | head -c 10

# 步骤2: 构建 Tags + Lyrics（见上方规则）
TAGS="lo-fi hip-hop, dusty drums, vinyl crackle, male rap vocals, warm, 88 bpm"
LYRICS="[intro]
[verse] Late night coding in the glow
[chorus] Keep pushing through the flow"

# 步骤3: 调用（生产级写法 — 含全参数 + 错误处理）
curl -s -X POST "https://api.acemusic.ai/v1/chat/completions" \
  -H "Authorization: Bearer $ACE_MUSIC_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$(python -c "
import json, sys
body = {
    'messages': [{'role': 'user', 'content': f'<prompt>${TAGS//\"/\\\"}</prompt>\n<lyrics>${LYRICS//\"/\\\"}</lyrics>'}],
    'audio_config': {
        'duration': 30,
        'bpm': 88,
        'vocal_language': 'en',
        'format': 'mp3'
    },
    'thinking': True
}
print(json.dumps(body))
")" | python -c "
import sys, json, base64
d = json.load(sys.stdin)
if 'choices' in d:
    audios = d['choices'][0]['message']['audio']
    for i, a in enumerate(audios):
        b64 = a['audio_url']['url'].split(',', 1)[1]
        fname = f'C:/Users/tinka/output_{i+1}.mp3'
        with open(fname, 'wb') as f:
            f.write(base64.b64decode(b64))
        print(f'✅ {fname}')
    meta = d['choices'][0]['message'].get('content','')
    if meta: print(meta)
else:
    print('❌ ERROR:', json.dumps(d.get('error', d), indent=2))
"
```

### 简化版（单行 prompt，适合快速测试）

```bash
curl -s -X POST "https://api.acemusic.ai/v1/chat/completions" \
  -H "Authorization: Bearer $ACE_MUSIC_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"lo-fi hip-hop, chill, rhodes piano, vinyl crackle, no vocals, 80 bpm"}],"audio_config":{"duration":30,"format":"mp3"}}' \
  | python -c "import sys,json,base64;d=json.load(sys.stdin);b64=d['choices'][0]['message']['audio'][0]['audio_url']['url'].split(',',1)[1];open('C:/Users/tinka/output.mp3','wb').write(base64.b64decode(b64));print('✅ output.mp3')"
```

## 资源

- API 文档: https://api.acemusic.ai（需 API Key）
- 官方模型: https://huggingface.co/anti-human-music/Ace-Step1.5
- GitHub: https://github.com/ace-step/ACE-Step
- 技术报告: https://arxiv.org/abs/2602.00744
- 完全指南: https://deapi.ai/blog/ace-step-1-5-prompting-guide

## 📦 生成指令存档机制

每次生成后必须存档，确保可溯源、调用和修改。

**存档目录：** `C:/Users/tinka/ace-archive/`
**结构：** `MANIFEST.json`（索引）+ `<slug>-vNNN-timestamp.json`（版本详情）

### 存档 JSON 字段

| 字段 | 说明 | 写入时机 |
|---|---|---|
| `version` / `timestamp` / `filename` | 元信息 | 生成前 |
| `ace_tags` / `ace_lyrics` / `ace_performance_hints` | 完整 ACE prompt | 生成前 |
| `api_params` | `{model, bpm, key, duration, thinking, format}` | 生成前 |
| `lyrics_languages` / `source` / `notes` | 上下文 | 生成前 |
| `output_file` / `output_size_kb` / `api_metadata` | 生成结果 | 生成后 |

### 常用溯源操作

| 需求 | 操作 |
|---|---|
| 列出所有版本 | 读 `MANIFEST.json` |
| 查看某版本完整参数 | 读对应 JSON |
| 基于旧版改 BPM 再生成 | JSON 取出 tags+lyrics → 改参数 → 新版本存档 |
| 按 BPM/Key 批量搜索 | `grep '"bpm": 142' ace-archive/*.json` |

**生成脚本：** `python C:/Users/tinka/ace_generate.py`（每次执行自动存档）

> 📄 **references/suno-vs-ace-gap.md** — Suno vs ACE 系统性差异对照（架构、提示系统、容错能力对比）
> 📄 **templates/ace_generate.py** — 可复用生成脚本模板（复制后填入 tags/lyrics/api_params 即可）
