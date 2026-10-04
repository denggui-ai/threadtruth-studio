# 裁光模特开发交接

更新：2026-10-04。Owner：当前用户会话中的 Codex。当前阶段：D1、限定 D2、已有 D3 对账、D4 候选及本机授权安装均完成。用户随后要求继续质量开发；当前 APPEARANCE-1 源码修订已完成，视觉验证待授权。

- 正确开发位置：本 worktree `threadtruth-studio/.worktrees/model-reference-reuse`，分支 `feat/model-reference-reuse`。
- 运行时代码基线：`e1364a3`；已安装批次源码增量为首回复 `SKILL.md`，见[本批记录](../docs/verification/2026-10-04-first-response-flow.md)。运行时目标：`skills/threadtruth-studio/`；开发证据根：本仓库。
- 当前唯一开发路线：[model-selection-roadmap.md](../docs/development/model-selection-roadmap.md)。它更新后续排期，不改写历史实验。
- 核心目标：已有模特可沿用；没有模特时可推荐和选择；因子可理解和调整；首张确认后可携带参考包继续展示新品。
- 已完成：规则/辅助工具实现、固定姿势受限路径、四处恢复与校验修复、beta.11 规则整合，以及用户授权的本机安装启用。
- 当前限制：严格原真人还原、自由换姿势的一致性、部分商品细节和真实新会话调用证据未全部解决。六姿势样片只有有限可用接受，不能升级为完整产品验收。
- 本机安装版：`1.0.0-beta.11+codex.20261004T050220-2bd3b1d9`，已 installed-and-enabled；source/cache 各45运行文件通过，完整上一版备份与其他插件登记已保留。见[安装核验](../docs/verification/2026-10-04-flow1-live-install.md)。

## 当前工作与唯一下一步

用户在 FLOW-1 安装后要求继续原模特质量开发。已复现并修正 APPEARANCE-1：已有 AI/真人卡未逐项写妆发时，风格默认妆发仍漏入提示词；空 adjustable 又会抵触 locked 中明确的新妆发目标。见[当前修订](../docs/verification/2026-10-04-model-appearance-defaults.md)。89 项模特测试通过；已有 FLOW-1 完成状态不变。

下一步仅是准备好的两张原生图片对照：修前、修后各一张，相同原人物及商品附件，检验这个新反例的视觉影响。私人执行包位于工作台 `outputs/caiguang-model-appearance-20261004/REPORT.md`，当前 manifest 的 after 指向 after-v2；旧 after 只保留证据。生图次数授权为 0；不得因本次开发指令自动调用、重试或扩成六姿势。

当前修订尚未安装。本机仍为上列 FLOW-1 安装版，原安装备份保留；不重复请求已完成安装的同意。严格真人保真、自由换姿势和部分商品细节仍未解决，不能把提示词测试通过写成视觉成功。`DISCOVERY-1` 仍缺新安装版真实新会话行为证据，本批不重复同题代理或旧 14 次试拍。

## 恢复注意

- 顶层工作台的旧 handoff 涉及前身项目，不是此任务的开发边界；不要切回旧 skill 或别的 worktree。
- 历史报告中“未安装”“缺字体依赖”“真人素材缺失”等是当时状态；当前以路线图证据表及后续记录为准。
- 本次 D4 确实运行了 318 项，须同时披露 sharp 环境失败及定向恢复，不能称首轮全过；历史基线另保留。安装成功不是生图效果成功。
- 已安装 FLOW-1 批次只有一处运行时规则修订；后续 APPEARANCE-1 修改共享人物 helper 与对应参考说明及源侧回归，目前仅源码。后续批次没有生图、安装或公开发布。限定单例通过不等于普遍可靠性、完整产品验收或广泛闭环自进化。
