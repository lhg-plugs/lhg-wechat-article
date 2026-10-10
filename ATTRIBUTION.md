# 灵感来源与致谢（Attribution）

本插件的**方法论灵感**来自以下优秀的开源项目，**所有实现代码、检测规则与文案均为原创**，未复制任何第三方的原文案与代码。

| 项目 | 作者 | 许可 | 链接 | 借鉴了什么思路 |
|---|---|---|---|---|
| claude-writing-skills | xiaomoBoy | MIT（2026-10-11 经 GitHub API 核实：34 stars） | https://github.com/xiaomoBoy/claude-writing-skills | 「research → 打分 → 改写 → 发布」全链路流水线思想；本插件 `mp-write` 命令的五段式流程与 rubric 打分改写循环受其 `article-optimizer` / `publisher-wechatsync` 启发，**流程细节与文案均为原创** |
| 中文审校方法论 | 中文写作社区通用实践 | 通用方法论（无特定出处） | — | 「错别字表 + 敏感词表 + 人工复核清单」三层合规思想；本插件 24 条审计规则的词表与分级均为自建 |

## 声明

1. **借鉴思路，实现与文案均为原创**：以上项目的具体文案、规则原文、代码实现均未被复制。本插件的 skill 方法论文案、审计规则词表、命令流程均为独立撰写。
2. **许可合规**：xiaomoBoy/claude-writing-skills 为 MIT 许可，允许在保留声明的前提下进行思路借鉴与二次创作。本文件即为保留声明的一部分。
3. **商标与归属**：各项目名称与作者署名归其各自所有者所有。

## 本插件自身的许可

本插件原创部分采用 MIT 许可（见 `LICENSE` 文件），版权所有：刘洪光（https://github.com/lhg-skills）。
