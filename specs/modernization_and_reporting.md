# Modernization & Reporting — Technical Specification

**Status:** Implemented (2026-03-25)  
**Related:** [excel_reporting.md](./excel_reporting.md)

## 1. Purpose

This document specifies:

1. Migration from the legacy **`google-generativeai`** package to **`google-genai`** (unified Google Gen AI SDK for Python).
2. Hardening of session Excel reporting (`tests/conftest.py` + `utils/excel_writer.py`) for dependency, filesystem, and parametrized-test edge cases.
3. A controlled approach to **`FutureWarning`** noise from dependencies.

No production code changes should be merged until this spec is explicitly approved.

---

## 2. Baseline (current repository)

| Area | Location | Current behavior |
|------|----------|------------------|
| Gemini integration | `utils/gemini_provider.py` | `import google.generativeai as genai`; `genai.configure(api_key=...)`; `GenerativeModel(name).generate_content(prompt)`; `response.text` |
| Judge selection | `utils/judge_factory.py` | `LLM_TYPE=openai` → `OpenAIProvider()`, on failure → `GeminiProvider()`; `LLM_TYPE=gemini` → `GeminiProvider()` only |
| Result aggregation | `tests/conftest.py` | Module-level `results_table: list[dict]`; `pytest_runtest_makereport` appends one row per test **call** phase |
| Excel export | `tests/conftest.py` | Session `export_to_excel` fixture: `yield` then `write_excel_report(results_table, reports_dir)` |
| Excel writer | `utils/excel_writer.py` | `pandas` guarded at import; `openpyxl` missing surfaces as `ModuleNotFoundError` inside write; `PermissionError` → timestamped fallback file |
| Dependencies | `requirements.txt` | Includes `google-generativeai`, `pandas`, `openpyxl` |

**Note on task wording:** `GeminiProvider` is **not** defined in `judge_factory.py`; migration work applies to **`utils/gemini_provider.py`**. `judge_factory.py` must keep fallback semantics unchanged (no behavioral regression).

---

## 3. Part A — Google Gen AI SDK migration

### 3.1 Package change

| Remove | Add |
|--------|-----|
| `google-generativeai` | `google-genai` |

Update **`requirements.txt`** accordingly. Pin a minimum version compatible with the chosen API surface (to be locked at implementation time after `pip install` verification).

### 3.2 Import and client

- Use: `from google import genai` (as required by the product brief).
- Initialize a **`genai.Client`** with the Gemini API key:
  - Prefer explicit `api_key=` from `GEMINI_API_KEY` (consistent with current `ValueError` if missing).
  - Alternative: `genai.Client()` when env is set — acceptable only if behavior matches “key required” contract; **spec default:** explicit key from env.

Store the client on the provider instance (e.g. `self._client`) for reuse across `evaluate()` calls.

### 3.3 Content generation API

Replace:

- `GenerativeModel(model_name).generate_content(prompt)`

With the new SDK pattern (verify exact signatures against [Migrate to the Google GenAI SDK](https://ai.google.dev/gemini-api/docs/migrate) and [python-genai](https://googleapis.github.io/python-genai/) at implementation time):

- `client.models.generate_content(model=<id>, contents=<prompt>)`

### 3.4 Model identifiers

Current candidates: `models/gemini-1.5-flash`, `models/gemini-2.0-flash`.

**Implementation rule:** Map IDs to the form accepted by `google-genai` (may be short names such as `gemini-1.5-flash` without the `models/` prefix). Keep the same **fallback order** and **“model not found → next model”** logic based on error message inspection.

### 3.5 Response text extraction

Preserve:

- Strip markdown fences from JSON (` ```json ` / ` ``` `).
- `json.loads` on the cleaned string.

**Implementation rule:** Use the new SDK’s documented way to read text (e.g. `response.text`). If the object shape differs (e.g. candidates/parts), add a small private helper that returns a single string for parsing — **without** changing the outward `evaluate()` return schema.

### 3.6 Error handling parity

Retain:

- `classify_api_error_message` integration for `SISTEM_YETKI` / `SISTEM_KOTA`.
- Retry loop with `_extract_retry_seconds` for quota-style errors.
- Same return dicts for system/quota/fail paths.

Adjust string matching only if exception messages from `google-genai` differ; keep behavior equivalent.

### 3.7 Fallback (`judge_factory`)

**No change** to public `get_judge()` contract: OpenAI first, Gemini on failure when `LLM_TYPE=openai`; dedicated Gemini when `LLM_TYPE=gemini`.

---

## 4. Part B — Reporting & fixture fixes

### 4.1 Fixture lifecycle (session-scoped, yield, single write)

**Target behavior:**

1. **Collection:** All rows are appended only via existing `pytest_runtest_makereport` (or an equivalent single writer) into **one** session-wide structure.
2. **Teardown:** The session fixture runs **only after** all tests; it triggers Excel generation **once** with the full list.

**Current state:** Already `yield`-based; collection is a module-level `results_table`.  

**Spec refinements for implementation:**

- Prefer passing the **same list object** the hook mutates into `write_excel_report` (or document explicitly that the fixture reads the module-level list — avoid shadowing or re-binding that drops rows).
- Optionally wrap the list in a small **session-scoped fixture** that returns the shared `results_table` for clarity (autouse child) — only if it does not break hook ordering; **default:** keep hook + module list, add comments/tests proving one teardown write.

### 4.2 Dependency guard (pandas / openpyxl)

**Requirement:** `try` / `except` around imports with a **clean, logged** message if missing.

**Options (pick one at implementation; spec allows either if tests cover behavior):**

- **A.** Centralize in `utils/excel_writer.py` (already guards `pandas`; extend to **proactive `openpyxl` import** in `try`/`except` with the same user-facing message style as today).
- **B.** Guard in `conftest.py` teardown before calling `write_excel_report`, using `logging` (or `print` consistent with project) — must not raise; session must end cleanly.

**Acceptance:** Missing `pandas` or `openpyxl` → one clear message, no traceback from teardown by default, pytest exit 0/consistent with current policy.

### 4.3 Directory safety

Before writing:

- Ensure `reports/` exists: `Path.mkdir(parents=True, exist_ok=True)` on the target directory (already in `write_excel_report`; **do not remove**).

### 4.4 Locked primary file (`PermissionError`)

**Requirement:** If `Chatbot_Test_Raporu.xlsx` is open/locked, catch and write `Chatbot_Test_Raporu_<TIMESTAMP>.xlsx`.

**Current state:** `write_excel_report` already implements this for `PermissionError` with `YYYYMMDD_HHMMSS`.

**Spec additions:**

- If **both** primary and a colliding timestamp name fail (unlikely), log and swallow or re-raise per team policy — **default:** log second failure, do not crash pytest teardown if avoidable.
- Tests must use **mocking** (`PermissionError` on primary path) rather than requiring a locked real file.

### 4.5 Parametrized tests / data persistence

**Acceptance:**

- For N parametrized **call** outcomes that produce a makereport row, the Excel row count (data rows) equals N (plus header).
- Skipped/failed tests still produce rows when the hook runs for `when == "call"` (current design).

**Verification approach:** Integration-style test with a dummy item/report is optional; **minimum:** unit tests on `write_excel_report` + a test that the hook appends expected keys (existing behavior preserved).

---

## 5. Part C — `FutureWarning` / deprecation noise

### 5.1 Discovery

Run the full test suite with warnings visible (`pytest -W default` or equivalent) after migration.

### 5.2 Remediation order

1. **Fix at source** if the warning is from **our** code (e.g. deprecated pandas API usage in `excel_writer.py`).
2. If the warning originates **only** from a third-party dependency and a fix is not available:
   - Add a **narrow** `filterwarnings` entry in `pytest.ini` matching the exact message/module, with a one-line comment in `pytest.ini` or adjacent config explaining why.

**Anti-pattern:** Blanket `ignore::FutureWarning` without justification.

---

## 6. TDD workflow (after spec approval)

### 6.1 Red — `tests/test_infra.py` (new)

| Test case | Intent |
|-----------|--------|
| Gemini + new SDK | Mock `google.genai` / `Client` / `models.generate_content` so that `GeminiProvider.evaluate()` returns parsed JSON without network; assert client constructed with API key and `generate_content` invoked with expected model iteration |
| Excel locked file | Call `write_excel_report` with a temporary directory; patch inner write or `pd.ExcelWriter` / `_write_with_autowidth` so first open raises `PermissionError`, then succeeds; assert a `Chatbot_Test_Raporu_*.xlsx` exists and primary was attempted |

Tests must not require real API keys or Excel installed on CI beyond declared deps (use mocks where appropriate).

### 6.2 Green

- Implement Part A & B per sections 3–4.
- Make `test_infra.py` pass.

### 6.3 Refactor

- Type hints for new client attributes and helpers.
- Remove dead imports (`google.generativeai`).
- Align docstrings/comments with actual module layout (`gemini_provider.py` vs `judge_factory.py`).

---

## 7. Non-goals (this iteration)

- Changing Allure attachment behavior.
- Replacing `print` with `logging` project-wide (unless required for “clean error” acceptance).
- Adding new LLM providers.

---

## 8. Acceptance checklist (sign-off)

- [ ] `requirements.txt`: `google-genai` present; `google-generativeai` removed.
- [ ] `GeminiProvider` works against mocked `google-genai` in CI.
- [ ] `get_judge()` fallback OpenAI → Gemini unchanged by manual/automated check.
- [ ] Session ends with **one** Excel write in teardown; parametrized rows all present.
- [ ] Missing `pandas` / `openpyxl`: clear message, no teardown crash.
- [ ] Locked xlsx: timestamped fallback created (tested with mock).
- [ ] No unjustified `FutureWarning` spam in default pytest run (per Part C).

---

## 9. Approval

**Implement code only after:** explicit approval of this document (edit status line at top to **Approved** with date/owner).

When approved, proceed in order: **Red (`test_infra.py`) → Green (implementation) → Refactor → Part C warning pass.**
