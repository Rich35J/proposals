import os
import json
import datetime
from startup import load_config, log_event, explain

CONFIG_PATH = "D:/Interpolbility/config.json"
PROFILE_PATH = "D:/Interpolbility/user_profile.json"

# Thresholds for profile progression
PROGRESSION_THRESHOLDS = {
    "beginner_to_intermediate": {
        "min_sessions": 5,
        "explanation_skip_rate": 0.5,
        "avg_response_time_max": 30,
        "investigate_rate_min": 0.4,
        "fix_it_rate_max": 0.4
    },
    "intermediate_to_experienced": {
        "min_sessions": 15,
        "explanation_skip_rate": 0.75,
        "avg_response_time_max": 15,
        "investigate_rate_min": 0.65,
        "fix_it_rate_max": 0.2
    }
}

LEVEL_ORDER = ["beginner", "intermediate", "experienced"]


def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r") as f:
            return json.load(f)
    return initialize_profile()


def initialize_profile():
    profile = {
        "experience_level": "beginner",
        "sessions": 0,
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
        "growth_moments": [],
        "last_updated": datetime.datetime.now().isoformat()
    }
    save_profile(profile)
    return profile


def save_profile(profile):
    profile["last_updated"] = datetime.datetime.now().isoformat()
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)


def record_alert_response(decision, response_time_seconds, explanation_type, config):
    profile = load_profile()

    profile["total_alerts"] += 1

    # Record response time
    profile["response_times"].append(round(response_time_seconds, 2))

    # Record explanation engagement
    if explanation_type in profile["explanation_requests"]:
        profile["explanation_requests"][explanation_type] += 1

    # Record decision type
    if decision in ["diff", "hash", "log"]:
        profile["decisions"]["investigated"] += 1
    elif decision == "fix_it":
        profile["decisions"]["fix_it"] += 1
    elif decision == "allow":
        profile["decisions"]["allow_without_review"] += 1
    elif decision == "block":
        profile["decisions"]["block_without_review"] += 1

    save_profile(profile)
    log_event(f"Profile updated — decision: {decision}, response_time: {response_time_seconds}s, explanation: {explanation_type}")

    # Check for fix_it pattern
    check_fix_it_pattern(profile, config)

    # Check for progression
    check_progression(profile, config)


def check_fix_it_pattern(profile, config):
    total = profile["total_alerts"]
    if total < 3:
        return

    fix_it_count = profile["decisions"]["fix_it"]
    fix_it_rate = fix_it_count / total if total > 0 else 0

    if fix_it_rate >= 0.6 and fix_it_count >= 3:
        print("\n  [Interpolbility] I noticed something worth mentioning.")

        if config["user_profile"]["verbose_mode"]:
            print("\n  You've been resolving alerts quickly without investigating what triggered them.")
            print("  That's completely fine — you're in control of how you use this tool.")
            print("\n  But I want to make sure I'm helping you build understanding, not just clearing alerts.")
            print("  AI works best as a tool that makes you stronger, not one that does the thinking for you.")
            print("\n  Here's what triggered the last alert in plain English:")
        else:
            print("\n  Quick note on the last alert before we move on:")

        log_event("Fix-it pattern detected — user nudged toward investigation")


def compute_metrics(profile):
    total = profile["total_alerts"]
    if total == 0:
        return None

    explanation_total = sum(profile["explanation_requests"].values())
    skip_rate = profile["explanation_requests"]["skipped"] / explanation_total if explanation_total > 0 else 0

    response_times = profile["response_times"]
    avg_response = sum(response_times) / len(response_times) if response_times else 999

    investigated = profile["decisions"]["investigated"]
    investigate_rate = investigated / total if total > 0 else 0

    fix_it = profile["decisions"]["fix_it"]
    fix_it_rate = fix_it / total if total > 0 else 0

    return {
        "sessions": profile["sessions"],
        "total_alerts": total,
        "explanation_skip_rate": round(skip_rate, 2),
        "avg_response_time": round(avg_response, 2),
        "investigate_rate": round(investigate_rate, 2),
        "fix_it_rate": round(fix_it_rate, 2)
    }


def check_progression(profile, config):
    current_level = profile["experience_level"]
    metrics = compute_metrics(profile)

    if not metrics:
        return

    current_index = LEVEL_ORDER.index(current_level)
    if current_index >= len(LEVEL_ORDER) - 1:
        return

    next_level = LEVEL_ORDER[current_index + 1]
    threshold_key = f"{current_level}_to_{next_level}"
    thresholds = PROGRESSION_THRESHOLDS.get(threshold_key)

    if not thresholds:
        return

    qualifies = (
        metrics["sessions"] >= thresholds["min_sessions"] and
        metrics["explanation_skip_rate"] >= thresholds["explanation_skip_rate"] and
        metrics["avg_response_time"] <= thresholds["avg_response_time_max"] and
        metrics["investigate_rate"] >= thresholds["investigate_rate_min"] and
        metrics["fix_it_rate"] <= thresholds["fix_it_rate_max"]
    )

    if qualifies:
        offer_progression(profile, current_level, next_level, metrics, config)


def offer_progression(profile, current_level, next_level, metrics, config):
    print("\n" + "="*60)
    print("  INTERPOLBILITY — GROWTH DETECTED")
    print("="*60)

    print(f"\n  Based on how you've been engaging, I think you've grown past {current_level} level.")
    print(f"\n  Here's what I observed across {metrics['sessions']} sessions:\n")
    print(f"    You investigated alerts before deciding:  {int(metrics['investigate_rate']*100)}% of the time")
    print(f"    You skipped explanations you didn't need: {int(metrics['explanation_skip_rate']*100)}% of the time")
    print(f"    Your average response time:               {metrics['avg_response_time']}s")
    print(f"\n  That looks like {next_level} behavior to me.")

    agree = input(f"\n  Does that feel right to you? Ready to move to {next_level}? (y/n): ").strip().lower()

    if agree == "y":
        profile["experience_level"] = next_level
        profile["growth_moments"].append({
            "from": current_level,
            "to": next_level,
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics_at_progression": metrics,
            "user_confirmed": True
        })
        save_profile(profile)

        # Update config verbose mode
        config["user_profile"]["experience_level"] = next_level
        config["user_profile"]["verbose_mode"] = next_level != "experienced"
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)

        print(f"\n  [Interpolbility] Profile updated to {next_level}.")
        print("  You'll notice explanations adjusting to match where you are now.")
        print("  You can always change this manually in config.json.")
        log_event(f"PROFILE PROGRESSION — {current_level} to {next_level} — confirmed by user")

    else:
        profile["growth_moments"].append({
            "from": current_level,
            "to": next_level,
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics_at_progression": metrics,
            "user_confirmed": False
        })
        save_profile(profile)

        print(f"\n  [Interpolbility] Understood. Staying at {current_level}.")
        print("  You know yourself better than my metrics do.")
        print("  I'll check back in after a few more sessions.")
        log_event(f"PROFILE PROGRESSION offered — {current_level} to {next_level} — declined by user")


def show_profile_summary(config):
    profile = load_profile()
    metrics = compute_metrics(profile)
    verbose = config["user_profile"]["verbose_mode"]

    print("\n" + "="*60)
    print("  INTERPOLBILITY — YOUR PROFILE")
    print("="*60)

    print(f"\n  Experience level:  {profile['experience_level'].capitalize()}")
    print(f"  Sessions:          {profile['sessions']}")
    print(f"  Total alerts seen: {profile['total_alerts']}")

    if metrics:
        print(f"\n  How you engage:")
        print(f"    Investigated before deciding:  {int(metrics['investigate_rate']*100)}%")
        print(f"    Skipped explanations:          {int(metrics['explanation_skip_rate']*100)}%")
        print(f"    Average response time:         {metrics['avg_response_time']}s")
        print(f"    Quick fix rate:                {int(metrics['fix_it_rate']*100)}%")

    if profile["growth_moments"]:
        print(f"\n  Growth history:")
        for moment in profile["growth_moments"]:
            confirmed = "confirmed" if moment["user_confirmed"] else "declined"
            print(f"    {moment['from']} to {moment['to']} — {moment['timestamp'][:10]} ({confirmed})")

    if verbose:
        explain("WHAT: This is your personal profile that Interpolbility builds over time.", config)
        explain("WHY: The more you interact with the tool, the better it understands how to communicate with you — more detail when you need it, less noise when you don't.", config)

    log_event("Profile summary viewed by user")


if __name__ == "__main__":
    config = load_config()

    print("\n  Running Layer 4 demo...\n")

    # Simulate a session of interactions
    print("  Simulating user interactions to build profile metrics...\n")

    # Simulate 6 sessions worth of interactions
    profile = load_profile()
    profile["sessions"] = 6
    save_profile(profile)

    # Simulate alert responses
    interactions = [
        ("diff",    12.4, "full"),
        ("hash",    8.1,  "partial"),
        ("log",     15.2, "full"),
        ("allow",   5.0,  "skipped"),
        ("diff",    9.3,  "partial"),
        ("block",   7.8,  "skipped"),
        ("hash",    11.0, "full"),
        ("diff",    6.5,  "skipped"),
        ("log",     14.2, "partial"),
        ("allow",   4.1,  "skipped"),
    ]

    for decision, response_time, explanation_type in interactions:
        record_alert_response(decision, response_time, explanation_type, config)

    print("\n  Interactions recorded. Showing profile summary:\n")
    show_profile_summary(config)
