# MiniMax Music 提示词规范

MiniMax music-2.6 使用 **prompt + lyrics 分离输入**，与 ACE 的 Tags+Lyrics 类似但更灵活。

---

## 1. Prompt（风格描述）

**格式：逗号分隔的标签**（不是自然语言段落）

```text
独立民谣, 忧郁, 内省, 渴望, 独自漫步, 咖啡馆
```

### 有效标签类型

| 类别 | 示例 |
|------|------|
| **音乐流派** | `电子`, `独立民谣`, `J-Pop`, `City Pop`, `管弦`, `爵士` |
| **情绪/氛围** | `忧郁`, `温暖`, `史诗`, `放松`, `内省`, `欢快` |
| **场景** | `咖啡馆`, `雨中`, `夜空`, `海风` |
| **人声风格** | `男声独唱`, `女声独唱`, `男女对唱`, `合唱` |
| **乐器** | `钢琴`, `民谣吉他`, `弦乐`, `鼓` |
| **制作风格** | `Lo-Fi`, `模拟`, `空间感` |

### 关键规则

- **长度**: 1-2000 字符
- **分隔**: 逗号
- **有歌词时可选**: 如果传了 `lyrics`，prompt 可简写几个标签
- **纯音乐时必填**: `is_instrumental: true` 时 prompt 必须充分描述风格

---

## 2. Lyrics（歌词 + 结构）

### 结构标签（14 个 reserved keywords）

```text
[Intro]      — 前奏
[Verse]      — 主歌
[Pre Chorus] — 预副歌
[Chorus]     — 副歌
[Hook]       — 钩子
[Post Chorus]— 后副歌
[Bridge]     — 桥段
[Build Up]   — 铺垫
[Interlude]  — 间奏
[Inst]       — 乐器段
[Solo]       — 独奏
[Transition] — 过渡
[Break]      — 停顿
[Outro]      — 尾奏
```

### 格式示例

```
[Intro]

[Verse]
街灯微亮晚风轻抚
影子拉长独自漫步

[Chorus]
推开木门香气弥漫
熟悉的角落陌生人看

[Verse]
旧唱片的沙沙声响
回忆在空气中飘荡

[Chorus]
推开木门香气弥漫
熟悉的角落陌生人看

[Outro]
晚安晚安这座城市
晚安我亲爱的影子
```

### 规则

- 每行一句歌词，`\n` 隔开
- 标签独占一行，前后留空行
- 长度 1-3500 字符
- 结构标签不支持自定义，只认上面 14 个

---

## 3. 纯音乐

设置 `is_instrumental: true`，此时：
- `prompt` **必填**（充分描述风格、情绪、乐器）
- `lyrics` 为空
- 不要传 `lyrics_optimizer`

```text
prompt: "Cinematic orchestral, building tension, epic battle, strings, brass, percussion"
is_instrumental: true
```

---

## 4. 自动生成歌词

设置 `lyrics_optimizer: true`，系统根据 `prompt` 自动创作歌词：

```text
prompt: "Upbeat pop, summer love, beach, ukulele, bright female vocal"
lyrics_optimizer: true
# 不传 lyrics
```

---

## 5. 实战 Prompt 库

### 中文流行

```text
prompt: "中文流行, J-Pop, 青春, 活力, 女声独唱, 钢琴, 鼓"
lyrics: "[Verse]\n阳光洒在课本上\n偷偷看你认真模样\n[Chorus]\n想把心意写成歌唱给你\n就算笨拙也没关系"
```

### Lo-Fi 纯音乐

```text
prompt: "Lo-Fi hip hop, chill, Study, relaxing, piano, Jazz guitar, vinyl crackle"
is_instrumental: true
```

### 民谣

```text
prompt: "独立民谣, 叙事, 温暖, 男声独唱, 民谣吉他"
lyrics: "[Verse]\n小镇的夜晚很安静\n星星比城市亮很多\n[Chorus]\n我在这头望着那头\n故乡是回不去的温柔"
```

### 电子 / Synthwave

```text
prompt: "Synthwave, retro, 80s, nostalgic, driving beat, synth bass, female vocal"
lyrics: "[Verse]\n霓虹灯闪烁的夜晚\n车载音响放着老歌\n[Chorus]\n沿着海岸线一路向北\n追逐夕阳下的余晖"
```

### 中国风

```text
prompt: "中国风, 古筝, 笛子, 悠扬, 唯美, 女声"
lyrics: "[Verse]\n烟雨入江南\n山水如墨染\n[Chorus]\n你撑一把油纸伞\n走过青石板"
```

---

## 6. 与 ACE / Suno 的区别

| | MiniMax | ACE | Suno |
|------|------|------|------|
| 风格输入 | 逗号标签 | 逗号标签 (严格) | 自然语言 |
| 歌词标签 | [Verse]/[Chorus] (14 个) | 自定义 | 自然语言 |
| 纯音乐 | is_instrumental: true | (instrumental) lyrics | make_instrumental: true |
| 输出格式 | hex / url (24h) | base64 data URL | CDN URL |
| 同步/异步 | 同步 | 同步 | 异步 |
