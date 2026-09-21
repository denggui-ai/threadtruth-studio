# Compatibility / 兼容性

| Surface / 环境 | Evidence / 证据 | Boundary / 边界 |
|---|---|---|
| macOS | `26.6.2` maintainer host | Local verification environment / 本机验证环境 |
| Codex CLI | `codex-cli 0.155.1` | beta.5 local registration, enablement and version verification recorded separately / beta.5本机注册、启用与版本核验另见记录 |
| Local beta.5 / 本地beta.5 | Shared head/body relations and ecommerce pilot; source, package and installer checks | [Local verification record / 本地验证](verification/2026-09-21-beta.5-local.md); no GitHub beta.5 release / 未发布GitHub beta.5 |
| Public beta.4 / 公开beta.4 | Two accepted historical 24-style preview galleries | Preserved byte-for-byte; not current-runtime visual evidence / 逐字节保留，不算当前运行时视觉证据 |
| Codex desktop / 桌面应用 | Build unavailable / build不可用 | Open a new task to load the upgraded Skill; current task does not reload / 升级后需新建任务，当前任务不热更新 |
| Clean non-maintainer environment / 非维护者干净环境 | No retained successful record / 无留存成功记录 | Pending / 待验证 |
| Official Plugin marketplace / 官方市场 | No listing or acceptance evidence / 无上架或获批证据 | Not available / 不可用 |

The beta.5 local delivery covers deterministic source/runtime validation, immutable-gallery integrity, allowlist packaging, clean extraction, installer tests and the explicitly recorded maintainer-machine cutover. It does not establish new-task trigger behavior, a fresh-host lifecycle, or visual quality across 24 styles. The earlier beta.1 lifecycle and beta.3/beta.4 public artifact checks remain historical evidence. Stable v1.0.0 and public Beta exit criteria are separate pending work.

beta.5本地交付覆盖源码／运行时静态检查、历史图库完整性、白名单打包、干净解压、安装器回归及明确记录的维护者本机升级。它不证明新任务触发、外部干净环境完整生命周期或24风格视觉质量。beta.1生命周期及beta.3／beta.4公开制品核验保留为历史证据；稳定版v1.0.0和公开Beta退出条件仍是后续工作。

Installation, backups and rollback: [INSTALL.md](INSTALL.md). Successful `plugin add` and installed-byte verification establish local enablement, not a paid image-generation test. / 安装、备份和回滚见[安装指南](INSTALL.md)。成功启用与安装字节核验只证明本机安装，不代表付费生图实测。
