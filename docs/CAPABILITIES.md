# 裁光能力与用法 / Capabilities & usage

从真实服饰照片开始，先识别、选方向，再决定是否生成。本文说明**beta.12** 的工作流与条件，包含缺背面时的第六张替代规则；不承诺所有功能组合都已实测。

Start with real garment photos, identify the source and choose a direction before generating. This guide describes the **beta.12** workflow and its conditions. It includes the front-only slot-6 substitution rule; it does not claim every combination has been tested.

[开始安装 / Install](INSTALL.md) · [产品首页 / Website](https://denggui-ai.github.io/threadtruth-studio/) · [24 风格样例 / Style examples](https://denggui-ai.github.io/threadtruth-studio/#style-highlights) · [兼容性 / Compatibility](COMPATIBILITY.md)

默认一份人物、风格、用途和张数方案，一次明确确认后执行；已有授权沿用，图片优先展示，单张满意即结束。人物因子、备选和完整目录按需展开。模特参考包与受限局部换装见[模特复用](MODEL-REUSE.md)。

## 单件、套装与六姿势 / Garments, outfits and six poses

单件服饰和完整套装都可以生成 AI 模特上身展示。两者均可从 24 风格中选择一个主风格，按默认六姿势生成六张独立图片；不是指定真人换装或尺码合体仿真。套装同时关注单品、层次、比例及鞋包配饰。单件上装所需的补全搭配应在方案中确认，不当作源图事实。

Both a single garment and a coordinated outfit can become AI model portraits in one of 24 styles. A full set contains six independent images; it is not a supplied-person identity or fit simulation. Outfits preserve the identified items, layers, proportions and accessories. Complementary styling for a single top is confirmed in the plan, not treated as source evidence.

<a id="six-poses"></a>

| 默认姿势 / Default pose | 英文 / English |
|---|---|
| 1. 侧身回转站姿 | Side-turn standing |
| 2. 侧身倚靠墙面 | Side-leaning against a wall |
| 3. 端正半身坐姿 | Upright half-body seated |
| 4. 正面轻步迈步 | Front-facing gentle step |
| 5. 微前倾俯身 | Slight forward lean |
| 6. 背身回眸 | Back-turn glance |

姿势是默认人像方案，实际构图还需结合素材、服饰与所选模式确认。平铺、挂拍、人台使用对应非人像构图，不把六个真人姿势直接套用过去。首张验收后作为后续人物参考，并逐张检查服饰、人物一致性与画幅。

These are default portrait poses, subject to source coverage, garment and mode constraints. Flat-lay, hanger and mannequin outputs use their own compositions. The accepted first portrait anchors later identity references; each image still needs review.

beta.11 缺背面分支：正面/前侧清楚时，仅明示替代第六张为正面自然站姿，前五保留；六张必须动作可区分，不能只换背景或裁切。明确要求原六姿势或背部结构时仍须补实拍。非人像背面构图不套用此真人例外。

beta.11: with sufficient front/front-side coverage but no rear source, disclose only slot 6 as stationary frontal standing. Keep slots 1–5 and six distinct actions. Explicit original-pose/rear-detail demands and nonportrait rear compositions still require rear material.

[准备素材 / Photo guide](INPUT-GUIDE.md) · [单件 24 风格预览 / Garment previews](demo/style-previews/white-vest-24-v1/) · [套装 24 风格预览 / Outfit previews](demo/style-previews/beige-blazer-denim-outfit-24-v1/)

两套历史预览均为每风格一张六宫格，不是独立成片。分发包内保留白马甲六图历史案例；线上另有[六组六图案例](https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html)，含外部试用套装，各组保留来源与验收范围。 / Both historical collections contain one six-panel sheet per style, not independent finals. The bundle retains the historical white-vest case; six reviewed groups, including an external outfit trial, are available online with their own source and review scope.

## 第一次用，先做这一步 / Start here

安装并启用插件后，在**新的 Codex 任务**中上传一张清晰、有权使用的真实服饰或完整套装照片。以下两条指令任选一种语言；这一步不调用生图。

After enabling the Plugin, upload a clear, authorized garment or coordinated-outfit photo in a **new Codex task**. Choose either language below. This step does not generate images.

```text
请用 $threadtruth-studio 识别并推荐风格，不要生图
```

```text
Use $threadtruth-studio to identify this garment and recommend styles. Do not generate images.
```

预期得到：服饰识别卡、主推与备选风格、完整 24 风格目录。看不清的细节应标为不确定或请求补图；不会因为上传照片就自动消耗生图额度。

Expect a garment recognition card, a primary style recommendation with alternatives, and the complete 24-style catalogue. Unclear details require uncertainty notes or better photos. Uploading a photo alone does not authorize image generation.

## 六组能力 / Six capability groups

“指令已定义”表示当前版本有对应工作流；“工具校验”指本地脚本检查。两者均不等于视觉效果或跨设备实测通过。右列单独说明证据范围。

“Workflow defined” means instructions exist in this version; “helper checks” means local scripts validate specific conditions. Neither proves visual quality or compatibility on every device. Evidence is listed separately.

| 能力 / Capability | 输入与结果 / Input → output | 当前实现与条件 / Implementation & conditions | 已有证据与边界 / Evidence & limits |
|---|---|---|---|
| **识别服饰 / Identify garments** | 单件、完整套装或同件多角度照片 → 颜色、结构、廓形及配饰的识别卡。 / Garment, outfit or multi-view photos → a card of visible colors, construction, silhouette and accessories. | 指令已定义；需要清晰真实照片。不同套装逐套处理，不自动混搭。 / Workflow defined; clear real photos required. Separate outfits are handled separately. | 有公开单件与套装样例；不是所有服饰类别的识别准确率评测。 / Public garment and outfit examples exist; no accuracy benchmark across all categories. |
| **选择风格 / Choose a style** | 识别卡与偏好 → 主推、备选和 24 风格自由选择。 / Source card and preferences → recommendations and a choice of all 24 styles. | 指令已定义；风格推荐不授权生图。已明确选定风格时不重复要求选菜单。 / Workflow defined; a recommendation is not generation approval. | 公开配对图库有 24 风格、48 张结果；不是当前版本 24 套六图流程的验证。 / 24 styles and 48 paired results, not 24 verified six-image beta.11 workflows. |
| **设置拍摄 / Set the shoot** | 风格、场景、输出形式、用途或比例 → 一组拍摄方案。 / Style, setting, presentation and ratio → a shoot plan. | 棚拍、场景、混合及五种输出形式均有指令；实际生图依赖宿主能力。 / Studio, location, hybrid and five presentation forms are defined; generation depends on the host. | 公开案例以服饰人像为主；不露脸、平铺、挂拍、人台没有本页可引用的逐形式完整公开验证。 / Public evidence focuses on portraits; this guide has no complete public validation per alternate form. |
| **选择产物 / Choose an output** | 已确认方案 → 单张测试、方向预览、六张独立成片或六条提示词。 / Confirmed plan → one test, a direction preview, six independent images or six prompts. | 四种动作已定义；生图另需明确授权及账号额度。 / Four actions defined; images require explicit approval and account quota. | 有历史预览、包内白马甲六图和线上六组案例；提示词输出不证明实际生成效果。 / Historical previews, the bundled white-vest set and six online reviewed groups exist; prompts alone do not prove image quality. |
| **选择入口 / Choose a route** | 同一方案 → Codex 原生生图，或 ChatGPT 网页转交包。 / The same plan → Codex generation or a ChatGPT web handoff. | 默认 Codex；网页为显式选择。网页自动执行需宿主浏览器工具；可转手动流程。 / Codex by default; web is opt-in. Automation needs host browser tools; a manual path is documented. | 维护者 macOS 已完成网页六张流程；非维护者新机器与真人手动易用性未验证。 / A six-image web run is recorded on the maintainer's Mac; fresh-host and human manual usability remain unverified. |
| **检查与修正 / Review & retry** | 源图、生成原文件与反馈 → 逐张问题记录、尺寸核对和授权后的单张重试。 / Sources, original outputs and feedback → per-image review, dimension checks and an authorized retry. | 有 QA 指令；网页助手校验尺寸、重复文件、顺序与请求记录。失败不会自动获得重试权限。 / QA instructions and web-helper size, duplicate, sequencing and request checks. Failures do not grant retry permission. | 本地助手有回归测试；视觉判断仍需对照源图及人工确认，不能保证小字、Logo 或合体效果。 / Helper regression tests exist; visual quality still requires source comparison and human review. |

对应规则与证据：[识别规则](../skills/threadtruth-studio/references/recognition.md)、[风格路由](../skills/threadtruth-studio/references/style-router.md)、[公开图库](https://denggui-ai.github.io/threadtruth-studio/compare.html)、[完整案例](demo/primary-cases/white-hooded-puffer-vest-korean-cold/README.md)、[版本与环境记录](COMPATIBILITY.md)、[网页助手测试（在线源码，需联网）](https://github.com/denggui-ai/threadtruth-studio/blob/main/tests/test_web_task.py)。测试源码不包含在插件 ZIP 内。 / Test source is online and is not included in the plugin ZIP.

Rules and evidence: recognition and routing references, public gallery, complete case, version/environment records and web-helper tests linked above. Tests of a helper are not end-to-end image-generation tests.

## 拍摄方式怎么选 / Choose the presentation

风格决定视觉方向，模式决定拍摄环境，输出形式决定是否出现模特，画幅决定交付尺寸；它们是不同选择。未指定输出形式时默认真人模特，不必填写额外问卷。

Style controls the visual direction, mode the setting, presentation whether a model appears, and canvas the output dimensions. These are separate choices. Human-model portraits are the default; no extra questionnaire is required.

| 选择 / Setting | 可用项 / Options | 说明 / Notes |
|---|---|---|
| 拍摄模式 / Mode | A 自动推荐 / auto recommendation；B 棚拍 / studio；C 场景 / location；D 混合 / hybrid | A 是在 B/C/D 中推荐，不是额外一种拍摄模式。 / A recommends B, C or D; it is not a fourth shooting mode. |
| 输出形式 / Presentation | 真人模特 / human model；不露脸局部 / faceless detail；平铺 / flat-lay；挂拍 / hanger；人台 / mannequin | 后四种可明确请求；规则已定义，验证范围见上表。 / The latter four are opt-in; their evidence limits are listed above. |
| 画幅 / Canvas | 明确比例或像素优先；未指定用途与比例时，独立成片默认 2:3。 / Explicit ratio or pixels take priority; independent images default to 2:3 when neither ratio nor use is specified. | 生成后读取文件尺寸；只写在提示词里不算通过。 / Check output metadata; a prompt is not proof of compliance. |

用途可辅助确定画幅与构图；电商主图、小红书封面、详情页、品牌大片的默认规则见[拍摄与画布说明](../skills/threadtruth-studio/references/modes-scenes.md)。这里提供图片素材，不自动制作带字海报、完整电商详情页，也不承诺平台审核通过。

Use cases can guide canvas and composition; see the linked mode/canvas reference. This produces image assets, not automatic typography, a complete ecommerce detail page or guaranteed platform acceptance.

## 预览、测试、成片有什么区别 / Output choices

| 动作 / Action | 得到什么 / Result | 生图调用 / Image-generation calls |
|---|---|---|
| 0 方向预览 / Direction preview | 一张带“非成片”标记的六宫格。 / One six-panel sheet labeled as a preview. | 1 次；使用所选账号额度。 / One; uses the chosen account's quota. |
| 1 独立成片 / Independent set | 同一套服饰的六张独立图片；首张检查后再逐张继续。 / Six separate images of one outfit, proceeding after first-image review. | 初始最多 6 次串行调用；失败会停止，可能无法一次完成六张。 / Up to six initial sequential calls; failure can stop the set before completion. |
| 2 单张测试 / Single test | 一张独立测试图。 / One independent test image. | 1 次。 / One. |
| 3 仅提示词 / Prompts only | 六条编号提示词与通用负面词。 / Six numbered prompts and shared negative instructions. | 0 次生图；不输出图片。 / No image-generation call; no images. |

预览不能裁切或放大后冒充独立成片；确认预览不自动授权六张生成。重试需明确授权并保留已用次数；多个套装逐套确认。完整交付仍需人工对照源图验收。

A preview cannot be cropped or upscaled into independent finals. Accepting it does not automatically authorize six images. Retries need explicit approval with used attempts retained. Handle multiple outfits separately and review outputs against the sources.

<a id="first-generation"></a>

## 可复制的任务指令 / Copyable task prompts

先完成上方识别步骤，再使用后续指令。将风格替换为目录中的实际选项；这些是操作示例，不是已测结果。

Complete recognition first. Replace the style with an option from the catalogue. These are usage examples, not recorded test results.

**只做方案，不生图 / Plan without generating**

```text
我选择电商棚拍风格、B 棚拍模式、真人模特、1:1。请确认服饰要点和拍摄方案，先不要生图。
```

```text
Choose ecommerce-studio, studio mode B, a human model and a 1:1 canvas. Confirm garment details and the shoot plan. Do not generate images yet.
```

**只要提示词 / Prompts only**

```text
沿用已确认的风格与方案，只输出六条编号提示词和通用负面词，不要生图。
```

```text
Use the confirmed style and plan. Return six numbered prompts and shared negative instructions only. Do not generate images.
```

**先测一张 / Generate one test — 会使用生图额度 / uses image quota**

```text
按刚确认的方案，授权在 Codex 先生成一张测试图。检查服饰与尺寸，不自动重试，也不要继续生成其余图片。
```

```text
Using the confirmed plan, I authorize one test image in Codex. Check the garment and dimensions. Do not retry automatically or generate more images.
```

**单件六图 / Six images of one garment — 使用生图额度 / uses image quota**

```text
按已确认的单件服饰、主风格和方案，授权在 Codex 按默认六姿势生成六张独立图片。首张验收通过后再继续，整组人物和画幅保持一致；失败暂停，不自动重试。
```

```text
Using the confirmed garment, main style and plan, I authorize six independent images in Codex with the default six poses. Review the first image before continuing; keep model identity and canvas consistent. Stop on failure; no automatic retries.
```

**套装六图 / Six images of a coordinated outfit — 使用生图额度 / uses image quota**

```text
按已确认的整套服饰、主风格和方案，授权在 Codex 按默认六姿势生成六张独立图片，保留已确认的单品、层次和鞋包配饰。首张验收通过后再继续，人物和画幅保持一致；失败暂停，不自动重试。
```

```text
Using the confirmed coordinated outfit, main style and plan, I authorize six independent images in Codex with the default six poses. Preserve the confirmed items, layers and accessories. Review the first image before continuing, keep identity and canvas consistent, and stop on failure without automatic retries.
```

**准备网页转交 / Prepare a web handoff — 此步不上传 / no upload yet**

```text
我选择 ChatGPT 网页路线。请准备已确认方案的编号参考图与单张提示词转交包，先不要上传或发送。
```

```text
I choose the ChatGPT web route. Prepare numbered references and a single-image prompt for the confirmed plan. Do not upload or submit anything yet.
```

网页流程的上传授权、手动步骤、浏览器条件及失败恢复见[网页教程](CHATGPT-WEB-TUTORIAL.md)。无生图工具时可继续识别或准备提示词；安装插件不会自动带来浏览器工具或额外图片额度。

See the web tutorial for upload approval, manual steps, browser requirements and recovery. Without generation tools, recognition and prompt preparation remain available. Installing the Plugin supplies neither browser automation tools nor extra image quota.

## 如何理解“已验证” / Read the evidence correctly

- **公开案例 / Public cases：** 24 风格配对样例、历史方向预览和已复核六图案例各有范围。它们不等于 beta.11 全风格、全形式、全环境验证。 / Paired samples, historical previews and reviewed six-image cases have separate scopes; they do not validate every beta.11 combination.
- **工具测试 / Helper tests：** 可证明测试覆盖的顺序、次数、文件和尺寸检查行为；不能代替生成图片的视觉验收。 / Tests establish covered helper behavior, not the visual quality of generated images.
- **环境实测 / Environment runs：** 当前公开记录以维护者 macOS 为主。其他系统、新用户安装和人工手动易用性仍需各自验证。 / Published records focus on the maintainer's Mac. Other systems, fresh-user installation and manual usability need their own evidence.

这里的“试穿”指 AI 模特上身展示；不承诺指定真人身份换装、尺码/合体仿真、非服饰商品生成或无人值守商业交付工具。真实人物照片用于读取服饰，不承诺复刻该人物身份。样例有各自媒体条款，公开可见不等于可任意商用。详见 [README 限制](../README.zh-CN.md#适用范围与限制) 与[媒体条款](demo/RIGHTS.md)。

Here, “try-on” means apparel presented on an AI model. This does not promise identity-preserving try-on on a supplied person, size/fit simulation, non-apparel generation or unattended commercial delivery. A person's photo supplies garment facts, not a promise to reproduce that person's identity. Public examples retain their own media terms; public visibility is not unrestricted commercial permission.

维护说明：本页是完整能力说明的维护入口，README 与首页仅提炼摘要。更新能力时同时核对当前发布版本、规则来源和实际证据；有新指令或测试并不自动升级“已实测”表述。

Maintenance: this page holds the detailed capability description; the README and homepage summarize it. Recheck release scope, rule sources and evidence when updating. New instructions or tests alone do not justify a new end-to-end verification claim.
