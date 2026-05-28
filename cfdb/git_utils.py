from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def repo_root(cwd: Path) -> Path | None:
    result = run_git(["rev-parse", "--show-toplevel"], cwd, check=False)
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def commit_paths(paths: list[Path], subject: str, body: str, cwd: Path) -> bool:
    root = repo_root(cwd)
    if root is None:
        print("auto-commit skipped: not inside a git repository")
        return False

    relative_paths: list[str] = []
    for path in paths:
        resolved = path.resolve()
        try:
            relative_paths.append(str(resolved.relative_to(root)))
        except ValueError:
            print(f"auto-commit skipped: path is outside repository: {resolved}")
            return False

    run_git(["add", "--", *relative_paths], root)
    diff = run_git(["diff", "--cached", "--quiet", "--", *relative_paths], root, check=False)
    if diff.returncode == 0:
        print("auto-commit skipped: no staged changes")
        return False

    commit = run_git(
        [
            "-c",
            "user.name=Codex",
            "-c",
            "user.email=codex@example.local",
            "commit",
            "-m",
            subject,
            "-m",
            body,
        ],
        root,
        check=False,
    )
    if commit.returncode != 0:
        print("auto-commit failed:")
        print(commit.stderr.strip())
        return False
    print(commit.stdout.strip())
    return True

