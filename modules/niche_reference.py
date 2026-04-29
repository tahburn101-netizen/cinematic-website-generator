"""
Niche Reference Finder Module
Finds a visually stunning website in the same niche as the target,
then runs SkillUI (ultra mode) to extract its full design system.
"""

import os
import json
import subprocess
import shutil
from pathlib import Path

# Curated list of stunning reference sites per niche
# These are real, beautifully designed sites that serve as design references
NICHE_REFERENCES = {
    "restaurant": [
        "https://www.noburestaurants.com",
        "https://www.eleven11.com.au",
        "https://www.alinearestaurant.com",
    ],
    "fitness": [
        "https://www.equinox.com",
        "https://www.peloton.com",
        "https://www.crossfit.com",
    ],
    "beauty": [
        "https://www.glossier.com",
        "https://www.aesop.com",
        "https://www.rituals.com",
    ],
    "real_estate": [
        "https://www.compass.com",
        "https://www.sothebysrealty.com",
        "https://www.elliman.com",
    ],
    "tech_saas": [
        "https://www.linear.app",
        "https://www.vercel.com",
        "https://www.stripe.com",
    ],
    "ecommerce": [
        "https://www.allbirds.com",
        "https://www.casper.com",
        "https://www.warbyparker.com",
    ],
    "agency": [
        "https://www.unfoldagency.com",
        "https://www.instrument.com",
        "https://www.basicagency.com",
    ],
    "medical": [
        "https://www.onemedical.com",
        "https://www.zocdoc.com",
        "https://www.hims.com",
    ],
    "hotel": [
        "https://www.ace-hotel.com",
        "https://www.1hotels.com",
        "https://www.sohohouse.com",
    ],
    "law": [
        "https://www.cravath.com",
        "https://www.weil.com",
        "https://www.skadden.com",
    ],
    "business": [
        "https://www.notion.so",
        "https://www.figma.com",
        "https://www.framer.com",
    ],
}


def get_reference_url(niche: str) -> str:
    """Get the best reference URL for a given niche."""
    refs = NICHE_REFERENCES.get(niche, NICHE_REFERENCES["business"])
    return refs[0]  # Use the top reference


def run_skillui(reference_url: str, output_dir: str, project_name: str) -> dict:
    """
    Run SkillUI ultra mode on the reference URL to extract design system.
    Returns dict with paths to extracted files.
    """
    print(f"[Niche Reference] Running SkillUI on: {reference_url}")
    os.makedirs(output_dir, exist_ok=True)

    result = {
        "reference_url": reference_url,
        "skill_dir": None,
        "skill_md": None,
        "design_md": None,
        "colors": {},
        "typography": {},
        "animations": "",
        "screenshots": [],
        "raw_tokens": {}
    }

    try:
        # Run skillui with ultra mode for full cinematic extraction
        cmd = [
            "skillui",
            "--url", reference_url,
            "--mode", "ultra",
            "--out", output_dir,
            "--name", project_name,
            "--screens", "5"
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=output_dir
        )
        print(f"[Niche Reference] SkillUI stdout: {proc.stdout[-500:]}")
        if proc.returncode != 0:
            print(f"[Niche Reference] SkillUI stderr: {proc.stderr[-500:]}")
            # Fall back to default mode
            cmd_default = [
                "skillui",
                "--url", reference_url,
                "--out", output_dir,
                "--name", project_name,
            ]
            proc = subprocess.run(cmd_default, capture_output=True, text=True, timeout=60, cwd=output_dir)

    except subprocess.TimeoutExpired:
        print("[Niche Reference] SkillUI timed out, trying default mode...")
        try:
            cmd_default = ["skillui", "--url", reference_url, "--out", output_dir, "--name", project_name]
            subprocess.run(cmd_default, capture_output=True, text=True, timeout=60, cwd=output_dir)
        except Exception as e:
            print(f"[Niche Reference] SkillUI default also failed: {e}")
    except Exception as e:
        print(f"[Niche Reference] SkillUI error: {e}")

    # Find the output directory created by skillui
    skill_dir = Path(output_dir) / project_name
    if not skill_dir.exists():
        # Try to find any directory created
        dirs = [d for d in Path(output_dir).iterdir() if d.is_dir()]
        if dirs:
            skill_dir = dirs[0]

    if skill_dir.exists():
        result["skill_dir"] = str(skill_dir)

        # Read SKILL.md
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            result["skill_md"] = skill_md_path.read_text()[:8000]  # cap at 8k chars

        # Read DESIGN.md
        design_md_path = skill_dir / "DESIGN.md"
        if design_md_path.exists():
            result["design_md"] = design_md_path.read_text()[:6000]

        # Read color tokens
        colors_json = skill_dir / "tokens" / "colors.json"
        if colors_json.exists():
            try:
                result["colors"] = json.loads(colors_json.read_text())
            except Exception:
                pass

        # Read typography tokens
        typo_json = skill_dir / "tokens" / "typography.json"
        if typo_json.exists():
            try:
                result["typography"] = json.loads(typo_json.read_text())
            except Exception:
                pass

        # Read animations reference
        anim_md = skill_dir / "references" / "ANIMATIONS.md"
        if anim_md.exists():
            result["animations"] = anim_md.read_text()[:3000]

        # Find screenshots
        screens_dir = skill_dir / "screens"
        if screens_dir.exists():
            screenshots = list(screens_dir.rglob("*.png")) + list(screens_dir.rglob("*.jpg"))
            result["screenshots"] = [str(s) for s in screenshots[:5]]

        print(f"[Niche Reference] SkillUI extraction complete. Files in: {skill_dir}")
    else:
        print(f"[Niche Reference] SkillUI output directory not found at {skill_dir}")

    return result


def get_design_reference(niche: str, output_dir: str) -> dict:
    """
    Main function: get design reference for a niche.
    Returns extracted design system data.
    """
    ref_url = get_reference_url(niche)
    project_name = f"{niche}-reference"
    return run_skillui(ref_url, output_dir, project_name)


if __name__ == "__main__":
    import sys
    niche = sys.argv[1] if len(sys.argv) > 1 else "restaurant"
    output = sys.argv[2] if len(sys.argv) > 2 else "/tmp/skillui-test"
    result = get_design_reference(niche, output)
    print(json.dumps({k: v for k, v in result.items() if k not in ['skill_md', 'design_md', 'animations']}, indent=2))
