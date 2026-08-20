*** Settings ***
Documentation       iOS-only behaviour that has no Android equivalent.
...
...                 Keep this suite small. Anything that *can* be expressed
...                 cross-platform belongs in ``tests/mobile/shared/``.

Resource            ../../../resources/pages/login_page.resource
Resource            ../../../resources/pages/products_page.resource

Suite Setup         Setup Mobile Suite
Suite Teardown      Teardown Mobile Suite
Test Setup          Setup Mobile Test
Test Teardown       Teardown Mobile Test

Test Tags           mobile    ios-only    regression
Test Timeout        5 minutes


*** Test Cases ***
Catalogue Survives A Rotation
    [Documentation]    Rotating to landscape and back must not lose the catalogue.
    ...    Layout regressions on rotation are common in React Native builds.
    Skip If    not $IS_IOS    This suite only runs on iOS.
    Login As    standard
    Products Screen Should Be Displayed
    Landscape
    Product List Should Not Be Empty
    Portrait
    Products Screen Should Be Displayed

App Survives Being Backgrounded
    [Documentation]    Resuming from the app switcher must not drop the session.
    Skip If    not $IS_IOS    This suite only runs on iOS.
    Login As    standard
    Products Screen Should Be Displayed
    Background Application    5
    Products Screen Should Be Displayed
