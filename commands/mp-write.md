---
description: 公众号长文一键成稿：选题→大纲→初稿→爆款 rubric 打分→多轮改写→合规检测→排版，全流程走完。
argument-hint: <主题/选题方向> [--outline-only] [--quality]
---

# /lhg-wechat-article:mp-write —— 公众号长文一键成稿

用户输入在 `$ARGUMENTS` 中：`<主题/选题方向> [--outline-only] [--quality]`。
主题缺省时，先问用户要写什么（给 3 个候选方向让他挑）。

全程按 5 个 skill 的顺序推进：`lhg-mp-topic` → `lhg-mp-outline` → `lhg-mp-draft` → `lhg-mp-rubric` → `lhg-mp-compliance`。

## 流程

### 1. 选题（lhg-mp-topic）
- 用选题 skill 的四维打分（受众痛点 / 时效红利 / 账号调性匹配 / 可写深度）给 3~5 个候选选题打分，选出 Top1。
- 把选定的选题 + 目标读者 + 预估字数写进稿件头部的元信息区（YAML frontmatter：title/topic/audience/words/date）。

### 2. 大纲（lhg-mp-outline）
- 按大纲 skill 输出三级大纲：钩子开头 → 3~5 个论述模块（每模块：论点+论据+案例/金句）→ 收尾行动点。
- 大纲先给用户过一眼（打印出来），确认后再写初稿。`--outline-only` 到此为止，只交付大纲。

### 3. 初稿（lhg-mp-draft）
- 按大纲逐模块写初稿：每模块 300~600 字，段落 ≤ 150 字（手机阅读）。
- 开头 150 字内必须出现钩子（悬念 / 反常识 / 痛点共鸣三选一）；每模块至少 1 个金句（划线句）。
- 初稿存为 `drafts/<日期>-<选题拼音或英文>.md`。

### 4. rubric 打分 + 多轮改写（lhg-mp-rubric）
- 用 rubric（钩子 20 / 结构 20 / 信息密度 20 / 语言 20 / 传播性 20，共 100）给初稿打分，逐项给依据和扣分点。
- 改写轮次：默认 2 轮；`--quality` 3 轮。每轮只改 rubric 扣分最多的 2 项，改完重新打分。
- 停止条件：总分 ≥ 80，或轮次用完（取最高分版）。每轮保留版本（`v1/v2/v3` 后缀）。

### 5. 合规检测（lhg-mp-compliance + 脚本）
- 先跑确定性脚本（必做）：
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit/mp_audit.py --target drafts/<本次稿件> --format text
```
- blocker（涉政敏感词 / 医疗断言 / 金融承诺）必须清零：改写或删除，不许为清零改脚本。
- warning（AI 味信号 / 标题过长 / 标题党）逐条处理：能改就改，改不了写进"已知风险"清单。
- 再按合规 skill 做人工复核：洗稿风险、事实核查、引用来源。

### 6. 排版交付
- 输出发布版 Markdown：标题（≤30 字）、摘要（≤120 字，写进 frontmatter 的 `excerpt`）、正文分段、小标题加粗、金句单独成段。
- 打印最终 rubric 得分 + 合规报告摘要，告诉用户：建议发布时间、封面图建议、文末引导关注话术（1 句）。

## 注意事项

- 全程中文输出；除非用户要求，不写英文段落。
- 数字、机构名、人名、政策名称必须可核查：不确定的写"（待核实）"标记，不许编。
- 发布动作（复制到公众号后台 / 调用发布工具）**永远由用户亲手做**，本命令只交付排版好的稿件 + 发布 checklist。
