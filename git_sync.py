# git_sync.py — robust auto-committer for transcripts (final stable build)
# Works in Chromebook/Linux terminals

import subprocess
from datetime import datetime
from pathlib import Path


def push_to_github(message=None):
    """
    Adds, commits, and pushes transcript changes to GitHub.
    Creates transcripts/ if missing and handles all edge cases gracefully.
    """
    repo_dir = Path(__file__).resolve().parent
    transcripts_dir = repo_dir / "transcripts"
    transcripts_dir.mkdir(exist_ok=True)

    timestamp = datetime.utcnow().isoformat(timespec="seconds")
    commit_msg = message or f"Auto-update transcript logs ({timestamp})"

    try:
        # Stage transcript folder
        subprocess.run(["git", "-C", str(repo_dir), "add", "transcripts"], check=True)

        # Try committing and capture all output
        commit_proc = subprocess.run(
            ["git", "-C", str(repo_dir), "commit", "-m", commit_msg],
            capture_output=True,
            text=True,
        )

        if commit_proc.returncode != 0:
            out = (commit_proc.stdout or "") + (commit_proc.stderr or "")
            if "nothing to commit" in out.lower() or "no changes added" in out.lower():
                print("ℹ️  No new transcript changes to commit.")
                return
            else:
                print("⚠️  Git commit error:\n", out.strip())
                return

        # Commit succeeded → push
        push_proc = subprocess.run(
            ["git", "-C", str(repo_dir), "push"],
            capture_output=True,
            text=True,
        )

        if push_proc.returncode == 0:
            print("✅  Auto-pushed new transcripts to GitHub successfully.")
        else:
            print("⚠️  Git push failed:\n", push_proc.stderr.strip())

    except subprocess.CalledProcessError as e:
        print("⚠️  Git operation failed:", e)
    except Exception as e:
        print("⚠️  Unexpected error during GitHub sync:", e)


if __name__ == "__main__":
    push_to_github()
