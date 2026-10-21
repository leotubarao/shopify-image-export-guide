#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimize images for Shopify WITHOUT losing resolution.

Principles:
  1. Never upscale and, by default, never shrink below the requested 2x size.
  2. Convert to sRGB (correct colors in the browser) and strip heavy metadata.
  3. To reach the target weight, lower only the compression QUALITY, inside a
     safe range (default 90 -> 80), using binary search: the result always has
     the HIGHEST quality that fits the target.
  4. Dimensions are reduced only if you ask for it (--allow-downscale).
  5. Measures fidelity (PSNR) against the resized original and warns if it drops.

Quick use:
  python3 optimize.py ./photos -o ./optimized --preset product
  python3 optimize.py banner.psd -o out --preset banner --display-width 1600
  python3 optimize.py ./photos --check --preset product
"""
import argparse
import csv
import io
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageCms, ImageChops, ImageOps, ImageStat

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".psd"}

# max_side  = long side in px (already 2x, for retina/4K screens)
# min_side  = below this the image tends to look soft on retina/4K (used by --check)
# target_kb = target weight; a GOAL, it never forces smaller dimensions.
PRESETS = {
    "product": dict(max_side=2400, min_side=2048, target_kb=500),
    "collection": dict(max_side=2000, min_side=1600, target_kb=400),
    "banner": dict(max_side=3200, min_side=2400, target_kb=900),
    "blog": dict(max_side=2400, min_side=1600, target_kb=500),
}

MIN_ZOOM_PX = 800  # below this, product page zoom may not work

SRGB_PROFILE = ImageCms.createProfile("sRGB")


# ------------------------------------------------------------------ helpers
def slugify(stem: str) -> str:
    s = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "image"


def clean_name(value: str) -> str:
    """Sanitize a name coming from a names file: drop a typed image extension, then slugify."""
    value = str(value).strip()
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if value.lower().endswith(ext):
            value = value[: -len(ext)]
            break
    return slugify(value)


def clean_affix(value) -> str:
    """Sanitize a prefix/suffix. Returns '' when nothing usable is left (slugify would return 'image')."""
    if not value:
        return ""
    s = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()


def fmt_kb(n_bytes: int) -> str:
    return f"{n_bytes / 1024:,.0f} KB"


def is_srgb(profile) -> bool:
    try:
        desc = ImageCms.getProfileDescription(profile) or ""
    except Exception:
        desc = ""
    return "srgb" in desc.lower()


def has_real_alpha(im: Image.Image) -> bool:
    if im.mode in ("RGBA", "LA"):
        return im.getchannel("A").getextrema()[0] < 255
    if im.mode == "P" and "transparency" in im.info:
        return True
    return False


def describe_profile(mode: str, icc) -> str:
    """Human-readable color profile of the ORIGINAL file (for the before/after report)."""
    if icc:
        try:
            desc = (ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))) or "").strip()
        except Exception:
            desc = "unreadable profile"
        desc = desc or "unnamed profile"
        return f"CMYK ({desc})" if mode == "CMYK" else desc
    return "CMYK (no profile)" if mode == "CMYK" else "none"


# ------------------------------------------------------------- color / mode
def normalize_color(im: Image.Image, notes: list) -> Image.Image:
    """Return an 8-bit sRGB image (RGB or RGBA)."""
    icc = im.info.get("icc_profile")

    # 16-bit / integer -> 8-bit
    if im.mode.startswith("I") or im.mode == "F":
        im = im.point(lambda v: v * (1 / 256)).convert("L")
        notes.append("16-bit converted to 8-bit")

    if im.mode == "P":
        im = im.convert("RGBA" if "transparency" in im.info else "RGB")
    if im.mode == "LA":
        im = im.convert("RGBA")
    if im.mode == "L":
        im = im.convert("RGB")

    alpha = None
    if im.mode == "RGBA":
        alpha = im.getchannel("A")
        base = im.convert("RGB")
    else:
        base = im

    if im.mode == "CMYK" or base.mode == "CMYK":
        if icc:
            try:
                src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
                base = ImageCms.profileToProfile(
                    base, src, SRGB_PROFILE,
                    renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                    outputMode="RGB",
                    flags=ImageCms.Flags.BLACKPOINTCOMPENSATION,
                )
                notes.append("CMYK converted to sRGB using the embedded profile")
            except Exception as e:  # broken profile
                base = base.convert("RGB")
                notes.append(f"CMYK conversion unreliable ({e}); check the colors")
        else:
            base = base.convert("RGB")
            notes.append("CMYK WITHOUT a profile: colors may shift. Ask the designer for RGB")
    elif icc:
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            if not is_srgb(src):
                base = ImageCms.profileToProfile(
                    base, src, SRGB_PROFILE,
                    renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                    outputMode="RGB",
                    flags=ImageCms.Flags.BLACKPOINTCOMPENSATION,
                )
                desc = ImageCms.getProfileDescription(src).strip()
                notes.append(f"converted from '{desc}' to sRGB")
        except Exception as e:
            notes.append(f"unreadable color profile ({e}); assumed sRGB")

    if alpha is not None:
        base = base.convert("RGB")
        base.putalpha(alpha)
    return base


# ------------------------------------------------------------------ encoding
def encode(im: Image.Image, fmt: str, q: int, chroma: int) -> bytes:
    buf = io.BytesIO()
    if fmt == "jpeg":
        im.convert("RGB").save(
            buf, "JPEG", quality=q, optimize=True, progressive=True,
            subsampling=0 if chroma == 444 else 2,
        )
    elif fmt == "webp":
        im.save(buf, "WEBP", quality=q, method=6)
    elif fmt == "png":
        im.save(buf, "PNG", optimize=True)
    else:
        raise ValueError(fmt)
    return buf.getvalue()


def flatten_white(im: Image.Image) -> Image.Image:
    """Composite over white. Needed to compare images with transparency: the RGB
    'hidden' under transparent pixels changes on compression and would skew the metric."""
    if im.mode == "RGBA":
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.getchannel("A"))
        return bg
    return im.convert("RGB")


def psnr(ref: Image.Image, data: bytes) -> float:
    out = Image.open(io.BytesIO(data))
    out.load()
    a, b = flatten_white(ref), flatten_white(out)
    if a.size != b.size:
        return float("nan")
    rms = ImageStat.Stat(ImageChops.difference(a, b)).rms
    mse = sum(r * r for r in rms) / 3
    return 99.0 if mse == 0 else 10 * math.log10(255 * 255 / mse)


def best_quality(im, fmt, target_bytes, q_max, q_min, chroma):
    """Highest quality in [q_min, q_max] whose file fits the target.
    Returns (bytes, quality, fits_target)."""
    if fmt == "png":
        data = encode(im, "png", 0, chroma)
        return data, 0, len(data) <= target_bytes
    lo, hi = q_min, q_max
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        data = encode(im, fmt, mid, chroma)
        if len(data) <= target_bytes:
            best = (data, mid)
            lo = mid + 1
        else:
            hi = mid - 1
    if best:
        return best[0], best[1], True
    data = encode(im, fmt, q_min, chroma)
    return data, q_min, False


def resize_to(base: Image.Image, max_side: int):
    w, h = base.size
    long = max(w, h)
    if long <= max_side:
        return base, False
    s = max_side / long
    return base.resize((max(1, round(w * s)), max(1, round(h * s))), Image.LANCZOS), True


# ------------------------------------------------------------------ optimize
def process(path: Path, out_dir: Path, a) -> dict:
    notes, warns = [], []
    orig_size = path.stat().st_size
    with Image.open(path) as im0:
        im0.load()
        orig_dims = im0.size
        orig_fmt = im0.format or path.suffix.lstrip(".").upper()
        orig_q = estimate_jpeg_quality(im0) if im0.format == "JPEG" else None
        im = ImageOps.exif_transpose(im0)
        im.info.update(im0.info)
        icc = im.info.get("icc_profile")
        orig_profile = describe_profile(im.mode, icc)
        color_fixed = im.mode == "CMYK" or (bool(icc) and "srgb" not in orig_profile.lower())
        base = normalize_color(im, notes)

    alpha = has_real_alpha(base)
    max_side = a.max_side
    if a.display_width and a.max_side_from_preset:
        max_side = min(max_side, a.display_width * 2)

    fmt = a.format
    if fmt == "auto":
        fmt = "png" if alpha else "jpeg"

    target = a.target_kb * 1024
    img, resized = resize_to(base, max_side)
    data, q, ok = best_quality(img, fmt, target, a.q_max, a.q_min, a.chroma)

    # PNG with transparency over the target -> WebP with alpha (keeps transparency)
    if not ok and fmt == "png" and a.format == "auto":
        data2, q2, ok2 = best_quality(img, "webp", target, a.q_max, a.q_min, a.chroma)
        if len(data2) < len(data):
            data, q, ok, fmt = data2, q2, ok2, "webp"
            notes.append("PNG with transparency too heavy: converted to WebP (keeps transparency)")

    # Dimensions are reduced only when explicitly allowed
    if not ok and a.allow_downscale:
        long = max(img.size)
        floor = min(a.floor_side, max(base.size))
        while not ok and long > floor:
            long = max(floor, int(long * 0.92))
            img, resized = resize_to(base, long)
            data, q, ok = best_quality(img, fmt, target, a.q_max, a.q_min, a.chroma)
        notes.append(f"dimensions reduced by --allow-downscale (floor {a.floor_side}px)")

    fid = psnr(resize_to(base, max(img.size))[0], data) if fmt != "png" else 99.0

    # warnings
    if not ok:
        tail = ("already at the dimension floor; ask for cleaner artwork or raise --target-kb"
                if a.allow_downscale else
                "dimensions kept on purpose; ask for cleaner artwork, raise --target-kb or use --allow-downscale")
        warns.append(f"above target ({fmt_kb(len(data))} > {a.target_kb} KB) even at minimum quality: {tail}")
    if max(orig_dims) < MIN_ZOOM_PX:
        warns.append(f"original is {max(orig_dims)}px: below {MIN_ZOOM_PX}px (zoom may not work in the store). Ask for a larger file")
    if a.display_width and img.size[0] < a.display_width * 2:
        warns.append(f"width {img.size[0]}px < 2x the display width ({a.display_width * 2}px): may look soft on retina screens")
    if not resized and max(orig_dims) < max_side:
        notes.append("not enlarged (we never upscale)")
    if fmt != "png" and fid < 38:
        warns.append(f"low fidelity (PSNR {fid:.1f} dB). Raise --q-min or --target-kb")
    if len(data) >= orig_size:
        warns.append("output is larger than the original (the original was already well compressed)")

    ext = {"jpeg": ".jpg", "webp": ".webp", "png": ".png"}[fmt]
    custom = a.names_map.get(path.name) or a.names_map.get(path.stem)
    if custom:
        stem = clean_name(custom)
        notes.append("renamed from the names file")
    else:
        stem = path.stem if a.no_slug else slugify(path.stem)
    stem = "-".join(p for p in (a.name_prefix, stem, a.name_suffix) if p)
    out_path = out_dir / f"{stem}{ext}"
    n = 2
    while out_path.exists() and a._written.get(out_path) != path:
        out_path = out_dir / f"{stem}-{n}{ext}"
        n += 1
    out_path.write_bytes(data)
    a._written[out_path] = path

    orig_kb, new_kb = round(orig_size / 1024), round(len(data) / 1024)
    return dict(
        file=path.name, output=out_path.name,
        orig_format=orig_fmt, format=fmt.upper(),
        orig_dim=f"{orig_dims[0]}x{orig_dims[1]}", new_dim=f"{img.size[0]}x{img.size[1]}",
        orig_kb=orig_kb, new_kb=new_kb, saved_pct=round(100 - 100 * len(data) / max(orig_size, 1)),
        orig_profile=orig_profile, orig_quality=orig_q if orig_q is not None else "-",
        quality=q if fmt != "png" else "-", psnr_db=round(fid, 1) if fmt != "png" else "-",
        within_target="yes" if ok else "NO", warnings=" | ".join(warns), notes=" | ".join(notes),
        _color_fixed=color_fixed,
    )


# ------------------------------------------------------------ --check (audit)
# Standard JPEG luminance table (Annex K), used to estimate the quality of an
# already exported JPEG (libjpeg-equivalent 1-100 scale).
_STD_LUM = [
    16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56, 14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99,
]


def estimate_jpeg_quality(im: Image.Image):
    q = getattr(im, "quantization", None)
    if not q or 0 not in q or len(q[0]) != 64:
        return None
    table = list(q[0])
    best, best_err = None, float("inf")
    for quality in range(1, 101):
        s = 5000 / quality if quality < 50 else 200 - 2 * quality
        ref = [min(255, max(1, int((v * s + 50) // 100))) for v in _STD_LUM]
        err = sum((x - y) ** 2 for x, y in zip(table, ref))
        if err < best_err:
            best, best_err = quality, err
    return best


def check_file(path: Path, a) -> dict:
    """Audit a file delivered by the designer. Writes nothing, never recompresses."""
    issues, notes = [], []
    size = path.stat().st_size
    preset = PRESETS[a.preset]
    with Image.open(path) as im:
        fmt, (w, h), mode = im.format, im.size, im.mode
        icc = im.info.get("icc_profile")
        qual = estimate_jpeg_quality(im) if fmt == "JPEG" else None
        progressive = bool(im.info.get("progressive") or im.info.get("progression"))
        exif_kb = len(im.info.get("exif") or b"") / 1024
        alpha = has_real_alpha(im)

    long = max(w, h)
    min_side = a.display_width * 2 if a.display_width else preset["min_side"]
    max_side = a.max_side or preset["max_side"]
    target_kb = a.target_kb or preset["target_kb"]

    if fmt not in ("JPEG", "WEBP", "PNG"):
        issues.append(f"format {fmt}: export JPEG (photos) or PNG/WebP (transparency)")
    if fmt == "PNG" and not alpha and size / 1024 > target_kb:
        issues.append("PNG without transparency: export JPEG instead (much lighter, same look)")
    if mode == "CMYK":
        issues.append("CMYK: convert to RGB (sRGB)")
    if icc and mode != "CMYK":
        try:
            prof = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            if not is_srgb(prof):
                desc = (ImageCms.getProfileDescription(prof) or "?").strip()
                issues.append(f"profile '{desc}': Shopify strips color profiles, so colors come out wrong. Use 'Convert to sRGB'")
        except Exception:
            notes.append("unreadable color profile")
    elif not icc and mode != "CMYK":
        notes.append("no embedded profile (fine if exported with 'Convert to sRGB')")
    if long < min_side:
        issues.append(f"{w}x{h}: below {min_side}px on the long side (needs to be 2x). Will look soft on retina/4K")
    if long > max_side * 1.05:
        issues.append(f"{w}x{h}: larger than needed (max {max_side}px). Adds weight for nothing")
    if size / 1024 > target_kb:
        issues.append(f"{size / 1024:.0f} KB: above the {target_kb} KB target (lower the quality only, never the dimensions)")
    if qual is not None and qual < a.q_min:
        issues.append(f"JPEG quality ≈ {qual} (< {a.q_min}): already heavily compressed. Re-export from the original")
    if exif_kb > 20:
        notes.append(f"heavy metadata ({exif_kb:.0f} KB): export with Metadata = None")
    if fmt == "JPEG" and not progressive:
        notes.append("non-progressive JPEG (optional)")
    if slugify(path.stem) != path.stem:
        issues.append("file name not SEO-friendly (lowercase, hyphens, no accents or spaces)")

    return dict(
        file=path.name, format=fmt, dim=f"{w}x{h}", kb=round(size / 1024),
        est_quality=qual if qual is not None else "-",
        profile="CMYK" if mode == "CMYK" else ("yes" if icc else "none"),
        status="OK" if not issues else "FIX",
        issues=" | ".join(issues), notes=" | ".join(notes),
    )


def collect(inputs, recursive):
    files = []
    for raw in inputs:
        p = Path(raw)
        if p.is_dir():
            it = p.rglob("*") if recursive else p.glob("*")
            files += sorted(f for f in it if f.suffix.lower() in EXTS and f.is_file())
        elif p.is_file() and p.suffix.lower() in EXTS:
            files.append(p)
        else:
            print(f"[ignored] {raw}", file=sys.stderr)
    return files


def write_csv(path: Path, rows: list):
    # ';' delimiter + UTF-8 BOM so the file opens directly in Excel in pt-BR locales
    fields = [k for k in rows[0] if not k.startswith("_")]  # "_" keys are internal (report page only)
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description="Optimize images for Shopify without losing resolution.")
    ap.add_argument("inputs", nargs="+", help="files and/or folders")
    ap.add_argument("-o", "--out", default=None,
                    help="output folder (default: ./optimized; originals are never overwritten)")
    ap.add_argument("--check", action="store_true",
                    help="audit only (format, 2x size, weight, profile, estimated quality, name); writes no images")
    ap.add_argument("--preset", choices=PRESETS, default="product")
    ap.add_argument("--max-side", type=int, help="long side in px (default: from the preset, already 2x)")
    ap.add_argument("--display-width", type=int,
                    help="width (CSS px) at which the image appears in the theme; caps the export at 2x that value")
    ap.add_argument("--target-kb", type=int, help="target weight in KB (default: from the preset)")
    ap.add_argument("--q-max", type=int, default=90, help="highest quality tried (default 90)")
    ap.add_argument("--q-min", type=int, default=80, help="lowest quality accepted (default 80)")
    ap.add_argument("--format", choices=["auto", "jpeg", "webp", "png"], default="auto",
                    help="auto: JPEG for photos, PNG/WebP when there is transparency")
    ap.add_argument("--chroma", type=int, choices=[444, 420], default=444,
                    help="444 keeps text/labels sharp (default); 420 makes smaller files")
    ap.add_argument("--allow-downscale", action="store_true",
                    help="allow reducing dimensions if the target is not reachable (off by default)")
    ap.add_argument("--floor-side", type=int, default=2048, help="long-side floor used with --allow-downscale")
    ap.add_argument("--no-slug", action="store_true", help="keep the original file name")
    ap.add_argument("--names", metavar="FILE.json",
                    help="JSON file mapping each original file name to a new name, e.g. "
                         '{"IMG_001.png": "vitamin-c-serum-front"}. Names are still sanitized. '
                         "Without this option, files only get the plain slug (lowercase, hyphens, no accents)")
    ap.add_argument("--name-prefix", metavar="TEXT",
                    help="text added before every output name (sanitized), e.g. the brand")
    ap.add_argument("--name-suffix", metavar="TEXT",
                    help="text added after every output name (sanitized), e.g. v2")
    ap.add_argument("--names-template", metavar="FILE.json",
                    help="write an empty names file for the given inputs and exit (to fill by hand or with an AI)")
    ap.add_argument("-r", "--recursive", action="store_true", help="include subfolders")
    a = ap.parse_args()

    preset = PRESETS[a.preset]
    a.max_side_from_preset = a.max_side is None
    a.max_side = a.max_side or preset["max_side"]
    a.target_kb = a.target_kb or preset["target_kb"]
    if a.q_min > a.q_max:
        ap.error("--q-min cannot be greater than --q-max")
    a._written = {}

    files = collect(a.inputs, a.recursive)
    if not files:
        sys.exit("No images found (accepted: " + ", ".join(sorted(EXTS)) + ")")

    if a.names_template:
        tpl = {f.name: "" for f in files}
        Path(a.names_template).write_text(json.dumps(tpl, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Names template with {len(tpl)} file(s) written to {a.names_template}")
        sys.exit(0)

    a.name_prefix = clean_affix(a.name_prefix)
    a.name_suffix = clean_affix(a.name_suffix)
    a.names_map = {}
    if a.names:
        try:
            raw = json.loads(Path(a.names).read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("expected a JSON object")
        except Exception as e:
            sys.exit(f"Could not read --names file: {e}")
        a.names_map = {str(k): str(v) for k, v in raw.items() if str(v).strip()}
        known = {f.name for f in files} | {f.stem for f in files}
        unmatched = [k for k in a.names_map if k not in known]
        if unmatched:
            print("[warning] names file entries with no matching image: " + ", ".join(unmatched), file=sys.stderr)

    if a.check:
        rows = []
        for f in files:
            try:
                r = check_file(f, a)
            except Exception as e:
                print(f"{f.name:<34} FAILED: {e}", file=sys.stderr)
                continue
            rows.append(r)
            mark = "OK " if r["status"] == "OK" else "FIX"
            print(f"[{mark}] {r['file']:<34} {r['format']:<5} {r['dim']:>11} {r['kb']:>6} KB  "
                  f"q≈{r['est_quality']}  profile={r['profile']}")
            for p in filter(None, r["issues"].split(" | ")):
                print(f"        ✖ {p}")
            for n in filter(None, r["notes"].split(" | ")):
                print(f"        · {n}")
        bad = sum(r["status"] != "OK" for r in rows)
        print(f"\n{len(rows)} file(s): {len(rows) - bad} OK, {bad} to fix (preset: {a.preset}).")
        if a.out and rows:
            Path(a.out).mkdir(parents=True, exist_ok=True)
            write_csv(Path(a.out) / "check-report.csv", rows)
        sys.exit(0)

    out_dir = Path(a.out or "optimized")
    out_dir.mkdir(parents=True, exist_ok=True)
    if any(out_dir.resolve() == f.parent.resolve() for f in files):
        sys.exit("The output folder cannot be the same as the originals' folder.")

    rows, failed = [], 0
    for f in files:
        try:
            r = process(f, out_dir, a)
            rows.append(r)
            flag = "  !" if r["warnings"] else ""
            print(f"{r['file']:<34} {r['orig_dim']:>11} {r['orig_kb']:>6} KB -> "
                  f"{r['new_dim']:>11} {r['new_kb']:>5} KB  {r['format']:<4} q={r['quality']:<3} "
                  f"PSNR={r['psnr_db']}{flag}")
            for w in filter(None, r["warnings"].split(" | ")):
                print(f"    WARNING: {w}")
            for n in filter(None, r["notes"].split(" | ")):
                print(f"    note:    {n}")
        except Exception as e:
            failed += 1
            print(f"{f.name:<34} FAILED: {e}", file=sys.stderr)

    if rows:
        rep = out_dir / "report.csv"
        write_csv(rep, rows)
        tot_o = sum(r["orig_kb"] for r in rows)
        tot_n = sum(r["new_kb"] for r in rows)
        n_color = sum(bool(r["_color_fixed"]) for r in rows)
        n_ren = sum(Path(r["file"]).stem != Path(r["output"]).stem for r in rows)
        n_warn = sum(bool(r["warnings"]) for r in rows)
        print(f"\nBefore -> after ({len(rows)} image(s))")
        print(f"  weight:   {tot_o:,} KB -> {tot_n:,} KB ({100 - 100 * tot_n / max(tot_o, 1):.0f}% smaller)")
        print(f"  color:    {n_color} converted to sRGB")
        print(f"  names:    {n_ren} renamed")
        print(f"  warnings: {n_warn} image(s) need attention")
        print(f"  CSV report: {rep}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
