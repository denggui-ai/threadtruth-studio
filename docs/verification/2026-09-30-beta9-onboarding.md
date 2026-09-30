# beta.9 Caiguang 安装体验候选验证

Conclusion: conditional — 本地候选准备通过；非维护者新环境试用仍待进行。
Mode and scope: `release`，仅本地 Codex Plugin 候选包与试用指南。
Runtime path: `skills/threadtruth-studio`。
Evidence root: 仓库根目录；测试、changelog 与本记录不进入 runtime。
Status: `candidate`。本状态不提升 24 风格包的 `DRAFT` 等级。

## 授权与实现边界

- 用户批准先准备 beta.9 的安装品牌一致性，并准备非维护者试用验收步骤。
- 显示名统一为“裁光 · Caiguang”，品类说明为 AI Fashion Studio；插件版本为 `1.0.0-beta.9`，项目 URL 同步当前仓库与网站。
- 技术 ID、`$threadtruth-studio`、注册 selector、安装目录、implicit policy、默认提示词、风格和生成门禁均保留。
- 对 runtime 全部文件逐字节比对基线 `33a3a75`：只有 SKILL 标题与 agents UI 显示名不同，除此之外完全一致。
- `guide-required`：离线 HTML 与对应 beta.9 的试用 Markdown 提供安装、识别、独立单张授权、回滚、移除、数据流和脱敏记录步骤。表格不预填成功。
- 未修改全局配置、live skill 或当前启用插件；未调用 Codex 安装命令、真实技能触发或图片服务；未联系试用者、推送、公开发布或替换 beta.8 资产。

## 发现及闭环

1. `fixed` / Stabilization：公开名称与插件、skill 的 UI 名称不同，项目元数据仍指向旧账号。已同步显示信息，并保留技术兼容性。
2. `fixed` / Stabilization：旧构建器复制整个 docs 与开发 changelog，会把验证记录和开发状态一并交付。改为明确用户文档清单，排除 CHANGELOG、RELEASE、ROADMAP、WORK-STATUS、申请材料、verification 和 superpowers。公开案例图片及其必需权利/来源记录仍随包保留，未修改历史媒体字节。
3. `fixed` / Stabilization：旧离线指南混合历史版本安装文字。新版明确 beta.9 candidate，保留 beta.8 公共安装指南并增加版本分流，校验失败时不执行解压。同步修正深色模式行内代码对比。

包排除回归先在旧构建逻辑下复现失败（CHANGELOG 仍存在），收紧清单后通过；未为显示文字新增复述实现的测试。

## 已验证

- 全量 Python 测试：216 项通过，84.125 秒。
- 现有 manifest 身份契约与实际归档排除检查更新后通过；基础技能校验、源码 strict 标准检查、runtime-stage strict、官方插件校验均通过。
- 24 风格 pack lint、132 归属 / 22 query / 3 评分 / 47 style / 13 conflict / 1 core conflict 断言通过。Public tree + history scan、diff whitespace 检查通过。
- ZIP 校验命令实跑通过，条目安全边界、大小限制、重复名称、压缩比、CRC、无源码证据目录检查通过；干净解压后各文件与源文件逐字节一致。
- 隔离临时 recipient 中验证：预检不写入；首次注册；保留其他 marketplace 条目和非默认名称；旧版元数据夹具升级至 beta.9、保留备份、无重复注册、恢复旧版元数据成功。未设置或改写系统 HOME，未调用真实 Codex。
- 解压后的默认入口脚本返回 `codex_native`，web-task 帮助启动正常。这是确定性本地 smoke，不是模型行为证据。
- 离线 HTML：1440/390/320px × light/dark 六组 Chromium 验证，无页面横向溢出、JS 错误或远程运行资产，本地链接和锚点存在，键盘 skip link 可用，打印导航隐藏。已目视复核手机明暗两版安装区；未声称真实 Safari 验证。

## 未验证与后续

- 非维护者新电脑的安装、Codex GUI 显示、新任务触发、识别理解与单张图像质量仍为 `not-tested`。
- 升级/回滚夹具使用当前源与历史 beta.8 manifest 元数据，不是冻结 beta.8 ZIP 的真实 Codex 升级实测。缓存启用、真实移除、完整生命周期仍待试用。
- 没有新增外部采用、完整案例或 L3 模型行为闭环声明。
- 下一步：把候选 ZIP、匹配 checksum 与离线指南交给自愿参与的非维护者，使用 `docs/BETA9-TRYOUT.md` 记录实际结果；修正问题后再决定公开 beta.9。技术 ID 迁移与新六图套装案例不在本轮范围。

## 候选制品

- 文件：`threadtruth-studio-1.0.0-beta.9.zip`。
- SHA-256：`fe3bc21f864c17a0fb11ecbef85027e0f725ca3021c35cb10b35bb55bdd45321`。
- 269 个文件；仅为本地候选制品，未创建公开 tag 或 Release。

## 独立审查闭环

独立只读审查未发现 P1/P2；一项 P3 已 `fixed`：仍被递归复制的 `docs/demo/GROWTH.md` 属于旧开发规划，并链接到已排除的工作台账。候选包已排除它，源码历史不改。先复现归档排除断言失败，再修复为通过；重新打包、校验、干净解压及隔离注册/升级/回滚 smoke 全部通过。项目中无其他文档链接到该文件，未产生新的本地引用缺口。Open findings = 0。

独立审查采用已完成的 216 项测试证据，没有重复全量测试。修复后只重跑受影响的归档回归与制品核验；runtime 和网页产品未变。
