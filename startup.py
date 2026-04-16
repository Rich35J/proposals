import os
import json
import hashlib
import datetime

CONFIG_PATH = "D:/Interpolbility/config.json"
BASELINE_PATH = "D:/Interpolbility/baseline_hashes.json"
LOG_DIR = "D:/Interpolbility/logs"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def explain(message, config):
    if config["user_profile"]["verbose_mode"]:
        print(f"\n  [Interpolbility] {message}")

def hash_file(filepath):
    try:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except (PermissionError, FileNotFoundError):
        return None

def build_baseline(config):
    print("\n  [Interpolbility] Building a security baseline now.")
    explain("WHAT: Scanning your allowed directories and recording a fingerprint (hash) of every file.", config)
    explain("WHERE: Only scanning directories listed as 'allowed' in config.json.", config)
    explain("WHY: This baseline is how we detect if any file is changed without your knowledge. Think of it as a before-photo. If something changes later, we compare against this.", config)

    baseline = {}
    allowed_dirs = config["allowed_directories"]

    for directory in allowed_dirs:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    filepath = os.path.join(root, filename).replace("\\", "/")
                    file_hash = hash_file(filepath)
                    if file_hash:
                        baseline[filepath] = {
                            "hash": file_hash,
                            "recorded_at": datetime.datetime.now().isoformat()
                        }

    with open(BASELINE_PATH, "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"\n  [Interpolbility] Baseline complete. {len(baseline)} file(s) recorded.")
    explain("You can find this baseline at: " + BASELINE_PATH, config)
    explain("Do not delete this file. It is your ground truth for detecting unauthorized changes.", config)

def onboard_user(config):
    print("\n" + "="*60)
    print("  Welcome to Interpolbility")
    print("  AI Scope-Aware Write Protection System")
    print("="*60)

    print("\n  Before we begin, one quick question.")
    print("\n  What is your experience level with AI systems and security?")
    print("\n    [1] New to this — please explain things as we go")
    print("    [2] Some experience — explain the important stuff")
    print("    [3] Experienced — just show me the alerts, skip the explanations")

    while True:
        choice = input("\n  Enter 1, 2, or 3: ").strip()
        if choice in ["1", "2", "3"]:
            break
        print("  Please enter 1, 2, or 3.")

    level_map = {"1": "beginner", "2": "intermediate", "3": "experienced"}
    config["user_profile"]["experience_level"] = level_map[choice]
    config["user_profile"]["verbose_mode"] = choice in ["1", "2"]
    config["user_profile"]["sessions"] = 1

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    if choice == "1":
        print("\n  Got it. Interpolbility will explain what it's doing, why it matters,")
        print("  and what your options are every step of the way.")
    elif choice == "2":
        print("\n  Got it. You'll get explanations for anything important.")
    else:
        print("\n  Got it. Clean alerts only. You can change this anytime in config.json.")

    return config

def set_home_directory(config):
    home = config["startup"]["home_directory"]
    os.makedirs(home, exist_ok=True)
    os.chdir(home)
    explain(f"WHAT: Setting the working directory to {home}.", config)
    explain("WHERE: This is your safe zone. The agent starts here every session.", config)
    explain("WHY: Starting in a known, controlled location prevents the agent from accidentally operating in sensitive system areas.", config)
    print(f"\n  [Interpolbility] Working directory set to: {os.getcwd()}")

def create_log_dir(config):
    os.makedirs(LOG_DIR, exist_ok=True)
    explain("WHAT: Creating a logs folder to record all agent activity.", config)
    explain("WHERE: " + LOG_DIR, config)
    explain("WHY: Every action the agent takes is logged. If something goes wrong, you have a full record of what happened and when.", config)

def log_event(message):
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}\n"
    log_file = LOG_DIR + "/interpolbility.log"
    with open(log_file, "a") as f:
        f.write(log_entry)

def startup():
    config = load_config()

    # First run — onboard the user
    if config["user_profile"]["experience_level"] is None:
        config = onboard_user(config)
    else:
        config["user_profile"]["sessions"] += 1
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        print("\n" + "="*60)
        print("  Interpolbility — Session", config["user_profile"]["sessions"])
        print("="*60)

    # Set home directory
    set_home_directory(config)

    # Create log directory
    create_log_dir(config)

    # Build or verify baseline
    if not os.path.exists(BASELINE_PATH):
        build_baseline(config)
    else:
        explain("WHAT: A security baseline already exists from a previous session.", config)
        explain("WHY: Interpolbility will use this to detect any unauthorized file changes during this session.", config)
        print(f"\n  [Interpolbility] Existing baseline loaded from: {BASELINE_PATH}")

    log_event("Startup complete. Session " + str(config["user_profile"]["sessions"]))
    print("\n  [Interpolbility] System ready. Monitoring active.\n")

    return config

if __name__ == "__main__":
    startup()
