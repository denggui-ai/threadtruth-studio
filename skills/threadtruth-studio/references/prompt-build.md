# 姿势母版 + 头部视线 + 负面词 + image_gen 调用 + 单张重试(core,风格无关管线)

> **行为等价基线:** 抽取自 `korean-fashion-editorial/references/prompt-build.md`,**护栏逐字保留**;唯一抽象点 = §4.1/§4.2 公式里"韩系底座/场景"→ **pack 变量**;**风格美学负面词下沉到 `pack.negative_delta_add`**(core §3a/§3b 只保留通用安全/反拼图/保真/质量负面词,core 在预览+成片两阶段经 §4.1 商品事实守卫过滤后 append 本组 pack 负面词)。
> **铁律:** 原六姿势为默认,仅 §1b 缺背面资料分支允许明示替代第六张;闭集、串行、分阶段负面词与 source-truth 逻辑继续保留,不得放宽 B7、安全或服饰保真。

## Contents
- §1 六个姿势母版 / §1a 输出形态覆盖层 / §1b 缺背面资料的第六张替代 / §2 头部视线 / §3 负面词(3a 成片 / 3b 预览 / 露肤追加) / §4 image_gen 规范(4.0 闭集串行计数 / 4.0a 首张身份锚点 / 4.0b 批次画布契约 / 4.1 成片公式 / 4.2 预览公式 / 4.3 预览→成片红线 / §4.4 落盘) / §5 QA / §6 高风险 fallback / §7 单张重试

## 1. 六个原始姿势母版(任何模式·任何风格都继承)

| # | 姿势 | 母版名 |
|---|---|---|
| 1 | 侧身回转站姿 | SIDE_TURN_STANDING |
| 2 | 侧身倚靠墙面 | SIDE_LEANING_WALL |
| 3 | 端正半身坐姿 | UPRIGHT_SEATED |
| 4 | 正面轻步迈步 | FRONT_LIGHT_STEP |
| 5 | 微前倾俯身 | SLIGHT_FORWARD_LEAN |
| 6 | 背身回眸 | BACK_TURN_GLANCE |

默认搭配流程除 §1b 的明确例外,不得替换为普通商品站桩 / 普通街拍 / 普通 lookbook / 写真姿势。用户明确要求详情页细节 shot 时,沿用 `modes-scenes.md §4` 已有编号覆盖规则,仍须真实素材支持;这不是自行改默认姿势的权限。pack 可经 `pose_masters` 声明风格化增量,但**不得删减这 6 母版**。

## 1a. 输出形态覆盖层(仅 opt-in 或安全降级触发)

默认输出形态 = **真人模特服饰人像**,沿用 §1 六姿势母版与 §2 头部视线。用户未指定输出形态时,不得主动打断追问;在识别卡给一句可改提示即可。

允许的覆盖:
- **不露脸 / 局部 / 切头:** 仍是人像输出,可继承 6 姿势母版;但头部视线改为 `face out of frame, face naturally obscured, cropped below the nose or from neck down when composition allows, no identifiable face, garment remains the focus`。不得复刻源图真人身份。若使用母版 6,`BACK_TURN_GLANCE` 的回眸只保留背身/肩线姿态张力,不得要求露脸或看向镜头。
- **平铺 flat-lay:** 非人像输出;跳过 §1/§2 的真人姿势和头部视线,改为 `clean flat-lay product composition on a low-distraction surface, garment laid naturally, full outline visible, front/back/detail views as requested, no human model, no face`。
- **挂拍 hanger:** 非人像输出;跳过真人姿势和头部视线,改为 `garment hanging on a simple hanger or rail, low-distraction background, full silhouette visible, no human model, no face`。
- **人台 / 假人 / ghost mannequin:** 非真人身份输出;跳过真人头部视线,改为 `ghost mannequin or simple mannequin product presentation, no human model, no realistic face, no hair, garment shape supported clearly, low-distraction studio setting`。

非人像闭集构图编号(动作1逐张成片、动作0六宫格预览都使用同一编号语义):

| # | 平铺 flat-lay | 挂拍 hanger | 人台 / ghost mannequin |
|---|---|---|---|
| 1 | 正面全轮廓平铺,完整展示长度、肩线、下摆 | 正面挂拍全轮廓,衣架/横杆低存在感 | 正面人台全轮廓,服饰结构被清楚撑起 |
| 2 | 背面全轮廓平铺,保留后片结构与后摆 | 背面挂拍全轮廓,保留后片与后摆 | 背面人台全轮廓,保留后片结构 |
| 3 | 领口、肩部、袖口或腰头细节 | 领口、肩部、袖口或腰头细节 | 领口、肩部、袖口或腰头细节 |
| 4 | 面料纹理、纽扣、拉链、logo/图案等可见细节 | 下摆、裤脚、开衩、五金或图案细节 | 面料纹理、纽扣、拉链、logo/图案等可见细节 |
| 5 | 轻微 45° 造型平铺,显示厚度/层次,不扭曲版型 | 侧向 45° 挂拍,显示厚度/垂坠 | 侧向 45° 人台,显示版型体积 |
| 6 | 折叠/搭配展示,只包含参考图里已有鞋包配饰 | 低干扰搭配挂拍,只包含参考图里已有鞋包配饰 | 细节/配饰关系展示,只包含参考图里已有鞋包配饰 |

非人像输出仍遵守一套 outfit 一组、最多 6 张、串行、计数、服饰保真、风险与 tool gates。它只改变"呈现形态",不允许并发、多套混合、API fallback 或放宽安全。非人像输出保留经 §4.1 `STYLE_VISUAL` 商品事实守卫过滤后的 `pack.visual_language` 与 `pack.lighting_palette`,但其中任何人物、真人、portrait、pose、street portrait、editorial model 等语义都必须转译为服饰呈现、商品构图、材质光线或低干扰场景,不得据此拉回真人模特。`pack.model_persona` 中的脸部、表情、姿态、身份词忽略或转译;克制、松弛、高级、低调、冷感等气质词可保留为光线/场景/构图倾向。童装敏感品类的安全降级优先使用平铺/挂拍/人台,并在前台明示。

## 1b. 缺背面资料的第六张替代(真人/不露脸搭配图)

**六张是交付数量,原六姿势是默认方案。** 调用前先核识别卡的素材可见范围:

- 有同款真实背面图且所需结构清楚:保留 §1 全部六母版。AI 生成的背面、同类/另一 SKU 图片和文字描述都不能充当背部事实图。
- 正面清楚、前五姿势可在实拍支持的正面/前侧范围内完成,但没有足够背部事实:只把第六张 `BACK_TURN_GLANCE` 替代为 `FRONT_RELAXED_STANDING`(正面自然站姿),仍交六张独立图。前五母版、身份、服饰、风格和画布不变,不新增姿势库或风格包字段。
- 用户明确要求“原六姿势不变”“背部结构图”或同等要求:不能自动替代,先索取真实背面图或请用户确认第六张替代。不可把“凑满六张”当作编造后片/扣位/开衩的授权。前五也无法在已知范围完成时,补对应素材或暂停该编号;不连带任意换姿势。非人像的背面构图不套用此真人例外,所需背部事实仍须补图。

在门禁完成后、提示词输出/预览/独立生图之前明示一次:
“背面资料未提供,第六张改为正面自然站姿;前五姿势保留,共六张。只展示素材支持的范围,不验证背部结构。”
通常的六张搭配图请求可沿本规则继续,不新增必答问卷;明确与用户姿势要求冲突时才确认。明示替代本身不产生生图或额外重试授权。

**第六张动作与构图:** 全身正面、躯干直立、双脚稳定落地,不迈步、不倚墙/家具、不坐、不俯身、不做侧身回转或越肩回眸。双手自然放松,原图有包时可一手提原包,另一手避开门襟/腰带/关键结构;不为制造差异新增配饰。保持自然杂志感,头颈中性放松,表情依所选风格,不靠扭头或换背景制造第七种“动作”。

每条替代提示词把姿势块与头部关系一起替换,不用母版6的越肩词:

```
POSE 6: FRONT_RELAXED_STANDING — full-body frontal relaxed standing,
upright torso, both feet planted, no step, no wall or furniture support,
no sitting, no forward lean, no side-turn or over-shoulder glance.
Arms relaxed; retain the original bag only if present in the source,
keep closures and key garment construction visible.
Head/gaze: relaxed neutral neck alignment with the frontal standing body.
Show only source-supported front/front-side construction; do not invent or expose unknown back details.
```

与前五的区别按身体动作核对:第1张侧身回转、第2张倚墙、第3张坐姿、第4张迈步、第5张俯身;第6张静止正面站立。只换裁切、表情、视线、背景不能证明不重复。实际画面重复或露出无依据背部结构=`qa-retry`,按原调用/重试门禁处理,不能降为“多角度变化”通过。

动作0、动作1、动作2(选中第6张测试)和动作3使用同一实际姿势计划;预览第六格、成片第六张与第六条提示词一致。不露脸继续执行 §1a 遮脸规则,不得因新头部句要求露脸。替代编号6沿用全身安全边距、裁切负面词与场景逻辑;若场景文字预设“背转/越肩”,只去掉与当前动作冲突的姿势词,保留风格光影与环境。

## 2. 头部方向 / 视线(24 风格共用,服从身体姿势)

头部只保留与身体姿势必要的关系。左右、抬低头和是否看镜头不固定;表情沿用所选 pack 的 `model_persona`,视线配合已有动作和场景,不额外发明道具。直视镜头不等于亲和,低头也不等于冷感。服饰展示和自然头肩关系优先。

| 图 | 头部 / 视线关系 |
|---|---|
| 1 | 转头与身体回转协调 |
| 2 | 头颈放松,符合倚靠关系 |
| 3 | 头部与坐姿平衡 |
| 4 | 转头与行进动作协调 |
| 5 | 头颈顺应前倾,不强制垂目 |
| 6 | 保留越肩回看,避免过度扭颈 |

§1b 替代第六张时,使用正面站立的自然头颈关系,不注入母版6的越肩回看;不露脸仍由 §1a 覆盖。

真人模特的预览、独立图及 prompts-only 在姿势块之前使用下面的共用说明一次;整组以“结合动作和场景形成自然变化,避免机械重复”为目标,不设左右数量、直视比例或角度配额。

```
Head/gaze guidance: choose head orientation and gaze naturally for the body action and existing scene, with no fixed left/right direction, head tilt or eye-contact quota; expression follows the selected style's Attitude; preserve garment visibility and natural head/neck alignment without adding props; vary naturally with action and scene to avoid mechanical repetition.
```

§1a 的输出形态覆盖优先于本节:不露脸时用原有遮脸/切头说明替换头部表及共用说明;平铺、挂拍、人台跳过本节。不因回眸要求露脸,不把非人像拉回真人。

## 3. 负面词(分阶段;**预览阶段和成片阶段不同**)

> ⚠️ 六宫格只在**预览阶段**允许,成片阶段是 6 张独立图。"禁合成页"类负面词**只在成片阶段拼**,预览阶段必须豁免(否则六宫格生不出来)。
> ⚠️ **风格美学负面词(如 no influencer style / no catalog look)= 视觉轴,由 `pack.negative_delta_add` 提供;core 在预览+成片两阶段都把经 §4.1 商品事实守卫过滤后的本组 pack 负面词 append 进去。** core §3a/§3b 只保留**通用项**。

### 3a. 成片阶段通用负面词(动作 1 逐张独立成片,每条 prompt 都拼;通用,风格无关)
```
no collage, no grid, no contact sheet, no multi-panel layout, no split-screen,
no multiple poses in one image, no lookbook composite, no poster, no text layout,
no magazine page layout, no multiple models, no logo invention, no fake text,
no garment redesign, no color change, no length change,
deformed hands, extra fingers.
```
**+ append 经 §4.1 商品事实守卫过滤后的 `pack.negative_delta_add`**(风格美学负面词,如韩系 = no influencer style / no aegyo / no sweet idol smile / no e-commerce catalog look)。

**全身姿势(母版 1/2/4/6)成片时追加**(B4:全身构图必须鞋包下摆完整):
```
cropped shoes, cropped bag, cropped hem.
```
**半身姿势(母版 3/5)不拼这三条** —— 半身构图本就自然截到上半身/膝上,鞋不在画面属正常取景,不算"裁切丢失";但仍禁止**被遮挡丢失**(如包被手臂压没、下摆被家具吃掉)。

**非人像输出不按真人姿势母版 1/2/4/6 分类。** 平铺/挂拍/人台按 §1a 构图编号拼裁切约束:#1/#2/#5/#6 需要全轮廓或搭配关系清楚,可追加 `no cropped garment outline, no cropped hem, no cropped accessories`;#3/#4 是刻意细节图,**不追加** full-body/cropped shoes/bag/hem 或 full-outline 裁切负面词,只要求目标细节(领口、袖口、面料、纽扣、logo 等)清楚完整。

### 3b. 预览阶段负面词(动作 0 出六宫格预览)
预览图本身=「一张图里 6 个姿势」,**严禁拼**任何 `no grid / no collage / no multi-panel / no multiple poses in one image`。预览阶段只拼:
```
no multiple models, no logo invention, no fake text, no garment redesign,
no color change, no length change, deformed hands, extra fingers.
```
**+ append 经 §4.1 商品事实守卫过滤后的 `pack.negative_delta_add`**(风格美学负面词同样在预览阶段拼,与基线一致)。

**露肤 / 吊带 / bra / 短裙额外追加(去性感化,safety-core R4;预览和成片两阶段都拼;通用安全,风格无关):**
```
adult model, tasteful high-fashion editorial, non-sexualized styling, no erotic mood,
no seductive expression, no bedroom context, no lingerie advertisement feeling,
no provocative pose, no upskirt, modest seated posture.
```
> 注:`adult model` 是 R4 安全主体的去性感化锁;**性别年龄轴主体(adult/child·female/male)由 core 注入**(童装走 R1 的 `child model, age-appropriate, modest…`),pack persona 禁声明。

## 4. image_gen 调用规范(服饰保真核心)

本系统 = **保留上传服饰 + 重塑姿势/头部/场景/模特**,本质是**带参考图的生成 / 编辑**,不是纯文生图。

- **默认用宿主提供的原生图片生成能力**,无需 API key,可能消耗订阅额度。入口名称由宿主决定,也可能不在 UI 中逐字显示;**不要因没看到某个固定工具名就判定不可用**。
- **若当前会话确认没有任何可调用原生图片生成能力,立即返回 `tool-blocked`。** 不读取/使用 `OPENAI_API_KEY`,不调 OpenAI Images API,不跑 `openai` CLI / `curl` / 自写联网脚本,也不要求用户开 network 绕过 host 契约。
- **成片阶段每张图独立一次 image_gen 调用**(6 张 = 6 次)。绝不在一次调用里出多图/拼图。
- **必须把用户上传的真实服饰图作为参考图传入**,按 index+role 标注:单图 `Image 1: garment reference, keep the garment exactly as shown`;多图 `Image 1: front view` / `Image 2: back view` / `Image 3: detail/fabric`。
- **不指定具体模型、快照或 API 专属参数。** 使用宿主当前提供的参考图能力;若宿主不支持参考图输入,进入 `tool-blocked`,不得改走 API、CLI 或第三方 fallback。

**多参考图事实优先级(所有成片/重试共用):** `当前已锁定 outfit/SKU 的用户上传服饰参考图 > 识别卡中的可见事实 > 已验收的生成 look-1 身份锚点 > 风格包视觉语言`。生成图永远不是新的服饰事实源;任何生成图与上传服饰图冲突时,以上传图为准。多色/多套输入先按 `recognition.md §3.4/§3.9` 锁定本组 SKU/outfit,不得把未选色或另一套参考图混进本组。

### 4.0 ⛔ B1 闭集 + 串行 + 计数护栏
成片阶段(动作 1)**强制**:
1. **一套 outfit = 一组 = 恰好 6 张闭集。** 一次生成请求只产**一组**。绝不为多套 outfit 同时铺多组(多套逐套串行,见 `recognition.md §3.9`)。
2. **串行执行,严禁并行。** 6 次 image_gen 调用**依次**进行(look-1→…→look-6),前一张落盘确认后再发下一张。**禁止同时开多个 image_gen 调用 / 多会话自调度并发。**
3. **生成后核对计数 = 6。** 全组完成后清点:应 6 张、实际几张、缺哪个 look 编号。少于 6 张不得以"差不多"收尾;但**补齐或 QA 重试也不得突破 B7 单次请求最多 6 次 image_gen 调用**。触顶时保留 `image-draft` + `qa-retry`,报告缺失/失败编号并等待用户明确授权对应的单张重试或“重试 look-1 后继续余下 5 张”,不得自动发第 7 次调用。
4. 测试动作(2)只产 1 张;预览动作(0)只产 1 张六宫格。两者都不触发 6 张闭集。

### 4.0a 真人组首张身份锚点(P1 商业一致性门禁)

动作1的默认真人模特与不露脸/局部真人输出,必须按以下顺序执行;平铺、挂拍、人台/ghost mannequin 跳过本节:

1. **首张参考角色。** 成人 look-1 可接收当前商品全部服饰源、已有原始人物身份参考、可选审美参考;逐图编号声明用途。仅服饰源决定商品事实。没有身份沿用要求时不复制服饰源中的真人;审美样图不复制脸。preview-grid 永不作首张身份参考。
2. **技术 QA 和用户选人分开。** 首张落盘核服饰硬事实、画幅、人体/安全、原始身份与明确人物条件。硬失败=`qa-retry`,停止传播。合格或仅剩不阻断的 `qa-user-review` 可记录技术接受,但成人组必须展示首张并等用户明确接受人物,再记录 `model_confirmation`、使用 `accepted_identity_anchor`。用户对当前图的整体接受可作为人物确认，不再拆开追问；单张结束与整组续生按 `flow-gates.md`，不能把满意当新增调用授权。没有用户确认不得继续后五张;选人通过不代表 `image-ready`。
3. **失败不自动加调用。** 保持 `image-draft` + `qa-retry`,保留结果和已用次数,说明失败点。明确重试授权后才执行;未决调用先恢复,不得复制任务重置预算。
4. **后五张携带全部依据。** 顺序为 `Image 1…N = current SKU garment sources`、`Image N+1…M = original identity-reference (ignore garment/pose/background/lighting)`、可选 `aesthetic-reference (do not copy identity or garment)`、最后 `accepted current look-1 = identity-only`。按文件哈希对重复身份文件去重,保留不同角色。每个新商品首张重新对照原始人物,后五张也始终携带原始依据,不只对照最近一张生成图。
5. **人物固定条件覆盖冲突的人物气质与人物负面词。** 预览、测试、成片及仅提示词都采用同一份人物条件;不删除安全/人体/商品负面词。妆发调整以用户明确允许项为准。原始人物参考和本组锚点永不覆盖新商品事实,也不自动继承旧搭配、配饰、拍摄风格或背景。人物卡只写人物,不保存旧商品。
6. **不露脸仍不补可识别脸。** 成人不露脸组固定其可见轮廓,继续遮脸/切头规则。童装仍按原安全流程:首张技术 QA 后才用 AI 身份锚点,本次成人参考包功能不扩展到儿童。
7. **单张测试续生成组。** 首张必须是本组母版1独立图,技术接受且成人人物已获用户确认;上下文商品/风格/模式/形态/画幅一致,并有新增五张授权时原图直接为 look-1,只追加 look-2…6。保留累计预算、失败历史和原始首张。其他母版测试不直接转成组六张;另行说明剩余编号和授权,不得悄悄重生第一张。

具体选人、因子交付、原始参考包及第二版任务记录见 `model-selection.md`。旧版任务执行/恢复语义保持不变,不自动升级。

### 4.0b 批次画布契约(P1 商业比例门禁)

动作1/2在第一次付费调用前,必须按 `modes-scenes.md §4` 解析并锁定一个 `canvas_contract`:

```text
target_ratio: <用户显式比例 > 用途默认比例 > 无用途默认2:3>
target_orientation: portrait | square | landscape
target_pixels: <用户显式像素,否则 unset>
batch_canvas_baseline: <首张通过比例门禁后的实际 WIDTHxHEIGHT>
```

执行顺序:

1. **先锁比例再调用。** 每条独立图 prompt 都逐字注入同一个精确比例和方向,并要求主体/服饰/鞋包下摆位于安全边距内。不能只写“竖版倾向”或依赖姿势词让 host 猜画幅。
2. **提示词不等于通过。** 原生生图 host 可能忽略比例并返回内容自适应尺寸。每张落盘后立即读取实际宽高;优先运行 `python3 scripts/image-spec-check.py --ratio <W:H> [--size <WxH>] <file>`。工具不可用时也必须用当前 host 的只读元数据能力做等价检查,不得目测比例。
3. **首张同时锁批次像素。** 用户显式给像素时,首张必须精确匹配;只给比例时,首张先通过精确比例,其实际 `WIDTHxHEIGHT` 才能成为 `batch_canvas_baseline`。真人/不露脸的 look-1 还必须同时通过 §4.0a,才能作为身份锚点;非人像组的首张只建立画布基线,不建立身份锚点。
4. **后续五张双重检查。** 每张必须同时满足目标比例和 `batch_canvas_baseline` 的精确像素尺寸。可运行 `python3 scripts/image-spec-check.py --ratio <W:H> --same-size <accepted-look-1-or-first.png> <new-look.png>` 做增量校验;整组交付前再对六张一起校验。
5. **失配立即止损。** 比例或批次像素失配属于交付结构失败=`qa-retry`;该图不得成为 identity anchor 或 accepted deliverable。停止后续未调用编号,报告已消耗调用数/失败文件实际尺寸/目标契约,等待用户明确授权单张重试或续生;不得自动突破 B7。
6. **禁止静默修形。** 不得用非等比拉伸、强裁切、加边、preview-grid 放大或无授权 outpaint 掩盖失配。用户明确要求本地后处理时保留原图、版本化保存并重跑服饰/构图/元数据 QA;若需要新原生生图,仍走付费授权门禁。

动作0预览使用独立 grid 画布,只检查其自身为单张 preview-grid;它不继承也不建立动作1的 `batch_canvas_baseline`。

### 4.1 单张成片 prompt 拼装公式(抽象点:底座/场景→pack 变量)

**`STYLE_VISUAL` 商品事实守卫(中心规则,预览/成片/prompts-only 与所有输出形态共用):** 先用识别卡中的真实服饰事实过滤 `pack.visual_language`、`pack.lighting_palette` 与会影响服饰外观的 `pack.model_persona` 语义,再注入 prompt。pack 提到的面料/材质、口袋/绑带/五金、层叠、腰线/衣长、图案/logo、配饰、廓形/剪裁/结构或搭配方式,只有在参考图已明确存在时才可作为服饰描述保留,且只能强调、不得改写。参考图未出现或无法确认时,不得给服装新增这些事实;只把相应风格意图转译为灯光、色调、低干扰背景/道具或构图氛围,且道具不得覆盖服饰。`pack.negative_delta_add` 同样不得删除参考图已有的 logo、图案、材质、结构、配饰或层次;冲突项改写为 `no added/invented ...` 或跳过。该守卫对真人模特、不露脸、平铺、挂拍、人台一视同仁。

**`lighting_palette` 场景自适应光影签名(不新增 schema):** 将这个单一字段按“光源 → 方向 → 阴影特征 → 对比/曝光”顺序解释并转译到当前场景;pack 已写明的分量必须保留,未写明或无法从字段判断的分量保持克制,不得自行补成戏剧光。方向可以随 `pack.scenes` 与输出形态做等价转译,但不得改变光影气质。光线只用于照明、塑形和呈现服饰事实,不得导致服饰改色、换材质、改廓形,不得遮挡 logo/图案/结构或凭空新增层叠与配饰。柔光、低阴影、低对比 pack 必须继续保持柔和,不得为了“光影感”统一升级成硬光或高反差。

`pack.qa_extra` 只能在出图后作为 QA 加项读取,永不注入 prompt;每条 QA 先经同一商品事实守卫。若 QA 项暗示删除、新增或改写参考图中的 logo/图案/材质/结构/配饰/层次,该项必须改写为“无新增/无改写”检查或直接忽略;core source truth 永远优先。

```
[Reference roles: look-1 = current garment source(s) plus declared original identity/aesthetic references;
 look-2..6 = uploaded garment source(s) as authoritative garment truth
 + original identity references + human-confirmed current look-1 as identity-only anchor, per §4.0a]
+ [Canvas contract per §4.0b: exact <W:H> <orientation> canvas for every
   independent image; keep the complete required subject/garment/shoes/bag/hem
   inside safe margins; no extra-tall or alternate-ratio canvas]
+ [core 注入的安全主体:按 recognition 性别年龄轴 + safety-core R1/R4
   → adult model(默认)/ child model, age-appropriate, modest(童装)/ + 去性感化锁(露肤时)]
+ [成人组:注入已选择/推荐后确认的人物条件,童装仅在用户明确选角时注入短目标,覆盖冲突的 pack 人物气质;
   未指定时不添加此块,沿用现有默认;非人像跳过]
+ [output form: 默认真人模特→用 §1 姿势母版+§2 头部视线;
   不露脸→继承姿势但改 face-obscured/cropped framing;
   平铺/挂拍/人台→改用 §1a 非人像构图,跳过真人头部视线]
+ [STYLE_VISUAL = 经商品事实守卫过滤后的 pack.visual_language + 场景自适应四段光影签名 pack.lighting_palette
   (非人像输出时再把人物/portrait 语义转译为服饰呈现与光线)]
+ [经商品事实守卫过滤后的 pack.model_persona
   (真人模特/不露脸时气质叠加;非人像输出只保留氛围/气质词,忽略或转译表情/脸部/姿态要求)]
+ [真人模特→§2 共用头部说明一次;不露脸/非人像→§1a 覆盖]
+ Pose/composition: [真人模特→本轮实际姿势 #N + 对应头部关系(默认母版,第6张可按 §1b 明示替代);
   非人像输出→平铺/挂拍/人台构图 #N,无真人头部视线]
+ Mode/scene: [真人模特/不露脸→棚拍背景 或 pack.scenes #N(对齐 modes-scenes 场景强度);
   平铺/挂拍/人台→棚拍表面/衣架/人台/低干扰商品背景;C/D 模式只把 pack.scenes #N 转译为材质、光线、色调、背景氛围或陈列环境,不得直拼真人地点场景或拉回人像]
+ Garment fidelity: keep the garment from the reference image unchanged —
  keep [颜色/材质/版型/长度/领型/袖型/肩线/下摆/纽扣/图案/logo/鞋/包/配饰 中的实际项],
  do not redesign, do not change color/material/length.
+ single image only, one model/mannequin/garment presentation only, one pose or composition only.
+ Negative: [§3a 通用成片负面词 + 经商品事实守卫过滤后的 pack.negative_delta_add (+ 全身追加 cropped 三条 / + 露肤追加)]
```

### 4.2 六宫格预览 prompt 拼装公式(动作 0,只调一次 image_gen 出 1 张图)
```
[core 安全主体] + [STYLE_VISUAL(先过 §4.1 商品事实守卫;非人像时再转译人物/portrait 语义)] + [经商品事实守卫过滤后的 pack.model_persona(非人像时只保留气质/氛围)]
+ [真人模特→§2 共用头部说明一次;不露脸/非人像→§1a 覆盖]
+ A single 2x3 grid contact-sheet preview showing the SAME one outfit in 6
  different directions.
  - 真人模特/不露脸: show the SAME one model in six pose templates
    (top row poses 1-2-3, bottom row poses 4-5-6; pose 6 follows the declared §1b substitution when back sources are missing), with head/gaze per actual pose
    or face-obscured framing when requested.
  - 平铺/挂拍/人台: show the SAME garment presentation type in six non-portrait
    composition views #1-#6 from §1a, no human model, no head/gaze instruction.
+ This is a LOW-RES DIRECTION PREVIEW, not a final deliverable.
+ Garment fidelity: keep the garment from the reference image unchanged —
  keep [实际服饰项], do not redesign, do not change color/material/length.
+ Add a small, unobtrusive single-line preview label near the bottom-right corner
  or bottom margin, no larger than about 3-4% of image height, low opacity but
  readable, never covering the model, face, garment, shoes, bag, or pose:
  "方向预览·非成片 / PREVIEW ONLY — NOT FINAL".
+ Do not place a large centered watermark across the image.
+ Negative: [§3b 预览负面词 + 经商品事实守卫过滤后的 pack.negative_delta_add (+ 露肤追加)]   ← 注意:不拼 no grid/no collage
```
> 多套不同 outfit 的预览(`recognition.md §3.9`):6 格改为「每格一套 outfit 的代表姿势」,其余规则一致。
> **摄影试点追加句(仅 ecommerce-studio,预览与动作 2 单张共用,独立于 §2 通用头部规则):** ①身份锚点句补齐 §4.0a 第 4 条的忽略项——`is identity-only: preserve face, hair, apparent age and body proportions; ignore its garments, garment colors and washes, lighting, backdrop, pose and crop; never treat it as outfit authority`;②全身母版 1/2/4/6 的 Framing 写成可见动作 `full body visible, feet and shoes fully inside the frame with a small margin below the soles`(半身母版不变);③首行后加一次真实感锚词 `Photorealistic photograph taken with a real camera`。三句都不触碰服饰事实、母版编号、负面词与安全主体;动作 2 单张按 §3a 成片负面词拼装并注入 §4.0b 精确画幅。

### 4.3 ⛔ 预览→成片的红线(逐字保留,风格无关)
1. **`preview-grid` 与 `image-ready` 严格互斥。** 六宫格预览**永远**不能当最终成片,哪怕用户主动说"预览就行/不用再出了"也必须拒绝,固定回复:"预览图为低分辨率方向示意,无法逐张做服饰保真审计,不能当成片。要拿到可用成片,需逐张重新生成 6 张高清独立图(消耗订阅额度)。要我现在开始生成这 6 张吗?"**到此停住等用户明确回答,不自动进成片。** 仅当用户明确说"生成/全部生成/动作1/好/开始"等才进成片;用户改口不生成则停在 `preview-grid` 不调 image_gen。
2. **禁止任何形式的子图提取/裁切/放大/超分。** 对预览图做切割/抠图/放大/超分的请求一律拒绝。成片必须是**重新独立调用 image_gen** 生成的单图。用户说"把预览第3格给我高清版"= 按预览阶段输出形态对应的姿势母版 3 或非人像构图 #3 **重新独立生成**,不是放大预览格。
3. **不接受去标记请求。** 预览标记是生成时画进图里的,**不得**应用户要求 P 掉/遮盖/透明化/局部重绘;遇此请求拒绝并引导进成片。
4. **预览修正至多 3 轮**,但预览永远不具备成片资格;进成片必须经用户**明确**"方向确认/全部生成/动作1"等指令。**"可以了/出图吧/就这个"等模糊词不自行推断为成片授权**——先回确认一句"那我进成片逐张生 6 张高清独立图?"得到肯定再开始。
5. 预览阶段产出状态 = `preview-grid`,绝不标 `image-draft`/`image-ready`。**升 `image-ready` 前二次核验:本组有 look-1…look-6 六个有效独立文件、无 preview-grid 残留、调用数已报告且商业 QA/用户确认已关闭**,否则不得标 ready。

### 4.4 落盘(官方 save-path 策略 + B3 沙箱 fallback,逐字保留)
- 内置模式产物默认在 `$CODEX_HOME/generated_images/...`;要保存时生成后 move/copy 到工作目录,**不只留默认路径**。
- **B3 fallback:** 若沙箱无写入权限,**不要静默失败、也不要重试制造并发**。明确告知:图已生成但落不进工作目录,实际在 `$CODEX_HOME/generated_images/`,并**列出每张缓存绝对路径**让用户自取。绝不因为"看起来没生成"就重跑。
- 不覆盖已有图,版本化命名(`look-1.png` / `look-3-v2.png` / `preview-grid.png`)。

在本组现有运行记录中逐张保留实际参考图的顺序/角色及文件哈希、原始身份参考(无则注明无)、本组首张与用户人物确认(局部修图注明原图用途)、实际提示词文本及哈希、输出路径/哈希/宽高和逐项 QA 结果。生成图不得作为服饰事实源。修正另记版本与被替代编号,保留失败图和原始记录;历史缺失的参考顺序、身份锚点或调用凭据标为 `unknown`,不得从提示词意图倒推成实际调用事实。

第六张替代时在同一记录保留 `ordinal: 6`、`original_pose: BACK_TURN_GLANCE`、`actual_pose: FRONT_RELAXED_STANDING`、替代理由、实际素材可见范围与明示/用户确认依据。实际姿势与去重 QA 以画面复核为准,提示词仅表示计划;缺失信息写 `unknown`,不倒填历史案例。

## 5. QA 审计(生成或出提示词前内部自检)

逐张检查:通过输入门禁 / 有真实服饰事实源 / 有明确生成意图 / 单图输出 / 服饰是主角 / 输出形态符合用户或安全默认(真人模特/不露脸/平铺/挂拍/人台) / 真人模特时符合本轮实际姿势计划并核动作不重复(§1b 例外不可说原六母版齐全) / 非人像时符合 §1a 构图编号且无真人头部视线 / 身体结构清楚(非人像不适用) / 头部方向合理(非人像不适用) / 场景低干扰 / **已读取元数据且符合本组 `canvas_contract` 与 `batch_canvas_baseline`** / 用途构图与留白目标到位 / 颜色材质版型保真 / pack 未新增或删除参考图不存在/已有的材质、结构、图案、层叠、配饰 / 鞋包配饰保留 / 模特身份一致(非人像不适用) / **风格底座到位(对齐所选 pack;非人像时人物/portrait 语义已转译)** / **光源、方向、阴影、对比/曝光与所选 pack 一致,柔光/低阴影 pack 未被戏剧化,光线未改变服饰颜色、材质或结构可见性** / 露肤已非性感化。

**裁切检查按姿势分类(B4):**
- **全身姿势(母版 1/2/4/6):** 鞋、包、下摆必须完整在画面,被裁掉=不合格,重试。
- **半身姿势(母版 3/5):** 构图本就到膝上/腰上,鞋不在画面属正常取景,**不算裁切丢失**;只检查"画面内应有的服饰项是否被遮挡丢失"。
- **非人像构图编号:** #1/#2/#5/#6 检查服饰全轮廓、下摆、结构线、已有鞋包/配饰关系是否完整;#3/#4 是刻意细节裁切,不得按真人全身裁切规则误判,只检查目标细节是否清楚且未被不合理遮挡。

**B8 指标性质:** 下列百分比是 **LLM 自评启发式目标,不是可测量客观指标**,**不得对用户声称"已达成 X% 保真"**:(启发式目标)单图输出正确率 100%;服饰保真 ≥95%;姿势母版保真 ≥92%;头部方向合理 ≥90%;场景适配 ≥90%;风格底座感 ≥90%。

动作1每张落盘后还必须执行 `commercial-qa.md` 的结构化逐张 QA;用户有商用意图时默认只展示图片、简短结论与影响使用的问题；详细检查报告按 `commercial-qa.md` 按需展开。任何硬服饰事实或真人身份一致性失败都保持 `image-draft` + `qa-retry`,不得直接升 `image-ready`。

## 6. 高风险 fallback

高风险品类(透明/超短裙/复杂礼服/复杂图案/强民族结构/极端前卫/大logo大文字/多层叠穿):
1. 推荐棚拍版 → 2. 建议先生成 1 张测试 → 3. 测试通过再扩展 6 张 → 4. 用户坚持直接 6 张则用更保守姿势+低干扰背景+更严格遮挡 → 5. 失败只重试单张。泳装/内衣叠 safety-core R4(去性感化 + 被拦不绕过)。

## 7. 单张重试(不重做整组)

用户说"重试第3张""第5张不好""只改图2"时,只重试指定单张。**仅用于成片阶段(`image-draft`)的单张**;预览阶段(`preview-grid`)改方向走 flow-gates 分支4b"第N格调整"。QA 发现失败只报告 `qa-retry`,**未经用户明确单张重试授权不自动调用 image_gen**。

**必须继承:** 当前已锁定 outfit/SKU 的全部用户上传服饰参考图(始终第一事实源) / 原服饰事实档案 / 原模式 / 原场景逻辑 / 原输出形态(真人模特/不露脸/平铺/挂拍/人台) / 已验收 look-1 身份锚点(真人/不露脸适用) / 原姿势编号或非人像构图编号 / 原鞋包配饰关系 / 原用途规格线索 / **原 `canvas_contract` + `batch_canvas_baseline`** / **原风格底座(所选 pack)** / 原负面规则(真人全身 1/2/4/6 拼 cropped 三条,真人半身 3/5 不拼;非人像 #1/#2/#5/#6 查全轮廓/搭配关系,#3/#4 细节图不拼真人 cropped 规则)。

- 重试 look-2…look-6:同时传上传新品服饰源 + 原始人物参考 + 已确认本组 look-1;生成图只作身份锚点。
- 重试 look-1:旧 look-1 若脸/发型身份种子可用,可在用户授权后作为 identity-only seed 与上传服饰源共同传入;若身份/人体本身不可用,必须前台说明需要重建锚点,不得静默换人。仅当后续尚未生成、旧首张未获技术接受时才可在原任务显式重试;已接受首张不可静默替换。新首张通过 QA 且成人用户确认后才继续余图;长期原始人物参考不更新。
- 若 look-6 已按 §1b 替代,继承 `actual_pose` 及其头部关系,不能因编号6自动恢复背身回眸;补足实拍背面且用户明确要求恢复时先更新计划,仍须对应生图授权。

只修复指定问题(姿势跑偏 / 头部方向错 / 场景抢戏 / 颜色变了 / logo文字漂移 / 下摆被遮 / 鞋包丢失 / 过甜美 / 过网红 / 变电商目录照)。

重试 prompt patch 模板:
```
Retry only image N. Use every uploaded garment reference as the authoritative fact source.
When a real/faceless model is used, also use the accepted look-1 as identity-only anchor;
never copy garment, pose, crop, lighting, background or accessories from the anchor over the source.
Keep the same outfit colors,
materials, silhouette, shoes, bag, accessories, same generation mode, same pose template
number or same non-portrait composition type, same output form, same [pack 风格底座] mood,
and same model identity when a real model is used.
Keep the exact original canvas contract: <W:H>, <orientation>, and batch pixel
baseline <WIDTHxHEIGHT>; keep all required content inside safe margins.
Fix only this issue: <retryReason>.
Do not redesign the outfit. Do not change the mode. Do not regenerate the whole set.
single image only, one model/mannequin/garment presentation only, one pose or composition only,
no collage, no grid, no text.
[真人模特/不露脸且 N 为全身姿势 1/2/4/6,追加: no cropped shoes, no cropped bag, no cropped hem.]
[平铺/挂拍/人台且 N 为 #1/#2/#5/#6,追加: no cropped garment outline, no cropped hem, no cropped accessories.]
[平铺/挂拍/人台且 N 为 #3/#4,不要追加真人 cropped 或 full-outline 裁切负面词;只写清目标细节必须完整清楚。]
```
