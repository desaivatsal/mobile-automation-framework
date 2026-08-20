*** Settings ***
Documentation       Android-only behaviour that has no iOS equivalent.
...
...                 Keep this suite small. Anything that *can* be expressed
...                 cross-platform belongs in ``tests/mobile/shared/``.

Resource            ../../../resources/pages/login_page.resource
Resource            ../../../resources/pages/products_page.resource
Resource            ../../../resources/pages/product_details_page.resource

Suite Setup         Setup Mobile Suite
Suite Teardown      Teardown Mobile Suite
Test Setup          Setup Mobile Test
Test Teardown       Teardown Mobile Test

Test Tags           mobile    android-only    regression
Test Timeout        5 minutes


*** Test Cases ***
Hardware Back Button Returns To The Catalogue
    [Documentation]    Android users expect the system back gesture to work,
    ...    not just the in-app back control.
    Skip If    not $IS_ANDROID    This suite only runs on Android.
    Login As    standard
    Products Screen Should Be Displayed
    Open First Product
    Product Details Should Be Displayed
    Navigate Back
    Products Screen Should Be Displayed

App Survives Being Backgrounded
    [Documentation]    Backgrounding and resuming must not drop the session.
    ...    This is the cheapest way to catch state that is only held in memory.
    Skip If    not $IS_ANDROID    This suite only runs on Android.
    Login As    standard
    Products Screen Should Be Displayed
    Background Application    5
    Products Screen Should Be Displayed
