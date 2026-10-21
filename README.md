# Shopify image export guide

[Português (Brasil)](docs/README-ptbr.md)

A standard for exporting and validating images for Shopify stores without losing sharpness or color, with a good weight for SEO and performance.

## What is here

| File | For whom | What it is |
| --- | --- | --- |
| [`docs/designers-guide.md`](docs/designers-guide.md) | Designers (Photoshop) | 2× sizing, sRGB conversion, Save for Web settings, file naming and a delivery checklist |
| [`shopify-image-optimizer/`](shopify-image-optimizer/) | Designers and developers | A skill with the script that audits and optimizes images before they are sent or uploaded |

Portuguese versions: [`docs/README-ptbr.md`](docs/README-ptbr.md) and [`docs/designers-guide-ptbr.md`](docs/designers-guide-ptbr.md).

## Download

- With Git: `git clone https://github.com/leotubarao/shopify-image-export-guide.git`
- Without Git: on the repository page on GitHub, click **Code > Download ZIP** and extract it.

Designers: the guide ([`docs/designers-guide.md`](docs/designers-guide.md)) tells you how to export, and the skill checks your files before you send them. No terminal needed with Claude: attach the images to a chat and ask it to check them for Shopify.

## Install the skill (optional)

- **Claude (claude.ai or desktop app):** code execution must be enabled. Download [`shopify-image-optimizer.zip`](https://github.com/leotubarao/shopify-image-export-guide/releases/latest/download/shopify-image-optimizer.zip) from the latest release, add it in **Customize > Skills** and turn the skill on. After that, attach images to a chat and ask Claude to check or optimize them for Shopify. Official guide: [How to create custom skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills).
  - If you would rather build the ZIP yourself, zip the `shopify-image-optimizer` folder so that the folder itself is the root of the ZIP (`shopify-image-optimizer.zip` containing `shopify-image-optimizer/SKILL.md`). Do not zip the whole repository.
- **Claude Code:** copy the `shopify-image-optimizer` folder to `~/.claude/skills/` (all your projects) or to `.claude/skills/` inside a project. Official guide: [Extend Claude with skills](https://code.claude.com/docs/en/skills).
- **Without Claude:** run the script directly with Python, as shown below.

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

Naming is optional. By default files only get a plain slug (lowercase, no accents or special characters, hyphens instead of spaces). To name files by what they show, ask Claude: the skill asks first, looks at each image and writes a names file. Without Claude, fill the names yourself (`--names-template names.json`, then `--names names.json`). `--name-prefix` and `--name-suffix` add text before or after every name.

Every optimize run prints a before and after summary: image count, total weight before and after, percent saved, colors converted to sRGB, files renamed and warnings. `report.csv` has the same numbers per image (original and new format, dimensions, weight, color profile and estimated quality).

The recommended flow is to run `--check` first and optimize only what comes back as FIX, preferably from the designer's original file, because each JPEG recompression loses a little quality. The CSV reports use `;` as the delimiter, so they open directly in Excel in pt-BR locales.

## Things to keep in mind

- The presets (2× sizes and target weights) are team defaults, not Shopify limits. Adjust them per client and per theme.
- Photoshop's quality scale is not the same as the one estimated by `--check`. Check each designer's first batch and adjust if the estimated quality comes back below 80.
- The script was tested with synthetic images (photos, CMYK with a profile, transparent PNG, repeated names). Validate it with real client files before using it on a batch.
