# Image export guide for the store (Photoshop → Shopify)

[Português (Brasil)](designers-guide-ptbr.md)

Export at 2× the displayed width, in sRGB, as JPEG with quality 85. That way the image reaches Shopify sharp and light enough for SEO and speed. Never shrink the dimensions to lower the weight: lower only the quality, and only down to 80.

## Why images lose quality in the store

1. **Too few pixels.** Phones and 4K monitors display images with twice the pixels. A 1,200 px file in a 1,200 px slot looks soft: it needs to be 2,400 px.
2. **Wrong color profile.** Shopify strips the color profile when it displays the image in the store. A file in Adobe RGB, Display P3 or CMYK comes out dull or shifted. Convert to sRGB before exporting.
3. **Too much compression.** Shopify does not compress on upload, but the image may be compressed when served through the theme, and it is converted to WebP or AVIF when the browser supports it. A JPEG exported at low quality gets worse at that stage. The better the file you send, the better the final result.

An overweight file also hurts: it slows the page and SEO. So the rule is correct dimensions, with weight controlled only through compression quality.

## Sizes by image type

Export at twice the width the image has in the theme. The values below are the defaults; the dev gives you the real width of each slot for each client.

| Type | Displayed in the theme (example) | Export (2×) | Aspect ratio | Target weight |
| --- | --- | --- | --- | --- |
| Product | 1,000 to 1,200 px | 2,048 to 2,400 px on the long side | 1:1, the same on every photo | up to 500 KB |
| Collection | 1,000 px | 2,000 px | the theme's, the same on all | up to 400 KB |
| Banner / full-width hero | 1,600 px | 3,200 px | the theme's | up to 900 KB |
| Blog | 1,200 px | 2,400 px | the theme's | up to 500 KB |

Shopify limits: 20 MB and 20 megapixels per image. For a square product image, Shopify points to 2,048 × 2,048 px as the size that usually displays best. Never enlarge small artwork in Photoshop: ask for the original file. Below 800 px, zoom on the product page may not work.

## Step by step in Photoshop

Menu names are in English; localized versions of Photoshop may differ slightly.

1. **Start from the original PSD**, in high resolution. Always export from it, never from an already exported JPEG: each new compression loses quality.
2. **Set the final size** in Image > Image Size. Width in px = 2× the value in the table. When reducing, use Resample: Bicubic Sharper (reduction). If the artwork is smaller than needed, do not enlarge it: tell the dev.
3. **Check the mode** in Image > Mode: RGB Color and 8 Bits/Channel. Never CMYK.
4. **Convert to sRGB** in Edit > Convert to Profile: Destination Space = sRGB IEC61966-2.1, Intent = Relative Colorimetric, Use Black Point Compensation on. Use *Convert*, not *Assign*: only Convert changes the color values.
5. **Export** with File > Export > Save for Web (Legacy), shortcut Alt+Shift+Ctrl+S on Windows and Opt+Shift+Cmd+S on Mac. Use the settings in the next section.
6. **Check the weight** at the bottom left of the window, with the preview at 100%. Above the target weight, lower the quality in steps of 5, down to 80 at the minimum. If it is still over, do not reduce the dimensions: send the file to the dev.
7. **Name the file** for SEO: lowercase, hyphens, no accents or spaces, describing the image. Example: `vitamin-c-serum-front.jpg` and `vitamin-c-serum-texture.jpg`. Avoid "final", "new" and "copy".
8. **Transparent background:** export PNG-24 with Transparency on. The dev converts it to WebP if it gets heavy.

## Save for Web (Legacy) settings

The whole team uses this method and these settings, so the quality scale is the same across files.

| Field | Value | Why |
| --- | --- | --- |
| Format | JPEG | Best balance of weight and quality for photos |
| Quality | 85, never below 80 | Photoshop's "Very High" range, suitable for product photos |
| Progressive | On | The image shows up whole and gains sharpness as it loads |
| Optimized | On | Smaller file, no quality loss |
| Convert to sRGB | On | Guarantees the right colors, since Shopify strips the profile |
| Embed Color Profile | Either | What matters is the conversion in step 4 |
| Blur | 0 | Any higher value takes away sharpness |
| Metadata | None | Removes EXIF and thumbnails, which only add weight |
| Image Size | 100% (width and height already set in step 2) | Do not resize again here |
| Matte | White | Only matters if the artwork has transparent areas |

If a field has a different name in your version, send the dev a screenshot of the window. Export As is also fine as an alternative: turn on Convert to sRGB, choose Metadata = None and do not let the program resize. Export As's Quality scale may not equal Save for Web's, so the dev checks the first batch before the team adopts that method.

## Checklist before sending

- [ ] Width equal to 2× the one in the table (for example, 2,400 px for product)
- [ ] RGB mode, 8-bit, converted to sRGB with Convert to Profile
- [ ] JPEG with Quality 85 (minimum 80), Progressive and Optimized on, Metadata set to None
- [ ] Weight within the table's target, without having reduced the dimensions
- [ ] Name in lowercase, with hyphens, no accents and no spaces
- [ ] Aspect ratio equal to the other images in the same group (products at 1:1)
- [ ] Exported from the original PSD, not from another JPEG
- [ ] Preview at 100% with label text and edges sharp, no blocks or halos

## Dev check

Before uploading to Shopify, the dev runs the [`shopify-image-optimizer`](../shopify-image-optimizer/SKILL.md) skill in audit mode. It lists, per file, format, dimensions, weight, color profile, estimated JPEG quality and name, and marks OK or FIX without changing anything.

```
python3 shopify-image-optimizer/scripts/optimize.py designer-folder --check --preset product
```

A file with estimated quality below 80, a size smaller than 2×, or a profile other than sRGB goes back to the designer for a new export from the PSD. A file with correct size and color but over the weight target is optimized by the dev without reducing the resolution:

```
python3 shopify-image-optimizer/scripts/optimize.py designer-folder -o optimized --preset product
```

## Sources

- [Shopify: product media types](https://help.shopify.com/en/manual/products/product-media/product-media-types): accepted formats, 20 MB limit and the 2,048 × 2,048 px size for square products.
- [Shopify: theme images](https://help.shopify.com/en/manual/online-store/images/theme-images): no compression on upload, color profile removed on display, 20 MB and 20 megapixel limits.
- [Adobe Community: Export As options](https://community.adobe.com/t5/photoshop-ecosystem-discussions/i-need-help-understanding-the-options-in-export-as-quot/m-p/12762940): Convert to sRGB and Embed color profile.
- [Adobe Community: wrong colors when exporting sRGB](https://community.adobe.com/t5/photoshop-ecosystem-discussions/ps-export-as-srgb-jpg-colors-wrong/m-p/14432944): document profile and Convert to sRGB.

What does not come from those pages: the 2× rule and the weight targets are team recommendations, not Shopify limits. The two Shopify pages disagree on the megapixel limit (20 on one, 25 on the other); this guide uses the lower one. The Save for Web fields follow Photoshop's standard interface, and I did not find an accessible Adobe page confirming each one.
