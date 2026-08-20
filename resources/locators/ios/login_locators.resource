*** Settings ***
Documentation    iOS locators for the Login screen.
...
...              Variable names are identical to the Android file on purpose:
...              ``resources/pages/login_page.resource`` imports whichever of the
...              two matches ``${PLATFORM}``, so a single set of page keywords
...              drives both platforms.


*** Variables ***
${LOGIN_USERNAME_FIELD}         accessibility_id=test-Username
${LOGIN_PASSWORD_FIELD}         accessibility_id=test-Password
${LOGIN_SUBMIT_BUTTON}          accessibility_id=test-LOGIN
${LOGIN_ERROR_MESSAGE}          accessibility_id=test-Error message
${LOGIN_SCREEN_ROOT}            accessibility_id=test-Login Screen
