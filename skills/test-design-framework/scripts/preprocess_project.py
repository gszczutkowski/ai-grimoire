"""
Preprocess an E2E test project for architectural analysis.

Exhaustively scans the project, excludes non-source content,
strips comments and noise from source files, deduplicates
structurally similar files, and produces a compact JSON summary
suitable for AI analysis.

Usage:
    python preprocess_project.py <project_path> [--tech <tech_stack>]

Output: JSON to stdout with structure:
{
    "directory_tree": { ... },
    "config_files": [ { "path": ..., "relevant_keys": ... } ],
    "source_files": [
        {
            "path": ...,
            "category": ...,
            "stripped_content": ...,
            "is_representative": true/false,
            "group_id": ...,
            "group_size": ...
        }
    ],
    "stats": { ... }
}
"""

import sys
import os
import json
import re
import hashlib
from pathlib import Path
from collections import defaultdict
import argparse

SCRIPT_DIR = Path(__file__).resolve().parent
if not SCRIPT_DIR.exists():
    print(f"ERROR: Script directory not found at '{SCRIPT_DIR}'.", file=sys.stderr)
    sys.exit(1)

# Directories to exclude from scanning
EXCLUDE_DIRS = {
    "node_modules", "dist", "build", "out", ".output",
    "playwright-report", "test-results", "coverage",
    ".git", ".svn", ".hg",
    "allure-results", "allure-report",
    ".cache", ".pytest_cache", "__pycache__",
    "screenshots", "videos", "downloads", "traces",
    ".nyc_output", ".next", ".nuxt",
    "target", "bin", "obj",
    "reports", "logs",
    ".idea", ".vscode",
    "vendor", "bower_components",
}

# File extensions to exclude
EXCLUDE_EXTENSIONS = {
    # Lock files
    ".lock",
    # Binary / media
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".mp4", ".avi", ".mov", ".webm",
    ".mp3", ".wav",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    # Compiled / generated
    ".map", ".min.js", ".min.css",
    ".d.ts",
    ".pyc", ".pyo", ".class", ".o", ".so", ".dll", ".exe",
    # Database
    ".sqlite", ".db",
}

# Exact filenames to exclude
EXCLUDE_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "composer.lock", "Gemfile.lock", "poetry.lock",
    ".DS_Store", "Thumbs.db",
    ".gitattributes",
}

# Config file patterns (read but extract only relevant keys)
CONFIG_PATTERNS = {
    "package.json", "tsconfig.json", "tsconfig.base.json",
    "playwright.config.ts", "playwright.config.js",
    "cypress.config.ts", "cypress.config.js", "cypress.config.mjs",
    "wdio.conf.ts", "wdio.conf.js",
    "jest.config.ts", "jest.config.js",
    "vitest.config.ts", "vitest.config.js",
    ".env", ".env.example", ".env.test", ".env.staging", ".env.production",
    "pytest.ini", "setup.cfg", "pyproject.toml", "conftest.py",
    ".eslintrc.json", ".eslintrc.js", ".eslintrc.yml",
    "babel.config.js", "babel.config.json",
    ".babelrc",
    "README.md", "readme.md",
}

# Source file extensions to process
SOURCE_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".py",
    ".java", ".kt", ".kts",
    ".cs",
    ".rb",
    ".go",
    ".rs",
    ".spec.ts", ".test.ts", ".spec.js", ".test.js",
}


def should_exclude_dir(dir_name: str) -> bool:
    """Check if a directory should be excluded."""
    return dir_name in EXCLUDE_DIRS or dir_name.startswith(".")


def should_exclude_file(file_path: Path) -> bool:
    """Check if a file should be excluded."""
    name = file_path.name
    suffix = file_path.suffix.lower()

    if name in EXCLUDE_FILES:
        return True
    if suffix in EXCLUDE_EXTENSIONS:
        return True
    if name.endswith(".min.js") or name.endswith(".min.css"):
        return True
    if name.endswith(".generated.ts") or name.endswith(".generated.js"):
        return True

    return False


def is_config_file(file_path: Path) -> bool:
    """Check if a file is a configuration file."""
    return file_path.name in CONFIG_PATTERNS


def is_source_file(file_path: Path) -> bool:
    """Check if a file is a source file to analyze."""
    suffix = file_path.suffix.lower()
    return suffix in SOURCE_EXTENSIONS


def scan_directory(project_path: Path) -> dict:
    """Scan directory tree and build a summary with file counts."""
    tree = {"name": project_path.name, "type": "dir", "children": [], "file_count": 0}
    all_files = []

    def _scan(current_path: Path, node: dict, depth: int = 0):
        if depth > 15:
            return

        try:
            entries = sorted(current_path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return

        for entry in entries:
            if entry.is_dir():
                if should_exclude_dir(entry.name):
                    continue
                child = {"name": entry.name, "type": "dir", "children": [], "file_count": 0}
                _scan(entry, child, depth + 1)
                if child["file_count"] > 0 or child["children"]:
                    node["children"].append(child)
                    node["file_count"] += child["file_count"]
            elif entry.is_file():
                if should_exclude_file(entry):
                    continue
                rel = entry.relative_to(project_path)
                node["file_count"] += 1
                all_files.append(entry)
                if not is_config_file(entry) and not is_source_file(entry):
                    node["children"].append({"name": entry.name, "type": "file"})
                else:
                    node["children"].append({"name": entry.name, "type": "file"})

    _scan(project_path, tree)
    return tree, all_files


def strip_comments_ts_js(content: str) -> str:
    """Strip comments from TypeScript/JavaScript content."""
    # Remove single-line comments (but not URLs with //)
    content = re.sub(r'(?<!:)//(?!/)[^\n]*', '', content)
    # Remove multi-line comments
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    # Collapse multiple blank lines into one
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def strip_comments_python(content: str) -> str:
    """Strip comments from Python content."""
    # Remove single-line comments
    content = re.sub(r'#[^\n]*', '', content)
    # Remove docstrings (triple quotes) but keep the function/class signature
    content = re.sub(r'"""[\s\S]*?"""', '""""""', content)
    content = re.sub(r"'''[\s\S]*?'''", "''''''", content)
    # Collapse multiple blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def strip_comments_java_cs(content: str) -> str:
    """Strip comments from Java/C#/Kotlin content."""
    content = re.sub(r'//[^\n]*', '', content)
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def strip_comments_ruby(content: str) -> str:
    """Strip comments from Ruby content."""
    content = re.sub(r'#[^\n]*', '', content)
    content = re.sub(r'=begin[\s\S]*?=end', '', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def strip_comments(content: str, extension: str) -> str:
    """Strip comments based on file extension."""
    ext = extension.lower()
    if ext in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
        return strip_comments_ts_js(content)
    elif ext == ".py":
        return strip_comments_python(content)
    elif ext in {".java", ".kt", ".kts", ".cs", ".go", ".rs"}:
        return strip_comments_java_cs(content)
    elif ext == ".rb":
        return strip_comments_ruby(content)
    return content


def remove_long_strings(content: str) -> str:
    """Remove long string literals that aren't locators."""
    # Keep short strings (likely selectors/locators) but remove long ones (error messages, descriptions)
    def replace_long_string(match):
        s = match.group(0)
        inner = s[1:-1]
        # Keep if it looks like a selector/locator
        locator_patterns = [
            r'[#\.\[]',  # CSS selectors
            r'data-',     # data attributes
            r'//',        # XPath
            r'role=',     # ARIA
            r'>>',        # Playwright chained selectors
        ]
        for pattern in locator_patterns:
            if re.search(pattern, inner):
                return s
        # Keep short strings
        if len(inner) <= 80:
            return s
        return s[0] + "..." + s[-1]

    # Match single and double quoted strings (non-greedy)
    content = re.sub(r'"[^"]{80,}"', replace_long_string, content)
    content = re.sub(r"'[^']{80,}'", replace_long_string, content)
    content = re.sub(r'`[^`]{80,}`', replace_long_string, content)
    return content


def extract_structural_signature(content: str, extension: str) -> str:
    """Extract a structural signature for deduplication.

    Captures class hierarchy, method signatures, and import patterns
    while ignoring implementation details.
    """
    lines = content.split('\n')
    signature_parts = []

    ext = extension.lower()
    if ext in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
        for line in lines:
            stripped = line.strip()
            # Class declarations with extends/implements
            if re.match(r'(export\s+)?(abstract\s+)?class\s+', stripped):
                signature_parts.append(stripped)
            # Method signatures
            elif re.match(r'(async\s+)?(public|private|protected|static|\s)*\w+\s*\(', stripped):
                # Keep just the signature, not the body
                sig = re.match(r'[^{]+', stripped)
                if sig:
                    signature_parts.append(sig.group(0).strip())
            # Import statements (for dependency analysis)
            elif stripped.startswith('import '):
                signature_parts.append(stripped)
            # Decorators
            elif stripped.startswith('@'):
                signature_parts.append(stripped)
            # Interface/type declarations
            elif re.match(r'(export\s+)?(interface|type)\s+', stripped):
                signature_parts.append(stripped)
    elif ext == ".py":
        for line in lines:
            stripped = line.strip()
            if re.match(r'class\s+', stripped):
                signature_parts.append(stripped)
            elif re.match(r'(async\s+)?def\s+', stripped):
                signature_parts.append(stripped)
            elif stripped.startswith('import ') or stripped.startswith('from '):
                signature_parts.append(stripped)
            elif stripped.startswith('@'):
                signature_parts.append(stripped)
    elif ext in {".java", ".kt", ".kts", ".cs"}:
        for line in lines:
            stripped = line.strip()
            if re.match(r'(public|private|protected|abstract|static|final|\s)*(class|interface|enum)\s+', stripped):
                signature_parts.append(stripped)
            elif re.match(r'(public|private|protected|abstract|static|final|override|\s)*\w+\s+\w+\s*\(', stripped):
                sig = re.match(r'[^{]+', stripped)
                if sig:
                    signature_parts.append(sig.group(0).strip())
            elif stripped.startswith('import '):
                signature_parts.append(stripped)
            elif stripped.startswith('@') or stripped.startswith('['):
                signature_parts.append(stripped)

    return '\n'.join(signature_parts)


def compute_structure_hash(signature: str) -> str:
    """Compute a hash from structural signature for grouping."""
    # Normalize: remove specific names but keep patterns
    normalized = re.sub(r'\b[A-Z][a-zA-Z0-9]+(?:Page|Component|Element|Widget|Module|View)\b', '<CLASS>', signature)
    normalized = re.sub(r'(?<=\s)\w+(?=\s*\()', '<METHOD>', normalized)
    return hashlib.md5(normalized.encode()).hexdigest()


def categorize_file(file_path: Path, content: str) -> str:
    """Categorize a source file based on its path and content."""
    name = file_path.name.lower()
    path_str = str(file_path).lower().replace('\\', '/')

    # Test specs
    if any(p in name for p in ['.spec.', '.test.', '_spec.', '_test.']):
        return 'test_spec'
    if '/specs/' in path_str or '/tests/' in path_str or '/test/' in path_str:
        return 'test_spec'

    # Test fixtures / data
    if '/fixtures/' in path_str or '/testdata/' in path_str or '/test-data/' in path_str:
        return 'test_data'
    if 'fixture' in name:
        return 'test_data'

    # Page objects
    if any(p in name for p in ['page.', 'page-object', 'pageobject']):
        return 'page_object'
    if any(p in path_str for p in ['/pages/', '/page-objects/', '/pageobjects/']):
        return 'page_object'

    # Base classes
    if any(p in name for p in ['base.', 'abstract.']) or name.startswith('base'):
        return 'base_class'
    if '/base/' in path_str:
        return 'base_class'

    # Components
    if any(p in path_str for p in ['/components/', '/component/', '/widgets/', '/elements/']):
        return 'component'
    if any(p in name for p in ['component.', 'widget.', 'element.']):
        return 'component'

    # Helpers / utilities
    if any(p in path_str for p in ['/helpers/', '/utils/', '/utilities/', '/support/', '/lib/']):
        return 'helper_utility'
    if any(p in name for p in ['helper.', 'util.', 'utils.']):
        return 'helper_utility'

    # Steps (for BDD/Cucumber patterns)
    if '/steps/' in path_str or 'steps.' in name or 'step-def' in name:
        return 'step_definition'

    # Models / data classes
    if any(p in path_str for p in ['/models/', '/types/', '/interfaces/', '/dto/']):
        return 'model_type'

    # Config / setup
    if any(p in path_str for p in ['/config/', '/setup/', '/env/']):
        return 'config_setup'
    if 'config' in name or 'setup' in name:
        return 'config_setup'

    # Reporters / logging
    if any(p in name for p in ['reporter', 'logger', 'logging']):
        return 'reporter_logger'
    if '/reporters/' in path_str:
        return 'reporter_logger'

    return 'other'


def extract_config_relevant_keys(file_path: Path, content: str) -> str:
    """Extract architecturally relevant content from config files."""
    name = file_path.name

    if name == "package.json":
        try:
            data = json.loads(content)
            relevant = {}
            for key in ["name", "scripts", "dependencies", "devDependencies"]:
                if key in data:
                    relevant[key] = data[key]
            return json.dumps(relevant, indent=2)
        except json.JSONDecodeError:
            return content

    if name.startswith("tsconfig"):
        try:
            # Remove comments from tsconfig (JSON with comments)
            cleaned = re.sub(r'//[^\n]*', '', content)
            cleaned = re.sub(r'/\*[\s\S]*?\*/', '', cleaned)
            data = json.loads(cleaned)
            relevant = {}
            if "compilerOptions" in data:
                co = data["compilerOptions"]
                relevant["compilerOptions"] = {
                    k: co[k] for k in ["target", "module", "baseUrl", "paths", "rootDir", "outDir", "strict"]
                    if k in co
                }
            for key in ["include", "exclude", "extends", "references"]:
                if key in data:
                    relevant[key] = data[key]
            return json.dumps(relevant, indent=2)
        except (json.JSONDecodeError, ValueError):
            return content

    if name.startswith(".env"):
        # Extract key names only, not values (security)
        lines = content.split('\n')
        keys = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key = line.split('=')[0].strip()
                keys.append(f"{key}=<VALUE>")
        return '\n'.join(keys)

    if name in {"README.md", "readme.md"}:
        # Keep README as-is (contains project documentation)
        return content

    # For framework config files (.ts/.js configs), strip comments but keep structure
    if name.endswith(('.ts', '.js', '.mjs')):
        return strip_comments_ts_js(content)

    return content


def build_directory_tree_string(tree: dict, prefix: str = "", is_last: bool = True) -> str:
    """Build a visual directory tree string."""
    lines = []
    connector = "`-- " if is_last else "|-- "

    if tree.get("type") == "dir":
        count_info = f" ({tree['file_count']} files)" if tree.get("file_count", 0) > 0 else ""
        lines.append(f"{prefix}{connector}{tree['name']}/{count_info}")
        child_prefix = prefix + ("    " if is_last else "|   ")

        children = tree.get("children", [])
        for i, child in enumerate(children):
            is_child_last = (i == len(children) - 1)
            lines.append(build_directory_tree_string(child, child_prefix, is_child_last))
    else:
        lines.append(f"{prefix}{connector}{tree['name']}")

    return '\n'.join(lines)


def process_project(project_path: Path, tech_stack: str = "") -> dict:
    """Main processing pipeline."""
    if not project_path.exists():
        print(f"ERROR: Project path does not exist: '{project_path}'", file=sys.stderr)
        sys.exit(1)

    if not project_path.is_dir():
        print(f"ERROR: Project path is not a directory: '{project_path}'", file=sys.stderr)
        sys.exit(1)

    # Step 1: Scan directory
    tree, all_files = scan_directory(project_path)

    # Step 2: Separate config and source files
    config_files = []
    source_files = []
    skipped_count = 0

    for f in all_files:
        if is_config_file(f):
            config_files.append(f)
        elif is_source_file(f):
            source_files.append(f)
        else:
            skipped_count += 1

    # Step 3: Process config files
    processed_configs = []
    for cf in config_files:
        try:
            content = cf.read_text(encoding='utf-8', errors='replace')
            relevant = extract_config_relevant_keys(cf, content)
            processed_configs.append({
                "path": str(cf.relative_to(project_path)),
                "content": relevant,
            })
        except Exception as e:
            processed_configs.append({
                "path": str(cf.relative_to(project_path)),
                "content": f"ERROR reading file: {e}",
            })

    # Step 4: Process source files - strip, categorize, extract signatures
    processed_sources = []
    signatures = {}

    for sf in source_files:
        try:
            content = sf.read_text(encoding='utf-8', errors='replace')
            rel_path = str(sf.relative_to(project_path))

            # Strip comments and noise
            stripped = strip_comments(content, sf.suffix)
            stripped = remove_long_strings(stripped)

            # Categorize
            category = categorize_file(sf.relative_to(project_path), content)

            # Extract structural signature for deduplication
            signature = extract_structural_signature(stripped, sf.suffix)
            structure_hash = compute_structure_hash(signature)

            processed_sources.append({
                "path": rel_path,
                "category": category,
                "stripped_content": stripped,
                "signature": signature,
                "structure_hash": structure_hash,
                "original_lines": len(content.split('\n')),
                "stripped_lines": len(stripped.split('\n')),
            })

            if structure_hash not in signatures:
                signatures[structure_hash] = []
            signatures[structure_hash].append(rel_path)

        except Exception as e:
            processed_sources.append({
                "path": str(sf.relative_to(project_path)),
                "category": "error",
                "stripped_content": f"ERROR reading file: {e}",
                "signature": "",
                "structure_hash": "",
                "original_lines": 0,
                "stripped_lines": 0,
            })

    # Step 5: Deduplicate - mark representatives and outliers
    for source in processed_sources:
        h = source["structure_hash"]
        group = signatures.get(h, [])
        if len(group) <= 1:
            source["is_representative"] = True
            source["group_id"] = None
            source["group_size"] = 1
        else:
            source["is_representative"] = (source["path"] == group[0])
            source["group_id"] = h[:8]
            source["group_size"] = len(group)

    # Step 6: Build output
    # For non-representative files, include only metadata (not full content)
    output_sources = []
    for source in processed_sources:
        entry = {
            "path": source["path"],
            "category": source["category"],
            "is_representative": source["is_representative"],
            "group_id": source["group_id"],
            "group_size": source["group_size"],
            "original_lines": source["original_lines"],
            "stripped_lines": source["stripped_lines"],
        }
        if source["is_representative"]:
            entry["stripped_content"] = source["stripped_content"]
        else:
            entry["stripped_content"] = f"[DEDUPLICATED — same structure as group {source['group_id']}, see representative]"
            entry["signature"] = source["signature"]

        output_sources.append(entry)

    # Build tree string
    tree_string = build_directory_tree_string(tree)

    # Compute stats
    total_original_lines = sum(s["original_lines"] for s in processed_sources)
    total_stripped_lines = sum(s.get("stripped_lines", 0) for s in processed_sources if s["is_representative"])
    representative_count = sum(1 for s in output_sources if s["is_representative"])
    deduplicated_count = len(output_sources) - representative_count

    # Category breakdown
    category_counts = defaultdict(int)
    for s in processed_sources:
        category_counts[s["category"]] += 1

    stats = {
        "total_files_scanned": len(all_files),
        "config_files": len(config_files),
        "source_files": len(source_files),
        "skipped_files": skipped_count,
        "representative_files": representative_count,
        "deduplicated_files": deduplicated_count,
        "total_original_lines": total_original_lines,
        "total_stripped_lines_representatives": total_stripped_lines,
        "token_reduction_estimate": f"{round((1 - total_stripped_lines / max(total_original_lines, 1)) * 100)}%",
        "categories": dict(category_counts),
    }

    return {
        "directory_tree": tree_string,
        "config_files": processed_configs,
        "source_files": output_sources,
        "stats": stats,
    }


def main():
    parser = argparse.ArgumentParser(description="Preprocess E2E test project for architectural analysis")
    parser.add_argument("project_path", help="Path to the E2E test project")
    parser.add_argument("--tech", default="", help="Tech stack hint (e.g., 'Playwright + TypeScript')")
    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()
    result = process_project(project_path, args.tech)

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
