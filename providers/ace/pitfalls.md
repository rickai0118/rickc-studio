# 🕳️ ACE 避坑指南

实战累计踩坑记录。每次翻车自动追加。

---

## 坑 #1：多流派标签 → 声部分层飘移

**症状**：人声和伴奏仿佛不在同一图层，像两个独立的音频叠在一起。

**根因**：ACE 的 LM 策划器收到 3+ 流派标签（如 `lo-fi vapor-dance + liquid garage + late-night house`），会为每个流派生成独立的策划方案，DiT 执行器无法合并为统一输出。

**修复**：标签锁定单一流派主导（`lo-fi house`），其余用 mood + instrument 标签补充氛围。

**案例**：ghosts_in_the_machine v1

---

## 坑 #2：BPM 与流派预期严重偏离

**症状**：节奏骨架紧张，但流派情绪松散，听完感觉"着急又不舒服"。

**根因**：从 Suno prompt 照搬的 142 BPM，实际 lo-fi 安全区间是 60–100 BPM。142 更接近 drum and bass / liquid DnB。

**修复**：降 BPM 到 115（lo-fi 氛围 + house 节奏的折中点）。查速查表验证流派期望区间。

**案例**：ghosts_in_the_machine v1 (142 → 115)

---

## 坑 #3：多调性跳跃 → Bridge 音高迷路

**症状**：副歌正常，Bridge 开始"走音"——旋律在 E minor 和 G major 之间漂泊。

**根因**：ACE 不支持段落间转调。`Key: E minor / G major` 被 split 为两个独立指令，互相干扰。

**修复**：锁死一个 Key（`E minor`），用和弦变化替代调性变化。

**案例**：ghosts_in_the_machine v1 (E minor / G major / Em7b5 → E minor 固定)

---

## 坑 #4：演出指令过重 → 旋律苍白的"混音课作业"

**症状**：混音细节满分（reverb、delay、automation、EQ 全部到位），但旋律记不住，听完就忘。

**根因**：15 行 perfromance hints 占用了 LM 策划器的注意力预算，它把精力花在"如何制作"，而不是"做什么歌"。

**修复**：精简到 ≤ 3 行，只描述最核心的人声处理 + 节奏感。

```diff
- [15 行：reverb type, delay time, compression ratio, EQ curve, automation...]
+ Soft intimate female vocal, light reverb. Steady house kick, vinyl warmth.
```

**案例**：ghosts_in_the_machine v1 → v2

---

## 坑 #5：Suno 方言不兼容

**症状**：`[Energy: High]`、`*aggressive*`、`[Build-up, tension rising]` 等 Suno 专属标记被 ACE 当作歌词念出来或直接乱套。

**根因**：ACE 和 Suno 是完全不同的架构（LM+DiT vs 自回归扩散），Suno 的训练数据里有这些标记，ACE 没有。

**修复**：翻译为 ACE 原生格式：

| Suno 标记 | ACE 替换 |
|-----------|----------|
| `[Energy: High]` | `high energy, driving` 进 tags |
| `*whisper*` | 直接写拟声词 |
| `[Build-up]` | `crescendo, tension build` 进 perf hints |

---

## 防坑总则

1. **一流派原则** — 标签不超过 1 个流派
2. **BPM 不照搬** — 从 Suno 搬来的必查速查表
3. **Key 只写一个** — 想转调用和弦变，不动 Key
4. **指令 3 行上限** — perf hints 越短，旋律越好
5. **清除所有方言** — `[Energy]`、`*...*`、`(whisper)` 全删
6. **先简后繁** — 第一版只用 tags + lyrics，能跑了再加 perf hints
