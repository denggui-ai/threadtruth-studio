# 22张卡的动作池迁移（2026-11-02）

状态：`candidate/source`。按用户授权从`07ea0c8`在既有`feat/pose-library-minimal`分支／worktree继续，开工无未提交改动；本包不生图、不做新模型评测、不安装或发布。

## 完成范围

22张已有动作卡的176条词条全部迁入`references/pose-library/style-vocabulary.json`，卡片改为有序`pose_pool`引用。`visual_library.py show/prepare`解析回原八字段`pose_vocabulary`，同时冻结所选词条、所引用几何定义、版本与哈希；`visual_plan`校验来源与解析结果一致。动作候选只供编排，实际请求仍由逐张`body_action/hands/support`编译，不整池输出或自动附图。

- **164条原文字**：与基线八字段逐项相等，包含倒茶、扶车、翻书及无等价支撑的动作。
- **12条共享几何**：从已有52动作库继承身体、手位、支撑与附加限制，保留原词条ID、风格场景语境、原检查及限制。所需商品视角与迁移前一致。
- 22卡版本均升一个补丁号、索引同步；其他卡片字段完全相等，包括摄影、场景候选、人物语气、动作倾向、承诺与既有证据记录。另14卡保持原字节。
- 旧内嵌快照继续可用；新冻结任务的校验、恢复与导出不重读当前共享目录。男装等原文字路径继续可用，不扩大女版图片、儿童或真人新露脸角度范围；受限推袖不能进入自动动作池。

共享几何处置：

| 卡片 | 原词条ID → 自有动作／视图 |
|---|---|
| american-street | as-platform-wait → tt-stand-weight-shift / diag |
| athleisure | al-rail-pause → tt-lean-forearm-rail / diag；al-studio-floor-sit → tt-floor-cross-leg / front |
| bridal-ethereal | be-centre-stand → tt-stand-neutral / front |
| clean-fit | cf-window-stand → tt-stand-neutral / front |
| coquette-ladylike | cq-ankle-cross-stand → tt-stand-crossed-ankles / front |
| korean-menswear | km-atrium-stand → tt-stand-neutral / front；km-lobby-cube-sit → tt-sit-upright / front；km-back-still → tt-turn-back-still / back |
| nordic-minimal | nm-open-stand → tt-stand-neutral / front；nm-stair-pause → tt-stand-step-level / diag |
| workwear-vintage | wv-brick-stand → tt-stand-neutral / front |

日式`jl-floor-sit`初稿曾引用`tt-floor-side-fold/front`，逐项复核发现该几何实际需要`front-side`商品依据，而原词条只需`front`，已保留原文字，不改变既有支持范围：`fixed(MIGRATION-VIEW-01)`。

## 必要验证与证据复用

1. 新增`tests/test_style_pose_pool.py` **8项通过**：22卡／176条解析、22卡各原生与网页的**44个实际合成任务导出**、12条几何的商品视角门禁、冻结不重读、篡改拒绝、未知／重复／受限引用拒绝、男装文字与图片范围分离、旧冻结请求兼容。合成任务无授权、attempts=0，使用测试色块，不是商品样片或模型对话评测。
2. 旧冻结夹具从基线`07ea0c8`的实际脚本与卡片生成；迁移后原生／网页两条路线的prompt SHA256仍为`5694b7eff2e3276875eb7308e100979eb23c756bc3136e480e9468ca4c6d540c`。夹具保留在`tests/fixtures/style-pool-legacy.json`。
3. **24项受影响旧回归通过**：原动作词条9项、局部修订1项、知识与风格衔接8项、组件／旧请求／输出形态4项、主体范围／经典计划2项。知识默认行为测试使用同一已解析来源隔离承诺逻辑；旧卡存储兼容由上述真实基线夹具单独检验。
4. 176条对照基线原词条哈希与处置，164条完整相等，12条保留原视角／检查／限制；22卡非迁移字段及索引元数据保持，14卡字节保持。`show nordic-minimal`实际CLI输出与解析结果一致。
5. 52／60目录、图片、选姿页、知识目录、`shot_plan.py`与`web-task.py`相对基线无变化，复用既有资产、页面与原117／43项的有效证据，不重跑全量、图片哈希或浏览器交互，不把不同批次累计为一次全量通过。

初次新增测试执行因合成coverage遗漏系统必需的正面依据、对`avoid_when=none`的断言过严而失败；已修正测试数据与断言后通过，未放宽运行门禁。源侧新增PL-09–12四个场景，仅定义，未运行新模型评测。

系统skill-creator结构校验通过：默认Python缺PyYAML，使用本机已有`/usr/bin/python3`完成，未安装依赖。新增／修改的7处本地链接、26份JSON和27个场景ID唯一性检查通过；公共扫描及`git diff --check`通过。打包器原有递归`skills`范围已覆盖新增运行文件，仅阅读核对，未打包或修改打包器。

逐项处置与本地日志留在korea工作台`outputs/caiguang-card-pools-20261102/`：`migration-map.json`、`migration-verification.json`、两份回归日志；原始日志不入源码仓。共享文字目录SHA256为`1bee6c967cbdc64dabf2461e260a6f27a5e5fa28b531eb7beb0e63bfecaa7ac0`；176条处置清单SHA256为`26e176fa8267ea4d39841e296b777300afba8c55a56c0404357f56889fda0d0f`。

## 保留限制与停止条件

本包完成结构迁移与确定性传递，不证明新规划或成片效果优于旧文字。既有卡片预览接受记录只保留原范围；旧六图`qa-retry`、GEO-SLEEVE-01及商品／人物缺证均不关闭。未补写其余14卡、跨组历史数据库、近似姿势算法、推荐评分或新检索。

新增生图0、新模型评测0，无Astra或外审材料上传；池232/400、余168保持。安装仍为14／16候选，既有完整物料固定569a9b6且不包含本包。未安装、重新打包、推送、开PR、合并或公开发布；本地提交、交接更新后停止。
