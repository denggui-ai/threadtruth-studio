# 六宫格预览：统一账本与成片承接

## 当前方案与正常审美修订

新编号人像任务在init spec顶层声明可选扩展`shot_plan`（格式见下）；新流程准备应使用它，缺字段旧任务只按原记录恢复，不宣称已经核验六格计划。model是当前人物条件唯一来源，摄影与商品约束各有职责；正文不再重复写另一套人物年龄/妆发或六pose。导出器统一生成`[Current model conditions]`及`[Task shot plan]`，检测已标记块或明确结构化条款冲突；任意自由文本的语义仍需人工核对。

技术accept不等于用户满意。用户要改已评定（accepted/rejected）但未关闭预览时，先记正常修订，不伪造QA失败：

```sh
python3 scripts/web-task.py revise-preview --task <preview> --look 1 --expected-output-sha256 <当前原图哈希> --spec <revision.json> --note <实际反馈范围>
python3 scripts/web-task.py retry-authorize --task <preview> --look 1 --expected-attempt <当前次数> --approval-id <唯一ID> --note <实际1次新授权>
```

revision.json含完整新`prompt`、可选完整`model`、可选`shot_plan`；省略的项目沿用当前值。也可用`--prompt-file`、`--model-spec`传入。只准备revise-preview不增加调用、不改变当前图的技术QA；待修订方案未出图验收前不能确认其方向。retry-authorize启用该候选并把旧model/计划/图/QA留在history，不必先reject-model。正式首张的reject-model边界不变。无新授权就停在候选方案；初次1次+最多3次修正不变。

manifest给出`current_plan_sha256`与版本；采用此扩展或正常预览修订后的reserve必须同时提供`--expected-plan-sha256`，并照旧匹配当前prompt/参考哈希。旧handoff不可提交；导出目录带版本。方向确认后prepare-delivery直接继承最新有效model、路由及六格计划；单张选择对应编号，预览只留provenance，不当身份附件。停止不等于接受未实现的候选，未解决修订不能转成片。

### 商品覆盖与双路由扩展

`shot_plan`包含version=1、sku、route=A|B、preservation=classic|adapted、adaptation_note、coverage、looks。coverage每项为`{sha256, views, usable, same_sku, note}`；views从front/front-side/back/detail中选择，引用真实garment-source。实际看图后声明清晰度和同SKU，不以文件名或AI生成背面作依据。正面不足先补图；有可用同款背面为A，否则B。脚本检查声明及引用一致，不会识别SKU、角度或视觉质量。

looks按实际编号排列：预览及整组6项，单张1项。每项为`{pose, master, framing, garment_views, reference_sha256s}`；classic关系/景别见[pose-baselines.md](pose-baselines.md)。adapted须有真实变更说明，可另给本格arrangement。程序渲染统一身体关系；真人计划仍独占真实头向/眼球视线/面部覆盖，所需商品引用必须在其本格附件选择中，不复制两份自由文本权威。新增商品视角没有授权推断真人侧脸。

可在revision.json增加`garment_references: [{path, sha256}]`，与修订后的shot_plan一起声明用户新提供的真实商品图。准备阶段只核对文件，取得对应重试授权后才加入冻结库存；原图、历史与累计次数不改写。真人只由工具派生当前商品附件选择，保留原始面部覆盖、身份与未指定的身体/头向/视线；B→A第6显示背部并隐藏脸，明示不补未知回眸脸。若要改变真人面部覆盖或其他头向，须遵守原始身份的显式版本边界。所有实际请求仍受5附件限制；不合格/另一SKU素材不成为实际商品附件。

同商品母版1单张续五张时，若已有shot_plan，continue-authorize的spec还要给完整6项shot_plan；其覆盖、路由、已接受第1项不变，后五沿同一规则编译。已有真人任务同时声明原real_face_looks，不新增默认调用权限。

### 预览分项检查

分别核商品、选角妆发、六格关系、场景摄影、明确保留项与本次变更项。明确约定失败判qa-retry；局部细节太小列qa-user-review；纯偏好不喜欢单独记修订，不改写技术事实。用户只说“场景可以”只接受场景。不能承诺整张grid重生会像素冻结其余格，也不能说预览同一张脸必然传到独立图；正式人物以独立首张实际接受为准。


默认主线在风格选择后进入动作0；准备、执行、恢复或转成片时读取。用户主动单张可跳过预览。使用 `scripts/web-task.py` 的schema2；所有命令只操作本地记录，不生成图片，也不证明用户实际给了授权。图片和任务仍保存在用户工作区。

## 准备与次数

- `init` 的spec沿用原始服饰参考、人物来源及角色字段，`context.purpose="preview-grid"`、`context.first_pose=1`，只放**一条完整六宫格提示词**。这里的1是格子编排起点，不是已生成的正式母版1。非人像按六个构图编号编排。
- `size`/`context.size`为独立grid画布；精确尺寸用 `canvas_policy="exact"`，仅比例用 `ratio-first`。与后续成片画布独立。
- 单条请求含六格，`authorize --limit 1`只授权1次；`reserve --look 1`占用1次。`attempts`为本任务已提交数，`total_attempts`含可追溯的上游预览次数。保持现有未决请求、原图、哈希、元数据与失败恢复检查，不因“只是预览”而绕过。
- `export`导出一个带“方向预览·非成片 / PREVIEW ONLY — NOT FINAL”标记的六格请求，不加独立成片反拼图前缀。操作者仍需按 `prompt-build.md §4.2` 编排六格，不把任意六图或标记文本存在当作实际视觉验收通过。
- 初次1次，最多**另加3次预览修正请求**，总提交最多4次。技术失败沿用`reject`/`retry-authorize`，正常审美修改先`revise-preview`再按授权`retry-authorize`；要有实际反馈、对应1次新授权及唯一approval ID；失败消耗仍保留，达到上限就结束或先报告问题，不新建预览来清零。

真人露脸预览须提供 `real_face_plan` 的六个格子计划，逐格使用原真人真实覆盖内的朝向。实际附件为六格所选参考的并集，原生总数最多5张；一次grid没有后续首张锚点占位。计划与manifest保留六格及实际并集，不能只核第1格或静默丢图。AI/new与非人像仍按原分流；真实覆盖约束不扩展到AI。

## 结果与停止

`returned`导入有效原图后，`delivery_status=preview-grid`；重试历史里有预览也保持该状态，没有有效原图则是prepared。先按方向预览核对商品、六格布局、标记、人物与安全等适用项，用 `accept`/`reject`记录。这里的 `qa-pass` 只是预览可继续讨论，不是商业QA或用户选人确认。

- 技术接受预览不自动完成、不确认模特；禁止 `confirm-model`、`export-model`、`continue-authorize`，也不把grid当正式look-1。
- 用户确认方向：`finish-preview --decision direction-confirmed --note <实际用户意思>`；须先有已接受预览。
- 用户说“预览就行/不用再出”：`finish-preview --decision stop --note <实际用户意思>`，直接收尾，不追问六张。尚未提交也可停止，不能编造已出预览；已返回先评定，已知失败先按原请求核实恢复；reserved/unknown不能当作远端已停止。
- 完成后 `complete=true`只表示预览任务结束，状态仍preview-grid或prepared，绝不是image-ready；后续不能在已关闭预览里继续提交。保留旧请求与原图，不裁格或去标记。

## 转成片：关联新任务

默认在用户确认预览方向后准备6条独立提示词及独立画布；用户主动改为单张时才准备1条。核对成片6次或主动单张1次的适用授权，不能把方向确认当成调用授权；已授权的范围不重复确认。先结束已评定的预览（方向确认或停止均保留原记录），再执行：

```sh
python3 scripts/web-task.py prepare-delivery --task <new-delivery-directory> --preview-task <closed-preview-directory> --spec <delivery-spec.json> --note <实际成片需求>
```

`delivery-spec.json`含 `context`、`size`、`prompts`，以及适用的 `real_face_plan`；purpose省略或为delivery。沿用原商品、风格、模式、输出形态、人物来源/条件及原始附件。多套预览选中一套时，额外用 `garment_sha256s`显式列出该套原始商品参考哈希，并在context.outfit注明所选套；未选商品不传入成片，原身份依据仍保留。其它风格/模式/输出形态变更按另立任务处理，不静默覆盖本预览选择。

关联任务初始 `attempts=0`、`authorization=null`、`model_confirmation=null`。`preview_origin`、本地冻结预览账本与原grid副本只作历史证据，存于provenance，不进入参考附件、人物包或成片像素基线。`total_attempts`显示预览（含失败/重试）与成片本地次数之和；授权上限仍仅管本次新任务，不能把预览授权当成成片授权。一次预览只关联一个正式任务；单张后续+5仍走既有合格母版1续组规则。

成人成片首张仍须技术QA和实际人物接受；预览确认不能代替。真人成片重新给出适用于1/6张的计划，真实coverage和原身份不从grid补造。首次有效独立图才建立成片画布基线。未知、损坏或未评定预览不能转任务；不得编辑账本绕过关联或清空历史。创建中断时先核原preview与目标目录，不换目录盲目重复prepare。
