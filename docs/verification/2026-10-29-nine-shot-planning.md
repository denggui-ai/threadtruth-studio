# 九张服饰姿势编排：源码与离线验证

日期：2026-10-29。开发基线：`e7125aa`。用户授权实施九张方案；本报告关闭本次源码工作包，不包含生成、安装或公开发布。

## 实现结果

新人物／不露脸默认九张，由现有服饰事实、展示用途和素材覆盖决定动作；保留明确单张／六张、经典六姿势、非人像六构图和旧任务契约。此次复用现有识别、人物选择、摄影计划、生成入口、任务账本和QA，没有新增生成器或另一套商品识别。

- `shot_plan.version=2`保存完整逻辑系列、稳定`shot_id`和当前选择。每张记录用途、必须可见部位、选姿理由、身体关系、手位／支撑、景别、商品方向及依据。单张选择不截断原系列。
- `visual_plan`负责摄影；真人身体描述从同一shot计划编译，真实头向／目光及脸部覆盖仍由`real_face_plan`约束。预览和独立图继承同一冻结计划。
- 创建、预览承接、导出、续图、重试、检查贯通1／6／9。预览第七格转本地look-1仍保留第七格身份；只有明确series-first可在确认与新增授权后续八张。
- 逐张解析实际有序附件：必要商品与身份、当前审美参考、可选一个主要姿势参考。创建与修订预检后续独立图容量；不静默丢掉必需素材。九格预览默认不附姿势图，逐格文字仍来自相同计划。
- `pose_catalog.py`提供可替换的来源／动作组／视图适配。实际读取研究库得到1,439条、288组；当前来源保持research-only，不进入任何生图角色或运行包。来源校验不能识别任意无声明、改名或修改过的图片，也不代替权利核验。
- v2局部重试保留其他已接受图、共享条件、旧计划／输出及累计次数。独立单张允许合法修订；系列身份锚点继续走专门流程。网页v2单次请求封套不会把九格误当九次调用，旧v1封套字节及历史验证保持。

详细运行决策见[姿势规划](../../skills/threadtruth-studio/references/pose-planning.md)，实施与反审意见见[设计契约](../development/pose-reference-integration-plan.md)。

## 已运行检查

以下是不同阶段的实际结果，有交叠，不能相加当作互不重复的测试数，也不描述为一次全套全绿。

| 检查 | 实际结果与范围 |
|---|---|
| 全量`unittest discover -s tests` | 654项，147.435秒；628通过、10失败、16错误。16项缺fontTools，10项缺Node sharp。完整首次失败记录保留 |
| 字体相关定向补跑 | 复用已有fontTools/PIL环境，16项全部通过；没有安装新包 |
| 换衣图像相关定向补跑 | 复用已有Node及sharp目录，14项全部通过，覆盖原10项环境失败 |
| 最终运行相关回归 | 256项全部通过，6.313秒；覆盖v2计划／附件／九张／真人／重试／恢复／旧任务及最后三项反审修复 |
| 最终仓库、预览规则、打包、首页 | 29项全部通过，28.478秒；新增模块／参考说明进入包，研究图库数据／图片不进入包 |
| Creator结构与生产标准source检查 | 均通过；使用已有含PyYAML的环境。主技能160行，242条源侧eval定义。定义数量不是模型评估通过数量 |
| 旧格式兼容对照 | 分工实现者实际比较：56组合法v1 shot render/apply；36风格×1／6×全组／首张／末张，共216份v1 visual导出；v1网页前后缀及四类完整material，均与基线字节一致 |

最终256项命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_nine_task tests.test_pose_plan_v2 tests.test_pose_catalog tests.test_visual_pose_v2 tests.test_plan_revision tests.test_visual_plan tests.test_real_face_plan tests.test_reference_execution tests.test_preview_task tests.test_web_task tests.test_web_execution tests.test_revision_recovery tests.test_repository_contract tests.test_preview_rules_equivalence
```

最终29项命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_repository_contract tests.test_preview_rules_equivalence tests.test_build_release tests.test_home_copy
```

全量执行后增加了三条反审回归，它们纳入最终256项；未为宣称全绿再次重跑所有无关测试。原始日志、环境补跑和哈希清单位于korea工作台私人目录`outputs/caiguang-nine-implementation-20261029/`，不进入Git和runtime。

## 反审发现闭环

| 发现 | 修复与状态 |
|---|---|
| 真人预览逐格引用其他格商品附件 | 按当前shot实际附件编号导出；fixed(source/regression) |
| 第七格独立单张因本地look-1误判身份锚点，不能结构化重试 | 按series_role及实际依赖判断；fixed(source/regression) |
| 未来系列附件超限到试拍后才发现 | 首次创建即预检完整后续系列；fixed(source/regression) |
| 目录适配器返回的sha输入不被导入接受 | 导入接受并实读校验文件哈希；fixed(source/regression) |
| 移除references_sha256后可改姿势来源声明 | v2／姿势库存必须保留冻结元数据哈希；fixed(source/regression) |
| 网页v2准备后省略manifest可绕过预留检查 | 按实际封套版本检查目录和manifest；fixed(source/regression) |
| 预览修订／局部合成未复核后续附件容量 | 统一未来系列预检，失败原任务不写入；fixed(source/regression) |
| 预览追加商品图可绕过已知研究来源限制 | 追加入口同样执行来源门禁；fixed(source/regression) |
| AI／新人物预览缺逐格审美参考编号 | 同样导出逐格实际有序附件映射；fixed(source/regression) |
| recognition保留未限定版本的“缺背面只替第六” | 明确仅经典／旧v1适用，v2替换所有失去依据的视角；fixed(source/docs) |

最后三条代码回归由独立review agent补入，先单独通过，再纳入主线程256项。已知代码发现无剩余open；这不等于证明不存在未知缺陷。

## 四类服饰离线规划探针

独立agent以新技能和四组明确的假设商品事实作零生图规划，不继承实施会话；不是原始商品图识别测试、真实用户完整会话或自动冻结任务。

| 场景 | 观察与结论边界 |
|---|---|
| 胸前印花短款上衣 | 低位手臂避开胸前，完整衣长有展示；局部图明确不算新身体动作 |
| 有正背依据阔腿裤 | 安排裤腿分离、腰头、后袋及小步；去掉背面后替换两个受影响项，不仅第六张 |
| 后中开衩长裙 | 区分闭合前片与后中开衩，避免凭空前开衩／侧面和夸张甩裙 |
| 独立珠网披肩层叠服饰 | 珠网披肩、光滑袖身、领襟分别安排，未把披肩材质移到袖身 |
| 改成九张全身 | 原局部项改成完整全身；如实承认站立／小步动作仍同类，不凭编号声称九种不同动作 |

主线程阅读全部探针并对照给定事实：选姿理由可追溯，未发现借图库补商品事实；原始输出中的文档冲突已按上表修订，探针原文保留。若干站立、小步的边际用途仍需实际编辑与成图评审，不能从这份文字判断真实多样性改善。该证据不构成视觉L3闭环。

## 未关闭项与停止条件

- `open(material-rights)`：当前图库许可冲突未解决，继续research-only；实际可执行参考须自有或用途授权清楚。
- `open(image-effect)`：未生成新图片，未证明九张编排更好、参考图有增益、商品保真或人物一致性已改善；既有7项视觉失败与真人延期项保持原状态。
- 两件商品各一次九格预览加九张独立图的20次样例须另有明确授权；不自动启动、增加重试或重置旧预算。证明编排／图片参考增益仍分别需要控制条件的对照。

本工作包为源码实现与离线验证完成。未安装替换活动插件，未推送或发布，不自动续开实图或其他审计。
