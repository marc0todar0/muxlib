#!/usr/bin/env python3
import argparse
import os
import subprocess
from dotenv import load_dotenv
from single import get_single, get_single_info

load_dotenv()


def show_id3_tags(path):
    try:
        subprocess.run(["mid3v2", path], check=True)
    except FileNotFoundError:
        print(
            "mid3v2 not found, install python3-mutagen: sudo apt install python3-mutagen"
        )


def main():
    parser = argparse.ArgumentParser(description="Download YouTube audio as MP3")
    parser.add_argument("url", help="YouTube URL to download")
    parser.add_argument(
        "-o",
        "--output",
        default=os.getenv("SAVE_FOLDER", "./downloads/"),
        help="Output folder (default: SAVE_FOLDER env or ./downloads/)",
    )
    parser.add_argument(
        "--info-only",
        action="store_true",
        help="Only show yt-dlp metadata, don't download",
    )
    parser.add_argument(
        "--tags",
        action="store_true",
        help="Show ID3 tags of the downloaded file (mid3v2)",
    )
    args = parser.parse_args()

    if args.info_only:
        info = get_single_info(args.url)
        print(f"Title:     {info.title}")
        print(f"Artist:    {info.artist}")
        print(f"Album:     {info.album}")
        print(f"Date:      {info.date}")
        print(f"Thumbnail: {info.thumbnail}")
    else:
        os.makedirs(args.output, exist_ok=True)
        path = get_single(args.url, FOLDER=args.output, EXT=args.ext)
        print(f"\nSaved: {path}")
        if args.tags:
            print("\n--- ID3 tags ---")
            show_id3_tags(path)


if __name__ == "__main__":
    main()
