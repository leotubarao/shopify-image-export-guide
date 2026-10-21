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
3. **Ask about naming (optimize runs only).** Before optimizing, ask once, in one short message: "Do you want me to look at each image and rename it by what it shows? You can also add a prefix or suffix, for example the brand or `v2`. If not, I'll just sanitize the names: lowercase, no accents or special characters, hyphens instead of spaces." Skip the question when the user already answered in the request, when you are only running `--check`, or when nobody is there to answer. If the answer is no, or the user does not care, go straight to step 4 with the default behavior. If the answer is yes, follow "Naming files" below.
4. **Optimize only what needs it**, preferably from the designer's original/master file (not from an already compressed JPEG):
   ```bash
   python3 scripts/optimize.py FOLDER_OR_FILES -o ./optimized --preset product
   ```
5. **Read the report** in the terminal and in `optimized/report.csv`. Then tell the user the before and after (see "Before and after" below), with **every warning**.
6. Deliver the files in `optimized/`. Originals are never changed.

If Pillow is missing: `pip install Pillow` (add `--break-system-packages` on managed Python installs).

## Naming files

**Default** (the user said no, or did not care): files only get the plain slug. Lowercase, accents and special characters removed, spaces and symbols turned into hyphens (`Sérum Vitamina C - frente.png` becomes `serum-vitamina-c-frente.jpg`). Nothing else changes.

**Context naming** is optional and happens only when the user says yes. The script cannot see images; you can. Procedure:

1. Look at every image (open it; in a chat, attached images are already visible).
2. Pick a name that says what the image shows: subject first, then view or variant, 3 to 6 words. Examples: `vitamin-c-serum-front`, `vitamin-c-serum-texture`, `woman-applying-cream`.
3. Use brand or product names only when they are readable in the image or the user gave them. Never invent names, ingredients, benefits or claims; describe what is visible. For skincare and pharma, no therapeutic claims in file names.
4. Do not name real people. Describe them generically ("woman-applying-cream").
5. Write the names in the language the user writes in, unless told otherwise. The script strips the accents.
6. Keep names unique inside the batch (front, back, side, texture, lifestyle). The script adds `-2`, `-3` to repeated names as a safety net.
7. If you cannot tell what an image shows, leave it out of the names file: it gets the plain slug. Tell the user which ones.
8. Save a JSON file mapping each original file name to the new name (extension optional) and run with `--names`. To start from a skeleton: `python3 scripts/optimize.py FOLDER --names-template names.json`.
   ```bash
   python3 scripts/optimize.py FOLDER -o ./optimized --names names.json
   ```
9. After the run, show a short table: old name, new name. Originals are untouched, so a bad name is cheap to redo.

**Prefix and suffix:** if the user wants one (brand, client, season, version), add `--name-prefix` and/or `--name-suffix`. They apply to every file, with or without `--names`, and are sanitized the same way.

```bash
python3 scripts/optimize.py FOLDER -o ./optimized --names names.json --name-prefix brand --name-suffix v2
```

## Before and after

After every optimize run, tell the user what happened, in the user's language and in plain words. Keep it short. Example: "I adjusted 5 images: 7.8 MB before, 1 MB after, 87% saved. 1 image had its colors converted to sRGB, 3 were renamed, 1 needs attention (the original is only 600 px)." Take the numbers from the script's "Before -> after" block and from `report.csv`; never estimate them.

- Add a small table only when it helps: old name, new name, weight before and after, per file.
- Explain every warning in plain language and say what the designer should do (usually: export again from the original PSD).
- Be honest about what the numbers mean: weight is a real measurement; fidelity (PSNR above ~40 dB) means the difference should be imperceptible, not that it is zero. Do not promise "no visible loss" beyond that.

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

- The user may be a designer without a terminal. Run the commands yourself on the attached images, then hand back the optimized files with a plain-language summary (what was fixed, what still needs a new export from the original PSD).
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
--names FILE.json    map original file names to new names (sanitized)
--names-template F   write an empty names file for the inputs and exit
--name-prefix TEXT   text added before every output name
--name-suffix TEXT   text added after every output name
-r                   include subfolders
```
