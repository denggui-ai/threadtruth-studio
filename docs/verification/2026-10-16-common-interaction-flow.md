# 常用交互流程修订（2026-10-16）

## 任务与边界

用户指定修订交互盘点 Q01、Q02、Q03、Q05、Q06、Q08，先理顺“服饰输入→简短方案→首张→续组或结束”，本轮不生图。开发位置为现有 model-reference-reuse worktree，基线 `95a4abe`。系统 skill-creator 用于本轮创作；没有进行安装、生产认证或公开发布。图片调用为0，未重新开展真人全身锁脸研究。

## 结果与状态

| 问题 | 本轮结果 | 状态 |
|---|---|---|
| Q01 默认入口 | 新 schema2 的 create/CLI 默认 Codex；现有记录仍沿原 route，schema1 保留网页默认 | fixed(source/local) |
| Q02 画布契约 | 新比例任务声明 frozen context.canvas_policy=ratio-first；首张有效原图确定像素基线，后续/重试/续组相同；exact及无字段旧任务保留精确尺寸 | fixed(source/local) |
| Q03 单张续组 | 首张前说明是否可续；同类别取景保留编号；仅delivery母版1满足现有前提才可+5，先查后续附件与真人覆盖；不新增续组能力 | fixed(source/rule) |
| Q05 默认呈现 | 一份具体推荐方案，人物备选、24风格及模式按需展开；保留自由选择能力 | fixed(source/rule) |
| Q06 预览停止 | 预览满意可结束；按实际需求1张或6张独立重生成，方向确认不等于次数授权；跨轮和GRID-FINAL同步 | fixed(source/rule) |
| Q08 完成措辞 | 单张接受结束、商品待核和商业交付分别说明；单张image-ready按本张适用检查，不要求凑六张；账本不自动升商业状态 | fixed(source/rule) |

`fixed(source/rule)` 只证明规则已对齐，不等于新模型对话已验证。真实对话表现为 deferred(live-dialogue-validation)，本轮不新增模型或图片调用。Q04预览统一账本、Q07真人素材教程、Q09网页手动体验、Q10童装记录和Q11称呼均不在本轮修复范围；原盘点保留为历史，不自动改写成全项通过。

## 画布实现说明

`size` 与 `context.size` 始终相同并受原上下文校验保护。ratio-first时，它们表达目标比例的整数宽高（如[2,3]），不是隐藏的精确像素要求。首张导出仅要求比例；首张有效返回后，从首张output及其保留history推导像素基线，后续导出要求该实际像素。不新增可被重置的独立基线状态，也不改冻结的context。

只通过PNG解码、比例和去重检查的原图才建立基线；视觉拒选仍保留已经合规的画布。比例不符、损坏或重复原图不建立新基线，原失败证据与累计次数保持。商业验收与人物确认继续独立判断。旧任务无canvas_policy时精确像素语义不变；读取不迁移、不重写。

## 验证

- 测试先行：新增初始8项本地合成图回归，修前6失败/2通过，失败覆盖旧默认网页与缺少比例策略；修后连同原任务测试78项通过。
- 最新定向：`python3 -m pytest tests/test_common_flow.py tests/test_model_task.py tests/test_web_task.py tests/test_generation_entry.py tests/test_real_face_plan.py tests/test_photography_targets.py -q -p no:cacheprovider`：136 passed，166 subtests passed。common-flow包含9项，额外覆盖网页比例导入及冻结策略防篡改。所有图片为测试临时目录中的合成色块，不调用生成工具。
- 全量：`python -m unittest discover -s tests -q`，462项通过。该次发现阶段加载了初始8项common-flow；新增第9项已在上述最新定向136项中通过。
- 环境：首次默认Python全量462项中，16个test_brand_assets用例因缺fontTools出错，10个test_wardrobe_edit用例因Node sharp不可用失败。切换本机已有依赖完整的Python环境，并设置现有bundled Node包路径后，全量462项通过；未安装依赖。首次系统creator验证也因缺PyYAML失败，复用现有环境后输出Skill is valid。
- 独立源码审查：任务助手兼容性无发现；1项P2为跨轮预览与GRID-FINAL残留强制六张，已同步修正并获复核fixed，open=0。审查未运行图片/模型/网络调用。
- CF-01–08位于 `evals/common-flow-evals.json`，是源侧无生图回归定义，未宣称实际模型运行结果。

本批仅交付开发源码及其本地验证。已安装插件和公开beta.13保持原版本；本批不自动安装、推送、发版或追加验证循环。
