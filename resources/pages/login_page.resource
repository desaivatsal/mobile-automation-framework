*** Settings ***
Documentation       Page object for the Login screen.
...
...                 Locators come from ``resources/locators/${PLATFORM}/`` so this
...                 single file drives both Android and iOS. If a flow genuinely
...                 differs between platforms, branch on ``$IS_ANDROID`` *here* -
...                 never in a test case.

Resource            ../common/imports.resource
Resource            ../locators/${PLATFORM}/login_locators.resource


*** Keywords ***
Login Screen Should Be Displayed
    [Documentation]    Verifies the app is sitting on the login screen.
    Screen Should Be Displayed    ${LOGIN_USERNAME_FIELD}    Login    ${APP_LAUNCH_TIMEOUT}

Enter Username
    [Documentation]    Types ``username`` into the username field.
    [Arguments]    ${username}
    Type Into Field    ${LOGIN_USERNAME_FIELD}    ${username}

Enter Password
    [Documentation]    Types ``password`` into the password field, masked in the log.
    [Arguments]    ${password}
    Type Secret Into Field    ${LOGIN_PASSWORD_FIELD}    ${password}

Submit Login
    [Documentation]    Taps the login button.
    Tap Element    ${LOGIN_SUBMIT_BUTTON}

Login With Credentials
    [Documentation]    Full login flow. Returns nothing - assert on the next screen.
    [Arguments]    ${username}    ${password}
    Login Screen Should Be Displayed
    Enter Username    ${username}
    Enter Password    ${password}
    Submit Login

Login As
    [Documentation]    Logs in using a named user from the environment's test data,
    ...    e.g. ``Login As    standard``. Keeps credentials out of test files.
    [Arguments]    ${user_key}
    ${users}=    Get From Dictionary    ${TEST_DATA}    users
    ${user}=    Get From Dictionary    ${users}    ${user_key}
    Login With Credentials    ${user}[username]    ${user}[password]

Login Error Should Be Displayed
    [Documentation]    Asserts the inline error banner contains ``expected_text``.
    [Arguments]    ${expected_text}
    Element Text Should Contain    ${LOGIN_ERROR_MESSAGE}    ${expected_text}    screen=Login

Login Error Should Not Be Displayed
    [Documentation]    Asserts no error banner is present on the login screen.
    Page Should Not Contain Element    ${LOGIN_ERROR_MESSAGE}
