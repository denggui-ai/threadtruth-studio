# Lookset运行时开发注记

本文件不随安装包分发，保存beta.3文字迁移涉及的开发验证、沿革与实现注记；不替代运行时规则，也不授予新增试验、生成或发布权限。原文基线为`ca80316b5064b24de1ef727451cebcec166495e7`，逐项位置见[迁移表](beta3-migration.md)。

## 成熟度与历史版本

以下为基线开发记录，版本号不代表当前安装包。当前版本以 `.codex-plugin/plugin.json` 为准；运行时成熟度摘要保留在主文件。

**技能成熟度状态(诚实标注当前等级):**
- `DRAFT`:静态结构通过、风格包过 pack-lint,但**生图行为未实测**。
- `CANDIDATE`:已在至少一个 host 跑过 G4 等价回归并留证据,待复核。
- `VERIFIED-CODEX`:Codex 全链路真机实测通过(G5:无fallback/不误判/童装/泳装 moderation/受控故障,证据用 event_msg 计数+md5)。
- `BLOCKED`:发现阻断性缺陷,暂停发布。
- **当前公开 Beta 等级(2026-11-04):** 插件版本 `1.0.0-beta.18`；36 个视觉入口、52 动作／60 参考视图。视觉一致性、新机器行为与实际回滚未完整验证，仓库整体保持 `DRAFT`。私有前身的历史测试结论仅作 provenance,不自动升级公开版本成熟度。
- **未真机不得标 CANDIDATE/VERIFIED-CODEX。** G4 等价回归 + G5 真机落地后才升级。

## 运行时缺口

基线 runtime-quickstart.md:86 的“已记 backlog”指普通任务没有追加次数命令。运行时仍保留该限制，不重建任务、不凭记忆多生成；此记录不是新增排期。

## 姿势库验证注记

pose-planning.md:68 原句：

既有记录为59图几何可参考（含3图沿用试点判断，未新增独立复核），不代表画风、边距、商品效果或全部规格通过。

运行时保留逐图限制、user-only推袖门禁及“不代表全部规格通过”。

## 真人全身验证注记

model-selection.md:48 的基线验证注记：

即使先确认 knee-up 首张并经 `export-model --include-accepted-reference` 导出为补充图，验证中仍只有约三分之一被判像。

不据此扩大能力。运行时继续保留全身图脸部至少qa-user-review、不承诺像，以及所需补拍角度与张数仍未验证的原文。

## 路由回归入口

### trigger-eval(L1 发现 + L2 路由)

`evals/trigger-evals.json` 覆盖 core L1 发现与人读 L2 期望;`evals/style-route-evals.json` 由 `tools/trigger-eval.py` 对真实 query 执行规范化、同包别名折叠、最长匹配与 route/hold/none 判定。正负各列:L1 正(法式/日系/老钱/电商/男装/童装 → 触发 core)、L1 负(带货文案配图→xhs;狗粮→非服饰)、L2 确定性归属、L2 未解决同维度冲突、比较/融合意图与跨维度组合、L2 真兜底、L2 假 trace 检测、互抢隔离。

## 注册表历史标记

基线style-router.md:95-113中，preppy、british-heritage、nordic-minimal、gorpcore、balletcore、y2k-millennium、neo-chinese、guochao-street、cityboy、korean-menswear、workwear-vintage、office-commute-women、resort-vacation、coquette-ladylike标“v1 静态”；clean-fit、athleisure、italian-luxe标“Wave 2”。这些仅为沿革，运行时注册表继续保留各别名、冲突与适配规则。

## WP编号沿革

以下仅为开发追踪编号，运行时条件仍在原章节或legacy-tasks：pose-planning.md:115的WP-21b（逐格摄影及最低文本检查）、:129的WP-23（三场景）；visual-plan.md:44的WP-21e（asset_trace）、:45的WP-21d（六格第2格替换）、:46的WP-21（contract=21）、:47的WP-21c（承诺过滤）。

## 旧版本字段注记

visual-plan.md:58 的原版本例证为“beta.18 的旧计划也有两个值为2的标记”。运行时仍要求以实际任务/冻结记录判断新旧，不从两个数值推断。
