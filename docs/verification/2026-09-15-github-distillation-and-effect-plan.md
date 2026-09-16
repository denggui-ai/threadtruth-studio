# 2026-09-15 · GitHub 同类资源蒸馏 + 以出图效果为中心的优化方案

前提:Owner 指出"过度文件治理意义不大,用户更需要出图效果"。本文只回答两件事:三个 GitHub 来源到底给了什么,以及我们的生成输入应该怎么改。治理只保留一条:改了哪张的提示词就重生成哪张(等价绑定已实现)。

## 1. 蒸馏结果(全部实读正文;标"已看图"的是实际查看过样图)

### 1.1 motiful/product-shots(multi-angle 子技能)

| 实际内容 | 可迁移 | 不迁移 |
|---|---|---|
| 三个摄影预设是**长格式规格块**(光源类型/位置/扩散、阴影方向/边缘/密度、胶片颗粒/暗角、材质反射、禁止项),每张提示词逐字重复整块 | 摄影块写成结构化规格而非形容词;整组逐字重复以锁风格一致 | 预设 B"Soft Muted Film"要求完全漫反射、无高光、扁平绘画感、情感疏离——正是我们要摆脱的"照平"和"冷感" |
| 9 张任务提示词每张给:镜头焦段、裁切上下界+禁止出现的身体部位、姿态几何(重心偏一侧、躯干旋转、手一屈一伸、骨盆右转 20°/胸部左转 30° 的对立扭转)、头部/视线、表情 | **姿势写成几何**:重心、肩胯反向、手部状态、头部角度;裁切用"禁止出现 X"负面句 | 九图数量、发型验证视图、极端面部特写、单次批量 9 张 |
| 14 变量先抽取再生成(发色/发型结构/肤色/服饰逐件材质版型/包/首饰/背景色/风格块/画幅),不得静默默认 | 我们已有识别卡;可补"每件单品材质+版型+层叠顺序"的抽取粒度 | — |
| 8 条硬约束:参考图必传、先分析后生成、发型不重释、配饰不增不减、硬裁切、全局风格统一、按变量影响面重渲染、单批生成 | 配饰不增不减、按影响面重渲染(与等价绑定同思路) | 单批 9 张(我们的宿主是串行单图) |
| 样图(dress/multi-angle/01-front、main-image/01-amazon-main,**已看图**) | 反面证据:白底匀光、无地面阴影、人物与背景无分离、站桩,与我们电商预览的问题一样 | 不作为效果目标 |

结论:product-shots 的价值在**结构**(规格块 + 几何化姿势 + 负面裁切句),不在它的光线审美。

### 1.2 YouMind nano-banana-pro 提示库

- 库结构:11 个分类 JSON,`ecommerce-main-image` 575 条,`product-marketing` 5699 条;每条含 content/title/sourceMedia。用"服饰词 × 光线词"过滤,电商类命中 80 条。
- 样图**已看**两条:"Casual Denim Studio Portrait"(灰背景、柔和方向光、脚下有清晰接触阴影、背景有明暗梯度、一脚踩凳的非对称站姿)、"Minimalist Studio Portrait of a Young Man"(灰无缝、"gentle gradations and soft shadows on the floor around the chair and the man's feet",画面里确实有地面阴影与背景渐变)。
- 有效提示词的共同写法:光线一句写清"柔和 + 方向 + 在哪里形成阴影";姿势写清重心与手在做什么;背景写材质与色;情绪一两个词。无效填充:"8K、ultra-detailed、cinematic"之类。
- 未知:这些样图的模型、后期、筛选比例都未知,不把精选图当成功率。

### 1.3 openai-cookbook(image-gen-models-prompting-guide / gpt-image-1.5 guide)

- 结构顺序:**背景/场景 → 主体 → 关键细节 → 约束**,并写明用途(ad / product photo)以设定精修程度。
- 写实靠"镜头、光圈感、光线"比"8K/超清"更稳。
- 换装示例的约束句可直接借用:"Match lighting, shadows, and color temperature… so the outfit integrates photorealistically, without looking pasted on";"Do not add accessories, text, logos, or watermarks"。
- `input_fidelity=high` 是 API 参数;宿主原生生图不暴露,不写进 Skill。

## 2. 诊断:我们的提示词为什么出图平

对照上面三源,当前动作 0 提示词(约 4.4K 字符)里**真正影响画面的内容不到三分之一**:

| 现状 | 问题 |
|---|---|
| `visual_language` 1 行形容词,`lighting_palette` 1 行,`model_persona` 1 行 | 没有方向、比例、阴影落在哪、地面关系;模型只能给匀光 |
| 六行头部视线全是韩系情绪词 | 24 个风格共用一种"冷静疏离" |
| 姿势母版只有名字(SIDE_TURN_STANDING 等) | 没有重心/肩胯/手/与环境距离,出来就是站桩 |
| C 模式六格六个地点 | 光线、色温、时段全变,系列感散 |
| 标题/副标题/页脚/引用角色/守卫句占大量篇幅 | 治理文本挤占了模型的注意力预算 |

## 3. 优化方案(效果优先,不加字段、不加状态)

### 3.1 每个 pack 的"摄影块"扩成四段规格(进 prompt)

已在 ecommerce-studio 试点。推广时每个 pack 的 `lighting_palette` 固定写四段:光源与方向 → 补光比与阴影侧可读性 → 阴影落在哪(服饰褶皱/脚下/背景) → 曝光与一致性。柔光 pack 保持柔,但"柔"也要写出方向和接触阴影。

### 3.2 六姿势母版补几何描述(core 一次性改,全部风格受益)

给 `prompt-build.md §1` 每个母版补一行几何:重心在哪条腿、肩与胯是否反向、手在做什么、头部角度、与背景的距离。情绪一律由 pack `model_persona` 提供,即把 §2a 的做法从"仅试点"扩到全部 24 包。这是本方案里唯一的全局改动;等价绑定下,它只让提示词真变化的预览失效。

### 3.3 C 模式六场景改为"一个地点、六个机位"

`pack.scenes` 语义从"六个不同地点"改为"同一地点同一时段的六个机位/朝向";在 `modes-scenes.md §3` 加一句系列规则:整组共享光向、色温、时段。美式街头、日系先做。

### 3.4 提示词顺序重排,治理文本后置

按 cookbook 顺序:用途一句 → 服饰事实(逐件:材质/版型/层叠/鞋包) → 摄影块 → 姿势几何 + 表情 → 场景 → 约束(不增不减配饰/无文字/无 logo/画幅)。标题、页脚、参考图角色说明压到最后并缩短。目标:影响画面的文本占比从不到 1/3 提到 2/3 以上,总长度不增。

### 3.5 借来的负面句(直接可用)

- 匀光问题:`no flat shadowless lighting, no multi-directional shadows`
- 编造背景文字(日系第 2 格):`no invented signage, no readable text in the background`
- 新增道具(日系第 3 格):`no added props beyond the reference`
- 换装贴片感:`match lighting, shadows and color temperature so the outfit does not look pasted on`
- 站桩:`no symmetric stance, no stiff catalog pose`(配合几何描述才有效)

### 3.6 明确不做

- 不做 9 图、不做发型验证视图、不做单批多图。
- 不用"8K / ultra-detailed / cinematic"填充词。
- 不为每次规则改动重跑 24 张验收;只重生成提示词实际变化的预览。
- 不新增 schema 字段、状态词、审计脚本。

## 4. 执行顺序(每步都以一张图为判据)

1. 等 Codex 额度恢复 → 跑已授权的 ecommerce-studio B0 一次,按冻结标准对照(验证 3.1 是否有效)。
2. 有效则:3.2 六母版几何 + §2a 扩全包 + 3.4 顺序重排,一次提交;重生成受影响的公开预览(数量 = 提示词真变化的风格数)。
3. american-street:3.3 场景收敛 + 3.1 摄影块,1 张对照。
4. japanese-lifestyle:3.5 两条负面句 + 3.1,1 张对照。
5. 每步只改一个变量组,失败就回退该步,不叠加。

评审固定三问:更想用哪张?商品事实对不对?哪里不对?允许"无差异 / 都不合格"。
