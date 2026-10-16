# Q04预览账本：本机更新与无生图验收

2026-10-16。用户明确要求先备份当前版，再把Q04更新到本机，验证预览、停止和转成片的账本流程，仍不生图。本批沿production-governor本机release检查，运行源码固定add4da1；开发证据根为本仓，实际运行证据保留于工作台outputs/caiguang-q04-local-install-20261016，不进入运行包。

## 备份与安装

既有allowlist构建285文件候选（50运行文件）；ZIP SHA256 `2a73e20e3db7f85c9639207cb516e3d5ba7e2418a18ee21da577cbcb6ea90f25`。sidecar、CRC、路径/大小/symlink与干净解包核对通过；运行字节与固定源码一致，未混入测试、eval、缓存、客户资料或开发交接。

既有安装器在切换前完整保留旧源284文件和个人marketplace登记。备份后缀`backup-20261016T123927-97fdc5b4`，完整旧源与安装前逐文件清单相等，登记备份字节一致。随后官方plugin add启用 `1.0.0-beta.13+codex.20261016T123927-97fdc5b4`；官方列表installed/enabled为true。活动源与官方缓存285文件完全一致，50运行文件与add4da1一致；候选仅manifest版本戳有预期差异，其它个人插件/登记保持。

## 已安装流程验证

直接加载官方缓存中的web-task.py，128项本地助手测试通过，包含17个Q04预览用例。测试模块及其CLI子进程显式绑定实际安装脚本；前后活动源/缓存文件哈希保持不变。采用临时合成色块与测试账本，不冒充客户图片或视觉验收。

另保留三条实际安装CLI逐步回执与账本（ledger-smoke.json、ledger-smoke-commands.json及synthetic-ledgers）：

- 预览停止：模拟一次reserve/returned/accept后finish-preview stop；保持preview-grid、complete=true，再提交被拒绝。
- 转单张：关联新的1张任务，attempts=0、total_attempts含预览，authorization/model_confirmation为空；独立2:3画布，grid不进入附件。
- 转六张：关联新的6张任务，同样不继承授权与人物确认；未授权reserve被拒绝。模拟导入20×30独立首张，未确认人物前后续被拒绝；模拟确认后可导出第二张，使用新的独立首张锚点与像素基线，余五张仍pending。

账本里的授权/次数是明确标注的测试模拟，不是实际生成授权或调用；本批真实图片工具调用0。旧任务兼容、未知请求、重试上限、真人逐格引用并集及多套选择由已安装定向回归覆盖。

## 门禁与结论范围

source strict、干净runtime strict、实际安装runtime strict及quick_validate通过。前批源码最终480项全量作为既有证据，本批没有修改行为源码，针对安装路径执行128项，不重复全量。

独立安装审查pass，open=0；复算完整备份、登记、候选/缓存、固定源码运行哈希及128项测试绑定；另核34条CLI命令、4个预期拒绝与模拟账本状态。完整回执留在私人输出目录。

本批结论仅覆盖本机安装与无生图账本执行，状态released(local install)。没有新文字模型场景、视觉质量、隐式触发、新机器、进程中断恢复或实际回滚验证；客户订单/预算未变。未推送、公开发布或重开真人全身锁脸研究，Q07/Q09/Q10/Q11保持未处理。

完整回滚入口在私人安装回执与ROLLBACK.md：先以旧源备份做安装器replace只读预检，需要恢复时才apply并官方启用，不覆盖整份marketplace/Codex配置。本批未实际回滚。后续实际使用从新对话读取新版，当前已运行会话不保证热更新已加载技能。
