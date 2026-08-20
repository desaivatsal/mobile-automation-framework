*** Settings ***
Documentation    iOS locators for the Products (catalogue) screen.


*** Variables ***
${PRODUCTS_TITLE}               xpath=//XCUIElementTypeStaticText[@name="PRODUCTS"]
${PRODUCTS_ITEM}                accessibility_id=test-Item
${PRODUCTS_ITEM_TITLE}          accessibility_id=test-Item title
${PRODUCTS_ITEM_PRICE}          accessibility_id=test-Price
${PRODUCTS_TOGGLE_VIEW}         accessibility_id=test-Toggle
${PRODUCTS_SORT_BUTTON}         accessibility_id=test-Modal Selector Button
${PRODUCTS_CART_BUTTON}         accessibility_id=test-Cart
${PRODUCTS_MENU_BUTTON}         accessibility_id=test-Menu
${PRODUCTS_CART_BADGE}          xpath=//XCUIElementTypeOther[@name="test-Cart"]//XCUIElementTypeStaticText
${MENU_LOGOUT}                  accessibility_id=test-LOGOUT
${MENU_ROOT}                    accessibility_id=test-Menu Item

# Parameterised locator - format with the product name before use.
${PRODUCT_BY_NAME}              xpath=//XCUIElementTypeStaticText[@name="{name}"]
