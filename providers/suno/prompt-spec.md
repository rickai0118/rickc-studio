# Suno Music 提示规范

> Provider: Suno v4/v4.5 via comfly.org proxy
> 模型: `suno_music` | 模式: 异步 submit→poll→download

## 核心机制

Suno 通过 comfly 接收**自然语言描述** (`gpt_description_prompt`)，内部展开为：
1. **Tags** — 详细的制作/风格/混音标签（Suno 自动生成）
2. **Lyrics** — AI 生成的歌词（包含结构标记 `[Verse]` `[Chorus]` 等）
3. **Prompt** — 通常固定为 `[Instrumental]` 或歌词首句

每次生成返回 **2 首** 独立的歌曲变体。

## gpt_description_prompt 写法

### 基础格式

```
<风格/流派> <氛围> <配器> <制作质感>
```

### 有效示例

```
a lo-fi chill beat with soft piano, warm vinyl crackle, 
mellow drums, and a late-night study vibe
```

```
upbeat synthwave track with driving 80s drums, arpeggiated 
bass, neon-soaked pads, and an anthemic chorus
```

```
emotional piano ballad with cinematic strings, slow build, 
delicate vocal, and a soaring orchestral finale
```

### 关键要素（按优先级）

| 要素 | 说明 | 示例 |
|------|------|------|
| **Genre/Style** | 流派或风格标签放在最前 | `lo-fi`, `synthwave`, `indie folk` |
| **Mood/Vibe** | 情绪氛围关键词 | `melancholic`, `energetic`, `dreamy` |
| **Instrumentation** | 核心乐器描述 | `soft piano`, `driving drums`, `string quartet` |
| **Production** | 制作/混音质感 | `warm vinyl crackle`, `spacious reverb`, `tight compression` |
| **Structure hint** | 结构提示（可选） | `building chorus`, `quiet verse`, `epic bridge` |

## 与 ACE-Step 的核心差异

| 维度 | ACE-Step | Suno |
|------|----------|------|
| 输入语言 | Tags（逗号分隔标签）+ Lyrics（结构标记）| 自然语言一句话 |
| 歌词 | 用户提供完整歌词+结构标记 | Suno 自动生成（或用户可选提供） |
| BPM/Key | 可精确指定 | 无法指定 |
| 返回数量 | 1 首 | 2 首 |
| 调用模式 | 同步（提交即返回音频） | 异步（submit → poll → download） |
| 流派精确度 | 高（标签系统精细） | 中（Suno 自己解释自然语言） |
| 声乐质量 | 中（需关键词辅助） | 高（Suno 默认人声合成优秀） |
| 制作细节可控性 | 极高（混音参数可逐项指定） | 低（仅自然语言暗示） |

## 已知限制与避坑

### 1. "custom mode" 触发防滥用
- ❌ 不要在请求中传 `mode: "custom"` — comfly 直接转发给 Suno，会触发 423 风控
- ✅ 只用 `gpt_description_prompt`，让平台处理模式选择

### 2. 无法指定 BPM/Key
- Suno API（via comfly）不支持精确 BPM 或调性设置
- 如需精确音乐参数，使用 ACE-Step

### 3. 结果不可复制
- 相同 prompt 每次生成结果不同（Suno 的随机种子不可控）
- 如需可复现的音乐生成，使用 ACE-Step

### 4. 中英文混合
- `gpt_description_prompt` 支持中英文混合，但英文流派/风格术语更精确
- 中文描述可能产生非预期的文化混合

### 5. 轮询超时
- 默认最大等待 300s，高负载时可能超时
- 超时后 task_id 仍有效，可手动重新轮询

## 鉴权

- **Header**: `Authorization: Bearer $COMLFY_API_KEY`
- **环境变量**: `COMLFY_API_KEY`（在 config.yaml 的 `auth.env_var` 中定义）
- Base URL: `https://ai.comfly.org`
