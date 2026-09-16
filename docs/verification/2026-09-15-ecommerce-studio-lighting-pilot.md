# 2026-09-15 · ecommerce-studio 光影与表情试点(实验候选,未视觉验证)

状态:**局部代码候选 + 规则干跑完成;未生图;未合并;三风格优化未完成。**
本记录串起来源、方法、修改与验证。它不是成片证据,也不改变任何 pack 的 `maturity`。

## 1. 实际基线与实验位置

| 项 | 值 |
|---|---|
| 基线分支 / 提交 | `docs/preview-task-schedule` @ `f44433c`(= `origin/main` a491646 + 1 个 docs 提交;tracked 工作树干净) |
| 说明 | 主 checkout 的 `main` 停在 `1ad4dd8`,落后 origin/main 49 个提交,不作基线 |
| 实验副本 | 新建 worktree `.worktrees/pilot-ecom-light`,分支 `exp/pilot-ecommerce-lighting`,从 `f44433c` 派生;原工作区未被 reset/clean/stash |
| 未提交改动 | 基线无;本轮全部改动只在实验分支 |
| 修改前基线检查 | `python3 -m unittest discover -s tests`:136 tests OK;`pack-lint --strict`:PASS(3 条 INFO 子串近邻,历史已知);`trigger-eval.py`:132/22/3/47/13/1 断言全部成立 |

## 2. 现状核实(旧对话线索 → 实际文件)

| 线索 | 核实结果 | 证据 |
|---|---|---|
| 通用情绪是否覆盖风格 | **是。** `prompt-build.md §2` 六行头部视线把"冷静疏离 / 不正面营业 / 避免目录照式 / 避免甜美手托腮"注入全部 24 包;`tools/style_preview.py` 逐字读取该表写进每格 `Head/gaze:` | 已归档提示词 `.threadtruth/style-previews/beige-blazer-denim-outfit-24-v1/prompts/*.txt`(本地忽略目录) |
| 六场景是否破坏系列 | **C 模式存在。** `pack.scenes` 六个不同地点逐格分配,american-street 从白天涂鸦墙跳到黄昏霓虹,光线不连贯;B 模式(ecommerce-studio)不受影响 | 公开预览 `docs/demo/style-previews/beige-blazer-denim-outfit-24-v1/american-street.jpg` |
| 视觉要求是否只进入 QA | **部分。** `lighting_palette` 只有一行形容词;方向光/接触阴影/背景分离等要求此前不在任何进入 prompt 的字段;`qa_extra` 只在出图后读取 | pack 文件 + `prompt-build.md §4.1` |
| 状态定义是否矛盾 | 未发现互相矛盾;但 `qa-user-review` 只覆盖 logo/面料/隐蔽结构,对"风格目标偏离"没有处置路径(仅"可记录优化") | `SKILL.md §4`、`commercial-qa.md §2/§3`、`flow-gates.md §2` 已逐条核对 |

已实际查看(非文本推断)的三张公开预览(beige-blazer 套装,同一 AI 模特):

- **ecommerce-studio(B)**:六格匀光,西装翻领/口袋盖/袖子几乎无明暗过渡,鞋下无接触阴影,人物与白背景无分离;第 2/5 格低头"冷感"表情与 pack 自己的 `neutral approachable` 冲突。→ 本轮试点目标。
- **american-street(C)**:六个地点六种光;第 1/2/4 格人物贴墙无纵深;姿势偏站桩;第 2 格低头冷感。→ 候选设计,未实施。
- **japanese-lifestyle(C)**:暖调基本成立;第 2 格背景出现编造英文招牌(fake text);第 3 格新增咖啡杯道具;第 2 格低头冷感。→ 候选设计,未实施。

## 3. 资料与方法卡(精简)

| 来源 | 日期 | 实际看见的证据 | 未知项 | 可迁移方法 | 不迁移 |
|---|---|---|---|---|---|
| Studio Nicholson SS26 looks(官方站,Look 3 / Look 10 成片 + Lismore Jacket 商品页图) | 页面 2026-09;图已实际查看 | 灰/白无缝背景;柔和方向光来自画面左上;夹克袖管与领口有可见渐变阴影;脚下有淡接触阴影与地平线;背景带微弱明暗梯度使人物分离;模特重心自然、手插袋、表情平静 | 具体灯具/机位/后期未知 | 方向光塑形、接触阴影、背景分离、平静中性表情 | 其品牌造型(卷袖、墨镜)、极简搭配 |
| Profoto《How to photograph a model wearing a coat for e-commerce》 | 2023-07-30;文本 + 教程图已查看 | 文字:主光从模特左侧横打制造少量阴影与对比;整组保持同一灯光以保证线上一致;曝光过高会冲掉细节,用前景补光让面料细节显现;客户想看的是材质、廓形。图:灰背景,左侧主光,大衣右侧明显更暗,脚下有影 | 灯具功率、比例数值未知 | 主光方向 + 补光比 + 一致性 + 曝光保细节 | 系带、造型操作 |
| Profoto《…direct your model for stills》 | 2023-08-04;仅文本 | 事先说明氛围与姿势;地面做标记保持位置一致;让模特换腿、转身展示背面 | 文本层分析,视觉未核实 | 重心/换腿、整组位置一致 | — |
| Profoto《…design your set and style your model…》 | 2023-07-25;仅文本 | 道具会抢产品注意力;无缝背景白/灰 | 文本层分析,视觉未核实 | 电商棚拍不加道具 | 杂志式道具 |
| broncolor《How to Set Up your Lights for Ecommerce Fashion Shoots》 | 未标日期;仅文本(视频未看) | 三灯方案;强调曝光与色彩绝对一致;白底白品要靠阴影保住边缘 | 视频画面未核实 | 边缘靠阴影分离 | 设备型号 |
| Profoto《Hard Reflectors White》 | — | **未访问**(本试点为柔光方向,硬光不在范围) | 缺口 | — | — |
| OpenAI image prompting guide | 页面 2026-09;文本 | 用可见细节描述光线/材质;人物动作要写身体取景、视线、与物体的互动;相机参数只是外观线索 | 具体宿主是否同一模型未知 | 写"可见关系"而非形容词 | API 参数、模型名 |
| motiful/product-shots presets + task-prompts | 仓库 main;仅结构层 | PHOTOGRAPHY_STYLE 块逐字重复进每张;单张只变镜头/裁切/姿势 | preset 正文未取到(索引只返回标题) | "整组固定光线块,单张变姿势" | 九图、发型验证视图 |
| nano-banana-pro 提示库 | README 仅 | 未找到服饰人像商业案例入口 | 未核 | — | — |
| 本项目素材/输出/反馈 | 见 §2 | 24 张预览人工验收通过(几何/事实),没有针对光影/表情的用户意见 | 用户对光影的真实意见:**未收集** | — | — |

拒绝或存疑:卷袖/夹衣等造型操作(违反保真);硬光方案(与 pack 柔光基调冲突,未研究);任何把研究图当运行时输入的做法。

补充(同日稍后):product-shots 预设正文、nano-banana 库内容、openai-cookbook 两本 prompting guide 已实读并看图,结论与效果优先的优化方案见 [2026-09-15-github-distillation-and-effect-plan.md](2026-09-15-github-distillation-and-effect-plan.md)。

## 4. 修改清单(全部在实验分支,均进入真实消费链)

| 文件 | 改动 | 解决什么 | 是否进入生成输入 |
|---|---|---|---|
| `references/styles/ecommerce-studio.pack.yaml` | `lighting_palette` 改为四段可见关系(主光方向 → 补光比 → 渐变阴影/接触阴影/背景分离 → 曝光)并锁六张一致;`visual_language` 去掉 `even soft lighting`;`model_persona` 写重心/手部/视线且排除冷感;负面词加 `no flat shadowless lighting` / `no cold detached expression`;`qa_extra` 加三条对应检查 | 衣服被照平、无接触阴影、无背景分离、表情冷感 | 是(`Lighting/background palette:` / `Mood only:` / `Attitude:` / `Style negative append:`) |
| `references/prompt-build.md` | 新增 `§2a 试点情绪覆盖`,`pilot_persona_expression_slugs: [ecommerce-studio]` + 六行"方向几何"表;§2 原表逐字未动 | 韩系情绪修饰语覆盖试点风格 | 是(`Head/gaze:` 六行) |
| `tools/style_preview.py` | 新增 `_pilot_expression_override()`;`_plan_v5` 对试点 slug 用几何 + `PILOT_EXPRESSION_NOTE` 替换 head_gaze | 让真实动作 0 入口读到 §2a | 是 |
| `references/commercial-qa.md` §2/§3、`SKILL.md §4` | 试点 slug 的可定位光影/表情偏离归 `qa-user-review`(附理由,人工裁决,不自动 retry,不加调用) | 视觉目标有处置路径且不新增状态机 | 否(QA 层) |
| `evals/styles/ecommerce-studio.json` | 新增 `ec-lighting-pilot-8` | eval 同步 | — |
| `tests/test_pilot_ecommerce_lighting.py` | 3 条:范围恰为 ecommerce-studio 且几何无情绪词;光线字段含可见关系并经 `_visual()` 读出;真实 `prepare` 产物中试点 prompt 含方法、其余 23 包 head/gaze 逐字不变 | 证明"方法被读取"与"非试点未改" | — |
| `CHANGELOG.md` | Unreleased 增加实验候选条目 | 留痕 | — |

未改:`pose_masters`(仍 `inherit`)、六母版编号、全身/半身规则、B7、安全主体、其它 23 个 pack、schema、linter。

## 5. 规则干跑(真实入口产生,非人工拼装)

命令(实验目录):`python3 tools/style-preview.py prepare --run-id pilot-ecom-{baseline,candidate}-20260915 --source-case beige-blazer-denim-outfit`
产物在本地忽略目录 `.threadtruth/style-previews/pilot-ecom-*/prompts/`;基线产物与已归档 `beige-blazer-denim-outfit-24-v1/prompts/ecommerce-studio.txt` **逐字节相同**,证明入口可复现。

| 指标 | 基线 | 候选 |
|---|---|---|
| ecommerce-studio 提示词字符数 | 4460 | 5854(+1394) |
| tiktoken cl100k 估算 token(非宿主真实计数) | 1163 | 1406(+243) |
| 其余 23 包提示词 | — | 与基线逐字节相同(23/23) |

变化行(候选 vs 基线,均为方法对应):`Mood only`(去匀光 → 方向光/质感)、`Attitude`(重心/手/视线,排除冷感)、`Lighting/background palette`(四段关系)、六行 `Head/gaze`(去情绪词,加"表情随 Attitude,无冷感")、`Style negative append`(+2 项)。保留:全部服饰事实句、参考图角色、画布/标签/预览负面词。

## 6. 分层验证结果

| 层 | 结果 |
|---|---|
| pack-lint --strict | PASS(改后 `✓ 无问题`;INFO 与基线相同) |
| trigger-eval | PASS(断言数与基线相同) |
| unittest(改后 139 条) | **136 通过,2 FAIL + 1 ERROR**,均为**同一原因**:`docs/demo/style-previews/beige-blazer-denim-outfit-24-v1/evidence.json` 把公开预览集合绑定到 `prompt-build.md` 等规则文件与 pack 的 **当前 sha256**(`style_preview._check_plan` → "stale or invalid rules");任何规则/pack 改动都会让公开集合失效,连带 `validate_style_index`、`validate_public_cases`、`build_release` 失败。这是既有治理契约,不是本轮引入的缺陷;本轮**未放宽**该校验 |
| 新增试点测试 | 3/3 通过 |
| 宿主加载核验 | 未做(未生图) |
| 真机出图 / 真实评审 | 未做 |

**契约冲突与 Owner 裁定:** 按原规则,任何规则/pack 改动都让公开预览集合整体失效。Owner 于 2026-09-15 裁定"同意等价绑定"。已实施:`style_preview._check_plan` 不再要求 `rules` 与 pack 的 sha256 与当前文件相等,只要求记录形状合法(provenance 保留),并逐张要求 **当前规则重算出的 `prompt_sha256` 与记录相等**;不等时按风格名报错(`<slug>: prompt is not reproducible under the current rules`)。红→绿证据:`tests/test_preview_rules_equivalence.py` 4 条在旧校验下 2 ERROR + 1 FAIL,新校验下 4/4 通过;全套 143 条中仍有 3 条失败,失败信息已收敛为唯一原因 `beige-blazer-denim-outfit-24-v1: ecommerce-studio: prompt is not reproducible under the current rules`,即公开集合里只有试点这一张需要在新规则下重生成并验收(或恢复旧规则)。其余 23 张在规则改动后仍被判有效,未放宽任何其它校验。

## 7. 冻结的对照标准(先于任何生图)

同一源图(`docs/demo/preview-sources/beige-blazer-denim-outfit/source.jpg`)、同一身份锚点、风格 `ecommerce-studio`、模式 B、动作 0 六宫格(或经授权的动作 2 单张,母版 1),仅改变 §4/§5 记录的候选文本。旧图 = 已公开的 `ecommerce-studio.jpg`(基线规则生成);新图 = 候选规则生成。两版由同一评审表打分,不用各自 QA 通过数比较:

1. 商品硬事实(五件核心单品颜色/结构/长度/鞋包)是否正确 — 任一失败为阻断,不被视觉抵消。
2. 是否看到:主光方向可辨、袖/翻领有渐变阴影、鞋下接触阴影、人物与背景分离、六格光线一致。
3. 表情是否中性亲和(无低头冷感),重心/手部自然。
4. 真实评审者更愿意用哪张及原因;允许"无明显差异 / 各有优点 / 都不合格 / 证据不足"。
5. 调用数、失败数、人工干预数(首轮与修复轮分开)。

模型版本、种子:未知,标未知。更讨喜的随机人脸不算方法改善。

## 8. 另外两个方向(仅方法卡 + 候选设计,未改文件)

- **american-street**:问题 = 六格六地点光线不连贯、人物贴墙无纵深、姿势站桩。候选:`scenes` 收敛为同一街区/同一时段的六个机位(同一光向、同一色温);`lighting_palette` 写"低角度自然侧光 + 人物与墙面保持 1–2 米、背景轻微虚化的空间关系";`model_persona` 写"重心在后腿、肩胯反向、手有动作(拎包/插袋/整理袖口)"。需先在 core 明确"C 模式六场景应共享光线与时段"是否为系列规则(影响全部 C 模式包,超出单包范围,需授权)。
- **japanese-lifestyle**:问题 = 背景编造文字招牌、新增道具、冷感表情。候选:`negative_delta_add` 加 `no invented signage or readable text in background, no added props`;`lighting_palette` 写"窗光单一方向、暖白、低对比、阴影柔"; persona 走 §2a 覆盖(需把 slug 加入试点列表,本轮未加)。
- 两者均待首个试点拿到视觉证据后再各自做小范围测试;一个方向有效不等于另外两个有效。

## 9. 待授权清单(一次问完)

- 素材:已登记的 beige-blazer 套装源图 + 白马甲 look-1 身份锚点(均在仓库,已有公开权利登记)。宿主/数据去向:仅 Codex/ChatGPT 原生生图,不上传第三方。
- 版本:基线 = 公开 `beige-blazer-denim-outfit-24-v1/ecommerce-studio.jpg`(不再生成);候选 = 实验分支 `exp/pilot-ecommerce-lighting` 当前提交。
- 风格/模式/动作:`ecommerce-studio` / B / **动作 0 六宫格 1 次调用**(与旧图同形态可比);失败不自动重试。
- 总上限:1 次;失败即停并报告;修复另行授权。
- 需要 Owner 决定:§6 的契约冲突处理路径(重绑全集 vs 校验等价规则)。

## 10. 授权消耗与执行状态

Owner 原话「同意等价绑定,授权电商 B0 一次」已登记为运行 `pilot-ecom-candidate-20260915` 的不可变批次 `ecom-b0-pilot-01`(styles=[ecommerce-studio],maximum_calls=1,scope=serial-native-generation;no-auto-retry;授权文本与 sha256 存于该运行的 `authorizations/`,本地忽略目录)。

本记录的编写环境(Claude Code CLI)**没有原生图片生成能力**,按 `SKILL.md` 属 `tool-blocked`:未调用任何 API/CLI/第三方替代,未生成图片。可执行材料已备齐在该运行目录的 `EXECUTION-PACKET.md`:冻结提示词(`prompts/ecommerce-studio.txt`,sha256 `4868e434…`)、两张参考图的仓库路径与 sha256、生成记录模板、ingest/compose/audit 命令与宿主加载核验步骤。由具备原生参考图生图能力的 Codex/ChatGPT 宿主在实验分支 checkout 上执行 1 次;结果回到本记录 §7 的冻结标准做新旧对照。

下一步唯一最小动作:在原生生图宿主中按 `EXECUTION-PACKET.md` 执行这 1 次调用并 ingest;之后进行人工对照评审。
