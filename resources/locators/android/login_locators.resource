*** Settings ***
Documentation    Android locators for the Login screen.
...
...              LOCATOR RULES (enforced in review):
...              1. Prefer ``accessibility_id`` - it is stable across releases and
...              shared with iOS, which is what lets one page object drive both.
...              2. ``id`` (resource-id) is second choice.
...              3. XPath is a last resort and must never use positional indices
...              such as ``[3]`` or ``//*``; anchor on a content-desc or text.
...              4. No locator lives in a test file. Ever.


*** Variables ***
${LOGIN_USERNAME_FIELD}         accessibility_id=test-Username
${LOGIN_PASSWORD_FIELD}         accessibility_id=test-Password
${LOGIN_SUBMIT_BUTTON}          accessibility_id=test-LOGIN
${LOGIN_ERROR_MESSAGE}          accessibility_id=test-Error message
${LOGIN_SCREEN_ROOT}            accessibility_id=test-Login Screen
