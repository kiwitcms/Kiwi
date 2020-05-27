#!/bin/bash

. /usr/share/beakerlib/beakerlib.sh

assert_up_and_running() {
    sleep 10
    IP_ADDRESS=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' kiwi_web`
    # HTTP redirects; HTTPS displays the login page
    rlRun -t -c "curl       -o- http://$IP_ADDRESS:8080/  | grep 'The document has moved'"
    rlRun -t -c "curl -k -L -o- https://$IP_ADDRESS:8443/ | grep 'Welcome to Kiwi TCMS'"
}

rlJournalStart
    rlPhaseStartTest "[PostgreSQL] Container up"
        rlRun -t -c "docker-compose -f docker-compose.postgres up -d"
        sleep 10
        rlRun -t -c "docker exec -i kiwi_web /Kiwi/manage.py migrate"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "[PostgreSQL] Container restart"
        rlRun -t -c "docker-compose -f docker-compose.postgres restart"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartCleanup "[PostgreSQL] Cleanup"
        rlRun -t -c "docker-compose -f docker-compose.postgres down"

        if [ -n "$TRAVIS" ]; then
            rlRun -t -c "docker volume rm kiwi_db_data"
        fi
    rlPhaseEnd

    # wait for tear-down b/c in Travis CI subsequent tests can't find
    # the db host
    sleep 5

    # the rest of the scenarios use MariaDB by default
    rlPhaseStartTest "Container up"
        rlRun -t -c "docker-compose up -d"
        sleep 10
        rlRun -t -c "docker exec -i kiwi_web /Kiwi/manage.py migrate"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Container restart"
        rlRun -t -c "docker-compose restart"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Container stop & start"
        rlRun -t -c "docker-compose stop"
        sleep 5
        rlRun -t -c "docker-compose start"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Container kill & start"
        rlRun -t -c "docker-compose kill"
        sleep 5
        rlRun -t -c "docker-compose start"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun -t -c "docker-compose down"
    rlPhaseEnd
rlJournalEnd

rlJournalPrintText
