---
name: extract-page-components
description: Scan ServiceNow Next Experience pages for a given feature, match elements against global component registry, produce page mapping and new components report. Reads URLs from test documentation, performs two-tier matching, flags low-confidence matches for human review.
metadata:
  version: 1.0.0
---

# Extract Page Components

You scan ServiceNow Next Experience (Polaris/UI Builder) pages for a given feature, match discovered interactive elements against a global component registry, and produce a page mapping file with parameterized Playwright locators. New components are added to the registry and reported separately. The output is designed to be consumed by downstream Page Object generation and component implementation skills.

**Tools required:** Playwright MCP server (`browser_navigate`, `browser_evaluate`, `browser_wait_for`)

---

## Step 1 — Parse inputs

Extract from `$ARGUMENTS`:

1. **featureName** (required) — kebab-case feature identifier (e.g., `incident-management`)
2. **storageStatePath** (optional, default: `D:\Repositories\grc-forge\auth\storageState.json`) — path to Playwright storage state JSON

Derive file paths from `featureName`:

- **Test documentation:** `docs/<featureName>/<featureName>-e2e-test-doc.md`
- **Component registry:** `specs/component-registry.json`
- **Output page mapping:** `specs/mappings/<featureName>.json`
- **Output new components report:** `specs/mappings/<featureName>-new-components.json`

---

## Step 2 — Pre-flight validation

Validate all required inputs before any browser interaction. Abort with an actionable error message on the first failure.

1. **Storage state file** — confirm file exists at `storageStatePath`. If not: abort with **"Storage state file not found at `<path>`. Update or regenerate it before running this skill."**

2. **Test documentation** — confirm `docs/<featureName>/<featureName>-e2e-test-doc.md` exists. If not: abort with **"Test documentation not found at `<path>`. Run Phase 1.1 (E2E Test Documentation) first."**

3. **README.md conventions** — read the project `README.md` and confirm it contains a section titled "Component Class Conventions". If not: abort with **"README.md is missing the 'Component Class Conventions' section. Add it before running this skill."**

4. **Component registry** — check if `specs/component-registry.json` exists:
   - If yes: read and parse it
   - If no: create it with initial content `{ "version": 1, "components": [] }` and proceed

5. **Extract URLs** — read the test documentation and extract all URLs from **Section 3 (Views & URLs)**. Parse the table rows to get `viewName` and `url` pairs. If Section 3 is missing or contains no URLs: abort with **"No URLs found in Section 3 (Views & URLs) of test documentation."**

6. **Read conventions** — read and retain the "Component Class Conventions" section from README.md for use in Step 5.

7. **Ensure output directory** — create `specs/mappings/` if it does not exist.

---

## Step 3 — Navigate and extract (per page)

For each URL extracted in Step 2, perform the following:

### 3a. Navigate and wait

1. Use `browser_navigate` to open the URL (pass storage state for authentication)
2. Wait for network idle
3. Wait an additional **5 seconds** settle delay (ServiceNow Next Experience loads dynamically)
4. Check the current URL — if it redirected to a login page (URL contains `/login` or `login.do`), abort with message: **"Authentication failed — update your storage state file at `<storageStatePath>`"**

### 3b. Extract element inventory

Execute a **single** `browser_evaluate` call with a JavaScript function that:

1. Uses `document.body` as the DOM root

2. Recursively traverses the entire DOM tree **including open shadow roots**:
   - For each element, check if it has a `shadowRoot` — if so, traverse into it
   - For closed shadow roots, mark the element as `opaque: true`

3. Finds all interactive elements matching ANY of:
   - Tag name starts with `now-` (ServiceNow web components)
   - Native tags: `input`, `select`, `textarea`, `button`
   - Elements with ARIA roles: `checkbox`, `textbox`, `combobox`, `radio`, `switch`, `slider`, `spinbutton`, `searchbox`, `listbox`, `menuitemcheckbox`, `menuitemradio`

4. Deduplicates — same DOM node found via multiple queries should appear once

5. For each element, captures:
   - `tagName`: lowercase tag name
   - `type`: the `type` attribute (for `<input>`) or null
   - `ariaRole`: the `role` attribute or implicit ARIA role
   - `label`: resolved via this priority chain:
     1. `aria-label` attribute -> labelSource: `"aria-label"`
     2. Associated `<label>` element (via `for`/`id` or wrapping) -> labelSource: `"label-element"`
     3. `placeholder` attribute -> labelSource: `"placeholder"`
     4. `name` attribute -> labelSource: `"name"`
     5. `id` attribute -> labelSource: `"id"`
     6. nth-of-type index (e.g., `"checkbox-3"`) -> labelSource: `"nth-index"`
   - `structuralHtml`: trimmed HTML showing the element's tag, key attributes (role, type, class), and first-level children structure. Strip instance-specific values (ids, dynamic classes). Cap at ~500 characters.
   - `parentWrapper`: immediate meaningful container tag + key attributes
   - `opaque`: boolean — true only if shadow root was closed

6. Returns the full inventory as a JSON array

If the page has rendering errors or the evaluate call fails, **abort** — do not produce partial results.

If no interactive elements are found on a page, log a warning: **"No interactive elements found on `<viewName>` (`<url>`)"** and continue to the next page.

---

## Step 4 — Classify into component classes (AI reasoning, per page)

Group the extracted elements by structural similarity before matching against the registry.

**Same class** = same tag name + same type/role + same structural HTML pattern

**Rules:**

- Two elements with identical behavior in Playwright belong to the same class
- Minor structural variations (e.g., one has helper text, one doesn't) -> **same class** with a `variants` array noting the differences and which instance labels belong to each variant
- The goal: one component class = one reusable Playwright interaction pattern
- Use the `now-*` tag name as `className` when available; otherwise derive from tag + type (e.g., `input-text`, `select-dropdown`)

For each class, produce an intermediate record:

- `tagName`: the element tag
- `ariaRole`: the element's ARIA role
- `structuralSignature`: normalized pattern like `now-input[type=text][role=textbox] > label + input`
- `exampleHtml`: one representative trimmed HTML snippet (~500 chars max)
- `instances`: array of `{ label, labelSource, ariaRole }`
- `variants`: array of `{ difference: string, instanceLabels: [string] }` or `null`
- `opaque`: boolean

---

## Step 5 — Match against global registry (AI reasoning)

For each component class produced in Step 4, perform two-tier matching against the global component registry loaded in Step 2.

### 5a. Primary match: tag name + ARIA role

Search the registry for a component where:

- `className` matches the element's `now-*` tag name (or derived name)
- AND the structural signature is compatible with the element's ARIA role

If a match is found: **high confidence**. Use the registry's `className`, `locatorStrategy`, and `locatorPattern`.

### 5b. Fallback match: structural HTML signature

If primary match fails, search the registry for a component where:

- `structuralSignature` matches the element's structural signature (fuzzy — allow minor variations)

If a match is found: **low confidence**. Use the registry's class name but flag with `confidence: "low"` and `confidenceReason` explaining why the match is uncertain.

### 5c. No match: new component

If neither tier matches:

1. Determine the proper `className` following the README.md "Component Class Conventions" section
2. Determine the best Playwright locator strategy in this priority order:
   - **`getByRole()`** with name parameter — preferred when ARIA role is present
   - **`getByLabel()`** — for form fields with associated labels
   - **CSS selector** — fallback for custom components without ARIA
3. Add the new component to an in-memory registry update list (do NOT write yet) with:
   - `className`
   - `structuralSignature`
   - `exampleHtml`
   - `locatorStrategy`: `"getByRole"` | `"getByLabel"` | `"css"`
   - `locatorPattern`: parameterized template string (e.g., `page.getByRole('checkbox', { name: '<label>' })`)
   - `supportedActions`: inferred list of actions (e.g., `["check", "uncheck"]` for checkboxes)
   - `filePath`: empty string (to be populated by Phase 2.2)
4. Mark this locator entry as `new: true` in the page mapping

### 5d. Build page mapping entries

For each element on the current page, produce a locator entry:

- `key`: camelCase identifier derived from the label (e.g., `activeCheckbox`)
- `label`: the resolved label text
- `component`: the matched or newly created `className`
- `new`: `true` if this component was not in the registry before this run, `false` otherwise
- `confidence`: `"high"` or `"low"` (only present if low)
- `confidenceReason`: explanation string (only present if low confidence)

---

## Step 6 — Write outputs

After processing ALL pages, write outputs in this order:

### 6a. Update global component registry

If new components were discovered:

1. Read the current `specs/component-registry.json` (to get the latest version number)
2. Increment the `version` field by 1
3. Append all new components to the `components` array
4. Write the updated file

If no new components were discovered, do not modify the registry.

### 6b. Write page mapping file

Write `specs/mappings/<featureName>.json`:

```json
{
  "featureName": "<featureName>",
  "timestamp": "<ISO 8601>",
  "pages": [
    {
      "view": "<viewName from Section 3>",
      "url": "<url>",
      "locators": [
        {
          "key": "activeCheckbox",
          "label": "Active",
          "component": "now-checkbox",
          "new": false
        },
        {
          "key": "descriptionField",
          "label": "Description",
          "component": "now-textarea",
          "new": true,
          "confidence": "low",
          "confidenceReason": "Matched by structural signature only — tag name differs from registry entry"
        }
      ]
    }
  ]
}
```

### 6c. Write new components report (only if new components found)

Write `specs/mappings/<featureName>-new-components.json`:

```json
{
  "featureName": "<featureName>",
  "newComponents": [
    {
      "className": "now-textarea",
      "structuralSignature": "now-textarea[role=textbox] > div.input-wrapper > textarea",
      "exampleHtml": "<now-textarea role=\"textbox\" aria-label=\"Description\">...</now-textarea>",
      "locatorStrategy": "getByRole",
      "locatorPattern": "page.getByRole('textbox', { name: '<label>' })",
      "suggestedActions": ["fill", "clear", "getValue"]
    }
  ]
}
```

### 6d. Report to the user

- File paths where outputs were saved
- Summary: number of pages scanned, total elements found, components matched vs. new
- Per-page breakdown: view name, locator count, any low-confidence matches
- List of new components added to the registry (if any)

---

## Abort conditions (stop immediately, do not create any output files)

- Storage state file not found
- Test documentation file not found
- README.md missing "Component Class Conventions" section
- No URLs found in Section 3 of test documentation
- Page redirects to login (authentication failure)
- DOM extraction script fails / page rendering errors
- `browser_evaluate` returns an error

Note: "No interactive elements found" on a single page is a **warning**, not an abort — continue to the next page. Only abort if ALL pages yield no elements.

## Important constraints

- **Pre-flight validation** — check all required inputs before any browser interaction
- **Single evaluate call per page** for DOM extraction — minimize browser round-trips
- **Registry writes are batched** — build all registry updates in memory across all pages, write once at the end to avoid inconsistencies on mid-scan abort
- **exampleHtml** capped at ~500 characters per class
- **Structural signatures** must strip instance-specific values (IDs, dynamic classes, GUIDs)
- **Do not** modify the page (no clicking, no form filling) — read-only analysis
- **Pierce open shadow roots** to find labels/roles, but classify by outer component tag
- **Closed shadow roots** -> classify by outer tag only, mark `opaque: true`
- **Component naming** — new components must follow README.md "Component Class Conventions" strictly; no temporary or placeholder names
