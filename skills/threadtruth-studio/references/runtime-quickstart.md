# 运行时速查：默认原生路线的命令序列

本页是 SKILL.md 第 0 节"不经账本脚本，绝不生图"的执行清单，只覆盖**原生路线的生图任务**：网页路线在 `export` 之后改用 `export-web-execution` 与 [chatgpt-web.md](chatgpt-web.md) 的信封提交；固定姿势换装走 [fixed-pose-wardrobe.md](fixed-pose-wardrobe.md) 的专用工具；只要提示词（动作 3）不建任务、不生图。`$SKILL` 指 SKILL.md 所在目录；所有命令在用户工作区目录里运行，任务目录也建在工作区里。脚本只操作本地文件，不生成图片，也不证明用户给了授权。任何一步报错：把错误原样告诉用户并停下，不要绕过、不要手写等价物。

## 0. 识别后、生图前（0 次调用）

1. 商品图登记：`references` 每张一个 `{path, role}`，`role` 用 `garment-source`（商品）、`identity-reference`（沿用的真人身份）、`aesthetic-reference`、`pose-reference`。用 `shasum -a 256 <文件>` 取哈希，后面的 `source_sha256s`、`coverage`、`reference_sha256s` 都填它。
2. 风格入口：`python3 "$SKILL/scripts/visual_library.py" route "<用户说的风格>"` 得到 `entry_ids`；`list` 看全部 36 个入口；`show <entry_id>` 读卡片。推荐理由仍按 style-router。
3. 逐张编排（新人物／不露脸默认 9 张）：按 [pose-planning.md](pose-planning.md) 写 `shot_plan.json`，`version=2`。顶层：`sku`、`route`（有可用背面图为 `A`，否则 `B`）、`coverage`、`looks`、`selected_shot_ids`、`series_role`（整组 `series`，单张 `standalone`），并带 `framing_guidance: 2`（取景留白句由它触发；1 仅为旧冻结计划保留）和 `variety_checks: 2`（新自由编排，动作去重、商品视角及场景检查；旧冻结计划保持1或缺省）。每个 look 必填：`slot`、`shot_id`、`display_goal`、`must_show`、`reason`、`body_action`、`hands`、`support`、`framing`（`full-body`/`knee-up`/`half-body`/`detail`）、`garment_views`（`front`/`front-side`/`back`/`detail` 的子集）、`reference_sha256s`；露脸 AI 人物另给 `head`、`gaze`。风格卡带 `pose_vocabulary` 时，look 另写 `pose_id`（所选词条 id；例：`"pose_id": "kc-wall-stand"`；新计划不设五格配额）。自有库动作使用 `pose_library.py apply` 返回的 `pose_selection` 快照，文字与附图模式见 [选姿说明](pose-planning.md#可选动作与用户指定)，默认继承动作文字，再按本件商品适配`body_action`、`hands`并记录必要的adaptation_note；不用库时写`pose_decision`及具体理由，见同一选姿说明。`coverage` 每项：`{sha256, views, usable, same_sku, note}`。
4. 冻结视觉方案：

```
python3 "$SKILL/scripts/visual_library.py" prepare --spec prepare.json --output visual_plan.json
```

`prepare.json` 骨架：

```json
{"entry_id": "<入口ID>",
 "garment": {"description": "<只写可核对的事实>", "keep": ["<必须保留的结构 1>", "..."], "source_sha256s": ["<商品图哈希>"]},
 "inventory": [{"role": "garment-source", "sha256": "<商品图哈希>"}],
 "model": {"source_type": "new", "scope": "full", "subject": "adult female model", "locked": [], "adjustable": [], "consent_note": "", "styling_lock": "identity"},
 "output_form": "human",
 "shot_plan": <shot_plan.json 全文>}
```

`garment` 可选两键：源图能确定上衣外穿／塞腰／半塞时加 `"hem_state": "untucked" | "tucked" | "half-tucked"`；裤型能确定时加 `"silhouette": "straight-leg" | "wide-leg" | "tapered-leg" | "flared-leg"`。看不清就省略，不要写 unknown。

局部图在完整的`overrides.shots`对应项加`garment_focus: {"description":"本张目标商品/部件与取景边界", "keep":["从源图核对的关键结构"]}`。独立导出优先使用本张商品重点，原商品哈希与必要人物依据保留；例如带鞋结构应明确写出斜带走向及连接位置，不只写“保持原样”。非人像用非人像output_form及商品参考，不带人物要求。

采用知识修饰语、主辅风格或文化资料时，按[知识转译](visual-plan.md#把选中的知识与风格要求写入执行字段)写入上述商品字段与`overrides.photography/art`、逐张计划；来源ID不能代替执行句。显式修改拍法后若与原卡承诺冲突，用`overrides.commitments`提供完整的本轮承诺列表，保留相容项，再经现有人物／形态过滤；不手改冻结的`visual_plan.json`。

`model.source_type`：`new` 新 AI 人物、`ai` 沿用已确认 AI 人物、`real` 真人；`subject` 用 `adult female model` / `adult male model` / `child model`。输出的 `visual_plan.json` 含 9 个 `shots` 和可选 `persona`，不要手改。`--output` 指向已有文件会被拒绝（冻结方案不覆盖），报错里给出可用的新文件名，换名重跑即可。

## 1. 预览任务（动作 0，1 次调用）

```
python3 "$SKILL/scripts/web-task.py" init --task preview --spec init-preview.json
python3 "$SKILL/scripts/web-task.py" authorize --task preview --limit 1 --spec preview-decision.json --note "<已有的本阶段调用授权>"
python3 "$SKILL/scripts/web-task.py" export --task preview
```

`preview-decision.json` 为 `{"style":"<已选正式入口ID>","path":"preview","image_count":1,"note":"<已确认方案的依据>"}`。新建schema2任务标`workflow_version=1`，生成前核对风格、路线、当前阶段张数与选姿记录；已有选择/授权直接记录，不重复询问。如果授权已经记过，只补 `confirm-plan --spec <decision.json>`，不能再次authorize。旧冻结任务无标记时维持原契约，不删字段伪装旧任务。

> `init` 报 `shot_plan.<路径> must be <形状>; got <值>` 是你的 JSON 写错了：改 `shot_plan.json`（如 `must_show` 必须是字符串列表），**必须重新 `prepare --output` 到新文件名**（visual_plan 里冻结着旧 shot_plan，只改 shot_plan.json 重跑 init 会再次被拒），再 `init`；同一任务最多自改 3 次。`--output … already exists` 按报错给的新名重跑。账本/授权/次数/哈希及其他任何报错：原样停下问用户。

`init-preview.json` 骨架：

```json
{"references": [{"path": "<商品图路径>", "role": "garment-source"}],
 "size": [2, 3], "route": "codex_native",
 "model": <同 prepare.json 的 model>,
 "context": {"outfit": "<SKU 标签>", "style": "<入口ID>", "mode": "C", "output_form": "human", "size": [2, 3], "first_pose": 1, "purpose": "preview-grid", "canvas_policy": "ratio-first"},
 "shot_plan": <shot_plan.json 全文>, "visual_plan": <visual_plan.json 全文>}
```

`size` 与 `context.size` 写目标**比例**（默认 2:3）并用 `canvas_policy: ratio-first`，首张返回图确定像素基线，之后同比例的其他像素会被拒收；只有用户给了精确像素才写像素并去掉 `canvas_policy`（按 [modes-scenes.md](modes-scenes.md)）。

`export` 生成 `preview/handoff/look-1-vK/`：`prompt.txt`（唯一允许发给生图的提示词，带九格标记与留白句）、`request.json`（`referenced_image_paths` 的顺序就是附件顺序）、`manifest.json`（`reference_hashes`、`current_plan_sha256`）。然后：

```
python3 "$SKILL/scripts/web-task.py" reserve --task preview --look 1 --ready --refs <manifest.reference_hashes 逐个> --expected-plan-sha256 <manifest.current_plan_sha256>
```

`reserve` 成功后才调用原生生图：prompt 用 `prompt.txt` 原文，附件按 `request.json` 顺序。生图返回后立即导入并评定，再问用户方向：

```
python3 "$SKILL/scripts/web-task.py" returned --task preview --look 1 --file <生成的 PNG>
python3 "$SKILL/scripts/web-task.py" accept --task preview --look 1 --qa qa-pass --review-file preview-qa.json --note "<看到了什么>"   # 或 reject --qa qa-retry
python3 "$SKILL/scripts/web-task.py" finish-preview --task preview --decision direction-confirmed --note "<用户原话>"   # 用户只看预览：--decision stop
```

QA JSON规则见[目标记录](commercial-qa.md#新账本的目标记录)。预览只评可见的方向/分格目标，无法判断的小格商品结构记unknown与qa-user-review，不声称商业成片通过。

## 2. 成片任务（动作 1，N 次调用，N 默认 9）

```
python3 "$SKILL/scripts/web-task.py" prepare-delivery --task delivery --preview-task preview --spec delivery.json --note "<用户原话>"
python3 "$SKILL/scripts/web-task.py" authorize --task delivery --limit <本次授权次数> --spec delivery-decision.json --note "<已有的本阶段调用授权>"
```

`delivery-decision.json` 同上，`path` 为 `after-preview`、`image_count` 为本任务实际N张。明确跳过预览时直接init delivery，记录 `path: "direct"`；主动独立单张可用 `single`。一次整份方案确认覆盖所有选择，note沿用已有确认，内部记录不应变成给用户的多轮问卷。

`delivery.json` 骨架：`{"context": {<同预览 context，但 "purpose": "delivery">}, "size": [2, 3], "count": 9, "series_role": "series"}`。`--limit` 填用户本次明确的成片次数（1…N）。**一个任务只能 `authorize` 一次，当前版本没有追加次数的命令**（`continue-authorize` 只用于经典 v1 单张续五和 v2 series-first 续组，`retry-authorize` 补被拒或已核实失败的单张；关联修订另按§3记录独立的1次授权）。用户先批部分、用完再批时：如实告诉用户这组已记录的次数已用完、追加授权要等运行时补上追加命令（已记 backlog），不要重建任务、不要凭记忆多生成。

每张（look = 1…N）固定四步，串行：

```
python3 "$SKILL/scripts/web-task.py" export --task delivery            # 读 delivery/handoff/look-<N>-vK/
python3 "$SKILL/scripts/web-task.py" reserve --task delivery --look <N> --ready --refs <manifest.reference_hashes> --expected-plan-sha256 <manifest.current_plan_sha256>
<原生生图：prompt.txt 原文 + request.json 顺序的附件>
python3 "$SKILL/scripts/web-task.py" returned --task delivery --look <N> --file <生成的 PNG>
python3 "$SKILL/scripts/web-task.py" accept --task delivery --look <N> --qa <qa-pass|qa-user-review> --review-file qa.json --note "<核对结论>"   # 失败：reject --qa qa-retry；成片 accept 会把头顶留白测量值写入账本（只记录，不改 QA 结论）
```

首张（look 1）技术评定后必须问用户人物是否可用，确认后记录：

```
python3 "$SKILL/scripts/web-task.py" confirm-model --task delivery --look 1 --note "<用户原话>"   # 拒绝：reject-model
```

之后 look 2…N 的 `export` 会自动带上 `02-identity-only.png` 锚点。首张被拒选换人物、单张重试、修订提示词分别用 `reject-model`、`retry-authorize`、`revise-pending`，细则见 [preview-ledger.md](preview-ledger.md) 与 [commercial-qa.md](commercial-qa.md)。

## 3. 审核暂停与关联修订

首次明确审核拦截后暂停相似请求。真实回执用`failed --reason moderation_blocked --failure-receipt <本地原始回执>`记录；不凭猜测分类，其他错误仍按原恢复门禁。相似范围按人物/非人像形态与detail/身体取景分组，本轮人物细节图属同组。暂停本身不增加次数；普通有图视觉拒收不进入审核暂停，已确认不受影响的其他编号可继续。未知请求先核实原结果，超时不当作终态失败。

恢复先保留原展示目标和呈现形式，检查既有动作候选、遮挡、取景与实际商品依据；提出静物方案时，说明人物呈现发生变化并核对明确确认，已有预授权直接沿用。不保证换姿/换景/减少参考能通过审核；实际安全问题不能靠换措辞绕开。确认某个相似编号可继续时，用`review-hold --look N --failure-sha256 <failure对象哈希> --note <核对后的具体决定>`解除该编号对应一次拦截的暂停；其他编号仍暂停。这不是额外调用授权。

已核实无图失败先执行`reconcile-failure --look N --expected-attempt M --request-check-completed --note <核实结论>`。同一呈现、非首张的局部动作/构图修正可用原`retry-authorize --spec`；它保留原目标、稳定图号、其他图和历史。额外1次授权与修订一起记录，当前本张暂停被审阅，其他相似图不会自动解除。未知、未核实失败、旧attempt/plan哈希和重复授权ID仍拒绝。

首张纠正或呈现形式变化使用关联修订，不能拆成互不相干的单张任务：

```bash
python3 "$SKILL/scripts/web-task.py" prepare-revision --task delivery --look 1 --spec correction.json --approval-id correction-1 --note "<明确的额外1次授权与修订范围>"
# 人物改静物时加 --form-change-note "<明确的呈现形式确认>"
# 原new人物的已生成首张转ai参考时加 --identity-note "<接受沿用该实际人物的依据>"
```

`correction.json` 沿用普通单张init spec：同SKU/style/mode/canvas，`count:1`，原人物/商品依据，修订后的visual_plan和可选shot_plan；已有图局部修正用`purpose: correction-edit`、原始身份依据与本张edit-target。无图失败使用delivery且不伪造edit-target；首次new无图失败保留原选角条件。人物改静物只带原商品参考及非人像model/identity声明。运行时将原展示目标与must_show写入子任务请求；v2子计划的展示目标也应保留。

返回的子任务位于`delivery/revisions/<approval-id>`，已经绑定这一次授权与已确认方案，不再authorize。按其真实路径执行export/reserve/returned/QA；有人的修订需确认实际人物，再采用：

```bash
python3 "$SKILL/scripts/web-task.py" adopt-revision --task delivery --approval-id correction-1 --expected-output-sha256 <修订原图哈希> --note "<实际接受并采用该修订结果>"
python3 "$SKILL/scripts/web-task.py" status --task delivery
```

根系列统一稳定图号、当前采用结果与授权。创建关联即停用原槽；重复采用同一已接受结果幂等，不增加调用/预算。首张只在尚无下游生成时采用，同商品/同人物/同画幅且通过QA及实际人物确认后继续原系列；原图、原失败保留。子任务与根系列共用锁，存在任何未决请求时不再提交；子任务不能自行续组或追加授权，失败后到根系列申请下一次实际修订授权。采用后子任务冻结，复核和保留决定写在根系列。

status中的`attempts`仍是该根任务的直接调用，`series_attempts`汇总每个已登记子任务各一次，`series_total_attempts`再加原预览；采用动作不计调用。`files_complete`与`goals_met`分别报告齐图和目标达到。旧任务恢复不补新契约，历史原始失败不因源码修复变成成功。

## 4. 对用户怎么说

- 每一步只报结果与下一步要的确认，不展示 JSON、哈希或状态码；文件路径只在用户要时给。
- `status --task <目录>` 能随时回答"已用几次、还剩几次、哪张待核"，用它的数字，不凭记忆。
- 脚本拒绝（如重复图、比例不符、授权不足）是流程保护：原样转述原因，等用户决定。
