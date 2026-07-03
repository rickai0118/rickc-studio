# ACE-Step 1.5 提示规范

## Tags（逗号分隔标签）

格式：`genre, mood, instruments, vocal_type, effects, BPM, Key`

```
lo-fi house, late-night, intimate, melancholy,
Rhodes piano, vinyl crackle, sub-bass, 4-on-the-floor kick,
female vocals, analog warmth, 115 bpm, E minor
```

规则：
- **单一流派**：最多 1 个主导流派，多流派导致声部分层
- BPM 与流派必须匹配（查速查表）
- Key 只写一个，不支持段落转调

## Lyrics（结构标记）

```
[Intro]
[vinyl crackle, sub-bass pulse]

[Verse 1]
歌词内容...

[Pre-Chorus 1]
...

[Chorus 1]
...

[Bridge]
...

[Outro]
...

[End]
```

规则：
- 必须用 `[End]` 收尾
- 结构指令写在 `[...]` 内，歌词写在下方
- 支持拟声词 / 无意义音节 (nae, la, solune...)
- 中文 / 英文 / 日文均可，混合使用零吞字

## Performance Hints（演出指令）

≤ 3 行，描述人声处理 + 节奏感：

```
Soft intimate female vocal, light reverb.
Steady house kick, vinyl warmth.
```

## 常见错误

| 错误 | 症状 | 修复 |
|------|------|------|
| 3+ 流派标签 | 人声和伴奏不在一个图层 | 单流派主导 |
| BPM 与流派冲突 | 节奏骨架和情绪割裂 | 查速查表 |
| 多 Key 转调 | Bridge 段音高迷路 | 锁死一个 Key |
| 演出指令 > 5 行 | 混音细节有但旋律苍白 | 精简到 3 行 |
| Suno 方言 `[Energy: High]` | 输出乱套 | 全部清除 |
