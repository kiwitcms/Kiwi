*** Settings ***
Library           SeleniumLibrary

*** Variables ***
${SERVER}               https://localhost
${BROWSER}              Headless Firefox
${DELAY}                0
${SVG_URL}              ${SERVER}/uploads/attachments/auth_user/2/inline_javascript.svg
${HTML_URL}             ${SERVER}/uploads/attachments/auth_user/2/html_with_external_script.html


*** Test Cases ***
Directly accessing an SVG image should not execute inline JavaScript
    Open Browser    ${SVG_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}

    Location Should Be    ${SVG_URL}

    [Teardown]    Close Browser


Directly accessing an HTML file should not execute JavaScript
    Open Browser    ${HTML_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}

    Location Should Be    ${HTML_URL}

    [Teardown]    Close Browser
