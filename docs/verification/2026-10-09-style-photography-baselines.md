# 摄影基准接入 Skill：源码验证

日期：2026-10-09。变更前源码基线：`3f85696`。作者流程：系统 skill-creator；第二阶段：production-governor 独立只读审查。运行目标为 `skills/threadtruth-studio`，证据根为本开发仓库；私人输出目录名为 `caiguang-style-baselines-20261009`。

## 用户能力与范围

用户希望24风格的效果尽量接近各自案例，并明确选择本轮只推进 Skill、不新增生图。此前 [24张案例像素对照](2026-10-09-style-case-alignment.md) 已形成逐风格摄影观察；本轮将相容基准接入运行规则，使执行者在所选风格准备与QA时有可读取的具体依据。

新增 `references/style-photography-baselines.md`：24个slug小节，分别保留各自光影、色彩、空间和支撑关系。入口、提示词组装与商业QA连接该参考，只读取公共使用方式及所选slug，避免把全部目录注入请求。示例编排不改变母版、默认模式、场景索引或景别；B/D棚拍、半身和非人像按本次条件转译相容部分。

商品事实、用户明确呈现、所选pack气质和已核真人计划保持优先。真人原表情、真实参考覆盖与body/head/gaze依据不变；AI/new不新增真人朝向限制。读取基准不要求增加案例附件，含其他人脸的审美图仍仅为审美角色，不能由角色声明保证硬锁脸或宣布漂移根因已证实。

24风格包、全部脚本、schema、辅助工具默认值和历史冻结任务未修改。本轮净runtime差异只有入口及两处引用、新增一份基准文件；旧47文件快照与新48文件stage已保留。完整原始日志、哈希与独立报告留在私人证据目录，不纳入运行包。

## 回归与检查

- 源侧新增 SB-01–SB-03 三份场景，主eval IDs197–199同步：风格差异、明确呈现与人物分流、分项QA及完成声明。它们是定义，不是三次模型运行。
- 定向 `unittest`：photography_spec、photography_targets、repository_contract 共 **47项通过**，7.828秒；包含既有B/D边界、景别、真人计划、AI/new、24编译与实际请求传递。没有因参考文档修改重复跑既有443项全量。
- 系统 creator quick_validate、governor source strict、JSON/ID/参考链接与diff检查通过。
- 24个基准slug与注册目录集合一致，目标对应既有像素审计卡；24pack与变更前及安装版一致。
- 净 **48文件 runtime-stage** 与源码逐字节一致；runtime strict及public-scan通过，独立审查亦复跑通过。无source eval、CHANGELOG、日志、用户素材、symlink或cache混入stage。
- 源目录存在既有 `scripts/__pycache__`，独立审查直接对源树做runtime profile时因此失败。未清理无关缓存；以净stage处理发布payload卫生，不能宣称源树直接runtime检查已通过。

独立源侧审查未发现必须修正的规则或参考路由问题；当前open/must-fix为0。没有新增生图、新模型会话、网络动作、安装或发布。

## 裁定与停止点

结论：**源侧规则与净运行包检查通过；行为与画面仍为candidate。** 新规则最多支持L2源侧定义与静态检查，不宣称L3闭环或24风格实际画面通过。上一张新中式摄影获认可、锁脸和商品细节失败的结论保持；四附件身份隔离请求仍未执行，本轮用户明确不增加调用。

- `fixed(SB-REFERENCE-ROUTING)`：基准已接入入口、提示词与QA，所选slug按需读取。
- `fixed(SB-RUNTIME-CACHE, scoped-clean-stage)`：净stage排除既有缓存并验证，源缓存保留。
- `deferred(current-behavior-and-image-validation)`：尚无新模型会话或画面验证，不安装、不发布、不升级成熟度。
- `deferred(issue:SB-D-NONPORTRAIT-SAMPLING)`：新增三份源侧场景未单独展开D与非人像取样；公共转译规则与现有D机械回归保持，作为非阻断后续取样，不扩大当前工作。

本源码工作包到此收口，后续实际效果与锁脸按具体任务另行验证；摄影改善不能抵消身份或商品失败。
