# style-router.md — 风格路由(推荐 + 确认 + 冲突检测 + 可审计 trace)

> **职责(L2 内部 router):** core 已加载后,据"识别事实 + 用户措辞"选风格包,输出**可审计 trace**;**只推荐不生图、不自动选定**。选定风格代号后仍须 §SKILL §6 动作授权才进生图。
> **铁律:** 路由结果**不得绕过** `safety-core.md`(R1–R7)与输入门禁;`score` 只能查权重表累加,模型不得自由填分。

**先查执行索引再读卡：** `visual-library/index.json`包含36个执行入口的ID、中文名和卡片路径。原24入口还对应下方§6 pack注册表；实际读到映射后再打开文件，不猜路径。知识目录只在解释、比较或查缺时加载，不把知识条目当成已验证执行入口。

## 1. 路由输入

使用识别卡可见事实、用户已有用途、人物/输出形态与原话。将词分别识别为服饰流派或形制、摄影、场景、色彩情绪、媒介、交付用途。文化身份与人物身份不由风格名称推断。

未选方向时给主推、两个有区别的备选及简短理由，再展示索引中的完整36入口目录；已有明确选择沿用，不重复问菜单。只要通用清单或提示词可直接文字交付；没有真实服饰图时不伪造商品方案或生成图片。

## 2. 选择、比较和融合

1. 先理解语境、否定和动作意图。`不要哥特`不是选择哥特，`美式复古厨房`首先是场景，裸`美式`不再直路由街头。地域/文化大词不自动选定某个细分方向；只有实际会改变结果的歧义才问。
2. 对肯定选择的入口别名使用NFKC/casefold、ASCII词边界、同入口去重和同位置最长完整命中；不同位置的独立命中保留。新入口别名来自执行索引/卡片，旧24仍以pack trigger_words为准。
3. 不同维度相容时直接形成方案，例如`法式＋美拉德＋居家`是主方向、色彩和场景。不得把全部词当多个pack而停问；色彩只影响环境/光线关系，不能改原衣服颜色。
4. 用户要求比较时输出并列方案；明确要求各生成一张则在相同商品/人物条件下建立独立单张任务串行执行，不自动融合。只问区别不生图。
5. 用户已明确主辅时沿用，并记录融合说明；未说明主次的同维度多方向才进入`style-conflict-hold`，用一句话问具体选择。不要机械再问已回答的问题。
6. `anti_categories`和性别倾向是适配提示，不是安全禁令。用户要借摄影氛围且不需改实物时可转译；只有确实会改变商品、人物或违反安全时暂停并指出具体冲突。不得把女装转成男装、删除制服/蕾丝或给普通衣服添加文化结构。
7. 未有执行方案的知识方向可解释、比较或给明确标注的通用提示词；如用户要实际出图，说明当前方案缺口并确定可执行方向，不冒称其已有样片或支持范围。

## 3. 冲突按本轮具体要求判断

不使用风格家族的永久互斥表。检查是否同时要求同一张的互斥媒介/光线/场景、是否擅改原商品或人物、是否与逐张动作冲突。强对比与柔光、室外与窗内布景等应具体到光源和位置判断。商品事实、安全和明确要求优先；合法的审美融合本身不需要拒绝。

## 4. 路由 trace(防"模型假装路由" + 防"假算分")

每次路由**必须**保留结构化 trace 供内部审计;有本地任务目录时写入该目录的审计记录,不得把未落盘记录称为已保存。面向用户默认只展示选定/推荐风格、基于服饰事实的理由、冲突及需用户选择的事项;不展示 route-trace、rule_id、分数或权重。仅用户明确要求路由诊断时才展开这些内部记录。正常选择菜单中的风格代号仍可展示。**算分硬约束:**
- 每个 `hit` **必须**绑定一个 `rule_id`(来自 §5 权重表),其 `term` 必须是用户措辞/识别事实里**真实出现**的词(来自 §5 hit vocabulary)。
- `score` **只能**由命中规则权重**累加**:`score(pack) = Σ weight(rule_id_i)`;**禁止**模型自由填分。
- **同一输入 token 只消费一次:** 先执行 `STYLE_EXPLICIT`;一旦某个规范化输入片段已作为显式风格命中消费,不得再用同一片段重复命中 `USE_*`、`MAT_*`、`SILH_*` 或其它评分规则。不同真实片段可分别计分,trace 应能看出每个 term 的唯一 `rule_id`。
- **同一 pack 的 `STYLE_EXPLICIT` 权重最多计 1 次:** 同一 slug 同时命中多个不同别名/近义 trigger 时,trace 可把它们列在 `matched_terms`,但加权 hit 只保留 1 条 `STYLE_EXPLICIT(w=100)`;不得因用户重复说同一风格而把显式分叠成 200/300。
- **无命中即不打分:** 某 pack 若 `hits=[]`,不得出现在 candidates。
- trace 必须**可复算**:审计者据 §5 表 + 列出的 `rule_id` 应能重算同一 `score`;对不上 = 假 trace = FAIL。
- **不暴露:** 用户密钥/凭证、本地路径、环境变量;仅含识别事实与路由决策。

```
[route-trace]
detected: {category: 连衣裙, main_color: 米白, material: 醋酸缎, skin_exposure: 低,
           gender_age: 女装成人, ecommerce: 否, platform: 小红书, high_risk: 否}
conflict_check: 命中风格 token = [];无显式风格,跳过冲突 hold
candidates(top3):
  - {pack: french-effortless, score: 78, hits: [
        {rule_id: MAT_ACETATE_FR, term: 醋酸缎, w: 18},
        {rule_id: PLATFORM_XHS_RELAX, term: 小红书, w: 12},
        {rule_id: SILH_RELAXED, term: 松弛廓形, w: 8}, ... ]}   # Σw = 78,可复算
  - {pack: korean-cold-editorial, score: 71, hits: [{rule_id: COLOR_COOLWHITE_KR, term: 米白, w: 16}, ...]}
  - {pack: clean-fit, score: 64, hits: [{rule_id: SILH_MINIMAL_CLEAN, term: 极简版型, w: 14}, ...]}
chosen: 推荐主推=french-effortless(待用户确认);备选=korean-cold-editorial / clean-fit
fallback_used: 否
gate: recognition-ready(未生图,等待当前具体方案的选择/生成授权)
```

> `rule_id + term + w` 让"路由是否真按事实算分"可**逐条复算**;`score` 是启发式排序累加值,**不对外声称是测量值**。

## 5. 权重常量表 + hit vocabulary(trace 唯一算分依据)

> 权重与命中词典是**常量**;模型只能"查表命中→累加",不能自创规则或分数。骨架节选,加 pack 时补全。

**(a) 权重表(rule_id → weight,节选):**
| rule_id | 维度 | 命中条件(term ∈ vocabulary) | weight |
|---|---|---|---|
| `STYLE_EXPLICIT` | 显式风格 | 用户直接说出该 pack 风格名/代号 | 100(直路由级) |
| `MAT_ACETATE_FR` | 材质 | 醋酸缎/雪纺/真丝 → french-effortless | 18 |
| `COLOR_COOLWHITE_KR` | 主色 | 冷白/冷灰 → korean-cold-editorial/nordic-minimal | 16 |
| `SILH_MINIMAL_CLEAN` | 版型 | 极简/基础版型 → clean-fit/nordic-minimal | 14 |
| `PLATFORM_XHS_RELAX` | 平台 | 小红书 → japanese-lifestyle/french-effortless/clean-fit | 12 |
| `USE_ECOM_STUDIO` | 用途 | 商品上架/店铺首图/白底商品照/详情页展示 → ecommerce-studio;仅在未命中该 pack 显式 trigger 时计分 | 20 |
| `USE_EDITORIAL` | 用途 | 品牌大片/杂志感 → editorial 族 | 16 |
| `SILH_RELAXED` | 版型 | 松弛/oversize 廓形 → french-effortless/american-street | 8 |
| `RISK_PENALTY_EXPOSE` | 风险(负) | 高露肤/高风险品类 → 压低重场景/露肤风格 | −P(见 safety-core) |

**(b) hit vocabulary(term 词典,节选;term 必须真实出现才可命中):**
- 材质:`醋酸缎/雪纺/真丝/针织/棉麻/皮革/金属/丝绒/牛仔` …
- 主色:`冷白/冷灰/暖土/高饱和/低饱和/暖金` …
- 版型:`oversize/廓形/修身/正装/极简/基础` …
- 平台/用途:`小红书/商品上架/店铺首图/白底商品照/详情页展示/品牌大片/杂志感/editorial` …
- 风格名/代号:见 §6 注册表(显式风格命中 → `STYLE_EXPLICIT`,先过 §2 第 0 步冲突检测)。

## 6. 触发词 → 风格包 注册表(pack `trigger_words` 是数据真相源;本表为完整人读镜像,SKILL description 只放高频词)

| 用户措辞(示例) | 路由到 pack | 说明 |
|---|---|---|
| 韩系/韩杂/韩系杂志风/韩国杂志/韩国杂志人像/W Korea/Vogue Korea/性冷淡/安静奢华/冷感大片 | korean-cold-editorial | 已落地 |
| 法式/松弛感/巴黎/effortless/French girl/慵懒法式 | french-effortless | 已落地 |
| 电商主图/高转化/淘宝白底/棚拍主图/商品主图人像/详情页人像 | ecommerce-studio | 已落地,默认棚拍 B;这些词已由 `STYLE_EXPLICIT` 消费时不得再重复记 `USE_ECOM_STUDIO` |
| 日系/日系生活/日杂/无印感/无印风/japanese lifestyle/muji style | japanese-lifestyle | 已落地（公开 Beta `DRAFT`；`通勤日系穿搭`只命中本包,不靠裸「通勤」强塞 office；`日系简约男装`则按最长完整触发词归 cityboy） |
| 美式街头/街拍/vibe 街头/美式复古街头/american street | american-street | 已落地（裸「美式」「街头」不作具体街头方向触发词） |
| 老钱/old money/old-money/世家/低调奢华/名媛世家 | old-money | 已落地 |
| quiet luxury/quiet-luxury/静奢风/静奢穿搭/当代静奢 | quiet-luxury | 已落地（触发与 old-money「低调奢华」/韩系「安静奢华」隔离,裸「静奢」因是「安静奢华」子串故排除） |
| preppy/美式学院/常春藤风/ivy style/校园学院风/varsity prep | preppy | 已落地（v1 静态;美式学院 lane;与 british-heritage 视觉可融合,；同时命中按比较/融合意图处理） |
| 英伦传承/传统英伦/british heritage/heritage tailoring/tweed country/英式复古 | british-heritage | 已落地（v1 静态;英伦传承 lane;与 preppy 同时命中按§2判断意图） |
| 极简基础/极简版型/基础款/clean fit/简约基础/minimal basic | clean-fit | 已落地（Wave 2;冷调极简基础 lane;裸『极简』**不直路由**、只作 §5 SILH_MINIMAL_CLEAN 评分词(→clean-fit/nordic-minimal 共候选);暖调无印→japanese-lifestyle,『北欧/性冷淡极简』归 nordic-minimal;同时命中按§2判断意图） |
| 北欧极简/性冷淡极简/nordic minimal/scandi minimal/斯堪的纳维亚/冷淡北欧 | nordic-minimal | 已落地（v1 静态;与 clean-fit 视觉可融合；同时命中按比较/融合意图处理,裸『极简』仍只作 §5 评分词） |
| gorpcore/山系/户外机能/机能户外/山系机能/outdoor technical | gorpcore | 已落地（v1 静态;机能户外 lane） |
| 运动风/瑜伽/athleisure/运动休闲/健身穿搭/sporty chic | athleisure | 已落地（Wave 2;『机能/户外/山系』仍归 gorpcore,裸『运动』『松弛感』排除——松弛属 french-effortless/american-street SILH_RELAXED） |
| balletcore/芭蕾风/芭蕾柔美/纱裙轻盈/ballet mood/soft ballet | balletcore | 已落地（v1 静态;融合按本轮具体要求判断） |
| Y2K/千禧风/千禧辣妹/复古千禧/y2k millennium/millennium style | y2k-millennium | 已落地（v1 静态;不设置审美家族永久互斥） |
| 新中式/立领盘扣/neo chinese/modern chinese/东方极简/中式现代 | neo-chinese | 已落地（v1 静态;保留现代新中式范围；真实历史服饰转对应形制入口，见recognition §3.7） |
| 国潮街头/街头国风/guochao street/国风街头/潮流国风/新国潮 | guochao-street | 已落地（v1 静态;国风街头 lane） |
| 品牌大片/杂志感/editorial | korean-cold-editorial / italian-luxe(按事实) | editorial 族(§5 USE_EDITORIAL 共享评分词,**不直路由**、按识别事实细分;italian-luxe 已落地见下行) |
| 意式奢华/意式优雅/米兰风/意大利风格/italian luxe/italian luxury | italian-luxe | 已落地（Wave 2;暖调意式奢华 editorial lane;『品牌大片/杂志感/editorial』不进本行、只作 §5 USE_EDITORIAL 评分词→korean-cold-editorial/italian-luxe 共候选;融合按本轮具体要求判断） |
| 男装 + 各风格 | korean-menswear / cityboy / workwear-vintage / gorpcore | 性别横切共享识别事实,**不直路由**;须继续命中下方具体 pack 或按识别事实评分 |
| cityboy/都市男孩/宽松男装/男装通勤/casual menswear/city casual/日系简约男 | cityboy | 已落地（v1 静态;都市宽松男装 lane;`日系简约男装`按最长完整触发词归本包,淘汰 japanese 的裸`日系`） |
| korean menswear/韩国男装/韩式男装/冷感男装/首尔男装/seoul menswear | korean-menswear | 已落地（v1 静态;韩式冷感男装 lane） |
| 复古工装/workwear/工装复古/heritage workwear/vintage utility/rugged workwear | workwear-vintage | 已落地（v1 静态;复古工装 lane） |
| 职场通勤/OL通勤/商务女装/office commute/office lady style/通勤女装 | office-commute-women | 已落地（v1 静态;女性职场通勤 lane;男装通勤归 cityboy） |
| 度假风/resort/海岛度假/沙滩度假/resort vacation/假日度假 | resort-vacation | 已落地（v1 静态;旺季泳装/连衣裙时仍叠 safety-core R4） |
| coquette/千金风/甜美名媛/ladylike coquette/coquette style/精致淑女 | coquette-ladylike | 已落地（v1 静态;高客单甜美名媛 lane;禁幼态化/性化） |
| 童装/儿童/亲子 | 儿童版风格 + safety-core R1 | 敏感主体通道(非独立 pack;不因风格包放宽 R1) |
| 泳装/内衣/比基尼 | resort-vacation / clean-fit + safety-core R4 | 高风险通道(共享识别事实,不直路由;R4 优先) |

> 原24注册表的slug与pack文件名保持一致，trigger_words镜像由pack-lint校验。新增12入口从visual-library索引读取，不能据此伪称新增了12个传统pack。

### 6.1 完整目录与证据状态

从执行索引列36个入口，每项恰好一次，使用中文短名；用户要求内部代号时再展开ID。保留原24的名字、ID和旧任务映射。推荐不构成生成授权。

目录分别说明执行能力、maturity与实图范围。知识记录可查但不能混入“已验证”清单；有旧样片不证明新版方案或所有服种已通过。儿童只借相容视觉方向，按R1安全转译；插画或艺术广告不放宽商品、身份和授权条件。

## 7. trigger-eval(L1 发现 + L2 路由)
`evals/trigger-evals.json` 覆盖 core L1 发现与人读 L2 期望;`evals/style-route-evals.json` 由 `tools/trigger-eval.py` 对真实 query 执行规范化、同包别名折叠、最长匹配与 route/hold/none 判定。正负各列:L1 正(法式/日系/老钱/电商/男装/童装 → 触发 core)、L1 负(带货文案配图→xhs;狗粮→非服饰)、L2 确定性归属、L2 未解决同维度冲突、比较/融合意图与跨维度组合、L2 真兜底、L2 假 trace 检测、互抢隔离。
