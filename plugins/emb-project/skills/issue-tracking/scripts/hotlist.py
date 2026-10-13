#!/usr/bin/env python3
"""个人热点：把某人最近点了“关注”的 open issue 排到前面，再慢慢降温（method.md 第 10.1 节）。

只读：通过 GitHub GraphQL 读取 open issue 的关注表情、评论、交叉引用、提交引用和指派事件，打分后输出到标准输出。
不读 issue 的 updatedAt：批量改标签、改模板会刷新它，排序因此失真。

打分：每个事件按“权重 × 0.5^(距今天数 / 半衰期)”累加。

主信号是“关注”：本人在 issue 正文上点的表情（默认 👀，--focus-reaction 可改），权重 10，
半衰期 7 天，看 60 天内的。取消后再点一次，时间就更新为新的，issue 重新升温。

其余活动是次要信号，看 14 天内的，半衰期 3 天：

  事件                                   权重
  本人新开 issue                           3
  本人评论                                 3
  他人评论中 @本人                         2
  他人评论                                 1
  本人的 PR 引用该 issue                   4
  他人的 PR 引用该 issue                   1
  本人的提交引用该 issue                   2
  指派给本人                               2
  当前指派给本人（不衰减）                 1

本人相关得分 > 0 的进入“我的热点”；其余按总分取前几名列为“团队热点”，供参考。

用法：
  python3 hotlist.py --repo OWNER/NAME [--user LOGIN] [--days 14] [--half-life 3] [--top 10] [--json]
  python3 hotlist.py --input issues.json --user LOGIN --now 2026-01-01T00:00:00Z   # 离线，用于自检

鉴权：依次使用环境变量 GITHUB_TOKEN、GH_TOKEN、`gh auth token` 的输出。只用 Python 标准库。
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.request

FOCUS_WEIGHT = 10
WEIGHTS = {
    "opened": 3,
    "comment_self": 3,
    "mention": 2,
    "comment_other": 1,
    "pr_self": 4,
    "pr_other": 1,
    "commit_self": 2,
    "assigned": 2,
}
ASSIGNEE_BONUS = 1
SELF_KINDS = {"focus", "opened", "comment_self", "mention", "pr_self", "commit_self", "assigned"}
LABELS = {
    "focus": "关注",
    "opened": "新开",
    "comment_self": "评论",
    "mention": "@你",
    "comment_other": "{who} 评论",
    "pr_self": "PR #{ref}",
    "pr_other": "{who} 的 PR #{ref}",
    "commit_self": "提交 {ref}",
    "assigned": "指派给你",
}

QUERY = """
query($owner: String!, $name: String!, $after: String, $since: DateTime!,
      $reaction: ReactionContent!) {
  viewer { login }
  repository(owner: $owner, name: $name) {
    issues(states: OPEN, first: 50, after: $after, orderBy: {field: UPDATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title url createdAt
        author { login }
        assignees(first: 10) { nodes { login } }
        reactions(content: $reaction, last: 50) { nodes { createdAt user { login } } }
        comments(last: 50) { nodes { createdAt body author { login } } }
        timelineItems(last: 50, since: $since,
                      itemTypes: [CROSS_REFERENCED_EVENT, REFERENCED_EVENT, ASSIGNED_EVENT]) {
          nodes {
            __typename
            ... on CrossReferencedEvent {
              createdAt
              source { __typename ... on PullRequest { number author { login } } }
            }
            ... on ReferencedEvent { createdAt actor { login } commit { abbreviatedOid } }
            ... on AssignedEvent { createdAt assignee { ... on User { login } } }
          }
        }
      }
    }
  }
}
"""


def parse_time(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def token():
    for key in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(key):
            return os.environ[key]
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit("FAIL 没有 GitHub 凭据：设置 GITHUB_TOKEN，或先 gh auth login")


def fetch(repo, since, reaction):
    owner, name = repo.split("/", 1)
    tok, after, issues, viewer = token(), None, [], None
    while True:
        body = json.dumps({"query": QUERY, "variables": {
            "owner": owner, "name": name, "after": after, "since": since.isoformat(),
            "reaction": reaction}})
        req = urllib.request.Request("https://api.github.com/graphql", data=body.encode(),
                                     headers={"Authorization": f"bearer {tok}",
                                              "Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            data = json.load(r)
        if data.get("errors"):
            sys.exit(f"FAIL GraphQL：{data['errors'][0].get('message')}")
        viewer = data["data"]["viewer"]["login"]
        page = data["data"]["repository"]["issues"]
        issues += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return viewer, issues
        after = page["pageInfo"]["endCursor"]


def login(node):
    return ((node or {}).get("login") or "").lower()


def events(issue, user):
    """把一个 issue 的原始数据转成 (时间, 类型, 说明参数) 列表。"""
    out = []
    for r in (issue.get("reactions") or {}).get("nodes", []):
        if login(r.get("user")) == user:
            out.append((r["createdAt"], "focus", {}))
    if login(issue.get("author")) == user:
        out.append((issue["createdAt"], "opened", {}))
    mention = re.compile(rf"@{re.escape(user)}\b", re.I)
    for c in issue["comments"]["nodes"]:
        who = login(c.get("author"))
        if who == user:
            out.append((c["createdAt"], "comment_self", {}))
        elif mention.search(c.get("body") or ""):
            out.append((c["createdAt"], "mention", {"who": who}))
        else:
            out.append((c["createdAt"], "comment_other", {"who": who}))
    for e in issue["timelineItems"]["nodes"]:
        kind = e["__typename"]
        if kind == "CrossReferencedEvent" and e["source"]["__typename"] == "PullRequest":
            who = login(e["source"].get("author"))
            out.append((e["createdAt"], "pr_self" if who == user else "pr_other",
                        {"who": who, "ref": e["source"]["number"]}))
        elif kind == "ReferencedEvent" and e.get("commit") and login(e.get("actor")) == user:
            out.append((e["createdAt"], "commit_self", {"ref": e["commit"]["abbreviatedOid"]}))
        elif kind == "AssignedEvent" and login(e.get("assignee")) == user:
            out.append((e["createdAt"], "assigned", {}))
    return out


def score(issue, user, now, cfg):
    mine = total = 0.0
    recent = []
    for when, kind, args in events(issue, user):
        age = (now - parse_time(when)).total_seconds() / 86400
        if kind == "focus":
            weight, window, half = FOCUS_WEIGHT, cfg["focus_days"], cfg["focus_half_life"]
        else:
            weight, window, half = WEIGHTS[kind], cfg["days"], cfg["half_life"]
        if age < 0 or age > window:
            continue
        pts = weight * 0.5 ** (age / half)
        total += pts
        if kind in SELF_KINDS:
            mine += pts
        recent.append((when, LABELS[kind].format(**args)))
    if any(login(a) == user for a in issue["assignees"]["nodes"]):
        mine += ASSIGNEE_BONUS
        total += ASSIGNEE_BONUS
    recent.sort(reverse=True)
    return {
        "number": issue["number"], "title": issue["title"], "url": issue.get("url", ""),
        "score": round(total, 1), "mine": round(mine, 1),
        "assigned": any(login(a) == user for a in issue["assignees"]["nodes"]),
        "recent": [f"{w[5:10]} {what}" for w, what in recent[:3]],
    }


DEFAULTS = {"days": 14, "half_life": 3.0, "focus_days": 60, "focus_half_life": 7.0}


def rank(issues, user, now, top=10, **cfg):
    cfg = {**DEFAULTS, **cfg}
    rows = [score(i, user, now, cfg) for i in issues]
    rows.sort(key=lambda r: (-r["score"], -r["number"]))
    mine = [r for r in rows if r["mine"] > 0][:top]
    team = [r for r in rows if r["mine"] == 0 and r["score"] > 0][:max(3, top // 2)]
    return mine, team


def render(mine, team, user, now):
    lines = [f"# {user} 的近期热点（{now:%Y-%m-%d %H:%M} UTC）", "",
             "| # | issue | 分 | 最近动作 |", "| --- | --- | --- | --- |"]
    for i, r in enumerate(mine, 1):
        tag = "（指派给你）" if r["assigned"] else ""
        lines.append(f"| {i} | #{r['number']} {r['title']}{tag} | {r['score']} | "
                     f"{'；'.join(r['recent']) or '—'} |")
    if team:
        lines += ["", "## 团队热点（与你无关，供参考）", ""]
        lines += [f"- #{r['number']} {r['title']}（{r['score']}；{'；'.join(r['recent'])}）"
                  for r in team]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", help="OWNER/NAME")
    ap.add_argument("--user", help="GitHub 登录名；默认取凭据对应的用户")
    ap.add_argument("--days", type=int, default=DEFAULTS["days"], help="活动的计分窗口（天）")
    ap.add_argument("--half-life", type=float, default=DEFAULTS["half_life"], help="活动的半衰期（天）")
    ap.add_argument("--focus-days", type=int, default=DEFAULTS["focus_days"], help="关注的计分窗口（天）")
    ap.add_argument("--focus-half-life", type=float, default=DEFAULTS["focus_half_life"],
                    help="关注的半衰期（天）")
    ap.add_argument("--focus-reaction", default="EYES",
                    help="表示关注的表情（GraphQL ReactionContent，如 EYES、ROCKET、HEART）")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--json", action="store_true", help="输出 JSON 而不是 Markdown")
    ap.add_argument("--input", help="离线：读取已保存的 issue 列表（GraphQL nodes 格式）")
    ap.add_argument("--now", help="离线：指定当前时间（ISO 8601）")
    a = ap.parse_args()

    now = parse_time(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    if a.input:
        if not a.user:
            sys.exit("FAIL 离线模式需要 --user")
        with open(a.input, encoding="utf-8") as f:
            issues, user = json.load(f), a.user
    elif a.repo:
        viewer, issues = fetch(a.repo, now - dt.timedelta(days=a.days), a.focus_reaction.upper())
        user = a.user or viewer
    else:
        sys.exit("FAIL 需要 --repo 或 --input")

    user = user.lower()
    mine, team = rank(issues, user, now, a.top, days=a.days, half_life=a.half_life,
                      focus_days=a.focus_days, focus_half_life=a.focus_half_life)
    if a.json:
        json.dump({"user": user, "generated_at": now.isoformat(), "mine": mine, "team": team},
                  sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        print(render(mine, team, user, now))


if __name__ == "__main__":
    main()
