#!/usr/bin/env python3
"""中继批量发送（Call 2/2）：一次 SSH 完成 发回复 + 关正在输入 + 删认领 + 读回核对。
用法：python3 /opt/chat/relay_send.py <agent> <payload_b64>
payload（JSON，先 base64，防 shell 截断）：
  {"replies": [{"text": "..."}, ...], "claims": [<id>, ...], "dry_run": false}
- replies：要发的回复（按顺序，每条一次 append）；空列表表示只清理不发。
- claims：要删的认领消息 id（只删本次回过的；先删 ts 文件再 rmdir，
  兼容 hook 写的含 ts 目录与 cron 的空目录）。
- dry_run：true 时不发消息，只关 typing、删 claim、读回（供自测）。
- 回复文本经 base64 传进本脚本、再以 argv 列表调 helper，全程不走 shell，
  不怕双引号、换行与加号；长回复也直接 append，不再走 stream 分块。
输出 JSON：
  {"ok": true, "sent": [{"id": N}...], "typing": false,
   "claims_deleted": [ids], "last": {...}, "verify_ok": bool}
- verify_ok：发了消息时，逐条核对 sent 的 id 与文本都在历史里；没发时恒为 true。
"""
import base64
import json
import os
import subprocess
import sys

HELPER = ["python3", "/opt/chat/chat-helper.py"]


def run_helper(args):
    r = subprocess.run(HELPER + args, capture_output=True, text=True)
    return r.stdout.strip(), r.returncode


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"ok": False, "error": "usage: relay_send.py <agent> <payload_b64>"}, ensure_ascii=False))
        return 2
    agent = sys.argv[1]
    hist = "/opt/chat/history/%s.json" % agent
    claims = "/opt/chat/claims"
    try:
        payload = json.loads(base64.b64decode(sys.argv[2]).decode("utf-8"))
    except Exception as e:
        print(json.dumps({"ok": False, "error": "bad payload: %s" % e}, ensure_ascii=False))
        return 1
    if not isinstance(payload, dict):
        print(json.dumps({"ok": False, "error": "payload must be an object"}, ensure_ascii=False))
        return 1
    replies = payload.get("replies") or []
    claim_ids = payload.get("claims") or []
    dry_run = bool(payload.get("dry_run"))
    result = {"ok": True, "sent": [], "typing": None,
              "claims_deleted": [], "last": None, "verify_ok": False}
    # 1. 发回复（dry_run 时跳过）
    if not dry_run:
        for rep in replies:
            if not isinstance(rep, dict):
                continue
            text = rep.get("text", "")
            if not text:
                continue
            out, _rc = run_helper(["append", agent, agent, text])
            try:
                d = json.loads(out)
                if d.get("ok") and d.get("id") is not None:
                    result["sent"].append({"id": d["id"], "text": text})
            except Exception:
                pass
    # 2. 关正在输入
    out, _rc = run_helper(["typing", agent, "0"])
    try:
        d = json.loads(out)
        result["typing"] = d.get("typing")
    except Exception:
        result["typing"] = False
    # 3. 删认领（只删指定的）
    for uid in claim_ids:
        if not isinstance(uid, int):
            continue
        claim = os.path.join(claims, "%s-box-%d" % (agent, uid))
        try:
            ts = os.path.join(claim, "ts")
            if os.path.exists(ts):
                os.remove(ts)
            os.rmdir(claim)
            result["claims_deleted"].append(uid)
        except Exception:
            pass
    # 4. 读回核对：逐条核对 sent 的 id 与文本都在历史里
    try:
        with open(hist, encoding="utf-8") as f:
            msgs = json.load(f)
    except Exception:
        msgs = []
    if not isinstance(msgs, list):
        msgs = []
    if msgs:
        result["last"] = msgs[-1]
    if result["sent"]:
        by_id = {}
        for m in msgs:
            if isinstance(m, dict) and isinstance(m.get("id"), int):
                by_id[m["id"]] = m
        ok = True
        for s in result["sent"]:
            m = by_id.get(s["id"])
            if m is None or m.get("text") != s["text"] or m.get("from") != agent:
                ok = False
                break
        result["verify_ok"] = ok
    else:
        result["verify_ok"] = True
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
