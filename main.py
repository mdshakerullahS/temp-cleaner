import os
import platform
import time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse


SYSTEM_TEMP_PATHS = {
    "Windows": [
        lambda: os.environ.get("TEMP"),
        lambda: os.environ.get("TMP"),
        lambda: os.environ["WINDIR"] + "\\Temp",
    ],
    "Linux": [
        lambda: "/tmp",
        lambda: "/var/tmp",
    ],
    "Darwin": [
        lambda: os.environ.get("TMPDIR"),
        lambda: "/tmp",
        lambda: "/private/tmp",
    ],
}


def create_log(message: str):
    with open("log.txt", "a", encoding="utf-8") as log:
        log.write(message + "\n")


def create_cleanup_summary(start_time: datetime, stats: dict[str, int]):
    end_time = datetime.now()
    duration = end_time - start_time

    summary = f"""
----- CLEANUP SUMMARY -----
Start Time : {start_time.strftime("%Y-%m-%d %H:%M:%S")}
End Time   : {end_time.strftime("%Y-%m-%d %H:%M:%S")}
Duration   : {duration}

Files Scanned : {stats['scanned']} ({format_bytes(stats['total_size_scanned'])})
Old Files     : {stats['old']}
Deleted       : {stats['deleted']}
Skipped       : {stats['skipped']}
Failed        : {stats['failed']}
Freed Space   : {format_bytes(stats['freed_space'])}
---------------------------
"""

    return summary


def format_bytes(size: float):
    if size == 0:
        return "0.00 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def scan_directory(folder: str):
    stack = [folder]

    while stack:
        current = stack.pop()

        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    if entry.is_file(follow_symlinks=False):
                        yield entry

                    elif entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)

        except PermissionError:
            continue


def process_file(
    entry: os.DirEntry, now: float, seconds_threshold: float, dry_run: bool
):
    try:
        stat = entry.stat()
        age = now - stat.st_mtime
        size = stat.st_size

        if age > seconds_threshold:
            if dry_run:
                return (
                    "old",
                    entry.path,
                    size,
                    f"[DRY RUN] Would delete: {entry.path}",
                )

            else:
                return ("old", entry.path, size, None)

        return None
    except Exception as e:
        return ("failed", entry.path, 0, f"[ERROR] {entry.path}: {e}")


def remove_empty_dirs(folders: list[str]):
    for folder in folders:
        path = Path(folder)

        if not path.exists():
            continue

        for p in sorted(path.rglob("*"), reverse=True):
            try:
                if p.is_dir() and not any(p.iterdir()):
                    p.rmdir()
                    msg = f"[REMOVED EMPTY DIR] {p}"
                    print(msg)
                    create_log(msg)
            except Exception:
                pass


def clean_folders_concurrently(
    stats: dict[str, int],
    folders: list[str],
    days_threshold: int,
    dry_run: bool = True,
    workers: int = 10,
):
    seconds_threshold = days_threshold * 86400
    now = time.time()

    mode_label = "DRY RUN" if dry_run else "CLEANUP"
    print(f"\n--- Starting {mode_label} ---")

    files_to_process: list[tuple[Path, int]] = []

    def file_generator():
        for folder in folders:
            if Path(folder).exists():
                for file in scan_directory(folder):
                    yield file

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for result in executor.map(
            lambda f: process_file(f, now, seconds_threshold, dry_run),
            file_generator(),
            chunksize=50,
        ):
            stats["scanned"] += 1

            if result is None:
                continue

            status, file, size, message = result
            stats["total_size_scanned"] += size

            if status == "old":
                stats["old"] += 1
                files_to_process.append((Path(file), size))
                if message:
                    print(message)

            elif status == "failed":
                stats["failed"] += 1
                if message:
                    print(message)
                    create_log(message)

    unit = "days" if days_threshold > 1 else "day"
    print(f"\nFiles older than {days_threshold} {unit}: {stats['old']}")

    if not files_to_process:
        print("No files to delete.")
        return

    if dry_run:
        confirm = input("Delete these files? (Y/N): ")
        if confirm.lower() != "y":
            print("Cleanup cancelled.")
            return

    start_time = datetime.now()
    print(f"\n--- CLEANUP STARTED {start_time} ---")
    create_log(f"\n--- CLEANUP STARTED {start_time} ---")

    for file, size in files_to_process:
        try:
            file.unlink()
            stats["deleted"] += 1
            stats["freed_space"] += size
            msg = f"[DELETED] {file}"

        except PermissionError:
            stats["skipped"] += 1
            msg = f"[SKIPPED] {file} (In use)"

        except Exception as e:
            stats["failed"] += 1
            msg = f"[FAILED] {file}: {e}"

        print(msg)
        create_log(msg)

    summary = create_cleanup_summary(start_time, stats)
    print(summary)
    create_log(summary)

    remove_empty_dirs(folders)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Clean old files from system temporary directories."
    )

    parser.add_argument(
        "--days",
        type=float,
        default=3,
        help="Delete files older than this many days (default: 3)",
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Delete files without confirmation",
    )

    parser.add_argument(
        "--folder",
        action="append",
        help="Add custom folder(s) to clean",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of concurrent threads (default: 10)",
    )

    return parser.parse_args()


def get_default_temp_paths():
    system = platform.system()

    path_providers = SYSTEM_TEMP_PATHS.get(system, [])

    paths = []
    for provider in path_providers:
        val = provider()
        if val:
            p = Path(val)
            if p.exists():
                paths.append(str(p))
    return paths


def main():
    stats = {
        "scanned": 0,
        "total_size_scanned": 0,
        "old": 0,
        "deleted": 0,
        "skipped": 0,
        "failed": 0,
        "freed_space": 0,
    }

    args = parse_arguments()

    default_folders = get_default_temp_paths()

    folders = args.folder if args.folder else default_folders
    if not folders:
        print("No valid directories found to clean.")
        return

    for f in folders:
        p = Path(f).resolve()
        if p == p.anchor:
            print(f"Refusing to clean root directory: {p}")
            return

    print(f"Cleaning {len(folders)} directories on {platform.system()}...")

    clean_folders_concurrently(
        stats,
        folders=folders,
        days_threshold=args.days,
        dry_run=not args.auto,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
