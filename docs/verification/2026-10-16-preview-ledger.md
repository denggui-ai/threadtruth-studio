# Q04：六宫格预览接入统一账本

日期2026-10-16，源码基线0046710。用户指定只推进Q04，仍不生图。本批使用系统skill-creator创作，目标为开发仓的skills/threadtruth-studio；回归定义、CHANGELOG与验证记录留在源侧。未改本机已安装版本或公开beta包。

## 用户能力与结果

| 能力 | 实现 | 状态 |
|---|---|---|
| 预览次数 | schema2 purpose=preview-grid，一条完整六格prompt；初次1次，最多另加3次明确授权修正；每次reserve占一次，失败/重试保留 | fixed(source/local) |
| 预览状态 | 有有效grid或其历史则preview-grid，无有效原图仍prepared；accept不是选人确认；finish-preview记录方向确认或停止，complete不等于商业就绪 | fixed(source/local) |
| 结束与恢复 | 可取消未提交预览；returned先评定，unknown/reserved先恢复，已知失败须核原请求；关闭后不继续提交 | fixed(source/local) |
| 承接独立图 | prepare-delivery关联1/6张新任务，原始服饰/人物依据保持；grid仅存冻结provenance，独立画布/授权/首张技术与人物确认 | fixed(source/local) |
| 历史不清零 | 预览attempts含全部已提交请求；正式任务total_attempts含上游预览，任务本地attempts单独计；上游快照与grid副本核哈希，一次预览只关联一个正式任务 | fixed(source/local) |
| 真人与多套 | 六格真实朝向计划、实际附件并集最多5张、逐格Image编号映射；多套选一套须显式选择原始商品hash，不以grid提取新商品或身份 | fixed(source/local) |

本轮没有把预览变成商业成片；confirm-model、export-model和直接+5都拒绝preview。非人像支持同一预览生命周期；真人预览无后续锚点占位，普通独立成片仍保留原后续锚点限制。既有任务没有preview-purpose就保持原语义，不自动迁移。

## 验证与复核

- 先补真实本地API/CLI回归，观察旧代码不支持preview-grid purpose的预期失败，再实现；另对来源快照篡改和逐格附件映射分别观察红灯后修正。
- tests/test_preview_task.py含17个用例，合成色块/临时账本覆盖原生与网页、次数、错误状态、修正上限、停止、1张/6张承接、跨任务累计、人物确认隔离、画布隔离、真人六格并集/真实覆盖、CLI、多套选取及来源防篡改；没有调用图片工具。
- 定向预览/common-flow/web-task/model-task/real-face-plan：128项通过，58个subtests通过。包括承接后独立首张实际导入、确认门禁及后续参考，不以文字断言代替执行。
- 首轮和最终全量均480项通过；最终运行105.894秒（unittest实报）。系统creator quick_validate、公共扫描及git diff --check通过。既有本机依赖环境及bundled Node包复用，没有安装依赖。
- 独立只读源码审查发现1项P2：真人六格合并附件后实际prompt缺少逐格引用编号。已增加实际Image编号、selection note与禁止跨格混商品的说明，回归先失败再通过，独立复核fixed；无其它open P1/P2。
- PV-01–06位于evals/preview-ledger-evals.json，是源侧场景定义，没有执行新模型会话或视觉评测，不能升级为真实对话/画面验收。

## 使用与范围

运行说明集中在references/preview-ledger.md，并从SKILL、flow-gates、prompt-build和网页记录说明导入。操作只改变本地记录；实际授权真假和图片是否真的有六格/正确标记仍由操作者核对。记录会保留预览结束与关联路径；进程在跨目录承接写入时中断，须先核原preview和目标目录，不换目录盲目重复。未做进程崩溃注入验证。

本批结束于源码、本地验证与提交；图片生成调用0，未安装、推送、发布或重开锁脸研究。当前安装版仍是上一轮常用交互修订版，尚不含本Q04。Q07/Q09/Q10/Q11保持未处理，不自动进入下一包。
