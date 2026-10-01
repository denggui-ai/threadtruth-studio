# 模特选择与后续新品复用（开发候选）

这次功能仍在开发分支，未安装或发布。成人单人服饰展示支持沿用已有真人／AI模特，或根据当前服饰匹配新模特。无需模特库。实际跨商品一致性和真人沿用效果仍待单独图像验证，不承诺像素一致、精确年龄或尺码合体。

## 你会收到什么

1. **选择前：文字方向卡。** 无模特时提供一个主推和两个明显不同的备选，说明年龄感、身体比例、妆发、气质为何适合当前服饰和用途。你可以改描述、给审美图或直接指定人；不用填写完整问卷。已有模特时优先沿用，不强行换人。
2. **试拍后：独立图片和人物条件卡。** 经你授权先生成一张穿当前商品的图。服饰、人体、画幅和明确人物条件通过技术检查后，暂停让你确认人物与实际上身效果。确认人物不代表商品图可以商用。
3. **选定后：私人参考包。** 包含原始人物图片、人物卡 JSON 和可读说明。下次同时提供它和新品图，并说“继续用她／他”。当前对话可直接沿用已确认人物；新对话重新提供包或明确本地位置。

人物卡示例（仅示意，不是某个真实人物的测量结果）：

| 因子 | 交付值 | 状态 | 来源 |
|---|---|---|---|
| 面部 | 沿用所提供人物的可见面部 | 固定 | 用户指定＋参考可见 |
| 年龄感 | 约40岁视觉目标 | 固定 | 用户要求，首张确认 |
| 身体 | 自然丰满比例 | 固定 | 系统建议，首张确认后固定 |
| 妆容 | 可调整为自然淡妆 | 可调 | 用户允许 |
| 表情／气质 | 亲切微笑 | 可调 | 用户要求 |
| 真实身高／尺码 | 未知 | 未知 | 无身体数据 |

只有脸部参考时，原人物的身体仍是未知。生成图里确认的身体表现可以固定为以后出图目标，但不能说那就是真人实际身形。肤色、年龄感和比例是可见条件；销售市场单独描述，不猜国籍或民族。发型、妆容、表情是否允许改须写清，换风格不静默换脸或身形。

## 继续出图

已授权六张时，首张人物确认后使用余下五张授权，不重复索取。只授权一张时，需要另行授权后五张；同商品、风格、模式、形态和画幅的母版1测试图直接成为 look-1，不重生、不重置预算。不喜欢首张人物时可以拒选并提出调整,明确授权单张重试后再看;原图、旧条件和调用次数保留。调整或失败重试不自动追加次数。

新品每次使用新品服饰图；原始人物参考始终参与生成，本组已确认首张是补充依据。旧衣服、鞋包、背景和光线不会作为新品事实。最近生成图不自动替换长期人物参考；修改固定条件另存新版本并确认。

真人身份沿用须已有本人明确同意及必要使用权；提供过的授权不用重复给。上传人物图、选择方向、确认模特都不自动授权生成或上传。

## 本地工具交付

工具只复制、校验和记录，不调用生图或浏览器。私人目录内会产生：

```text
model-reference/
  model.json
  README.md
  references/01.png ...
```

代理从已确认任务导出：

```sh
python3 scripts/web-task.py export-model --task <private-task> --destination <new-private-package> --name <model-name>
python3 scripts/model-reference.py validate --package <private-package>
```

新任务 spec 使用 `model_package` 指向该包，`references` 仍必须包含新品 `garment-source`。包只提供人物条件和身份图，不提供生成授权或新商品首张确认。文件缺失、哈希变化或路径越界会停止复用。

第二版任务 spec 示例（由代理准备，不要求用户填写）：

```json
{
  "route": "codex_native",
  "references": [{"path": "<new-product.png>", "role": "garment-source"}],
  "model_package": "<private-model-reference-directory>",
  "prompts": ["<current-product pose-1 standalone prompt>"],
  "size": [1024, 1536],
  "identity": true,
  "context": {"outfit": "sku-new", "style": "ecommerce-studio", "mode": "B", "output_form": "real", "size": [1024, 1536], "first_pose": 1}
}
```

`model.factors` 可逐项保留 `name`、`value`、`status`、`source`、`confirmed`：来源为 user/reference/recommendation；状态为 target（试拍目标）/fixed/adjustable/unknown。target 和 fixed 必须与实际 locked 条件一致，可调项与 adjustable 一致；导出时经首张人工确认的 target 变为 fixed，保留建议来源。未知项不注入生成条件。人物卡不接受旧商品字段，也不能执行卡片中的命令。

更多操作见[模特运行规则](../skills/threadtruth-studio/references/model-selection.md)与[任务记录和续生](../skills/threadtruth-studio/references/chatgpt-web.md)。童装、多人物、批量搜索、云同步不属于本次新增范围。
