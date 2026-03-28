---
name: e2e-test-documentation
description: Transform business documentation into structured, test-oriented Markdown documentation for E2E test creation. Extracts views/URLs, fields, user flows, actors, business rules, error states, and test data requirements. Flags ambiguities as open questions.
metadata:
  version: 1.0.0
---

# E2E Test Documentation

You transform business documentation into structured, test-oriented Markdown documentation. Your output is designed to be consumed by downstream skills in the E2E test creation workflow (business test plan, component scan, page object creation, test data provisioning).

---

## Step 1 — Parse inputs

Extract from `$ARGUMENTS`:

1. **featureName** (required) — kebab-case feature identifier (e.g., `incident-management`)
2. **additionalDocs** (optional) — comma-separated list of additional file paths to read (`.txt`, `.md`)

Derive file paths from `featureName`:

- **Business documentation (primary input):** `docs/<featureName>-business.md`
- **Output directory:** `docs/<featureName>/`
- **Output file:** `docs/<featureName>/<featureName>-e2e-test-doc.md`

---

## Step 2 — Pre-flight validation

Validate all required inputs before processing. Abort with an actionable error message on the first failure.

1. **Business documentation** — confirm `docs/<featureName>-business.md` exists. If not: abort with **"Business documentation not found at `docs/<featureName>-business.md`. Run `create-business-docs` first."**

2. **Additional documents** — if `additionalDocs` is provided, confirm each file exists. If any file is missing: abort with **"Additional document not found at `<path>`. Check the file path and try again."**

3. **Ensure output directory** — create `docs/<featureName>/` if it does not exist.

4. **Check for existing output** — if `docs/<featureName>/<featureName>-e2e-test-doc.md` already exists, warn the user: **"Existing E2E test documentation found. Proceeding will overwrite it."** Wait for user confirmation before continuing.

---

## Step 3 — Read all source documents

Read and retain the full content of:

1. **Primary:** `docs/<featureName>-business.md`
2. **Additional:** each file listed in `additionalDocs` (if provided)

---

## Step 4 — Extract test-relevant information

Analyze all source documents and extract the following categories of information. For each category, be exhaustive — capture everything that is test-relevant, even if it seems minor.

### 4.1 — Test Scope

- Identify all features and capabilities described in the documentation
- Determine what is explicitly in scope for testing
- Identify anything explicitly stated as out of scope
- If scope is unclear, list what you believe is in scope and flag it as an open question

### 4.2 — Actors & Roles

- Extract all user roles, personas, or actors mentioned
- For each actor, capture:
  - Role name (exact as in documentation)
  - Role description / responsibilities
  - Required credentials or setup (if mentioned)
- If credential/setup details are missing, flag as an open question

### 4.3 — Views & URLs

- Extract all page views, screens, or URLs referenced
- For each view, capture:
  - View name (exact as in documentation)
  - URL or URL pattern (if provided)
  - Purpose / what the view is used for
- If URLs are missing for known views, flag as an open question

### 4.4 — Fields & Components per View

- For each view identified in 4.3, extract all fields and interactive components
- For each field, capture:
  - Field name (exact as in documentation)
  - Type (text input, dropdown, checkbox, date picker, reference field, etc.)
  - Whether the field is required or optional
  - Validation rules (if mentioned)
  - Possible values or value constraints (if mentioned)
- If field types or validation rules are not specified, infer from context where reasonable and mark inferred values with `(inferred)`. If inference is not possible, flag as an open question.

### 4.5 — User Flows (Testable)

- Extract all user workflows, processes, or sequences of actions
- Reformulate each flow as testable steps with:
  - Preconditions (what must be true before the flow starts)
  - Numbered steps (concrete, observable actions)
  - Expected result (what should happen at the end)
  - Postconditions (what state the system should be in after)
- If a flow lacks clear expected results or preconditions, flag as an open question

### 4.6 — Business Rules

- Extract all business rules, conditions, and logic constraints
- For each rule, capture:
  - Rule identifier or short name
  - The rule itself (plain language)
  - Trigger (what causes the rule to fire)
  - Expected behavior when triggered

### 4.7 — Error States & Edge Cases

- Identify potential error states and edge cases, including:
  - States explicitly mentioned in the documentation
  - States reasonably inferred from the described functionality (mark as `(inferred)`)
- For each, capture:
  - Scenario description
  - Trigger condition
  - Expected behavior / error handling

### 4.8 — Test Data Requirements

- Extract all test data needs implied by the flows, actors, and business rules
- For each data entity, capture:
  - Entity type (user, record, configuration, etc.)
  - Required attributes
  - Required state (e.g., active, approved, draft)
  - Purpose (which flows or tests need this data)

---

## Step 5 — Identify gaps and open questions

Review all extracted information and compile a list of gaps:

- Flows without clear expected results
- Fields without defined types or validation rules (that could not be inferred)
- Missing preconditions or postconditions
- Actors without credential/setup information
- Views mentioned but without URLs
- Any contradictions or ambiguities in the source documents

**Critical rule:** Flag ambiguous or missing information as open questions. NEVER guess or fabricate information to fill gaps. Clearly state what is missing and why it matters for testing.

---

## Step 6 — Generate output document

Generate the structured Markdown document at `docs/<featureName>/<featureName>-e2e-test-doc.md` using the **exact** template structure below. Every section is required — if a section has no content, include it with a note explaining why (e.g., "No business rules identified in source documentation.").

```markdown
# <Feature Name> — E2E Test Documentation

> **Source:** `docs/<featureName>-business.md`
> **Generated:** <current date>
> **Version:** 1.0

## 1. Test Scope

- **Features under test:**
  - <list>
- **Out of scope:**
  - <list or "None identified">

## 2. Actors & Roles

| Actor  | Role          | Credentials/Setup  |
| ------ | ------------- | ------------------ |
| <name> | <description> | <details or "TBD"> |

## 3. Views & URLs

| View Name | URL            | Purpose   |
| --------- | -------------- | --------- |
| <name>    | <url or "TBD"> | <purpose> |

## 4. Fields & Components per View

### 4.1 <View Name>

| Field Name | Type   | Required | Validation Rules            | Possible Values   |
| ---------- | ------ | -------- | --------------------------- | ----------------- |
| <name>     | <type> | Yes/No   | <rules or "None specified"> | <values or "N/A"> |

<!-- Repeat subsection for each view -->

## 5. User Flows (Testable)

### 5.1 <Flow Name>

- **Preconditions:** <list>
- **Steps:**
  1. <action>
  2. <action>
- **Expected Result:** <outcome>
- **Postconditions:** <state after flow>

<!-- Repeat subsection for each flow -->

## 6. Business Rules

| Rule ID | Rule   | Trigger   | Expected Behavior |
| ------- | ------ | --------- | ----------------- |
| BR-01   | <rule> | <trigger> | <behavior>        |

## 7. Error States & Edge Cases

| Scenario   | Trigger   | Expected Behavior |
| ---------- | --------- | ----------------- |
| <scenario> | <trigger> | <behavior>        |

## 8. Test Data Requirements

| Entity   | Attributes   | State   | Purpose   |
| -------- | ------------ | ------- | --------- |
| <entity> | <attributes> | <state> | <purpose> |

## 9. Open Questions

| #   | Question   | Section                    | Impact                       |
| --- | ---------- | -------------------------- | ---------------------------- |
| 1   | <question> | <which section it affects> | <why it matters for testing> |
```

---

## Step 7 — Present output to user

After writing the file:

1. Summarize what was generated:
   - Number of actors identified
   - Number of views/URLs captured
   - Total fields across all views
   - Number of user flows
   - Number of business rules
   - Number of error states / edge cases
   - Number of test data requirements
   - **Number of open questions** (highlight if > 0)

2. If there are open questions, recommend the user reviews Section 9 and resolves them before proceeding to Phase 1.2 (Business Test Plan).

3. Remind the user of the downstream consumers:
   - **Phase 1.2 (Business Test Plan):** reads the full document
   - **Phase 2.1 (Component Scan):** reads Sections 3 and 4
   - **Phase 3.1 (Page Object Creation):** reads Sections 4 and 5
   - **Phase 4.1 (Test Data Script Creation):** reads Sections 2 and 8

---

## Constraints

- **Preserve exact names.** URLs, field names, role names, and view names must be preserved exactly as they appear in the source documentation. Do not rephrase or normalize them.
- **Flag, don't guess.** When information is ambiguous or missing, add it to Section 9 (Open Questions). Never fabricate details.
- **Infer conservatively.** When inferring field types or edge cases from context, always mark them with `(inferred)` so the user can verify.
- **Complete structure.** Every section of the output template must be present, even if empty with an explanation.
- **Single source of truth.** The output document becomes the canonical test-oriented reference for the feature. It must be self-contained — a reader should not need to go back to the business documentation to understand what to test.
