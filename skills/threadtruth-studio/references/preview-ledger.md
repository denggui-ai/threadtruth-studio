# 方向预览：统一账本与成片承接

## 当前方案与正常审美修订

新人物／不露脸任务在init spec顶层声明shot_plan v2（见pose-planning.md）；默认9格／9张，明确经典六姿势用v1，缺字段旧任务只按原记录恢复，不宣称已经核验逐格计划。model是当前人物条件唯一来源，摄影与商品约束各有职责；正文不再重复写另一套人物年龄/妆发或另一套pose。导出器统一生成`[Current model conditions]`及`[Task shot plan]`，检测已标记块或明确结构化条款冲突；任意自由文本的语义仍需人工核对。

技术accept不等于用户满意。用户要改已评定（accepted/rejected）但未关闭预览时，先记正常修订，不伪造QA失败：

```sh
python3 scripts/web-task.py revise-preview --task <preview> --look 1 --expected-output-sha256 <当前原图哈希> --spec <revision.json> --note <实际反馈范围>
python3 scripts/web-task.py retry-authorize --task <preview> --look 1 --expected-attempt <当前次数> --approval-id <唯一ID> --note <实际1次新授权>
```

revision.json含完整新`prompt`、可选完整`model`、可选`shot_plan`；省略的项目沿用当前值。也可用`--prompt-file`、`--model-spec`传入。只准备revise-preview不增加调用、不改变当前图的技术QA；待修订方案未出图验收前不能确认其方向。retry-authorize启用该候选并把旧model/计划/图/QA留在history，不必先reject-model。正式首张的reject-model边界不变。无新授权就停在候选方案；初次1次+最多3次修正不变。

manifest给出`current_plan_sha256`与版本；采用此扩展或正常预览修订后的reserve必须同时提供`--expected-plan-sha256`，并照旧匹配当前prompt/参考哈希。旧handoff不可提交；导出目录带版本。方向确认后prepare-delivery直接继承最新有效model、路由及完整逐格计划；单张选择对应编号，预览只留provenance，不当身份附件。停止不等于接受未实现的候选，未解决修订不能转成片。

### 撤回候选与失效素材退出

用户撤回尚未采用的修改、明确继续使用原图时，记录真实撤回意思并执行：

```sh
python3 scripts/web-task.py cancel-preview-revision --task <preview> --look 1 --expected-candidate-sha256 <当前候选哈希> --expected-output-sha256 <原预览哈希> --note <实际撤回理由>
```

该操作只归档并移除指定候选，不改变原QA、原图、model/shot_plan、次数或授权；原图技术accepted才可随后确认方向。rejected原图不能因撤回变成通过。取消不是新的生成授权，也不自动等于方向接受；结束仍用finish-preview stop。已关闭或未决请求不走此分支。

尚未采用候选的外部图片在提议时和采用时核字节；其间删除、改变或失效只能阻止采用，不能阻止撤回、替换或停止。已冻结商品、原图、当前请求/历史哈希与候选元数据绑定仍须有效，不得把这一退出能力扩成跳过事实检查。

### 提示词契约与历史恢复

新schema2任务自动标prompt_contract_version=1；缺标记的旧冻结记录按0恢复，保留原prompt字节/哈希，不要求旧单条或两条人物说明事后凑齐新格式。新准备、候选采用或续组显式进入v1时，原记录按原契约留痕；不自动修改已接受图或无关后续记录。不要删字段伪装旧任务以绕过新检查。

新契约采用shot_plan的请求只由当前计划生成编号动作；正文中的已知`POSE n:`/`Shot n:`旧块先整理到计划，不能再和当前块一起提交。旧契约冻结任务的已知编号master及显式Framing与当前计划一致时，可原字节恢复导出；冲突或未知头允许读取/停止，但必须显式重新准备后才能提交。该检查不解析任意自由文本语义，摄影自由正文仍保留并人工核对。

### 经典v1商品覆盖与双路由扩展

`shot_plan`包含version=1、sku、route=A|B、preservation=classic|adapted、adaptation_note、coverage、looks。coverage每项为`{sha256, views, usable, same_sku, note}`；views从front/front-side/back/detail中选择，引用真实garment-source。实际看图后声明清晰度和同SKU，不以文件名或AI生成背面作依据。正面不足先补图；有可用同款背面为A，否则B。脚本检查声明及引用一致，不会识别SKU、角度或视觉质量。

looks按实际编号排列：预览及整组6项，单张1项。每项为`{pose, master, framing, garment_views, reference_sha256s}`；classic关系/景别见[pose-baselines.md](pose-baselines.md)。adapted须有真实变更说明，可另给本格arrangement。程序渲染统一身体关系；真人计划仍独占真实头向/眼球视线/面部覆盖，所需商品引用必须在其本格附件选择中，不复制两份自由文本权威。新增商品视角没有授权推断真人侧脸。

新准备的露脸`ai`/`new`系列，逐项增加`head`（头部相对身体的朝向）和`gaze`（目光落点），按[prompt-build.md §2](prompt-build.md#2-头部方向--视线人物输出共用服从身体姿势)完成本轮具体安排。二者是成对的非空单行文本；一项使用时，本计划全部项都须具备，不留某格给模型自行补全。它们不改变身体母版或景别，不要求改为adapted；不限制左右次数或直视比例，用户明确固定方向时可按原意重复。真人继续使用real_face_plan，不在此重复记录；不露脸/非人像不添加这两个字段。

这两个字段随shot_plan一起冻结、导出到每个Shot块，预览修订及成片继承沿用同一版本；prompt-only也核对实际导出。旧v1计划可继续不含它们，保持原渲染字节和恢复行为；不向已调用历史或已接受首张回填新头向。字段只检查完整性与来源分支，不自动识别画面、理解自由文字或证明整组有自然变化。

可在revision.json增加`garment_references: [{path, sha256}]`，与修订后的shot_plan一起声明用户新提供的真实商品图。准备阶段只核对文件，取得对应重试授权后才加入冻结库存；原图、历史与累计次数不改写。真人的real_face_plan拥有本格完整实际附件选择，shot_plan声明商品必需引用并作子集校验；额外选择的商品细节也须在coverage声明可用且同SKU，不静默过滤。修订保留仍可用的已选细节，增补当前必需商品引用，保留原始面部覆盖、身份与未指定的身体/头向/视线；B→A第6显示背部并隐藏脸，明示不补未知回眸脸。若要改变真人面部覆盖或其他头向，须遵守原始身份的显式版本边界。所有实际请求仍受5附件限制；不合格/另一SKU素材不成为实际商品附件。

同商品母版1单张续五张时，若已有shot_plan，continue-authorize的spec还要给完整6项shot_plan；其覆盖、路由、已接受第1项不变，后五沿同一规则编译。已有真人任务同时声明原real_face_looks，不新增默认调用权限。

### 新服饰驱动v2承接

v2完整契约见[pose-planning.md](pose-planning.md)。`looks`保留完整逻辑系列，`selected_shot_ids`选择当前执行项；预览编排与独立图共用相同shot_id及冻结字段，不在提交前重新选姿。route A/B只说明背面依据可用性，不把背面绑定第六格。

准备新人物整组时默认九项、一次3×3预览；明确六张仍为六项。首版预览不传pose-reference图片，使用冻结动作文字与必要商品／身份依据；独立图才精确选择本张姿势图。用户明确要求预览使用指定图时先核当前能力，不能静默省略。来源为research-only的材料在任何角色都不可执行。

从第七格选单张时保留完整系列与来源shot_id，series_role=standalone，不因本地look-1而获得续组资格。真正系列首张试拍为series-first，只有原计划、已接受首张及必要依据保持，并取得N−1次新增授权，才可续成原系列。修订、续生、重试、导出共用实际附件选择和容量检查，所有原始次数与历史保留。

### 预览分项检查

分别核商品、选角妆发、逐格关系、场景摄影、明确保留项与本次变更项。明确约定失败判qa-retry；局部细节太小列qa-user-review；纯偏好不喜欢单独记修订，不改写技术事实。用户只说“场景可以”只接受场景。不能承诺整张grid重生会像素冻结其余格，也不能说预览同一张脸必然传到独立图；正式人物以独立首张实际接受为准。

### 用户已授权的本地单格拼接

需要其余区域像素不变、且用户明确允许本地合成时，可将已取得的同画布修改图作为供图，只替换约定矩形。不要为此再生整张grid：

```sh
python3 scripts/web-task.py compose-preview --task <preview> --look 1 --file <existing-donor.png> --rectangle <left> <top> <right> <bottom> --expected-output-sha256 <current-preview-sha256> --expected-donor-sha256 <donor-sha256> --note <实际本地修改授权与范围>
```

仅适用于未关闭且已评定的schema2预览，不缩放供图、不覆盖原始返回；冻结供图、矩形、合成结果、原QA与哈希，并逐像素回查重建结果。操作新增生成0次，原attempts和授权不变；供图此前的生图消耗仍须保留，不能由“本地0次”抹掉。新结果回到returned，重新实际核验后才能accept和确认方向，不自动确认人物或商用。

若本次明确改变了逐格安排，可加`--spec <local-plan.json>`，文件只含完整已审`shot_plan`；SKU、路由和原商品覆盖保持。原生成prompt/计划字节不变，合成记录保存实际修改后的计划，prepare-delivery继承该版本。未指定时沿用当前有效计划；不允许清空计划。后续再生修订通过revise-preview承接该版本，不丢回原安排。无本地操作授权时仍使用原生编辑的真实能力边界，不承诺像素保护。


默认主线在风格选择后进入动作0；准备、执行、恢复或转成片时读取。用户主动单张可跳过预览。使用 `scripts/web-task.py` 的schema2；命令只操作本地记录与文件，不调用生成，也不证明用户实际给了授权。图片和任务仍保存在用户工作区。

## 准备与次数

- `init` 的spec沿用原始服饰参考、人物来源及角色字段，`context.purpose="preview-grid"`、`context.first_pose=1`，只放**一条完整预览提示词**，v2默认九格。这里的1是格子编排起点，不是已生成的正式母版1。非人像按六个构图编号编排。
- `size`/`context.size`为独立grid画布；精确尺寸用 `canvas_policy="exact"`，仅比例用 `ratio-first`。与后续成片画布独立。
- 单条请求含本轮六格或九格，`authorize --limit 1`只授权1次；`reserve --look 1`占用1次。`attempts`为本任务已提交数，`total_attempts`含可追溯的上游预览次数。保持现有未决请求、原图、哈希、元数据与失败恢复检查，不因“只是预览”而绕过。
- `export`导出一个带“方向预览·非成片 / PREVIEW ONLY — NOT FINAL”标记的宫格请求，不加独立成片反拼图前缀。操作者仍需按 `prompt-build.md §4.2` 编排全部计划格，不把任意多图或标记文本存在当作实际视觉验收通过。
- 初次1次，最多**另加3次预览修正请求**，总提交最多4次。技术失败沿用`reject`/`retry-authorize`，正常审美修改先`revise-preview`再按授权`retry-authorize`；要有实际反馈、对应1次新授权及唯一approval ID；失败消耗仍保留，达到上限就结束或先报告问题，不新建预览来清零。

真人露脸预览须提供 `real_face_plan` 的本轮全部格子计划，逐格使用原真人真实覆盖内的朝向。实际附件为全部格子必要参考的并集，原生总数最多5张；一次grid没有后续首张锚点占位。计划与manifest保留全部格子及实际并集，不能只核第1格或静默丢图。AI/new与非人像仍按原分流；真实覆盖约束不扩展到AI。

## 结果与停止

`returned`导入有效原图后，`delivery_status=preview-grid`；重试历史里有预览也保持该状态，没有有效原图则是prepared。先按方向预览核对商品、当前六格／九格布局、标记、人物与安全等适用项，用 `accept`/`reject`记录。这里的 `qa-pass` 只是预览可继续讨论，不是商业QA或用户选人确认。

- 技术接受预览不自动完成、不确认模特；禁止 `confirm-model`、`export-model`、`continue-authorize`，也不把grid当正式look-1。
- 用户确认方向：`finish-preview --decision direction-confirmed --note <实际用户意思>`；须先有已接受预览。
- 用户说“预览就行/不用再出”：`finish-preview --decision stop --note <实际用户意思>`，直接收尾，不追问整组。尚未提交也可停止，不能编造已出预览；已返回先评定，已知失败先按原请求核实恢复；reserved/unknown不能当作远端已停止。
- 完成后 `complete=true`只表示预览任务结束，状态仍preview-grid或prepared，绝不是image-ready；后续不能在已关闭预览里继续提交。保留旧请求与原图，不裁格或去标记。

## 转成片：关联新任务

默认在用户确认方向后准备9条独立提示词及独立画布；明确六张／经典／非人像保留6，主动单张为1。核对当前成片N次的适用授权，不能把方向确认当成调用授权；已授权的范围不重复确认。先结束已评定的预览（方向确认或停止均保留原记录），再执行：

```sh
python3 scripts/web-task.py prepare-delivery --task <new-delivery-directory> --preview-task <closed-preview-directory> --spec <delivery-spec.json> --note <实际成片需求>
```

`delivery-spec.json`含 `context`、`size`，以 `count` 或 `prompts` 声明本次张数；已有visual_plan时可省略prompts确定性编译。purpose省略或为delivery。v2抽单张以context.first_pose指定原slot，默认series_role=standalone；仅真正首张试拍显式设series_role=series-first。沿用原商品、风格、模式、输出形态、人物来源/条件及原始附件。多套预览选中一套时，额外用 `garment_sha256s`显式列出该套原始商品参考哈希，并在context.outfit注明所选套；未选商品不传入成片，原身份依据仍保留。其它风格/模式/输出形态变更按另立任务处理，不静默覆盖本预览选择。

关联任务初始 `attempts=0`、`authorization=null`、`model_confirmation=null`。`preview_origin`、本地冻结预览账本与原grid副本只作历史证据，存于provenance，不进入参考附件、人物包或成片像素基线。`total_attempts`显示预览（含失败/重试）与成片本地次数之和；授权上限仍仅管本次新任务，不能把预览授权当成成片授权。一次预览只关联一个正式任务；v2单张续组按上述series-first规则，旧v1母版1续五保持原契约。

成人成片首张仍须技术QA和实际人物接受；预览确认不能代替。v2真人成片按稳定shot_id承接预览中已审的真人计划；显式传入时须一致，需调整先修订预览。旧v1仍显式提供本次真人计划。真实coverage和原身份不从grid补造。首次有效独立图才建立成片画布基线。未知、损坏或未评定预览不能转任务；不得编辑账本绕过关联或清空历史。创建中断时先核原preview与目标目录，不换目录盲目重复prepare。
