# create-presentation

Generate professional PowerPoint presentations (.pptx) from a topic, context, and presentation type (business or technical).

## Prerequisites

- **Python 3.8+** must be installed and available in your PATH
- **python-pptx** library:
  ```bash
  pip install python-pptx
  ```

## Usage

Invoke the skill in Claude Code:

```
/create-presentation
```

Then provide:
- **Topic materials** — paste text, reference files, or provide URLs
- **Type** — `business` or `technical`

### Optional Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `audience` | Engineers and product owners | Who will view the presentation |
| `goal` | Solution proposal | Purpose of the presentation |
| `time` | Content-driven (max 20 slides) | Presentation duration in minutes |
| `detail_level` | `medium` | `low`, `medium`, or `high` |

## How It Works

1. Claude parses your input materials (text, files, URLs)
2. Proposes a topic and goal for your confirmation
3. Shows a condensed slide structure for approval
4. Generates a JSON specification
5. Runs `generate_pptx.py` to produce the `.pptx` file
6. Saves to `docs/presentations/`

## Output

- `.pptx` file saved to `docs/presentations/<slugified-title>.pptx`
- Modern visual style with navy/grey/white palette and gold accents
- European Commission branding (replace `scripts/logo.png` with your logo)
- Actual charts and tables generated from data (bar, pie, line, tables)
- Speaker notes included

## Customization

### Logo
Replace `scripts/logo.png` with your organization's logo. Recommended size: 150x80px, transparent PNG.

### Colors
Edit the color constants at the top of `scripts/generate_pptx.py`:
- `NAVY` — primary dark color
- `ACCENT_BLUE` — primary accent
- `ACCENT_GOLD` — secondary accent

## Directory Structure

```
create-presentation/
├── SKILL.md              # Skill definition (prompt)
├── README.md             # This file
└── scripts/
    ├── generate_pptx.py  # PowerPoint generator
    └── logo.png          # Logo placeholder (replace with your own)
```
