# AI Developer Instructions & Constraints

## 1. UI & Styling Rules
- **Design System:** Always use the existing CSS classes in `new_theme.css` (`jira-card`, `jira-pill-success`, `jira-table`, `btn-jira-primary`).
- **No Inline CSS:** Do not use inline `style="..."` for colors, padding, or borders. Only use inline CSS for dynamic width/height (like progress bars or specific column widths).
- **Toasts:** Use Django `messages` framework for success/error notifications. The base template automatically renders these as 3-second floating toasts.

## 2. JavaScript & Security Rules
- **CSP Strictness:** Never generate `onclick="..."`, `javascript:void(0)`, or `<script>` blocks inside HTML templates.
- **External JS Only:** If a feature requires JS (like a modal, dynamic form, or Select2 initialization), write the JS in a separate file in `tcms_ui_custom/static/js/` and link it via `{% block extra_js %}`.
- **No External CDNs:** If a library is needed, assume it must be downloaded and stored in `tcms_ui_custom/static/vendor/`.

## 3. Backend & Database Rules
- **View Isolation:** Do not put complex data manipulation inside templates. Do it in `views.py` or helper functions.
- **Model Abstraction:** Use native Kiwi models. If a form submission fails, use Django's `messages.error` and pass a boolean flag (e.g., `form_has_error = True`) to keep UI elements (like collapsible forms) open on reload.
- **M2M Handling:** Always remember that `component` and `tag` on a `TestCase` are Many-to-Many. Use `.add()`, `.clear()`, and `component__id` for filtering.

## 4. Future-Proofing
- When writing step-parsing or complex relational logic, encapsulate it in a dedicated helper function (e.g., `_format_testcase_text`) so that future database migrations (Option B) only require changing that one function, not the views or templates.

## 5. Deletion Safety
- **Never** write a view that calls `.delete()` on `Product`, `Component`, `Build`, `Version`, `Category`, or `TestPlan`.
- **Always** implement the `PROTECT` check for any reference model before allowing deletion.
- **Default to Archiving:** If a user needs to "remove" a project or module, implement a "disable/archive" flow.
