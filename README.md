# ai-grimoire

Spells for making AI do exactly what you want.

A development workspace for crafting and testing Claude Code **skills**, **commands**, **agents**, **hooks**, and **MCP servers**.

## Repository Structure

```
ai-grimoire/
├── .github/
│   └── workflows/       # CI/CD: validate-pr.yml, tag-artifact.yml
├── skills/              # Skill definitions (each in its own directory with SKILL.md)
├── commands/            # Custom slash commands (.md files or subdirectories)
├── agents/              # Agent definitions
├── hooks/               # Hook scripts (wired via .claude/settings.json)
├── mcp-servers/         # MCP server implementations
└── README.md
```

## Naming Convention

All artifacts (skills, commands, agents, hooks) follow a unified naming convention to ensure scalability, readability, and consistency.

### Structure

```
<domain>-<action>[-<modifier>]
```

| Segment | Required | Description |
|---------|----------|-------------|
| **Domain** | Yes | Functional area the artifact belongs to (e.g., `code`, `skill`, `jira`, `release`, `workflow`, `test`, `docs`, `mcp`, `component`) |
| **Action** | Yes | What the artifact does. Use consistent verbs from the approved list below |
| **Modifier** | No | Additional specialization (e.g., `advanced`, `business`, `story`, `page`) |

### Approved Verbs

Use these verbs consistently — do not mix synonyms.

| Verb | Use when... |
|------|-------------|
| `create` | Producing a structured artifact (ticket, story, document) |
| `generate` | Producing content or output (report, PDF, presentation) |
| `evaluate` | Scoring or assessing quality |
| `improve` | Iteratively enhancing an existing artifact |
| `refactor` | Restructuring without changing behavior |
| `validate` | Checking correctness or compliance |
| `extract` | Pulling data or components from a source |
| `implement` | Building something from a specification |
| `design` | Architecting structure or workflow |
| `deploy` | Publishing or installing artifacts |
| `list` | Enumerating available items |
| `review` | Comprehensive inspection across multiple criteria |
| `document` | Transforming information into structured documentation |

### Rules

- Always use **kebab-case** (`-` separator)
- Always start with a **domain** prefix
- Maximum **3 segments** (domain-action-modifier) — no deeper nesting
- Keep names **short but descriptive**
- Avoid unnecessary abbreviations
- No camelCase, no version suffixes, no generic names

### Artifact-Specific Guidance

| Artifact Type | Pattern | Examples |
|---------------|---------|----------|
| **Skill** | `<domain>-<action>[-<modifier>]` | `code-review`, `skill-evaluate`, `jira-create-story` |
| **Command** | `<domain>-<action>[-<modifier>]` | `skill-deploy`, `mcp-list-tools` |
| **Agent** | `<domain>-<role>` (noun-based) | `code-reviewer`, `test-runner`, `deploy-manager` |
| **Hook** | `<event>-<action>` | `precommit-lint`, `postmerge-notify` |

### Anti-Patterns

```
createSkill          # camelCase, no domain prefix
advancedSkillCreator # no grouping by domain
skillThingV2         # version in name
create-jira-story    # action-first instead of domain-first
```

### Scalability

The domain-first ordering supports natural growth:

```
skill-evaluate
skill-evaluate-quality
skill-evaluate-consistency
skill-improve
skill-improve-structure
skill-improve-performance
```

## Versioning

Artifacts use semantic versioning with a SNAPSHOT convention in their frontmatter:

| Version | Meaning | Install | Deploy | Tagged |
|---------|---------|---------|--------|--------|
| `1.0.0` | Stable release | Yes | Yes | Yes |
| `1.1.0-SNAPSHOT` | In development | Yes (with warning) | Blocked | No |

To release a SNAPSHOT version, remove the `-SNAPSHOT` suffix from the `version` field in the artifact's frontmatter.

### Git Tags

Every stable artifact version gets a git tag automatically when its PR is merged to `main`. Tags follow the format:

```
<artifact_type>/<artifact_name>@<version>
```

Examples:

| Tag | Meaning |
|-----|---------|
| `skills/jira-create-story@1.0.0` | Skill `jira-create-story` version 1.0.0 |
| `commands/skill-deploy@2.0.0` | Command `skill-deploy` version 2.0.0 |
| `hooks/precommit-lint@0.1.0` | Hook `precommit-lint` version 0.1.0 |

Tags are the source of truth for [ai-operation-manager](https://github.com/gszczutkowski/ai-operation-manager) — it uses them to discover, resolve, and install artifact versions.

### CI/CD Enforcement

Two GitHub Actions workflows enforce the versioning rules:

**`validate-pr.yml`** — runs on every PR to `main`:

- **One artifact per PR** — a PR may only touch files belonging to a single artifact. Changing multiple artifacts in one PR is rejected.
- **Version bump required** — the version in the artifact's frontmatter must be higher than the version on `main`.
- **Conventional Commits title** — the PR title must follow `type(scope): description` format (type must be lowercase).
- **Bump consistency** — the version bump must match the PR title:
  - `fix:`, `chore:`, `docs:`, etc. → at least a **patch** bump (e.g., `1.0.0` → `1.0.1`)
  - `feat:` → at least a **minor** bump (e.g., `1.0.0` → `1.1.0`)
  - `type!:` or `BREAKING CHANGE:` in body → at least a **major** bump (e.g., `1.0.0` → `2.0.0`)
- **SNAPSHOT allowed** — SNAPSHOT versions pass validation but will not be tagged on merge.

**`tag-artifact.yml`** — runs when a PR is merged to `main`:

- Detects the changed artifact and reads its version from frontmatter.
- Skips SNAPSHOT versions (no tag created).
- Creates an annotated git tag in the `<type>/<name>@<version>` format and pushes it.

#### Setup

Create a **`PAT_TOKEN`** repository secret (Settings → Secrets and variables → Actions) with a Personal Access Token that has `contents: write` permission. Tags pushed with the default `GITHUB_TOKEN` do not trigger downstream workflows — this is a GitHub limitation.

### Developer Workflow Example

Suppose you want to add a new output format to the `jira-create-story` skill (currently at version `1.0.0`).

**1. Create a feature branch:**

```bash
git checkout -b feat/jira-story-table-output
```

**2. Make your changes:**

Edit `skills/jira-create-story/SKILL.md` — add the new output format logic.

**3. Bump the version in frontmatter:**

Since this is a new feature, bump the minor version:

```yaml
# Before
metadata:
  version: 1.0.0

# After
metadata:
  version: 1.1.0
```

**4. Commit and push:**

```bash
git add skills/jira-create-story/SKILL.md
git commit -m "feat: add table output format to jira-create-story"
git push -u origin feat/jira-story-table-output
```

**5. Open a PR with a Conventional Commits title:**

```
feat: add table output format to jira-create-story
```

> The `feat:` prefix tells CI to expect at least a minor bump. Since you went from `1.0.0` → `1.1.0`, validation passes.

**6. CI validates the PR:**

- Only `skills/jira-create-story` was changed — single-artifact rule passes.
- Version bumped from `1.0.0` to `1.1.0` — bump detected.
- `feat:` requires at least minor — `1.0.0` → `1.1.0` is minor — consistency passes.
- Tag `skills/jira-create-story@1.1.0` does not exist yet — uniqueness passes.

**7. Merge the PR:**

On merge, the `tag-artifact` workflow automatically creates and pushes the tag:

```
skills/jira-create-story@1.1.0
```

The skill is now discoverable and installable via `aom` at version `1.1.0`.

#### Quick Reference: What Bump Do I Need?

| I am doing… | PR title prefix | Minimum bump |
|-------------|-----------------|--------------|
| Fixing a typo or bug | `fix:` | Patch (`1.0.0` → `1.0.1`) |
| Adding a new capability | `feat:` | Minor (`1.0.0` → `1.1.0`) |
| Changing behavior in a breaking way | `feat!:` or `fix!:` | Major (`1.0.0` → `2.0.0`) |
| Refactoring internals | `refactor:` | Patch (`1.0.0` → `1.0.1`) |
| Updating docs within a skill | `docs:` | Patch (`1.0.0` → `1.0.1`) |
| Starting work on a new version | any | Use `-SNAPSHOT` suffix (no tag) |

## Deploy

**Deploy** copies artifacts to global `~/.claude/` so they're available in all projects. SNAPSHOT versions are blocked. Use the `/deploy-skills` command inside Claude Code:

```
/deploy-skills          # Deploy all stable artifacts globally
/deploy-skills undeploy # Remove all deployed artifacts
```

## Skills Documentation

| Skill | New Name | Description |
|-------|----------|-------------|
| **code-review** | `code-review` | Comprehensive code review across 10 quality categories with scored Markdown report |
| **create-business-docs** | `docs-create-business` | Generate standardized business documentation from raw input documents |
| **create-jira-story** | `jira-create-story` | Generate a Jira ticket description from a standard template (quick or guided mode) |
| **create-release-notes** | `release-create-notes` | Generate a Release Notes markdown file for a GRC system fix version |
| **create-story-release-notes** | `release-create-story-notes` | Generate a Release Notes markdown file for specific Jira issues |
| **design-workflow** | `workflow-design` | Architect multi-skill workflows with data contracts and Mermaid diagrams |
| **e2e-test-documentation** | `test-document-e2e` | Transform business documentation into structured test-oriented documentation |
| **evaluate-skill** | `skill-evaluate` | Adversarial evaluator that scores a skill/command definition across 22 criteria |
| **evaluate-workflow** | `workflow-evaluate` | Adversarial evaluator that scores a workflow architecture across five criteria |
| **extract-page-components** | `component-extract-page` | Scan ServiceNow Next Experience pages and match elements against component registry |
| **generate-handwriting-practice** | `child-generate-handwriting` | Generate a printable handwriting practice page (PDF) for a child |
| **implement-missing-components** | `component-implement-missing` | Implement TypeScript component classes for newly discovered ServiceNow components |

## Commands Documentation

| Command | New Name | Description |
|---------|----------|-------------|
| **list-mcp-tools** | `mcp-list-tools` | List all available tools with descriptions for a given MCP server |
| **skill/create-advanced-skill** | `skill-create-advanced` | Transform a vague idea into a fully specified, implementation-ready AI skill |
| **skill/deploy-skills** | `skill-deploy` | Deploy or undeploy all local project artifacts to global `~/.claude/` |
| **skill/improve-skill-definition** | `skill-improve` | Iteratively improve, fix, or extend an existing skill, command, or agent |

## Artifact Types at a Glance

| Type | Location | Purpose |
|------|----------|---------|
| **Skill** | `skills/` | Reusable prompt routines invoked via `/skill-name` |
| **Command** | `commands/` | Custom slash commands for common workflows |
| **Agent** | `agents/` | Specialized sub-agents spawned by the Agent tool |
| **Hook** | `hooks/` | Shell scripts triggered by Claude Code events |
| **MCP Server** | `mcp-servers/` | Model Context Protocol server implementations |
