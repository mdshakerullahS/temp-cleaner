# Cross-Platform Temp Cleaner (Python)

A Python utility to scan and clean **system temporary directories** on Windows, Linux, and macOS.

It performs a **safe dry run by default**, shows which files would be deleted, tracks total size scanned, and asks for confirmation before actually removing anything. The script also logs cleanup activity and reports how much disk space was freed. It includes safety checks to prevent cleaning the root directory.

---

# Features

- Detects and cleans **system temp folders** on Windows, Linux, and macOS
- Recursively scans directories and tracks **total size scanned**
- Deletes files older than a configurable number of days
- **Dry run mode by default** (preview deletions safely)
- Concurrent file processing for faster cleanup
- Generates **cleanup summary** with counts and disk space freed
- Removes empty directories after cleanup
- Handles locked or inaccessible files gracefully
- **Prevents accidental cleaning of root directories**
- Logs all actions to `log.txt`

---

# Default Folders Cleaned

By default, the script detects system temporary directories for your OS:

- **Windows**: `%TEMP%`, `%TMP%`, `C:\Windows\Temp`
- **Linux**: `/tmp`, `/var/tmp`
- **macOS**: `$TMPDIR`, `/tmp`, `/private/tmp`

You can also provide **custom folders** with the `--folder` option.

---

# Requirements

- Python **3.10+**

No external dependencies are required. The script uses only Python’s **standard library**.

---

# Installation

Clone the repository:

```bash
git clone https://github.com/mdshakerullahS/temp-cleaner.git
```

Move into the project directory:

```bash
cd temp-cleaner
```

---

# Usage

Run the script:

```bash
python main.py
```

By default, the script will:

- Detect system temp directories based on your OS
- Scan temp folders recursively
- Track total size scanned
- Find files older than **3 days**
- Run in **dry run mode**
- Ask for confirmation before deleting anything
- Refuse to clean the **root directory** for safety

---

# How It Works

1. Detects system temporary directories based on the OS (Windows, Linux, macOS).
2. Recursively scans directories using `os.scandir`.
3. Calculates file age using the last modification timestamp.
4. Tracks **total size scanned** and identifies old files.
5. Uses `ThreadPoolExecutor` for concurrent file processing.
6. Performs deletion after confirmation (unless `--auto` is used).
7. Logs results and prints a cleanup summary.
8. Removes empty directories after files are deleted.
9. **Skips cleaning the root directory** to avoid catastrophic deletion.

---

# Command Line Options

## Set File Age Threshold

Delete files older than a specific number of days.

```bash
python main.py --days 7
```

---

## Skip Confirmation (Automatic Cleanup)

```bash
python main.py --auto
```

This deletes files immediately without asking for confirmation.

---

## Clean Custom Folder

Provide additional folders to clean.

```bash
python main.py --folder "D:/temp"
```

Multiple folders can be added:

```bash
python main.py --folder "D:/temp" --folder "E:/cache"
```

---

## Control Concurrency

Control the number of worker threads.

```bash
python main.py --workers 20
```

Default value:

```
10
```

---

# Example

```bash
python main.py --days 5 --auto
```

This command will:

- Delete files older than **5 days**
- Run cleanup **without confirmation**

---

# Example Output

```
--- Starting DRY RUN ---
Files scanned: 5241 (2.15GB)

[DRY RUN] Would delete: C:\Temp\a.tmp
[DRY RUN] Would delete: C:\Temp\b.log

Files older than 5 days: 245

Delete these files? (Y/N):
```

After cleanup:

```
--- CLEANUP STARTED 2026-03-10 10:12:34 ---
[DELETED] C:\Temp\a.tmp
[DELETED] C:\Temp\b.log

----- CLEANUP SUMMARY -----
Start Time : 2026-03-10 10:12:31
End Time   : 2026-03-10 10:12:38
Duration   : 0:00:07

Files Scanned : 5241 (2.15 GB)
Old Files     : 245
Deleted       : 240
Skipped       : 3
Failed        : 2
Freed Space   : 1.43 GB
---------------------------
```

---

# Logging

Cleanup activity is saved to:

```
log.txt
```

The log includes:

- Deleted files
- Skipped files
- Errors
- Cleanup summaries

---

# License

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute this software with proper attribution.

---

# Author

**Md Shakerullah Sourov**\
<small>Full-Stack Web Developer</small>

- LinkedIn: https://linkedin.com/in/mdshakerullah

- Email: sourovmdshakerullah@gmail.com

---

# Why This Script Exists

Temporary folders can silently grow to **several gigabytes** over time. This script provides a safe and simple way to periodically clean them while still allowing you to preview changes before deleting anything.
