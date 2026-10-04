# 裁光模特开发交接

更新：2026-10-04。Owner：当前用户会话中的 Codex。当前阶段：flow2已按授权本机安装启用，无生图验收完成但为12/13；首句措辞回归与默认提示词兼容警告记录为非阻断后续项。历史人物样本有限接受及保脸增益inconclusive保持。

- 正确开发位置：本 worktree `threadtruth-studio/.worktrees/model-reference-reuse`，分支 `feat/model-reference-reuse`。
- 运行时代码基线：`e1364a3`；已安装批次源码增量为首回复 `SKILL.md`，见[本批记录](../docs/verification/2026-10-04-first-response-flow.md)。运行时目标：`skills/threadtruth-studio/`；开发证据根：本仓库。
- 当前唯一开发路线：[model-selection-roadmap.md](../docs/development/model-selection-roadmap.md)。它更新后续排期，不改写历史实验。
- 核心目标：已有模特可沿用；没有模特时可推荐和选择；因子可理解和调整；首张确认后可携带参考包继续展示新品。
- 已完成：规则/辅助工具实现、固定姿势受限路径、四处恢复与校验修复、beta.11 规则整合，以及用户授权的本机安装启用。
- 当前限制：严格原真人还原、自由换姿势的一致性、部分商品细节和真实新会话调用证据未全部解决。六姿势样片只有有限可用接受，不能升级为完整产品验收。
- 本机安装版：`1.0.0-beta.11+codex.20261004T105122-85550bbb`（flow2），installed-and-enabled；source/cache278文件一致、45运行文件匹配候选，完整旧源及登记备份保留。官方更新移除旧缓存；新会话无生图验收12/13。见[当前安装核验](../docs/verification/2026-10-04-flow2-live-install.md)。

## 当前工作与唯一下一步

flow2已按用户明确授权安装并启用，278源/缓存文件一致、45运行文件匹配候选，完整旧版备份保留。已安装助手6项本地状态检查通过；真实新CLI会话读取新版并保持零生图，13项行为断言12项通过。唯一失败为首句在素材核对后预告选角交付，记为非阻断 `FLOW2-INSTALLED-FIRST-1=deferred(issue:flow2-installed-first-reply)`；不把安装成功写成验收全过。见[当前记录](../docs/verification/2026-10-04-flow2-live-install.md)。本次安装/验收已结束，不自动追加重跑、改包或生图；flow2超长默认提示词被宿主忽略另记 `deferred(issue:flow2-host-metadata-compat)`。如要修这些后续项，先明确下一轮源码范围。严格保脸和商品验收限制保持。

本机新CLI显式调用已安装版本有真实证据，`DISCOVERY-1`限定关闭；隐式自动触发与其他主机仍未验证。新聊天可加载flow2；当前聊天仍可能持有旧版已载入规则。候选开发的24/24仅属历史限定证据，见[候选收口](../docs/verification/2026-10-04-routing-closeout.md)。

前批AUTO-FLOW-2与CLI-FIRST-1的限定修订仍保留，旧证据见[历史记录](../docs/verification/2026-10-04-casting-flow-followup.md)。原ROUTE-PATH-1/CLAIM-ORDER-1/EVAL-138-SPLIT backlog已由本批在声明范围关闭，不覆盖历史结论。

安装后自动化验收原结果为31项集成通过、三个场景12/14项断言通过，见[历史自动化验收](../docs/verification/2026-10-04-installed-automation.md)。用户随后同意补齐真实调用证据并修正两项呈现问题；本批源码与限定复测见[自动化修订](../docs/verification/2026-10-04-automation-fixes.md)。84项定向回归通过，独立源码审查无新增阻断；两项行为复测9/10，原三发现关闭于声明范围，当时新增试拍/人物确认说明缺项与CLI首句预告，已由上段后续限定修订闭环。已安装appearance1保持原版本，本批不自动安装或追加生图；实际新品使用仍先核对六图附件总数。

用户在 FLOW-1 安装后要求继续原模特质量开发。已复现并修正 APPEARANCE-1：已有 AI/真人卡未逐项写妆发时，风格默认妆发仍漏入提示词；空 adjustable 又会抵触 locked 中明确的新妆发目标。见[当前修订](../docs/verification/2026-10-04-model-appearance-defaults.md)。89 项模特测试通过；已有 FLOW-1 完成状态不变。

已按用户“授权确认”完成修前、修后各一张原生图片对照，输入与提示沿用冻结包。结果未证明明确保脸提升；用户已接受两张的人物表现，确认与私人参考包已记录，商品仍单独qa-user-review。私人执行包位于工作台 `outputs/caiguang-model-appearance-20261004/REPORT.md`，当前 manifest 的 after 指向 after-v2；旧 after 只保留证据。授权2次已全部执行，剩余0；不得自动重试或扩成六姿势。用户已选择此前说明的接受后打包安装路径；本机备份替换与启用已完成，见[发布记录](../docs/verification/2026-10-04-appearance-release.md)。下一步为新会话实际新品使用，用户需提供新品实拍并指定已有私人人物包。不追加生图。

当前修订已安装，完整原FLOW-1版备份保留；不重复请求本次安装同意、不重复安装或抽图。严格真人保真、自由换姿势和部分商品细节仍未解决，不能把提示词测试通过写成视觉成功。后续flow2已补齐本机新CLI显式调用证据，仍不证明隐式触发或视觉质量；不重复旧14次试拍。

## 恢复注意

- 顶层工作台的旧 handoff 涉及前身项目，不是此任务的开发边界；不要切回旧 skill 或别的 worktree。
- 历史报告中“未安装”“缺字体依赖”“真人素材缺失”等是当时状态；当前以路线图证据表及后续记录为准。
- 本次 D4 确实运行了 318 项，须同时披露 sharp 环境失败及定向恢复，不能称首轮全过；历史基线另保留。安装成功不是生图效果成功。
- 已安装 FLOW-1 批次只有一处运行时规则修订；后续 APPEARANCE-1 修改共享人物 helper 与对应参考说明及源侧回归，已完成本机安装。后续批次按授权完成2次原生图片对照及接受后的本机交付，没有公开发布。限定单例通过不等于普遍可靠性、完整产品验收或广泛闭环自进化。
