# Web layer (extension point)

Nothing here runs yet. This directory exists so adding web UI tests later is
**additive**, not a refactor.

## What is already in place

- `config/default.yaml` and every environment file carry a `web:` block
  (`base_url`, `browser`, `headless`), surfaced to Robot as `${WEB_BASE_URL}`.
- `requirements-web.txt` pins the browser libraries.
- `tests/web/` is the suite root, already excluded from the mobile CI jobs by
  path, not by tag.

## How to add the first web test

1. `pip install -r requirements-web.txt && rfbrowser init`
2. Add `Library  Browser` to `resources/web/web_libraries.resource`.
3. Mirror the mobile structure:
   - `resources/web/locators/<page>_locators.resource` — data only
   - `resources/web/pages/<page>_page.resource` — keywords only
   - `tests/web/<area>_tests.robot` — assertions only
4. Reuse `resources/common/assertions.resource` — the assertion helpers are
   library-agnostic by design.
5. Add a `web` job to `.github/workflows/regression.yml`, copying the mobile job
   and swapping the suite path.

Sauce Labs also runs web sessions; `libs/capabilities.py` already knows how to
build a `sauce:options` block, so a `sauce_web` target is a small addition to
`config/platforms/` rather than new plumbing.

See `tests/web/example_web_tests.robot.example` for the shape of a suite.
