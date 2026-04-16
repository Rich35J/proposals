import os
import json
import re
import datetime
from startup import load_config, log_event, explain

CONFIG_PATH = "D:/Interpolbility/config.json"
ALERTS_PATH = "D:/Interpolbility/logs/alerts.json"
PENDING_PATH = "D:/Interpolbility/logs/pending_holds.json"

# Credential patterns to scan for in file content
CREDENTIAL_PATTERNS = [
    (r"(?i)api[_\-\s]?key\s*=\s*['\"]?[A-Za-z0-9\-_]{16,}", "API Key"),
    (r"(?i)secret[_\-\s]?key\s*=\s*['\"]?[A-Za-z0-9\-_]{16,}", "Secret Key"),
    (r"(?i)token\s*=\s*['\"]?[A-Za-z0-9\-_\.]{16,}", "Token"),
    (r"(?i)password\s*=\s*['\"]?.{6,}", "Password"),
    (r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----", "Private Key"),
    (r"(?i)authorization:\s*bearer\s+[A-Za-z0-9\-_\.]+", "Bearer Token"),
    (r"(?i)aws_access_key_id\s*=\s*[A-Z0-9]{20}", "AWS Access Key"),
    (r"(?i)aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}", "AWS Secret Key"),
]


def is_path_allowed(filepath, config):
    filepath = os.path.abspath(filepath).replace("\\", "/")
    allowed = [os.path.abspath(d).replace("\\", "/") for d in config["allowed_directories"]]
    for allowed_dir in allowed:
        if filepath.startswith(allowed_dir):
            return True
    return False


def is_path_protected(filepath, config):
    filepath = os.path.abspath(filepath).replace("\\", "/")
    protected = [os.path.abspath(d).replace("\\", "/") for d in config["protected_directories"]]
    for protected_dir in protected:
        if filepath.startswith(protected_dir):
            return True
    for protected_file in config["protected_files"]:
        if filepath.endswith(protected_file):
            return True
    for ext in config["protected_extensions"]:
        if filepath.endswith(ext):
            return True
    return False


def scan_content(content):
    findings = []
    for pattern, label in CREDENTIAL_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            findings.append({
                "type": label,
                "count": len(matches)
            })
    return findings


def save_alert(alert):
    alerts = []
    if os.path.exists(ALERTS_PATH):
        with open(ALERTS_PATH, "r") as f:
            alerts = json.load(f)
    alerts.append(alert)
    os.makedirs(os.path.dirname(ALERTS_PATH), exist_ok=True)
    with open(ALERTS_PATH, "w") as f:
        json.dump(alerts, f, indent=2)


def save_pending_hold(hold):
    holds = []
    if os.path.exists(PENDING_PATH):
        with open(PENDING_PATH, "r") as f:
            holds = json.load(f)
    holds.append(hold)
    os.makedirs(os.path.dirname(PENDING_PATH), exist_ok=True)
    with open(PENDING_PATH, "w") as f:
        json.dump(holds, f, indent=2)


def clear_pending_holds():
    if os.path.exists(PENDING_PATH):
        os.remove(PENDING_PATH)


def get_pending_holds():
    if os.path.exists(PENDING_PATH):
        with open(PENDING_PATH, "r") as f:
            return json.load(f)
    return []


def present_alert_options(filepath, reason, findings, config):
    verbose = config["user_profile"]["verbose_mode"]

    print("\n" + "!"*60)
    print("  INTERPOLBILITY ALERT")
    print("!"*60)
    print(f"\n  Blocked write attempt to: {filepath}")
    print(f"  Reason: {reason}")

    if findings:
        print("\n  Suspicious content detected:")
        for f in findings:
            print(f"    - {f['type']} ({f['count']} instance(s) found)")

    print("\n  What would you like to do?")
    print("\n    [1] Diff    — show exactly what the agent was trying to write")
    print("    [2] Hash    — compare current file state against the baseline")
    print("    [3] Log     — review the full activity log for this session")
    print("    [4] Allow   — permit this write and continue")
    print("    [5] Block   — deny this write and continue")

    if verbose:
        print("\n  Need help deciding? Here's what each option means:")
        print("\n    Diff:  Shows you a before/after comparison of the file.")
        print("           Use this if you want to see exactly what changed or")
        print("           what the agent was trying to add.")
        print("\n    Hash:  Generates a fingerprint of the current file and")
        print("           compares it to the baseline taken at startup.")
        print("           Use this to verify whether the file has already")
        print("           been modified without your knowledge.")
        print("\n    Log:   Opens the full session activity log.")
        print("           Use this to see everything the agent has done")
        print("           since startup, not just this one event.")
        print("\n    Allow: Permits this specific write to go through.")
        print("           Use this if you reviewed it and it looks clean.")
        print("\n    Block: Denies this write completely.")
        print("           Use this if anything looks suspicious.")

        ask = input("\n  Do you need me to explain any of these further before deciding? (y/n): ").strip().lower()
        if ask == "y":
            print("\n  Type the name of the option you want explained more (diff/hash/log/allow/block):")
            detail = input("  > ").strip().lower()
            explain_option_detail(detail)

    while True:
        choice = input("\n  Enter your choice (1-5): ").strip()
        if choice in ["1", "2", "3", "4", "5"]:
            return choice
        print("  Please enter a number between 1 and 5.")


def explain_option_detail(option):
    details = {
        "diff": (
            "\n  A diff shows you the difference between two versions of a file."
            "\n  Think of it like track changes in a Word document."
            "\n  Lines marked with + were being added. Lines marked with - were being removed."
            "\n  If you see credentials, system paths, or anything unexpected — block it."
        ),
        "hash": (
            "\n  A hash is a unique fingerprint of a file's contents."
            "\n  SHA-256 produces a 64-character string. Change one byte in the file"
            "\n  and the entire hash changes. If the current hash matches the baseline,"
            "\n  the file hasn't been touched. If it doesn't match, something changed it."
        ),
        "log": (
            "\n  The activity log records everything Interpolbility has seen this session."
            "\n  Every write attempt, every block, every user decision — timestamped."
            "\n  Use it to understand the full picture, not just this one event."
        ),
        "allow": (
            "\n  Allowing a write tells Interpolbility to let this specific operation through."
            "\n  It will still be logged. You can review it later."
            "\n  Only allow if you have reviewed the content and destination and are confident it's safe."
        ),
        "block": (
            "\n  Blocking a write cancels the operation completely."
            "\n  The file will not be created or modified."
            "\n  The attempt will be logged with a full record of what was blocked and why."
        ),
    }
    print(details.get(option, "\n  Option not recognized. Please type: diff, hash, log, allow, or block."))


def check_write(filepath, content="", config=None):
    if config is None:
        config = load_config()

    yolo_mode = config.get("yolo_mode", False)
    timestamp = datetime.datetime.now().isoformat()
    filepath_clean = os.path.abspath(filepath).replace("\\", "/")

    # Stage 1 — Destination check
    if is_path_protected(filepath_clean, config):
        reason = "Destination is a protected directory or file type"
        log_event(f"BLOCKED write to protected path: {filepath_clean} | Reason: {reason}")

        alert = {
            "timestamp": timestamp,
            "filepath": filepath_clean,
            "reason": reason,
            "findings": [],
            "mode": "YOLO" if yolo_mode else "NORMAL",
            "outcome": "BLOCKED"
        }

        if yolo_mode:
            print(f"\n  [YOLO MODE] Write to protected path attempted: {filepath_clean}")
            print(f"  [YOLO MODE] Blocked automatically. Logged for your review on next startup.")
            alert["outcome"] = "BLOCKED_YOLO"
            save_alert(alert)
            save_pending_hold(alert)
            return False

        save_alert(alert)
        choice = present_alert_options(filepath_clean, reason, [], config)
        return handle_user_choice(choice, filepath_clean, content, alert, config)

    # Stage 2 — Content check
    if content:
        findings = scan_content(content)
        if findings:
            reason = "Suspicious credential patterns detected in file content"
            log_event(f"FLAGGED content write to: {filepath_clean} | Findings: {[f['type'] for f in findings]}")

            alert = {
                "timestamp": timestamp,
                "filepath": filepath_clean,
                "reason": reason,
                "findings": findings,
                "mode": "YOLO" if yolo_mode else "NORMAL",
                "outcome": "PENDING"
            }

            if yolo_mode:
                print(f"\n  [YOLO MODE] Suspicious content detected in write to: {filepath_clean}")
                print(f"  [YOLO MODE] Allowed through. Logged for your review on next startup.")
                alert["outcome"] = "ALLOWED_YOLO"
                save_alert(alert)
                save_pending_hold(alert)
                return True

            save_alert(alert)
            choice = present_alert_options(filepath_clean, reason, findings, config)
            return handle_user_choice(choice, filepath_clean, content, alert, config)

    # Clean write
    log_event(f"ALLOWED write to: {filepath_clean}")
    return True


def handle_user_choice(choice, filepath, content, alert, config):
    if choice == "1":
        print("\n  --- DIFF ---")
        if content:
            print(f"\n  Agent was attempting to write the following to {filepath}:\n")
            for i, line in enumerate(content.splitlines(), 1):
                print(f"  + {line}")
        else:
            print("  No content provided for diff.")
        alert["outcome"] = "DIFF_REVIEWED"
        log_event(f"User reviewed diff for: {filepath}")
        return handle_user_choice(
            present_alert_options(filepath, alert["reason"], alert["findings"], config),
            filepath, content, alert, config
        )

    elif choice == "2":
        from layer3 import run_hash_check
        run_hash_check(filepath, config)
        alert["outcome"] = "HASH_CHECKED"
        log_event(f"User ran hash check for: {filepath}")
        return handle_user_choice(
            present_alert_options(filepath, alert["reason"], alert["findings"], config),
            filepath, content, alert, config
        )

    elif choice == "3":
        log_file = "D:/Interpolbility/logs/interpolbility.log"
        print(f"\n  --- SESSION LOG ---\n")
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                print(f.read())
        else:
            print("  No log entries found for this session.")
        alert["outcome"] = "LOG_REVIEWED"
        log_event(f"User reviewed session log during alert for: {filepath}")
        return handle_user_choice(
            present_alert_options(filepath, alert["reason"], alert["findings"], config),
            filepath, content, alert, config
        )

    elif choice == "4":
        alert["outcome"] = "ALLOWED_BY_USER"
        log_event(f"ALLOWED by user decision: {filepath}")
        save_alert(alert)
        print(f"\n  [Interpolbility] Write allowed. Logged.")
        return True

    elif choice == "5":
        alert["outcome"] = "BLOCKED_BY_USER"
        log_event(f"BLOCKED by user decision: {filepath}")
        save_alert(alert)
        print(f"\n  [Interpolbility] Write blocked. Logged.")
        return False


def review_pending_holds(config):
    holds = get_pending_holds()
    if not holds:
        return

    print("\n" + "="*60)
    print("  INTERPOLBILITY — YOLO MODE SUMMARY")
    print("="*60)
    print(f"\n  {len(holds)} operation(s) were processed while you were away:\n")

    for i, hold in enumerate(holds, 1):
        print(f"  [{i}] {hold['timestamp']}")
        print(f"       File:    {hold['filepath']}")
        print(f"       Reason:  {hold['reason']}")
        print(f"       Outcome: {hold['outcome']}")
        if hold["findings"]:
            print(f"       Flags:   {', '.join(f['type'] for f in hold['findings'])}")
        print()

    save_choice = input("  Do you want to save this summary as an alerts file? (y/n): ").strip().lower()
    if save_choice == "y":
        summary_path = f"D:/Interpolbility/logs/yolo_summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, "w") as f:
            json.dump(holds, f, indent=2)
        print(f"\n  [Interpolbility] Summary saved to: {summary_path}")
        log_event(f"YOLO summary saved to: {summary_path}")
    else:
        print("\n  [Interpolbility] Summary not saved. All events remain in the main log.")
        log_event("User declined to save YOLO summary.")

    clear_pending_holds()


if __name__ == "__main__":
    config = load_config()

    # Demo — simulate a blocked write attempt
    print("\n  Running write protection demo...\n")

    print("  Test 1: Writing to an allowed directory (should pass)")
    result = check_write("D:/Interpolbility/test_output.txt", "This is safe content.", config)
    print(f"  Result: {'ALLOWED' if result else 'BLOCKED'}\n")

    print("  Test 2: Writing a file with a hardcoded API key (should flag)")
    result = check_write(
        "D:/Interpolbility/test_creds.txt",
        "api_key = 'sk-abc123xyz456def789ghi012jkl345mno678'",
        config
    )
    print(f"  Result: {'ALLOWED' if result else 'BLOCKED'}\n")

    print("  Test 3: Writing to a protected directory (should block)")
    result = check_write("C:/Users/Rich/.ssh/known_hosts", "attacker_host ssh-rsa AAAAB3...", config)
    print(f"  Result: {'ALLOWED' if result else 'BLOCKED'}\n")
