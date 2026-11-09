#!/usr/bin/env python3
"""Generate one vertically joined Japanese image per episode, without editing originals."""

import argparse
import io
import json
import re
from pathlib import Path
from statistics import median
from typing import Any, cast

from PIL import Image, ImageChops, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent
DEFAULT_DOCS = ROOT


def trim_background(image: Image.Image, threshold: int = 16) -> Image.Image | None:
    """Trim only outer background; return None for light, empty spacer images."""
    width, height = image.size
    corners = [
        cast(tuple[int, int, int], image.getpixel(point))
        for point in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))
    ]
    background = tuple(int(median(c[channel] for c in corners)) for channel in range(3))
    # Full-bleed artwork and ambiguous backgrounds are safer left untouched.
    if min(background) < 180 or any(
        max(c[channel] for c in corners) - min(c[channel] for c in corners) > 24
        for channel in range(3)
    ):
        return image.copy()
    smoothed = image.filter(ImageFilter.GaussianBlur(1))
    channels = ImageChops.difference(
        smoothed, Image.new("RGB", image.size, background)
    ).split()
    difference = ImageChops.lighter(
        ImageChops.lighter(channels[0], channels[1]), channels[2]
    )
    bounds = difference.point(lambda value: 255 if value > threshold else 0).getbbox()
    if bounds is None:
        return None
    # Leave a safety margin around lettering and illustrations outside the panels.
    safety = max(16, round(width * 0.015))
    left, top, right, bottom = bounds
    return image.crop(
        (
            max(0, left - safety),
            max(0, top - safety),
            min(width, right + safety),
            min(height, bottom + safety),
        )
    )


def join_pages(
    paths: list[Path],
    *,
    trim: bool = True,
    threshold: int = 16,
    max_width: int = 1600,
    gap: int = 16,
    padding: int = 16,
) -> Image.Image:
    pages = []
    background = None
    for path in paths:
        with Image.open(path) as original:
            image = ImageOps.exif_transpose(original).convert("RGB")
        if background is None:
            background = image.getpixel((0, 0))
        page = trim_background(image, threshold) if trim else image
        if page is not None:
            pages.append(page)
    if not pages:
        raise ValueError("Episode contains only blank images")
    # Use a common scale so lettering does not grow/shrink between source pages.
    scale = min(1.0, (max_width - 2 * padding) / max(page.width for page in pages))
    if scale < 1:
        pages = [
            page.resize(
                (max(1, round(page.width * scale)), max(1, round(page.height * scale))),
                Image.Resampling.LANCZOS,
            )
            for page in pages
        ]
    width = max(page.width for page in pages) + 2 * padding
    height = sum(page.height for page in pages) + gap * (len(pages) - 1) + 2 * padding
    if height > 65500:
        raise ValueError(
            "Joined image exceeds the JPEG height limit; reduce --max-width"
        )
    result = Image.new("RGB", (width, height), background)
    y = padding
    for page in pages:
        result.paste(page, ((width - page.width) // 2, y))
        y += page.height + gap
    return result


def fit_max_dimension(image: Image.Image, max_dimension: int = 2048) -> Image.Image:
    """Shrink only when a side exceeds the limit; never upscale or crop."""
    width, height = image.size
    scale = min(1.0, max_dimension / width, max_dimension / height)
    if scale >= 1.0:
        return image
    return image.resize(
        (max(1, int(width * scale)), max(1, int(height * scale))),
        Image.Resampling.LANCZOS,
    )


def read_episodes(docs: Path) -> list[dict[str, Any]]:
    rows = json.loads((docs / "4komaData.json").read_text(encoding="utf-8-sig"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("4komaData.json must contain a nonempty episode array")
    seen = set()
    source = (docs / "4koma" / "ja").resolve()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Every episode must be an object")
        index = row.get("Index")
        valid_index = (type(index) is int and index >= 0) or (
            isinstance(index, str)
            and re.fullmatch(r"[A-Za-z0-9_-]+", index) is not None
        )
        if not valid_index or str(index) in seen:
            raise ValueError(f"Invalid or duplicate Index: {index!r}")
        seen.add(str(index))
        urls = row.get("ImagesUrl")
        if not isinstance(urls, list) or not urls:
            raise ValueError(f"Episode {index}: ImagesUrl must be a nonempty array")
        for url in urls:
            if not isinstance(url, str) or not url:
                raise ValueError(f"Episode {index}: invalid image path {url!r}")
            path = (source / url).resolve()
            if not path.is_relative_to(source) or not path.is_file():
                raise ValueError(
                    f"Episode {index}: missing or unsafe image path {url!r}"
                )
    return rows


def write_if_changed(path: Path, data: bytes) -> bool:
    if path.exists() and path.read_bytes() == data:
        return False
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)
    return True


def generate(
    docs: Path = DEFAULT_DOCS,
    *,
    trim: bool = True,
    threshold: int = 16,
    max_width: int = 1600,
    max_dimension: int = 2048,
    gap: int = 16,
    padding: int = 16,
    quality: int = 90,
) -> tuple[int, int]:
    if (
        max_width <= 2 * padding
        or max_width > 65500
        or not 1 <= max_dimension <= 65500
        or gap < 0
        or padding < 0
        or not 1 <= threshold <= 255
        or not 1 <= quality <= 100
    ):
        raise ValueError("Invalid width, gap, padding, threshold or quality")
    rows = read_episodes(docs)
    source = docs / "4koma" / "ja"
    output = source / "simple"
    output.mkdir(parents=True, exist_ok=True)
    simple = []
    changed = 0
    for row in rows:
        image = join_pages(
            [source / url for url in row["ImagesUrl"]],
            trim=trim,
            threshold=threshold,
            max_width=max_width,
            gap=gap,
            padding=padding,
        )
        image = fit_max_dimension(image, max_dimension)
        encoded = io.BytesIO()
        image.save(
            encoded,
            "JPEG",
            quality=quality,
            optimize=True,
            progressive=True,
            subsampling=0,
        )
        name = f"{row['Index']}.jpg"
        changed += write_if_changed(output / name, encoded.getvalue())
        simple.append({**row, "ImagesUrl": [f"./simple/{name}"]})
    write_if_changed(
        docs / "4komaDataSimple.json",
        (json.dumps(simple, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    return len(simple), changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=Path, default=DEFAULT_DOCS)
    parser.add_argument(
        "--no-trim", action="store_true", help="Keep all source margins/spacers"
    )
    parser.add_argument(
        "--threshold", type=int, default=16, help="Background tolerance (1-255)"
    )
    parser.add_argument(
        "--max-width", type=int, default=1600, help="Maximum width; never upscale"
    )
    parser.add_argument(
        "--max-dimension",
        type=int,
        default=2048,
        help="Maximum width and height in pixels; shrink only, never upscale",
    )
    parser.add_argument("--gap", type=int, default=16, help="Pixels between pages")
    parser.add_argument(
        "--padding", type=int, default=16, help="Outer padding in pixels"
    )
    parser.add_argument("--quality", type=int, default=90, help="JPEG quality (1-100)")
    args = parser.parse_args()
    try:
        count, changed = generate(
            args.docs,
            trim=not args.no_trim,
            threshold=args.threshold,
            max_width=args.max_width,
            max_dimension=args.max_dimension,
            gap=args.gap,
            padding=args.padding,
            quality=args.quality,
        )
    except (ValueError, OSError) as error:
        parser.exit(1, f"Generation failed: {error}\n")
    print(f"Generated {count} simple episodes ({changed} images changed).")


if __name__ == "__main__":
    main()
