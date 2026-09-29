# Install ThreadTruth Studio / 安装 ThreadTruth Studio

[English](#english) | [简体中文](#简体中文)

## English

### Before you begin

Download both files from the same [beta.8 prerelease](https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.8):

- [Plugin ZIP — threadtruth-studio-1.0.0-beta.8.zip](https://github.com/denggui-ai/threadtruth-studio/releases/download/v1.0.0-beta.8/threadtruth-studio-1.0.0-beta.8.zip)
- [Matching checksum — threadtruth-studio-1.0.0-beta.8.zip.sha256](https://github.com/denggui-ai/threadtruth-studio/releases/download/v1.0.0-beta.8/threadtruth-studio-1.0.0-beta.8.zip.sha256)

GitHub's automatic **Source code (zip)** and **Source code (tar.gz)** downloads are not the verified Plugin package. Optional media archives are not the Plugin either. Commands below target beta.8. A checksum checks integrity when obtained through a trusted channel and does not independently authenticate the publisher.

This online guide can receive onboarding corrections after publication. The published beta.8 ZIP, tag and checksum remain unchanged; older releases use their own bundled guides.

The release ZIP extracts to a versioned root such as `threadtruth-studio-1.0.0-beta.8/`. That whole root, containing `.codex-plugin/plugin.json` and `install-local.py`, is the install source. Do not use the inner `skills/threadtruth-studio/` folder.

On the tested maintainer host, installation requires macOS and Codex CLI with `plugin add` support; no administrator access or additional API key is needed. Allow about 100 MB for the source, cache and one backup, and a few minutes for local setup. A Codex account with native image access is needed for later generation, which requires separate approval and host quota. Fresh-host compatibility is unverified.

Before writing any installation files, open a terminal and check that Python 3 and the Codex plugin command are available:

```bash
python3 --version
codex plugin add --help
```

Continue only if the first command reports Python 3 and the second displays help for `plugin add`. If either command is missing or the subcommand is unsupported, stop and check [compatibility](COMPATIBILITY.md); do not run `--apply` or manually edit Codex configuration to bypass it.

### 1. Verify and extract

Put the Plugin ZIP and its matching sidecar in the same directory, then run:

```bash
shasum -a 256 -c threadtruth-studio-1.0.0-beta.8.zip.sha256
unzip threadtruth-studio-1.0.0-beta.8.zip
cd threadtruth-studio-1.0.0-beta.8
```

Use the actual published filenames if they differ. Stop if verification fails or extraction does not produce exactly one expected release root.

### 2. Preview, register, then enable

The helper is dry-run by default and prints JSON, including the source path, personal marketplace path, version, and returned `selector`:

```bash
python3 install-local.py
python3 install-local.py --apply
```

`--apply` copies the verified release to **home directory → `plugins` → `threadtruth-studio`** and registers that source in the implicitly discovered personal marketplace. It preserves unrelated marketplace entries. It does **not** enable the Plugin or edit Codex enabled-plugin state.

Run the exact `Next:` command printed by the helper. With the default marketplace it is:

```bash
codex plugin add threadtruth-studio@personal --json
codex plugin list --marketplace personal --json
```

The returned `selector` is already the full `plugin@marketplace` value. If the helper reports a marketplace name other than `personal`, use its printed command and substitute that marketplace name in the list command. Do not manually edit JSON/TOML. Do not run `codex plugin marketplace add` for the default personal marketplace.

In the JSON `installed` list, find the entry whose `pluginId` matches the helper's selector (normally `threadtruth-studio@personal`) and check that both `installed` and `enabled` are `true`. Do not use `--available` as proof of installation: it also includes uninstalled marketplace plugins. This checks installation and enablement; the new-task recognition check below verifies that the Skill can actually be used.

### 3. First use

Start a **new Codex task** so the Skill is loaded. Upload a garment image first, then enter exactly:

```text
Use $threadtruth-studio to identify this garment and recommend styles. Do not generate images.
```

Expected: a garment recognition card, a primary recommendation plus alternatives, and the full 24-style catalogue. No image should be generated and no generation cost is authorized.

First use succeeds when the installed entry is enabled, the new task can invoke `$threadtruth-studio`, and the recognition card and style catalogue appear. Share a brief success or failure through the [installation feedback form](https://github.com/denggui-ai/threadtruth-studio/issues/new?template=installation-feedback.yml); report the actual installed version, or the attempted release if installation did not complete, and keep private images, credentials and full logs out of the public Issue.

### Troubleshooting

| What happened | What to do next |
|---|---|
| Checksum fails, or the expected release root is missing | Stop before installation. Download the named Plugin ZIP and its matching checksum from the same release again, then repeat verification and extraction. Do not substitute the source-code ZIP. |
| The helper reports an existing installation | Keep it intact. Follow **Upgrade and rollback** below, previewing with `--replace` before applying; retain the reported backups. |
| Python or `codex plugin add` is unavailable | Stop before `--apply`. Check the supported setup in [compatibility](COMPATIBILITY.md), make the required command available, then rerun the preflight. Fresh-host support is not assumed. |
| The Plugin is missing, disabled, or recognition does not appear | Run the helper's exact `Next:` command, then check its selector in the `installed` list without `--available`. Start a new task, upload your garment image and use the explicit prompt above. If it still fails, report your host/version and a short sanitized result through the feedback form. Do not retry by generating images. |

### Upgrade and rollback

From a separately extracted and checksum-verified newer release, include `--replace` in the dry-run because an active source already exists. Inspect the reported paths, then apply and run the exact `Next:` command printed by the helper:

```bash
python3 install-local.py --replace
python3 install-local.py --apply --replace
codex plugin add threadtruth-studio@personal --json
```

`--replace` creates UTC-stamped backups of the active source and, when present, marketplace config. It adds a UTC `+codex.*` cachebuster to the installed manifest, so installed bytes intentionally differ from the pristine archive. Keep both archive checksum and installed version in any audit record. Start a new task after upgrade.

If runtime verification fails, use the `source_backup` path printed by the applied upgrade; do not overwrite the marketplace file from its backup because it may contain legitimate later changes:

```bash
python3 install-local.py --source <reported-source_backup-path> --replace
python3 install-local.py --source <reported-source_backup-path> --apply --replace
codex plugin add threadtruth-studio@personal --json
```

Again, use the helper's exact printed `Next:` command if the marketplace name is not `personal`, then start a new task and verify the restored release. To remove enabled state, use `codex plugin remove threadtruth-studio@personal --json` (or the returned non-default selector). Source directory, marketplace entry, and backups are separate layers and are retained unless deliberately handled.

### Distribution channels

- **Personal Plugin source:** the tested installer path described above.
- **GitHub:** source code and Release downloads; cloning a repository is not Codex registration or enablement.
- **Official marketplace:** no listing or acceptance is claimed.

See [compatibility](COMPATIBILITY.md). Submit sanitized installation results through the [installation feedback form](https://github.com/denggui-ai/threadtruth-studio/issues/new?template=installation-feedback.yml); use [Discussions](https://github.com/denggui-ai/threadtruth-studio/discussions) for broader questions.

## 简体中文

### 开始前

从同一个 [beta.8 预发布页](https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.8)下载这两个文件：

- [插件 ZIP — threadtruth-studio-1.0.0-beta.8.zip](https://github.com/denggui-ai/threadtruth-studio/releases/download/v1.0.0-beta.8/threadtruth-studio-1.0.0-beta.8.zip)
- [匹配的校验文件 — threadtruth-studio-1.0.0-beta.8.zip.sha256](https://github.com/denggui-ai/threadtruth-studio/releases/download/v1.0.0-beta.8/threadtruth-studio-1.0.0-beta.8.zip.sha256)

GitHub 自动生成的 **Source code (zip)** 和 **Source code (tar.gz)** 不是已验证的插件安装包；媒体包也不是插件。以下命令针对 beta.8。请经可信渠道取得校验值；checksum 本身不能认证发布者身份。

在线指南可能在发布后修订上手说明，已发布 beta.8 的 ZIP、标签及校验值保持不变；旧版本使用各自包内指南。

发行 ZIP 会解压为带版本号的根目录，例如 `threadtruth-studio-1.0.0-beta.8/`。安装源是包含 `.codex-plugin/plugin.json` 与 `install-local.py` 的整个根目录，不是内层 `skills/threadtruth-studio/`。

维护者测试环境为macOS和支持`plugin add`的Codex CLI；无需管理员权限或额外API key。源、缓存和一份备份建议预留约100 MB，安装通常需要几分钟。后续生图需要有原生图片能力的Codex账号、另行授权及宿主额度；新宿主兼容性尚未验证。

写入安装文件前，先在终端确认 Python 3 和 Codex 插件命令可用：

```bash
python3 --version
codex plugin add --help
```

第一条应显示 Python 3，第二条应显示 `plugin add` 帮助。若命令不存在或不支持该子命令，先停止并查看[兼容性说明](COMPATIBILITY.md)，不要继续 `--apply`，也不要手改 Codex 配置绕过检查。

### 1. 校验并解压

把 Plugin ZIP 与匹配的 sidecar 放在同一目录：

```bash
shasum -a 256 -c threadtruth-studio-1.0.0-beta.8.zip.sha256
unzip threadtruth-studio-1.0.0-beta.8.zip
cd threadtruth-studio-1.0.0-beta.8
```

若正式发布文件名不同，以实际文件名为准。校验失败或未得到唯一、预期的发行根目录时立即停止。

### 2. 预检、注册、启用

安装器默认 dry-run，并输出 JSON，其中包含源路径、personal marketplace 路径、版本与返回的 `selector`：

```bash
python3 install-local.py
python3 install-local.py --apply
```

`--apply` 把已校验发行包复制到**用户主目录 → `plugins` → `threadtruth-studio`**，并注册到系统隐式发现的 personal marketplace，同时保留无关条目。它**不会**启用 Plugin，也不会修改 Codex 的启用状态。

执行安装器打印的完整 `Next:` 命令。默认 marketplace 的示例是：

```bash
codex plugin add threadtruth-studio@personal --json
codex plugin list --marketplace personal --json
```

返回的 `selector` 已经是完整的 `plugin@marketplace`。若安装器返回的 marketplace 名称不是 `personal`，以其打印命令为准，并在 list 命令中替换名称。不要手改 JSON/TOML；默认 personal marketplace 不需要执行 `codex plugin marketplace add`。

在 JSON 的 `installed` 列表中找到 `pluginId` 与安装器返回 selector 相符的项（通常是 `threadtruth-studio@personal`），确认 `installed` 和 `enabled` 都是 `true`。不要用 `--available` 判断安装成功，因为它也会列出尚未安装的插件。这一步确认安装与启用，接下来的新任务识别才验证 Skill 是否真正可用。

### 3. 首次使用

新建一个 **Codex 任务**以加载 Skill。先上传服饰图，再原样输入：

```text
请用 $threadtruth-studio 识别并推荐风格，不要生图
```

预期返回服饰识别卡、主推与备选风格、完整 24 风格目录；不应生成图片，也没有授权任何生图费用。

首次使用成功应同时满足：已安装项处于启用状态，新任务能调用 `$threadtruth-studio`，并返回识别卡和风格目录。成功或失败均可提交[安装反馈表](https://github.com/denggui-ai/threadtruth-studio/issues/new?template=installation-feedback.yml)，填写实际安装版本；若尚未安装成功，填写 not installed 和尝试安装的版本。不要在公开 Issue 中附私图、凭据或完整日志。

### 安装排查

| 遇到的问题 | 下一步 |
|---|---|
| 校验失败，或解压后没有预期根目录 | 暂停安装。从同一个发行页重新下载有完整插件名称的 ZIP 和匹配校验文件，再校验、解压；不要改用源码 ZIP。 |
| 安装器提示已有安装 | 保留现有安装，按下方“升级与回滚”操作；先带 `--replace` 预检，再应用，并保留输出的备份。 |
| 找不到 Python 或不支持 `codex plugin add` | 不执行 `--apply`。查看[兼容性说明](COMPATIBILITY.md)，使所需命令可用后重新预检；不默认所有新宿主都兼容。 |
| 插件未出现、未启用，或没有识别结果 | 执行安装器打印的完整 `Next:` 命令，再用不带 `--available` 的列表检查对应 selector。新建任务、上传服饰图并使用上方显式提示；仍失败时通过反馈表提交宿主、版本与简短脱敏结果，不通过生图来重试。 |

### 升级与回滚

在单独解压且校验通过的新版本根目录做 dry-run 时也必须带 `--replace`，因为活动源已经存在。核对路径后应用，并执行安装器打印的完整 `Next:` 命令：

```bash
python3 install-local.py --replace
python3 install-local.py --apply --replace
codex plugin add threadtruth-studio@personal --json
```

`--replace` 会为活动源目录和已有 marketplace 配置创建 UTC 时间戳备份，并给安装后的 manifest 增加 UTC `+codex.*` cachebuster，因此安装后字节与原始 ZIP 有意不同。审计时同时记录归档 checksum 与安装版本。升级后新建任务。

若运行验证失败，使用应用升级时输出的 `source_backup` 路径恢复；不要用 marketplace 备份直接覆盖现有文件，因为它可能已有合法的新变更：

```bash
python3 install-local.py --source <输出的-source_backup-路径> --replace
python3 install-local.py --source <输出的-source_backup-路径> --apply --replace
codex plugin add threadtruth-studio@personal --json
```

如果 marketplace 不是 `personal`，仍以安装器打印的完整 `Next:` 命令为准；随后新建任务验证旧版本。移除启用状态使用 `codex plugin remove threadtruth-studio@personal --json`（或返回的非默认 selector）。启用状态、源目录、marketplace 条目和备份是不同层，默认不会一并删除。

### 三种渠道不是一回事

- **Personal Plugin source：**本页说明的已测试安装路径。
- **GitHub：**源码与 Release 下载渠道；仅 clone 不等于完成 Codex 注册和启用。
- **官方 marketplace：**本项目未宣称上架或获批。

另见[兼容性说明](COMPATIBILITY.md)。脱敏安装结果请提交到[安装反馈表](https://github.com/denggui-ai/threadtruth-studio/issues/new?template=installation-feedback.yml)；一般讨论请使用 [Discussions](https://github.com/denggui-ai/threadtruth-studio/discussions)。
