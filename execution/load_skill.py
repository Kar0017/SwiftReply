import argparse
import json
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def download_repo(url: str, dest: Path) -> Path:
    # Basic URL parsing, assumes github.com/user/repo
    parts = url.rstrip('/').split('/')
    user = parts[-2]
    repo = parts[-1]
    
    zip_url = f"https://github.com/{user}/{repo}/archive/refs/heads/main.zip"
    zip_path = dest / f"{repo}.zip"
    
    print(f"Downloading {zip_url}...")
    try:
        urllib.request.urlretrieve(zip_url, zip_path)
    except Exception as e:
        print(f"Failed to download main.zip. Trying master.zip... ({e})")
        zip_url = f"https://github.com/{user}/{repo}/archive/refs/heads/master.zip"
        urllib.request.urlretrieve(zip_url, zip_path)
        
    print(f"Extracting {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(dest)
        extracted_dir = zip_ref.namelist()[0].split('/')[0]
        
    os.remove(zip_path)
    return dest / extracted_dir

def load_skill(github_url: str, custom_name: str = None):
    # Parse name from URL if not provided
    name = custom_name or github_url.rstrip('/').split('/')[-1]
    print(f"Loading skill: {name} from {github_url}")
    
    tmp_dir = Path(".tmp")
    ensure_dir(tmp_dir)
    
    try:
        repo_dir = download_repo(github_url, tmp_dir)
    except Exception as e:
        print(f"Error downloading repository: {e}")
        return
        
    # Check for skill.manifest.json or SKILL.md
    manifest_path = repo_dir / "skill.manifest.json"
    skill_md_path = None
    
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        entry = manifest.get("entry_directive", "SKILL.md")
        skill_md_path = repo_dir / entry
    else:
        # Fallback to looking for SKILL.md in common places
        possible_paths = [
            repo_dir / "SKILL.md",
            repo_dir / "skills" / name / "SKILL.md",
            repo_dir / "source" / "skills" / name / "SKILL.md",
            repo_dir / "dist" / "claude-code" / ".claude" / "skills" / name / "SKILL.md",
            repo_dir / "README.md"
        ]
        for p in possible_paths:
            if p.exists():
                skill_md_path = p
                break
                
    if not skill_md_path or not skill_md_path.exists():
        print(f"Could not find SKILL.md in {github_url}")
        return
        
    # Read SKILL.md content
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        skill_content = f.read()
        
    # Copy to all 4 locations
    paths_to_write = [
        Path(f".claude/skills/{name}/SKILL.md"),
        Path(f".agents/skills/{name}/SKILL.md"),
        Path(f".github/skills/{name}/SKILL.md"),
        Path(f"directives/{name}.md")
    ]
    
    for path in paths_to_write:
        ensure_dir(path.parent)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(skill_content)
        print(f"Written: {path}")
        
    # Update registry.json
    registry_path = Path("skills/registry.json")
    ensure_dir(registry_path.parent)
    
    registry = {}
    if registry_path.exists():
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
        except json.JSONDecodeError:
            registry = {}
            
    registry[name] = {
        "capabilities": manifest.get("capabilities", []),
        "tags": manifest.get("tags", []),
        "mcp_servers": manifest.get("requires_mcp", []),
        "invoke": f"See {name}.md"
    }
    
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)
    print(f"Registered {name} in skills/registry.json")
    
    print(f"Successfully loaded {name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load a skill from a GitHub repository.")
    parser.add_argument("url", help="GitHub URL of the skill repository")
    parser.add_argument("--name", help="Custom name for the skill", default=None)
    args = parser.parse_args()
    
    load_skill(args.url, args.name)
