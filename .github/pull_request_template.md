## What changed

<!-- One or two sentences. -->

## Checklist

- [ ] No locator appears in a `.robot` test file — locators live in `resources/locators/<platform>/`
- [ ] No `Sleep` was added (use the keywords in `resources/common/waits.resource`)
- [ ] New tests are tagged: `smoke` for the critical path, `regression` otherwise
- [ ] `robocop check` and `pytest tests/unit` pass locally
- [ ] `robot --dryrun` passes for **both** platforms, not just the one I tested
- [ ] If a test is platform-specific, it lives in `tests/mobile/android|ios/`, not in `shared/`

## Evidence

<!-- Link to the Sauce build, or paste the report summary. "It works on my
machine" is not evidence. -->
