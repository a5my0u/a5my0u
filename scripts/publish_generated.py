"""Publish only validated generated assets to the dedicated branch.

Default is validation-only. --publish is an intentional external write and is
used by the workflow only after the owner approves deployment of that workflow.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

try:
    from .update_profile import ASSET_NAMES, validate_snapshot, validate_svg
except ImportError:
    from update_profile import ASSET_NAMES, validate_snapshot, validate_svg


class PublishError(RuntimeError):
    pass


def destination(config: dict) -> tuple[str, str]:
    repo = config["repository"]
    branch = config["generated_branch"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("Invalid GitHub repository")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", branch) or branch in {"main", "master", "gh-pages"}:
        raise ValueError("A separate simple generated branch is required")
    if repo.split("/")[0].casefold() != config["username"].casefold():
        raise ValueError("Publishing is restricted to the configured user's repository")
    return f"https://github.com/{repo}.git", branch


def load_assets(folder: Path) -> dict[str, bytes]:
    assets = {name: (folder / name).read_bytes() for name in ASSET_NAMES}
    for name, value in assets.items():
        if len(value) > 5_000_000:
            raise ValueError("Generated asset unexpectedly large")
        if name.endswith(".svg"):
            validate_svg(value.decode("utf-8"))
    validate_snapshot(json.loads(assets["public-data.json"]))
    return assets


def run_git(work: Path, args: list[str], env: dict, *, data: bytes | None = None, allow: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess:
    result = subprocess.run(["git", "-C", str(work), *args], input=data, capture_output=True, env=env, timeout=90, check=False)
    if result.returncode not in allow:
        # Git error output can contain auth context. Never echo it.
        raise PublishError(f"Git {args[0]} failed with exit code {result.returncode}")
    return result


def prepare_commit(work: Path, assets: dict[str, bytes], previous: str | None, env: dict) -> str | None:
    if set(assets) != set(ASSET_NAMES):
        raise ValueError("Cannot publish a partial asset set")
    run_git(work, ["read-tree", previous] if previous else ["read-tree", "--empty"], env)
    for name in ASSET_NAMES:
        blob = run_git(work, ["hash-object", "-w", "--stdin"], env, data=assets[name]).stdout.decode().strip()
        run_git(work, ["update-index", "--add", "--cacheinfo", f"100644,{blob},assets/generated/{name}"], env)
    tree = run_git(work, ["write-tree"], env).stdout.decode().strip()
    if previous:
        old_tree = run_git(work, ["rev-parse", f"{previous}^{{tree}}"], env).stdout.decode().strip()
        if tree == old_tree:
            return None
    args = ["commit-tree", tree]
    if previous:
        args += ["-p", previous]
    args += ["-m", "Update public profile analytics [skip ci]"]
    return run_git(work, args, env).stdout.decode().strip()


def publish(config: dict, assets: dict[str, bytes], token: str) -> bool:
    remote, branch = destination(config)
    if not token:
        raise ValueError("GITHUB_TOKEN is required for publishing")
    env = os.environ.copy()
    env.update({
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_AUTHOR_NAME": "github-actions[bot]",
        "GIT_COMMITTER_NAME": "github-actions[bot]",
        "GIT_AUTHOR_EMAIL": "41898282+github-actions[bot]@users.noreply.github.com",
        "GIT_COMMITTER_EMAIL": "41898282+github-actions[bot]@users.noreply.github.com",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
        "GIT_CONFIG_VALUE_0": "AUTHORIZATION: basic " + base64.b64encode(f"x-access-token:{token}".encode()).decode(),
    })
    with tempfile.TemporaryDirectory(prefix="profile-publish-") as temp:
        work = Path(temp)
        run_git(work, ["init", "--quiet"], env)
        run_git(work, ["remote", "add", "origin", remote], env)
        found = run_git(work, ["ls-remote", "--exit-code", "--heads", "origin", f"refs/heads/{branch}"], env, allow=(0, 2))
        previous = None
        if found.returncode == 0:
            run_git(work, ["fetch", "--quiet", "--depth=1", "origin", f"refs/heads/{branch}"], env)
            previous = run_git(work, ["rev-parse", "FETCH_HEAD"], env).stdout.decode().strip()
        commit = prepare_commit(work, assets, previous, env)
        if commit is None:
            return False
        # One non-forced ref update publishes the complete set atomically. If
        # another writer advances the branch, Git rejects the non-fast-forward.
        run_git(work, ["push", "origin", f"{commit}:refs/heads/{branch}"], env)
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/profile.json"))
    parser.add_argument("--assets", type=Path, default=Path("assets/generated"))
    parser.add_argument("--publish", action="store_true", help="Write validated assets to the configured GitHub branch")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        destination(config)
        assets = load_assets(args.assets)
        if not args.publish:
            print("Assets validated. Nothing was sent to GitHub; pass --publish only after approval.")
            return 0
        changed = publish(config, assets, os.environ.get("GITHUB_TOKEN", ""))
        print("Generated branch updated." if changed else "Generated branch unchanged; no commit created.")
        return 0
    except Exception as exc:
        print(f"Generated branch not updated ({type(exc).__name__}). Previous branch content was retained.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
