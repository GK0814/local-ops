# 总控台

**Preview / Alpha · 源码预览**

总控台是面向 macOS 的本地服务与批处理任务启动、运行监测工具：把常用项目命令、长期服务和一次性任务集中到本地网页中。后端是 Python 3 标准库单文件实现，前端是无构建、无 CDN 的原生 HTML/CSS/JavaScript，只绑定回环地址。

> 总控台只服务当前 Mac 和当前用户，不是远程运维、多人协作或公网管理面板。它能以当前用户权限执行你保存的命令，请勿通过反向代理、SSH 隧道或端口映射暴露到不受信任的网络。当前仍为 Preview / Alpha 阶段，接口、配置格式和安装方式可能调整；`总控台.app` 是项目内启动器，不是可单独复制的自包含应用。

**📚 文档**：[使用手册](https://github.com/laogou717/local-ops/wiki/使用手册) · [数据与备份](https://github.com/laogou717/local-ops/wiki/数据与备份) · [故障排查](https://github.com/laogou717/local-ops/wiki/故障排查) · [开发者与发布指南](https://github.com/laogou717/local-ops/wiki/开发者与发布指南) · [Wiki 主页](https://github.com/laogou717/local-ops/wiki)

## 亮点

- 每 2 秒查看当前用户本地监听服务的 CPU、内存、运行时长与**启动者溯源**（Codex/Claude 等 AI 助手、VS Code/Cursor 等编辑器、终端或总控台）。
- 保存常用服务与批处理任务，集中启动、停止、重启、查日志与诊断；运行 token + 进程组 + UID 三重校验，不会因端口相同就杀掉外部进程。
- 选择工作区文件夹后只读识别项目启动命令（Node/pnpm、Hexo、Django/FastAPI、Go、Rust、静态站点等），不安装依赖、不执行项目代码。
- 新端口发现与一键加入启动台、全局命令面板 ⌘K、日志中心 ⌘J、Ops 指挥台单一主题（浅色/深色/跟随系统）、拖拽与键盘排序。

## 界面预览

以下截图使用脱敏演示数据，不包含真实用户名、目录、命令或服务信息。

| 启动台 | 服务监控 |
| --- | --- |
| ![Ops 指挥台 · 启动台](docs/screenshots/ops-launchpad.jpg) | ![Ops 指挥台 · 服务监控](docs/screenshots/ops-services.jpg) |

## 快速开始

**要求**：macOS 12 或更高、Python 3.12、支持 ES Modules 的现代浏览器；运行时仅使用 Python 标准库，无需安装任何第三方包。（`VERSION` 是项目版本的唯一权威来源，`Info.plist`、发行包名和发行说明应与它保持一致。）

启动方式有三种，效果相同，按习惯选择：

| 方式 | 操作 | 适用场景 |
| --- | --- | --- |
| 双击应用 | 双击 `总控台.app` | 日常使用。后台运行，无 Terminal 窗口和 Dock 图标 |
| 双击脚本 | 双击 `start.command` | 想在 Terminal 里看实时输出 |
| 命令行 | `python3 server.py [--no-browser] [--preferred-port 9603]` | 调试、脚本化或远程 SSH 启动 |

首次打开互联网下载的 `总控台.app`，右键 → 打开（点「打开」），或执行 `xattr -dr com.apple.quarantine "总控台.app"`，只需一次。这是 macOS 对互联网下载应用的常规隔离提示，不是程序损坏；解压后请保持目录结构完整，不要单独移动 `总控台.app`。

启动后自动打开 `http://127.0.0.1:9600`，被占则尝试 9601–9609。实际地址看顶栏「重启 :9600」按钮，或终端输出 / `~/Library/Logs/总控台/console.log`。

## 使用

左侧导航轨切换「启动台 / 服务监控」，右侧信息栏展示实时动态；所有数据每 2 秒自动刷新，断连时显示横幅提示。

- **启动台**：点「+ 添加服务」选择工作区，自动识别项目并给出候选命令（也可「选择脚本」或手动填写）；卡片大按钮启停（任务是运行/中止），右侧常显复制/日志/诊断/重启/编辑/删除；支持拖拽排序、键盘排序、分区筛选与批量停止。
- **服务监控**：概览卡 + 服务表格；页面打开期间新出现的未管理监听端口会单独提醒，可「加入启动台」（自动识别项目并原子认领进程）、「忽略并隐藏」或「暂时关闭」。
- **日志中心（⌘J）/ 设置中心 / 命令面板（⌘K）**：从导航轨或快捷键进入；命令面板支持全局搜索与全键盘操作。
- 红色按钮会结束进程或删除应用，需要二次确认。顶栏「重启 / 停止」控制的是总控台自身，**不会**停止启动台里已经运行的应用——它们是独立进程组，会继续运行。
- 选择批处理脚本时，总控台只保存脚本的绝对路径和生成的执行命令，不复制或托管脚本内容；脚本移动、改名或删除后任务会失效。

任务退出码约定：自然退出 `0` = 成功，其他非零 = 失败；脚本内用户主动取消请退出 `130`（显示「已取消」）；总控台按钮主动中止显示为「已中止」。此约定只用于 `task`，长期服务仍按普通退出处理。

分区与表格细节、关注进程、基线规则、停止与重启语义等完整说明见 Wiki「[使用手册](https://github.com/laogou717/local-ops/wiki/使用手册)」。

## 安全边界

- 只添加你已检查且信任的命令和工作目录；总控台能以当前用户权限执行保存的 shell 命令。
- 不要将服务绑定到 `0.0.0.0`，不要通过反向代理、SSH 隧道或端口映射对外暴露；不要在共享或不受信任的用户账户中运行。
- 不要把 `~/Library/Application Support/总控台/config.json`、日志或故障截图未经脱敏就上传。
- 本地回环绑定只是第一层边界，不能替代写接口的 Host/Origin/控制令牌防护；发布验收必须执行 [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) 中的安全项。

## 维护说明

总控台由作者个人维护：功能的新增、修改与完善以作者日常使用中的实际需求为准，迭代节奏不定；PR 不承诺审阅或合入。

如果你希望增加功能、修复问题或适配其他平台，欢迎 **Fork 本仓库自行修改**，并在 Discussions 中提交衍生版本说明。经过试用评估后，优秀的衍生版本会收录到下方 [社区衍生版本](#社区衍生版本) 列表推荐给大家；衍生版本由各自作者维护，未经原作者审阅或测试，使用前请自行评估。

## 社区衍生版本

以下衍生版本由社区贡献者各自维护，未经原作者审阅或测试，收录仅作推荐。提交新衍生版本或更新说明，请前往 Discussions。

| 衍生版本 | 说明 | 出处 |
| --- | --- | --- |
| Windows 10/11 适配（双平台运行） | 共享代码 + 平台分支收敛，不新增运行时依赖，含 Windows 专属测试与 CI | PR [#2](https://github.com/laogou717/local-ops/pull/2)（dontpanic1） |
| Windows 11 安全优先移植（Draft） | Job Objects、签名回执、CREATE_SUSPENDED 等更严格的进程所有权模型，含打包体系 | PR [#3](https://github.com/laogou717/local-ops/pull/3)（songconmaisaix31-design） |
| Windows 后端 `server_win.py` | 独立 Windows 后端（纯标准库），复用本仓库前端 | PR [#4](https://github.com/laogou717/local-ops/pull/4)（Hexvork） |
| sysops.py 跨平台抽象层方案 | psutil 唯一新增依赖，macOS 分支零改动，作者已在日常使用 | [Issue #1 提案](https://github.com/laogou717/local-ops/issues/1)（FL411） |

## 参与贡献

**推荐路径（不需要等待审阅）**：

1. Fork 本仓库，自行开发并长期维护自己的版本；
2. 阅读 [CONTRIBUTING.md](CONTRIBUTING.md)——安全校验不得削弱（回环绑定、当前 UID、run token、进程组）、一个 PR 只解决一个主题、提交前运行 `make check`、不提交个人路径/日志/未脱敏素材；
3. 在 Discussions 提交衍生版本说明（名称、定位、fork 地址）；
4. 经试用评估后，收录到上方「社区衍生版本」推荐列表。

Issue 与 PR 同样可以提交，欢迎讨论与参考，但不承诺审阅或合入（见「维护说明」）。行为规范见 [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)；安全问题请按 [`SECURITY.md`](SECURITY.md) 私下报告，不要公开披露。

## 更多文档

- [Wiki 主页](https://github.com/laogou717/local-ops/wiki)：[使用手册](https://github.com/laogou717/local-ops/wiki/使用手册) / [数据与备份](https://github.com/laogou717/local-ops/wiki/数据与备份) / [故障排查](https://github.com/laogou717/local-ops/wiki/故障排查) / [开发者与发布指南](https://github.com/laogou717/local-ops/wiki/开发者与发布指南)
- [`CHANGELOG.md`](CHANGELOG.md) — 变更记录
- [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) — 发布人工验收清单

## 许可与第三方素材

项目自有代码和文档采用 [`MIT License`](LICENSE)。Lucide、Geist Mono 以及项目生成图像等素材可能适用各自的许可或发布限制，不因根目录 MIT 许可证而自动改变，详见 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) 与 [`ASSET_PROVENANCE.md`](ASSET_PROVENANCE.md)。
