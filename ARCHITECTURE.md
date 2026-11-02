# Modular TCMS Architecture & Context

## 1. Core Philosophy
- **Do not modify Kiwi Core:** All custom code lives in `tcms_ui_custom`. We do not edit files inside `tcms/` (except `settings/common.py` and `urls.py` for registration).
- **API-First / MCP Ready:** All data is stored in native Kiwi models (`Product`, `Component`, `TestCase`, `TestPlan`, etc.) to ensure the future AI MCP server and API testing modules can interact with the system seamlessly.
- **Jira-Style UX:** The UI completely replaces Kiwi's default PatternFly 3 interface with a modern, responsive Jira-inspired design.

## 2. Directory Structure
- `tcms_ui_custom/` - The primary Django app.
  - `templates/` - Overrides Kiwi templates. Contains custom pages (`project_overview.html`, `testcase_view.html`, etc.).
  - `static/css/new_theme.css` - The Global Design System. DO NOT use inline styles for colors/layout.
  - `static/js/` - Holds all JavaScript to comply with Kiwi's strict Content Security Policy (CSP).
  - `views.py` - Custom controller logic.
  - `forms.py` - Form definitions.
  - `urls.py` - Custom routing.

## 3. Data Storage Strategy (Current State)
- **Test Cases:** Stored in Kiwi's `TestCase` model.
- **Steps & Conditions (Option A):** Stored as HTML inside `TestCase.text`. This is abstracted via the `_format_testcase_text()` helper in `views.py`.
- **Future Migration (Option B):** When we move to relational steps, we will create a `CustomStep` model in `tcms_ui_custom` with a ForeignKey to `TestCase`. The helper function will be updated to save to this new table, leaving the views untouched.

## 4. Security & Constraints
- **Content Security Policy (CSP):** Kiwi blocks all inline scripts (`onclick`, `<script>` blocks) and external CDNs (like Cloudflare).
  - *Rule:* ALL JavaScript must be written in separate `.js` files inside `tcms_ui_custom/static/js/` and linked via `<script src="...">`.
- **ManyToMany Relationships:** Be careful. `TestCase.component` is a M2M field. Use `.add()` and `.clear()`, and filter using `component__id`.

## 5. Data Safety & Deletion Policy
- **No Hard Deletes for Reference Data:** Models like `Product`, `Component`, `Build`, `Version`, and `Category` must never be hard-deleted via the UI.
- **Archive Pattern:** To "remove" these items, add an `is_archived` boolean field via a custom migration in `tcms_ui_custom`. Filter them out of active lists.
- **Disable Pattern:** Test Plans should be disabled, not deleted, to preserve execution history.
- **Protect Pattern:** For attributes (Tag, Priority, Status), the backend must check for `TestCase.objects.filter(fk=item).exists()` and block deletion if in use.
