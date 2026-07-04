---
name: code-documentation-standards
description: Enforce Python commenting standards (PEP 257/8) and ensure corresponding documentation under the docs/ directory is updated when code changes are made.
---

# Code Documentation and Standards Guide

This guide ensures that when coding changes are made to the Mealie codebase, the code is appropriately commented and user-facing documentation is kept in sync.

## 📌 Python Commenting and Docstring Standards

When modifying or writing Python code in the [mealie/](file:///home/quok/Antigravity/mealie/mealie-1/mealie/) directory:

1. **Docstrings (PEP 257):**
   - Every public module, class, method, and function must have a docstring.
   - Use triple double-quotes `"""`.
   - For simple functions, a one-line docstring is sufficient.
   - For complex logic, use multi-line docstrings detailing:
     - A brief summary of the purpose.
     - **Args:** list of arguments with their types and descriptions.
     - **Returns:** description of the return value and type.
     - **Raises:** any exceptions that might be explicitly raised.

2. **Inline Comments (PEP 8):**
   - Write comments to explain *why* something is done, not *what* the code is doing (unless the code is doing something non-trivial or working around a known issue).
   - Keep comments up to date. Avoid comments that contradict the code.

---

## 📝 Synchronized Documentation Updates

Whenever backend or frontend code changes are proposed or executed:

1. **Identify Impacted Documentation:**
   - Determine if the change alters user configuration, API endpoints, workflow steps, or installation procedures.
   - Search the [docs/docs/](file:///home/quok/Antigravity/mealie/mealie-1/docs/docs/) directory for relevant markdown files that reference the modified feature or component.

2. **Update Docs:**
   - Modify the corresponding markdown documentation under `docs/docs/` to reflect the new state.
   - Maintain the existing tone and format of the documentation.
