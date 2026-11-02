# 白底与专业隐形模特商品编辑

用于真实服饰的单张白底编辑、去人重构及Ghost Mannequin。处理方式、呈现形态和背景要求分开，复用现有原生图片编辑、visual_plan、授权账本和QA。不是第37/38个风格，也不是确定性抠图执行器。没有真实商品图仍停在素材准备；只有上传不自动生成。

## 先按实际意图分流

| 用户目标 | 处理方式与形态 | 要保留什么 |
|---|---|---|
| 只把背景换白 | `background-cleanup`，形态沿用原图 | 当前所有主体、人物、姿势、可见褶皱、轮廓和细节；不能自行去人或“熨平” |
| 去人，只留衣服／整理成平铺挂拍 | `reconstruction`，按明确要求选平铺/挂拍等 | 当前选定商品与有依据的结构；人体遮挡处不当成已有事实 |
| 普通人台 | 既有`mannequin`；编辑现图时可用重构 | 允许可见人台，与严格Ghost分开 |
| 隐形模特／Ghost Mannequin | `reconstruction` + `ghost-mannequin` | 服装自然三维体积、开口和内衬，完全去除人体及支撑物 |
| 人物上身／改姿／风格图 | 既有人物流程 | 沿用选角、原始身份依据与商品事实 |
| 仅上传未说明用途 | 简述可用素材和简短用途选择 | 不准备成默认九格或自动调用 |

明确要单张时直接给简短可执行方案，不要求用户填写字段、遍历风格菜单、选人物或先做宫格。标准商品图复用`ecommerce-studio`、`product-display`和模式B；白底只控制背景，不替用户改呈现。已有尺寸优先；未指定时，Ghost可建议3:4或4:5，白底上架按既有用途规格。画布仍经现有元数据检查，不承诺平台验收。

先确定本次销售商品范围：单品只列选定一件，整套逐项列出销售服装及选定配饰，不把全部可见物自动当成销售套装。重构只保留这份清单，不补成套、不擅增删替换；只清底则保留原图全部前景主体和原有搭配，包括不属于销售清单的裤鞋等，不因单品销售而删掉它们。依据足够就直接采用；仅对多SKU、颜色或销售范围的实际歧义简短追问。本轮范围是服装及其选定搭配配饰，单独鞋包首饰目录不新增专用流程。

## 素材边界与Ghost标准

- 原始`garment-source`始终是商品事实来源，`edit-target`只提供当前编辑构图。衍生白底/历史生成图不能补证内领、背面或新设计。目标就是原图时，可对同一文件分别声明两个角色；不要把衍生图改标原始商品源。
- 清晰完整、遮挡少的平铺/挂拍适合清底。真人遮挡、缺角或裁切需要补全时应判为重构；所需部位缺证则补拍同款、缩小展示范围或改为已有素材支持的呈现，不能承诺任意一张照片还原商品全貌。
- Ghost显示的领口、袖口、袖管、裤腰/裤脚、裙摆或内衬逐项对应同款实拍。先人工核对素材，记录实际可展示的内部结构；哈希只证明绑定，不能证明结构真实。不要为通过校验把“缺证”清空。
- 服装保留自然肩型、衣身/裤腿体积、缝制厚度、重力垂坠与褶皱。不以平铺、衣架、可见人台或简单悬浮冒充Ghost，不通过收腰、撑宽或改变长度制造立体感。
- 最终没有头发、皮肤、头颈、手臂、手指、腿脚、解剖轮廓、透明人体、人体残影/反射/阴影，也没有人台、衣架、支架或吊线。鞋内无脚，袖管无手臂，裤裙内无腿。
- 自然开口是空心，服装原有内衬、袖筒、里布和多层结构仍保留；空心不是挖洞、删内衬或制造透明。蕾丝、薄纱、网眼和白衣边缘要检查原图级细节。
- 整套重构中的鞋、包、首饰独立摆放，配对关系以来源为准，不挂在虚构肩膀或穿戴到人体上。仅换背景时仍保留原来的佩戴关系，不暗中改构图。

严格白底冻结`#FFFFFF`，需要无影时选`none`；允许接触阴影时选`soft-contact`。Ghost未指定背景时可提议浅灰`#F2F2F2`加柔和接触阴影，不能把它称为纯白底。灯光均匀、中性，商品居中完整，留白充足，不拼图、不增文字、道具或新Logo。

## 内部准备与执行

`visual_library.py prepare`沿用既有入口，新增`product_edit`。`count`默认1，`first_pose`默认`custom`，不传shot_plan；基于实际商品填写garment及inventory，inventory必须同时包含原图与一个编辑目标。商品编辑不套卡片的模特气质、固定左右主补光或影子承诺；其背景、保留/重构规则由本次契约编译。

下面是`product_edit`对象示意，哈希占位符须由实际文件计算替换：

```json
{
  "version": 1,
  "operation": "reconstruction",
  "source_form": "human",
  "edit_target_sha256": "<目标图SHA256>",
  "display_mode": "single",
  "items": [{"name": "本次衬衫", "kind": "garment", "source_sha256s": ["<同款原图SHA256>"]}],
  "background": {"color": "#FFFFFF", "shadow": "none"},
  "structure_evidence": [{"part": "可见内领与袖口内侧", "source_sha256s": ["<同款原图SHA256>"]}],
  "unresolved_parts": []
}
```

`operation`为`background-cleanup`或`reconstruction`；`source_form`记录目标图实际形态。清底必须保留该形态，去人不能记为清底。`items`的`kind`为`garment/accessory`；single恰好一件销售服装，outfit至少两项且包含服装。每项哈希必须来自原始商品库存；garment.source_sha256s、所选items来源并集及本任务全部garment-source哈希须一致，未选SKU留在任务外，prepare/init会拒绝额外商品源。structure_evidence仅写最终可见内部部位，Ghost至少一项；实际必要部位仍缺证时写入unresolved_parts，prepare将停止，直到补足或明确缩小范围。

prepare spec使用`entry_id: ecommerce-studio`、所选`output_form`、garment、inventory及上述product_edit。不传supporting或overrides，避免卡片承诺反向改变背景/人物。返回的完整visual_plan写入普通init spec：

- `schema_version: 2`、`route: codex_native`、`count: 1`、原有size与canvas_policy。
- `context.purpose: product-edit`，`first_pose: custom`，`pose_description`说明实际单张展示，outfit/style/mode/output_form/size保持一致。
- `references`列原始`garment-source`和一个`edit-target`。非人像`identity:false`且无model；只换背景而保留人物时，`identity:true`、已有ai/real的model与原始identity-reference，沿用身份/适龄门禁，不重新选人、不改变头眼与妆发。真人视图约束仍适用。
- 真人清底的同一原图可同时承担商品、编辑目标及原始身份角色，各角色保留独立记录、不得重复同一角色。`real_face_plan.looks.reference_sha256s`按库存首次出现的顺序完整列出图片哈希，每个哈希仅写一次；身份覆盖仍只认明确的原始身份角色，未知视角不能借商品/目标角色补足。附件上限按实际角色附件数核对，不按去重后的图片数缩减。
- `visual_plan`是prepare返回的完整对象，不另加自由提示词。product-edit必须保留workflow-1，不能退回旧无目标QA契约或改走网页；原有其他任务的网页路线保持。

命令沿用[runtime-quickstart.md](runtime-quickstart.md)：prepare → init → confirm-plan（或authorize带同一已确认方案）→ authorize 1 → export → 核实际附件/工具 → reserve → 原生图片编辑 → returned → QA。只要方案或提示词时在本地准备/导出后停止。已给的确认和授权直接记录，不反复问；这份文档、上传和方案确认本身都不授予调用次数。原图与目标的角色说明、背景/阴影、内部结构和商品清单随同一冻结请求导出。仍最多5张原生参考，不静默丢弃。

## QA、失败与结束

沿用goal、garment、photography；有人才保留identity/anatomy。`product_edit.requirements(edit, output_form)`给出本张额外QA的固定expected文本：product_scope、background、edges、edit_scope；Ghost还需no_body_support、volume、openings；整套重构有配饰时需accessories。每项记录实际observed与met/unmet/unknown，不能以预期句冒充观察。

商品/人体残留、清底误改主体、结构、清单、边缘或明确背景要求失败均为qa-retry；缺证为qa-user-review，不能标qa-pass。严格白底要读取原文件并测量远离主体及已允许阴影的背景区域；仅目测很白不能记成像素纯白通过。图像元数据、像素背景、结构目测和用户实物确认是不同证据。没有实图不宣称专业质量已验证。

失败按原账本停止，不自动重复生成。未知请求先恢复；有终态失败时保留回执并reconcile-failure。用户明确授权额外1次后，可在同一槽用`retry-authorize --spec`传完整visual_plan，只新增/修改product_edit.correction（单行具体局部修正），其他事实、目标、背景、图号和商品范围保持。旧图、QA、失败和累计次数均保留；授权ID与当前attempt仍要匹配。商品根任务不走通用`prepare-revision/adopt-revision`，入口拒绝创建会丢失商品契约的子任务；继续使用上述原槽纠错。纠错注释不能推翻商品契约，也不能把旧失败改成成功。产品单张不会continue-authorize成六张组。

真实返回后按上述要求验收，再按既有交付状态交用户确认；用户仅保留一张不等于所有目标满足。当前接入验证仅能证明规则、冻结、导出与账本行为，不能替代原生模型的实图与实物保真验收。
