# Shopify image export guide

[Português (Brasil)](docs/README-ptbr.md)

A standard for exporting and validating images for Shopify stores without losing sharpness or color, with a good weight for SEO and performance.

## What is here

| File | For whom | What it is |
| --- | --- | --- |
| [`docs/designers-guide.md`](docs/designers-guide.md) | Designers (Photoshop) | 2× sizing, sRGB conversion, Save for Web settings, file naming and a delivery checklist |
| [`shopify-image-optimizer/`](shopify-image-optimizer/) | Developers | A skill with the script that audits and optimizes delivered images |

Portuguese versions: [`docs/README-ptbr.md`](docs/README-ptbr.md) and [`docs/designers-guide-ptbr.md`](docs/designers-guide-ptbr.md).

## The rule in one line

Export at **2× the displayed width**, in **sRGB**, as **JPEG quality 85** (never below 80), and control the weight **through quality only**, never through the dimensions.

## Using the script

Requirements: Python 3 and Pillow (`pip install Pillow`).

Audit what the designer delivered (writes nothing):

```bash
python3 shopify-image-optimizer/scripts/optimize.py designer-folder --check --preset product
```

Optimize without losing resolution (originals are never changed):

```bash
python3 shopify-image-optimizer/scripts/optimize.py designer-folder -o optimized --preset product
```

Presets: `product`, `collection`, `banner`, `blog`. Use `--display-width` to give the real width of the slot in the theme and `--target-kb` to change the target weight. All options are in [`shopify-image-optimizer/SKILL.md`](shopify-image-optimizer/SKILL.md) or in `--help`.

The recommended flow is to run `--check` first and optimize only what comes back as FIX, preferably from the designer's original file, because each JPEG recompression loses a little quality. The CSV reports use `;` as the delimiter, so they open directly in Excel in pt-BR locales.

## Things to keep in mind

- The presets (2× sizes and target weights) are team defaults, not Shopify limits. Adjust them per client and per theme.
- Photoshop's quality scale is not the same as the one estimated by `--check`. Check each designer's first batch and adjust if the estimated quality comes back below 80.
- The script was tested with synthetic images (photos, CMYK with a profile, transparent PNG, repeated names). Validate it with real client files before using it on a batch.
