# 运行时速查：默认原生路线的命令序列

本页是 SKILL.md 第 0 节"不经账本脚本，绝不生图"的执行清单，只覆盖**原生路线的生图任务**：网页路线在 `export` 之后改用 `export-web-execution` 与 [chatgpt-web.md](chatgpt-web.md) 的信封提交；固定姿势换装走 [fixed-pose-wardrobe.md](fixed-pose-wardrobe.md) 的专用工具；只要提示词（动作 3）不建任务、不生图。`$SKILL` 指 SKILL.md 所在目录；所有命令在用户工作区目录里运行，任务目录也建在工作区里。脚本只操作本地文件，不生成图片，也不证明用户给了授权。任何一步报错：把错误原样告诉用户并停下，不要绕过、不要手写等价物。

## 0. 识别后、生图前（0 次调用）

1. 商品图登记：`references` 每张一个 `{path, role}`，`role` 用 `garment-source`（商品）、`identity-reference`（沿用的真人身份）、`aesthetic-reference`、`pose-reference`。用 `shasum -a 256 <文件>` 取哈希，后面的 `source_sha256s`、`coverage`、`reference_sha256s` 都填它。
2. 风格入口：`python3 "$SKILL/scripts/visual_library.py" route "<用户说的风格>"` 得到 `entry_ids`；`list` 看全部 36 个入口；`show <entry_id>` 读卡片。推荐理由仍按 style-router。
3. 逐张编排（新人物／不露脸默认 9 张）：按 [pose-planning.md](pose-planning.md) 写 `shot_plan.json`，`version=2`。顶层：`sku`、`route`（有可用背面图为 `A`，否则 `B`）、`coverage`、`looks`、`selected_shot_ids`、`series_role`（整组 `series`，单张 `standalone`），并带 `framing_guidance: 1`（取景留白句由它触发）。每个 look 必填：`slot`、`shot_id`、`display_goal`、`must_show`、`reason`、`body_action`、`hands`、`support`、`framing`（`full-body`/`knee-up`/`half-body`）、`garment_views`（`front`/`front-side`/`back`/`detail` 的子集）、`reference_sha256s`；露脸 AI 人物另给 `head`、`gaze`。`coverage` 每项：`{sha256, views, usable, same_sku, note}`。
4. 冻结视觉方案：

```
python3 "$SKILL/scripts/visual_library.py" prepare --spec prepare.json --output visual_plan.json
```

`prepare.json` 骨架：

```json
{"entry_id": "<入口ID>",
 "garment": {"description": "<只写可核对的事实>", "keep": ["<必须保留的结构 1>", "..."], "source_sha256s": ["<商品图哈希>"]},
 "inventory": [{"role": "garment-source", "sha256": "<商品图哈希>"}],
 "model": {"source_type": "new", "scope": "full", "subject": "adult female model", "locked": [], "adjustable": [], "consent_note": ""},
 "output_form": "human",
 "shot_plan": <shot_plan.json 全文>}
```

`garment` 可选两键：源图能确定上衣外穿／塞腰／半塞时加 `"hem_state": "untucked" | "tucked" | "half-tucked"`；裤型能确定时加 `"silhouette": "straight-leg" | "wide-leg" | "tapered-leg" | "flared-leg"`。看不清就省略，不要写 unknown。

`model.source_type`：`new` 新 AI 人物、`ai` 沿用已确认 AI 人物、`real` 真人；`subject` 用 `adult female model` / `adult male model` / `child model`。输出的 `visual_plan.json` 含 9 个 `shots` 和可选 `persona`，不要手改。`--output` 指向已有文件会被拒绝（冻结方案不覆盖），报错里给出可用的新文件名，换名重跑即可。

## 1. 预览任务（动作 0，1 次调用）

```
python3 "$SKILL/scripts/web-task.py" init --task preview --spec init-preview.json
python3 "$SKILL/scripts/web-task.py" authorize --task preview --limit 1 --note "<用户原话>"
python3 "$SKILL/scripts/web-task.py" export --task preview
```

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
python3 "$SKILL/scripts/web-task.py" accept --task preview --look 1 --qa qa-pass --note "<看到了什么>"   # 或 reject --qa qa-retry
python3 "$SKILL/scripts/web-task.py" finish-preview --task preview --decision direction-confirmed --note "<用户原话>"   # 用户只看预览：--decision stop
```

## 2. 成片任务（动作 1，N 次调用，N 默认 9）

```
python3 "$SKILL/scripts/web-task.py" prepare-delivery --task delivery --preview-task preview --spec delivery.json --note "<用户原话>"
python3 "$SKILL/scripts/web-task.py" authorize --task delivery --limit <本次授权次数> --note "<用户原话>"
```

`delivery.json` 骨架：`{"context": {<同预览 context，但 "purpose": "delivery">}, "size": [2, 3], "count": 9, "series_role": "series"}`。`--limit` 填用户本次明确的成片次数（1…N）。**一个任务只能 `authorize` 一次，当前版本没有追加次数的命令**（`continue-authorize` 只用于经典 v1 单张续五和 v2 series-first 续组，`retry-authorize` 只补被拒单张）。用户先批部分、用完再批时：如实告诉用户这组已记录的次数已用完、追加授权要等运行时补上追加命令（已记 backlog），不要重建任务、不要凭记忆多生成。

每张（look = 1…N）固定四步，串行：

```
python3 "$SKILL/scripts/web-task.py" export --task delivery            # 读 delivery/handoff/look-<N>-vK/
python3 "$SKILL/scripts/web-task.py" reserve --task delivery --look <N> --ready --refs <manifest.reference_hashes> --expected-plan-sha256 <manifest.current_plan_sha256>
<原生生图：prompt.txt 原文 + request.json 顺序的附件>
python3 "$SKILL/scripts/web-task.py" returned --task delivery --look <N> --file <生成的 PNG>
python3 "$SKILL/scripts/web-task.py" accept --task delivery --look <N> --qa <qa-pass|qa-user-review> --note "<核对结论>"   # 失败：reject --qa qa-retry
```

首张（look 1）技术评定后必须问用户人物是否可用，确认后记录：

```
python3 "$SKILL/scripts/web-task.py" confirm-model --task delivery --look 1 --note "<用户原话>"   # 拒绝：reject-model
```

之后 look 2…N 的 `export` 会自动带上 `02-identity-only.png` 锚点。首张被拒选换人物、单张重试、修订提示词分别用 `reject-model`、`retry-authorize`、`revise-pending`，细则见 [preview-ledger.md](preview-ledger.md) 与 [commercial-qa.md](commercial-qa.md)。

## 3. 对用户怎么说

- 每一步只报结果与下一步要的确认，不展示 JSON、哈希或状态码；文件路径只在用户要时给。
- `status --task <目录>` 能随时回答"已用几次、还剩几次、哪张待核"，用它的数字，不凭记忆。
- 脚本拒绝（如重复图、比例不符、授权不足）是流程保护：原样转述原因，等用户决定。
