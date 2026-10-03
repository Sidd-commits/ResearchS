# AGENTS.md — ResearchS

## Mission

Continue development of the existing **ResearchS** project using the actual repository as the source of truth and `PROJECT_CONTEXT.md` as historical project context.

ResearchS is intended to become an AI-powered research assistant that can search research papers, accept PDF uploads, process paper content, compare pretrained transformer models, generate summaries, and answer questions about research papers.

## Mandatory First Steps

Before changing any code:

1. Read `PROJECT_CONTEXT.md`.
2. Inspect the complete repository structure.
3. Inspect the relevant existing source files.
4. Determine what is actually implemented.
5. Compare the implementation with the historical project context.
6. Identify the smallest safe next implementation step.

Do **not** start by rewriting the project.

## Source of Truth

Use this priority order:

1. Actual working repository/code
2. Current runtime behavior and test results
3. `PROJECT_CONTEXT.md`
4. Historical assumptions from the previous ChatGPT conversation

`PROJECT_CONTEXT.md` records what the previous development conversation intended. It does not prove that every planned feature or file currently exists.

If the code and historical context disagree, preserve working code and explain the discrepancy before making a substantial architectural change.

## Current Development Direction

The historical project is currently around **Step 16**.

The immediate intended functionality is:

```text
React Frontend
      ↓
PDF Upload
      ↓
FastAPI
      ↓
Validate PDF
      ↓
Temporarily Save PDF
      ↓
Return File Information
      ↓
Frontend Displays Result
```

If repository inspection confirms that Step 16 is incomplete, implement it before moving to later steps.

## Development Roadmap

Follow this general sequence unless the actual repository gives a strong reason to adjust it:

1. PDF upload
2. PDF text extraction
3. Text cleaning and chunking
4. FLAN-T5 inference
5. BART inference
6. LongT5 inference
7. Mistral 7B inference
8. Model comparison
9. Evaluation
10. Model selection
11. PDF-based chatbot
12. arXiv integration
13. Complete frontend/backend integration

Do not skip ahead merely because a later feature sounds interesting.

## AI Model Strategy

Use pretrained models.

Do **not** train FLAN-T5, BART, LongT5, or Mistral 7B from scratch unless the user explicitly changes the project requirements.

The intended workflow is:

```text
Pretrained Model
      ↓
Load in Python
      ↓
Provide processed research-paper text
      ↓
Generate output
      ↓
Evaluate
      ↓
Compare
```

Introduce models incrementally.

Mistral 7B may be resource-intensive. Do not install or run every large model simultaneously without checking the available hardware and project requirements.

## Architecture Rules

Prefer the existing architecture.

Do not introduce:
- A new frontend framework
- A new backend framework
- A new database
- A new state-management system
- A new model-serving architecture

unless the existing implementation genuinely requires it or the user explicitly asks for it.

Reuse existing components, services, utilities, and configuration.

Avoid duplicate implementations.

## Frontend Rules

The existing frontend is React/JavaScript.

Before changing UI:
- Inspect existing components.
- Preserve working design and interactions.
- Keep the ResearchS identity consistent.
- Avoid replacing the entire UI for a small feature.
- Ensure responsive behavior remains intact.

If an API integration is required, keep API calls organized rather than scattering duplicated fetch logic throughout components.

## Backend Rules

The backend is Python/FastAPI.

Before changing an endpoint:
- Inspect the existing FastAPI application.
- Preserve existing routes.
- Follow the existing project structure.
- Validate inputs.
- Return clear errors.
- Do not expose internal paths or secrets unnecessarily.

For file uploads:
- Validate file type.
- Avoid unsafe filenames/path traversal.
- Use controlled upload locations.
- Do not permanently retain files unless the product requirements require it.
- Handle failures cleanly.

## Dependencies

Before installing a package:

1. Check whether it is already installed.
2. Check whether the current stack already provides the functionality.
3. Prefer a lightweight, established dependency.
4. Avoid installing large ML packages prematurely.
5. Avoid unnecessary dependencies.

For ML dependencies, consider the user's available hardware before adding resource-heavy models.

## Environment and Secrets

Never hard-code:
- API keys
- Access tokens
- Passwords
- Private credentials
- Database passwords

Use environment variables where credentials are required.

Never commit `.env` files containing secrets.

## Testing Rules

After making a change:

1. Run the relevant backend/frontend checks.
2. Test the affected functionality.
3. Inspect errors rather than assuming success.
4. Confirm the existing functionality still works.
5. Report what was tested.

Do not say "working" solely because the code was written.

## Change Discipline

For each task:

- Make the smallest coherent change.
- Avoid unrelated refactoring.
- Avoid changing multiple architectural layers unnecessarily.
- Do not replace complete files when a focused modification is sufficient.
- Preserve existing behavior unless the task requires changing it.

If a larger refactor is genuinely necessary, explain why before doing it.

## Communication

Before substantial implementation, briefly state:
- What you found
- What you intend to change
- Any important discrepancy or risk

After implementation, report:
- Files changed
- What was implemented
- Tests/checks performed
- Any remaining limitation

Do not invent test results.

## Historical Context

The previous development conversation used numbered steps and instructed the user to confirm completion before continuing.

Maintain the logical progression of that roadmap, but do not require the user to manually repeat information that is already available in `PROJECT_CONTEXT.md`.

## Important Final Rule

**Inspect first. Modify second. Test third.**

Never assume that the historical ChatGPT conversation accurately describes the current repository state.
