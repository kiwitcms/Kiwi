*** Settings ***
Library           SeleniumLibrary

*** Variables ***
${SERVER}               https://localhost
${BROWSER}              Headless Firefox
${DELAY}                0
${LOGIN_URL}            ${SERVER}/accounts/login/
${DASHBOARD_URL}        ${SERVER}/
${TEST_PLAN_URL}        ${SERVER}/plan/1/


*** Test Cases ***
Uploading file works via file upload
    Open Browser    ${LOGIN_URL}    ${BROWSER}
    Maximize Browser Window
    Set Selenium Speed    ${DELAY}
    Title Should Be    Kiwi TCMS - Login

    Input Text    inputUsername    testadmin
    Input Text    inputPassword    password
    Click Button  Log in

    Location Should Be    ${DASHBOARD_URL}
    Title Should Be       Kiwi TCMS - Dashboard

    Go To                 ${TEST_PLAN_URL}
    Choose File   id:id_attachment_file    ${CURDIR}${/}test_upload_file.robot
    Click Button  Add attachment
    Page Should Contain   Your attachment was uploaded

    [Teardown]    Close Browser
