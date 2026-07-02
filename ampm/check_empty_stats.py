#!/usr/bin/env python3
import argparse
import os
import shutil


def find_empty_stats(root_dir):
    empty_runs = []
    for entry in sorted(os.listdir(root_dir)):
        run_dir = os.path.join(root_dir, entry)
        stats_path = os.path.join(run_dir, "stats.txt")
        if os.path.isdir(run_dir) and os.path.exists(stats_path):
            try:
                if os.path.getsize(stats_path) == 0:
                    empty_runs.append(entry)
            except OSError:
                continue
    return empty_runs


def main():
    parser = argparse.ArgumentParser(
        description="Find simulation runs where stats.txt exists but is empty."
    )
    parser.add_argument(
        "results_dir",
        help="Path to the results folder containing simulation subdirectories.",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.results_dir):
        raise SystemExit(f"Error: '{args.results_dir}' is not a directory.")

    empty_runs = find_empty_stats(args.results_dir)

    if empty_runs:
        print("Empty stats.txt found in the following runs:")
        for run in empty_runs:
            print(run)
            # delete the run folder recursively
            run_dir = os.path.join(args.results_dir, run)
            # try:
            #     shutil.rmtree(run_dir)
            #     print(f"Deleted empty run directory: {run_dir}")
            # except OSError as e:
            #     print(f"Error deleting directory {run_dir}: {e}")
        raise SystemExit(1)

    print("No empty stats.txt files found.")


if __name__ == "__main__":
    main()
