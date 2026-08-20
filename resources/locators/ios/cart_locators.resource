*** Settings ***
Documentation    iOS locators for the Product Details and Cart screens.


*** Variables ***
# --- Product details --------------------------------------------------------
${DETAILS_ADD_TO_CART}          accessibility_id=test-ADD TO CART
${DETAILS_REMOVE}               accessibility_id=test-REMOVE
${DETAILS_BACK}                 accessibility_id=test-BACK TO PRODUCTS
${DETAILS_DESCRIPTION}          accessibility_id=test-Description
${DETAILS_PRICE}                accessibility_id=test-Price

# --- Cart -------------------------------------------------------------------
${CART_TITLE}                   xpath=//XCUIElementTypeStaticText[@name="YOUR CART"]
${CART_ITEM}                    accessibility_id=test-Item
${CART_ITEM_TITLE}              accessibility_id=test-Item title
${CART_CHECKOUT_BUTTON}         accessibility_id=test-CHECKOUT
${CART_CONTINUE_SHOPPING}       accessibility_id=test-CONTINUE SHOPPING
${CART_QUANTITY}                accessibility_id=test-Amount
