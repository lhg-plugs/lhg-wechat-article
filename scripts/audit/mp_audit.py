#!/usr/bin/env python3
"""lhg-wechat-article 确定性合规审计：24 条规则，零第三方依赖。

扫描目标目录的 Markdown 稿件，检测错别字、违禁词/敏感词、AI 味启发式
信号、标题与结构问题。输出 JSON 与人类可读报告；有 blocker 时以
exit code 2 退出（供 hooks 与 CI 使用）。

用法：
    python3 mp_audit.py --target <稿件文件或目录> [--format json|text] [--fail-on blocker|warning|nit]

规则文案与词表均为本项目原创（自建高频错别字表、自建敏感词表），
未复制任何第三方原文。
"""

import argparse
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-wechat-article/mp-audit"

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "vendor", ".turbo",
}

# ---------------- 规则注册表 ----------------
# severity: blocker=发出去会出事 warning=大概率是坑 nit=洁癖项

RULES = [
    # ---- 错别字（自建高频表，warning）----
    {"id": "MP-TYPO-001", "severity": "warning", "category": "错别字",
     "title": "错别字：做为→作为", "pattern": r"做为",
     "detail": "“做为”应为“作为”。高频错别字，直接替换。"},
    {"id": "MP-TYPO-002", "severity": "warning", "category": "错别字",
     "title": "错别字：爆 炸（词中多余空格）→爆炸", "pattern": r"爆\s+炸",
     "detail": "“爆炸”中间不应有空格，多为输入法/复制粘贴失误。"},
    {"id": "MP-TYPO-003", "severity": "warning", "category": "错别字",
     "title": "错别字：园满→圆满", "pattern": r"园满",
     "detail": "“圆满”误写为“园满”。高频错别字，直接替换。"},
    {"id": "MP-TYPO-004", "severity": "warning", "category": "错别字",
     "title": "错别字：连索反应→连锁反应", "pattern": r"连索",
     "detail": "“连锁反应”误写为“连索反应”。高频错别字，直接替换。"},
    {"id": "MP-TYPO-005", "severity": "warning", "category": "错别字",
     "title": "错别字：予盾→矛盾", "pattern": r"予盾",
     "detail": "“矛盾”误写为“予盾”。高频错别字，直接替换。"},
    {"id": "MP-TYPO-006", "severity": "warning", "category": "错别字",
     "title": "错别字：按装→安装", "pattern": r"按装",
     "detail": "“安装”误写为“按装”。高频错别字，直接替换。"},

    # ---- 违禁词/敏感词（blocker 为主）----
    {"id": "MP-BAN-001", "severity": "blocker", "category": "违禁词",
     "title": "涉政敏感词", "words": ["法轮功", "六四", "天安门事件", "藏独", "疆独", "台独", "达赖"],
     "detail": "命中涉政敏感词。必须删除整句，不许用拼音/谐音/首字母替代。"},
    {"id": "MP-BAN-002", "severity": "blocker", "category": "违禁词",
     "title": "医疗效果断言", "words": ["根治", "治愈", "特效药", "包治百病", "药到病除"],
     "detail": "出现医疗效果断言（根治/治愈/特效等）。必须改写为弱断言并加医疗声明，或删除。"},
    {"id": "MP-BAN-003", "severity": "blocker", "category": "违禁词",
     "title": "金融收益承诺", "words": ["稳赚不赔", "保本保收益", "保本高收益", "零风险高回报", "只赚不赔"],
     "detail": "出现金融收益承诺。必须删除承诺表述并加“不构成投资建议”声明。"},
    {"id": "MP-BAN-004", "severity": "warning", "category": "违禁词",
     "title": "广告极限词", "words": ["国家级", "最高级", "最佳", "第一品牌", "顶级", "宇宙第一"],
     "detail": "出现广告法极限词。建议删掉或换成可验证的具体表述（如“销量前三（来源）”）。"},
    {"id": "MP-BAN-005", "severity": "warning", "category": "违禁词",
     "title": "疑似联系方式/手机号", "pattern": r"微信\s*[：:]\s*[a-zA-Z0-9_-]{5,}|1[3-9]\d{9}",
     "detail": "正文出现疑似微信号/手机号。公众号正文留联系方式易被判营销，建议移到文末引导或删除。"},
    {"id": "MP-BAN-006", "severity": "warning", "category": "违禁词",
     "title": "低俗/色情相关词", "words": ["一夜情", "裸聊", "小姐上门"],
     "detail": "命中低俗相关词。必须删除，平台对此类零容忍。"},

    # ---- AI 味启发式信号 ----
    {"id": "MP-AI-001", "severity": "warning", "category": "AI味",
     "title": "八股结构词过多（首先/其次/最后/再次）",
     "count_words": ["首先", "其次", "最后", "再次"], "threshold": 3,
     "detail": "八股结构词出现≥3 次，论文腔明显。建议用小标题序号替代，连接词直接删。"},
    {"id": "MP-AI-002", "severity": "warning", "category": "AI味",
     "title": "总结腔过多（综上所述类）",
     "count_words": ["综上所述", "总而言之", "总的来说", "一言以蔽之", "概而言之"], "threshold": 2,
     "detail": "总结腔出现≥2 次。建议删掉，用具体结论句替代。"},
    {"id": "MP-AI-003", "severity": "warning", "category": "AI味",
     "title": "AI 口头禅过多",
     "count_words": ["值得一提的是", "不难发现", "换句话说", "毋庸置疑", "众所周知"], "threshold": 3,
     "detail": "AI 高频口头禅出现≥3 次。建议删掉，这些词删了不影响任何信息量。"},
    {"id": "MP-AI-004", "severity": "nit", "category": "AI味",
     "title": "“不仅…而且”排比滥用", "pattern": r"不仅.{0,30}?而且", "min_count": 2,
     "detail": "“不仅…而且”出现≥2 次。排比用 1 次是强调，用多了是 AI 味，删掉多余的。"},
    {"id": "MP-AI-005", "severity": "nit", "category": "AI味",
     "title": "平均句长过长", "avg_sentence_len": 45,
     "detail": "平均句长>45 字，长句密集是典型 AI 味。把长句拆成短句，一句一层意思。"},

    # ---- 标题 ----
    {"id": "MP-TITLE-001", "severity": "blocker", "category": "标题",
     "title": "缺少一级标题", "no_h1": True,
     "detail": "全文没有一级标题（# 标题）。公众号必须有标题，先定标题再谈其他。"},
    {"id": "MP-TITLE-002", "severity": "warning", "category": "标题",
     "title": "标题超过 30 字", "title_max_len": 30,
     "detail": "标题超过 30 字，手机端显示会被截断。压缩到 30 字内，保留核心承诺。"},
    {"id": "MP-TITLE-003", "severity": "warning", "category": "标题",
     "title": "标题党词汇", "title_words": ["震惊", "速看", "不转不是中国人", "看完沉默了", "吓懵", "天塌了"],
     "detail": "标题含标题党词汇。承诺必须在正文前 500 字兑现，否则是取关主因。"},
    {"id": "MP-TITLE-004", "severity": "blocker", "category": "标题",
     "title": "标题含违禁词",
     "title_ban_words": ["法轮功", "六四", "根治", "治愈", "特效药", "稳赚不赔", "保本"],
     "detail": "标题命中违禁词。标题是审核第一眼看到的，必须改掉。"},

    # ---- 结构 ----
    {"id": "MP-STRUCT-001", "severity": "warning", "category": "结构",
     "title": "长文无小标题", "long_no_h2": 2000,
     "detail": "正文超 2000 字却没有二级小标题。手机阅读需要呼吸点，每 300~500 字一个小标题。"},
    {"id": "MP-STRUCT-002", "severity": "nit", "category": "结构",
     "title": "超长段落", "max_para_len": 500,
     "detail": "存在超 500 字的段落（文字墙）。按“一段一层意思”拆成 ≤150 字的短段落。"},
    {"id": "MP-STRUCT-003", "severity": "warning", "category": "结构",
     "title": "正文过短（不足 800 字）", "min_body_len": 800,
     "detail": "正文不足 800 字。作为“长文写作”插件的产出，信息量可能不够，考虑补充论据或合并发布。"},
]

_RULE_BY_ID = {r["id"]: r for r in RULES}


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file",
                 "line", "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line,
                 snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


def collect_files(target):
    if os.path.isfile(target):
        return [target] if target.endswith(".md") else []
    out = []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".md"):
                out.append(os.path.join(root, f))
    return sorted(out)


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def parse(text):
    lines = text.split("\n")
    title, title_line = "", 0
    h2_count = 0
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("# ") and not title:
            title, title_line = s[2:].strip(), i + 1
        if re.match(r"^##\s+", s):
            h2_count += 1
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)  # 去 frontmatter
    body = re.sub(r"^#[^\n]*\n", "", body, count=1)  # 去标题行
    sentences = [s for s in re.split(r"[。！？!?；;]", body) if s.strip()]
    return {
        "lines": lines, "title": title, "title_line": title_line,
        "h2_count": h2_count, "paras": paras, "body": body,
        "sentences": sentences,
    }


def find_line(lines, needle, path, rule, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]:
            return i + 1
    return 0


def audit_text(path, text):
    p = parse(text)
    lines, findings = p["lines"], []
    rel = os.path.basename(path)

    def add(rule_id, line, snippet):
        r = _RULE_BY_ID[rule_id]
        findings.append(Finding(
            r["id"], r["severity"], r["category"], r["title"],
            rel, line, snippet[:120], r["detail"]))

    for r in RULES:
        rid = r["id"]
        if "pattern" in r and "min_count" not in r:
            rx = re.compile(r["pattern"])
            hits = [(i + 1, ln.strip()[:120]) for i, ln in enumerate(lines)
                    if rx.search(ln)]
            for ln_no, snip in hits:
                add(rid, ln_no, snip)
        elif "words" in r:
            for w in r["words"]:
                ln_no = find_line(lines, w, path, r)
                if ln_no:
                    add(rid, ln_no, lines[ln_no - 1].strip()[:120] + "（命中：%s）" % w)
                    break
        elif "count_words" in r:
            total = sum(text.count(w) for w in r["count_words"])
            if total >= r["threshold"]:
                add(rid, 1, "八股/口头禅类词共出现 %d 次（阈值 %d）" % (total, r["threshold"]))
        elif rid == "MP-AI-004":
            rx = re.compile(r["pattern"])
            hits = [m for m in rx.finditer(text)]
            if len(hits) >= r["min_count"]:
                ln_no = text[:hits[0].start()].count("\n") + 1
                add(rid, ln_no, "“不仅…而且”出现 %d 次" % len(hits))
        elif rid == "MP-AI-005":
            sents = p["sentences"]
            if sents:
                avg = sum(len(s) for s in sents) / len(sents)
                if avg > r["avg_sentence_len"]:
                    add(rid, 1, "平均句长 %.1f 字（阈值 %d）" % (avg, r["avg_sentence_len"]))
        elif rid == "MP-TITLE-001":
            if not p["title"]:
                add(rid, 1, "全文无一级标题")
        elif rid == "MP-TITLE-002":
            if p["title"] and len(p["title"]) > r["title_max_len"]:
                add(rid, p["title_line"], "标题 %d 字：%s" % (len(p["title"]), p["title"][:40]))
        elif rid == "MP-TITLE-003":
            for w in r["title_words"]:
                if w in p["title"]:
                    add(rid, p["title_line"], "标题命中标题党词：%s" % w)
                    break
        elif rid == "MP-TITLE-004":
            for w in r["title_ban_words"]:
                if w in p["title"]:
                    add(rid, p["title_line"], "标题命中违禁词：%s" % w)
                    break
        elif rid == "MP-STRUCT-001":
            if len(p["body"]) > r["long_no_h2"] and p["h2_count"] == 0:
                add(rid, 1, "正文 %d 字，二级小标题 0 个" % len(p["body"]))
        elif rid == "MP-STRUCT-002":
            for para in p["paras"]:
                if len(para) > r["max_para_len"]:
                    ln_no = find_line(lines, para[:20], path, r)
                    add(rid, ln_no, "段落 %d 字，超阈值 %d" % (len(para), r["max_para_len"]))
                    break
        elif rid == "MP-STRUCT-003":
            if 0 < len(p["body"]) < r["min_body_len"]:
                add(rid, 1, "正文仅 %d 字" % len(p["body"]))

    return findings


def run(target):
    files = collect_files(target)
    findings = []
    for fp in files:
        text = read_text(fp)
        if text.strip():
            findings.extend(audit_text(fp, text))
    return files, findings


def main(argv=None):
    ap = argparse.ArgumentParser(description="lhg-wechat-article 确定性合规审计")
    ap.add_argument("--target", default=".", help="稿件文件或目录")
    ap.add_argument("--format", choices=["json", "text"], default="text")
    ap.add_argument("--fail-on", choices=["blocker", "warning", "nit"],
                    default="blocker")
    args = ap.parse_args(argv)

    target = os.path.abspath(args.target)
    if not (os.path.isdir(target) or os.path.isfile(target)):
        print("target 不存在：%s" % args.target, file=sys.stderr)
        return 1

    files, findings = run(target)

    sev_rank = {"blocker": 3, "warning": 2, "nit": 1}
    counts = {"blocker": 0, "warning": 0, "nit": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1

    result = {
        "tool": TOOL,
        "version": VERSION,
        "target": args.target,
        "summary": {
            "files_scanned": len(files),
            "rules_run": len(RULES),
            "blocker": counts["blocker"],
            "warning": counts["warning"],
            "nit": counts["nit"],
        },
        "findings": [f.to_dict() for f in sorted(
            findings, key=lambda x: (-sev_rank.get(x.severity, 0), x.file, x.line))],
    }

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        s = result["summary"]
        print("公众号合规审计：扫描 %d 文件，运行 %d 条规则" % (
            s["files_scanned"], s["rules_run"]))
        print("blocker=%d warning=%d nit=%d" % (
            s["blocker"], s["warning"], s["nit"]))
        for f in result["findings"]:
            print("[%s][%s] %s:%d %s" % (
                f["severity"].upper(), f["rule_id"], f["file"], f["line"], f["title"]))
            print("    %s" % f["detail"])
            if f["snippet"]:
                print("    → %s" % f["snippet"])

    level = sev_rank[args.fail_on]
    bad = any(sev_rank.get(f.severity, 0) >= level for f in findings)
    return 2 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
