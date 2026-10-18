# 裁光整体改版：实际验证与未完成项

结论：**源码已实现，实图与完整流程验收未全通过；候选未安装，整体计划尚未完成。** 36个执行入口保持DRAFT。最终证据时点为2026-10-18T20:21:27.673275+00:00，原始失败图、修订前图、提示词、源图、操作回执与QA均保留。

## 已实现的能力

24个旧方向迁入统一方案并保留标识，增加12个执行入口；三种用途分别约束商品展示、穿搭编辑与艺术广告。132条原目录记录及中国市场/文化知识可追溯，不作为132个已验证方案计数。可选带版本的visual_plan冻结方向文本、来源哈希、用途、服饰保护以及逐张场景、光线、构图和媒介；两条路线、预览修订、续图、提示词导出与恢复使用冻结方案。人物、动作和真人角度依据保留原模块职责。比较与明确融合分开，单张、仅提示词和停止分支保留。

运行基线：方案源码`f531e1a`；网页单次调用封套修复`f5519a8`；旧版对照`1c48871`。最终证据整理仅更改源码侧文档，不重写冻结任务、运行卡片或旧包。候选保留生成时的验证说明，当前实际范围以本报告为准。

## 实际数量与预算

| 项目 | 实际结果 |
| --- | --- |
| 确认发出的生成请求 | 49 |
| 保留的历史预留 | 50；含SR-049发送前失败 |
| 额外不确定调用 | 1；SR-048后的可能自动重试，分配SR-058保留 |
| 保守预算占用 | **51 / 60** |
| 保留输出 | 49个原始PNG；预览不计独立成片 |
| 方向覆盖 | 35 / 36有独立图；SR-018被失败预览阻断 |
| 原生儿童组 | 6 / 6独立图返回，整组拒收 |
| 网页成人组 | 3张预览返回，独立6张均未启动 |
| 新旧对照 | 3 / 3配对完成，未证明整体改善 |

预算未耗尽。四个预定备用槽已分配，剩余依赖/真人/编辑槽不擅自转作额外重试。SR-049虽无Send仍保留历史与保守预算；网页单次Send及本地账本不能证明远端恰好调用一次工具。确认发送数、文件数和工具调用数不混为同一事实。

所有独立PNG为1024×1536；六格预览为1254×1254。逐图哈希、实际尺寸和分项观察见[live-results.json](live-results.json)，60项原计划及实际状态见[request-matrix.json](request-matrix.json)。`qa-user-review`表示未发现所审范围内明确硬失败，仍有细节与人工复核；不表示商业就绪或用户已接受人物。

## 36个入口的实际范围

| 请求 | 方向 | 路线 / 展示 | 技术QA | 主要结论 |
| --- | --- | --- | --- | --- |
| SR-001 | 美式街头 | native / human | qa-retry | 实际图中前腿向前伸展承重，后腿屈膝后收并向前腿后方交叠，身体形成前进迈步的轮廓；不是双脚静止落地的自然站立。 |
| SR-002 | 运动休闲 | web / human | qa-retry | 当前人物前腿前伸、后腿明显屈膝并置于身后，后鞋朝前下方，整体呈前后交替的迈步式造型；核对原图与后脚原像素局部后，偏离冻结请求的独立静止站立及明确no stepping。判定基于整体腿部动作与支撑造型，不以轻微脚位错开本身判错，也不声称照片证明实际时间中的运动。 |
| SR-003 | 芭蕾日常 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-004 | 英伦复古 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-005 | Cityboy | native / human | qa-retry | 画面左侧手（人物右手）插入蓝色长裤的裤袋，上臂/肘略屈，只有腕部靠近裤腰；另一只手自然垂放。插袋不符合本轮明确双手垂在身体两侧的手位要求。 |
| SR-006 | Clean Fit | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-007 | 淑女柔美 | native / human | qa-retry | 画面右侧可见耳垂上有独立亮色圆形耳钉；原图局部最近邻放大后可见该附着耳垂的亮色饰物。当前人物为新AI，冻结搭配未授权耳饰，故属于新增首饰。 |
| SR-008 | 电商棚拍 | web / flatlay | qa-retry | 平铺成图左右肩口/袖窿上缘外侧均露出浅棕色硬质端片，位置与原正面挂拍图衣架两端相符，不能归作白马甲结构或金色拉链。冻结构图明确No hanger，当前保留这两处衣架端部痕迹未兑现该限制。 |
| SR-009 | 法式日常 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-010 | 都市户外 | web / human | qa-retry | 冻结请求明确独立静止站立并排除stepping；实际前腿前伸承重、后膝弯曲、后脚跟进，整体为前后交替的迈步式造型，偏离这一明确动作要求。判定来自整体腿部动作与支撑关系，非仅凭鞋前后有小幅位置差，也不声称单张照片证明真实时间运动。 |
| SR-011 | 国潮街头 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-012 | 意式轻奢 | web / human | qa-user-review | 技术QA后待人工复核 |
| SR-013 | 日系生活 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-014 | 韩系冷感 | web / human | qa-user-review | 技术QA后待人工复核 |
| SR-015 | 韩系男装 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-016 | 新中式 | web / human | qa-user-review | 技术QA后待人工复核 |
| SR-017 | 北欧极简 | native / hanger | qa-user-review | 技术QA后待人工复核 |
| SR-018 | 女性通勤 | web / human | 未执行 | 网页预览未通过，独立首图未启动 |
| SR-019 | 老钱风 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-020 | 学院风 | web / mannequin | qa-user-review | 技术QA后待人工复核 |
| SR-021 | 静奢 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-022 | 度假 | web / human | qa-user-review | 技术QA后待人工复核 |
| SR-023 | 工装复古 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-024 | 千禧风 | web / human | qa-user-review | 技术QA后待人工复核 |
| SR-025 | 美式复古日常 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-026 | 哥特暗调摄影 | web / human | qa-user-review | 技术QA后待人工复核 |
| SR-027 | 浪漫波西米亚 | native / faceless | qa-retry | 原图顶部中央仍可见下巴底部的浅色弧面及其与颈部的边界。已用原像素区域(470,0,610,70)仅在内存中最近邻放大确认，无眼鼻口且不可识别人物，但明确冻结要求是from just below the chin以及face and eyes remain entirely outside the canvas，当前仍露下巴底部没有完整兑现该裁切边界。 |
| SR-028 | 未来人工光摄影 | web / human | qa-retry | explicit_static_pose: clear stepping/follow-through pose with bent rear knee and lifted rear heel conflicts with frozen no-stepping requirement |
| SR-029 | 汉服指定形制展示 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-030 | 旗袍都市人像 | web / human | qa-user-review | 技术QA后待人工复核 |
| SR-031 | 林芝工布服饰展示 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-032 | 婚纱空灵 | web / human | qa-user-review | 技术QA后待人工复核 |
| SR-033 | Lolita层次展示 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-034 | 服饰插画 | web / human | qa-user-review | 技术QA后待人工复核 |
| SR-035 | Art Deco图形布景 | native / human | qa-user-review | 技术QA后待人工复核 |
| SR-036 | 超现实空间广告 | web / human | qa-retry | frozen_impossible_spatial_loop: receding repeated arch corridor does not clearly establish the specifically requested arch returning recursively into the same room |

汉服仅覆盖给定现代明制道袍，婚纱仅覆盖给定约1838年实物，Lolita仅覆盖所选正面层次。工布使用署名shengjingyoujian、CC BY-SA 2.0的原照片中指定节庆／舞蹈衣装；原题“公布”到“工布”的对应保留推断说明，不称博物馆认定或整个服饰体系通过。帽型比例与新人物独立性仍待复核。服装源许可、AI修改标识及相同方式共享要求见[素材记录](fixture-sources.md)；私人样片旁保留相应许可文件。

## 整组、对照与对话

D03儿童首张人物已获真实用户确认，后五张共用该锚点。第3/5张缺失源图可见第三排纽扣且景别不符；前五张头向、左向视线和微笑重复。六张返回不抵消商品/构图失败，整组保留qa-retry。D04网页末次预览修复了部分手位、前襟和裁切，但第1格躯干回转不足、第1–5格右向离镜视线重复；预览未接受，独立首图和后五张未启动，依赖的人物资料包跨商品复用也未执行。D05预览后正确停止，预览自身仍拒收。

| 配对 | 可观察结论 |
| --- | --- |
| PAIR-01：SR-006 / SR-054，Clean Fit | 主要商品、身份、姿态持平；新版暖灰背景遵循退化 |
| PAIR-02：SR-014 / SR-055，韩系冷感 | 主要可见轴持平，微细五金和皮肤颗粒待核 |
| PAIR-03：SR-019 / SR-056，老钱风 | 主要商品、身份、姿态持平；新版日光/地影偏硬 |

三对均固定原商品、原AI锚点、路线、姿态、场景目标及画幅，保留双方结果。每对各一次，模型版本与seed未完全可控；不做统计优越性或版本因果结论。主要结构未见明确退化不等于微细位置、尺寸或严格锁脸已通过。

对话共15定义：原12项加比较、缺素材、主辅融合3项。非真人/AI及非人像12项中，10项有真实隔离子代理actions与answer，D09依赖阻断、D11待答；真人D07/D08/D10按用户选择延期。7项有明确根审行为PASS记录（D01/D02/D06/D12/D13/D14/D15），不写成10项全通过。D12实际是仅提示词挂拍、0调用，SR-017是另建视觉任务。旧任务兼容保留确定性旧writer/字节证据，没有新模型兼容对话的通过记录。详见[runtime-dialogues.json](runtime-dialogues.json)。

## 代码与生产检查

首次全套573项出现28个失败；18项风格相关问题经定向修复复核，10项wardrobe环境失败在既有host依赖可用后以14项相关测试闭环。另有运行时、根定向、能力/触发及网页封套检查证据。未重跑一次全绿573项，不能写“全套573全通过”。具体闭环见[code-validation.md](code-validation.md)。

网页封套批188项范围检查、7种旧writer字节兼容和35份准备产物核验见[封套验证](../2026-10-19-web-execution-envelope.md)。代码检查不证明视觉改善或所有真实会话通过。候选97个运行文件与源码、净stage和解压结果一致；结构/runtime严格检查、归档路径/CRC/哈希和净解压CLI帮助检查已过。最终源码侧严格结构审查、公开资料扫描和diff检查通过；范围见代码检查记录，不重复把旧有效结果算新测试。

## 未完成与交付边界

- open：上述单图硬失败、D03整组失败、D04预览失败和两对摄影目标退步。
- blocked：SR-018、SR-042–046及SR-051依赖D04合格预览、首图和人物包；没有用独立测试图冒充这些流程。
- deferred(user-real-input)：真人D07/D08/D10及SR-052；SR-021/024改用既有AI仅覆盖风格，不代表真人。
- deferred(user-target-confirmation)：D11/SR-053准确底图和编辑确认未答，未调用。
- fixed(source)：统一方案和网页执行封套等源码变更；不扩称视觉缺陷已关闭。

候选归档固定`f5519a8`，SHA256 `ecc51d583c60cb7e8059067c799ec64dc3940742d444dc4111acc4960bcd4e8b`，标为candidate-not-release。完整源码另按最终证据提交归档；本地样片画廊包含全部返回图、拒收图和三组对照，私人完整日志不进入源码包。由于必需流程与实图未全过，按原计划不更新本机安装，也未公开发布。现有安装无需回滚；候选交接文件保留以后获准安装时的逐步备份/回滚方法，本轮未实测安装或回滚。
