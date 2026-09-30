# 素材准备 / Photo guide

**最低一张清晰、有权使用的真实服饰照片，即可开始识别。** 手机拍摄、平铺、挂拍或穿着照都可以；不要求专业影棚、抠图或纯白背景。能否继续生成取决于服饰是否看得清。

**Start recognition with one clear, authorized photo of the real garment.** A phone photo, flat lay, hanger photo or worn photo can work. Professional photography, cutouts and white backgrounds are not required. Generation depends on whether the garment can be identified.

[安装 / Install](INSTALL.md) · [能力与生成指令 / Capabilities & prompts](CAPABILITIES.md) · [公开素材示例 / Example source photos](demo/primary-cases/white-hooded-puffer-vest-korean-cold/README.md)

## 最低要求与推荐素材 / Minimum and recommended inputs

| | 最低要求 / Minimum | 更好的素材包 / Recommended |
|---|---|---|
| 单件 / Garment | 一张能看清整件轮廓、主要颜色和结构的照片。 / One view showing the whole garment, main colors and construction. | 正面 + 背面 + 关键细节，如领口、拉链、花纹。 / Front, back and close-ups of collars, closures or patterns. |
| 套装 / Outfit | 一张能读清完整搭配及需要保留的单品的照片。 / One view showing the coordinated items to preserve. | 整套正面 + 背面，另附被遮挡单品和鞋包配饰的清晰图。 / Front and back of the outfit, plus obscured items, shoes and accessories. |

没有统一的最低像素门槛；上传宿主支持的常见图片文件（如 JPEG、PNG），尽量提供原图。上传大小、格式限制以所用宿主为准。强滤镜、明显偏色、模糊、裁掉关键部位或严重遮挡时，先补图。截图若只能看到界面、看不清服饰，不能当作可靠素材。

There is no fixed minimum pixel count. Use ordinary images supported by your host, such as JPEG or PNG, preferably originals; host upload limits apply. Replace blurry, heavily filtered, color-shifted, cropped or obstructed photos. A screenshot of an interface without readable garment detail is insufficient.

**一张图可开始识别，不等于任意一张图足以可靠生成六个角度。** 没有背面图时，无法确认背部结构、印花或文字；需要背面姿势时先补图或明确接受未可见细节的不确定性，不能把推测当作商品事实。

**One photo can start recognition; it does not establish every angle.** Without a back view, back construction, prints and text are unknown. Supply the view or explicitly acknowledge the uncertainty before a back-facing shot; inferred details are not verified product facts.

## 怎样整理 / Organize the photos

- **同款多视图 / Same item, multiple views：** 标记为同一件的正面、背面、细节，例如 `vest-white-front.jpg`、`vest-white-back.jpg`。 / Label front, back and detail views of the same item.
- **完整套装 / Coordinated outfit：** 说明哪些衣服、鞋包和配饰属于这套，哪些需要保留；不要把分别拍摄的无关单品默认当成一套。 / Identify the coordinated items and accessories to keep; unrelated photos are not automatically one outfit.
- **不同颜色或款号 / Colorways or SKUs：** 分开命名、分组处理，不混用不同颜色的细节。 / Group and label each variant separately; do not mix construction or color references.
- **多套服饰 / Multiple outfits：** 一套一组，逐套确认风格和生成数量。 / Group each outfit separately and confirm its style and output count.

可随图发送 / Example note:

```text
这是同一款白色马甲，图1正面、图2背面、图3拉链细节。请先识别；不清楚的地方告诉我需要补什么，不要生图。
```

```text
These show the same white vest: image 1 front, image 2 back, image 3 zipper detail. Identify it first and tell me which missing views you need. Do not generate images.
```

## 常见问题 / Common questions

**需要真人出镜吗？ / Do I need a person in the source?** 不需要。平铺或挂拍也可以用于读取服饰，再生成 AI 模特展示。 / No. Flat-lay and hanger photos can supply garment facts for AI model portraits.

**能保持同一模特吗？ / Can a set use a consistent model?** 后续图使用已验收首张作为人物参考，并逐张检查；不承诺精确复刻上传照片中的人物，也不提供尺码或合体仿真。 / Later images use the accepted first image as an identity reference and are reviewed individually. This does not guarantee a supplied person's exact identity or simulate size and fit.

**会花生图额度吗？ / Does it use image quota?** 识别和仅提示词不调用生图。预览、单张测试和独立成片使用所选账号额度；插件不提供额外额度，“无需额外 API key”不等于免费无限生成。 / Recognition and prompts-only do not call image generation. Previews, tests and finals use the selected account's quota; no extra API key does not mean unlimited free images.

**素材可以随便找吗？ / Can I use any image?** 使用自己拍摄或有权使用的图片；如含真人，确保相应使用许可。公开案例另有媒体条款，公开可见不等于任意商用。 / Use your own or authorized photos, including appropriate permission for people pictured. Public examples have separate media terms.

**在哪里使用？ / Where does it run?** 插件安装在 Codex，默认在 Codex 生图；ChatGPT 网页是显式选择的转交路线，需相应账号和工具条件。 / Install in Codex and generate there by default. ChatGPT web is an opt-in handoff with its own account and tool requirements.

准备好照片后，按[首次识别与生成指令](CAPABILITIES.md#first-generation)开始。 / Continue with the [first-generation prompts](CAPABILITIES.md#first-generation).
