# Brand share-cover sources

These two 1200×630 HTML compositions are development sources for the homepage and comparison-page share covers. They use the same local licensed fonts and outlined Chinese wordmark as the site. The homepage composition uses only the already authorized white-vest source and two historical AI results; the comparison cover is typographic. Do not replace them with third-party research-gallery images.

## Update sequence

1. Use an isolated Python environment with `requirements-dev.txt`. Fetch the pinned official font sources to a temporary directory with `tools/brand_assets.py fetch --source-dir <font-cache> --revision <revision-from-brand-assets.json>`; the deployed source record contains the revision, URLs and hashes.
2. After changing site or cover text, run `tools/brand_assets.py build --source-dir <font-cache>` to rebuild the local font subsets and glyph outlines. This deliberately **does not refresh the manifest** or accept existing cover renders. The old manifest should continue to report drift until the dependent outputs have been reviewed.
3. Copy these two HTML files into the gallery root as `_og-home.html` and `_og-compare.html` temporarily. Serve the gallery on localhost. Open each temporary page in a browser at exactly **1200×630 CSS pixels**, wait for local fonts and images to load, and inspect the full composition. Capture the viewport into `assets/brand/og-home.png` and `assets/brand/og-compare.png`. The output must be actual PNG encoding, not JPEG bytes with a PNG filename; re-encode the capture if necessary without changing its pixel content.
4. Remove only the two temporary `_og-*.html` files. They are intentionally excluded from the deployment allowlist. Run `tools/brand_assets.py manifest --source-dir <font-cache>` **after** the new cover render has been inspected. This explicit command records the final outputs and source-template hashes.
5. Run `python tools/check_showcase.py --gallery gallery/style24-comparison-20260929 --repo-root .` and the brand/showcase tests before committing.

The manifest records provenance and detects unacknowledged drift; it cannot prove that an explicitly accepted screenshot matches a template. Browser inspection remains part of the update. Keep source photos, historical results and rights records unchanged. Neither the brand build nor cover rendering generates a new fashion image.
