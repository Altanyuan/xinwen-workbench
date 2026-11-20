#!/bin/bash
# 轮询领单脚本（骨架）：每 30 分钟跑一次，只领派给自己的 queued 单
# 用法：把 muse-2 改成你自己的子 Muse 名，放进定时任务每 30 分钟跑一趟
# 领单后在这里接你的执行步骤，完成后把结果写进对应工单的 result.md
POOL=/opt/shared/agent-bus/tasks
ME="muse-2"

for d in "$POOL"/*/; do
  [ -f "$d/task.md" ] || continue
  grep -q "指派给：$ME" "$d/task.md" || continue
  grep -q "状态：queued" "$d/task.md" || continue
  sed -i "s/状态：queued/状态：执行中（$ME 已领）/" "$d/task.md"
  # ---- 在这里执行任务，完成后写 $d/result.md ----
  # 示例：echo "结果写在这里" > "$d/result.md"
  echo "状态：done" >> "$d/task.md"
done
