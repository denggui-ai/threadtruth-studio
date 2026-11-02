# POC流程闭环修复：本地验证

日期：2026-11-02。运行目标：`skills/threadtruth-studio`；源侧证据根：本仓库。模式为已批准方案的源码修复与必要质量核验。作者入口使用system skill-creator，静态证据门禁单独使用production governor。

**结论：本包流程和代码修复完成，声明范围内本地检查通过。** 运行行为仍为源码candidate，未安装、发布或验证新画面。真实人物/商品稳定性和审核触发原因没有因此得到证明。

## 修复范围与闭环

| 原问题 | 当前行为 | 状态与证据 |
|---|---|---|
| 风格、预览/直出、张数未形成完整执行依据 | 新schema2标workflow_version=1；一次方案确认绑定已有选择、当前阶段数量及实际请求指纹，reserve检查缺失/过期记录 | fixed(source)：确认缺项、错风格/张数/路线、明确直出、预览、CLI预览转成片 |
| 查库未落实到动作 | 新v2逐张保存风格词条/自有库快照或custom/not-applicable理由；适用成人女装按目标查询推荐并核适配，默认文字，历史仅用用户指定范围 | fixed(source)：库内动作实际进入原生/网页导出，无历史摘要时不添加历史，合理自定义可用；代理实际遵循未做新模型评测 |
| 已核实failed不能结构化修订 | 同张动作/构图/已冻结相关参考可修订，保留原目标与其他图；核实记录绑定失败哈希和attempt | fixed(code)：原缺陷先失败后通过；未核实/unknown/旧attempt/过期计划继续阻止 |
| 审核后相似请求未暂停 | 明确moderation_blocked首次暂停同形态与detail/身体取景组；暂停不计调用，已核对不受影响的其他编号可继续 | fixed(code/rules)：根任务及关联子任务暂停覆盖、普通视觉拒收与非审核错误分支 |
| 首张纠正后拆单，系列与计数脱节 | prepare-revision/adopt-revision保留根图号、旧图/失败与当前采用来源；旧槽停用、根子共用锁；无下游时首张可接回，子任务不自行加预算 | fixed(code)：首张接回/继续、重复采用、unknown、并发、同SKU/人物/画幅、ratio-first像素基线、CLI及累计次数 |
| 人物改静物未经明确确认，逐张输入过宽 | 形态变化须明确依据；非人像子任务只用原商品来源；garment_focus收敛当前商品描述，原展示目标与must_show仍进入关联请求 | fixed(code/rules)：无确认拒绝、静物附件/请求、原目标传递；不能推断这些调整必然通过审核 |
| 目标失败混入摄影待核 | 记录要求/实际观察/met-unmet-unknown；商品/身份/人体/展示目标unmet为qa-retry，缺证与摄影偏好单列；用户保留不清除偏差 | fixed(code/rules)：目标失败不能以qa-user-review接受，保留/再评估留痕；files_complete与goals_met分开 |

当前包源码发现open=0。画面稳定性、实物核对和实际模型对话遵循为deferred(out-of-scope)，没有新增自动工作包或调用授权。

## 验证与初次失败

- 仓库unittest全量实际运行823项，首轮805项通过、18项失败/错误；不是一次全绿运行。16项为默认Python缺fontTools，改用现有品牌虚拟环境补跑16/16通过，没有安装新依赖。
- 另外两项：新QA历史验证对畸形字符串抛TypeError，已恢复为原本的受控拒绝；旧错误提示测试通过mock伪造不完整failure_reconciliation，改为真实failed→reconcile-failure路径，保留更严格的核实门禁。最终相关54项通过，逐项核对覆盖首轮所有18项失败；未重复未受影响的通过项。
- 新增[23项流程回归](../../tests/test_workflow_closure.py)，使用合成PNG与本地CLI，不做真实生成或视觉质量断言。原CLI端到端、运行时速查、旧任务恢复、动作/引用/计划及原生/网页导出均在覆盖内。
- 另补一项旧status兼容回归：保持只读诊断能力，不追写新确认字段，损坏证据仍禁止导出/执行。首轮823项加该项共824项得到所述覆盖。
- 旧测试中的95处账本工厂调用显式固定workflow_version=0，保留旧冻结任务的契约回归；新工厂默认与新CLI仍为1，没有为通过旧测试降低产品门禁。
- 24包严格lint通过；既有trigger-eval的133条归属、29条查询、3条评分账本、47条风格目标与1条core冲突断言通过。这是离线确定性检查，不是新模型隐式触发评测。
- system creator初次因缺PyYAML未执行，随后使用现有开发虚拟环境通过；governor quick/source strict通过。直接对源目录做runtime检查发现既有`__pycache__`，未删除历史缓存；allowlist临时构建排除缓存后runtime strict通过。
- JSON解析与Python无缓存编译通过，公共文本/历史扫描与diff检查通过。临时allowlist构建只验证打包边界；未更改版本、现有发布资产或安装目录。
- 官网、素材与浏览器脚本未改，复用同一源码中已完成的36方向页面验收；没有重复运行无关浏览器/视觉测试。

完整本地日志、初次失败、补跑结果及哈希留在工作台`outputs/caiguang-poc-closure-20261102/`，不进入运行包或`.ai`。本报告保留脱敏结论，不复制客户素材、原始请求或完整日志。

## 运行与证据边界

新命令和字段见[运行时速查](../../skills/threadtruth-studio/references/runtime-quickstart.md)，目标QA见[商业QA](../../skills/threadtruth-studio/references/commercial-qa.md)。[WF-01–08](../../evals/workflow-closure-evals.json)是源侧定义，已从主eval索引注明；没有运行新模型对话，不声称L3/L4闭环或production-ready。

新契约只作用于新任务，旧冻结记录不追写；本次历史POC数据与图片未修改。脚本校验的是明确声明、文件、哈希、流程与预算，不能认证真实授权语义、判断图片是否满足目标、还原审核原因或保证图像质量。仍须按源图检查，未知来源外观参考不能升级为实物保真证据。

本包零生图、零新模型评测，不扩图库、不安装、不推送、不发布；必要检查和本地提交完成后停止。
