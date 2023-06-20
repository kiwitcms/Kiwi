#!/bin/bash

. /usr/share/beakerlib/beakerlib.sh

assert_up_and_running() {
    sleep 10
    # HTTP redirects; HTTPS displays the login page
    rlRun -t -c "curl       -o- http://localhost/  | grep '301 Moved Permanently'"
    rlRun -t -c "curl -k -L -o- https://localhost/ | grep 'Welcome to Kiwi TCMS'"
}

assert_perform_initdb() {
    sleep 10
    # HTTPS displays the init-db page
    rm -f /tmp/testcookies.txt
    rlRun -t -c "curl -k -L -o- -c /tmp/testcookies.txt https://localhost/ | grep 'Initialize database'"
    # init-db page applies database migrations
    CSRF_TOKEN=$(grep csrftoken /tmp/testcookies.txt | cut -f 7)
    rlRun -t -c "curl -e https://localhost/init-db/ \
        -d init_db=yes -d csrfmiddlewaretoken=$CSRF_TOKEN -k -L -o- \
        -b /tmp/testcookies.txt https://localhost/init-db/"
}

rlJournalStart
    rlPhaseStartTest "[PostgreSQL] Container up"
        rlRun -t -c "docker-compose -f docker-compose.postgres up -d"
        assert_perform_initdb
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "/Kiwi/uploads/installation-id was created"
        rlRun -t -c "docker exec -i kiwi_web cat /Kiwi/uploads/installation-id"
    rlPhaseEnd

    rlPhaseStartTest "Container specifies a health-check command"
        rlRun -t -c "docker inspect -f '{{.State.Health.Status}}' kiwi_web"
    rlPhaseEnd

    rlPhaseStartTest "Use pg_dump for backup"
        rlRun -t -c "docker exec -i kiwi_db pg_dump -U kiwi --dbname=kiwi -F c > backup.bak"
        rlAssertExists "backup.bak"
        sleep 5
    rlPhaseEnd

    rlPhaseStartTest "Use pg_restore to restore from a backup"
        rlRun -t -c "cat backup.bak | docker exec -i kiwi_db pg_restore -U kiwi --dbname=template1 -vcC"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "[PostgreSQL] Container restart"
        rlRun -t -c "docker-compose -f docker-compose.postgres restart"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Backup files"
        rlRun -t -c "docker exec -i kiwi_web /bin/bash -c 'echo TEST-ME > /Kiwi/uploads/test.txt'"
        rlRun -t -c "docker exec -i kiwi_web /bin/tar -cP /Kiwi/uploads > uploads.tar"
        rlAssertExists "uploads.tar"
    rlPhaseEnd

    rlPhaseStartTest "Restore files"
        rlRun -t -c "docker exec -i kiwi_web /bin/rm -rf /Kiwi/uploads/*"
        rlRun -t -c "cat uploads.tar | docker exec -i kiwi_web /bin/tar -x"
        rlRun -t -c "docker exec -i kiwi_web /bin/bash -c 'cat /Kiwi/uploads/test.txt | grep TEST'"
    rlPhaseEnd

    rlPhaseStartCleanup "[PostgreSQL] Cleanup"
        rlRun -t -c "docker-compose -f docker-compose.postgres down"

        if [ -n "$ImageOS" ]; then
            rlRun -t -c "docker volume rm kiwi_db_data"
        fi
    rlPhaseEnd

    # wait for tear-down b/c in Travis CI subsequent tests can't find
    # the db host
    sleep 5

    # the rest of the scenarios use MariaDB by default
    rlPhaseStartTest "Container up"
        rlRun -t -c "docker-compose up -d"
        assert_perform_initdb
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartTest "Use mariadb-dump for backup"
        rlRun -t -c "docker exec -i kiwi_db mariadb-dump --user kiwi --password=kiwi kiwi > backup.sql"
        rlAssertExists "backup.sql"
    rlPhaseEnd

    rlPhaseStartTest "Restore from a backup"
        rlRun -t -c "cat backup.sql | docker exec -i kiwi_db mariadb --user kiwi --password=kiwi -v kiwi"
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
        if [ -n "$ImageOS" ]; then
            rlRun -t -c "docker volume rm kiwi_db_data"
        fi
    rlPhaseEnd

    sleep 5

    rlPhaseStartTest "Start Kiwi TCMS with Docker Secrets"
        rlRun -t -c "docker-compose -f docker-compose.with-secrets up -d"
        sleep 10

        rlRun -t -c "docker exec -i kiwi_web /Kiwi/manage.py migrate"
        assert_up_and_running
    rlPhaseEnd

    rlPhaseStartCleanup
        rlRun -t -c "docker-compose -f docker-compose.with-secrets down"
        if [ -n "$ImageOS" ]; then
            rlRun -t -c "docker volume rm kiwi_db_data"
        fi
    rlPhaseEnd

rlJournalEnd

rlJournalPrintText
