import os
import json
import hashlib
import datetime
from startup import load_config, log_event, explain

CONFIG_PATH = "D:/Interpolbility/config.json"
BASELINE_PATH = "D:/Interpolbility/baseline_hashes.json"
LOG_FILE = "D:/Interpolbility/logs/interpolbility.log"

# Terminal color codes
class Color:
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    RESET  = "\033[0m"
    BOLD   = "\033[1m"

def colorize(text, color):
    return f"{color}{text}{Color.RESET}"


def hash_file(filepath):
    try:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except (PermissionError, FileNotFoundError):
        return None


def run_diff(filepath, new_content, config):
    verbose = config["user_profile"]["verbose_mode"]

    print("\n" + "="*60)
    print(colorize("  DIFF — What the agent was trying to write", Color.BOLD))
    print("="*60)

    if verbose:
        explain("WHAT: A diff shows you the exact changes the agent was attempting to make.", config)
        explain("WHERE: Comparing what exists on disk now vs what the agent wanted to write.", config)
        explain("WHY: Lines marked in green (+) are being added. Lines marked in red (-) are being removed. Unchanged lines are shown in white.", config)

    # Read existing file if it exists
    existing_lines = []
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", errors="replace") as f:
                existing_lines = f.readlines()
        except Exception:
            existing_lines = []

    new_lines = new_content.splitlines(keepends=True) if new_content else []

    # Side by side header
    col_width = 55
    print(f"\n  {'CURRENT FILE':<{col_width}} {'AGENT WANTS TO WRITE':<{col_width}}")
    print(f"  {'-'*col_width} {'-'*col_width}")

    max_lines = max(len(existing_lines), len(new_lines))

    if max_lines == 0:
        print(colorize("\n  No content to compare. File does not exist yet and no new content provided.", Color.YELLOW))
    else:
        for i in range(max_lines):
            old_line = existing_lines[i].rstrip() if i < len(existing_lines) else ""
            new_line = new_lines[i].rstrip() if i < len(new_lines) else ""

            if old_line == new_line:
                left  = f"  {old_line:<{col_width}}"
                right = f" {new_line:<{col_width}}"
                print(colorize(left, Color.WHITE) + colorize(right, Color.WHITE))
            elif old_line and not new_line:
                left  = f"- {old_line:<{col_width}}"
                right = f" {'(removed)':<{col_width}}"
                print(colorize(left, Color.RED) + colorize(right, Color.RED))
            elif new_line and not old_line:
                left  = f"  {'(new file)':<{col_width}}"
                right = f"+ {new_line:<{col_width}}"
                print(colorize(left, Color.WHITE) + colorize(right, Color.GREEN))
            else:
                left  = f"- {old_line:<{col_width}}"
                right = f"+ {new_line:<{col_width}}"
                print(colorize(left, Color.RED) + colorize(right, Color.GREEN))

    print()
    log_event(f"DIFF reviewed for: {filepath}")


def run_hash_check(filepath, config):
    verbose = config["user_profile"]["verbose_mode"]

    print("\n" + "="*60)
    print(colorize("  HASH CHECK — File integrity verification", Color.BOLD))
    print("="*60)

    if verbose:
        explain("WHAT: Generating a SHA-256 fingerprint of the current file and comparing it to the baseline recorded at startup.", config)
        explain("WHERE: Baseline stored at: " + BASELINE_PATH, config)
        explain("WHY: If a single byte of the file has changed since the baseline was recorded, the hash will be completely different. A mismatch means the file was modified.", config)

    # Load baseline
    if not os.path.exists(BASELINE_PATH):
        print(colorize("\n  No baseline found. Cannot perform hash check.", Color.YELLOW))
        explain("WHY: The baseline is built during startup. If it's missing, restart Interpolbility to rebuild it.", config)
        log_event(f"HASH CHECK failed — no baseline found for: {filepath}")
        return

    with open(BASELINE_PATH, "r") as f:
        baseline = json.load(f)

    filepath_clean = os.path.abspath(filepath).replace("\\", "/")

    # Get baseline hash
    baseline_entry = baseline.get(filepath_clean)
    baseline_hash = baseline_entry["hash"] if baseline_entry else None
    baseline_time = baseline_entry["recorded_at"] if baseline_entry else None

    # Get current hash
    current_hash = hash_file(filepath_clean)
    current_time = datetime.datetime.now().isoformat()

    print(f"\n  File: {filepath_clean}")

    if not current_hash:
        print(colorize("\n  File does not exist on disk yet.", Color.YELLOW))
        print("  This is a new file the agent is attempting to create.")
        log_event(f"HASH CHECK — file does not exist yet: {filepath_clean}")
        return

    if not baseline_hash:
        print(colorize("\n  This file is not in the baseline.", Color.YELLOW))
        if verbose:
            print("\n  This means the file was created after the baseline was recorded.")
            print("  It may be a new legitimate file or something the agent created without authorization.")
        log_event(f"HASH CHECK — file not in baseline: {filepath_clean}")
    elif current_hash == baseline_hash:
        print(colorize("\n  MATCH — File is clean.", Color.GREEN))
        print(f"\n  Baseline hash:  {baseline_hash}")
        print(f"  Current hash:   {current_hash}")
        print(f"  Baseline taken: {baseline_time}")
        if verbose:
            explain("The file has not been modified since the baseline was recorded. It is safe.", config)
        log_event(f"HASH CHECK PASSED for: {filepath_clean}")
    else:
        print(colorize("\n  MISMATCH — File has been modified.", Color.RED))
        print(f"\n  Baseline hash:  {colorize(baseline_hash, Color.GREEN)}")
        print(f"  Current hash:   {colorize(current_hash, Color.RED)}")
        print(f"  Baseline taken: {baseline_time}")
        print(f"  Checked at:     {current_time}")

        if verbose:
            explain("WHAT: The file's current fingerprint does not match the one recorded at startup.", config)
            explain("WHY: This means the file was changed after Interpolbility started. This could be legitimate or it could indicate unauthorized modification.", config)

        log_event(f"HASH MISMATCH detected for: {filepath_clean}")

        # Prompt to explore further
        explore = input(colorize("\n  Would you like me to explore this further? (y/n): ", Color.YELLOW)).strip().lower()
        if explore == "y":
            explore_mismatch(filepath_clean, baseline_hash, current_hash, baseline_time, current_time, config)
        else:
            print("\n  [Interpolbility] Noted. Mismatch logged. You can review it in the activity log.")
            log_event(f"User declined further exploration of mismatch: {filepath_clean}")


def explore_mismatch(filepath, baseline_hash, current_hash, baseline_time, current_time, config):
    verbose = config["user_profile"]["verbose_mode"]

    print("\n" + "="*60)
    print(colorize("  MISMATCH DETAILS", Color.BOLD))
    print("="*60)

    print(f"\n  Affected file:  {filepath}")
    print(f"\n  {'BASELINE':<35} {'CURRENT':<35}")
    print(f"  {'-'*35} {'-'*35}")
    print(f"  {colorize(baseline_hash[:32], Color.GREEN)+'...':<35} {colorize(current_hash[:32], Color.RED)+'...':<35}")
    print(f"  Recorded: {baseline_time}")
    print(f"  Checked:  {current_time}")

    if verbose:
        explain("WHAT: The two hashes above represent the file at two different points in time.", config)
        explain("WHY: The difference tells you something changed the file between when the baseline was recorded and now. The timestamps help narrow down when it happened.", config)

    print(colorize("\n  This file is flagged as a potential unauthorized modification.", Color.RED))
    print("\n  Recommended actions:")
    print("    [1] Review the file manually at: " + filepath)
    print("    [2] Rebuild the baseline if you made legitimate changes")
    print("    [3] Report the file as compromised and do not use it")

    log_event(f"MISMATCH EXPLORED — user reviewed details for: {filepath}")


def run_log_review(filepath, config):
    verbose = config["user_profile"]["verbose_mode"]

    print("\n" + "="*60)
    print(colorize("  LOG REVIEW — Activity related to this file", Color.BOLD))
    print("="*60)

    if verbose:
        explain("WHAT: Searching the session log for every entry related to this specific file.", config)
        explain("WHERE: Reading from: " + LOG_FILE, config)
        explain("WHY: This shows you the full history of what Interpolbility has seen regarding this file during this session — every write attempt, block, allow, and check.", config)

    filepath_clean = os.path.abspath(filepath).replace("\\", "/")
    filename = os.path.basename(filepath_clean)

    if not os.path.exists(LOG_FILE):
        print(colorize("\n  No session log found.", Color.YELLOW))
        log_event(f"LOG REVIEW attempted but no log file found for: {filepath_clean}")
        return

    with open(LOG_FILE, "r") as f:
        all_entries = f.readlines()

    # Filter entries related to this file
    related = [e.strip() for e in all_entries if filepath_clean in e or filename in e]

    if not related:
        print(colorize(f"\n  No log entries found for: {filepath_clean}", Color.YELLOW))
        print("  This file has not been seen before this alert.")
    else:
        print(f"\n  Found {len(related)} log entry/entries for this file:\n")
        for entry in related:
            # Color code by event type
            if "BLOCKED" in entry:
                print(colorize("  " + entry, Color.RED))
            elif "ALLOWED" in entry:
                print(colorize("  " + entry, Color.GREEN))
            elif "MISMATCH" in entry or "FLAGGED" in entry:
                print(colorize("  " + entry, Color.YELLOW))
            else:
                print(colorize("  " + entry, Color.WHITE))

    log_event(f"LOG REVIEW completed for: {filepath_clean}")

    # Offer full log save
    print()
    save_full = input(colorize("  Would you like to save the full session log as well? (y/n): ", Color.CYAN)).strip().lower()
    if save_full == "y":
        save_path = f"D:/Interpolbility/logs/session_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(save_path, "w") as f:
            f.writelines(all_entries)
        print(f"\n  [Interpolbility] Full session log saved to: {save_path}")
        log_event(f"Full session log exported to: {save_path}")
    else:
        print("\n  [Interpolbility] Full log not saved. All entries remain in the active log.")
        log_event(f"User declined full log export during review of: {filepath_clean}")


if __name__ == "__main__":
    config = load_config()

    print("\n  Running Layer 3 demo...\n")

    # Demo diff
    print("  TEST 1: Diff — comparing existing file vs new content")
    run_diff(
        "D:/Interpolbility/config.json",
        '{\n  "project_name": "Interpolbility",\n  "malicious_key": "INJECTED_CONTENT"\n}',
        config
    )

    # Demo hash check — clean file
    print("\n  TEST 2: Hash check — clean file")
    run_hash_check("D:/Interpolbility/config.json", config)

    # Demo log review
    print("\n  TEST 3: Log review — entries for startup.py")
    run_log_review("D:/Interpolbility/startup.py", config)
