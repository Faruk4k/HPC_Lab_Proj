#!/usr/bin/env python3
import argparse
import os
import shutil


def find_amt_dirs(root_dir, keyword="amt"):
    matches = []
    for entry in sorted(os.listdir(root_dir)):
        path = os.path.join(root_dir, entry)
        if os.path.isdir(path) and keyword.lower() in entry.lower():
            matches.append(path)
    return matches


def main():
    parser = argparse.ArgumentParser(
        description="Delete directories whose names contain a keyword (default: amt)."
    )
    parser.add_argument("root_dir", help="Root folder to scan for matching directories.")
    parser.add_argument(
        "--keyword",
        default="ls64_l2",
        help="Keyword to match in directory names (case-insensitive).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show matching directories without deleting them.",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.root_dir):
        raise SystemExit(f"Error: '{args.root_dir}' is not a directory.")

    matches = find_amt_dirs(args.root_dir, keyword=args.keyword)
    if not matches:
        print(f"No directories found containing '{args.keyword}'.")
        return

    print("Matching directories:")
    for path in matches:
        print(path)

    if args.dry_run:
        print("\nDry run only; no directories were deleted.")
        return

    for path in matches:
        shutil.rmtree(path)
        print(f"Deleted: {path}")


if __name__ == "__main__":
    main()
