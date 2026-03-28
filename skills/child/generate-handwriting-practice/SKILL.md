---
name: generate-handwriting-practice
description: Generate a printable handwriting practice page (PDF) with a fun Polish educational story/fact for a 10-year-old child
metadata:
  version: 1.0.0
---

# Handwriting Practice Page Generator

Generate a printable A4 handwriting practice page for a 10-year-old child. The page contains a short, fun, educational story or fact in Polish, with each word displayed on a separate line alongside three handwriting guidelines for practice.

## Arguments

$ARGUMENTS should contain: page size (`half` or `full`, default: `full`), optionally followed by a topic.

Examples: `full`, `half`, `full fizyka`, `half natura`, `full historia`

Parse the arguments:

- If the first word is `half` or `full` → use it as size, rest is topic
- If no size keyword → default to `full`, treat everything as topic
- If no topic → pick a random interesting topic (science, nature, physics, chemistry, history, animals, space, weather, geology, biology)

## Step 1: Calculate word count

The script merges single-letter words (i, z, w, a, o, etc.) onto the same line as the next word, so they don't waste a practice row. Count only multi-letter words to determine how many practice lines are needed.

Based on page size (each multi-letter word = one practice row, rows are 15mm apart with 3mm margins):

- **full**: target **18 practice lines** — generate a text where the number of multi-letter words is exactly 18 (single-letter words like "i", "z", "w", "a", "o" are free and don't count)
- **half**: target **8 practice lines** — generate a text where the number of multi-letter words is exactly 8

## Step 2: Generate the Polish text

Generate a SHORT text in Polish — a fun, interesting fact or mini-story. Requirements:

- **Language**: Polish
- **Audience**: 10-year-old boy
- **Content**: Educational and fun — about science, nature, physics, chemistry, interesting historical facts, space, animals, or funny stories
- **Forbidden**: Nothing scary or violent
- **Word count**: MUST match the target from Step 1 exactly
- **Word complexity**: Avoid very long words (max ~12 characters per word). Use simple vocabulary appropriate for a child.
- **Coherence**: The text must form a complete, coherent, interesting fact or story even with the limited word count
- **Punctuation**: Follow standard Polish punctuation rules. Punctuation marks (commas, periods, exclamation marks, question marks, colons, semicolons, ellipses) must always be attached to the preceding word with no space before them — never as standalone tokens. When passing words to the script, include the punctuation as part of the word it follows (e.g. "serca," not "serca" + ","). Do NOT place punctuation marks as separate items in the word list.

Example (8 words): "Ośmiornice mają aż trzy serca i niebieską krew"
Example (18 words): "Błyskawica jest pięć razy gorętsza od powierzchni Słońca co jest naprawdę niesamowite i trwa tylko jedną krótką chwilę"

## Step 3: Generate the PDF

Run the Python script:

```bash
python .claude/skills/child/generate-handwriting-practice/scripts/generate_page.py --size SIZE --words "word1,word2,word3,..." --story "FULL STORY TEXT"
```

Where:

- `SIZE` is `half` or `full`
- `--words` is a comma-separated list of every word from the generated text
- `--story` is the complete story/fact text as a single string

The script will auto-install `fpdf2` on first run. The ElementarzDwa font must be installed in Windows user fonts.

## Step 4: Report to user

Tell the user:

1. The generated story/fact (so they know what their child will practice)
2. The filename of the generated PDF
3. That they can print it on A4 paper
