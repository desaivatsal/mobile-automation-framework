*** Settings ***
Documentation       Page object for the Cart screen.

Resource            ../common/imports.resource
Resource            ../locators/${PLATFORM}/cart_locators.resource


*** Keywords ***
Cart Screen Should Be Displayed
    [Documentation]    Asserts the cart screen is on display.
    Screen Should Be Displayed    ${CART_TITLE}    Cart

Get Cart Item Count
    [Documentation]    Number of line items currently in the cart.
    ${items}=    Get Webelements    ${CART_ITEM}
    ${count}=    Get Length    ${items}
    RETURN    ${count}

Cart Should Contain
    [Documentation]    Asserts the cart holds exactly ``expected_count`` line items.
    [Arguments]    ${expected_count}
    ${actual}=    Get Cart Item Count
    Should Be Equal As Integers    ${actual}    ${expected_count}
    ...    msg=Cart contained ${actual} item(s) but ${expected_count} was expected.

Cart Should Contain Product
    [Documentation]    Asserts a product with the given ``name`` is listed in the cart.
    [Arguments]    ${name}
    Page Should Contain Text    ${name}

Continue Shopping
    [Documentation]    Returns to the catalogue from the cart.
    Tap Element    ${CART_CONTINUE_SHOPPING}

Proceed To Checkout
    [Documentation]    Starts the checkout flow from the cart.
    Tap Element    ${CART_CHECKOUT_BUTTON}
