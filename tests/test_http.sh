#!/bin/bash

. /usr/share/beakerlib/beakerlib.sh

assert_up_and_running() {
    sleep 10
    # both HTTP and HTTPS display the login page
    rlRun -t -c "curl    -L -o- http://$1:8080/  | grep 'Welcome to Kiwi TCMS'"
    rlRun -t -c "curl -k -L -o- https://$1:8443/ | grep 'Welcome to Kiwi TCMS'"
}

get_dashboard() {
    rlRun -t -c "curl -k -L -o- -c /tmp/testcookies.txt $1/"
    CSRF_TOKEN=$(grep csrftoken /tmp/testcookies.txt | cut -f 7)
    rlRun -t -c "curl -e $1/accounts/login/ -d username=testadmin -d password=password \
        -d csrfmiddlewaretoken=$CSRF_TOKEN -k -L -i -o /tmp/testdata.txt \
        -b /tmp/testcookies.txt $1/accounts/login/"
    rlAssertGrep "<title>Kiwi TCMS - Dashboard</title>" /tmp/testdata.txt
}

rlJournalStart
    rlPhaseStartSetup
        # wait for tear-down from previous script b/c
        # in CI subsequent tests can't find the db host
        sleep 5
    rlPhaseEnd

    rlPhaseStartTest "Plain HTTP works"
        rlRun -t -c "docker-compose run -d -e KIWI_DONT_ENFORCE_HTTPS=true --name kiwi_web web /httpd-foreground"
        sleep 10
        rlRun -t -c "docker exec -i kiwi_web /Kiwi/manage.py migrate"
        IP_ADDRESS=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kiwi_web)
        assert_up_and_running "$IP_ADDRESS"
    rlPhaseEnd

    rlPhaseStartTest "Should not display SSL warning for HTTPS connection"
        rlRun -t -c "docker exec -i kiwi_web /Kiwi/manage.py createsuperuser \
            --username testadmin --email testadmin@domain.com --noinput"
        rlRun -t -c "cat tests/set_testadmin_pass.py | docker exec -i kiwi_web /Kiwi/manage.py shell"
        URL="https://$IP_ADDRESS:8443"
        get_dashboard "$URL"
        rlAssertNotGrep "You are not using a secure connection." /tmp/testdata.txt
    rlPhaseEnd

    rlPhaseStartTest "Should display SSL warning for HTTP connection"
        URL="http://$IP_ADDRESS:8080"
        get_dashboard "$URL"
        rlAssertGrep "You are not using a secure connection." /tmp/testdata.txt
    rlPhaseEnd

    rlPhaseStartTest "Should allow file upload with UTF-8 filenames"
        cat > ~/.tcms.conf << _EOF_
[tcms]
url = https://$IP_ADDRESS:8443/xml-rpc/
username = testadmin
password = password
_EOF_

        rlRun -t -c "./tests/test_utf8_uploads.py -v"
    rlPhaseEnd

    rlPhaseStartTest "Should send ETag header"
        rlRun -t -c "curl -k -D- https://$IP_ADDRESS:8443/static/images/kiwi_h20.png 2>/dev/null | grep 'ETag'"
    rlPhaseEnd

    rlPhaseStartTest "Should NOT send Cache-Control header"
        rlRun -t -c "curl -k -D- https://$IP_ADDRESS:8443/static/images/kiwi_h20.png 2>/dev/null | grep 'Cache-Control'" 1
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun -t -c "docker-compose down"
        rm -f /tmp/testcookies.txt
        rm -f /tmp/testdata.txt
        if [ -n "$ImageOS" ]; then
            rlRun -t -c "docker volume rm kiwi_db_data"
        fi
    rlPhaseEnd
rlJournalEnd

rlJournalPrintText
