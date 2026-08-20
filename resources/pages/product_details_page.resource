*** Settings ***
Documentation       Page object for the Product Details screen.

Resource            ../common/imports.resource
Resource            ../locators/${PLATFORM}/cart_locators.resource


*** Keywords ***
Product Details Should Be Displayed
    [Documentation]    Asserts a product detail screen is on display.
    Screen Should Be Displayed    ${DETAILS_ADD_TO_CART}    Product Details

Add Product To Cart
    [Documentation]    Adds the open product to the cart and waits for the control
    ...    to flip to "remove" - the app's own confirmation that it worked.
    Tap Element    ${DETAILS_ADD_TO_CART}
    Wait For Element    ${DETAILS_REMOVE}    screen=Product Details

Remove Product From Cart
    [Documentation]    Removes the open product from the cart.
    Tap Element    ${DETAILS_REMOVE}
    Wait For Element    ${DETAILS_ADD_TO_CART}    screen=Product Details

Get Product Price
    [Documentation]    Returns the displayed price as text, e.g. ``$29.99``.
    ${price}=    Get Text    ${DETAILS_PRICE}
    RETURN    ${price}

Go Back To Products
    [Documentation]    Uses the on-screen back control, which exists on both
    ...    platforms, rather than the Android hardware key - keeps the flow identical.
    Scroll Until Element Is Visible    ${DETAILS_BACK}    down
    Tap Element    ${DETAILS_BACK}
