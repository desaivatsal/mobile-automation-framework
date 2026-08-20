*** Settings ***
Documentation       Page object for the Products (catalogue) screen and its side menu.

Resource            ../common/imports.resource
Resource            ../locators/${PLATFORM}/products_locators.resource


*** Keywords ***
Products Screen Should Be Displayed
    [Documentation]    Asserts the catalogue screen is on display.
    Screen Should Be Displayed    ${PRODUCTS_TITLE}    Products

Get Product Count
    [Documentation]    Number of product tiles currently rendered.
    ${items}=    Get Webelements    ${PRODUCTS_ITEM}
    ${count}=    Get Length    ${items}
    RETURN    ${count}

Product List Should Not Be Empty
    [Documentation]    Asserts the catalogue rendered at least one product.
    Element Count Should Be At Least    ${PRODUCTS_ITEM}    1

Open Product By Name
    [Documentation]    Scrolls to a product by its visible name and opens it.
    [Arguments]    ${name}
    ${locator}=    Build Locator    ${PRODUCT_BY_NAME}    name=${name}
    Scroll Until Element Is Visible    ${locator}
    Click Element    ${locator}

Open First Product
    [Documentation]    Opens the first product tile. Use when the exact catalogue
    ...    contents are not what is under test.
    Tap Element    ${PRODUCTS_ITEM}

Open Cart From Products
    [Documentation]    Taps the cart icon in the header.
    Tap Element    ${PRODUCTS_CART_BUTTON}

Get Cart Badge Count
    [Documentation]    Returns the number on the cart badge, or 0 when absent.
    ${visible}=    Element Is Visible    ${PRODUCTS_CART_BADGE}    2s
    IF    not ${visible}    RETURN    ${0}
    ${text}=    Get Text    ${PRODUCTS_CART_BADGE}
    ${count}=    Convert To Integer    ${text}
    RETURN    ${count}

Cart Badge Should Show
    [Documentation]    Asserts the cart badge shows ``expected`` items.
    [Arguments]    ${expected}
    ${actual}=    Get Cart Badge Count
    Should Be Equal As Integers    ${actual}    ${expected}
    ...    msg=Cart badge showed ${actual} item(s) but ${expected} was expected.

Open Side Menu
    [Documentation]    Opens the hamburger menu.
    Tap Element    ${PRODUCTS_MENU_BUTTON}

Logout
    [Documentation]    Opens the side menu and logs out.
    Open Side Menu
    Tap Element    ${MENU_LOGOUT}
