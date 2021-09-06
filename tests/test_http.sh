#!/bin/bash

. /usr/share/beakerlib/beakerlib.sh

assert_up_and_running() {
    sleep 10
    IP_ADDRESS=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kiwi_web`
    # both HTTP and HTTPS display the login page
    rlRun -t -c "curl    -L -o- http://$IP_ADDRESS:8080/  | grep 'Welcome to Kiwi TCMS'"
    rlRun -t -c "curl -k -L -o- https://$IP_ADDRESS:8443/ | grep 'Welcome to Kiwi TCMS'"
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
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Check for SSL warning message"
        rlRun -t -c "docker exec -i kiwi_web /Kiwi/manage.py createsuperuser \
            --username testadmin --email testadmin@domain.com --noinput"
        rlRun -t -c "docker exec -i kiwi_web /Kiwi/manage.py set_fake_passwords"
        IP_ADDRESS=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kiwi_web`
        rm -f /tmp/testcookies.txt
        rlRun -t -c "curl -k -L -o- -c /tmp/testcookies.txt https://$IP_ADDRESS:8443/"
        CSRF_TOKEN=`grep csrftoken /tmp/testcookies.txt | cut -f 7`
        rlRun -t -c "curl -e https://$IP_ADDRESS:8443/ -d username=testadmin \
            -d password=password -d csrfmiddlewaretoken=$CSRF_TOKEN -k -L -o /tmp/testdata.sslon \
            -b /tmp/testcookies.txt https://$IP_ADDRESS:8443/accounts/login/"
        rlAssertNotGrep "You are not using a secure connection." /tmp/testdata.sslon
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun -t -c "docker-compose down"
        if [ -n "$ImageOS" ]; then
            rlRun -t -c "docker volume rm kiwi_db_data"
        fi
    rlPhaseEnd
rlJournalEnd

rlJournalPrintText
