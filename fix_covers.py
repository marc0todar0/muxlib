#!/usr/bin/env python3
"""Crop non-square embedded cover art to center-square in all MP3s under a directory."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from mutagen.id3 import APIC, ID3, error as ID3Error


def get_image_dimensions(data: bytes) -> tuple[int, int] | None:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(data)
        tmp = f.name
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0",
                tmp,
            ],
            capture_output=True,
            text=True,
        )
        parts = result.stdout.strip().split(",")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except Exception:
        pass
    finally:
        os.unlink(tmp)
    return None


def crop_to_square(data: bytes) -> bytes | None:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f_in:
        f_in.write(data)
        tmp_in = f_in.name
    tmp_out = tmp_in + "_sq.jpg"
    try:
        subprocess.run(
            ["ffmpeg", "-i", tmp_in, "-vf", "crop=ih:ih", "-y", tmp_out],
            capture_output=True,
            check=True,
        )
        with open(tmp_out, "rb") as f:
            return f.read()
    except subprocess.CalledProcessError:
        return None
    finally:
        os.unlink(tmp_in)
        if os.path.exists(tmp_out):
            os.unlink(tmp_out)


def fix_mp3(path: Path, dry_run: bool) -> str:
    try:
        tags = ID3(path)
    except ID3Error as e:
        return f"skip (no tags: {e})"

    apic_keys = [k for k in tags if k.startswith("APIC")]
    if not apic_keys:
        return "skip (no cover)"

    apic: APIC = tags[apic_keys[0]]
    dims = get_image_dimensions(apic.data)
    if dims is None:
        return "skip (unreadable image)"

    w, h = dims
    if w == h:
        return f"ok ({w}x{h})"

    if dry_run:
        return f"would fix {w}x{h}"

    new_data = crop_to_square(apic.data)
    if new_data is None:
        return f"error cropping {w}x{h}"

    tags[apic_keys[0]] = APIC(
        encoding=apic.encoding,
        mime="image/jpeg",
        type=apic.type,
        desc=apic.desc,
        data=new_data,
    )
    tags.save()
    size = min(w, h)
    return f"fixed {w}x{h} -> {size}x{size}"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="Root directory to scan recursively")
    parser.add_argument("--dry-run", action="store_true", help="Report without modifying files")
    args = parser.parse_args()

    root = Path(args.directory)
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        sys.exit(1)

    mp3s = sorted(root.rglob("*.mp3"))
    if not mp3s:
        print("No MP3 files found.")
        return

    fixed = skipped = errors = 0
    for mp3 in mp3s:
        result = fix_mp3(mp3, args.dry_run)
        status = result.split()[0]
        print(f"[{status}] {mp3.name}: {result}")
        if status == "fixed":
            fixed += 1
        elif status in ("ok", "skip"):
            skipped += 1
        else:
            errors += 1

    label = "would fix" if args.dry_run else "fixed"
    print(f"\nDone: {label} {fixed}, skipped {skipped}, errors {errors} / {len(mp3s)} files")


if __name__ == "__main__":
    main()
