"""Local Git tests only; these tests never contact GitHub or publish."""
import os
from pathlib import Path
import shutil

import pytest

from scripts.publish_generated import destination, prepare_commit, run_git
from scripts.update_profile import ASSET_NAMES


@pytest.mark.parametrize("branch", ["main", "master", "gh-pages", "../main", "refs/heads/main"])
def test_rejects_unsafe_publication_branch(branch):
    with pytest.raises(ValueError):
        destination({"username": "fixture", "repository": "fixture/fixture", "generated_branch": branch})


@pytest.mark.skipif(not shutil.which("git"), reason="Git is required for the local publication test")
def test_unchanged_assets_skip_commit_and_changes_preserve_history(tmp_path):
    env = os.environ.copy()
    env.update({"GIT_AUTHOR_NAME": "Fixture", "GIT_COMMITTER_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"})
    run_git(tmp_path, ["init", "--quiet"], env)
    assets = {name: b"fixture-only" for name in ASSET_NAMES}
    first = prepare_commit(tmp_path, assets, None, env)
    assert first
    assert prepare_commit(tmp_path, assets, first, env) is None
    assets["github-stats.svg"] = b"updated-fixture"
    second = prepare_commit(tmp_path, assets, first, env)
    assert second != first
    assert run_git(tmp_path, ["rev-parse", f"{second}^"], env).stdout.decode().strip() == first
    assert run_git(tmp_path, ["show", f"{second}:assets/generated/languages.svg"], env).stdout == b"fixture-only"
