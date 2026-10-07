# 30-day Beta evidence register

Status: **active**.

<a id="current-status"></a>
## Current status / 当前状态 — 2026-10-02

| Track / 项目 | Recorded state / 已记录状态 | Next evidence / 下一项证据 |
|---|---|---|
| Public package / 公开安装包 | [v1.0.0-beta.12](https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.12); older assets remain unchanged / 旧版资产不变 | Version-matched trial; stable release and fresh-host validation remain separate / 版本匹配试用；稳定版与新宿主验证仍待完成 |
| beta.11 source-coverage fix / 缺背面修正 | Static/default-preview compatibility and six text scenarios passed; only slot 6 changes with missing rear sources / 静态、默认预览兼容及六个文字场景通过，缺背面仅替代第六张 | [Trial guide](BETA11-TRYOUT.md); native rendering in the upgraded version still requires real-use verification / 升级版原生生图仍需真实使用验证 |
| beta.10 verification / 验证 | Scoped explicit/default casting and first-reply text rechecks passed; one authorized native correction closed visible cuff/placket failures, originals retained / 限定选角及首回复复测通过，经授权修图关闭可见袖口与门襟失败，保留原始证据 | [Trial guide](BETA10-TRYOUT.md); no installed-plugin discovery, commercial-ready image or new six-image workflow claim / 不声称已安装插件发现、图可商用或新增六图流程 |
| beta.9 evidence / beta.9验证 | beta.9; maintainer installed-CLI text checks retained 8/8 passing final replies, including three original-prompt repetitions / 留存本机已安装插件文字复测，最终8/8通过 | [Version-matched trial](BETA9-TRYOUT.md); desktop display and non-maintainer fresh-host validation remain pending / 桌面显示与非维护者新环境验证待完成 |
| Issue #1 | Scoped maintainer correction is recorded; the public issue remains open / 本机限定范围修复已记录，公开Issue仍未关闭 | Fresh-host reproduction and fix distribution / 新环境复测与修复分发 |
| External adoption / 外部采用 | One anonymous external Codex trial reported six images and satisfaction; qualifying installation count remains unverified / 已记录一则匿名外部Codex六图满意反馈，合格安装人数仍未核实 | [Trial record](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/feedback/2026-10-01-external-codex-outfit.md); version, OS and installation/discovery observations are unknown / 版本、系统与安装发现过程未知 |
| Complete cases / 完整主案例 | One historical primary case; four styling sets and one external six-image example published separately / 历史主案例1组，另公开穿搭4组及外部六图示例1组 | External satisfaction is recorded; visible button variation and hidden garment details remain separate from complete commercial QA / 已记录外部满意反馈，扣位差异与隐藏细节仍需独立核对 |
| External lifecycle and feedback patch / 外部生命周期与反馈补丁 | Neither has a qualifying completed record / 均无合格完成记录 | Real participant observations; local fixtures cannot substitute / 需真实参与者观察，本地夹具不能替代 |

Read [compatibility](COMPATIBILITY.md) for the scope of each observation. The [dated work ledger (online)](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/WORK-STATUS.md) and earlier verification reports are historical records, not current instructions. Publication and candidate validation do not mean stable-release readiness, external adoption or image-quality acceptance. / 各项观察范围见兼容性说明；历史台账与旧报告保留当时事实。发布与候选验证不等于稳定版就绪、外部采用或画质验收。

The Beta clock began when [`v1.0.0-beta.1`](https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.1) was published at **2026-09-13T04:59:28Z** (Asia/Shanghai: **2026-09-13 12:59:28**). The 30-day minimum reaches **2026-10-13T04:59:28Z**; elapsed time alone does not satisfy the exit criteria.

Publication baseline: one maintainer-owned authorized complete workflow, one auxiliary CC0 rights case, one of 24 styles with final-image evidence, and zero qualifying non-maintainer installations. Beta.3 added the white-vest 24-style preview collection; beta.4 adds the coordinated-outfit 24-style preview collection. Neither adds a complete workflow.

## Maintainer preflight — 2026-09-12

The public repository and required CI are active. On the maintainer machine, `1.0.0-beta.1` completed install, discovery, uninstall, reinstall, cache-buster upgrade, legacy rollback, and final restoration. Explicit invocation, substantive implicit discovery, and non-apparel isolation passed. A minimal implicit missing-image request may skip Skill loading; this medium-severity limitation is tracked in [Issue #1](https://github.com/denggui-ai/threadtruth-studio/issues/1).

This preflight is not a non-maintainer installation, a real workflow case, or the start of the 30-day Beta clock.

Institution-sourced CC0 auxiliary cases are also excluded from the installation and complete-case thresholds. They demonstrate reproducible rights handling only; the maintainer-owned publication-authorized main case remains a separate prerequisite.

## Exit criteria

These are the project's own evidence targets, not fixed OpenAI admission requirements. Patch releases do not restart the clock. Admission remains an external decision.

- At least five non-maintainer installations.
- At least three complete, authorized real workflows.
- At least one patch release driven by external feedback.
- At least one clean-environment install, discovery, upgrade, uninstall, and rollback validation.
- No open high-severity issues.
- Stable `v1.0.0` published.

## Privacy-preserving records

Do not add runtime telemetry. For each opt-in tester, record a public handle or pseudonymous ID, environment class, version, install outcome, workflow outcome, linked Issue/Discussion if any, consent to publish the record, and date. Do not store email, customer content, raw private prompts, cookies, tokens, or full logs.

## Register

| ID | Non-maintainer | Host / version / OS | Plugin version | Install / discovery / recognition | Complete case | Feedback link | Publish consent | Date |
|---|---:|---|---|---|---|---|---|---|

No qualifying installation record has been added yet. One publication-authorized anonymous external trial is recorded below; its unknown installation and version fields prevent counting it as a verified fresh-host installation or beta.10-specific regression.

## Reported external trial — 2026-10-01

[Anonymous Codex outfit trial](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/feedback/2026-10-01-external-codex-outfit.md): the maintainer reports a non-maintainer used the skill in Codex, generated six images and was satisfied. All six forwarded PNGs are distinct and 1024×1536. Permission to publish the outfit input, six results and sanitized feedback was confirmed on 2026-10-01. [View the external example](https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#external-black-leather).

Plugin version, OS, installation/discovery observations, exact prompts and actual generation-call count are unknown. The record demonstrates reported external use and satisfaction, not verified installation lifecycle, attribution to beta.10, or full commercial QA. The private chat screenshots are not published.

已记录外部试用与满意反馈；与合格安装人数、版本专项验证及商用逐项验收分开统计。

## Opt-in feedback and local metrics

Use the [installation feedback form](https://github.com/denggui-ai/threadtruth-studio/issues/new?template=installation-feedback.yml). Issues and Discussions are public even without evidence consent; consent controls whether a sanitized record is counted in this register. Do not submit customer media, private prompts, email, tokens, or full logs. A nickname/public handle is sufficient. Count a consenting non-maintainer once, regardless of repeated reports or versions; record failed discovery/recognition separately instead of treating a download as a working installation.

Maintainers can run `python3 tools/beta-metrics.py` from the development checkout using an already authenticated GitHub CLI. This makes read-only GitHub requests and writes summary snapshots only to ignored `.threadtruth/beta-metrics/`. It never publishes or adds runtime telemetry. Optional `--install-register` accepts a local JSON list with `public_id`, `host`, `host_version`, `plugin_version`, `date`, boolean `non_maintainer` / `public_consent`, and `install` / `discovery` / `recognition` results (`pass`, `fail`, `not-tested`). Counts are deduplicated case-insensitively; raw identities are not copied into snapshots. Cross-handle duplicates require maintainer review.

Plugin ZIP, original media ZIP, checksum and other downloads are recorded separately. Traffic is a UTC rolling 14-day snapshot; overlapping weeks must never be added together. Unavailable/forbidden data is marked unavailable, not zero. Only reviewed aggregates may be added to this public register. Retain local summaries through the Beta review; inspect and explicitly delete selected dated snapshots when no longer needed.

Two preview targets are published: beta.3 retains the frozen white-vest 24-style collection, and beta.4 adds the coordinated-outfit 24-style collection. Each is 24/24 machine-layout checked, maintainer accepted and publicly included. They remain six-pose direction previews, never satisfy the three-complete-workflow target, and do not change the Beta clock. See the [total task register and schedule](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/WORK-STATUS.md).
