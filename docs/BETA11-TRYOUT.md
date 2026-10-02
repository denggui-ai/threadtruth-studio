# 裁光 / Caiguang beta.11 试用指南


**状态：beta.11 预发布试用。** 从 [beta.11 Release](https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.11) 取得 `threadtruth-studio-1.0.0-beta.11.zip` 与同名 `.sha256` 文件。不要把 beta.9 的校验文件用于 beta.11，也不要改 ZIP 名称来升级。新环境安装和桌面显示尚未由非维护者验证。

本版本新增缺背面时的第六张替代：正面/前侧清楚时明示改为正面自然站姿，前五保留，仍为六张；明确要求原六姿势或背部结构时先补同款实拍。动作重复验收失败。保留选角、首张验收、生图授权及额度规则。安装后预期显示 **裁光 · Caiguang**；技术名称、目录与调用指令继续使用 `threadtruth-studio`。

**English:** This guide covers the beta.11 prerelease ZIP and matching checksum. The expected display name is **裁光 · Caiguang**, while `$threadtruth-studio` and the installation directory stay unchanged. Older beta.9 and earlier downloads remain unchanged; fresh-host discovery and desktop display remain unverified. This trial does not authorize image generation or public sharing of your materials.

## 1. 试用前准备 / Before installation

- 使用自己的 macOS 电脑与 Codex 账号。需要 Python 3 和支持 `codex plugin add` 的 Codex CLI；其他系统暂不作为本轮通过范围。
- 记录 macOS、Codex CLI、桌面应用版本和试用起止时间。不要求填写账号、设备标识或本机完整路径。
- 第一步只安装与识别，不消耗图片生成额度；后续可自愿授权测试一张。图片功能、账号额度和宿主权限由 Codex 提供，不包含在插件中。
- 准备一张清晰且有权使用的服饰照片：优先使用自己的单件上衣或完整套装。没有合适照片时，先做第 4 节的无图片检查，服饰识别与出图记为 `not-tested`，不使用客户素材凑测试。
- 为压缩包、解压目录、插件源、Codex 缓存和旧版备份预留约 300 MB；实际安装时间由网络和本机环境决定，记录实际耗时。

在“终端”分别检查（不安装、不改配置）：

```bash
python3 --version
codex --version
codex plugin add --help
sw_vers -productVersion
```

**English:** Use your own Mac and Codex account. Check Python 3 and a CLI supporting plugin installation. Record software versions, elapsed time and whether this is a new installation or upgrade. Reserve about 300 MB for the ZIP, extracted files, source, cache and a backup. Start with recognition only; generating one image later requires separate approval and account quota. Supply only authorized garment photos; otherwise test the missing-input path and mark image steps untested.

## 2. 校验与解压 / Verify and extract

把 beta.11 的 ZIP 与匹配校验文件放在同一文件夹。先在终端进入该文件夹；若在默认下载目录，可执行：

```bash
cd "$HOME/Downloads" &&
shasum -a 256 -c threadtruth-studio-1.0.0-beta.11.zip.sha256 &&
unzip threadtruth-studio-1.0.0-beta.11.zip &&
cd threadtruth-studio-1.0.0-beta.11
```

只有校验输出 `threadtruth-studio-1.0.0-beta.11.zip: OK` 才继续。校验值应从可信交付渠道取得；与包一起收到的校验文件只能帮助检查一致性，不能独立认证发布者。若存在同名解压目录，先保留旧目录并换一个空文件夹，避免覆盖提示。不要使用 GitHub 自动生成的源码 ZIP。

**English:** Put both release files together and run the commands from that folder. Stop if verification fails. Extract into a fresh directory and use the full versioned release root, not the inner skill folder. Obtain the expected checksum through a trusted channel; a checksum alone does not authenticate the publisher.

## 3. 预检、安装与启用 / Preview, register and enable

首次安装先预检：

```bash
python3 install-local.py
```

预检不会写入。确认安装位置在自己的用户主目录 `plugins/threadtruth-studio`，注册表在 `.agents/plugins/marketplace.json`；不是系统目录，也不需要管理员权限。然后：

```bash
python3 install-local.py --apply
```

运行输出中 **`Next:` 后的完整命令**。默认个人 marketplace 的示例为：

```bash
codex plugin add threadtruth-studio@personal --json
codex plugin list --json
```

若安装器返回其他 marketplace 名称，以它打印的 selector 为准，不要拼接第二个 `@personal`。列表中核对已安装、已启用、版本以 `1.0.0-beta.11` 开头；预期显示名为“裁光 · Caiguang”。若界面仍显示旧名称，记录现象并停止反复重装，不要手工改全局配置。

**已有版本：** 不要执行覆盖式首次安装。先用 `python3 install-local.py --replace` 预检，再用 `python3 install-local.py --apply --replace` 应用，保留输出的 `source_backup` 和 `marketplace_backup`，执行新打印的 `Next:` 命令。升级时安装器会添加 `+codex.*` 版本后缀刷新缓存，这是预期行为；原 ZIP 校验值不变。

**English:** Preview first, then apply only after checking the paths. Registration copies to your home directory and preserves other marketplace entries; it does not enable the plugin. Run the exact printed `Next:` command and inspect the installed list. An existing source requires `--replace` in both preview and apply. Keep the reported backups. A `+codex.*` suffix after replacement is expected. Check the displayed name and version; do not repair failures by editing global configuration.

## 4. 新任务识别 / Recognition in a new task

每次安装或升级后都要新建 Codex 任务；旧任务不会重新加载技能。

先新建一个空白任务，不上传图片、不写技能名，检查 Issue #1 的原始入口：

```text
帮我把一件外套做成电商模特图。目前还没有上传图片，也没有授权生图。请简短回应。
```

预期先核对素材并请求真实服饰照片；首轮和收尾都不预告“授权后再生图”。若界面能显示工具读取，记录是否读入完整技能；只能看到技能名称时，加载情况记 `not-observable`。仅缺少读取记录不等于未加载。保留失败，不反复重试到成功。然后另开一个空白任务做显式调用对照：

```text
请用 $threadtruth-studio 帮我制作服饰模特图。先告诉我需要准备什么，不要生图。
```

预期：要求真实服饰图，说明输入要求，不编造服饰、不生成图片。这个无图片检查不需要提供任何素材。

再上传自己的服饰照片并输入：

```text
请用 $threadtruth-studio 识别并推荐风格，不要生图。
```

预期：返回服饰识别卡、主推及备选方向、完整 24 风格目录。核对颜色、款式、配饰和看不到的部位是否诚实标注；此时应生成 **0 张图片**。记录文字是否看得懂、是否需要维护者临时指导。

**English:** Run the original Chinese prompt above in a fresh empty task without naming the skill; keep input-checking replies separate from conditional generation promises. Record full skill loading only when the host exposes it, otherwise use `not-observable`. Do not retry away a failure. Use another fresh task for the explicit control below.

**English prompts:**

```text
Use $threadtruth-studio to help me create fashion model images. First explain what inputs you need. Do not generate images.
```

```text
Use $threadtruth-studio to identify this garment and recommend styles. Do not generate images.
```

Expected: request a real garment photo when missing; with a valid photo, return recognition and all 24 style choices without generating images.

### 缺背面方案文字检查 / Front-only plan check

已识别清楚的正面素材后，使用以下免费文字检查；不授权生图：

```text
我只有同款正面和前侧实拍，没有背面。通勤风格 C3，真人AI模特，只给六条编号提示词，不要生图。说明第六张如何避免与前五重复。
```

预期：前五默认动作保留；第六张为静止正面站立、双脚落地、无迈步/倚靠/俯身/侧身回转，去掉越肩回眸。明确背部未知，不能把 AI 背身图当实拍。若原素材严重模糊，先补图；若坚持原六姿势不变，先补背面或确认替代。实际图片仍需视觉验收。

Expected: preserve slots 1–5, disclose stationary frontal standing in slot 6, and reject duplicate actions. AI rear images do not supply garment facts. This free text check is not image-generation verification.

## 5. 自愿授权一张测试 / Optional one-image test

先核对识别结果并选定风格、场景、画幅，再明确授权。以下只是可复制示例，不代表试用参与者已经授权：

```text
使用刚才确认的服饰与电商棚拍风格（ecommerce-studio），真人模特，2:3 竖图。
允许在 Codex 中只生成 1 张测试图，不继续生成整组，不自动重试。
```

```text
Use the confirmed garment with ecommerce-studio styling, a human model and a 2:3 portrait canvas. I authorize exactly one test image in Codex. Do not continue the set or retry automatically.
```

可在测试指令中补充希望的表观年龄、体型表现、妆发和气质；未指定时沿用默认。首张应核对这些已声明条件，不能把明确要求未兑现降成审美偏好。风格名不推断国籍，照片人物身份不复制。

预期只生成一张并提供可保存文件。记录是否有原生图片能力、原文件实际尺寸、能否下载、服饰颜色/结构/配饰是否保持、是否出现明显人体问题。单张测试不算六张完整案例；有缺陷时保留结果并停止，不通过自动重试掩盖失败。无额度或工具不可用时，记录 `tool-blocked`，不改用 API 或第三方服务。

**English:** Confirm recognition and shoot choices before separately approving one test. Save the original, record actual dimensions, compare garment details and inspect anatomy. One image is not a complete six-image case. Keep failures; no automatic retry or API fallback. If the image capability is unavailable, record `tool-blocked` rather than treating installation as failed.

## 6. 回滚、移除与数据 / Rollback, removal and data

若升级失败，在已校验的新包目录运行当前安装器，以升级输出的旧版 `source_backup` 为源，先预检再应用：

```bash
python3 install-local.py --source "<reported-source_backup-path>" --replace
python3 install-local.py --source "<reported-source_backup-path>" --apply --replace
```

将占位符替换为真实备份路径，随后执行新打印的 `Next:` 命令并新建任务。不直接用旧 marketplace 文件覆盖当前配置，以免丢失后来合法添加的插件。

停用/移除启用状态使用 `codex plugin remove threadtruth-studio@personal --json`（非默认 marketplace 使用实际 selector）。此操作不会一并删除插件源、个人 marketplace 条目、缓存、备份、解压包或图片；保留它们可回滚，需要清理时单独核对后处理。未完成真实 Codex 移除测试时记 `not-tested`。

插件无独立遥测、额外 API key 或远程服务。上传到 Codex 的素材会由宿主处理；图片生成使用宿主服务及额度。输出和本地任务记录保存在用户选择的工作区，由用户决定删除；宿主侧留存遵循账号与服务商政策。不要把真实账号、客户照片、私有提示词、路径或完整日志写进反馈。

**English:** Roll back through the installer using the reported source backup, preview before applying, then enable with the new printed command and start a new task. Never blindly overwrite the marketplace backup. Plugin removal leaves source, registry entry, cache, backups and output files separate. The plugin adds no telemetry or API key requirement; host processing and retention still apply to materials submitted to Codex.

## 7. 脱敏验收记录 / Sanitized acceptance record

复制下表填写；每项用 `pass / fail / not-tested`。不要预填成功；本地脚本模拟不等于非维护者新环境验证。可先私下反馈，只有参与者明确同意，才发布脱敏结果并计入外部 Beta 记录。

| 项目 / Check | 状态 / Result | 简述 / Note |
|---|---|---|
| 收到 beta.11 ZIP 和匹配校验文件 / Prerelease received | not-tested | |
| 校验、解压 / Verify and extract | not-tested | |
| 首次安装或升级 / Install or upgrade | not-tested | |
| 显示名与实际版本 / Name and version | not-tested | |
| 新任务调用 / New-task invocation | not-tested | |
| 无技能名的原始短提示 / Minimal implicit entry (Issue #1) | not-tested | Full read: pass / fail / not-observable |
| 缺图收尾无生图预告 / Missing-input response | not-tested | |
| 服饰识别、完整目录、0 张生图 / Recognition only | not-tested | |
| 单张生图（可选）/ One image, optional | not-tested | |
| 原文件保存、尺寸、服饰对照 / File and visual review | not-tested | |
| 升级回滚（适用时）/ Rollback, if applicable | not-tested | |
| 移除启用状态（可选）/ Removal, optional | not-tested | |

附：是否非维护者、全新安装或旧版升级、系统/CLI/桌面版本、耗时、最难理解的一步、是否需要帮助；不含身份和私有路径。公开反馈可使用 [安装反馈表](https://github.com/denggui-ai/threadtruth-studio/issues/new?template=installation-feedback.yml)。

**English:** Record actual results, software versions, elapsed time, assistance needed and the most confusing step. Keep installation, recognition, generation, visual review and lifecycle results separate. Share only sanitized feedback, with separate consent before public attribution or Beta counting.

## 维护者发布条件

至少取得一位非维护者的新环境安装、显示名核对和识别实测；自愿单张出图结果与任何跳过原因单独记录。beta.11 已按维护者授权以预发布形式分发；继续收集这些证据，修正发现的问题并复测，不能因发布而将试用项标为完成。此表是试用步骤，不是已完成的证据，不自动增加外部采用或完整案例数量。
