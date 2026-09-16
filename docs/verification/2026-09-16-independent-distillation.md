# 2026-09-16 独立重新蒸馏（盲审式）— 让六张服饰人像"出图效果"更好

> 本文由一个全新会话独立完成。写作顺序严格为：项目文件与图 → 外部来源 → 独立结论 → 最后才读前一会话的两份文档并列分歧。
> 本次未生图、未调任何付费或第三方模型、未改 `skills/`、`tools/`、`tests/`、`evals/`、`CHANGELOG.md`，未对 `.threadtruth/` 写入；仓库新增文件仅本文一份。

## 0. 范围、边界与已知未知

- 工作 checkout：`.worktrees/pilot-ecom-light`，分支 `exp/pilot-ecommerce-lighting`，起点提交 `d26f19d`（工作树干净）。
- 改前基线用 `git show f44433c:<path>` 读取；改后即当前 HEAD。**两者都按候选评价，不预设改后为正确答案。**
- 三张预览图生成时的模型与种子：**未知**（`evidence.json` 记录 `per_call_model: unavailable`）。
- 三张预览图均为 1254×1254 的 2×3 六宫格，单格约 390×520 px。**光影细节、面料纹理、接触阴影在这种分辨率下只能做粗判**；正式成片是 6 张独立图，任何结论都应在 1 张独立图上复核后再定。
- `.ai/`、memory、YAML 注释、commit 摘要里出现的前一会话判断，本文一律视为待验证假设，不作依据。

## 1. 项目内实读：提示词是怎样拼出来的（改前 / 改后）

读了 `SKILL.md`、`prompt-build.md`（§1、§2、§2a、§3、§4.1、§4.2）、`modes-scenes.md`、三个 pack，以及 `tools/style_preview.py` 中拼装动作 0 预览提示词的函数（只读，未改）。

拼装顺序（动作 0 预览）：标题/副标/页脚文字 → 服饰事实（core_items）→ 身份锚点一句 → `Mode` → `Mood only:` = `visual_language` → `Attitude:` = `model_persona` → `Lighting/background palette:` = `lighting_palette` → 6 个姿势块（母版名、Head/gaze、Mode/scene、Framing、保真一句）→ 预览负面词 + `negative_delta_add`。

三个对效果有直接影响的拼装事实：

1. **B 模式下六格场景被折叠成同一句。** `_mode_scene()` 对 B 模式（以及 D 模式前两格）一律返回 `low-distraction white or light-gray studio background`，pack 的六个 `scenes`（纯白无缝 / 浅灰无缝 / 柔光棚拍空间 / 浅米色纯色背景 / 低对比影棚 / 居中柔光位）在预览提示词里**一个都没出现**。六格拿到的是完全相同的一句背景描述。
2. **身份锚点句比 §4.0a 的成片措辞弱。** 预览提示词只写"identity-only: preserve face, hair, apparent age and body proportions; never treat it as outfit authority"，没有 §4.0a 里那句"Ignore its garment, pose, crop, lighting, background and accessory details"。锚点图本身是浅灰影棚、平光、中蓝色直筒牛仔裤——与电商包的目标场景高度相似。
3. **Head/gaze 行是中文，其余是英文。** 改后（§2a 试点）把情绪词去掉，只留几何，然后给每一格追加同一句英文 `expression and attitude follow the Attitude line above; no cold or detached editorial mood`，六格重复六次。

改前/改后 `ecommerce-studio.pack.yaml` 的字段差异（只列有效果影响的）：

| 字段 | f44433c（改前） | HEAD（改后） |
|---|---|---|
| `visual_language` 光线分句 | `even soft lighting` | `soft directional studio lighting that shows form and fabric texture` |
| `lighting_palette` | `even soft-box lighting, neutral white balance, true color, low shadow`（12 词） | 主光 45° 机左略高 / 低比例补光 / 袖口翻领口袋盖褶皱的渐变阴影 / 鞋下接触阴影 + 背景渐变分离 / 高光保细节 / 六张一致（约 95 词） |
| `model_persona` | `neutral approachable expression, composed catalog attitude, no exaggerated posing` | 追加：放松下颌与肩、`calm direct or softly averted gaze without cold detachment`、重心落一腿、手自然垂放 / 插口袋 / 搭在参考图已有配饰上 |
| `negative_delta_add` | 5 条 | 7 条（新增 `no flat shadowless lighting`、`no cold detached expression`） |
| `qa_extra` | 3 条 | 6 条（新增方向光/接触阴影、六张光线一致、表情中性亲和） |

预览提示词长度：改前 569 词（4.4 KB），改后 797 词（5.9 KB），增长约 40%。

## 2. 逐格实看三张预览图（观察与推测分开写）

服饰源图（平铺）事实：米色单排两粒扣平驳领西装（袖口三粒扣、有袋盖口袋）、白色圆领 T 恤、**深靛蓝**直筒牛仔裤、橄榄绿方形托特包、深棕马衔扣乐福鞋；可选：金色细项链、两枚戒指、棕带腕表。

### 2.1 `ecommerce-studio.jpg`（B 模式，改前规则）

| 格 | 光线方向与阴影 | 人物与背景关系 | 姿势与重心 | 表情 | 编造 / 漂移 |
|---|---|---|---|---|---|
| 1 侧身回转 | 正面平光，看不出主光方向；西装几乎无明暗面；鞋下阴影极淡 | 浅灰背景无地平线、无渐变，人像像剪贴 | 重心居中偏正，手扶驳领；成立 | 平静、视线侧前 | 牛仔裤偏中蓝，比源图浅 |
| 2 倚靠墙面 | 同上，无墙面接触阴影 | **看不到墙**：背景与"墙"同色同亮，倚靠读作悬空后仰 | 交叉腿、手插兜；倚靠无支撑感 | 微垂目 | 牛仔裤偏浅 |
| 3 端正坐姿 | 平光；白色方块与地面几乎同色 | 坐在一个白色立方块上（源图与提示词都没有该道具，属于影棚道具，可接受） | 交叉腿坐姿成立，半身裁切正常 | 侧望，平静 | 牛仔裤最浅的一格 |
| 4 正面迈步 | 平光；地面看不见 | 无地平线，人像悬浮 | 迈步、手插兜；成立 | 侧望 | 无 |
| 5 前倾俯身 | 平光；西装褶皱处略有明暗 | 坐在白色方块上 | 前倾成立；**手抬到耳侧触脸**，接近"托腮"语义（提示词只在第 3 格禁托腮） | 垂目 | 无 |
| 6 背身回眸 | 平光；鞋下阴影几乎不可见 | 无地平线 | 回眸成立，全身完整 | 回望镜头 | 无 |

系列层面：身份一致；六格光线"一致地平"；背景六格完全相同；整张更像同一剪影贴在灰底上的目录页，而不是一次影棚拍摄。服饰硬事实（西装结构、包型、鞋型）基本保真；**牛仔裤色深是可见漂移**（第 1/3/4 格明显浅于源图的深靛蓝）。

推测（非观察）：牛仔裤变浅与身份锚点图的中蓝色牛仔裤一致，且只在与锚点场景最相似的这张图上最明显——怀疑是锚点图的服饰/光线语义泄漏到输出，而不是纯随机。

### 2.2 `american-street.jpg`（C 模式）

| 格 | 光线方向与阴影 | 人物与背景关系 | 姿势与重心 | 表情 | 编造 / 漂移 |
|---|---|---|---|---|---|
| 1 涂鸦墙 | 阴天散射光，人物落地、有脚下阴影 | **涂鸦背景强、色彩多，抢过米色西装** | 站姿、手插兜；成立 | 侧望 | 墙上有大量伪文字/海报 |
| 2 地铁站台 | 站台顶光，有接触阴影 | 有真实倚靠的柱面 | 倚靠成立 | 微垂目 | 站牌渲染了 `14 Street` 文字 |
| 3 石阶 | 侧光，阶梯投影清楚 | 坐在石阶上，包放身侧 | 半身坐姿成立 | 仰望侧方 | 无 |
| 4 卷帘门 | 散射光 | 卷帘门作背景，低干扰 | 迈步、手插兜 | 侧望 | 门上渲染了 `KEEP CLEAR` 文字 |
| 5 篮球场 | 散射光 | 坐在水泥台，背景围栏+篮球 | 前倾、双手抱包；**包被压在双手与膝之间且贴下边缘** | 垂目 | 包色偏灰棕，橄榄绿漂移 |
| 6 黄昏霓虹 | 暖色点光+湿地反光，最"摄影"的一格 | 街景虚化，人物清楚 | 回眸成立 | 回望 | 乐福鞋在霓虹下发黑，鞋色不可判 |

系列层面：六格是六个不同地点、六种光色，单格都成立但整张不像同一次拍摄；这是 pack 设计（六场景）本身的结果。另：pack 的 `anti_categories` 含"西装"，这套米色西装+乐福鞋+结构托特包与"美式街头"本身就是风格错配——**评价出图时要把这点算进去**，它不是提示词质量问题。

### 2.3 `japanese-lifestyle.jpg`（C 模式）

| 格 | 光线方向与阴影 | 人物与背景关系 | 姿势与重心 | 表情 | 编造 / 漂移 |
|---|---|---|---|---|---|
| 1 原木公寓 | 窗光从右侧进入，地面有明确投影 | 落地、有空间深度 | 站姿成立 | 侧望，柔和 | 无 |
| 2 咖啡馆门口 | 侧光 | 倚靠白墙，有支撑 | 倚靠成立 | 微垂目 | 门上渲染了 `GOOD COFFEE A BETTER DAY` 文字 |
| 3 沙发 | 柔光 | 坐在沙发，包放旁边 | 半身坐姿，**手持马克杯**（源图无此道具） | 侧望，最柔和的一格 | 杯子为编造道具 |
| 4 小巷自行车 | 散射日光 | 落地 | 迈步、手插兜 | 侧望 | 无 |
| 5 文具店 | 店内暖光 | **货架密集**，背景干扰高；包带斜挎压住西装前襟 | 前倾翻看笔记本 | 垂目 | 无 |
| 6 米色亚麻棚拍 | 柔光 | **米色西装贴米色亚麻背景，分离度最低** | 回眸成立 | 回望 | 无 |

系列层面：暖调贯穿六格，整张最"像照片"、最舒服；代价是**米色西装和白 T 恤整体偏暖偏黄**，作为"true-to-product"的电商用途有色彩风险，但作为日系生活风是设计使然。

### 2.4 三张横向比较得到的观察

- 三张图的**服饰结构保真都够用**；三张图差异主要在"有没有光的方向、人物有没有落地、背景有没有层次"。
- 唯一"照平且悬浮"的是电商棚拍这张，也正是唯一被折叠成单一背景句、且光线描述只有"even / low shadow"的那张。
- 表情在三张图里差别不大，都是"平静、不看镜头"；电商那张并不比另外两张更"冷"，它更像"没有状态"。

## 3. 外部来源方法卡

栏目固定为：来源与日期/提交 ｜ 实际看见的证据（文本层 / 已看图分开）｜ 未知项 ｜ 可迁移到"服饰保真 + 六张人像 + 串行单图宿主"的方法 ｜ 不能迁移及原因 ｜ 预期可观察的画面变化。

### 3.A `motiful/product-shots`（`main` @ `063c508`，2026-06-08）

**文本层（五个文件全文实读）**
- `photography-style-presets.md`：三套风格块（复古直闪 / 柔光哑光胶片 / 硬光编辑）。每套都用"光源→阴影→后期/材质→禁止项"四段写，且要求**整块逐字重复进每一条任务提示词**。共通禁止项：多方向阴影（暴露多光源）、纯黑阴影、数字洁净感。Preset B 明确"背景 #f1eee9、肤色与背景色调融合、无强分离、扁平绘画感、情绪疏离"——这恰是"照平"的正面定义，被该仓库当作一种可选风格。Preset C 要求"阴影必须透明、保留暖色底、阴影区仍见纹理"。
- `hard-constraints.md`：8 条 MUST——参考图必传、先析后生、发型结构不可重释（背面/侧面两张是"验证视角"）、配饰不加不减（超出裁切时写"frame doesn't reach them"）、硬裁切边界用**负面身体部位**表达（"No knees, lower legs, or feet"）、全局风格统一（"不允许某张比其它张更干净/更数字/更高对比"）、覆盖只重生受影响图、单批生成 9 张避免跨调用漂移。
- `task-prompts.md` / `task-prompts-6-9.md`：9 张模板，每张给镜头（85/35/100/105mm）、裁切上下界、姿态（重心偏一侧、躯干旋转、手不对称、contrapposto、骨盆与胸部反向扭转角度）、视线与表情。
- `variables-and-workflow.md`：14 变量抽取规范，OUTFIT 抽取要求"件数 / 主色+点缀色 / 材质 / 松紧 / 层叠顺序"，并给出"错误示例 vs 正确示例"。

**已看图**（`assets/gallery/dress/`：multi-angle 01/02/03、main-image 01/02）：粉色碎花中长裙，白/浅灰无缝影棚。01 正面与 main-image 01 都是**正面平光、几乎无投影、地平线不可见**——与本项目电商图同一种"剪贴感"；03 侧面那张有影棚 cyclorama 的墙地渐变，人物明显落地，观感最好。即该仓库的样图并没有兑现它文本里的光影规范。

**未知项**：样图生成模型与是否用了 preset；样图是否经过后期。

**可迁移**
1. 光影写法四段化（光源→方向→阴影特征→对比/曝光）并在每张独立图**逐字重复**——与本项目 §4.1 的"四段顺序"一致，可直接沿用；重复而非引用，是为了六次串行调用间不漂移。
2. 禁止项改写成可见判据："单一方向阴影""阴影区保留纹理与色彩""不允许任何一张比其它张更干净/更高对比"。后者可直接进 `qa_extra`。
3. 裁切边界的负面身体部位写法，可补到本项目全身母版："feet and shoes fully inside the frame with a small margin below the soles"。
4. 姿态写法：重心偏一侧、躯干微转、双手不对称——这是母版 1/4 的自然补充，不新增母版。

**不能迁移及原因**：单批生成 9 张（违反本项目 B1 串行单图）；发型结构锁（本项目锁的是服饰不是人）；镜头焦段逐张变化（本项目六张要一致）；Preset A/C 的过曝、油光、硬光（电商 true-to-product 不允许）。

**预期可观察变化**：六张里阴影方向一致；西装出现明暗面；不再有"某张更平"的漂移。

### 3.B `YouMind-OpenLab/nano-banana-pro-prompts-recommend-skill`（`main` @ `990958c`，2026-09-16；manifest 15,638 条）

**文本层**：`manifest.json` 11 类；`ecommerce-main-image.json` 575 条，按"服饰/模特 × 光线/影棚"过滤命中 80 条；`product-marketing.json` 13.3 MB、5,699 条，同样过滤（外加"电商/目录/无缝/全身"）命中 554 条，其中高分项多为名人相似脸、JSON 结构化"luxury editorial"，与电商保真关系不大。真正有用的写法集中在少数条目：
- id 27620：`seamless, solid neutral gray backdrop (both floor and wall) ... soft and diffused ... gentle gradations and soft shadows on the floor around the chair and the man's feet` —— 明确写了"地面与墙同为无缝背景"和"脚周围的地面软阴影"。
- id 34120：`Plain soft neutral gray studio background, soft even studio lighting, ... shot on medium format camera, shallow depth of field, clean commercial look` —— 文本写的是"even"，但样图并不平（见下）。
- id 12693（JSON）：`setup: soft key light from front-left, balanced fill light, minimal shadows; shadows: soft and diffused under legs and behind subject; floor: smooth studio floor blending with backdrop`。
- id 24378：多角度 lookbook 一条提示词生多张（"standing hand in pocket / sitting on wooden block crate / adjusting lapels"）。

**已看图**（5 张 sourceMedia：34120、27620、29040、24378、33479）：34120（酒红 polo 男坐高脚凳）——灰色带纹理背景、左上柔主光、凳与鞋下有接触阴影、胶片感颗粒，是这批里最"高级"的影棚图；27620——灰色无缝墙地一体，椅脚与鞋周围有清晰软阴影，人物落地；29040（牛仔胸衣女）——灰底、过度磨皮、典型"AI 电商"感；24378（鼠尾草绿套装坐木箱）——均匀柔光但有坐具接触阴影；33479（浅灰套装坐蓝色台）——高调、背景近白、有胶片感。

**未知项**：每条的生成模型/参数（sourceMedia 来自社媒转贴）；样图与提示词是否一一对应。

**可迁移**
1. "地面与背景同为无缝、人物脚周围有软阴影"这一句是**低成本、低保真风险**的落地写法。
2. "坐具/道具的接触阴影"——本项目母版 3/5 在 B 模式下要坐东西，写清道具名（白色方块 / 木箱）和接触阴影，比让宿主猜稳。
3. `soft key light from front-left + balanced fill` 的短写法（约 15 词）足以让 27620/12693 那类样图出现方向光，不必写成 90 词。

**不能迁移及原因**：名人相似脸、JSON 超长结构（本项目宿主是 ChatGPT/Codex 原生生图，提示词形式已由 core 固定）；一条提示词生多张（违反串行单图）；`8K / ultra-detailed` 类质量词（OpenAI 指南明确说这类词不如摄影语言有效）。

**预期可观察变化**：鞋下与坐具下出现软阴影；地面与背景出现可辨的分界或渐变；人物不再悬浮。

### 3.C OpenAI Cookbook 两本 notebook + 官方 image prompting 指南

（`image-gen-models-prompting-guide.ipynb` 最后提交 `d310dfa` 2026-08-20；`image-gen-1.5-prompting_guide.ipynb` 最后提交 `fc51ab3` 2025-12-16；官方指南页当前版本面向 GPT Image 2.5，注明 1.5 将于 2026-12-01 下线。两本 notebook 的 markdown 单元与代码单元里的 prompt 字符串已解析实读。）

**文本层要点**
- 顺序："背景/场景 → 主体 → 关键细节 → 约束"，并写明用途（ad / product photograph）以设定"模式"。
- 照片真实感：直接写 `photorealistic` / `real photograph`；用摄影语言（镜头、光、构图）比 `8K/ultra-detailed` 可靠；镜头参数"只当外观提示，不保证物理模拟"。
- 人物："full body visible, feet included"、"looking down at the open book, not at the camera"、"hands naturally gripping…"——**用可见动作而不是情绪词**描述姿态与视线。
- 约束："change only X + keep everything else"；**每次迭代重复保留清单**以抑制漂移；多图输入按索引指定角色（"Image 1: product photo… Image 2: style reference…"）。
- 虚拟试穿示例（5.2）：锁人只改衣，且要求"Match lighting, shadows, and color temperature… without looking pasted on"。
- 多图合成（5.9）：要求"matching lighting, perspective, scale, and shadows so the composite looks naturally captured"。
- 4.3 建议"避免暗示影棚修饰/摆拍的词"以获得自然感——这条对电商棚拍**不适用**（电商恰恰要影棚）。

**已看图**：指南页中的示例图（水手、试穿）只看了缩略，不作为证据。

**未知项**：ChatGPT/Codex 原生生图入口与 API 的 `gpt-image-*` 是否同一权重/同一提示词行为——本项目 host 证据里模型不可得。

**可迁移**
1. 参考图角色句改成指南格式并补齐"忽略项"：`Image 2 = identity anchor only: keep face, hair, apparent age, body proportions; ignore its garments, jeans wash, lighting, backdrop and pose.`
2. 全身格追加 `full body visible, feet and shoes included`（比 `Framing: full-body` 更被指南背书）。
3. 用可见动作替代情绪词写视线，例如把"视线避开镜头"写成 `eyes on a point just past the camera-right edge`。
4. 提示词开头加 `photorealistic e-commerce studio photograph`（一次即可）。

**不能迁移及原因**：API 参数（quality/size/fidelity）——本项目不指定模型与 API 参数（SKILL §4）；透明背景/蒙版编辑——与人像成片无关。

**预期可观察变化**：牛仔裤色深回到源图；鞋不被裁；姿态更"像被拍到"而不是"被摆放"。

### 3.D 摄影资料

**Profoto《How to photograph a model wearing a coat for e-commerce》（2023-07-30）** — 文本层：主光"across your model from his or her left"制造"a little shadowing and contrast"；"Keep the lighting the same throughout"；曝光过高会"washed out"细节与肤色；反光板补暗部，**也可用黑板吸光加对比**；顾客想看的是"texture of the material, the silhouette"。摆姿：头微垂=含蓄亲近；"how important the hands are"；膝盖处交叉腿加动感；脚的站位决定自信感；手插兜+直视=大胆。已看图：浅灰无缝背景带上亮下暗渐变，驼色大衣有清晰的明暗面与毛领质感，鞋下有接触阴影，三张并排是同一光线下的三个姿势——这正是"六张一致 + 有方向光"的实物参照。

**Profoto《How to successfully run a photoshoot and direct your model》（2023-08-04）** — 文本层：先定框架（宽框看衣与环境）；"Add marks to the floor for consistency"；每套衣服至少覆盖正面、背面、细节；outfit 要与 set 呼应。已看图：影棚幕后照，无直接光影证据。

**Profoto《How to design your set and style your model》（2023-07-25）** — 文本层：加"blocks or furniture"让模特有可用的支撑与层次；道具可能抢戏；背景可用白/灰各种深浅的无缝纸；styling 要无褶皱无线头。已看图：不同颜色的背景纸卷，无光影证据。

**broncolor《How to Set Up your Lights for Ecommerce Fashion Shoots》** — 文本层只有摘要（三盏灯完成电商时装棚；强调曝光与色彩绝对一致），正文是视频（YouTube embed），**视频内容未取到**，不补想象。

**Studio Nicholson Women's Summer '26 Looks** — 已看图：Look 1（灰色麂皮夹克 + 黑色直筒牛仔 + 黑凉鞋）与 Look 3（骨白色抽绳领夹克，半身）；核对同 look 商品页：Look 3 商品页第一张 `Lismore Jacket in Bone` 与 look 图为同一件（抽绳高领、双头拉链、袋盖口袋一致）；Look 1 商品页 `Barra Straight Leg Denim Pant` 与 look 图为同一条（洗黑色、直筒、裤长到脚背）。观察：白/浅灰无缝影棚，**地面与背景之间有可见的浅色地平线**，鞋下有很轻但确实存在的接触阴影，主光从左上给出柔和明暗面（麂皮绒面的方向感、棉布褶皱可读），背景右上略亮形成渐变；表情中性、直视或微侧；没有道具。商品页图比 look 图更平一点，但仍有地平线与鞋下阴影。

**可迁移（D 组合）**
1. 一句话的"主光在模特一侧、其余保持不变"是三家的共同底线；本项目改后版的方向已对，但可以更短。
2. "地平线 + 鞋下接触阴影 + 背景轻微渐变"三件套是品牌棚拍与教程照的共同特征，且不碰服饰事实。
3. 母版 2（倚靠）在影棚需要有形的支撑：Profoto 明说用 blocks/furniture；本项目电商 B 模式应给"白色影棚墙板/方块"而不是让宿主凭空倚靠。
4. 手的位置写具体（插兜 / 扶驳领 / 提包）——Profoto 与本项目改后 persona 一致。

**不能迁移及原因**：黑板吸光加对比（会加深阴影，对深色牛仔与深棕鞋的细节有风险，电商不宜默认）；Studio Nicholson 的"表情直视镜头"（与本项目母版 1–5 的视线几何冲突，不改母版）。

**预期可观察变化**：与 Studio Nicholson 图并排看时，本项目电商图出现地平线与鞋下阴影，西装左右两侧明度不同。

## 4. 独立结论（写于读前一会话文件之前）

### 4.1 诊断：三张预览图"不好看"的主要原因（按影响排序）

1. **电商图没有任何光的方向与落地关系，来源是三处互相强化的"平光"指令。**
   - `styles/ecommerce-studio.pack.yaml`（f44433c）`lighting_palette: even soft-box lighting … low shadow`；
   - 同文件 `visual_language` 中的 `even soft lighting`；
   - 同文件 `negative_delta_add` 的 `no dramatic shadows hiding product`（在没有正向阴影描述时，宿主只剩"少阴影"一个方向可走）。
   结果：西装无明暗面、鞋下无接触阴影、背景无渐变——2.1 表六格全部命中。
2. **B 模式六格背景被折叠成同一句，且这句既无地面也无墙。** `tools/style_preview.py::_mode_scene` 对 B 模式固定返回 `low-distraction white or light-gray studio background`，pack 的六个 `scenes` 未进入提示词。没有"floor / backdrop meets floor / wall"任何一个词，母版 2 的"倚靠墙面"在画面里就没有墙（2.1 第 2 格）。这一条与 `modes-scenes.md §1 B` 只写"纯白/浅灰无缝"也有关：规则层本身没有要求"地面可见"。
3. **身份锚点句缺少"忽略其服饰/光线/背景"的忽略项。** 预览提示词中的锚点句只有"preserve face, hair, apparent age and body proportions; never treat it as outfit authority"，`prompt-build.md §4.0a` 第 4 条那句"Ignore its garment, pose, crop, lighting, background and accessory details"没有进预览提示词。锚点图是浅灰影棚平光 + 中蓝牛仔裤；电商图恰好是三张里牛仔裤最浅、光最平的一张（观察），泄漏是合理推测（推测）。
4. **风格与服饰错配（仅 american-street）**：`american-street.pack.yaml` 的 `anti_categories` 含"西装"，米色西装 + 乐福鞋 + 结构托特包本来就不该路由到这个包；这张图的"不好看"更多是错配和涂鸦背景抢戏（2.2 第 1 格），不是提示词光影问题。
5. **场景文字与道具编造（american-street / japanese-lifestyle）**：`14 Street`、`KEEP CLEAR`、`GOOD COFFEE A BETTER DAY`、马克杯。预览负面词里的 `no fake text` 对"服饰上的文字"有效，对场景招牌无效；是否算问题取决于平台用途，电商主图不允许，生活感展示图可接受。位置：`prompt-build.md §3b` 负面词没有区分"服饰文字"和"环境文字"。
6. **表情**：三张图表情差异不大，电商图并不更冷，只是"没有状态"。改前 Head/gaze 里的"冷静疏离 / 不正面营业"在这张图上没有制造出可见的冷感（观察）。因此表情不是首要原因，排最后。

### 4.2 优化方案（只写方案与示例句，不改文件；按"预期视觉收益 / 改动成本 / 保真风险"排序）

| # | 改哪里 | 改成什么（示例句） | 单图验证方法 | 收益 / 成本 / 保真风险 |
|---|---|---|---|---|
| P1 | `ecommerce-studio.pack.yaml` → `lighting_palette`（用一段短句替换改前 12 词，也替换改后 95 词） | `one large soft key light from camera-left, slightly above eye level; soft fill from camera-right at about one third of the key; gentle shadow transition across the jacket so weave and construction stay readable; a soft contact shadow under the shoes; neutral white balance, true-to-product color; identical light in all six images.`（约 55 词） | 只出 look-1（母版 1）：看西装左右两侧是否明度不同、鞋下是否有阴影 | 高 / 低 / 低（不提任何具体服饰部件） |
| P2 | 同文件 → `scenes` 六条改写为带地面与支撑的影棚描述；或 `modes-scenes.md §1 B` 加一句"地面可见" | 例：`seamless light-gray studio, floor and backdrop meet in a soft horizon line, faint tonal gradient on the backdrop` / `same studio with a plain white studio wall panel for leaning` / `same studio with a low white studio block for seating` | 出母版 2：看是否有可见墙面与肩部接触阴影 | 高 / 中（涉及 `_mode_scene` 是否读 pack.scenes 的运行时规则）/ 低 |
| P3 | `tools/style_preview.py::_prompt` 的锚点句（或 `prompt-build.md §4.2` 预览公式） | `Attached image 2 is an identity-only anchor: keep face, hair, apparent age and body proportions; ignore its garments, denim wash, lighting, backdrop, pose and crop.` | 出 look-1：牛仔裤是否回到源图深靛蓝 | 中高 / 低 / 低（只增加忽略项） |
| P4 | 全身格 Framing 行 | `Framing: full body visible, feet and shoes fully inside the frame with a small margin below the soles` | 出母版 4：鞋是否完整、是否贴边 | 中 / 低 / 无 |
| P5 | 提示词首行加一次真实感锚词 | `Create one photorealistic e-commerce studio photograph …` | 与 P1 同图对比 | 中 / 低 / 无 |
| P6 | `model_persona`（改后版压缩） | `neutral approachable expression, relaxed jaw and shoulders, gaze per the pose line, weight naturally on one leg when standing, hands at ease (in a pocket only if the garment has one)` | 看第 3/5 格坐姿是否仍自然、手是否再触脸 | 低中 / 低 / 低（把"直视"和"插兜"改成条件式） |
| P7 | `§2a` 六格重复句 | 把 `expression and attitude follow the Attitude line above; no cold or detached editorial mood` 只在提示词头部写一次，六格不再重复 | 词数对比 + 看表情是否有变化 | 低 / 低 / 无 |
| P8 | `§3b` 预览负面词 | 增加 `no readable signage or storefront text` 仅对 C/D 模式 | 出日系第 2 格 | 低（电商无关）/ 低 / 无 |
| P9 | `qa_extra` | 加"六张里没有任何一张比其它张更平/更亮/更高对比"（来自 A 的 RULE_006） | 整组交付前肉眼并排 | QA 项，不影响出图 |

验证顺序建议：**只用 1 张独立图（动作 2，母版 1）验证 P1+P3+P4+P5**，再决定要不要碰 P2 这类运行时规则。

### 4.3 对 `ecommerce-studio.pack.yaml` 改前 / 改后两个版本的评价

**改前（f44433c）**：三处"平光"指令叠加，没有地面、没有阴影、没有分离；已有一张实图证明其输出是剪贴感。**不够好。**

**改后（HEAD）**：方向是对的（主光方向、补光比例、接触阴影、背景渐变、六张一致、`no flat shadowless lighting`），这是 A/B/D 三组来源共同支持的写法，**比改前更可能出好图**。但有五点过度或风险：
1. `lighting_palette` 里点名 `sleeves, lapels, pocket flaps and folds`——`lighting_palette` 是全 pack 通用字段，换一件没有袋盖/驳领的连衣裙时，这些词就是**给服饰新增结构的诱导**；§4.1 商品事实守卫要求过滤，但把服饰部件写进光线字段等于给守卫增加工作。应改成不提部件的写法（见 P1）。
2. `model_persona` 的 `hands … in a pocket` 同样可能给无口袋服饰"长出"口袋；`weight settled naturally on one leg` 对坐姿母版 3/5 是矛盾指令；`calm direct … gaze` 与 §2 母版 1–5"视线避开镜头"的几何冲突，宿主可能二选一。
3. 六格各追加同一句英文注记，加上 95 词光线，预览提示词从 569 词涨到 797 词。在**六宫格预览**里，一条 95 词的光线描述要同时作用于六格，稀释明显；在**独立成片**里值得，但也应压到 50–60 词。
4. `no cold detached expression` 与"视线避开镜头 / 视线垂落"的几何组合本身就容易读作疏离；负面词无法消除几何造成的观感，只能靠 persona 正向描述。
5. 改后仍**没有**处理 4.1 的第 2 条（地面/墙/支撑）和第 3 条（锚点忽略项）——这两条我认为对"悬浮剪贴感"的贡献不低于光线描述。

结论：**改后 > 改前，但两者都不够；改后需要瘦身并去掉服饰部件词，同时补地面与锚点忽略项。**

### 4.4 不建议做的事 / 价值不高的资源

不建议：
- 不要把 product-shots 的 Preset A（复古直闪过曝）或 Preset C（硬光油光）引入电商包，也不要加胶片颗粒——与 true-to-product 冲突。
- 不要为了"光影感"把 `no dramatic shadows hiding product` 删掉；它与 P1 并不冲突。
- 不要改六姿势母版或 §2 的视线几何来迎合"直视镜头"的品牌图；表情来源可以换，几何不动。
- 不要在预览六宫格上判定光线方案成败——单格 390 px 看不出接触阴影与面料明暗；用 1 张独立图。
- 不要用 JSON 结构化提示词或 `8K/ultra-detailed`；不要把 9 张单批生成、发型锁、镜头逐张变化搬进来。
- 不要靠 `negative_delta_add` 修表情；负面词对"几何造成的疏离感"无效。

价值不高的资源：
- `product-marketing.json`（5,699 条）：过滤后高分条目多是名人相似脸与超长 JSON，对服饰保真电商图几乎无增量；`ecommerce-main-image.json` 里的 3–4 条已足够。
- broncolor 页面：正文是视频，文本层只有摘要，对本次没有可引用的具体设置。
- product-shots 的画廊样图：文本规范写得比样图做得好，样图本身与本项目电商图同样"平"，不能当目标参照；Studio Nicholson 与 Profoto 的实拍图才是参照。
- OpenAI 指南里关于 API 参数、透明背景、蒙版编辑的部分：与本项目 host 契约无关。

## 5. 对照与分歧（最后一步：读完 `2026-09-15-github-distillation-and-effect-plan.md` 全文与 `2026-09-15-ecommerce-studio-lighting-pilot.md` §2、§3 之后逐条写）

只按证据给三种判定：同意 / 不同意 / 证据不足。

### 5.1 对《effect-plan》§1 蒸馏结果

| 前一会话结论 | 判定 | 理由 |
|---|---|---|
| product-shots 的价值在结构（规格块 + 几何化姿势 + 负面裁切句），不在光线审美；样图是反面证据 | 同意 | 我实读五文件、实看五张样图，结论一致（3.A）。补一条它没写的：RULE_006"不允许某张比其它张更干净/更高对比"应直接进 `qa_extra`。 |
| YouMind 两条样图有方向光与接触阴影；有效写法是"柔和 + 方向 + 阴影落在哪" | 同意 | 27620 一条的文本与图对应最好；29040（牛仔胸衣）我判为过度磨皮的典型 AI 图，可当"有接触阴影"的证据，不宜当效果目标。 |
| cookbook：顺序 背景→主体→细节→约束；写实靠摄影语言；换装约束句可借 | 同意 | 与 3.C 一致。补：指南把"full body visible, feet included"和按索引给参考图角色列为基本功，本项目预览提示词两处都可以更贴近。 |

### 5.2 对《effect-plan》§2 诊断表

| 前一会话诊断 | 判定 | 理由 |
|---|---|---|
| 三个视觉字段各一行形容词，没有方向/比例/阴影位置/地面关系，模型只能给匀光 | 同意，且补两条 | 我的 4.1 第 1 条与之相同；但前一会话没有指出 (a) 负面词 `no dramatic shadows` 在无正向阴影描述时会把宿主推向更平，(b) **B 模式六格场景被 `_mode_scene` 折叠成同一句且无地面/墙**（4.1 第 2 条）。后者是"悬浮剪贴感"的直接来源，前一会话 pilot §2 甚至写了"B 模式不受影响"。 |
| 六行头部视线全是韩系情绪词，24 风格共用一种"冷静疏离" | 证据不足 | 文本事实成立，但三张图里我看不到可归因于这些词的"冷感"；电商图第 2/5 格的"低头"来自 §2 的**几何**（头部微垂 / 前倾下压），改后 §2a 保留了同样的几何，只换情绪来源，因此"低头冷感"在候选图里大概率仍在。表情不是首要杠杆。 |
| 姿势母版只有名字，出来就是站桩 | 不同意 | 提示词里每格除母版名还有中文描述（"侧身回转站姿"等）；三张图的姿势都不是站桩：有迈步、倚靠、坐姿、回眸、手扶驳领、手插兜。american-street 第 1/4 格偏静，但仍有重心偏移。几何补写有益但排在光线、地面、锚点之后。 |
| C 模式六格六地点，光线时段全变，系列感散 | 同意观察，方案另议 | 观察属实（2.2/2.3）。但"六个地点"是 pack 设计意图，且 C 模式两张图的单格质量恰恰是三张里最好的；系列感与场景丰富度之间是产品取舍，不是缺陷。 |
| 标题/页脚/角色/守卫句挤占注意力预算 | 证据不足 | 三张图的标题、副标、页脚全部渲染正确，没有证据表明这些文本损害了画面；重排顺序成本低、可以做，但它不是被证明的病因。 |

### 5.3 对《effect-plan》§3 方案与 §4 执行顺序

| 方案 | 判定 | 理由 |
|---|---|---|
| 3.1 每个 pack 的 `lighting_palette` 扩成四段规格进 prompt | 同意方向，不同意现有写法 | 方向被 A/B/D 三组来源支持。但已实施版本 (a) 点名 `sleeves, lapels, pocket flaps`——光线字段不该出现服饰部件词，对无袋盖/无驳领的服饰是新增结构的诱导；(b) 95 词太长，50–60 词足够（见 4.2 P1）；(c) 推广到 24 包前必须先有 1 张独立图证据。 |
| 3.2 六母版补几何 + §2a 扩到全部 24 包（core 一次性改） | 不同意（作为下一步） | 这是唯一的全局改动，却建立在"站桩/冷感"这两个我认为证据不足的诊断上；且 persona 里的 `weight on one leg` / `hands in a pocket` / `calm direct gaze` 对坐姿母版、无口袋服饰、母版 1–5 视线几何都有冲突。应等 P1–P3 在独立图上验证后再决定。 |
| 3.3 C 模式改为"一个地点、六个机位" | 证据不足 | 会影响全部 C 模式包；它换来系列感，代价是场景多样性。建议先作为 `scene_strength=low` 时的可选行为而非默认；先拿一张对照图再定。 |
| 3.4 提示词顺序重排、治理文本后置 | 同意（低风险） | cookbook 支持该顺序；但不要以为它能解决平光。 |
| 3.5 负面句：`no flat shadowless lighting, no multi-directional shadows` | 同意 | 与 A 来源一致。 |
| 3.5 `no invented signage, no readable text in the background` | 同意，限 C/D 模式 | 对应日系第 2 格与美式第 2/4 格。 |
| 3.5 `no added props beyond the reference` | 不同意（B 模式） | 影棚里的坐姿母版 3/5 需要方块/坐具，这句会与之冲突；改为 `no props other than plain studio blocks or a plain wall panel`。 |
| 3.5 `match lighting, shadows and color temperature … not look pasted on` | 同意 | cookbook 原句。 |
| 3.5 `no symmetric stance, no stiff catalog pose` | 证据不足 | 负面词解决不了几何；而且 `no … catalog pose` 与电商包自己的 `composed catalog attitude` 互相打架。 |
| 3.6 明确不做（9 图、批量、8K 词、全量重跑、加字段） | 同意 | 与 4.4 一致。 |
| §4 步骤 1：等额度后跑一次 B0 六宫格验证 3.1 | 同意执行，但对判据保留 | 已授权、已绑定哈希，应照跑。但 1254 px 六宫格单格约 390 px，接触阴影与面料明暗在这个分辨率下很难判定；评审时要承认这一局限，之后的验证应改用动作 2 单张（母版 1）。 |
| §4 步骤 2：有效则一次提交 3.2 + §2a 扩全包 + 3.4 | 不同意 | 与同文"每步只改一个变量组"自相矛盾；三件事应各自 1 张图验证。 |
| §4 缺项 | — | 前一会话方案里**没有**地面/墙/支撑（P2）与锚点忽略项（P3）两条；我把这两条排在表情与姿势几何之前。 |

### 5.4 对《lighting-pilot》§2 现状核实与图像观察

| 前一会话表述 | 判定 | 理由 |
|---|---|---|
| "通用情绪覆盖风格：是" | 同意事实，不同意其权重 | 管线事实我核对过（`tools/style_preview.py` 逐字写入 Head/gaze）；但可见影响弱（5.2 第 2 行）。 |
| "六场景破坏系列：C 模式存在；B 模式不受影响" | 不同意后半句 | B 模式被折叠成一句无地面无墙的背景，是电商图悬浮感的来源之一；"不受影响"是漏判。 |
| "视觉要求只进入 QA：部分" | 同意 | — |
| "状态定义无矛盾；风格目标偏离缺处置路径" | 证据不足（未在本次范围内核对） | 本次目标是出图效果，未逐条核状态机。 |
| 电商图："六格匀光、无明暗过渡、无接触阴影、无分离" | 同意 | 2.1 表逐格一致。 |
| 电商图："第 2/5 格低头冷感表情与 neutral approachable 冲突" | 证据不足 | 我读到的是"垂目/平静"，冷感不明显；低头是几何指令的结果，候选未改几何。 |
| 美式图："第 1/2/4 格贴墙无纵深" | 部分同意 | 第 1/4 格属实；第 2 格有柱面与站台纵深。 |
| 美式图："姿势偏站桩" | 不同意 | 见 5.2 第 3 行。 |
| 美式图漏项 | — | 前一会话未提：涂鸦墙抢戏（第 1 格）、`14 Street`/`KEEP CLEAR` 环境文字、第 5 格包被压且贴边、第 6 格鞋色在霓虹下不可判、以及**风格与服饰错配**（pack `anti_categories` 含"西装"）。 |
| 日系图："暖调成立；第 2 格编造招牌；第 3 格新增咖啡杯" | 同意 | — |
| 日系图漏项 | — | 第 6 格米色西装贴米色亚麻背景分离度最低；第 5 格货架密集；整体暖调令西装与白 T 偏黄，电商用途有色彩风险。 |

### 5.5 对《lighting-pilot》§3 方法卡

| 来源 | 判定 | 理由 |
|---|---|---|
| Studio Nicholson（Look 3 / Look 10 + Lismore 商品页） | 同意 | 我看的是同两张 look 图与同一商品页，观察一致；补：Look 1 的 Barra 牛仔裤商品页也有地平线与鞋下阴影，说明"落地"在该品牌是商品页级别的默认。 |
| Profoto 大衣教程（文本 + 图） | 同意 | 补：教程还提到"用黑板吸光加对比"，我判为电商不宜默认（深色牛仔与深棕鞋会吃细节）。 |
| Profoto 导模 / 布景（仅文本） | 同意 | 我另外看了两张页面图，均为幕后照，无光影证据，与"仅文本"结论等价。 |
| broncolor（视频未看） | 同意 | 我也只取到摘要；"白底白品靠阴影保边缘"来自同页另一篇的摘要。 |
| OpenAI 指南 | 同意 | — |
| "用户对光影的真实意见：未收集" | 同意，且是最大的证据缺口 | 两次会话都是评审者自评；真实用户偏好未采样。 |
| 拒绝项：卷袖等造型操作、硬光 | 同意 | — |

### 5.6 分歧汇总（按重要性）

1. **病因排序不同。** 前一会话把"表情冷感 + 姿势站桩"与"平光"并列并落地成 §2a 与 persona 改动；我认为可见证据只支持"平光 + 无地面/墙 + 锚点泄漏"，表情与姿势几何排在其后，且"低头"是几何而非情绪词造成。
2. **B 模式六格背景折叠与地面缺失被漏判**（pilot §2 写"B 不受影响"）；这是我方案里的 P2，前一会话方案中没有对应项。
3. **身份锚点忽略项缺失**（P3）前一会话未提；牛仔裤变浅是电商图上唯一可见的服饰硬事实漂移，且与锚点图特征吻合。
4. **改后 pack 有服饰部件词与条件冲突**（`pocket flaps` / `hands in a pocket` / `weight on one leg` / `direct gaze`），前一会话文档未自检这一点。
5. **验证仪器**：六宫格不适合判定接触阴影与面料明暗；同意跑已授权的 B0，但之后应用单张。

## 6. 落盘与未做到的事

- 本文是本次唯一新增文件；`git status` 在写入前干净。校验命令：`python3 -m unittest discover -s tests -p "test_repository_contract.py"`（结果记录在提交信息与汇报中）。
- **未做到**：
  - broncolor 文章正文是视频，未观看，只取到摘要；
  - `product-marketing.json` 命中 554 条只实读了前 12 条文本，其 sourceMedia **未看图**（看图的 5 张全部来自 `ecommerce-main-image.json` 命中项）；
  - 未运行全套 unittest（起手说明有 3 条既有失败，不在范围），只跑了公开路径扫描；
  - 未做 DeepSeek/Gemini 交叉审（起手明令禁止）；
  - 未生成任何图片；所有"预期可观察变化"都是待验证的预测，不是证据；
  - 三张预览图的模型与种子未知，所有关于"锚点泄漏"的说法是推测。

