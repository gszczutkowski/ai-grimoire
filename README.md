# ai-grimoire

Spells for making AI do exactly what you want.

A development workspace for crafting and testing Claude Code **skills**, **commands**, **agents**, **hooks**, and **MCP servers**.

## Repository Structure

```
ai-grimoire/
├── skills/              # Skill definitions
├── commands/            # Custom slash commands
├── agents/              # Agent definitions
├── hooks/               # Hook scripts (wired via .claude/settings.json)
├── mcp-servers/         # MCP server implementations
├── templates/           # Scaffolding templates for new artifacts
│   ├── skill.template.md
│   ├── command.template.md
│   ├── agent.template.md
│   └── hook.template.sh
├── docs/
│   └── guides/          # How-to guides and design notes
├── examples/            # Example usage and demos
├── scripts/
│   ├── install.sh       # Install artifacts to a local project for testing
│   ├── deploy.sh        # Deploy stable artifacts to global ~/.claude/
│   └── validate.sh      # Lint frontmatter on all artifacts
├── CLAUDE.md            # Project instructions for Claude Code
└── README.md
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
| `skills/create-jira-story@1.0.0` | Skill `create-jira-story` version 1.0.0 |
| `commands/deploy-skills@2.0.0` | Command `deploy-skills` version 2.0.0 |
| `skills/child/painter@1.2.3` | Nested skill `child/painter` version 1.2.3 |
| `hooks/pre-commit@0.1.0` | Hook `pre-commit` version 0.1.0 |

Tags are the source of truth for [ai-operation-manager](https://github.com/your-org/ai-operation-manager) — it uses them to discover, resolve, and install artifact versions.

### CI/CD Enforcement

Two GitHub Actions workflows enforce the versioning rules:

**`validate-pr.yml`** — runs on every PR to `main`:

- **One artifact per PR** — a PR may only touch files belonging to a single artifact. Changing multiple artifacts in one PR is rejected.
- **Version bump required** — the version in the artifact's frontmatter must be higher than the version on `main`.
- **Conventional Commits title** — the PR title must follow `type(scope): description` format.
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

Suppose you want to add a new output format to the `create-jira-story` skill (currently at version `1.0.0`).

**1. Create a feature branch:**

```bash
git checkout -b feat/jira-story-table-output
```

**2. Make your changes:**

Edit `skills/create-jira-story/SKILL.md` — add the new output format logic.

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
git add skills/create-jira-story/SKILL.md
git commit -m "feat: add table output format to create-jira-story"
git push -u origin feat/jira-story-table-output
```

**5. Open a PR with a Conventional Commits title:**

```
feat: add table output format to create-jira-story
```

> The `feat:` prefix tells CI to expect at least a minor bump. Since you went from `1.0.0` → `1.1.0`, validation passes.

**6. CI validates the PR:**

- Only `skills/create-jira-story` was changed — single-artifact rule passes.
- Version bumped from `1.0.0` to `1.1.0` — bump detected.
- `feat:` requires at least minor — `1.0.0` → `1.1.0` is minor — consistency passes.
- Tag `skills/create-jira-story@1.1.0` does not exist yet — uniqueness passes.

**7. Merge the PR:**

On merge, the `tag-artifact` workflow automatically creates and pushes the tag:

```
skills/create-jira-story@1.1.0
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

## Install & Deploy

**Install** copies artifacts to a local project's `.claude/` folder for testing. SNAPSHOT versions are allowed (with a warning).

```bash
# Install all skills to a project
./scripts/install.sh ~/projects/my-app --skills

# Install a specific skill
./scripts/install.sh ~/projects/my-app --skills create-presentation

# Install everything
./scripts/install.sh ~/projects/my-app --all
```

**Deploy** copies artifacts to global `~/.claude/` so they're available in all projects. SNAPSHOT versions are blocked.

```bash
# Deploy all stable skills globally
./scripts/deploy.sh --skills

# Deploy a specific skill
./scripts/deploy.sh --skills create-presentation

# Deploy everything stable
./scripts/deploy.sh --all
```

## Creating New Artifacts

Use the templates in `templates/` as starting points:

```bash
# New skill
cp templates/skill.template.md skills/my-skill.md

# New command
cp templates/command.template.md commands/my-command.md

# New agent
cp templates/agent.template.md agents/my-agent.md

# New hook
cp templates/hook.template.sh hooks/my-hook.sh
```

## Validation

Run the validation script to check that all artifacts have required frontmatter:

```bash
./scripts/validate.sh
```

## Skills Documentation

| Skill | Description | Docs |
|-------|-------------|------|
| **create-presentation** | Generate professional .pptx presentations (business/technical) | [README](skills/create-presentation/README.md) |

## Artifact Types at a Glance

| Type | Location | Purpose |
|------|----------|---------|
| **Skill** | `skills/` | Reusable prompt routines invoked via `/skill-name` |
| **Command** | `commands/` | Custom slash commands for common workflows |
| **Agent** | `agents/` | Specialized sub-agents spawned by the Agent tool |
| **Hook** | `hooks/` | Shell scripts triggered by Claude Code events |
| **MCP Server** | `mcp-servers/` | Model Context Protocol server implementations |
