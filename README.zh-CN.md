# 裁光 · Caiguang

**AI Fashion Studio · 服饰 AI 影棚**

**当前预发布版：beta.11。** 在 Codex 中显示为“裁光 · Caiguang”，调用名仍为 `$threadtruth-studio`。请使用[对应版本的试用指南](docs/BETA11-TRYOUT.md)；新环境实测和稳定版验收仍待完成，旧版资产保持不变。

[![裁光 · Caiguang — AI Fashion Studio。米色套装参考图与 AI 生成效果。](https://denggui-ai.github.io/threadtruth-studio/assets/brand/og-home.png)](https://denggui-ai.github.io/threadtruth-studio/)

**单件或整套服饰，生成六姿势 AI 模特图，24 种风格可选。**<br>Turn a garment or coordinated outfit into six-pose AI model portraits. Choose from 24 styles.

**[下载裁光插件 · Download Caiguang](https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.11)**　·　**[开始安装 · Install](docs/INSTALL.md#简体中文)**　·　**[查看成片 · See results](https://denggui-ai.github.io/threadtruth-studio/#reviewed-cases)**　·　**[探索 24 风格 · Explore styles](https://denggui-ai.github.io/threadtruth-studio/#style-highlights)**

[English guide](README.md) · [中文说明](README.zh-CN.md) · [产品首页 / Website](https://denggui-ai.github.io/threadtruth-studio/)

## 单件和套装，都能拍一组

上传一件服饰或一套完整搭配，选择 24 种风格中的一个主风格，生成默认六姿势的**六张独立图片**。首张验收后继续，其余图片沿用人物参考以保持组内一致；不保证复刻上传照片中的真人。24 风格可选不代表一次生成 24 组。

正面及前侧清楚但缺背面资料时，第六张明示改为正面自然站姿，前五姿势保留，仍为六张独立图；要求准确背部结构时须补实拍。

[素材怎么准备](docs/INPUT-GUIDE.md) · [六姿势与生成指令](docs/CAPABILITIES.md#six-poses) · [单件 24 风格预览](docs/demo/style-previews/white-vest-24-v1/) · [套装 24 风格预览](docs/demo/style-previews/beige-blazer-denim-outfit-24-v1/)

以上两套是历史方向预览，每个风格一张六宫格，均不是六张独立成片。现新增 [六组六图穿搭案例](https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html)：红花裙、浅绿衬衫家居搭配，拼色 T 恤的两种风格，外部 Codex 用户的黑色外套搭配，以及同款通勤窗光案例，共 36 张独立 AI 图。各组验收范围分别披露。

## 为什么选择裁光

**让真实服饰，成为每一次创作的依据。**

- **细节有依据，成片可对照。** 先读颜色、结构与搭配，再对照源图逐张确认，让你知道该看哪些细节。[查看六姿势成片](https://denggui-ai.github.io/threadtruth-studio/#reviewed-cases)。
- **一套服饰，探索多种方向。** 从电商棚拍到品牌大片，在 24 种风格中寻找适合这套服饰的表达。[看同套服饰的三种风格](https://denggui-ai.github.io/threadtruth-studio/#outfit)。
- **先测一张，再决定是否继续。** 先看方案或只要提示词；选好方向后，授权测试一张，再决定是否继续生成。[先做一次识别](#三步开始)。

## 你可以用它做什么

- **识别服饰。** 从单件、套装或多角度照片读取可见细节。
- **选择方向。** 查看推荐，或从完整 24 风格中自主选择。
- **设置拍摄。** 选择棚拍、场景或混合，以及输出形式和画幅；其他输出形式的公开验证有限。
- **选择产物。** 单张测试、标注为非成片的方向预览、六张独立图，或仅输出提示词。
- **选择入口。** 默认在 Codex 生成，也可请求 ChatGPT 网页转交；自动执行依赖宿主浏览器工具。
- **检查与修正。** 对照源图、检查尺寸，按需要明确授权单张重试。

[完整能力、可复制指令与验证范围 →](docs/CAPABILITIES.md)

裁光插件安装在 **Codex** 中，beta.11 预发布版显示为 **裁光 · Caiguang**，旧版 beta.8 安装仍显示为 **ThreadTruth Studio**。默认在 Codex 生图；也可明确选择下方说明的 ChatGPT 网页转交路线。

## 三步开始

**需要准备：** macOS、Python 3、终端，以及支持 `codex plugin add` 的 Codex CLI。目前只有这一环境经过测试；Windows、Linux 和全新机器尚未验证。首次识别不生成图片；之后生图需要具备原生生图能力的 Codex 账号，选择网页路线时则需要有生图权限的 ChatGPT 账号。

1. 按[中文安装指南](docs/INSTALL.md#简体中文)下载 beta.11 插件 ZIP 与匹配的 `.sha256`，检查环境、校验归档并启用插件。请选择有完整插件名称的下载项，不要使用 GitHub 自动生成的源码 ZIP。
2. 新建一个 **Codex 任务**，上传你有权使用的真实单件服饰或完整套装照片。
3. 先请求识别与风格推荐：

```text
请用 $threadtruth-studio 识别并推荐风格，不要生图
```

预期返回服饰识别卡、主推与备选方向，以及完整的 24 风格目录。这一步**不授权生图**。随后确认风格、构图、尺寸和张数，再明确授权生成；生图会使用所选账号的图片额度。

没有返回识别结果时，先看[安装排查](docs/INSTALL.md#安装排查)。安装成功或失败都可通过[安装反馈表](https://github.com/denggui-ai/threadtruth-studio/issues/new?template=installation-feedback.yml)简短反馈。

## 选择在哪里生图

| 入口 | 使用方式 | 需要什么 |
|---|---|---|
| **Codex · 默认** | 授权后在 Codex 内生成，首张通过检查后再继续套组。 | 宿主具备原生生图能力，账号有可用额度。 |
| **ChatGPT 网页 · 明确选择** | Codex 准备编号参考图与提示词，由你手动转交，或授权 Codex 操作受支持的浏览器。 | ChatGPT 账号有生图权限和额度；自动执行还需要宿主提供上传文件、下载原图的浏览器工具。 |

裁光安装在 **Codex** 中。ChatGPT 入口按[网页教程](docs/CHATGPT-WEB-TUTORIAL.md)转交，安装插件本身不会安装浏览器工具。参考图上传 ChatGPT 需要授权；失败或状态不明时先检查原请求，重试须另行授权，已用次数会保留。[网页流程说明](docs/CHATGPT-WEB.md)。

## 案例与验证范围

**六组案例，共 36 张独立图。** [查看全部成片与来源说明](https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html)。红花裙、家居搭配的视觉方向已验收；两组 T 恤保留人工细节与动作复核。可用于穿搭效果预览，人物是 AI 模特，不承诺本人身份、实际尺码或合体效果。

**商品参考 → AI 场景穿搭。** 下图展示本次实际使用的衬衫、裤装主要参考与家居成片；裤装仅局部展示，另有结构和人物参考。外部 Codex 用户也已完成六图试用并反馈满意；其使用版本未知。

<a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#green-shirt-home"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/green-shirt-home/before-after.jpg" alt="Product references and AI home-scene result / 商品参考与 AI 家居成片" width="480"></a>

[查看家居 Before / After、六张原图与来源说明](https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#green-shirt-home)

**一张搭配图 → 六张通勤场景图。** 同一张已授权输入也用于外部试用；对照两种呈现方向，不作为版本升级前后的效果证明。缺少背面实拍，第六张采用正面自然站姿；细小服饰结构保留人工核对。

| 实际输入 | AI · 通勤窗光 |
|---|---|
| <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#black-jacket-office"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/black-jacket-office/input.jpg" alt="实际授权搭配输入" width="240"></a> | <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#black-jacket-office"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/black-jacket-office/look-1.png" alt="AI 生成的皮衣通勤搭配" width="240"></a> |

[查看两种方向、新六张与验收范围](https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#black-jacket-office) · [下载案例分享素材](https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/black-jacket-office/share/caiguang-black-jacket-share.zip)

| | | | | |
|---|---|---|---|---|
| <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#black-jacket-office"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/black-jacket-office/look-1.png" alt="通勤窗光 — AI-generated" width="150"></a><br>通勤窗光 · 同款对照 | <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#red-floral-french"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/red-floral-french/look-1.png" alt="红花裙 — AI-generated" width="150"></a><br>红花裙 | <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#green-shirt-home"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/green-shirt-home/look-1.png" alt="家居搭配 — AI-generated" width="150"></a><br>家居搭配 | <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#trim-tee-american"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/trim-tee-american/look-1.png" alt="美式街头 T 恤 — AI-generated" width="150"></a><br>美式街头 T 恤 | <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#trim-tee-japanese"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/trim-tee-japanese/look-1.png" alt="日系生活 T 恤 — AI-generated" width="150"></a><br>日系生活 T 恤 |

[案例记录与媒体说明](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/SHOWCASE-CASES.md)。

[![真实白色马甲源图，以及六张独立生成的韩系冷感 AI 人像](docs/demo/primary-cases/white-hooded-puffer-vest-korean-cold/hero.jpg)](docs/demo/primary-cases/white-hooded-puffer-vest-korean-cold/README.md)

**4 张源图 → 6 张独立 AI 人像。** 这组历史案例已完成人工验收，与配对图库分开记录，也不是 beta.8 新生成的结果。[查看完整案例与媒体条款](docs/demo/primary-cases/white-hooded-puffer-vest-korean-cold/README.md)。

**24 风格配对图库**展示 Codex 与 ChatGPT 网页端的结果，附来源署名、权利披露和逐组评审。图片为 AI 合成研究对照，不代表模型排名，也不代表每张图片均可自由复用。[查看图库来源与权利记录](https://denggui-ai.github.io/threadtruth-studio/rights.json)。

| 集合 | 已公开内容 | 能说明什么 |
|---|---|---|
| [新增穿搭案例](https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html) | **6 组 × 6 张独立图 = 36 张** | 分别记录视觉验收与待复核项；不计入旧版冻结的风格索引。 |
| [配对比较图库](https://denggui-ai.github.io/threadtruth-studio/compare.html) | **24 风格 × 2 个入口 = 48 张图片** | 同一输入的结果对照，含评审与权利披露；不等于 24 套完整六图交付，也不代表 beta.8 全风格验证。 |
| [白马甲完整案例](docs/demo/primary-cases/white-hooded-puffer-vest-korean-cold/README.md) | **1 种风格 × 6 张独立成片** | 一组完成人工验收的完整案例；旧版冻结主案例风格索引为 **1/24**。 |
| 历史方向预览 | **2 个集合 × 24 种风格** | 每种风格一张六姿势看板，经过版式检查与维护者验收；保留白马甲 beta.3、套装 beta.4 的原始证据。 |

<details>
<summary>展开历史单件服饰与完整套装预览</summary>

| 真实完整套装源图 | AI 合成的六姿势方向预览 |
|---|---|
| <img src="docs/demo/preview-sources/beige-blazer-denim-outfit/source.jpg" alt="米色西装完整搭配的真实源图" width="300"> | <img src="docs/demo/style-previews/beige-blazer-denim-outfit-24-v1/ecommerce-studio-display.jpg" alt="同一套米色西装搭配的 AI 六姿势方向预览" width="700"> |

**完整套装 · 24种风格** — 米色西装、白色上衣、深色牛仔裤、橄榄色托特包和棕色乐福鞋作为一套搭配锁定。此处是一张预览看板。[查看套装全部 24 张看板](docs/demo/style-previews/beige-blazer-denim-outfit-24-v1/)（GitHub 上列出图片文件；目录中的 `index.html` 是供下载后本地打开的图库页） · [媒体权利](docs/demo/RIGHTS.md)。

**单件服饰 · 24种风格** — 下方缩略图来自冻结的白马甲集合，点击可查看单张六姿势大图。[风格证据索引](docs/demo/STYLES.md) · [历史任务台账](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/WORK-STATUS.md)。

<!-- STYLE_PREVIEWS:START -->

| | | | |
|---|---|---|---|
| <a href="docs/demo/style-previews/white-vest-24-v1/american-street-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/american-street-thumb.jpg" alt="American Street — six-pose layout preview, not finals" width="180"></a><br>American Street | <a href="docs/demo/style-previews/white-vest-24-v1/athleisure-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/athleisure-thumb.jpg" alt="Athleisure — six-pose layout preview, not finals" width="180"></a><br>Athleisure | <a href="docs/demo/style-previews/white-vest-24-v1/balletcore-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/balletcore-thumb.jpg" alt="Balletcore — six-pose layout preview, not finals" width="180"></a><br>Balletcore | <a href="docs/demo/style-previews/white-vest-24-v1/british-heritage-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/british-heritage-thumb.jpg" alt="British Heritage — six-pose layout preview, not finals" width="180"></a><br>British Heritage |
| <a href="docs/demo/style-previews/white-vest-24-v1/cityboy-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/cityboy-thumb.jpg" alt="Cityboy — six-pose layout preview, not finals" width="180"></a><br>Cityboy | <a href="docs/demo/style-previews/white-vest-24-v1/clean-fit-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/clean-fit-thumb.jpg" alt="Clean Fit — six-pose layout preview, not finals" width="180"></a><br>Clean Fit | <a href="docs/demo/style-previews/white-vest-24-v1/coquette-ladylike-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/coquette-ladylike-thumb.jpg" alt="Coquette Ladylike — six-pose layout preview, not finals" width="180"></a><br>Coquette Ladylike | <a href="docs/demo/style-previews/white-vest-24-v1/ecommerce-studio-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/ecommerce-studio-thumb.jpg" alt="E-commerce Studio — six-pose layout preview, not finals" width="180"></a><br>E-commerce Studio |
| <a href="docs/demo/style-previews/white-vest-24-v1/french-effortless-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/french-effortless-thumb.jpg" alt="French Effortless — six-pose layout preview, not finals" width="180"></a><br>French Effortless | <a href="docs/demo/style-previews/white-vest-24-v1/gorpcore-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/gorpcore-thumb.jpg" alt="Gorpcore — six-pose layout preview, not finals" width="180"></a><br>Gorpcore | <a href="docs/demo/style-previews/white-vest-24-v1/guochao-street-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/guochao-street-thumb.jpg" alt="Guochao Street — six-pose layout preview, not finals" width="180"></a><br>Guochao Street | <a href="docs/demo/style-previews/white-vest-24-v1/italian-luxe-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/italian-luxe-thumb.jpg" alt="Italian Luxe — six-pose layout preview, not finals" width="180"></a><br>Italian Luxe |
| <a href="docs/demo/style-previews/white-vest-24-v1/japanese-lifestyle-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/japanese-lifestyle-thumb.jpg" alt="Japanese Lifestyle — six-pose layout preview, not finals" width="180"></a><br>Japanese Lifestyle | <a href="docs/demo/style-previews/white-vest-24-v1/korean-cold-editorial-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/korean-cold-editorial-thumb.jpg" alt="Korean Cold Editorial — six-pose layout preview, not finals" width="180"></a><br>Korean Cold Editorial | <a href="docs/demo/style-previews/white-vest-24-v1/korean-menswear-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/korean-menswear-thumb.jpg" alt="Korean Menswear — six-pose layout preview, not finals" width="180"></a><br>Korean Menswear | <a href="docs/demo/style-previews/white-vest-24-v1/neo-chinese-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/neo-chinese-thumb.jpg" alt="Neo Chinese — six-pose layout preview, not finals" width="180"></a><br>Neo Chinese |
| <a href="docs/demo/style-previews/white-vest-24-v1/nordic-minimal-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/nordic-minimal-thumb.jpg" alt="Nordic Minimal — six-pose layout preview, not finals" width="180"></a><br>Nordic Minimal | <a href="docs/demo/style-previews/white-vest-24-v1/office-commute-women-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/office-commute-women-thumb.jpg" alt="Office Commute Women — six-pose layout preview, not finals" width="180"></a><br>Office Commute Women | <a href="docs/demo/style-previews/white-vest-24-v1/old-money-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/old-money-thumb.jpg" alt="Old Money — six-pose layout preview, not finals" width="180"></a><br>Old Money | <a href="docs/demo/style-previews/white-vest-24-v1/preppy-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/preppy-thumb.jpg" alt="Preppy — six-pose layout preview, not finals" width="180"></a><br>Preppy |
| <a href="docs/demo/style-previews/white-vest-24-v1/quiet-luxury-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/quiet-luxury-thumb.jpg" alt="Quiet Luxury — six-pose layout preview, not finals" width="180"></a><br>Quiet Luxury | <a href="docs/demo/style-previews/white-vest-24-v1/resort-vacation-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/resort-vacation-thumb.jpg" alt="Resort Vacation — six-pose layout preview, not finals" width="180"></a><br>Resort Vacation | <a href="docs/demo/style-previews/white-vest-24-v1/workwear-vintage-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/workwear-vintage-thumb.jpg" alt="Workwear Vintage — six-pose layout preview, not finals" width="180"></a><br>Workwear Vintage | <a href="docs/demo/style-previews/white-vest-24-v1/y2k-millennium-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/y2k-millennium-thumb.jpg" alt="Y2K Millennium — six-pose layout preview, not finals" width="180"></a><br>Y2K Millennium |

<!-- STYLE_PREVIEWS:END -->

历史预览的来源、评审与哈希记录继续保留，不作为当前运行时视觉质量、新增完整案例或非维护者采用的证明。

</details>

## 适用范围与限制

裁光 · Caiguang 由社区独立维护，不是 OpenAI 官方产品，也不代表官方背书。安装与启用已在维护者的 macOS 本机验证，非维护者新环境仍待验证。详见[兼容性与验证范围](docs/COMPATIBILITY.md)。

- **以源图细节为依据。** 颜色、材质观感、廓形、结构、图案和 Logo 位置来自源图；完整套装还包括层次、比例及鞋包配饰。生成后仍需对照源图检查，不能保证小字、Logo 或合体效果完全准确。
- **交付需要人工验收。** 适用于 AI 模特服饰展示，不承诺指定真人身份换装或 CAD 合体模拟；不用于非服饰商品、纯文字概念图、API 集成或无人值守商业交付；不保证平台审核通过或销售效果。
- **风格名称只描述视觉方向。** 带性别或文化名称的风格，不用于推断人物身份、族裔、国籍、身体或性别。
- **使用有授权的素材，单独核对图片权利。** 生成结果需要适用的 AI 内容标识；图库公开不表示第三方权利已全部清理，应查看逐组披露。Apache-2.0 覆盖代码和文档，不覆盖演示媒体。
- **生图能力由所选宿主提供。** 插件不增加 API key 流程、第三方生图服务、MCP 服务或遥测。工具不可用时仍可识别和准备提示词，生图暂停；也可明确选择网页转交入口。

## 文档与反馈

[安装、升级与回滚](docs/INSTALL.md) · [兼容性](docs/COMPATIBILITY.md) · [离线指南](USER-GUIDE.html)（随插件 ZIP 提供，请在本地用浏览器打开；GitHub 上只显示 HTML 源码） · [更新记录](https://github.com/denggui-ai/threadtruth-studio/blob/main/CHANGELOG.md) · [Beta 进度](docs/BETA.md)

**当前预发布版：beta.11。** 纳入可选选角、审美参考转译、首张选角验收与服饰优先规则；只要提示词时首回复也先核对输入；保留 ChatGPT 网页转交与受控重试。旧版本和对应图库作为历史记录保留；安装旧版时使用其归档内的指南。Beta 退出目标与待验证事项见 [Beta 登记](docs/BETA.md)。

安装结果可通过[反馈表](https://github.com/denggui-ai/threadtruth-studio/issues/new?template=installation-feedback.yml)提交；Bug 使用 [Issues](https://github.com/denggui-ai/threadtruth-studio/issues)，一般问题使用 [Discussions](https://github.com/denggui-ai/threadtruth-studio/discussions)。公开反馈前请去除私有服饰图、客户数据、凭据和完整日志。维护者：DENGGUI · 微信：`Lvmusic0930`。

<details>
<summary>开发与项目记录</summary>

```bash
python3 -m unittest discover -s tests -v
python3 tools/pack-lint.py --strict skills/threadtruth-studio/references/styles/*.pack.yaml
python3 tools/trigger-eval.py
python3 tools/build-release.py
```

运行时位于 `skills/threadtruth-studio/`；测试、eval、发布工具和证据位于其外。另见[贡献指南](CONTRIBUTING.md)、[安全策略](SECURITY.md)、[迁移说明](MIGRATION.md)与[来源记录](PROVENANCE.md)。项目 Beta 目标不属于 OpenAI 准入规则，申请说明单独保存在 [Codex for Open Source](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/CODEX-FOR-OSS.md)。

</details>
