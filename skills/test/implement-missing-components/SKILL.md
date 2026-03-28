---
name: implement-missing-components
description: Implement TypeScript component classes for newly discovered ServiceNow components and update the global component registry with file paths. Reads the new components report from Phase 2.1, generates TS classes following base class conventions, and operates in plan-then-confirm mode.
metadata:
  version: 0.1.0
---

# Implement Missing Components

You implement TypeScript component classes for newly discovered ServiceNow web components. You read a new components report (output of the `extract-page-components` skill / Phase 2.1), generate TypeScript classes following the project's base class conventions, and update the global component registry with file paths to the new implementations.

You operate in **plan-then-confirm** mode: first present what you will create, then implement only after user approval.

---

## Step 1 — Resolve input file

Determine the new components report path from `$ARGUMENTS`:

- If a **file path** is provided (e.g., `specs/mappings/risk-management-new-components.json`), use it directly.
- If a **feature name** is provided (e.g., `risk-management`), derive the path: `specs/mappings/<feature-name>-new-components.json`
- If nothing is provided, ask:
  > **Which feature's new components should I implement? Provide the feature name or path to the new-components report.**

Extract `featureName` from the report filename by stripping the `-new-components.json` suffix and the directory prefix.

---

## Step 2 — Pre-flight validation

Validate all required inputs before generating any code. Abort with an actionable error on the first failure.

1. **New components report** — confirm the file exists at the resolved path. If not: abort with **"New components report not found at `<path>`. Run Phase 2.1 (extract-page-components) first."**

2. **Component registry** — confirm `specs/component-registry.json` exists. If not: abort with **"Component registry not found at `specs/component-registry.json`. Run Phase 2.1 first or create an initial registry."**

3. **README.md conventions** — read the project `README.md` and confirm it contains a section titled **"Component Class Conventions"**. If not: abort with **"README.md is missing the 'Component Class Conventions' section. Add it before running this skill."**

4. **Parse inputs:**
   - Read and parse the new components report JSON
   - Read and parse the component registry JSON
   - Read and retain the "Component Class Conventions" section from README.md

5. **Validate report is non-empty** — if `newComponents` array is empty: abort with **"New components report contains no components. Nothing to implement."**

6. **Check for already-implemented components** — for each component in the report, check the registry:
   - If the component already has a non-empty `filePath` in the registry AND the file exists on disk: skip it (already implemented)
   - Log skipped components as: **"Skipping `<className>` — already implemented at `<filePath>`"**
   - If ALL components are already implemented: report this and exit gracefully

---

## Step 3 — Read conventions and existing code

1. **Parse the "Component Class Conventions" section** from README.md. Extract:
   - Base class or interface name and import path
   - File location pattern (where component files should be placed)
   - File naming convention
   - Class naming convention
   - Required method signatures per action type
   - Any additional patterns (constructor, locator setup, etc.)

2. **Read the base class/interface file** referenced in the conventions. Understand:
   - Constructor signature
   - Abstract or required methods
   - Available utility methods
   - Type imports needed

3. **Read up to 2 existing component class files** (if any exist) to understand the concrete implementation pattern in practice. Pick components from the registry that have a populated `filePath`. This provides a real-world template beyond what the conventions document.

---

## Step 4 — Generate implementation plan

For each component to implement, produce a plan entry:

```
Component: <className>
  File path: <target file path per conventions>
  Base class: <base class name>
  Actions to implement: <list from suggestedActions>
  Methods:
    - <methodName>(args): <brief description>
    - ...
  Locator strategy: <from report>
  Locator pattern: <from report>
```

Present the full plan to the user:

> **Implementation Plan for `<featureName>`**
>
> I will create **N** component class files and update the component registry.
>
> <plan entries>
>
> **Shall I proceed?**

**Do NOT generate any code or write any files until the user confirms.**

If the user requests changes to the plan, adjust and re-present. Only proceed when the user approves.

---

## Step 5 — Implement component classes

After user confirmation, for each component in the plan:

### 5a. Generate TypeScript class

Create a TypeScript file following the conventions from Step 3. The class must:

1. **Import** the base class/interface and any required types
2. **Extend or implement** the base class/interface
3. **Set up the locator** in the constructor or as a class property, using the `locatorStrategy` and `locatorPattern` from the report
4. **Implement a method for each action** listed in `suggestedActions`:
   - Method name follows the conventions (e.g., `fill`, `click`, `check`, `getValue`)
   - Method body uses the Playwright locator pattern from the report
   - Method includes appropriate `await` for async Playwright operations
   - Method signatures match the base class requirements
5. **Include no placeholder or TODO comments** — every method must have a complete, functional implementation
6. **Include no extraneous methods** beyond what `suggestedActions` requires and the base class mandates

### 5b. Write the file

- Ensure the target directory exists (create if needed)
- Write the TypeScript file to the path determined in Step 4
- Do NOT overwrite any existing file. If the target path already exists: abort for that component with **"File already exists at `<path>` — skipping `<className>` to avoid overwriting. Investigate manually."**

---

## Step 6 — Update component registry

After ALL component files are written:

1. Re-read `specs/component-registry.json` (to avoid stale data)
2. For each newly implemented component, find its entry in the registry by `className` and update the `filePath` field to the relative path of the new TypeScript file
3. If a component from the report is NOT found in the registry: log a warning **"Component `<className>` not found in registry — cannot update filePath. Add it manually."**
4. Write the updated registry file

---

## Step 7 — Report to the user

Present a summary:

- **Files created:** list each file path
- **Registry updated:** number of components with `filePath` populated
- **Skipped:** any components that were already implemented or had conflicts
- **Warnings:** any issues encountered (missing registry entries, etc.)

---

## Abort conditions

Stop immediately and do not write any files if:

- New components report not found
- Component registry not found
- README.md missing "Component Class Conventions" section
- New components report is empty
- Base class/interface file referenced in conventions does not exist
- User declines the implementation plan

---

## Important constraints

- **Plan-then-confirm** — never write code without user approval of the plan
- **Never modify existing component classes** — this skill only creates new ones
- **Never overwrite existing files** — abort for that component if the file exists
- **Follow conventions strictly** — all naming, structure, and patterns must match README.md "Component Class Conventions"
- **Implement all suggested actions** — every action in `suggestedActions` must have a corresponding method
- **No placeholder code** — every method must be fully implemented
- **Registry updates are batched** — read once, update all, write once
- **File paths in registry must be relative** to the project root

---

## Expected "Component Class Conventions" README section

This skill expects the README.md "Component Class Conventions" section to define at minimum:

1. **Base class or interface** — name, import path, and what it provides (e.g., `BaseComponent` from `src/components/base-component.ts`)
2. **File location** — directory where component files are placed (e.g., `src/components/`)
3. **File naming** — convention for file names (e.g., `<ClassName>.ts`, `<class-name>.component.ts`)
4. **Class naming** — how to derive the TypeScript class name from the component's `className` in the registry (e.g., PascalCase of the `now-*` tag: `now-checkbox` → `NowCheckbox`)
5. **Constructor pattern** — how the locator is passed/configured (e.g., `constructor(page: Page, locator: Locator)`)
6. **Method naming** — how action names map to method names (e.g., `fill` → `async fill(value: string)`)
7. **Method signatures per action type** — expected argument types and return types for common actions (`fill`, `click`, `check`, `uncheck`, `select`, `getValue`, `isVisible`, `isEnabled`, etc.)
8. **Required imports** — standard imports every component file needs (e.g., Playwright types)
9. **Export pattern** — how the class is exported (default export, named export, re-exported from an index file)
