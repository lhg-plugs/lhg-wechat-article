<!-- About 简介（推送后填写到仓库 About 栏）：
公众号写作专家：选题到排版一气呵成 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-wechat-article
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, wechat, writing, chinese-nlp -->

# lhg-wechat-article：公众号写作专家

> **一句话介绍**：给 AI 写作助手装上"公众号长文流水线"——选题打分、大纲施工图、初稿写作、爆款 rubric 多轮改写、24 条确定性合规审计，小白也能产出可发布的公众号长文。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-wechat-article
> /plugin install lhg-wechat-article@lhg-plugs
> ```

## 它是什么

`lhg-wechat-article` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **3 个命令**（小白入口）：`mp-write` 选题→排版一键成稿，`mp-outline` 只做选题大纲，`mp-audit` 发文前自检
- **5 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：选题、大纲、初稿写作、rubric 打分改写、合规自查
- **3 个专家 agent**：初稿写手、改稿编辑、合规审查
- **2 个硬门 hooks**：发布命令前合规拦截、写稿后自动提醒（均可一键豁免）
- **24 条确定性审计规则**：错别字 / 违禁词 / AI 味信号 / 标题 / 结构，纯 Python、零第三方依赖，10 秒出结果

## 3 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-wechat-article:mp-write` | 选题→大纲→初稿→rubric 打分改写→合规检测→排版，全流程 | `/lhg-wechat-article:mp-write "AI 副业"` |
| `/lhg-wechat-article:mp-outline` | 只做选题+大纲（打分选 Top1，输出三级大纲） | `/lhg-wechat-article:mp-outline "职场"` |
| `/lhg-wechat-article:mp-audit` | 发文前自检（脚本 + 人工复核清单，分级报告） | `/lhg-wechat-article:mp-audit drafts/2026-10-11-ai.md` |

## 质量分档

- **默认 = 极速档**：rubric 改写 2 轮，确定性审计必跑。速度快、token 省，适合日更。
- **`--quality` = 品质档**：在 `mp-write` 后加 `--quality`，rubric 改写 3 轮 + 更严的合规复核。**诚实说明**：品质档 token 消耗约为极速档的数倍，请确认接受再使用。

## 自查说明

自查 = 确定性脚本（机器）+ 人工复核清单（人）：

1. 先跑 `scripts/audit/mp_audit.py`（24 条规则），零 LLM 成本；
2. 发现分三级：**blocker**（涉政/医疗断言/收益承诺，必须清零，发布前 hook 会拦截）、**warning**（错别字/AI 味/标题问题，修或写已知风险理由）、**nit**（顺手修）；
3. 再按 `lhg-mp-compliance` skill 的人工复核过一遍脚本抓不到的（事实核查、洗稿风险、引用规范、敏感题材声明、标题党兑现）。

blocker 清零才建议发布；为清零改规则算作弊，不许。

## 目录结构

```
lhg-wechat-article/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 3 个命令：mp-write / mp-outline / mp-audit
├── skills/                  # 5 个平台中立 skill（lhg-mp-topic/outline/draft/rubric/compliance）
├── agents/                  # 3 个专家 agent（mp-writer / mp-editor / mp-reviewer）
├── hooks/                   # 2 个硬门（发布前合规拦截 / 写稿后提醒）+ 豁免说明
├── scripts/audit/           # 24 条确定性合规审计规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你想写公众号但不知道写什么、从哪下笔时 → `/lhg-wechat-article:mp-write` 一句话开工
- 你有选题但大纲总写散、写崩时 → `/lhg-wechat-article:mp-outline` 先出施工图
- 稿子写完了、发之前心里没底时 → `/lhg-wechat-article:mp-audit` 跑一遍分级自检
- 你带团队写稿，想立一套"发文前必须过"的纪律时 → 它的 hooks 硬门开箱即用

**什么时候不用：**

- 你要的是短平快的微头条/朋友圈文案 → 本插件为 2000 字以上长文设计，短文案用它是大炮打蚊子
- 你希望 AI 直接替你点"发布" → 本插件永远不自动发布，发布必须由你亲手完成（这是设计，不是缺功能）
- 你的内容是英文或其他语种 → 错别字表、违禁词库、rubric 全部按中文公众号生态编写

## 风险提示（诚实说明）

1. **平台原创/洗稿判定**：微信的原创检测是黑盒。本插件的合规 skill 只能做"人工洗稿风险评估"（观点结构对比、找 3 个不同点测试），**不能保证**过平台原创。引用他人独家案例/数据必须注明来源；高风险题材建议先发原创声明。
2. **AI 味**：脚本的 AI 味规则是启发式（八股词计数、句长等），能抓明显的，不能抓"读着像 AI 但词表没覆盖"的。最终质检是"朗读测试"——大声读一遍，拗口就重写。深度去 AI 味不在本插件范围内。
3. **发布接口稳定性**：本插件**不内置**自动发布功能。`publisher-wechatsync` 类工具（见 ATTRIBUTION）的接口稳定性取决于第三方项目与微信侧变更；发布动作请走你信任的官方/半官方渠道，本插件只交付排版好的稿件 + 发布 checklist。
4. **词库时效性**：违禁词库是 2026-10 快照，平台规则会变。发现漏报/误报请按 skill 里的反馈渠道提 issue，词库随版本更新。

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、24 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-wechat-article/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 视频号：搜「刘洪光实名上网」
- 微信：lhgsmsw
