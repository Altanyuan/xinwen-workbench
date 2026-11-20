# 我的个人工作台

一个单文件 Python 工作台：零依赖，只用标准库。每天打开它，看新闻解读、天气、金价、粉丝、日历，顺手记事、管找工作、跟几个 AI 助手聊天。

这是作者自用工作台的脱敏开源版。原版跑在一台 24 小时开机的家用小电脑（玩客云）上，配几个 Muse 助手轮流干活；这个版本把账号、口令、持仓、求职计划等个人信息全部抽掉，换成示例配置，照着改就能跑自己的。

## 它能干什么

- **新闻解读**：按「天下 / 程序员职业 / 家庭」分组的 18 个板块，读 `data.json` 里的简报展示（简报本身用别的脚本采集，这个仓库只负责展示；`data.sample.json` 里有格式示例）。
- **天气**：和风天气优先（需自己申请免费 key），open-meteo 其次，wttr.in 兜底；10 分钟缓存，失败保留上次的好数据。
- **金价**：上期所沪金连续行情，60 秒刷新；填了持仓克数和均价后显示浮亏估算和提醒位。
- **粉丝管理**：读本地 sqlite 粉丝库显示关注数；粉丝系统本身是独立应用，这里只读数。
- **Agent 聊天**：跟几个 AI 助手聊天的入口页，聊天记录存在本地 `chat/` 目录的 JSON 文件里。
- **指挥中心 / 工作台原理**：`command-center/` 与 `principle/` 里的静态页，讲整套东西怎么转。
- **找工作**：每周计划、面试准备、投递跟踪、权益与材料四页；数据默认是示例，写自己的 `job-plan.json` 就能用。
- **时光、日历、随手记、下载统计、系统状态**：日历带农历、节气、节假日；下载统计按 `DOWNLOADS` 配置读计数文件。

## 快速开始

```bash
python3 app.py 18080
```

打开 http://127.0.0.1:18080 ，默认口令是 `changeme`，**首次打开先去 `/change-password` 改掉**，或启动前设环境变量：

```bash
WB_PASSWORD=你的主口令 WB_WORK_PASSWORD=你的工作口令 python3 app.py 18080
```

工作台只监听 `127.0.0.1`，想从外面访问，自己套一层隧道或反向代理（作者用的是 Tailscale + 零讯隧道）。

## 改成你的之前，先改这 10 个地方

都在 `app.py` 顶部附近，搜关键字就能找到：

| 位置 | 改什么 |
|---|---|
| `PASSWORD` / `WORK_PASSWORD` | 主口令与「工作」栏第二道口令（默认都是 `changeme`，必须改） |
| `CITY_NAME` / `CITY_LAT` / `CITY_LON` | 你的城市与经纬度（默认北京） |
| `HIRED` / `CONTRACT_END` | 入职日与合同到期日（留空则不显示时光卡） |
| `GOLD_HOLD_GRAMS` / `GOLD_AVG_COST` / `GOLD_ALERTS` | 纸黄金持仓克数、均价、提醒价位（默认 0，只显示行情） |
| `CHAT_AGENTS` | 你的 AI 助手名单（主 Agent 一个，子 Agent 若干） |
| `FANS_ACCOUNTS` | 你的公众号账号与粉丝库路径（示例一个） |
| `DOWNLOADS` | 你的产品下载统计（默认空，不显示下载卡） |
| `STATS_DIR` | 粉丝复盘数据源目录（默认空） |
| `DISKS` | 首页系统状态里要看的盘 |
| 和风天气 | 把你的 key 存进 `qweather_key`、专属 API Host 存进 `qweather_host`（两个文件都不会进仓库）；没有 key 也能跑，走 open-meteo |

## 数据文件

| 文件 | 说明 |
|---|---|
| `data.json` | 新闻简报数据（`{"briefs": [...], "news": [...], "rankings": [...]}`），没有就显示为空 |
| `briefs.json` / `notes.json` | 简报存档 / 随手记，没有会自动创建 |
| `job-plan.json` | 找工作数据（`{phases, weekly, interview}`），格式见 `job-plan.sample.json` |
| `auth.json` | 改口令后自动生成（0600），别进仓库 |
| `qweather_key` / `qweather_host` | 和风天气 key 与专属 Host，别进仓库 |
| `chat/` / `agent-bus/` | 聊天记录与子 Agent 状态目录，不存在会自动创建 |

`data.sample.json`、`notes.sample.json`、`job-plan.sample.json` 是格式示例，复制改名去掉 `.sample` 就能用。

## 部署建议

- 找一台常开的机器（旧电脑、迷你主机、NAS 都行），装 Python 3.10+，不用装任何依赖。
- 用 systemd 或 supervisor 托管：`python3 /path/to/app.py 18080`，开机自启。
- 数据备份：定期拷走 `data.json`、`briefs.json`、`notes.json`、`chat/`、`auth.json`，别只放一块盘。
- 只监听本机是故意的安全默认；要远程访问时，先想好怎么做认证和加密，别直接把端口暴露到公网。

## 许可证

GPL-2.0（见 `LICENSE`）。`lunardate.py` 是第三方 GPLv2 代码（LI Daobing，源自 lunar 项目），版权头保留在文件里；其余代码同样以 GPL-2.0 开源。
