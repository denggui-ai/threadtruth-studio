# 2026-09-16 执行计划：先跑已授权 B0，再用 1 张独立图验证光线 / 锚点 / 裁切

Owner 于 2026-09-16 对 [独立重蒸馏](2026-09-16-independent-distillation.md) 的推荐第一步回复「同意执行」。本文把"执行"拆成两步，写清每一步谁做、改什么、看什么。本记录由 Claude Code CLI 编写，该环境无原生图片生成能力（`tool-blocked`），**本文不生图、不改任何运行文件、不申请新授权**。

## 0. 硬约束（先于一切）

- 已授权的 B0（运行 `pilot-ecom-candidate-20260915`，批次 `ecom-b0-pilot-01`，上限 1 次）绑定了当前 `prompts/ecommerce-studio.txt` 与 pack 的 sha256。**在它执行并 ingest 之前，`skills/`、`tools/`、`tests/`、`evals/` 下任何文件都不能动**，否则执行包 §0 的哈希核验失败、授权作废。
- `tools/style_preview.py` 目前只有动作 0（六宫格）入口；动作 2 单张的提示词没有真实入口可产生。第二步需要先加一个最小入口，属代码改动，只能在第一步完成后做，并且新一次生成需要 Owner 另行授权（1 次）。
- 本环境不做 API / CLI / 第三方生图替代；不调 DeepSeek/Gemini 交叉审。

## 1. 第一步（不变）：在 Codex/ChatGPT 宿主按执行包跑 B0 一次

执行者：具备原生参考图生图能力的宿主，在实验 checkout `.worktrees/pilot-ecom-light`（分支 `exp/pilot-ecommerce-lighting`）内按该运行目录 `EXECUTION-PACKET.md` §0–§4 逐步执行；哈希核验不过就停。

评审：用 [lighting-pilot](2026-09-15-ecommerce-studio-lighting-pilot.md) §7 冻结的对照标准，另外补三问（来自独立蒸馏 4.1）：

1. 六格是否仍是同一句背景、有没有地平线或墙面（预期：仍没有，因为 `_mode_scene` 未改）。
2. 牛仔裤色深是否回到源图的深靛蓝（预期：不一定，因为锚点忽略项未加）。
3. 第 2/5 格是否仍"低头"（预期：仍会，因为 §2a 只换情绪来源，几何未改）。

评审时承认仪器局限：1254 px 六宫格单格约 390 px，鞋下接触阴影与面料明暗只能粗判；B0 结果只回答"光线描述方向对不对"，不回答"够不够"。

## 2. 第二步：B0 ingest 后，改四处并用 1 张独立图（动作 2，母版 1）验证

以下改动在实验分支新提交中一次应用（它们互不冲突、都不碰服饰事实），然后重新 `prepare`、登记新运行、申请 1 次动作 2 授权。改动文本逐字如下，落地前不再自由发挥。

### 2.1 P1 · `references/styles/ecommerce-studio.pack.yaml` → `lighting_palette`（替换现有 95 词版本）

```yaml
lighting_palette: >
  one large soft key light from camera-left, slightly above eye level;
  soft fill from camera-right at about one third of the key so the shadow side stays readable;
  gentle shadow transition across the garment so weave and construction stay visible;
  a soft contact shadow under the shoes and a faint tonal gradient on the seamless backdrop;
  neutral white balance, true-to-product color, highlights hold detail;
  identical light direction, softness and ratio in all six images.
```

理由：去掉 `sleeves, lapels, pocket flaps`（光线字段不写服饰部件），词数从约 95 压到约 60，四段顺序不变。

同文件 `model_persona` 改为条件式，去掉与坐姿母版和视线几何冲突的措辞：

```yaml
model_persona: neutral approachable expression, relaxed jaw and shoulders, gaze as given by the pose line, weight naturally on one leg when standing, hands at ease at the side or resting on an accessory already shown in the reference, composed catalog attitude, no exaggerated posing
```

### 2.2 P3 · 身份锚点句补忽略项

- `tools/style_preview.py::_prompt` 中的锚点行改为：
  `Attached image {N} is an identity-only anchor: keep face, hair, apparent age and body proportions; ignore its garments, denim wash, lighting, backdrop, pose and crop; never treat it as outfit authority.`
- `references/prompt-build.md §4.2` 预览公式的 `[core 安全主体]` 之后补一行同义说明，与 §4.0a 第 4 条对齐（§4.0a 本身不改）。

### 2.3 P4 · 全身格 Framing

`layout_contract.framing` 为 `full-body` 的格，提示词行改为：
`Framing: full body visible, feet and shoes fully inside the frame with a small margin below the soles`
半身格（`half-body-permitted`）不变。

### 2.4 P5 · 首行真实感锚词

动作 0 首行 `Create one action-0 preview for style …` 之后加一句：`Photorealistic e-commerce studio photograph.`；动作 2 单张入口首行直接写 `Create one photorealistic e-commerce studio photograph for style ecommerce-studio, pose template 1 (SIDE_TURN_STANDING), full body.`

### 2.5 动作 2 最小入口（代码改动，范围到此为止）

在 `tools/style_preview.py` 加 `prepare --action 2 --pose 1` 分支：复用动作 0 的服饰事实、锚点、Mode、Mood、Attitude、Lighting、负面词拼装；只输出 1 个姿势块；负面词按 `prompt-build.md §3a` 成片阶段（含 `no collage, no grid …` 与全身追加 `cropped shoes, cropped bag, cropped hem`）；画幅按 `modes-scenes.md §4` 电商主图默认 `1:1`（或 Owner 指定）。不加新状态、不加新 schema 字段。测试只加一条：动作 2 产物含且仅含一个 `POSE 1` 块、含成片阶段负面词。

**不在第二步做的**：P2（B 模式地面/墙/支撑与 `_mode_scene` 读 `pack.scenes`）、C 模式场景收敛、六母版几何、§2a 扩到 24 包、提示词顺序重排。这些各需单独一张图，且前两者涉及运行时规则，先看第二步结果。

## 3. 第二步的评审表（同一张独立图，先事实后视觉）

| # | 问题 | 判定 |
|---|---|---|
| 1 | 五件核心单品颜色/结构/长度/鞋包是否与源图一致；牛仔裤是否深靛蓝 | 任一失败为阻断 |
| 2 | 西装左右两侧明度是否可辨不同；鞋下是否有软阴影；背景是否有渐变 | 三项各答是/否 |
| 3 | 鞋是否完整在框内且下方有留白 | 是/否 |
| 4 | 表情是否中性亲和、头部是否仍"低头" | 描述 |
| 5 | 与公开的 `ecommerce-studio.jpg` 第 1 格并排：评审者更愿意用哪张、为什么 | 允许"无差异 / 都不合格" |
| 6 | 调用数、失败数、人工干预数 | 数字 |

模型版本与种子仍未知，标未知；更讨喜的随机人脸不算方法改善。

## 4. 时序与责任

1. Codex 额度恢复 → Owner/宿主跑 B0（第一步）→ ingest → 评审表回填到 lighting-pilot 记录。
2. 评审后 Claude/Codex 在实验分支提交 §2 的四处改动 + 动作 2 入口（一次提交，`[no-cross-check]`）→ `prepare` → 登记运行与授权文本 → 等 Owner 授权 1 次动作 2。
3. 动作 2 结果按 §3 评审；有效再决定 P2 与其它方向，每次仍只改一个变量组、只看一张图。

## 5. 状态更新（2026-09-16，Owner「作废 B0 授权」后）

- 第一步取消；§2.1–2.5 已在实验分支落地（pack 瘦身、试点 slug 三句、`single-prompt` 入口与测试），其余 23 个预览提示词逐字节不变。
- 实现与本文 §2.2 的措辞差异：锚点句保留原前缀 `is identity-only: preserve …` 再接忽略项，以维持既有测试断言；`denim wash` 改为通用的 `garment colors and washes`。
- 候选 v2 运行：`pilot-ecom-candidate2-20260916`（本地忽略目录），动作 2 母版 1 提示词位于该运行 `prompts/ecommerce-studio.action2-pose1.txt`。**尚无授权，未生图。**
- 首行真实感锚词实现为风格无关的 `Photorealistic photograph taken with a real camera; not an illustration or render.`，而非本文 §2.4 的电商专用措辞；动作 2 入口是独立子命令 `single-prompt`（不是 `prepare --action 2`），只写 `prompts/<style>.action2-pose<N>.txt`，不改 `evidence.json`。
- **2026-09-16 授权登记**:Owner 原话「授权电商 B2 母版 1 一次」,登记为运行 `pilot-ecom-candidate2-20260916` 的不可变批次 `ecom-b2-pose1-01`(styles=[ecommerce-studio],maximum_calls=1,scope=serial-native-generation;no-auto-retry;授权文本 sha256 `7985796d…`,存于该运行 `authorizations/`,本地忽略目录)。执行包:该运行目录 `EXECUTION-PACKET.md`(宿主加载核验 → 1 次调用 → 落盘与画幅元数据检查 → 生成记录 → 人工六问评审)。绑定:提示词 sha256 `7a8430fb…`,pack sha256 `c4896360…`,提交 `2c6244e`。本环境 tool-blocked,未生图。

## 6. 状态更新（2026-09-20，取代 §5 的“未生图”状态）

### 6.1 B2 母版 1：已验证并获 Owner 接受

- 运行：`pilot-ecom-candidate2-20260916`；输出：`native-outputs/ecommerce-studio.action2-pose1.png`。
- 输出 sha256：`77d88813b1f64f92134b54c9fa08ce9109c7823d382cf4267276275b4622f56b`；尺寸 `1254×1254`；`1:1` 元数据检查通过。
- 六问：①五件核心单品、颜色与长度保持，牛仔裤为深靛蓝；②西装两侧明暗、鞋下软阴影、背景渐变均可辨；③鞋完整且鞋底下有留白；④表情中性亲和，没有被“低头”语义压成冷漠；⑤相较旧公开图第 1 格，候选图的方向光、接触阴影和全身边界更清楚，因此优先候选图；⑥调用 `1`、失败 `0`、人工修形 `0`。
- Owner 回复「可以接受」。这只证明 P1/P3/P4/P5 组合有效，不把随机人脸差异算作方法改进。

### 6.2 P2（B 模式场景落地）：已实现并用母版 2 验证

- 提交：`1ecfb87`。`_mode_scene` 对 B 模式按姿势读取 pack 的六条场景；电商 pack 增加地面/墙板/坐姿方台等低干扰棚拍支撑。
- 回归测试先红后绿；试点测试 `6/6` 通过。全量验证除 3 个已知历史公开证据失败外通过（`86 passed`，另含 `26` 个 subtests）。
- 运行：`pilot-ecom-p2-pose2-20260920`；输出 sha256：`b920973d540c596f145f309ba02ac96657894564752a2a356c09c3a926336fd1`；尺寸 `1254×1254`；`1:1` 通过。
- 观察：墙面依靠关系、肩背接触阴影和可见地面均出现，五件核心单品继续保持；因此 P2 对“场景不能落地”的问题有效。

### 6.3 新公开六宫格候选：已生成，等待真人评审

- 运行：`pilot-ecom-public-p2-20260920`；批次：`ecom-public-p2-grid-01`；只执行 `1` 次原生调用，无自动重试。
- 提示词 sha256：`f6481f6d46dacc56867bf7fd879fe150ed7625b0eebda09e0316fc3435fa274e`。
- 原生输出：`native-outputs/ecommerce-studio.png`；sha256：`9965b3ffd6cee55a50905e7c7c43e44c1aa094a102354631ce4eafb66c713c69`；尺寸 `1254×1254`；`1:1` 检查通过。
- 机器流程状态：`awaiting-human-review`。初步观察为六格同人同套装，墙面、地面线、坐姿方台和接触阴影比旧公开图更明确；尚未写真人 review、未 compose/audit/approve/promote，也未替换公开证据。
- Owner 随后确认画面可通过，但要求评估并锁定各姿势的头部左右方向。该图保留为 P2 视觉证据；方向规则更新后提示词哈希已变化，因此不再作为可 promote 的当前规则产物。再次生成须另获授权。

## 7. 24 风格共用头部关系（2026-09-20，实验候选）

- Owner 重新评估后选择“自然与风格适配优先”，明确要求共用原则、减少硬编码。本节取代 `7c9e9f8` 的固定左右方向方案；§6 的图像、哈希与历史验收保留。
- `fixed(shared-head-gaze)`：两套头部表合为一套身体关系表；去除固定左右、低头、避开镜头及通用韩系情绪要求。表情沿用各自 `model_persona`，预览和单图共用一段说明；摄影试点范围与头部逻辑解耦。未改 24 个 pack、图片、CLI 或证据 schema。
- 静态验证：24 个风格的预览和全部 144 个单姿势提示词检查通过；修改共用头部关系能同时传入两种输出，灯光、场景、构图字段不变。pack-lint 24/24、trigger-eval 全部断言及 JSON/diff 检查通过。
- 全量 `python3 -m unittest discover -s tests`：147 项，144 通过、2 failures、1 error（104.541s）。失败仍为下列三个公开证据检查；本次全部风格的 prompt 均已改变，旧证据不能代表当前规则，未放宽发布校验：
  - `test_build_release.ReleaseBuildTests.test_allowlist_release_excludes_development_material`
  - `test_demo_media.DemoMediaModuleTests.test_combined_public_case_validation_accepts_primary_and_auxiliary_cases`
  - `test_primary_demo.PrimaryDemoTests.test_style_index_covers_every_pack_without_claiming_planned_images`
- `deferred(current-rule-public-evidence)`：当前不发布、不重写旧哈希、不自动重生历史图库。上述失败是实验候选的发布限制，不是全绿。
- `deferred(head-gaze-visual-validation)`：本轮生图调用 0。后续明确授权后，电商、韩系冷感、日系生活、运动休闲使用同一服饰与身份参考，各一张六宫格，只改变头部规则；比较头肩自然度、服饰遮挡、动作合理性、风格表达、机械重复，不按左右数量评分。没有改善或发生服饰/姿势退化时修订共用原则，不叠风格例外；四种通过也不宣称 24 风格全部实测。
- 声明式 eval 79–80 已补入风格独立性及不露脸/非人像覆盖场景，尚未运行宿主行为评估。命令行样张工具仍限真人六姿势，输出形态优先级由 skill §1a/§2 指令保证；自动拼装测试不证明该宿主行为或视觉效果。

## 8. 自然头部规则：电商单张预览实测（2026-09-20）

- Owner「同意执行 请你注意不要过度工程化」授权先测电商一张；批次 `ecom-natural-head-01`，原生调用 1、失败 0、重试 0。运行 `pilot-ecom-natural-head-20260920`，代码 `cb34dae`。
- 与 §6.3 的原始提示词逐行比较，差异仅为共用头部说明及六行头部关系；同一服饰图、身份图、摄影参数与场景，不把旧六宫格作为生成参考。
- 提示词 sha256：`1540685e7fd2d3c26ccb5ba007c84cfb340569aaf40b49866df7f320d5299635`；原图 `native-outputs/ecommerce-studio.png` sha256：`d40f8e6ae9f5d68a9a5ebb0ba328730aaaae2ed71424da39eb9595ef51d51d3b`；1254×1254，1:1 元数据通过，已 ingest。模型/种子未知；生成记录时间为工具返回完成时刻，文档版本日期沿用现有记录契约。
- 目测：第 2、5 格由低头转为抬头，头颈无明显过度扭转；五件主要单品仍可见，但第 2 格抱臂遮住较多前胸，第 3 格出现托腮。六格脸部仍主要偏画面右侧，未体现减少机械重复的目标。细微服饰结构未作通过认定。
- 结论：本次显示固定低头约束已解除，不能认定整体优于 §6.3 旧图。身份参考本身也朝右，可能影响结果，但单次对比不能据此确定原因。
- `open(head-gaze-repetition)`：按停止条件暂停扩测其余三风格；没有自动重试、改提示词或批准发布。保留结果供 Owner 比较，不追加逐风格方向表。
