#!/usr/bin/env python3
"""Copy catalog images into simple/, resizing only above VRChat's 2048px limit."""

import argparse
import io
import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
DEFAULT_DOCS = ROOT
MAX_DIMENSION = 2048


def fit_max_dimension(
    image: Image.Image, max_dimension: int = MAX_DIMENSION
) -> Image.Image:
    """Shrink only when a side exceeds the limit; never upscale or crop."""
    result = image.copy()
    result.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return result


def image_bytes(path: Path, max_dimension: int, quality: int) -> bytes:
    with Image.open(path) as original:
        original.load()
        if max(original.size) <= max_dimension:
            return path.read_bytes()
        image = fit_max_dimension(ImageOps.exif_transpose(original), max_dimension)
        encoded = io.BytesIO()
        options: dict[str, Any] = {}
        if original.format == "JPEG":
            image = image.convert("RGB")
            options = {"quality": quality, "optimize": True, "subsampling": 0}
        image.save(encoded, original.format, **options)
        return encoded.getvalue()


def read_episodes(docs: Path) -> list[dict[str, Any]]:
    rows = json.loads((docs / "4komaData.json").read_text(encoding="utf-8-sig"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("4komaData.json must contain a nonempty episode array")
    seen = set()
    source = (docs / "4koma" / "ja").resolve()
    output = source / "simple"
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
            relative = Path(url)
            path = (source / relative).resolve()
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or "\\" in url
                or not path.is_relative_to(source)
                or path.is_relative_to(output)
                or not path.is_file()
            ):
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
    max_dimension: int = MAX_DIMENSION,
    quality: int = 95,
) -> tuple[int, int]:
    if not 1 <= max_dimension <= MAX_DIMENSION or not 1 <= quality <= 100:
        raise ValueError("Invalid maximum dimension (1-2048) or quality (1-100)")
    rows = read_episodes(docs)
    source = docs / "4koma" / "ja"
    output = source / "simple"
    if output.is_symlink() or any(p.is_symlink() for p in output.rglob("*")):
        raise ValueError("simple/ must not contain symlinks")
    simple = []
    paths: set[Path] = set()
    for row in rows:
        relatives = [Path(url) for url in row["ImagesUrl"]]
        paths.update(relatives)
        simple.append(
            {**row, "ImagesUrl": [f"./simple/{p.as_posix()}" for p in relatives]}
        )
    changed = 0
    # Prepare every image before touching the published catalog or removing old files.
    with TemporaryDirectory(prefix=".simple-", dir=docs) as temporary:
        staging = Path(temporary)
        for relative in sorted(paths):
            staged = staging / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(image_bytes(source / relative, max_dimension, quality))
        output.mkdir(parents=True, exist_ok=True)
        for relative in sorted(paths):
            target = output / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            changed += write_if_changed(target, (staging / relative).read_bytes())
        write_if_changed(
            docs / "4komaDataSimple.json",
            (json.dumps(simple, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
        for path in sorted(output.rglob("*"), reverse=True):
            if path.is_file() and path.relative_to(output) not in paths:
                path.unlink()
            elif path.is_dir() and not any(path.iterdir()):
                path.rmdir()
    return len(simple), changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=Path, default=DEFAULT_DOCS)
    parser.add_argument(
        "--max-dimension",
        type=int,
        default=MAX_DIMENSION,
        help="Maximum width and height (1-2048); never upscale",
    )
    parser.add_argument(
        "--quality", type=int, default=95, help="Resized JPEG quality (1-100)"
    )
    args = parser.parse_args()
    try:
        count, changed = generate(
            args.docs,
            max_dimension=args.max_dimension,
            quality=args.quality,
        )
    except (ValueError, OSError) as error:
        parser.exit(1, f"Generation failed: {error}\n")
    print(f"Generated {count} simple catalog entries ({changed} images changed).")


if __name__ == "__main__":
    main()
