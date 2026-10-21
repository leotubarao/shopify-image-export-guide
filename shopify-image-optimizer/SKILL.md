---
name: shopify-image-optimizer
description: Audits and optimizes images for Shopify without losing resolution: checks 2x size, sRGB, weight and file names, then compresses by quality only. Use before uploading images to a store.
---

# Shopify image optimizer

Use this skill to compress, optimize, resize or validate product, collection, banner or blog images (JPG, PNG, WebP, TIFF, PSD) before they go to Shopify, when images look soft or have off colors on the site, or when files delivered by designers must be checked against the standard (2x size, sRGB, weight, SEO file name).

Goal: light images (SEO and performance) **without** the loss of sharpness and color that happens when files go to the site outside the standard.

## Why images lose quality in the store

1. **Too few pixels.** Phones and 4K monitors show images with twice the pixels. A file exported at 1x (for example 1200 px for a 1200 px slot) looks soft. Rule: export at **2x** the displayed width.
2. **Wrong color profile.** Shopify strips the color profile when it displays the image. A file in Adobe RGB, Display P3 or CMYK comes out dull or shifted. The file must be **converted to sRGB**.
3. **Too much, or repeated, compression.** A JPEG exported at low quality, or recompressed several times, shows blur and blocks. Shopify does not compress on upload, but the image may be compressed when served through the theme and converted to WebP/AVIF. The better the source file, the better the result.

This skill addresses all three: it checks/converts to sRGB, respects 2x, and reduces weight by changing **only compression quality**, inside a safe range.

## Workflow

1. **Find the slot.** Ask (or infer from context) where the image goes: product, collection, banner/hero or blog. If you know the width it appears at in the theme (CSS px), use `--display-width`. Otherwise use the preset.
2. **Audit first** (writes nothing, does not recompress):
   ```bash
   python3 scripts/optimize.py FOLDER_OR_FILES --check --preset product
   ```
   Shows, per file: format, dimensions, weight, color profile, estimated JPEG quality and name. Status `OK` or `FIX` with the reason.
3. **Optimize only what needs it**, preferably from the designer's original/master file (not from an already compressed JPEG):
   ```bash
   python3 scripts/optimize.py FOLDER_OR_FILES -o ./optimized --preset product
   ```
4. **Read the report** in the terminal and in `optimized/report.csv`. Tell the user: how many images, weight before/after, and **every warning**.
5. Deliver the files in `optimized/`. Originals are never changed.

If Pillow is missing: `pip install Pillow` (add `--break-system-packages` on managed Python installs).

## Presets

| Preset | Long side (2x) | Minimum accepted by `--check` | Target weight |
|---|---|---|---|
| `product` | 2400 px | 2048 px | 500 KB |
| `collection` | 2000 px | 1600 px | 400 KB |
| `banner` | 3200 px | 2400 px | 900 KB |
| `blog` | 2400 px | 1600 px | 500 KB |

These are starting goals. Adjust with `--max-side`, `--target-kb` or `--display-width` for each client's theme. Shopify limits: 20 MB and 20 megapixels per image; for a square product image, 2048 x 2048 px usually displays best.

## What the script does (and does not do)

- **Never upscales.** A small original becomes a warning, not an enlargement.
- **Does not shrink dimensions** below 2x unless the user asks for `--allow-downscale` (with a floor set by `--floor-side`, default 2048).
- **Quality:** binary search between `--q-max 90` and `--q-min 80`; keeps the highest quality that fits the target weight. If even the minimum quality does not fit, it keeps the dimensions and **warns** (it does not silently damage the image).
- **Color:** converts to sRGB (including CMYK with a profile, Adobe RGB and P3). CMYK without a profile triggers a warning because the conversion is approximate.
- **JPEG** is progressive, with 4:4:4 chroma subsampling by default (labels, packaging text and edges stay sharp; use `--chroma 420` if you need smaller files).
- **Transparency:** keeps PNG; if it exceeds the weight target, converts to WebP with transparency. Photos without transparency become JPEG.
- **Metadata** (EXIF, GPS, thumbnails) is removed.
- **File names** become SEO slugs (`Sérum Vitamina C - frente.png` → `serum-vitamina-c-frente.jpg`). Use `--no-slug` to keep the name. Repeated names get `-2`, `-3`.
- **Fidelity:** computes PSNR against the already resized original. Above ~40 dB is imperceptible; below 38 dB the script warns.

## Rules when using it

- Run `--check` before optimizing. If a file is already `OK`, **do not recompress it** (each recompression loses a little quality).
- If `--check` shows an estimated quality below 80, the problem came from the designer: ask for a new export from the original instead of trying to "fix" the JPEG.
- Never promise weight savings without running it; report the real numbers from the report.
- Product images (skincare, pharma, labels with small text): keep `--chroma 444` and do not lower `--q-min` below 80.
- Do not upload anything to Shopify or delete originals unless the user asks.

## Options

```
--check              audit only
-o, --out            output folder (default ./optimized)
--preset             product | collection | banner | blog
--display-width W    width of the slot in the theme (CSS px); target = 2x
--max-side N         long side in px
--target-kb N        target weight in KB
--q-max / --q-min    quality range (90 / 80)
--format             auto | jpeg | webp | png
--chroma             444 (default) | 420
--allow-downscale    allow reducing dimensions if the target is not reachable
--floor-side N       long-side floor with --allow-downscale (2048)
--no-slug            keep the original file name
-r                   include subfolders
```
