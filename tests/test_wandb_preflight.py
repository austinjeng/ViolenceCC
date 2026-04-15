"""Phase 4 D-39 — fail-fast wandb credential check (scripts/wandb_preflight.py).

Three behaviors:
  W1: WANDB_API_KEY env var set -> exit 0 with presence message
  W2: no env, no netrc -> exit 2 with actionable stderr
  W3: no env, but wandb.api.api_key present -> exit 0 with netrc message
"""
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_preflight_env_var_set():
    """W1: WANDB_API_KEY env set -> exit 0 with presence message."""
    env = os.environ.copy()
    env["WANDB_API_KEY"] = "dummy_test_key_abcdef"
    out = subprocess.run(
        [sys.executable, "scripts/wandb_preflight.py"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env,
    )
    assert out.returncode == 0, f"stderr: {out.stderr}"
    assert "WANDB_API_KEY env var set" in out.stdout


def test_preflight_missing_credentials_actionable():
    """W2: no env, no api_key -> exit 2 with actionable message mentioning
    WANDB_API_KEY and wandb login."""
    env = os.environ.copy()
    env.pop("WANDB_API_KEY", None)
    # Shim wandb with api_key=None via a synthetic module + exec of the preflight body.
    script = (
        "import sys\n"
        "import types\n"
        "fake = types.ModuleType('wandb')\n"
        "fake.api = types.SimpleNamespace(api_key=None)\n"
        "fake.errors = types.SimpleNamespace(Error=Exception)\n"
        "sys.modules['wandb'] = fake\n"
        "exec(open('scripts/wandb_preflight.py', encoding='utf-8').read())\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env,
    )
    assert out.returncode == 2
    combined = out.stderr + out.stdout
    assert "wandb is not configured" in combined
    assert "WANDB_API_KEY" in combined
    assert "wandb login" in combined


def test_preflight_netrc_path():
    """W3: no env but wandb.api.api_key is set -> exit 0 with netrc message."""
    env = os.environ.copy()
    env.pop("WANDB_API_KEY", None)
    script = (
        "import sys\n"
        "import types\n"
        "fake = types.ModuleType('wandb')\n"
        "fake.api = types.SimpleNamespace(api_key='xyz-key-from-netrc')\n"
        "fake.errors = types.SimpleNamespace(Error=Exception)\n"
        "sys.modules['wandb'] = fake\n"
        "exec(open('scripts/wandb_preflight.py', encoding='utf-8').read())\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True, env=env,
    )
    assert out.returncode == 0
    assert "api_key discovered" in out.stdout
