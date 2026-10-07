# 裁光 · Caiguang

**AI Fashion Studio · 服饰 AI 影棚**

**Current prerelease: beta.12.** Model-reference reuse and a compact conversation flow are included: one proposal, one confirmation, image-first review and single-image closeout. It displays “裁光 · Caiguang” in Codex and keeps `$threadtruth-studio`. Use the [version-matched trial guide](docs/BETA12-TRYOUT.md). Fresh-host testing and stable-release acceptance remain pending; older release assets stay unchanged.

[![裁光 · Caiguang — AI Fashion Studio。米色套装参考图与 AI 生成效果。](https://denggui-ai.github.io/threadtruth-studio/assets/brand/og-home.png)](https://denggui-ai.github.io/threadtruth-studio/)

**单件或整套服饰，生成六姿势 AI 模特图，24 种风格可选。**<br>Turn a garment or coordinated outfit into six-pose AI model portraits. Choose from 24 styles.

**[下载裁光插件 · Download Caiguang](https://github.com/denggui-ai/threadtruth-studio/releases/tag/v1.0.0-beta.12)**　·　**[开始安装 · Install](docs/INSTALL.md#english)**　·　**[查看成片 · See results](https://denggui-ai.github.io/threadtruth-studio/#reviewed-cases)**　·　**[探索 24 风格 · Explore styles](https://denggui-ai.github.io/threadtruth-studio/#style-highlights)**

[English guide](README.md) · [中文说明](README.zh-CN.md) · [产品首页 / Website](https://denggui-ai.github.io/threadtruth-studio/) · [能力清单与拓扑 / Capability topology](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/ARCHITECTURE.md) · [当前能力状态 / Capability status](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/CAPABILITY-STATUS.md)

When clear front/front-side photos are available but the back is missing, slot 6 is disclosed as stationary frontal standing; slots 1–5 remain, with six independent images. Accurate rear construction still requires a real rear photo.


[![Caiguang architecture and key workflows](https://raw.githubusercontent.com/denggui-ai/threadtruth-studio/main/docs/assets/architecture-overview.png)](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/ARCHITECTURE.md)


[Japanese-home workflow tutorial (中文)](docs/JAPANESE-HOME-TUTORIAL.md): materials, first-image approval, six standalone images and an honest case review. The tutorial identifies released and development behavior separately.

## One garment or a complete outfit, six poses

Upload a garment or coordinated outfit, choose **one of 24 styles**, and create **six independent AI model portraits** using the default pose set. Review the first image before continuing; later images use its identity reference for consistency within the set. This does not promise to reproduce a person in your input photo. A choice of 24 styles does not mean 24 sets in one request.

[Prepare your photos](docs/INPUT-GUIDE.md) · [Six poses and generation prompts](docs/CAPABILITIES.md#six-poses) · [Garment: 24 previews](docs/demo/style-previews/white-vest-24-v1/) · [Outfit: 24 previews](docs/demo/style-previews/beige-blazer-denim-outfit-24-v1/)

Both collections are historical direction previews: one six-panel sheet per style, not independent finals. [Six six-image styling cases](https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html) show 36 separate AI images: a floral dress, a sage-shirt home outfit, two styles of a contrast-trim T-shirt, an external Codex user’s black-jacket outfit, and our same-input Office Commute set. Each set discloses its review scope.

## Why create with Caiguang?

**Keep your real garment at the heart of every creative decision.**

- **Garment details you can review.** Review color, construction and styling before generation, then compare each result with your source photos. [See the six-pose cases](https://denggui-ai.github.io/threadtruth-studio/#reviewed-cases).
- **Explore more looks for one outfit.** Find a direction across 24 styles, from ecommerce studio to fashion editorial. [See one outfit in three styles](https://denggui-ai.github.io/threadtruth-studio/#outfit).
- **Try one image before a full set.** Start with a plan or prompts only. Approve one test image when ready, then decide whether to continue. [Start with recognition](https://denggui-ai.github.io/threadtruth-studio/#begin).

## What you can do

- **Identify the garment.** Read visible details from a single item, an outfit or multiple views.
- **Choose a direction.** Get recommendations or choose freely from all 24 styles.
- **Set the shoot.** Choose studio, location or hybrid, plus presentation and canvas. Alternate forms have limited public validation.
- **Choose the output.** Request one test, a labeled direction preview, six independent images, or prompts only.
- **Choose the route.** Use Codex by default or request a ChatGPT web handoff; automation needs host browser tools.
- **Review and refine.** Compare with the source, check dimensions, and authorize a specific retry when needed.

[Full capabilities, copyable prompts and verification scope →](docs/CAPABILITIES.md)

Install **裁光 · Caiguang** in **Codex**. The beta.12 prerelease displays **裁光 · Caiguang**; older beta.8 installations still display **ThreadTruth Studio**. Generate there by default, or explicitly choose the optional ChatGPT web handoff described below.

## Get started

**What you need:** macOS, Python 3, a terminal, and a Codex CLI that supports `codex plugin add`. This is the only tested setup; Windows, Linux, and fresh machines are unverified. The first recognition step generates no images. Generating images later needs a Codex account with native image generation, or a ChatGPT account with image access if you choose the web route.

1. Follow the [English installation guide](docs/INSTALL.md#english) to download the beta.12 Plugin ZIP and matching `.sha256`, check prerequisites, verify the archive, and enable the Plugin. Use the named Plugin download, not GitHub's automatic source-code ZIP.
2. Start a **new Codex task** and upload a real garment or coordinated-outfit photo you are authorized to use.
3. Ask for recognition and style recommendations:

```text
Use $threadtruth-studio to identify this garment and recommend styles. Do not generate images.
```

Expect a garment recognition card, a primary recommendation with alternatives, and the full 24-style catalogue. This first step does **not** authorize image generation. Confirm the style, composition, dimensions, and number of images before approving generation, which uses the selected account's image quota.

If recognition does not appear, follow [installation troubleshooting](docs/INSTALL.md#troubleshooting). Share a brief success or failure through the [installation feedback form](https://github.com/denggui-ai/threadtruth-studio/issues/new?template=installation-feedback.yml).

## Choose where to generate

| Route | How it works | What you need |
|---|---|---|
| **Codex · default** | Generate within Codex after approval; review the first image before continuing the set. | A Codex host with native image generation and available quota. |
| **ChatGPT web · explicitly selected** | Codex prepares numbered references and prompts. Transfer them manually, or authorize Codex to operate a supported browser. | A ChatGPT account with image access and quota. Automatic execution also requires host browser tools for uploading and downloading original files. |

Install 裁光 · Caiguang in **Codex**. The ChatGPT route uses the web handoff described in the [tutorial (中文)](docs/CHATGPT-WEB-TUTORIAL.md); installing this Plugin does not install browser tools. Uploading references to ChatGPT requires permission. Failed or uncertain requests are checked before any separately authorized retry, and used attempts remain recorded. [Web workflow details (中文)](docs/CHATGPT-WEB.md).

## Examples and what they demonstrate

**Six sets, 36 separate images.** [See all images and source notes](https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html). Dress and home-outfit visuals were accepted; the T-shirt sets retain fine-detail and action review. These AI-model images support styling previews, not personal identity, size or fit guarantees.

**Product references → AI scene styling.** The comparison shows the actual primary shirt and pants references alongside a home-scene result. The pants are displayed as a crop; additional construction and identity references were used. An external Codex user also completed six images and reported satisfaction; the version used was not recorded.

<a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#green-shirt-home"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/green-shirt-home/before-after.jpg" alt="Product references and AI home-scene result / 商品参考与 AI 家居成片" width="480"></a>

[See the home Before / After, all six originals and source notes](https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#green-shirt-home)

**One outfit input → six Office Commute images.** The same authorized input also appears in the external trial. Compare two presentation directions, rather than versions; the external version is unknown. Slot 6 uses stationary front standing because no real rear photo was supplied. Fine garment details remain subject to review.

| Actual input | AI · Office Commute |
|---|---|
| <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#black-jacket-office"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/black-jacket-office/input.jpg" alt="Actual authorized outfit input" width="240"></a> | <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#black-jacket-office"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/black-jacket-office/look-1.png" alt="AI-generated Office Commute jacket outfit" width="240"></a> |

[See both directions, all six new images and review scope](https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#black-jacket-office) · [Download case sharing materials](https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/black-jacket-office/share/caiguang-black-jacket-share.zip)

**Same jacket, different mood.** [Compare the French and American single-image tests](https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#black-jacket-style-comparison): the same outfit, AI identity and first pose. French v3's gentler expression was visually accepted; American retains a restrained urban mood with acceptance pending. One test image per style, with fine garment review still open.

| | | | | |
|---|---|---|---|---|
| <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#black-jacket-office"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/black-jacket-office/look-1.png" alt="Office Commute — AI-generated" width="150"></a><br>Office Commute · same-input comparison | <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#red-floral-french"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/red-floral-french/look-1.png" alt="Floral dress — AI-generated" width="150"></a><br>Floral dress | <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#green-shirt-home"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/green-shirt-home/look-1.png" alt="Home outfit — AI-generated" width="150"></a><br>Home outfit | <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#trim-tee-american"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/trim-tee-american/look-1.png" alt="American Street — AI-generated" width="150"></a><br>American Street | <a href="https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html#trim-tee-japanese"><img src="https://denggui-ai.github.io/threadtruth-studio/assets/reviewed-cases/trim-tee-japanese/look-1.png" alt="Japanese Lifestyle — AI-generated" width="150"></a><br>Japanese Lifestyle |

[Case notes and media terms](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/SHOWCASE-CASES.md).

[![A real white-vest source photo alongside six independent AI-generated Korean Cold Editorial portraits](docs/demo/primary-cases/white-hooded-puffer-vest-korean-cold/hero.jpg)](docs/demo/primary-cases/white-hooded-puffer-vest-korean-cold/README.md)

**Four source photos → six independent AI portraits.** This reviewed historical case is separate from the paired gallery and was not generated under beta.8. [Explore the complete case and its media terms](docs/demo/primary-cases/white-hooded-puffer-vest-korean-cold/README.md).

The **24-style paired gallery** compares Codex and ChatGPT web results, with source credits, rights disclosures, and per-case reviews. These are AI-generated research comparisons; they do not establish a model ranking or permission to reuse every image. [Read the gallery's source and rights records](https://denggui-ai.github.io/threadtruth-studio/rights.json).

| Collection | Published scope | What it establishes |
|---|---|---|
| [New styling cases](https://denggui-ai.github.io/threadtruth-studio/reviewed-cases.html) | **6 sets × 6 separate images = 36 images** | Visual acceptance and remaining review items are recorded separately; excluded from the frozen historical style index. |
| [Paired comparison gallery](https://denggui-ai.github.io/threadtruth-studio/compare.html) | **24 styles × 2 routes = 48 images** | Same-input comparisons with reviews and rights disclosures. These are not 24 complete six-image sets or verification of every style under beta.8. |
| [White-vest complete case](docs/demo/primary-cases/white-hooded-puffer-vest-korean-cold/README.md) | **1 style × 6 independent images** | One reviewed complete case; the frozen historical primary-case style index is **1/24**. |
| Historical direction previews | **2 collections × 24 styles** | One six-pose preview sheet per style, with layout checks and maintainer acceptance. The white-vest beta.3 and outfit beta.4 collections retain their original evidence. |

<details>
<summary>Explore the historical single-garment and complete-outfit previews</summary>

| Real coordinated-outfit source | AI-generated six-pose direction preview |
|---|---|
| <img src="docs/demo/preview-sources/beige-blazer-denim-outfit/source.jpg" alt="Real source photo of the coordinated beige-blazer outfit" width="300"> | <img src="docs/demo/style-previews/beige-blazer-denim-outfit-24-v1/ecommerce-studio-display.jpg" alt="AI-generated six-pose preview of the same beige-blazer outfit" width="700"> |

**coordinated outfit · 24 styles** — the beige blazer, white top, dark denim, olive tote, and brown loafers form one locked outfit. This is a single preview sheet. [Browse all 24 outfit sheets](docs/demo/style-previews/beige-blazer-denim-outfit-24-v1/) (GitHub lists the image files; the folder's `index.html` is a gallery page for a downloaded copy) · [Media rights](docs/demo/RIGHTS.md).

**single garment · 24 styles** — the thumbnails below show the frozen white-vest collection. Each opens a larger six-pose sheet. [Style evidence index](docs/demo/STYLES.md) · [Historical work register](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/WORK-STATUS.md).

<!-- STYLE_PREVIEWS:START -->

| | | | |
|---|---|---|---|
| <a href="docs/demo/style-previews/white-vest-24-v1/american-street-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/american-street-thumb.jpg" alt="American Street — six-pose layout preview, not finals" width="180"></a><br>American Street | <a href="docs/demo/style-previews/white-vest-24-v1/athleisure-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/athleisure-thumb.jpg" alt="Athleisure — six-pose layout preview, not finals" width="180"></a><br>Athleisure | <a href="docs/demo/style-previews/white-vest-24-v1/balletcore-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/balletcore-thumb.jpg" alt="Balletcore — six-pose layout preview, not finals" width="180"></a><br>Balletcore | <a href="docs/demo/style-previews/white-vest-24-v1/british-heritage-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/british-heritage-thumb.jpg" alt="British Heritage — six-pose layout preview, not finals" width="180"></a><br>British Heritage |
| <a href="docs/demo/style-previews/white-vest-24-v1/cityboy-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/cityboy-thumb.jpg" alt="Cityboy — six-pose layout preview, not finals" width="180"></a><br>Cityboy | <a href="docs/demo/style-previews/white-vest-24-v1/clean-fit-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/clean-fit-thumb.jpg" alt="Clean Fit — six-pose layout preview, not finals" width="180"></a><br>Clean Fit | <a href="docs/demo/style-previews/white-vest-24-v1/coquette-ladylike-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/coquette-ladylike-thumb.jpg" alt="Coquette Ladylike — six-pose layout preview, not finals" width="180"></a><br>Coquette Ladylike | <a href="docs/demo/style-previews/white-vest-24-v1/ecommerce-studio-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/ecommerce-studio-thumb.jpg" alt="E-commerce Studio — six-pose layout preview, not finals" width="180"></a><br>E-commerce Studio |
| <a href="docs/demo/style-previews/white-vest-24-v1/french-effortless-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/french-effortless-thumb.jpg" alt="French Effortless — six-pose layout preview, not finals" width="180"></a><br>French Effortless | <a href="docs/demo/style-previews/white-vest-24-v1/gorpcore-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/gorpcore-thumb.jpg" alt="Gorpcore — six-pose layout preview, not finals" width="180"></a><br>Gorpcore | <a href="docs/demo/style-previews/white-vest-24-v1/guochao-street-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/guochao-street-thumb.jpg" alt="Guochao Street — six-pose layout preview, not finals" width="180"></a><br>Guochao Street | <a href="docs/demo/style-previews/white-vest-24-v1/italian-luxe-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/italian-luxe-thumb.jpg" alt="Italian Luxe — six-pose layout preview, not finals" width="180"></a><br>Italian Luxe |
| <a href="docs/demo/style-previews/white-vest-24-v1/japanese-lifestyle-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/japanese-lifestyle-thumb.jpg" alt="Japanese Lifestyle — six-pose layout preview, not finals" width="180"></a><br>Japanese Lifestyle | <a href="docs/demo/style-previews/white-vest-24-v1/korean-cold-editorial-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/korean-cold-editorial-thumb.jpg" alt="Korean Cold Editorial — six-pose layout preview, not finals" width="180"></a><br>Korean Cold Editorial | <a href="docs/demo/style-previews/white-vest-24-v1/korean-menswear-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/korean-menswear-thumb.jpg" alt="Korean Menswear — six-pose layout preview, not finals" width="180"></a><br>Korean Menswear | <a href="docs/demo/style-previews/white-vest-24-v1/neo-chinese-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/neo-chinese-thumb.jpg" alt="Neo Chinese — six-pose layout preview, not finals" width="180"></a><br>Neo Chinese |
| <a href="docs/demo/style-previews/white-vest-24-v1/nordic-minimal-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/nordic-minimal-thumb.jpg" alt="Nordic Minimal — six-pose layout preview, not finals" width="180"></a><br>Nordic Minimal | <a href="docs/demo/style-previews/white-vest-24-v1/office-commute-women-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/office-commute-women-thumb.jpg" alt="Office Commute Women — six-pose layout preview, not finals" width="180"></a><br>Office Commute Women | <a href="docs/demo/style-previews/white-vest-24-v1/old-money-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/old-money-thumb.jpg" alt="Old Money — six-pose layout preview, not finals" width="180"></a><br>Old Money | <a href="docs/demo/style-previews/white-vest-24-v1/preppy-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/preppy-thumb.jpg" alt="Preppy — six-pose layout preview, not finals" width="180"></a><br>Preppy |
| <a href="docs/demo/style-previews/white-vest-24-v1/quiet-luxury-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/quiet-luxury-thumb.jpg" alt="Quiet Luxury — six-pose layout preview, not finals" width="180"></a><br>Quiet Luxury | <a href="docs/demo/style-previews/white-vest-24-v1/resort-vacation-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/resort-vacation-thumb.jpg" alt="Resort Vacation — six-pose layout preview, not finals" width="180"></a><br>Resort Vacation | <a href="docs/demo/style-previews/white-vest-24-v1/workwear-vintage-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/workwear-vintage-thumb.jpg" alt="Workwear Vintage — six-pose layout preview, not finals" width="180"></a><br>Workwear Vintage | <a href="docs/demo/style-previews/white-vest-24-v1/y2k-millennium-display.jpg"><img src="docs/demo/style-previews/white-vest-24-v1/y2k-millennium-thumb.jpg" alt="Y2K Millennium — six-pose layout preview, not finals" width="180"></a><br>Y2K Millennium |

<!-- STYLE_PREVIEWS:END -->

These historical previews retain their source records, reviews, and hashes. They do not prove universal garment or outfit coverage or establish current-runtime visual quality, additional complete cases, or non-maintainer adoption.

</details>

## Scope and limits

裁光 · Caiguang is independent and community-maintained, not an OpenAI product or endorsement. Installation and enablement have been verified on the maintainer's macOS machine; a fresh non-maintainer environment remains unverified. See [compatibility and verification scope](docs/COMPATIBILITY.md).

- **Source details guide the output.** Color, material appearance, silhouette, construction, pattern, and logo placement come from the source. For an outfit, this also includes layering, proportions, shoes, bags, and accessories. Check the generated result against your source; exact small text, logos, and fit are not guaranteed.
- **Human review remains part of delivery.** This workflow supports apparel imagery, not identity-preserving try-on on a supplied person, CAD fit simulation, non-apparel products, text-only concepts, API integration, or unattended commercial delivery. It does not guarantee platform approval or sales results.
- **Style names describe visual direction.** Gendered or culturally named styles do not infer a person's identity, ethnicity, nationality, body, or gender.
- **Use authorized material and keep rights separate.** Images are AI-generated and need applicable labeling. Gallery publication does not mean all third-party rights are cleared; follow the per-case disclosures. Apache-2.0 covers code and documentation, not demo media.
- **Generation depends on the chosen host.** The Plugin adds no API-key flow, third-party generation service, MCP server, or telemetry. Without the required tools, recognition and prompt preparation can continue; generation pauses or you can explicitly choose the web handoff route.

## Documentation and support

[Install, upgrade, and rollback](docs/INSTALL.md) · [Compatibility](docs/COMPATIBILITY.md) · [Offline guide](USER-GUIDE.html) (bundled in the Plugin ZIP; open it locally, since GitHub shows its HTML source) · [Changelog](https://github.com/denggui-ai/threadtruth-studio/blob/main/CHANGELOG.md) · [Beta progress](docs/BETA.md)

**Current prerelease: beta.12.** It includes optional casting goals, aesthetic-reference translation and first-image casting QA, with garment-first priorities. The first reply stays with input checks even for prompt-only requests. ChatGPT web handoff and controlled retries remain available. Earlier releases and their galleries remain historical records; use each old archive's bundled guide when installing that version. Beta exit targets and remaining validation are tracked in the [Beta register](docs/BETA.md).

Share sanitized installation results through the [feedback form](https://github.com/denggui-ai/threadtruth-studio/issues/new?template=installation-feedback.yml). Report bugs in [Issues](https://github.com/denggui-ai/threadtruth-studio/issues) and ask questions in [Discussions](https://github.com/denggui-ai/threadtruth-studio/discussions). Keep private garments, customer data, credentials, and full logs out of public posts. Maintainer: DENGGUI · WeChat: `Lvmusic0930`.

<details>
<summary>Development and project records</summary>

```bash
python3 -m unittest discover -s tests -v
python3 tools/pack-lint.py --strict skills/threadtruth-studio/references/styles/*.pack.yaml
python3 tools/trigger-eval.py
python3 tools/build-release.py
```

Runtime lives under `skills/threadtruth-studio/`; tests, evals, release tooling, and evidence stay outside it. See [Contributing](CONTRIBUTING.md), [Security](SECURITY.md), [Migration](MIGRATION.md), and [Provenance](PROVENANCE.md). Project Beta targets are not OpenAI admission rules; application details are kept in [Codex for Open Source](https://github.com/denggui-ai/threadtruth-studio/blob/main/docs/CODEX-FOR-OSS.md).

</details>
