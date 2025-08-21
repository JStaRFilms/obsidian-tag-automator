import os
import shutil
from pathlib import Path
import json
import time
import builtins
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from the project root
load_dotenv(project_root / '.env')

from tag_automator import ObsidianTagAutomator

# Use a demo vault inside the project directory
ROOT = Path(__file__).parent.parent
DEMO = ROOT / "_demo_vault"


def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_demo_vault():
    if DEMO.exists():
        shutil.rmtree(DEMO)
    DEMO.mkdir(parents=True, exist_ok=True)

    # Pre-seed tag_aliases.json to test alias application (e.g., next-js -> nextjs)
    (DEMO / "tag_aliases.json").write_text(json.dumps({
        "next-js": "nextjs",
        "ai-tool": "aitool"
    }, indent=2), encoding="utf-8")

    # Optional: pre-seed automator_config.json (empty; methods will mutate it)
    (DEMO / "automator_config.json").write_text(json.dumps({
        "excluded_tags": [],
        "excluded_paths": []
    }, indent=2), encoding="utf-8")

    # 1. File with inline tags and ai_processed false
    write_file(DEMO / "File1.md", """---
Title: File1
ai_processed: false
tags: [alpha, beta]
---
This is file 1. Mentions alpha and next-js. Also talks about ai-tool usage.
""")

    # 2. File with multi-line list tags
    write_file(DEMO / "File2.md", """---
Title: File2
tags:
  - gamma
  - next-js
---
This is file 2. Mentions Gamma and some NextJS framework notes.
""")

    # 3. File with no front matter
    write_file(DEMO / "File3.md", """
This is file 3. Content references alpha and aitool implicitly.
""")

    # 4. File with malformed tags (space and dot) for validation test
    write_file(DEMO / "File4.md", """---
Title: File4
tags: ["bad tag", dots.tag]
---
Contains malformed tags to trigger validation.
""")

    # 5. File marked as already AI processed
    write_file(DEMO / "File5.md", """---
Title: File5
ai_processed: true
tags: [delta]
---
Already processed file.
""")

    # In an excluded directory
    write_file(DEMO / "excluded_dir" / "Excluded.md", """---
Title: Excluded
ai_processed: false
tags: [excluded]
---
Should be skipped when path is excluded.
""")


def list_md_files(vault: Path):
    files = []
    for root, _, filenames in os.walk(vault):
        for fn in filenames:
            p = Path(root) / fn
            if p.suffix.lower() == ".md" and ".obsidian" not in p.parts:
                files.append(p)
    return sorted(files)


def read_tags_from_file(automator: ObsidianTagAutomator, path: Path):
    fm_raw, _ = automator._extract_front_matter_and_content(path)
    data = automator._parse_front_matter(fm_raw) if fm_raw else {}
    return data.get("tags", []), data.get("ai_processed", False)


def report_state(automator: ObsidianTagAutomator, title: str):
    print(f"\n=== {title} ===")
    for p in list_md_files(automator.vault_path):
        tags, ai = read_tags_from_file(automator, p)
        rel = str(p.relative_to(automator.vault_path))
        print(f"{rel:30} tags={tags} ai_processed={ai}")


def main():
    # Load environment variables from main vault directory first
    from dotenv import load_dotenv
    env_path = ROOT / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded .env from: {env_path}")
    else:
        print(f"Warning: .env file not found at {env_path}")
    
    build_demo_vault()
    
    automator = ObsidianTagAutomator(DEMO)

    # Ensure DB is up-to-date
    automator._update_tag_database()

    # Exclusions: add excluded_dir and a tag
    automator.add_excluded_path(str(DEMO / "excluded_dir"))
    automator.add_excluded_tag("excluded")

    report_state(automator, "Initial state")

    all_files = list_md_files(DEMO)

    # Helper to suppress interactive prompts inside run_automator (final scan question)
    class _NoPrompt:
        def __enter__(self):
            self._orig = builtins.input
            builtins.input = lambda *args, **kwargs: 'no'
            return self
        def __exit__(self, exc_type, exc, tb):
            builtins.input = self._orig

    # Option 1: Only process files NOT previously AI-tagged
    with _NoPrompt():
        automator.run_automator(all_files, re_tag_option='1')
    report_state(automator, "After re_tag_option=1")

    # Option 2: Re-tag ALL files
    with _NoPrompt():
        automator.run_automator(all_files, re_tag_option='2')
    report_state(automator, "After re_tag_option=2")

    # Option 3: Only re-tag files with existing tags but NOT AI-tagged
    with _NoPrompt():
        automator.run_automator(all_files, re_tag_option='3')
    report_state(automator, "After re_tag_option=3")

    # Option 4: Do NOT re-tag any files that already have tags (process only with no tags)
    with _NoPrompt():
        automator.run_automator(all_files, re_tag_option='4')
    report_state(automator, "After re_tag_option=4")

    # Option 5: Interactive review – monkeypatch to auto-accept combined tags
    def fake_review(file_path, current_tags, suggested_tags):
        # Simulate user 'accept all' behavior
        return sorted(list(set(current_tags + suggested_tags)))
    automator._interactive_tag_review = fake_review  # type: ignore
    with _NoPrompt():
        automator.run_automator(all_files, re_tag_option='5')
    report_state(automator, "After re_tag_option=5 (auto-accept)")

    # Generate suggested aliases (non-interactive path)
    automator._update_tag_database()
    suggested = automator._generate_suggested_aliases()
    print("\nSuggested aliases:", suggested)
    if suggested:
        # Merge with existing aliases without prompt
        current_aliases = automator._load_tag_aliases()
        current_aliases.update(suggested)
        automator._save_tag_aliases(current_aliases)

    # Rename a tag: beta -> beta-renamed
    automator.rename_tag("beta", "beta-renamed")
    report_state(automator, "After rename beta -> beta-renamed")

    # Merge a tag: alpha -> gamma (alpha should be replaced by gamma)
    automator.merge_tags("alpha", "gamma")
    report_state(automator, "After merge alpha -> gamma")

    # Clear tags from a subset of files
    automator.clear_tags([DEMO / "File1.md", DEMO / "File3.md"])  # Mixed front matter/no front matter cases
    report_state(automator, "After clearing tags on File1 and File3")

    # Validate tags (should flag 'bad tag' and 'dots.tag' in File4.md)
    automator.validate_tags()

    print("\nDemo complete. Demo vault at:", DEMO)


if __name__ == "__main__":
    main()
