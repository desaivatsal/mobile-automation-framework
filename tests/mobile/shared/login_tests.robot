*** Settings ***
Documentation       Login journeys. Runs unchanged on Android and iOS - the
...                 platform is selected by ``--variablefile config/variables.py:<env>:<platform>:<target>``.

Resource            ../../../resources/pages/login_page.resource
Resource            ../../../resources/pages/products_page.resource

Suite Setup         Setup Mobile Suite
Suite Teardown      Teardown Mobile Suite
Test Setup          Setup Mobile Test
Test Teardown       Teardown Mobile Test

Test Tags           mobile    login
Test Timeout        5 minutes


*** Test Cases ***
Valid User Can Log In
    [Documentation]    A standard user reaches the product catalogue.
    [Tags]    smoke    critical
    Login As    standard
    Products Screen Should Be Displayed
    Product List Should Not Be Empty

Invalid Credentials Are Rejected
    [Documentation]    Wrong credentials keep the user on the login screen and
    ...    surface an error, rather than failing open.
    [Tags]    regression    negative
    Login As    invalid
    Login Error Should Be Displayed    ${TEST_DATA}[expected][login_error]

Locked Out User Cannot Log In
    [Documentation]    A disabled account is refused with a distinct message.
    [Tags]    regression    negative
    Login As    locked_out
    Login Error Should Be Displayed    ${TEST_DATA}[expected][locked_out_error]

Empty Credentials Are Rejected
    [Documentation]    Submitting an empty form must not create a session.
    [Tags]    regression    negative
    Login With Credentials    ${EMPTY}    ${EMPTY}
    Login Screen Should Be Displayed

User Can Log Out
    [Documentation]    Logging out returns to the login screen and ends the session.
    [Tags]    smoke
    Login As    standard
    Products Screen Should Be Displayed
    Logout
    Login Screen Should Be Displayed
