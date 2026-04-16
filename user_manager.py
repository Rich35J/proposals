import os
import json
import datetime
from startup import load_config, log_event, explain

CONFIG_PATH = "D:/Interpolbility/config.json"
USERS_DIR = "D:/Interpolbility/users"


def get_all_users():
    if not os.path.exists(USERS_DIR):
        os.makedirs(USERS_DIR, exist_ok=True)
        return []
    users = []
    for filename in os.listdir(USERS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(USERS_DIR, filename)
            with open(filepath, "r") as f:
                user = json.load(f)
                users.append(user)
    return sorted(users, key=lambda u: u["name"].lower())


def get_user_profile_path(name):
    safe_name = name.lower().replace(" ", "_")
    return os.path.join(USERS_DIR, f"{safe_name}.json")


def load_user(name):
    path = get_user_profile_path(name)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


def save_user(user):
    os.makedirs(USERS_DIR, exist_ok=True)
    path = get_user_profile_path(user["name"])
    user["last_updated"] = datetime.datetime.now().isoformat()
    with open(path, "w") as f:
        json.dump(user, f, indent=2)


def create_new_user(config):
    print("\n" + "="*60)
    print("  INTERPOLBILITY - NEW USER SETUP")
    print("="*60)

    print("\n  Welcome. Let's get you set up.")
    name = input("\n  What should I call you? ").strip()

    if not name:
        name = "User"

    # Check if name already exists
    existing = load_user(name)
    if existing:
        print(f"\n  I already have a profile for {name}.")
        print("  If this is you, select your name from the main menu next time.")
        print("  If this is a different person, please use a different name.")
        return None

    print(f"\n  Good to meet you, {name}.")
    print("\n  One quick question before we continue.")
    print("\n  What is your experience level with AI systems and security?")
    print("\n    [1] New to this - please explain things as we go")
    print("    [2] Some experience - explain the important stuff")
    print("    [3] Experienced - just show me the alerts, skip the explanations")

    while True:
        choice = input("\n  Enter 1, 2, or 3: ").strip()
        if choice in ["1", "2", "3"]:
            break
        print("  Please enter 1, 2, or 3.")

    level_map = {"1": "beginner", "2": "intermediate", "3": "experienced"}
    experience_level = level_map[choice]
    verbose_mode = choice in ["1", "2"]

    user = {
        "name": name,
        "experience_level": experience_level,
        "verbose_mode": verbose_mode,
        "sessions": 1,
        "created_at": datetime.datetime.now().isoformat(),
        "last_updated": datetime.datetime.now().isoformat(),
        "total_alerts": 0,
        "explanation_requests": {
            "full": 0,
            "partial": 0,
            "skipped": 0
        },
        "response_times": [],
        "decisions": {
            "investigated": 0,
            "fix_it": 0,
            "allow_without_review": 0,
            "block_without_review": 0
        },
        "growth_moments": []
    }

    save_user(user)

    if choice == "1":
        print(f"\n  Got it, {name}. Interpolbility will explain what it's doing,")
        print("  why it matters, and what your options are every step of the way.")
    elif choice == "2":
        print(f"\n  Got it, {name}. You'll get explanations for anything important.")
    else:
        print(f"\n  Got it, {name}. Clean alerts only.")
        print("  You can change this anytime in your profile.")

    log_event(f"NEW USER created: {name} | level: {experience_level}")
    return user


def select_user(config):
    users = get_all_users()

    # No users yet - first run
    if not users:
        print("\n" + "="*60)
        print("  Welcome to Interpolbility")
        print("  AI Scope-Aware Write Protection System")
        print("="*60)
        print("\n  Looks like this is your first time here. Let's get you set up.")
        return create_new_user(config)

    # Single user - skip the menu
    if len(users) == 1:
        user = users[0]
        user["sessions"] += 1
        save_user(user)
        print("\n" + "="*60)
        print(f"  Welcome back, {user['name']}. Session {user['sessions']}.")
        print("="*60)
        log_event(f"SESSION START: {user['name']} | session {user['sessions']}")
        return user

    # Multiple users - show selection menu
    print("\n" + "="*60)
    print("  INTERPOLBILITY - WHO'S THERE?")
    print("="*60)
    print(f"\n  Hey there. I remember {len(users)} users on this machine.")
    print("  Before we continue, which are you?\n")

    for i, user in enumerate(users, 1):
        level = user["experience_level"].capitalize()
        sessions = user["sessions"]
        print(f"    [{i}] {user['name']}  ({level}, {sessions} session{'s' if sessions != 1 else ''})")

    print(f"\n    [{len(users) + 1}] I'm someone new")

    while True:
        choice = input("\n  Enter your number: ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(users):
                user = users[idx - 1]
                user["sessions"] += 1
                save_user(user)
                print(f"\n  Hey {user['name']}. Good to see you. Session {user['sessions']}.")
                log_event(f"SESSION START: {user['name']} | session {user['sessions']}")
                return user
            elif idx == len(users) + 1:
                return create_new_user(config)
        print("  Please enter a valid number from the list.")


def apply_user_to_config(user, config):
    config["user_profile"]["experience_level"] = user["experience_level"]
    config["user_profile"]["verbose_mode"] = user["verbose_mode"]
    config["user_profile"]["sessions"] = user["sessions"]
    config["active_user"] = user["name"]
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    return config


if __name__ == "__main__":
    config = load_config()

    print("\n  Running multi-user demo...\n")

    # Simulate existing users
    users_to_create = [
        {"name": "Billy", "level": "1"},
        {"name": "Bob", "level": "3"},
        {"name": "Sarah", "level": "2"},
    ]

    for u in users_to_create:
        if not load_user(u["name"]):
            level_map = {"1": "beginner", "2": "intermediate", "3": "experienced"}
            user = {
                "name": u["name"],
                "experience_level": level_map[u["level"]],
                "verbose_mode": u["level"] in ["1", "2"],
                "sessions": 3,
                "created_at": datetime.datetime.now().isoformat(),
                "last_updated": datetime.datetime.now().isoformat(),
                "total_alerts": 5,
                "explanation_requests": {"full": 2, "partial": 1, "skipped": 2},
                "response_times": [12.0, 8.5, 15.0, 6.0, 9.5],
                "decisions": {"investigated": 3, "fix_it": 0, "allow_without_review": 1, "block_without_review": 1},
                "growth_moments": []
            }
            save_user(user)
            print(f"  Created demo user: {u['name']}")

    print("\n  Demo users created. Running user selection...\n")
    selected = select_user(config)

    if selected:
        config = apply_user_to_config(selected, config)
        print(f"\n  Active user: {config['active_user']}")
        print(f"  Experience: {config['user_profile']['experience_level']}")
        print(f"  Verbose mode: {config['user_profile']['verbose_mode']}")
