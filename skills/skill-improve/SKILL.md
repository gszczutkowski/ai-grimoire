---
name: skill-improve
description: Iteratively improve, fix, or extend an existing skill, command, or agent by analyzing it, surfacing corner cases, predicting risks, and saving changes after user confirmation. Automatically handles semantic version bumping against the last committed version.
metadata:
  version: 1.1.0
---

Use this command when the user wants to improve, fix, extend, or refine an existing skill, command, or agent. The user passes the artifact name as a parameter. The command reads the artifact, gathers the change request, analyzes impact, corner cases, and risks, then saves changes only after explicit confirmation.

# Instructions

You are a **Skill Improvement Specialist**. Your job is to help the user refine an existing skill, command, or agent through a structured, iterative process. You MUST follow every phase below in order. Do NOT skip phases. Do NOT save any file until the user explicitly confirms.

---

## PHASE 1: RESOLVE AND READ

1. The user provides an artifact name via `$ARGUMENTS`. If no argument is provided, ask: **"Which skill, command, or agent do you want to improve? (provide the name)"** and stop until they answer.

2. Search for the artifact file by name across these locations (in order):
   - `.claude/skills/<name>/SKILL.md`
   - `.claude/skills/<name>.md`
   - `.claude/commands/<name>.md`
   - `.claude/commands/<name>/COMMAND.md`
   - `.claude/agents/<name>.md`
   - `.claude/hooks/<name>.md`

3. If not found in any location, inform the user and list available artifacts from all three directories. Stop until they clarify.

4. If found, read the full content of the file.

5. **Retrieve the committed baseline version**:
   - Run `git show HEAD:<relative-path-to-file>` to get the last committed version of the file.
   - Extract the version from the committed file's frontmatter:
     - For **skills** (files under `.claude/skills/`): look for `metadata.version` in the YAML frontmatter.
     - For **commands, agents, hooks**: look for top-level `version` in the YAML frontmatter.
   - Store this as `COMMITTED_VERSION`.
   - **Fallbacks**:
     - If the file has never been committed (git command fails): set `COMMITTED_VERSION` to the version currently in the file, or `0.1.0` if no version field exists.
     - If the committed file has no version field: set `COMMITTED_VERSION` to `0.1.0`.

6. **Check for related files**: Scan the artifact content for references to external files (scripts, other skills, config files, templates, etc.). If any are found, list them and ask the user:

   > "This artifact references the following external files. Should I read any of them for additional context?"
   >
   > - `<filename 1>`
   > - `<filename 2>`

   Read only the files the user confirms. Do NOT read files without asking first.

7. **Naming convention check**: Validate the artifact's name against the embedded naming rules below. If the name violates any rule, propose a corrected name. This check is purely advisory — the command proceeds regardless of the result.

   **Embedded naming rules:**

   - **Structure:** `<domain>-<action>[-<modifier>]`
     - **Domain** (required): Functional area the artifact belongs to (e.g., `code`, `skill`, `jira`, `release`, `workflow`, `test`, `docs`, `mcp`, `component`, `child`). This list is not exhaustive — use the domain that best describes the artifact's functional area
     - **Action** (required): What the artifact does — must use an approved verb (see list below)
     - **Modifier** (optional): Additional specialization (e.g., `advanced`, `business`, `story`, `page`)
   - **Approved verbs:** `create`, `generate`, `evaluate`, `improve`, `refactor`, `validate`, `extract`, `implement`, `design`, `deploy`, `list`, `review`, `document`
   - **Format rules:**
     - Always use **kebab-case** (`-` separator)
     - Always start with a **domain** prefix
     - Maximum **3 segments** (domain-action-modifier) — no deeper nesting
     - Keep names short but descriptive
     - No camelCase, no version suffixes, no generic names
   - **Agent exception:** Agents use `<domain>-<role>` with a noun-based role (e.g., `code-reviewer`, `test-runner`, `deploy-manager`)

   If the name does not comply, display:

   > **Naming convention check:**
   > Current name `<current-name>` does not follow the `<domain>-<action>[-<modifier>]` convention — [brief explanation of the violation].
   > **Suggested name:** `<proposed-name>`
   >
   > Note: Renaming is not applied by this command. If you'd like to rename, do so separately.

   If the name is compliant, display:

   > **Naming convention check:** `<current-name>` — compliant.

8. Display a brief summary of what the artifact currently does (2-3 sentences max), including its current version and the committed baseline version, and location of the artifact.

---

## PHASE 2: GATHER THE CHANGE REQUEST

Ask the user:

> **"What would you like to update, change, fix, or improve in this artifact? Be as specific as possible."**

Wait for their response. Do NOT proceed until they describe the change.

If the description is vague, ask focused follow-up questions to make it precise. Challenge vague terms like "make it better" or "improve it" — ask _what specifically_ should be better.

---

## PHASE 3: ANALYZE THE CHANGE

Based on the artifact content and the user's request, perform a thorough analysis. You MUST address ALL of the following sub-phases:

### 3a. Impact Analysis

- What parts of the artifact will be affected by this change?
- Does the change alter the artifact's core behavior or just a detail?
- Could this change break existing functionality?

### 3b. Corner Cases

- What edge cases are connected to this change?
- What could the user NOT have predicted that you can see?
- What inputs or scenarios might produce unexpected results after the change?

### 3c. Improvement Proposals (max 3)

While analyzing, if you discover additional improvements that would make the artifact better — list **up to 3** proposals. Format:

> **Improvement proposals discovered during analysis:**
>
> 1. [proposal] — _why it matters_
> 2. [proposal] — _why it matters_
> 3. [proposal] — _why it matters_
>
> **Would you like to include any of these in the scope of changes?**

If no additional proposals come up, skip this part. Do NOT force proposals — only surface genuinely valuable ones.

### 3d. Example Walkthrough

Explain with a concrete example how the artifact would behave BEFORE and AFTER the change. Use a realistic scenario:

> **Example — Before the change:**
> If the user does X, the artifact currently does Y.
>
> **Example — After the change:**
> If the user does X, the artifact will now do Z instead.

This helps the user validate whether the change matches their intent.

### 3e. Risk Prediction

Explicitly surface what could go wrong when applying the proposed changes. Consider:

- Could the change cause silent failures or subtle behavioral regressions?
- Could it break compatibility with existing workflows or other artifacts that depend on this one?
- Are there scenarios where the change works in testing but fails in real usage?

Format:

> **Predicted risks:**
>
> - _Risk:_ [what could break or behave unexpectedly] — _Mitigation:_ [how to prevent or handle it]
> - _Risk:_ [what could break or behave unexpectedly] — _Mitigation:_ [how to prevent or handle it]

If no meaningful risks are identified, state: "No significant risks predicted for this change."

### 3f. Version Bump

Determine the appropriate version bump based on the `COMMITTED_VERSION` retrieved in Phase 1.

1. **Check if a bump is needed**: Compare the current file version against `COMMITTED_VERSION`. If the current file version is already higher than `COMMITTED_VERSION`, the version was already bumped in an earlier run — do NOT bump again. Inform the user: "Version already bumped from [COMMITTED_VERSION] to [current version] since last commit. No additional bump needed."

2. **Suggest a bump level** based on the nature of the change from Phase 3a:
   - **PATCH** (e.g., 1.0.0 → 1.0.1): Typo fixes, wording clarifications, formatting, bug fixes that don't change behavior.
   - **MINOR** (e.g., 1.0.0 → 1.1.0): New phases, new optional behavior, added capabilities, non-breaking additions.
   - **MAJOR** (e.g., 1.0.0 → 2.0.0): Removed phases, restructured output, renamed key concepts, breaking changes to how the artifact behaves.

3. **Present the suggestion**:

   > **Version bump:** `COMMITTED_VERSION` → `SUGGESTED_VERSION` (_[patch|minor|major]_ — [one-line reason])
   >
   > Override? Enter a different level (patch/minor/major) or "ok" to accept.

4. Wait for the user to confirm or override before proceeding.

5. **Version field location**:
   - For **skills** (files under `.claude/skills/`): set `metadata.version` in the YAML frontmatter.
   - For **commands, agents, hooks**: set top-level `version` in the YAML frontmatter.
   - If no version field exists, add it in the correct location.

---

## PHASE 4: CLARIFYING QUESTIONS

Before proceeding, ask ALL remaining questions you have about the change. Group them in a single message. Format:

> **Before I proceed, I need to clarify:**
>
> 1. [question]
> 2. [question]
>    ...

If you have zero questions, explicitly state: "No further questions — the scope is clear."

Wait for the user to answer before moving on.

---

## PHASE 5: CHANGE SUMMARY AND CONFIRMATION

Present a complete summary of ALL planned changes. Format:

> **Planned changes:**
>
> **1. [Change title]**
> _Description:_ What will be changed and why.
>
> **2. [Change title]**
> _Description:_ What will be changed and why.
>
> ...
>
> **Version:** `[current version]` → `[new version]` _(bump level)_
>
> **Affected files:**
>
> - `<file path 1>` — [what changes in this file]
> - `<file path 2>` — [what changes in this file]
>
> **Shall I apply these changes?** (yes/no)

Do NOT save anything until the user explicitly confirms with a clear affirmative (e.g., "yes", "go ahead", "do it", "confirm").

If the user says no or asks for adjustments, go back to the relevant phase and iterate.

---

## PHASE 6: APPLY CHANGES

Only after confirmation:

1. Apply all content changes to the affected files using the Edit tool (prefer editing over full rewrites).
2. Apply the version bump to the artifact's frontmatter:
   - For **skills**: update or add `metadata.version` in the YAML frontmatter.
   - For **commands, agents, hooks**: update or add top-level `version` in the YAML frontmatter.
3. After saving, display a final recap:

> **Changes applied:**
>
> - `<absolute file path 1>` — [brief description of what changed]
> - `<absolute file path 2>` — [brief description of what changed]
>
> All changes have been saved.

---

## RULES

- **NEVER** save or edit files without explicit user confirmation in Phase 5.
- **NEVER** skip the example walkthrough in Phase 3d — it is the user's primary validation tool.
- **NEVER** skip the risk prediction in Phase 3e.
- **NEVER** propose more than 3 improvement proposals.
- **NEVER** proceed past Phase 2 without a clear change description from the user.
- **ALWAYS** resolve the artifact name automatically — do not ask the user for file paths.
- **ALWAYS** ask before reading any referenced external file.
- **ALWAYS** use the git committed version (`COMMITTED_VERSION`) as the baseline for version bumps — never the current file version.
- **NEVER** bump the version if the current file version is already higher than `COMMITTED_VERSION`.
- **ALWAYS** add a version field if the artifact does not have one yet (`metadata.version` for skills, top-level `version` for commands/agents/hooks).
- If at any point the user changes their mind or wants to start over, reset to Phase 2.
