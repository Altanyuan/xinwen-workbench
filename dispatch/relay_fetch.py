#!/usr/bin/env python3
"""中继批量取回（Call 1/2）：一次 SSH 完成 读历史 + 认领 claim + 记已读 + 开正在输入。
用法：python3 /opt/chat/relay_fetch.py <agent> [--preclaimed <id> ...]
输出 JSON：
  {"ok": true, "unreplied": [{id,from,text,ts,image?}...], "skipped": [ids],
   "context": [...最近 6 条...], "readmark": <id>|null, "typing": bool}
- unreplied：本次认领到（或 hook 已预认领）的未回用户消息，按 id 升序。
- skipped：已被别人认领且未满 5 分钟的消息（不要回）。
- context：历史最后 6 条，供 worker 生成回复做上下文。
- 若无未回消息：unreplied 为空，不做 readmark/typing，调用方直接退出。
- 认领目录：/opt/chat/claims/muse-box-<id>（与 cron/hook 共用，mkdir 原子，5 分钟过期）。
- 每次调用后调用方必须跑 relay_send.py（即使 replies 为空）来关 typing、删认领。
"""
import json
import os
import shutil
import subprocess
import sys
import time

CLAIM_TTL = 300


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: relay_fetch.py <agent> [--preclaimed <id> ...]"}, ensure_ascii=False))
        return 2
    agent = sys.argv[1]
    preclaimed = set()
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--preclaimed" and i + 1 < len(sys.argv):
            try:
                preclaimed.add(int(sys.argv[i + 1]))
            except ValueError:
                pass
            i += 2
        else:
            i += 1
    hist = "/opt/chat/history/%s.json" % agent
    claims = "/opt/chat/claims"
    helper = ["python3", "/opt/chat/chat-helper.py"]
    try:
        with open(hist, encoding="utf-8") as f:
            msgs = json.load(f)
    except Exception:
        msgs = []
    if not isinstance(msgs, list):
        msgs = []
    # 找出所有未回的用户消息（其后没有任何一条本 agent 的回复）
    unreplied_all = []
    for idx, m in enumerate(msgs):
        if not isinstance(m, dict):
            continue
        if m.get("from") == "user":
            if not any(isinstance(x, dict) and x.get("from") == agent for x in msgs[idx + 1:]):
                unreplied_all.append(m)
    result = {"ok": True, "unreplied": [], "skipped": [],
              "context": msgs[-6:], "readmark": None, "typing": False}
    if not unreplied_all:
        # 无未回消息时顺手清理残留的正在输入（上轮异常退出导致），仍只用这一次 SSH
        try:
            with open("/opt/chat/typing/%s.json" % agent, encoding="utf-8") as f:
                t = json.load(f)
            if isinstance(t, dict) and t.get("typing"):
                subprocess.run(helper + ["typing", agent, "0"], capture_output=True)
                result["typing_cleaned"] = True
        except Exception:
            pass
        print(json.dumps(result, ensure_ascii=False))
        return 0
    os.makedirs(claims, exist_ok=True)
    claimed = []
    for m in unreplied_all:
        uid = m.get("id")
        if not isinstance(uid, int):
            continue
        if uid in preclaimed:
            # hook 已认领，视为自己的
            claimed.append(m)
            continue
        claim = os.path.join(claims, "%s-box-%d" % (agent, uid))
        if os.path.isdir(claim):
            try:
                age = time.time() - os.path.getmtime(claim)
            except OSError:
                age = 9999
            if age <= CLAIM_TTL:
                result["skipped"].append(uid)
                continue
            shutil.rmtree(claim, ignore_errors=True)
        try:
            os.mkdir(claim)
            claimed.append(m)
        except FileExistsError:
            result["skipped"].append(uid)
    result["unreplied"] = claimed
    if claimed:
        last_uid = max(m.get("id") for m in claimed)
        subprocess.run(helper + ["readmark", agent, "agent", str(last_uid)],
                       capture_output=True)
        subprocess.run(helper + ["typing", agent, "1"], capture_output=True)
        result["readmark"] = last_uid
        result["typing"] = True
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
