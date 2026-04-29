"""
Vercel Deployment Module
Deploys the generated website to Vercel and returns a guaranteed public URL.

Requirements:
    export VERCEL_TOKEN="your-token"   # https://vercel.com/account/tokens

The deployment always uses --prod so the returned URL is the permanent
production alias (e.g. https://my-site-abc123.vercel.app) — no login required
to view it.
"""

import os
import json
import subprocess
import re
import time
import requests
import base64
from pathlib import Path

# ── Token resolution ──────────────────────────────────────────────────────────
# Never hardcode tokens. Load from environment only.
def _get_token() -> str:
    token = os.environ.get("VERCEL_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "VERCEL_TOKEN is not set.\n"
            "Get a token at https://vercel.com/account/tokens then run:\n"
            "  export VERCEL_TOKEN='your-token'"
        )
    return token


# ── Vercel CLI path (works on Linux/Mac/Windows) ──────────────────────────────
def _vercel_cli() -> str:
    # Try common locations
    candidates = [
        "/home/ubuntu/.nvm/versions/node/v22.13.0/bin/vercel",
        "/usr/local/bin/vercel",
        "/usr/bin/vercel",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    # Fall back to PATH
    import shutil
    found = shutil.which("vercel")
    if found:
        return found
    raise RuntimeError("Vercel CLI not found. Install with: npm i -g vercel")


# ── Helpers ───────────────────────────────────────────────────────────────────

def create_vercel_config(output_dir: str, project_name: str):
    """Create vercel.json for a static single-page site."""
    config = {
        "version": 2,
        "name": project_name,
        "builds": [{"src": "**/*", "use": "@vercel/static"}],
        "routes": [{"src": "/(.*)", "dest": "/$1"}],
        "public": True,          # Ensures the deployment is publicly accessible
    }
    config_path = os.path.join(output_dir, "vercel.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    return config_path


def sanitize_project_name(name: str) -> str:
    """Produce a Vercel-safe project name (lowercase, alphanumeric + hyphens)."""
    name = name.lower()
    name = re.sub(r"[^a-z0-9-]", "-", name)
    name = re.sub(r"-+", "-", name)
    name = name.strip("-")
    # Append short timestamp to avoid name collisions
    suffix = str(int(time.time()))[-6:]
    return f"{name[:28]}-{suffix}"


def _poll_for_public_url(deployment_url: str, token: str, timeout: int = 90) -> str:
    """
    Poll the Vercel API until the deployment is READY and return its
    permanent public alias URL (e.g. https://name-abc.vercel.app).
    Falls back to the deployment URL if polling times out.
    """
    # Extract deployment ID or use URL directly
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + timeout

    # Try to get the deployment record to find its alias
    # The deployment URL looks like https://name-<hash>-<team>.vercel.app
    # We need to find the production alias
    while time.time() < deadline:
        try:
            # List recent deployments and find the one matching our URL
            resp = requests.get(
                "https://api.vercel.com/v6/deployments",
                headers=headers,
                params={"limit": 5, "target": "production"},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                for dep in data.get("deployments", []):
                    dep_url = dep.get("url", "")
                    if not dep_url.startswith("https://"):
                        dep_url = "https://" + dep_url
                    # Match by URL or by recent creation time
                    state = dep.get("state", "")
                    if state == "READY":
                        # Prefer the alias list (permanent URLs)
                        aliases = dep.get("alias", [])
                        if aliases:
                            alias = aliases[0]
                            if not alias.startswith("https://"):
                                alias = "https://" + alias
                            return alias
                        return dep_url
        except Exception:
            pass
        time.sleep(3)

    return deployment_url  # fallback


# ── Main deployment function ──────────────────────────────────────────────────

def deploy_to_vercel(output_dir: str, project_name: str) -> dict:
    """
    Deploy the website to Vercel.

    Returns:
        {
            "success": bool,
            "url": str,       # permanent public URL, no login required
            "error": str,
        }
    """
    print(f"[Vercel Deployer] Deploying: {project_name}")

    result = {"success": False, "url": "", "project_name": project_name, "error": ""}

    try:
        token = _get_token()
    except RuntimeError as e:
        result["error"] = str(e)
        return result

    safe_name = sanitize_project_name(project_name)
    create_vercel_config(output_dir, safe_name)

    env = os.environ.copy()
    env["VERCEL_TOKEN"] = token

    # ── Attempt 1: Vercel CLI ─────────────────────────────────────────────
    try:
        cli = _vercel_cli()
        cmd = [
            cli,
            "--token", token,
            "--yes",
            "--prod",
            "--name", safe_name,
            output_dir,
        ]
        print(f"[Vercel Deployer] CLI: vercel deploy --prod --name {safe_name}")
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
            cwd=output_dir,
        )

        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()
        print(f"[Vercel Deployer] stdout: {stdout[-600:]}")
        if stderr:
            print(f"[Vercel Deployer] stderr: {stderr[-300:]}")

        if proc.returncode == 0:
            # Extract URL — Vercel CLI prints the production URL on the last line
            url = ""
            for line in reversed(stdout.split("\n")):
                line = line.strip()
                if line.startswith("https://") and "vercel.app" in line:
                    url = line
                    break

            if not url:
                m = re.search(r"https://[a-zA-Z0-9\-\.]+\.vercel\.app", stdout)
                if m:
                    url = m.group(0)

            # Also check stderr for "Aliased:" line (permanent public URL)
            alias_m = re.search(
                r"Aliased:\s*(https://[a-zA-Z0-9\-\.]+\.vercel\.app)", stderr
            )
            if alias_m:
                url = alias_m.group(1)

            if url:
                # Poll until READY and resolve permanent alias
                print(f"[Vercel Deployer] Polling for public alias…")
                public_url = _poll_for_public_url(url, token)
                result["success"] = True
                result["url"] = public_url
                print(f"[Vercel Deployer] Live public URL: {public_url}")
                return result
            else:
                result["error"] = "CLI succeeded but could not extract URL"
        else:
            result["error"] = f"CLI exit {proc.returncode}: {stderr[:300]}"

    except FileNotFoundError:
        result["error"] = "Vercel CLI not found — falling back to API"
    except subprocess.TimeoutExpired:
        result["error"] = "Vercel CLI timed out after 120s — falling back to API"
    except Exception as e:
        result["error"] = str(e)

    print(f"[Vercel Deployer] CLI attempt failed ({result['error']}), trying REST API…")

    # ── Attempt 2: Vercel REST API ────────────────────────────────────────
    api_result = _deploy_via_api(output_dir, safe_name, token)
    if api_result["success"]:
        return api_result

    # Merge errors
    result["error"] += " | API: " + api_result.get("error", "unknown")
    return result


def _deploy_via_api(output_dir: str, project_name: str, token: str) -> dict:
    """
    Deploy using the Vercel REST API (v13/deployments).
    Polls until READY and returns the permanent public alias URL.
    """
    result = {"success": False, "url": "", "error": ""}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Collect files
    files = []
    output_path = Path(output_dir)
    for fp in output_path.rglob("*"):
        if fp.is_file() and not any(p.startswith(".") for p in fp.parts[len(output_path.parts):]):
            rel = str(fp.relative_to(output_path))
            try:
                content = fp.read_bytes()
                files.append({
                    "file": rel,
                    "data": base64.b64encode(content).decode("utf-8"),
                    "encoding": "base64",
                })
            except Exception:
                pass

    if not files:
        result["error"] = "No files to deploy"
        return result

    payload = {
        "name": project_name,
        "files": files,
        "projectSettings": {
            "framework": None,
            "buildCommand": None,
            "outputDirectory": None,
            "installCommand": None,
        },
        "target": "production",
    }

    try:
        resp = requests.post(
            "https://api.vercel.com/v13/deployments",
            headers=headers,
            json=payload,
            timeout=90,
        )

        if resp.status_code in (200, 201):
            data = resp.json()
            dep_url = data.get("url", "")
            dep_id  = data.get("id", "")
            if dep_url and not dep_url.startswith("https://"):
                dep_url = "https://" + dep_url

            print(f"[Vercel API] Deployment created: {dep_url} (id={dep_id})")

            # Poll until READY
            public_url = _poll_deployment_ready(dep_id, dep_url, token)
            result["success"] = True
            result["url"] = public_url
            print(f"[Vercel API] Live public URL: {public_url}")
        else:
            result["error"] = f"API {resp.status_code}: {resp.text[:400]}"

    except Exception as e:
        result["error"] = str(e)

    return result


def _poll_deployment_ready(dep_id: str, fallback_url: str, token: str, timeout: int = 120) -> str:
    """
    Poll GET /v13/deployments/:id until state == READY.
    Returns the permanent alias URL (no login required).
    """
    if not dep_id:
        return fallback_url

    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            resp = requests.get(
                f"https://api.vercel.com/v13/deployments/{dep_id}",
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                state = data.get("state", "")
                print(f"[Vercel API] Deployment state: {state}")

                if state == "READY":
                    # Prefer alias list (permanent public URLs)
                    aliases = data.get("alias", [])
                    if aliases:
                        alias = aliases[0]
                        if not alias.startswith("https://"):
                            alias = "https://" + alias
                        return alias
                    url = data.get("url", fallback_url)
                    if url and not url.startswith("https://"):
                        url = "https://" + url
                    return url or fallback_url

                elif state in ("ERROR", "CANCELED"):
                    print(f"[Vercel API] Deployment failed with state: {state}")
                    return fallback_url

        except Exception as e:
            print(f"[Vercel API] Poll error: {e}")

        time.sleep(4)

    print("[Vercel API] Polling timed out — returning fallback URL")
    return fallback_url


# ── CLI test ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    test_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/deploy-test"
    test_name = sys.argv[2] if len(sys.argv) > 2 else "test-site"
    os.makedirs(test_dir, exist_ok=True)
    with open(os.path.join(test_dir, "index.html"), "w") as f:
        f.write("<html><body><h1>Test Deployment</h1></body></html>")
    print(json.dumps(deploy_to_vercel(test_dir, test_name), indent=2))
