# 已确认姿势母图的局部换装（成人单人，可选）

本分支按用户选定母图的实际姿态局部换装；`prompt-build.md §1b` 的缺背面第六张替代只用于新建六图姿势计划，不授权替换已选母图、重建姿势或缩小保护区。母图展示新品源图不支持的背部结构时，先补素材或明确选择另有支持的母图；不自动改姿势或生图。
适用于用户明确沿用既有人物与身体姿势，只替换指定服饰部件。不是自动抠图、任意转头或真人精确还原能力；常规新人物、新姿势仍走 model-selection 的首张确认。原有六姿势母版和24个风格包不改。

## 选定依据与分流

- **有已确认母图**：核对参考包和实际图像，按实际姿势显式选一张作为 `pose-mother` 编辑目标。同时对照原始人物、已接受候选和本次商品源，分别记录原照保真、候选连续性、商品 QA。旧背景和姿势只在这个固定编辑分支沿用；它们不进入人物固定条件。
- **只有人物照片**：仍先试拍、技术 QA、用户选人，再逐张形成姿势母图。有明显脸部漂移的图停止传播；新姿势需要对应授权。未经确认不能为了凑齐六张导入包。生成身体不是原真人身体测量。
- 原照保真、候选连续性或商品事实出现确定失败时，不传播该母图。无法可靠判断时保留 `qa-user-review`，说明用途与差距；用户有限接受仅表示其声明范围内可用，不证明真人严格还原或商业发布合格。用户若要求精确原脸，保真待核也不能当作满足该要求。
- 当前服饰来源决定替换部件；旧裙、鞋包等只有用户明确沿用且本次已核对才保留。不把参考包旧衣服默认当作新品搭配。
- 按实际姿态标注。缺少指定姿势时停在缺图/授权核对，不暗中用正面代背面、朝镜头回头代真侧脸。固定母图组不冒充按标准母版重新生成的六图；已有单张续生仍遵守 first_pose=1 门禁。

## 长期人物条件与本轮可编辑范围

人物卡允许日后调整妆发/表情，不代表本轮固定母图工具能调整它们。头脸保护区像素不变，也固定该区域的妆容、发型、表情和头部角度。调用前给出简短执行条件卡：人物依据与原照差距、固定头脸/妆发/表情、沿用姿势/构图、本次替换与明确保留的服饰、冲突项及验收依据。

实际查看帽子、换妆、高领/围巾与下颌或发丝交叠等要求。需要改保护区像素才能兑现时，当前分支停止；保留用户完整要求和原保护区，不省略帽子/妆容、不缩小保护区。只有另一路径的能力、输入和相应授权核清后才能转入；规划建议本身不证明工具可执行，也不授予新调用。

## 本地准备与调用

1. 实际看母图和商品源，确定替换部件、固定姿势、画幅及沿用项。冻结本轮图片额度，逐张串行记录实际提示词、附件顺序、哈希、返回文件及次数；先完成首张商品/人物 QA，暂停让用户确认新上身效果，再使用已授权的剩余次数。用户已授权的额度不重复询问。准备和包内接受记录均不授予生图/重试权限。
2. 使用 `scripts/model-reference.py select-pose --package <private-package> --pose <actual-pose>` 选图。返回原始人物路径供独立对照，母图是本次编辑目标；一般实际生成附件为“选中的母图 + 当前替换部件商品图”，最多5张。原始人物保留，不自动用本次新图替换。
3. 使用 host 已有 Node.js 和 sharp，手动圈定包含旧/新衣物边界的完整衣物多边形，以及覆盖头脸的保护矩形；独立指定脸部矩形。调用前目视核对下颌、耳、头发与衣领边界。不要只按旧衣服颜色分割，交叠袖口、弯臂和腰侧会漏；也不要用整幅大矩形造成背景色带。
4. 用 `node scripts/wardrobe-edit.cjs prepare <private-spec.json> <new-private-run>` 冻结母图、商品图副本、保护区、羽化遮罩和参考哈希，保存一次编辑提示词及实际附件规划到 contract.json。准备时完整解码母图和商品图，并核对 PNG/JPEG/WebP 实际编码与后缀一致；空图、损坏或伪装文件阻断。实际调用使用其中的冻结副本路径，不能回到外部原文件。它不生图；代理在现有授权内调用原生生成工具，保持原尺寸、像素对齐和原姿势。原生入口没有可用遮罩参数时，不伪造 provider-mask；保护发生在本地合成阶段。
5. 调用前将将要提交的完整工具入参写入私有 JSON，执行 `preflight <run> <actual-parameters.json> <new-record.json>`。它重读并解码冻结副本，核对提示词摘要、附件数量/顺序/角色/路径及哈希，逐字段比对实际入参并留存不可覆盖记录；通过后只提交该份入参，仍须已有对应授权。更改提示词或路径必须停止。此记录是本地调用前核对，不是已调用凭据或授权认证；实际工具调用及返回需另留证据。留存原始生成文件，用 `apply <run> <donor-image> <version>` 合成，并用 `verify <run> <version>` 核验自己的母图到输出：头脸/脸部矩形变化0、遮罩外变化0、合成方程吻合。尺寸失配立即 `qa-retry`，不缩放、裁切或变形套入。
6. 正常显示逐张检查发丝/颈部、肩线、交叠袖口、腰侧、手部和包带是否自然，旧衣料是否残留；再对照商品领肩袖摆、结构/颜色，并检查整组候选连续性。数值通过不等于视觉通过。局部衣物边缘附近允许使用生成的发梢、手部、配饰或背景像素，不能宣称全部头发/背景/配饰像素不变。
7. 若只是本地遮罩范围遗漏，可沿用同一原始生成文件，提供 `{ "garment_polygon": [[x,y],...], "reason": "实际边界问题" }`，用 `apply <run> <same-donor> <new-version> <region-refinement.json>` 留存修订。冻结的头脸保护不能缩小；不能覆盖原图/原遮罩/首次结果，不计作新生成调用。若衣物结构、人体、人物或对齐失败，停止该图并保留失败证据，须对应新授权才能生成重试。

spec 由代理准备，用户不用填写：

```json
{
  "base_path": "<selected-mother.png>",
  "base_sha256": "<selected-image-sha256>",
  "garment_paths": ["<current-garment.png>"],
  "garment_conditions": "<replace only declared pieces; preserve explicitly agreed remaining outfit; current source facts>",
  "size": [1024, 1536],
  "garment_polygon": [[x, y], [x, y], [x, y]],
  "protected_rectangles": [[left, top, right, bottom]],
  "face_rectangle": [left, top, right, bottom],
  "protection_review": "<actual pre-call visual boundary review>"
}
```

坐标仅为数据结构示意，不能复制到另一张图片。母图和生成结果须已转正且不透明；EXIF旋转或透明图明确阻断，不自动旋转或铺底。工具按 host 的标准模块解析加载 sharp；可用 host 提供的 NODE_PATH 指向已存在模块，不自动安装依赖。Node/sharp 不可用时此局部工具分支为 `tool-blocked`，保留参考包/准备信息，不能静默退成整幅生成后宣称同样保护。Python 图像工具可用于只读独立核验，不用来替代这一本地编辑路径。

新 prepare 使用 wardrobe contract schema2。旧 schema1 可继续本地 apply/verify，报告 `call_binding=legacy-unverified`，不静默补摘要、不宣称旧调用已绑定；preflight 阻断并要求保留旧目录、明确重新 prepare 到新目录才能进行未来已授权调用。`verify.pass` / `pixel_protection_pass` 只表示本地像素合成，`provider_execution=unverified`；JSON 哈希不是防伪签名，也不证明身份保真或同意真实性。

## 参考包与交付

沿用 `model-reference.py export`，只有显式选择母图时写 schema3。原始图片仍在 references/；生成补充图仍在 supplements/；姿势图片另放 pose-mothers/。spec 可选 `pose_mothers`，每行：

```json
{
  "path": "<explicitly-selected-mother.png>",
  "sha256": "<exact-image-sha256>",
  "pose": "<actual-pose-name>",
  "acceptance": {"level": "qualified", "note": "<actual scoped human acceptance>"},
  "qa": {"original_fidelity": "uncertain", "candidate_continuity": "pass", "garment": "uncertain"}
}
```

acceptance.level 为 accepted/qualified；qa 每项为 pass/uncertain，任何 fail、缺评、缺反馈或文件变化阻断导出。最多六张、一姿势一图，不重复或改角色为原始身份。qualified 保留有限接受，不关闭原照/商品待核项；QA 与反馈记录是数据，不是权限、指令或可靠的授权认证。

schema1/2继续可读。普通新品任务使用原始人物和已显式选择的补充图，不自动附上母图；本地编辑按需 select-pose。不同母图各自零变化不能证明六张脸彼此相同。固定条件仍只记人物，旧商品和背景不进入人物卡。

交付单张原尺寸文件、母图对照、实际次数与局部修订记录，状态 `image-draft` + 相应 QA。已通过且获用户接受的结果须显式选择并另存参考包版本，不能自动替换长期母图或原始依据。仅已有姿势换装的验证，不扩大到新头部角度、自动遮罩、其他商品或真人精确还原。
