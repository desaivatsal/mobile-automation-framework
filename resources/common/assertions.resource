*** Settings ***
Documentation    Assertion helpers with failure messages worth reading.
...
...              A failure message that says only "element not found" costs an
...              engineer ten minutes. Every keyword here states what was
...              expected, what was found, and on which screen.

Resource        libraries.resource
Resource        waits.resource


*** Keywords ***
Screen Should Be Displayed
    [Documentation]    Asserts an anchor element that uniquely identifies a screen.
    [Arguments]    ${anchor_locator}    ${screen_name}    ${timeout}=${ELEMENT_WAIT}
    ${displayed}=    Run Keyword And Return Status
    ...    Wait Until Element Is Visible    ${anchor_locator}    timeout=${timeout}
    IF    not ${displayed}
        Fail    Not on the '${screen_name}' screen: anchor '${anchor_locator}' not visible in ${timeout}.
    END

Element Text Should Equal
    [Documentation]    Asserts the exact text of an element.
    [Arguments]    ${locator}    ${expected}    ${screen}=${EMPTY}
    Wait For Element    ${locator}    screen=${screen}
    ${actual}=    Get Text    ${locator}
    Should Be Equal As Strings    ${actual}    ${expected}
    ...    msg=Text of '${locator}' was '${actual}' but '${expected}' was expected.
    ...    values=${FALSE}

Element Text Should Contain
    [Documentation]    Asserts an element's text contains ``expected``.
    [Arguments]    ${locator}    ${expected}    ${screen}=${EMPTY}
    Wait For Element    ${locator}    screen=${screen}
    ${actual}=    Get Text    ${locator}
    Should Contain    ${actual}    ${expected}
    ...    msg=Text of '${locator}' was '${actual}' which does not contain '${expected}'.
    ...    values=${FALSE}

Element Count Should Be At Least
    [Documentation]    Asserts at least ``minimum`` elements match ``locator``.
    ...    Use this instead of asserting an exact count when the list is
    ...    data-driven - exact counts are the number one source of false failures.
    [Arguments]    ${locator}    ${minimum}
    Wait For Element    ${locator}
    ${elements}=    Get Webelements    ${locator}
    ${count}=    Get Length    ${elements}
    Should Be True    ${count} >= ${minimum}
    ...    msg=Expected at least ${minimum} elements matching '${locator}' but found ${count}.
