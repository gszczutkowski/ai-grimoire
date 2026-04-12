"""
Compute scores and generate evaluation report for AI skill/command definitions.

Reads a structured JSON evaluation produced by the AI evaluator,
computes sub-averages and overall scores, and generates a formatted
Markdown report.

Usage:
    python compute_scores.py --input <json_path> --output <output_path>
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if not SCRIPT_DIR.exists():
    print(f"ERROR: Script directory not found at '{SCRIPT_DIR}'.", file=sys.stderr)
    sys.exit(1)

TEMPLATE_DIR = SCRIPT_DIR.parent / "templates"

CORE_CRITERIA_KEYS = [
    "1_intent_clarity",
    "2_input_output_definition",
    "3_internal_consistency",
    "4_structure_organization",
    "5_role_definition",
    "6_granularity",
    "7_determinism_flexibility",
    "8_handling_uncertainty",
    "9_testability",
    "10_user_error_resilience",
    "11_instruction_priority",
    "12_limitations_restrictions",
    "13_style_tone",
    "14_modularity",
    "15_cognitive_load",
    "16_edge_case_handling",
    "17_instruction_unambiguity",
    "18_information_hierarchy",
    "19_examples_quality",
    "20_iterability",
]

SECURITY_SUBCATEGORY_KEYS = [
    "21.1_boundaries",
    "21.2_prompt_injection",
    "21.3_sensitive_content",
    "21.4_hallucination_prevention",
    "21.5_fail_safe",
    "21.6_data_privacy",
    "21.7_priority_conflicts",
    "21.8_allowed_forbidden",
    "21.9_safety_examples",
    "21.10_safety_architecture",
]

SCRIPTS_SUBCATEGORY_KEYS = [
    "22.1_readability",
    "22.2_maintainability",
    "22.3_best_practices",
    "22.4_testability",
    "22.5_correctness",
    "22.6_performance",
    "22.7_security",
    "22.8_documentation",
    "22.9_consistency",
    "22.10_error_handling",
    "22.11_dependencies",
    "22.12_code_structure",
]

CRITERIA_DISPLAY_NAMES = {
    "1_intent_clarity": "Intent Clarity",
    "2_input_output_definition": "Input & Output Definition",
    "3_internal_consistency": "Internal Consistency",
    "4_structure_organization": "Structure & Organization",
    "5_role_definition": "Role Definition",
    "6_granularity": "Granularity",
    "7_determinism_flexibility": "Determinism vs Flexibility",
    "8_handling_uncertainty": "Handling Uncertainty",
    "9_testability": "Testability",
    "10_user_error_resilience": "User Error Resilience",
    "11_instruction_priority": "Instruction Priority",
    "12_limitations_restrictions": "Limitations & Restrictions",
    "13_style_tone": "Style & Tone",
    "14_modularity": "Modularity",
    "15_cognitive_load": "Cognitive Load",
    "16_edge_case_handling": "Edge-Case Handling",
    "17_instruction_unambiguity": "Instruction Unambiguity",
    "18_information_hierarchy": "Information Hierarchy",
    "19_examples_quality": "Examples Quality",
    "20_iterability": "Iterability",
}

SECURITY_DISPLAY_NAMES = {
    "21.1_boundaries": "Boundaries & Scope Control",
    "21.2_prompt_injection": "Prompt Injection Resilience",
    "21.3_sensitive_content": "Sensitive Content Handling",
    "21.4_hallucination_prevention": "Hallucination Prevention",
    "21.5_fail_safe": "Fail-Safe Behavior",
    "21.6_data_privacy": "Data Handling & Privacy",
    "21.7_priority_conflicts": "Priority & Conflict Resolution",
    "21.8_allowed_forbidden": "Allowed vs Forbidden Clarity",
    "21.9_safety_examples": "Safety Examples",
    "21.10_safety_architecture": "Safety Architecture",
}

SCRIPTS_DISPLAY_NAMES = {
    "22.1_readability": "Readability",
    "22.2_maintainability": "Maintainability",
    "22.3_best_practices": "Best Practices",
    "22.4_testability": "Testability",
    "22.5_correctness": "Correctness",
    "22.6_performance": "Performance",
    "22.7_security": "Security",
    "22.8_documentation": "Documentation & Comments",
    "22.9_consistency": "Consistency",
    "22.10_error_handling": "Error Handling",
    "22.11_dependencies": "Dependencies & Imports",
    "22.12_code_structure": "Code Structure & Organization",
}


def validate_score(score, context):
    """Validate that a score is an integer between 1 and 10."""
    if not isinstance(score, int):
        raise ValueError(f"Score for '{context}' must be an integer, got {type(score).__name__}: {score}")
    if score < 1 or score > 10:
        raise ValueError(f"Score for '{context}' must be between 1 and 10, got {score}")


def compute_average(scores, precision=1):
    """Compute the arithmetic mean of a list of scores, rounded to given precision."""
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), precision)


def validate_json_structure(data):
    """Validate the evaluation JSON has all required fields and valid scores."""
    errors = []

    for field in ("skill_name", "skill_path", "evaluation_date", "summary",
                  "strengths", "weaknesses", "required_improvements", "scores"):
        if field not in data:
            errors.append(f"Missing required top-level field: '{field}'")

    if errors:
        return errors

    scores = data["scores"]

    # Validate core criteria 1-20
    for key in CORE_CRITERIA_KEYS:
        if key not in scores:
            errors.append(f"Missing score entry: '{key}'")
        elif "score" not in scores[key]:
            errors.append(f"Missing 'score' field in '{key}'")
        elif "justification" not in scores[key]:
            errors.append(f"Missing 'justification' field in '{key}'")
        else:
            try:
                validate_score(scores[key]["score"], key)
            except ValueError as e:
                errors.append(str(e))

    # Validate criterion 21 (Security)
    if "21_security" not in scores:
        errors.append("Missing score entry: '21_security'")
    else:
        sec = scores["21_security"]
        if "subcategories" not in sec:
            errors.append("Missing 'subcategories' in '21_security'")
        else:
            for key in SECURITY_SUBCATEGORY_KEYS:
                if key not in sec["subcategories"]:
                    errors.append(f"Missing security subcategory: '{key}'")
                elif "score" not in sec["subcategories"][key]:
                    errors.append(f"Missing 'score' in '{key}'")
                elif "justification" not in sec["subcategories"][key]:
                    errors.append(f"Missing 'justification' in '{key}'")
                else:
                    try:
                        validate_score(sec["subcategories"][key]["score"], key)
                    except ValueError as e:
                        errors.append(str(e))

    # Validate criterion 22 (Scripts)
    if "22_scripts" not in scores:
        errors.append("Missing score entry: '22_scripts'")
    else:
        scr = scores["22_scripts"]
        if "applicable" not in scr:
            errors.append("Missing 'applicable' field in '22_scripts'")
        elif scr["applicable"]:
            if "subcategories" not in scr:
                errors.append("Missing 'subcategories' in '22_scripts' (applicable=true)")
            else:
                for key in SCRIPTS_SUBCATEGORY_KEYS:
                    if key not in scr["subcategories"]:
                        errors.append(f"Missing scripts subcategory: '{key}'")
                    elif "score" not in scr["subcategories"][key]:
                        errors.append(f"Missing 'score' in '{key}'")
                    elif "justification" not in scr["subcategories"][key]:
                        errors.append(f"Missing 'justification' in '{key}'")
                    else:
                        try:
                            validate_score(scr["subcategories"][key]["score"], key)
                        except ValueError as e:
                            errors.append(str(e))

    return errors


def compute_all_scores(data):
    """Compute sub-averages and overall score from the evaluation data."""
    scores = data["scores"]
    result = {}

    # Core criteria 1-20 individual scores
    core_scores = []
    for key in CORE_CRITERIA_KEYS:
        s = scores[key]["score"]
        core_scores.append(s)
        result[key] = s

    # Security sub-average (criterion 21)
    sec_scores = []
    for key in SECURITY_SUBCATEGORY_KEYS:
        s = scores["21_security"]["subcategories"][key]["score"]
        sec_scores.append(s)
    security_avg = compute_average(sec_scores)
    result["21_security"] = security_avg

    # Scripts sub-average (criterion 22)
    scripts_applicable = scores["22_scripts"]["applicable"]
    scripts_avg = None
    if scripts_applicable:
        scr_scores = []
        for key in SCRIPTS_SUBCATEGORY_KEYS:
            s = scores["22_scripts"]["subcategories"][key]["score"]
            scr_scores.append(s)
        scripts_avg = compute_average(scr_scores)
        result["22_scripts"] = scripts_avg

    # Overall score: equal weight across all applicable criteria
    all_scores = core_scores + [security_avg]
    if scripts_applicable and scripts_avg is not None:
        all_scores.append(scripts_avg)

    overall = compute_average(all_scores)
    result["overall"] = overall
    result["scripts_applicable"] = scripts_applicable
    result["total_criteria"] = len(all_scores)

    return result


def generate_report(data, computed):
    """Generate the formatted Markdown evaluation report."""
    template_path = TEMPLATE_DIR / "eval_report.template.md"
    if not template_path.exists():
        print(f"ERROR: Report template not found at '{template_path}'.", file=sys.stderr)
        sys.exit(1)

    template = template_path.read_text(encoding="utf-8")
    scores = data["scores"]

    # Build core scores table
    core_rows = []
    for key in CORE_CRITERIA_KEYS:
        name = CRITERIA_DISPLAY_NAMES[key]
        score = scores[key]["score"]
        core_rows.append(f"| {name} | {score}/10 |")
    core_rows.append(f"| **Security (21)** | **{computed['21_security']}/10** |")
    if computed["scripts_applicable"]:
        core_rows.append(f"| **Scripts (22)** | **{computed['22_scripts']}/10** |")
    else:
        core_rows.append("| **Scripts (22)** | **N/A** |")
    core_table = "\n".join(core_rows)

    # Build core justifications
    core_justifications = []
    for key in CORE_CRITERIA_KEYS:
        name = CRITERIA_DISPLAY_NAMES[key]
        entry = scores[key]
        core_justifications.append(f"### {key.split('_', 1)[0]}. {name} — {entry['score']}/10\n\n{entry['justification']}")
    core_justifications_text = "\n\n".join(core_justifications)

    # Build security subcategory table and justifications
    sec_rows = []
    sec_justifications = []
    for key in SECURITY_SUBCATEGORY_KEYS:
        name = SECURITY_DISPLAY_NAMES[key]
        entry = scores["21_security"]["subcategories"][key]
        sec_rows.append(f"| {name} | {entry['score']}/10 |")
        sec_justifications.append(f"**{key}. {name}** — {entry['score']}/10: {entry['justification']}")
    security_table = "\n".join(sec_rows)
    security_justifications = "\n\n".join(sec_justifications)

    # Build scripts section
    if computed["scripts_applicable"]:
        scr = scores["22_scripts"]
        files_eval = scr.get("files_evaluated", [])
        missing = scr.get("missing_scripts", [])
        unreferenced = scr.get("unreferenced_scripts", [])

        files_list = "\n".join(f"- `{f}`" for f in files_eval) if files_eval else "- None"
        missing_list = "\n".join(f"- **CRITICAL:** `{f}`" for f in missing) if missing else "- None"
        unreferenced_list = "\n".join(f"- `{f}`" for f in unreferenced) if unreferenced else "- None"

        scr_rows = []
        scr_justifications = []
        for key in SCRIPTS_SUBCATEGORY_KEYS:
            name = SCRIPTS_DISPLAY_NAMES[key]
            entry = scr["subcategories"][key]
            scr_rows.append(f"| {name} | {entry['score']}/10 |")
            scr_justifications.append(f"**{key}. {name}** — {entry['score']}/10: {entry['justification']}")
        scripts_table = "\n".join(scr_rows)
        scripts_justifications = "\n\n".join(scr_justifications)

        scripts_section = f"""## Scripts Evaluation — {computed['22_scripts']}/10

**Files evaluated:**
{files_list}

**Missing scripts (CRITICAL):**
{missing_list}

**Unreferenced scripts (warning):**
{unreferenced_list}

| Subcategory | Score |
|-------------|-------|
{scripts_table}

{scripts_justifications}"""
    else:
        scripts_section = "## Scripts Evaluation — N/A\n\nNo scripts found. Criterion 22 excluded from overall score."

    # Build critical issues section
    critical_issues = data.get("critical_issues", [])
    if critical_issues:
        critical_section = "## Critical Issues\n\n" + "\n".join(f"- **CRITICAL:** {issue}" for issue in critical_issues)
    else:
        critical_section = ""

    # Build file discovery section
    discovery = data.get("file_discovery", {})
    discovery_lines = []
    if discovery.get("referenced_scripts"):
        discovery_lines.append("**Referenced in skill:**")
        discovery_lines.extend(f"- `{f}`" for f in discovery["referenced_scripts"])
    if discovery.get("found_scripts"):
        discovery_lines.append("\n**Found in directory:**")
        discovery_lines.extend(f"- `{f}`" for f in discovery["found_scripts"])
    if discovery.get("missing_scripts"):
        discovery_lines.append("\n**MISSING (referenced but not found):**")
        discovery_lines.extend(f"- **CRITICAL:** `{f}`" for f in discovery["missing_scripts"])
    if discovery.get("unreferenced_scripts"):
        discovery_lines.append("\n**Unreferenced (found but not in skill):**")
        discovery_lines.extend(f"- `{f}`" for f in discovery["unreferenced_scripts"])
    file_discovery_section = "\n".join(discovery_lines) if discovery_lines else "No file dependencies discovered."

    # Build strengths/weaknesses/improvements
    strengths = "\n".join(f"- {s}" for s in data.get("strengths", []))
    weaknesses = "\n".join(f"- {w}" for w in data.get("weaknesses", []))
    improvements = "\n".join(f"- {i}" for i in data.get("required_improvements", []))

    # Apply template substitutions
    report = template
    report = report.replace("{{skill_name}}", data["skill_name"])
    report = report.replace("{{skill_path}}", data["skill_path"])
    report = report.replace("{{evaluation_date}}", data["evaluation_date"])
    report = report.replace("{{overall_score}}", str(computed["overall"]))
    report = report.replace("{{total_criteria}}", str(computed["total_criteria"]))
    report = report.replace("{{summary}}", data["summary"])
    report = report.replace("{{core_scores_table}}", core_table)
    report = report.replace("{{core_justifications}}", core_justifications_text)
    report = report.replace("{{security_average}}", str(computed["21_security"]))
    report = report.replace("{{security_table}}", security_table)
    report = report.replace("{{security_justifications}}", security_justifications)
    report = report.replace("{{scripts_section}}", scripts_section)
    report = report.replace("{{critical_issues_section}}", critical_section)
    report = report.replace("{{file_discovery_section}}", file_discovery_section)
    report = report.replace("{{strengths}}", strengths)
    report = report.replace("{{weaknesses}}", weaknesses)
    report = report.replace("{{required_improvements}}", improvements)

    return report


def main():
    parser = argparse.ArgumentParser(description="Compute evaluation scores and generate report.")
    parser.add_argument("--input", required=True, help="Path to the evaluation JSON file.")
    parser.add_argument("--output", required=True, help="Path for the output .eval.md report.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: Input JSON file not found: '{input_path}'", file=sys.stderr)
        sys.exit(1)

    try:
        raw = input_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in '{input_path}': {e}", file=sys.stderr)
        sys.exit(1)

    validation_errors = validate_json_structure(data)
    if validation_errors:
        print("ERROR: JSON validation failed:", file=sys.stderr)
        for err in validation_errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    computed = compute_all_scores(data)

    report = generate_report(data, computed)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print(f"Report saved to: {output_path}")
    print(f"Overall score: {computed['overall']}/10 (from {computed['total_criteria']} criteria)")
    if data.get("critical_issues"):
        print(f"CRITICAL ISSUES: {len(data['critical_issues'])}")


if __name__ == "__main__":
    main()
