# 多 Muse 拆单（dispatch/）

一个主 Muse 拆单、多个子 Muse 领单、人只跟主 Muse 说话的最小可跑核心。配套文章是公众号「地铁里的AI探员」的续篇《5 个 Muse 养起来了，活还是派不出去…》，工作台的「指挥中心」与「工作台原理」页讲的是同一套东西。

## 四个文件

| 文件 | 干什么 |
|---|---|
| `task-template.md` | 工单模板：一单一个目录，里面放 `task.md`，写清指派给谁、任务、验收标准、状态（queued → 执行中 → done），做完把结果写进 `result.md` |
| `poll-claim.sh` | 子 Muse 的轮询领单脚本（骨架）：每 30 分钟跑一趟，只领派给自己且状态为 queued 的单；领单后把状态改成「执行中」，做完写 `result.md` |
| `relay_fetch.py` | 中继取回（Call 1/2）：主 Muse 侧一次 SSH 完成读历史＋认领未回消息＋记已读＋开「正在输入」 |
| `relay_send.py` | 中继发送（Call 2/2）：主 Muse 侧一次 SSH 完成发回复＋关「正在输入」＋删认领＋读回核对 |

## 默认假设的路径

- 工单池：`/opt/shared/agent-bus/tasks`（一单一个子目录）
- 聊天记录：`/opt/chat/history/<agent>.json`
- 认领目录：`/opt/chat/claims`（`mkdir` 原子认领，5 分钟过期）
- 正在输入：`/opt/chat/typing`

按自己环境改这些路径就能用；`poll-claim.sh` 里把 `muse-2` 改成你自己的子 Muse 名，放进定时任务每 30 分钟跑一趟。

## 依赖提醒

`relay_fetch.py` 与 `relay_send.py` 会调 `/opt/chat/chat-helper.py`（盒子聊天系统的 helper，负责读历史、写已读、开关「正在输入」），**这个 helper 不在这个仓库里**。没有它，两个中继脚本跑不起来；`task-template.md` 与 `poll-claim.sh` 不依赖它，单拿走也能用。

`poll-claim.sh` 是骨架：领单后的「执行任务」那一步留了空位，接你自己的执行步骤。这是最小可跑核心，不是开箱即用的部署包。
