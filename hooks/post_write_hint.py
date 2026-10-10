#!/usr/bin/env python3
"""lhg-wechat-article 硬门②（提醒级，不拦截）：写/改 Markdown 稿件后跑合规审计，有问题只提醒。

触发：PostToolUse / Write|Edit。只处理 .md 文件；永远 exit 0、不拦截写入。

逃生方式：LHG_MP_HOOKS_OFF=1（环境变量）可关闭本提醒；
或 /plugin disable lhg-wechat-article 停用整个插件。
零第三方依赖。
"""

import json
import os
import subprocess
import sys


def main() -> int:
    if os.environ.get("LHG_MP_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # 输入解析失败：fail-open

    tool_input = payload.get("tool_input", {}) or {}
    path = tool_input.get("file_path", "") or ""
    if not path.lower().endswith(".md"):
        return 0  # 非 Markdown：快速放行

    # 只审计稿件目录下的文件，避免扫到 README 等
    norm = path.replace("\\", "/")
    if "/drafts/" not in norm and "/fixtures/" not in norm:
        return 0

    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = os.path.join(plugin_root, "scripts", "audit", "mp_audit.py")
    if not os.path.isfile(script):
        return 0  # 审计脚本缺失：fail-open

    target = os.path.dirname(os.path.abspath(path)) or "."
    try:
        r = subprocess.run(
            [sys.executable, script, "--target", target, "--format", "json"],
            capture_output=True, text=True, timeout=25)
        data = json.loads(r.stdout)
    except Exception:
        return 0  # 脚本出错：fail-open，不骚扰用户

    s = data.get("summary", {})
    b, w = s.get("blocker", 0), s.get("warning", 0)
    if b == 0 and w == 0:
        return 0

    out = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                "【lhg-wechat-article】稿件合规提醒：%s 本次审计发现 "
                "blocker=%d warning=%d。blocker（如涉政/医疗断言/收益承诺）"
                "必须清零才能发布；warning 建议顺手修。跑 "
                "`/lhg-wechat-article:mp-audit` 看明细。" % (path, b, w)),
        }
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
