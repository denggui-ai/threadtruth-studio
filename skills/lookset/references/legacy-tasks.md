# 旧冻结任务与经典六姿势

只在处理旧任务或明确经典六姿势时读取对应小节。此处只保存仍生效的兼容规则；新任务按[主流程](../SKILL.md#1-主流程与停点)及各当前参考，不自动继承旧契约。

## 冻结字段与恢复

处理旧冻结任务时按自身版本恢复，不静默升级、不删字段伪装旧任务；原始失败不因源码修复变成成功。图片状态从已有回执推导prepared/image-draft，不改文件、不重置预算、不自动升image-ready。

- `framing_guidance`仅接受整数1/2/3：新建为3；2为数字坐标句，1为旧“头高”句，仅旧冻结/续生保留原值，不互换；缺字段旧计划渲染逐字不变。新init自动补3，后续传计划省略时继承冻结值。
- `variety_checks=2`与`framing_guidance=2/3`都不能证明任务新建；旧`variety_checks: 1`的五格规则保持。原14动作/16视图定义保持，库更新不重写冻结快照；旧内嵌动作词条和旧任务快照继续可读。
- 缺`workflow_version=1`的冻结任务维持原契约，不补新契约；schema1仅旧网页任务使用。无product_edit维持原产品契约；无visual_plan继续原契约恢复。
- 历史姿势摘要version=1仍只精确比较、保留no-exact-repeat，不升级或补读历史；version=2比较规则见[跨组避重](pose-planning.md#跨组姿势避重)。

## 经典六姿势

仅明确经典六姿势或旧v1使用`shot_plan.version=1`、原六母版及校验/导出/续五/重试限制；不套普通新v2九张。完整母版与缺背面第6张替代见[prompt-build §1/§1b](prompt-build.md#1-六个原始姿势母版仅明确经典旧v1任务)，几何与景别见[pose-baselines](pose-baselines.md)，v1商品覆盖/双路由扩展见[preview-ledger](preview-ledger.md#经典v1商品覆盖与双路由扩展)。

- 仅合格母版1单张可按原契约追加五张；真实`context.first_pose`不隐式改编号。custom、诊断、修正编辑及非首张抽取不可续五，保留首张及累计预算。
- 真人续五时，在`continue-authorize --spec`的同商品/风格/画布说明中按look-2…6提供`real_face_looks`五项，仍核真实覆盖、实际附件与原预算，不新增授权。
- v1视觉`shots`按pose映射；非人像仍用原六构图，不用真人第6替代豁免未知背部事实。

## 视觉契约旧字段

- `presentation_2_substituted`（可选，仅六格 v1 的 flat-lay/hanger/mannequin）：无同款背面源时冻结为`true`，第2格渲染正面细节行；`prepare`的spec写`back_source: true`则不冻结。
- `contract`（可选）：`prepare` 写入 `21`。只有带它的计划才使用新的 persona 标题、`Commitment:` 行、第2格替换行，并强制文化入口的 `culture_profile` + `asset_trace`；没有它的旧计划渲染字节不变。承诺的 `needs` 若与人物条件里显式声明的表情／妆发／发型冲突，写入 `commitments_skipped`（reason `model-condition`）。

12个新入口默认无`persona`，需要时逐卡显式添加，不自动从`bases`合并。已冻结的旧任务与不含`persona`的方案渲染字节不变。

## 重新准备与关联修订

已有任务需要重新 `prepare` 时，用 `visual_library.py prepare --task <任务目录> --spec <修订准备文件> --output <新方案文件>` 读取并核对原冻结方案；Python 调用传 `frozen_visual_plan`。不传冻结上下文的准备按全新任务处理。是否已有冻结任务以任务记录／冻结方案为准，不能从 `variety_checks` 或 `framing_guidance` 推断；已有冻结计划也可能有两个值为2的标记。新选姿配额与原图模特造型排除句仅在全新任务首次准备时启用；修订、续组、恢复、重试保留原来有／无该句的状态。显式提交编译提示词时，方案与提示词中的完整匹配视觉块一起继承原渲染约定；不匹配的场景或额外正文仍拒绝。

关联修订同样用 `prepare --task <父任务目录>`（Python 传父任务的 `frozen_visual_plan`），从父任务冻结的 `shot_plan` 取目标格，跳过新任务配额并保留渲染版本及造型句原有状态；保留首张生成人物时允许 `new → ai`，其他来源变更仍拒绝，随后交给 `web-task.py prepare-revision`／`create_revision` 核对实际身份确认、首张图片哈希和固定人物条件。

已知限制：重新准备按**当前**风格卡读取动作池。所用卡在建任务之后新增或扩充了动作池时，旧任务的重新准备、修订和续组（续组需重新准备其余格）会与冻结方案不一致而被拒，`variety_checks: 1` 的旧任务还会被要求至少 5 格带 `pose_id`。此时请按新任务重新开始；已导出的原冻结请求仍可原样使用，不手工改写旧计划。

续图与恢复使用任务里冻结的plan；索引或卡片升级不改旧任务。无visual_plan的旧任务继续按原契约恢复；要采用新方案须显式准备新版本，不静默升级或重写历史请求。输出、修订与未知请求保留累计次数，先查询未知请求再决定是否需要新的授权调用。

## 人物与参考包旧字段

- 未给`styling_lock`的旧人物条件保持旧行为，等同`full`；新计划的显式identity默认不追溯改旧记录。
- 未给purpose的旧任务按原delivery恢复，不自动升级为model-check或改其续生资格。
- 新第二版任务声明`failure_recovery_version=1`；旧第二版须显式采用扩展并留说明，第一版恢复行为不变，均不重置次数。
- 参考包保留旧第一版读取；只有显式选定补充图时写第二版，具体包字段与采用方式仍按[参考包](model-selection.md#参考包与后续新品)。
