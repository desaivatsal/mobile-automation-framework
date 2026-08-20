*** Settings ***
Documentation    Explicit-wait primitives.
...
...              Implicit waits are disabled framework-wide (``timeouts.implicit_wait: 0``)
...              because they silently mask race conditions and make every
...              negative assertion slow. Wait explicitly, or not at all.

Resource        libraries.resource


*** Keywords ***
Wait For Element
    [Documentation]    Waits for ``locator`` to become visible and returns it.
    ...    The failure message names the locator and the screen, so a CI failure
    ...    is diagnosable without opening the Sauce video.
    [Arguments]    ${locator}    ${timeout}=${ELEMENT_WAIT}    ${screen}=${EMPTY}
    ${where}=    Set Variable If    '${screen}' == '${EMPTY}'    ${EMPTY}    ${SPACE}on screen '${screen}'
    Wait Until Element Is Visible    ${locator}    timeout=${timeout}
    ...    error=Element '${locator}'${where} was not visible within ${timeout}.
    RETURN    ${locator}

Wait For Element To Disappear
    [Documentation]    Waits until ``locator`` is no longer present on screen.
    [Arguments]    ${locator}    ${timeout}=${ELEMENT_WAIT}
    Wait Until Page Does Not Contain Element    ${locator}    timeout=${timeout}
    ...    error=Element '${locator}' was still present after ${timeout}.

Wait For Text
    [Documentation]    Waits until ``text`` appears anywhere on the current screen.
    [Arguments]    ${text}    ${timeout}=${ELEMENT_WAIT}
    Wait Until Page Contains    ${text}    timeout=${timeout}
    ...    error=Text '${text}' did not appear within ${timeout}.

Element Is Visible
    [Documentation]    Boolean probe for optional UI (consent dialogs, tooltips).
    ...    Never use this in place of an assertion - a probe that returns
    ...    ${FALSE} passes silently.
    [Arguments]    ${locator}    ${timeout}=3s
    ${visible}=    Run Keyword And Return Status
    ...    Wait Until Element Is Visible    ${locator}    timeout=${timeout}
    RETURN    ${visible}

Dismiss Optional Element
    [Documentation]    Taps ``locator`` only if it happens to be on screen.
    [Arguments]    ${locator}    ${timeout}=3s
    ${visible}=    Element Is Visible    ${locator}    ${timeout}
    IF    ${visible}    Click Element    ${locator}
