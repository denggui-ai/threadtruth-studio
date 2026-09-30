# 首页选图与文案澄清

用户已批准本轮审查建议并要求执行。此前中性页面设计保持，继续复用 publication-showcase 工作树。

## Scope

- 首屏采用米色完整套装参考图与意式奢华 A 样例，清楚标注输入和 AI 输出；增加浏览 24 风格入口与简短能力摘要。
- 首屏之后增加三个简短能力分组：可设置内容、可交付产物、已有公开案例；五种展示形式区分指令定义与公开验证。
- 修正逐缝线承诺、搭配源图范围、三种方向、参考摄影署名、双端名称、正面照片开始识别等中英文表达。
- 24 风格的不同源素材与选择范围说明前置，白马甲完整六图仍保留。
- 首页分享封面同步首图与输入输出标签，并更新资产来源清单与本地字体。
- 不新增生图，不改变插件运行时、原始图片或媒体授权，不推送、合并或部署。

### Task 1: Implement and verify the approved presentation

1. Update homepage markup and responsive CSS; synchronize both languages and preserve all existing anchors and interactions.
2. Update homepage share template and its declared source assets; rebuild local fonts and render covers.
3. Run existing Python suite, showcase validator, browser checks at five widths in both languages and diff whitespace check. Review desktop/mobile screenshots and cover visually.
4. Obtain one fresh-context review, resolve actionable findings, document outcomes and commit locally.

Expected: existing suites and asset validator pass; no horizontal overflow; all 24 styles visible; six-image case preserved; hero opens the matching original and provenance; claims match CAPABILITIES.md.

No new implementation-mirroring tests for this reversible content/layout change. Existing interaction and asset checks supply regression coverage; this follows the session's higher-priority testing instruction.

## Review Focus

Check that hero reference, output and source links match; no missing translations or unsupported capability claims; source-photographer attribution is unambiguous; local share-cover provenance matches rendered assets; all prior navigation and interactions remain available.
