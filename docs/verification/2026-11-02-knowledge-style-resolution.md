# 知识与风格规则的执行衔接

日期：2026-11-02。基线7f78875，现有 `feat/pose-library-minimal` 分支及pose-library-minimal worktree；开工无未提交改动。范围与停止条件已先同步到[当前交接](../../.ai/handoff.md)和[开发路线](../development/model-selection-roadmap.md)。本包为candidate(source)，不代表视觉验收。

## 核对结果与最小修改

当前已有36个执行入口、207条知识记录；25张卡带commitments，22张带动作词条。摄影、商品保护、人物过滤、来源快照、逐张计划和双路线导出已有实现，不重建或重写全库。

| 发现 | 处置与证据 | 状态 |
|---|---|---|
| 改本轮环境配色后，原卡承诺仍能给出相反要求 | 基线prepare接受暖棕palette却同时输出`kc-cool-white-balance`的冷白灰环境句；尝试修订承诺被入口拒绝。新增`overrides.commitments`完整替换列表，仍用现有结构、人物／形态过滤及冻结字段；移除的原卡ID以`explicit-override`留痕。T02合成任务的实际请求只含修订后的该条承诺，其他相容承诺保持。 | fixed(source) |
| 知识／文化／融合来源留痕未说明怎样变成执行要求 | 明确profile仅渲染ID与通用边界、asset_trace不渲染、supporting卡不自动合并。选中的内容需转入已有garment、photography、shot_plan、art等字段；补T02、C19与主辅布景示例。C11/C19合成任务确认商品保护、限制及展示目的进入实际请求，资料内部说明与ID不被灌入。 | fixed(source-guidance) |
| 准备说明仍写“仅五张卡有承诺” | 改为读取所选卡的实际字段；本轮未修改卡片、索引、知识目录或风格包。 | fixed |

只有显式提供override才替换承诺，未提供时保持原默认。脚本校验字段和过滤，不判断自然语言语义冲突；代理仍须核对摄影、逐张值、承诺与商品／人物是否相容。没有扩充知识记录、自动语义规则合并或新检索服务。

## 实际验证

- **8项新增定向回归有通过结果**：显式修订与默认分离、完整替换／移除留痕、人物锁定与五种输出形态、错误输入、知识转译、主辅字段归属、subset继承、与7f78875默认准备结果一致。
- **16项既有受影响回归通过**：`test_wp21_orchestration`的CommitmentTests、AssetTraceTests、ContractTests；`test_visual_expression`的VisualLibraryTests；`test_visual_plan`中实际结构化任务导出、双路线共用字节及旧无计划任务回放三项。含36入口默认prepare，不重跑仓库全量或上包姿势117项。
- **6个实际合成任务**：T02暖棕环境修订、C11旗袍范围转译、C19工布范围转译，各原生／网页两条。经过prepare→create/read→export，网页另导出单次执行信封；核对prompt、manifest、引用哈希及附件顺序，两路线艺术正文一致。未authorize、reserve或调用模型，attempts均0。测试素材为临时色块，不是服饰质量证据。冻结后改变传入草稿，旧导出保持。
- 首轮新增测试的3个子断言失败，原因是测试以旧v1六格信封前缀断言v2任务。改为现有按版本选择的前缀后7项通过；随后新增subset一项单独通过。未改信封代码，也未用通过结果隐去这次测试错误。
- source-side `visual-library-evals.json`新增3条知识／承诺场景，修订2条既有场景；27个ID唯一、JSON解析通过。**仅定义，未启动模型对话评测。**
- 系统skill-creator `quick_validate.py`通过。默认Python缺PyYAML，改用本机已有 `/usr/bin/python3`完成；未安装依赖。新增／修改文档的本地链接、公共文本扫描与`git diff --check`通过。

回归命令使用`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests:. python3 -m unittest`。运行代码只修改prepare入口，visual_plan渲染器、账本、旧任务格式和姿势库保持。

## 保留缺口与停止点

本包只证明源码与规则传递；代理在新聊天中是否稳定按说明选择／转译知识，以及实际画面收益均未验证。既有六图仍qa-retry，盲评未证明稳定成片收益，POSE-POC-01/02及商品／人物人工确认缺口保留。

GEO-SLEEVE-01仍open：推袖R029/v4为user-only，默认候选排除、自动选择拒绝；明确指定默认文字，明确附图才返回引用，两者均保留遮腹限制，不能用于腰腹无遮挡目标。本包未改任何姿势条目。

新增生图0，新模型评测0，无Astra或外审材料上传；池232/400、余168保持。本机仍为14／16候选，源码52／60未安装。22卡整体迁移、跨组历史数据库、近似姿势、推荐评分、新检索及无关UI仍暂缓。核验完成后本地提交并停止；未安装、打包、推送、开PR、合并或公开发布。
