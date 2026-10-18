# 本轮源码检查与失败闭环

适用范围：2026-10-18视觉工作室改版及2026-10-19网页执行封套修复。改版艺术方案基线为`f531e1a`，封套修复为`f5519a8`；各历史检查只证明其记录的版本和范围。

**首轮全套573项检查记录28个失败结果，不能写成“全套通过”。** 已记录失败均有后续定向闭环：18个pack/源码或旧断言失败，10个wardrobe依赖环境失败。没有留存全仓最终全部通过的重跑结果。最终source-evidence strict检查已通过；候选未安装，视觉与端到端验收未全通过。

## 首轮失败与定向闭环

| 范围 | 实际结果 | 证据层级与原件标识 | 限制 |
|---|---|---|---|
| 首轮全仓 | 573项，28个失败结果 | 原始unittest输出：`full-tests.log` | 28包含subtest失败，涉及15个失败方法；没有后续全仓绿灯记录 |
| pack相关闭环 | 18失败结果已处理；23个不同方法对其最终相关文件有通过记录 | 结构化执行记录：`capability-integration-fixes.json` | 1个真实balletcore氛围回归，另17个过时断言/字面期望；不能称18个运行时缺陷 |
| pack中间与最终检查 | 中间22项为21通过、1失败；修正受过滤措辞后，最终受影响3项通过 | 同上 | 两次范围有重叠，22＋3不等于25个不同方法；保留中间失败 |
| wardrobe环境闭环 | 14项重跑通过，覆盖10个原`host-provided Node sharp unavailable`失败 | 原始复跑输出：`wardrobe-test-rerun.log`；原因见首轮日志 | 复跑日志未包含完整命令和依赖路径，不补写未留存细节；未重跑全仓 |
| 根代理定向检查 | 32项通过 | 原始详细输出：`root-targeted-tests.log` | 覆盖仓库/公开资料契约、共同路线与画布流程、视觉表达；不是全仓 |

pack与wardrobe合计37个不同方法有针对性通过证据。源码修复记录所列五个修改文件的SHA256仍匹配留存记录；这是证据完整性核对，没有重新执行测试。

## 其他已有检查的实际范围

| 范围 | 留存结果 | 证据与限制 |
|---|---|---|
| 运行时视觉方案集成 | 248项通过，其中23项新visual-plan、225项既有运行时；最终SHA格式约束后跟进32项通过 | `runtime-checks.json`为结构化执行记录。248项发生在最后SHA强化前；后续32项是受影响范围，且与其他批次重叠 |
| 运行时辅助检查 | 4个代表性旧协议组合字节/指纹一致；36入口实际准备导出、206精确别名与7路由意图通过 | 合成素材与确定性helper检查，不是36组实图，也不增加fresh对话计数；不主张普遍字节等价或并发写入安全 |
| 能力目录 | 8个目录测试通过；99个声明用途编译、12个新入口六镜准备完成 | `capability-checks.json`；早期balletcore卡哈希由后续修复记录替代。24个新增行为case和13个保护case只是已编写定义，不是模型执行通过 |
| trigger路由 | 133归属断言、29查询、3计分账本、47风格目标、1核心冲突断言通过 | 由`capability-checks.json`记载，未找到单独stdout磁盘日志；不是新模型会话或经验触发率 |
| 网页执行封套 | 14新测试＋160既有运行时＋14仓库契约，共188项有通过记载；最后受影响14＋21＝35项重跑通过 | 见[封套源码验证说明](../2026-10-19-web-execution-envelope.md)。188依据源码验证说明，未另存原始unittest磁盘日志；35与188重叠，不累计为223，也不是573项全仓重跑 |
| 网页兼容与留存导出 | 7个旧writer导出字节一致，35份现存导出核对通过 | 有`web-execution-compatibility.json`及对应检查脚本；35为32个当前单张准备＋3个旧版对照。原任务写入、图片和浏览器调用均为0 |

网页兼容记录中，4个网页case明确验证加封套后旧原件不变；3个原生case的`old_bytes_unchanged_after_envelope=false`由脚本的`route == chatgpt_web`赋值得到，表示未创建原生封套，不是导出字节比较失败。所有7个case的旧新版导出比较均为true。

封套补丁保留初始测试fixture问题与缺PyYAML尝试，后续使用已有依赖修正并通过对应检查；没有因此放松授权或历史门禁。它证明本地传输约束和哈希绑定，不能认证远端实际工具调用次数，也不能由此宣称真实接收端、图像质量或端到端已通过。

## 结构标准与候选包

初始`quick-validate.log`、`source-standard.log`、`runtime-stage-standard.log`、`pack-lint.log`和`public-scan.log`保留结构、源标准、运行包标准、24包及公开资料扫描的通过输出。它们属于较早的158行SKILL、223项源eval记录范围，不能自动当作最后f551源码证据的严格审计。

固定f551候选有命令参数、返回码、日志SHA及原始输出，证明该候选的quick_validate、runtime profile strict、解包后`web-task.py --help`和归档checksum通过。其manifest明确：全代码测试未重跑，复用188项限定证据；构建当时source-evidence strict尚未执行。解包help不是新环境或完整生命周期验证；包仍为`candidate-not-release`，视觉门禁`not-passed`，未安装或发布。

**最终source-evidence strict：PASS（2026-10-19）。** 实际执行生产治理的`check_skill_standard.py`，参数为本仓`skills/threadtruth-studio --evidence-dir <repository-root> --strict`，使用已有host依赖且设置`PYTHONDONTWRITEBYTECODE=1`，未安装依赖。检查确认159行SKILL、状态/DoD/权限门禁、references与226项源eval、CHANGELOG等结构；这是源证据结构审查，不是226项模型执行或视觉通过。

原始命令、完整输出与回执留在私有`final-checks/source-standard`记录，输出SHA256为`dcf5c4c83ad389c27eed06c20d2f9d3dfaaa27619eac32d1ba6e5d3f10fe2459`。同轮`tools/public-scan.py --root <repository-root>`和`git diff --check`通过；运行源码未变，不重跑已有效的代码/候选包检查。

## 结论边界

各批检查存在重叠，不相加形成“全套通过数”。[静态准备记录](static-validation.json)中的60请求、18源素材、36源eval和12对话定义是预执行快照，不能冒充真实对话完成；旧任务兼容只保留既有确定性证据，不构造fresh兼容对话。真实对话与图像结果见[实际结果](live-results.md)。源码、结构、真实行为、视觉验收和安装分别判定。
