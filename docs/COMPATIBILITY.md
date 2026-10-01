# Compatibility / 兼容性

Updated 2026-10-01. The current public package remains [beta.9](https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.9); beta.10 is an unpublished candidate. Verification below is scoped to the recorded environment and task; it is not a general compatibility guarantee.

更新于2026-10-01。当前公开包仍为[beta.9](https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.9)；beta.10为未发布候选。下表仅说明已记录环境与任务的验证范围，不承诺所有环境兼容。

| Surface or task / 环境或任务 | Evidence / 证据 | Boundary / 边界 |
|---|---|---|
| beta.10 candidate / 候选 | 219 local tests and runtime static checks passed; two fresh-context casting preparations honored explicit/default targets; one native first-image PNG is 1024×1536 / 219项本地测试及静态检查通过，两条独立文字选角处理成立，一次原生首图尺寸符合 | Both first replies exceeded the input-gate-only boundary; generated sleeve construction and placket occlusion require qa-retry. Publication held. No fresh-host installation or six-image workflow proof / 首回复越界、袖口补造与门襟遮挡未关闭；暂缓发布，不证明新宿主或完整六图流程 |
| beta.9 archive checks / 归档检查 | Package extraction, isolated registration and prior-metadata upgrade/rollback fixtures passed; release does not establish fresh-host success / 解压、隔离目录注册及旧版元数据升级／回滚夹具通过；发布不代表新环境实测成功 | No fresh-host installation, GUI discovery or image-generation verification is claimed / 不声称已完成新环境安装、界面发现或生图验证 |
| beta.9 missing-photo CLI candidate / 缺图文字候选复测 | Fresh maintainer CLI probes reproduced [Issue #1](https://github.com/denggui-ai/threadtruth-studio/issues/1); revised project-scoped skill loaded on the original prompt and garment paraphrases / 本机独立文字会话复现后，项目级候选技能在原始提示及服饰改写中可观察完整读取 | CLI 0.155.1, project-scoped candidate, image capability disabled; not installed-plugin, GUI, fresh-host or paid-action proof / 项目级候选，关闭生图；不等于插件安装、界面、新用户或付费动作验证 |
| beta.9 installed-plugin text regression / 已安装插件文字复测 | Retained maintainer macOS 26.6.2 / CLI 0.155.1 record: final 8/8 visible replies passed independent grading; original minimal prompt 3/3, explicit invocation, catalog and garment paraphrases observed complete Skill reads; non-apparel control stayed outside apparel / 留存本机记录：最终8/8可见回复通过独立评分，原始短提示3/3、显式调用、目录及服饰改写观察到完整读取，非服饰对照未进入服饰流程 | Includes commentary before loading; prior 2/6 failures retained. Images were disabled. GUI display, actual rollback and non-maintainer fresh-host verification remain pending. This is a historical text-only observation, not a new run or a closed public Issue #1 / 包含读取前首答并保留初次安装候选2/6失败；关闭生图，界面显示、实际回滚及非维护者新环境仍待验证，本次未重跑或关闭公开Issue |
| beta.8 installation on maintainer macOS / 维护者macOS安装 | Installed and enabled; 290 source/cache files checked, with only the expected manifest version marker differing; prior backup retained / 已安装启用；290文件核对，仅有预期版本标记差异，旧版备份保留 | Local host only; fresh-host installation and an actual rollback were not tested in this round / 仅本机；本轮未验证新宿主安装或实际回滚 |
| Installed beta.8 instructions and helpers / 已安装指令与工具 | Explicit installed-path loading in a fresh context; local helper help, status and export checks passed / 独立上下文显式加载已安装路径，本地帮助、状态与导出检查通过 | Not automatic skill discovery or a new user's GUI session / 不等于自动发现技能或新用户界面实测 |
| ChatGPT web automation / 网页自动执行 | Six independent images returned and user-accepted on maintainer macOS with authorized dedicated Chrome / 维护者macOS与授权专用Chrome完成六张独立图并经用户验收 | Composition and variation limits remain; browser tools and account quota are required; image model unverified / 保留构图与变化度限制；依赖宿主浏览器工具及账号额度，生图型号未核实 |
| Single-image handoff / 单张转交 | Upload, one submission, original download and size/hash checks completed through automation / 自动化完成上传、一次提交、原图下载和尺寸／哈希检查 | Human manual usability unverified / 真人手动易用性未验证 |
| Codex desktop / 桌面应用 | Used in the maintainer workflow; desktop build not recorded / 维护者工作流已使用，桌面build未记录 | No cross-version or fresh-task automatic-trigger claim / 不承诺跨版本兼容或新任务自动触发 |
| Other hosts and operating systems / 其他宿主与操作系统 | No retained successful fresh-host lifecycle record / 无留存的新宿主完整生命周期成功记录 | Pending; manual handoff is documented, not proven across platforms / 待验证；已有手动转交说明，不等于跨平台实测 |
| Official Plugin marketplace / 官方市场 | No listing or acceptance evidence / 无上架或获批证据 | No official listing claimed / 不声称官方上架 |

Installation does not provide browser automation tools. Open a new Codex task after upgrading; an existing task does not reload its Skill instructions. Successful installation and helper checks are separate from image-generation evidence. Installation, backups and rollback instructions: [INSTALL.md](INSTALL.md). Web steps and tested limits: [CHATGPT-WEB-TUTORIAL.md](CHATGPT-WEB-TUTORIAL.md).

插件安装不附带浏览器自动化工具。升级后需新建Codex任务；旧任务不会热更新已加载的技能说明。安装与本地工具检查不能替代生图证据。[安装指南](INSTALL.md)说明安装、备份与回滚；[网页教程](CHATGPT-WEB-TUTORIAL.md)说明操作与实测边界。

## Public gallery and historical evidence / 公开图库与历史证据

- The [24-style paired gallery](https://denggui-ai.github.io/threadtruth-studio/compare.html) contains 48 comparison results from historical and supplementary batches, with per-case source credits, rights disclosures and reviews. It is not 24 completed six-image workflows or a claim that all results were generated with beta.8. / 新图库汇集历史及补测批次的24风格、48张对照结果，逐组列明来源、权利披露与评审；不等于24套完整六图流程，也不表示全部由beta.8生成。
- The [beta.5 local verification](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/verification/2026-09-21-beta.5-local.md) remains historical evidence for source/runtime checks, packaging and maintainer installation. The previously recorded macOS `26.6.2` and `codex-cli 0.155.1` environment belongs to that record, not a newly verified beta.8 compatibility matrix. / beta.5的源码、打包与本机安装记录保留；此前记录的系统及CLI版本不能自动当作beta.8的新兼容矩阵。
- The beta.3/beta.4 white-vest and coordinated-outfit direction-preview collections remain unchanged historical examples. Their acceptance does not validate current-runtime visual quality. Earlier beta.1 lifecycle checks also remain version-specific evidence. / beta.3／beta.4白马甲与完整套装方向预览保持不变，其验收不代表当前运行时画质；beta.1生命周期检查也仅证明当时版本的范围。

Stable v1.0.0, non-maintainer adoption and the public Beta exit criteria remain separate work. / 稳定版v1.0.0、非维护者采用与公开Beta退出条件仍是独立工作。
