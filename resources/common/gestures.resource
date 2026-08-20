*** Settings ***
Documentation    Cross-platform gestures.
...
...              Android and iOS need different native scroll implementations.
...              That difference is handled here, once, so page objects and tests
...              stay platform-agnostic.

Resource        libraries.resource
Resource        waits.resource


*** Keywords ***
Tap Element
    [Documentation]    Waits for an element then taps it. Prefer this over a bare
    ...    ``Click Element`` so every tap has an implicit visibility guard.
    [Arguments]    ${locator}    ${timeout}=${ELEMENT_WAIT}
    Wait For Element    ${locator}    ${timeout}
    Click Element    ${locator}

Type Into Field
    [Documentation]    Clears then types into a field, and hides the keyboard after.
    [Arguments]    ${locator}    ${text}    ${timeout}=${ELEMENT_WAIT}
    Wait For Element    ${locator}    ${timeout}
    Clear Text    ${locator}
    Input Text    ${locator}    ${text}
    Hide Keyboard Safely

Type Secret Into Field
    [Documentation]    Same as `Type Into Field` but the value is masked in the log.
    [Arguments]    ${locator}    ${text}    ${timeout}=${ELEMENT_WAIT}
    Wait For Element    ${locator}    ${timeout}
    Clear Text    ${locator}
    Input Password    ${locator}    ${text}
    Hide Keyboard Safely

Hide Keyboard Safely
    [Documentation]    Dismisses the soft keyboard, ignoring the "keyboard is not
    ...    shown" error that XCUITest and UiAutomator2 raise inconsistently.
    ${shown}=    Run Keyword And Return Status    Is Keyboard Shown
    IF    ${shown}    Run Keyword And Ignore Error    Hide Keyboard

Swipe Screen
    [Documentation]    Swipes across the middle of the screen.
    ...
    ...    ``direction`` is up | down | left | right, where "up" means the
    ...    content moves up (i.e. you see what is further down the page).
    ...    ``distance`` is a fraction of the screen (0.1 - 0.9).
    ...
    ...    Uses percentages rather than pixels so the same gesture behaves the
    ...    same on a 1080p phone and a tablet.
    [Arguments]    ${direction}=up    ${distance}=0.5    ${duration}=0.8
    ${half}=    Evaluate    int(${distance} * 100 / 2)
    ${near}=    Evaluate    50 - ${half}
    ${far}=    Evaluate    50 + ${half}

    IF    '${direction}' == 'up'
        Swipe By Percent    50    ${far}    50    ${near}    ${duration}
    ELSE IF    '${direction}' == 'down'
        Swipe By Percent    50    ${near}    50    ${far}    ${duration}
    ELSE IF    '${direction}' == 'left'
        Swipe By Percent    ${far}    50    ${near}    50    ${duration}
    ELSE IF    '${direction}' == 'right'
        Swipe By Percent    ${near}    50    ${far}    50    ${duration}
    ELSE
        Fail    Unsupported swipe direction '${direction}'. Use up, down, left or right.
    END

Scroll Until Element Is Visible
    [Documentation]    Scrolls the screen until ``locator`` is visible, or fails
    ...    after ``max_swipes``. Uses swipes rather than a native scroll command
    ...    so it behaves the same on Android and iOS.
    [Arguments]    ${locator}    ${direction}=up    ${max_swipes}=8
    FOR    ${index}    IN RANGE    ${max_swipes}
        ${visible}=    Element Is Visible    ${locator}    1s
        IF    ${visible}    RETURN
        Log    Swipe ${index} of ${max_swipes} searching for '${locator}'    level=DEBUG
        Swipe Screen    ${direction}    0.6
    END
    Fail    Element '${locator}' was not found after ${max_swipes} swipes ${direction}.

Navigate Back
    [Documentation]    Android uses the hardware back button; iOS has none, so the
    ...    caller must pass an on-screen back ``locator``.
    [Arguments]    ${ios_back_locator}=${EMPTY}
    IF    $IS_ANDROID
        Go Back
    ELSE IF    '${ios_back_locator}' != '${EMPTY}'
        Tap Element    ${ios_back_locator}
    ELSE
        Fail    iOS has no hardware back button - pass ios_back_locator to Navigate Back.
    END
