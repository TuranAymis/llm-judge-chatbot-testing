# Excel Reporting Specification

## Overview

Every `pytest` session must produce `reports/Chatbot_Test_Raporu.xlsx` automatically,
regardless of test outcomes (pass, fail, skip, error). The reporting subsystem must
be resilient to missing dependencies, locked files, and empty result sets.

## Edge Cases & Acceptance Criteria

### EC-1: Fixture Yield Logic

| Item | Detail |
|---|---|
| **Trigger** | `export_to_excel` is a `session`-scoped, `autouse=True` fixture. |
| **Behaviour** | Setup (before `yield`) initialises nothing beyond the shared `results_table` list. Teardown (after `yield`) converts the list to a DataFrame and writes the Excel file. |
| **Acceptance** | The xlsx file timestamp is always *after* the last test finishes. No data is written mid-session. |

### EC-2: Dependency Missing (pandas / openpyxl)

| Item | Detail |
|---|---|
| **Trigger** | `pandas` or `openpyxl` is not installed in the active environment. |
| **Behaviour** | A clear, human-readable warning is printed to stdout (package name + install command). The fixture returns without raising. |
| **Acceptance** | `pytest` exits cleanly (no teardown ERROR). Allure attachments from individual tests are still intact. |

### EC-3: Directory Missing

| Item | Detail |
|---|---|
| **Trigger** | `reports/` directory does not exist at write time. |
| **Behaviour** | `os.makedirs(reports_dir, exist_ok=True)` (or `Path.mkdir(parents=True, exist_ok=True)`) creates it before the write attempt. |
| **Acceptance** | File is written successfully on a fresh clone with no pre-existing `reports/` folder. |

### EC-4: File Locked (PermissionError)

| Item | Detail |
|---|---|
| **Trigger** | `Chatbot_Test_Raporu.xlsx` is open in Excel or another process holds a lock. |
| **Behaviour** | Catch `PermissionError`, generate a fallback filename with a `YYYYMMDD_HHMMSS` timestamp suffix, write to that path, print a warning showing both paths. |
| **Acceptance** | A timestamped xlsx file exists in `reports/`. No data is lost. No teardown crash. |

### EC-5: Data Integrity (including empty session)

| Item | Detail |
|---|---|
| **Trigger** | (a) Normal parametrized run with N test items. (b) Session where all tests are skipped or deselected (0 results). |
| **Behaviour** | (a) xlsx contains exactly N data rows plus a header row. Column order matches `report_columns`. (b) xlsx contains only the header row (valid, openable file). |
| **Acceptance** | `openpyxl.load_workbook(path).active.max_row` equals `N + 1` (or `1` for empty). |
