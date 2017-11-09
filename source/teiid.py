# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Python API for the Nitrate test case management system.
#   Copyright (c) 2012 Red Hat, Inc. All rights reserved.
#   Author: Petr Splichal <psplicha@redhat.com>
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
Teiid support

For enhanced query performance it's possible to use a Teiid instance.
Use the following config snippet to enable access via psycopg2 module:

    [teiid]
    user = username
    password = password
    database = public
    host = host.example.com
    port = 5432
"""

import psycopg2

from nitrate.config import log, Config
from nitrate.xmlrpc import NitrateError

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Exceptions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TeiidError(NitrateError):
    """ General Teiid Error """
    pass

class TeiidNotConfigured(TeiidError):
    """ Teiid not configured """
    pass

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Teiid Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Teiid(object):
    """ Teiid interface for Nitrate """

    def __init__(self):
        """ Initialize the connection if Teiid configured """
        # Fetch connection data from the config, bail out if missing
        config = Config()
        try:
            database = config.teiid.database
            user = config.teiid.user
            password = config.teiid.password
            host = config.teiid.host
            port = config.teiid.port
        except AttributeError:
            log.debug("Teiid not configured, skipping db connection")
            self.connection = None
            return
        # Initialize the connection
        log.debug("Connecting as {0} to database {1} at {2}:{3}".format(
                user, database, host, port))
        try:
            self.connection = psycopg2.connect(database=database,
                    user=user, password=password, host=host, port=port)
        except psycopg2.DatabaseError as error:
            log.error("Teiid connect error: {0}".format(error))
            raise TeiidError("Failed to connect to the Teiid instance")
        self.connection.set_isolation_level(0)

    def cursor(self):
        """ Create and return a new cursor """
        if self.connection is None:
            raise TeiidNotConfigured("Teiid is not configured")
        return self.connection.cursor()

    def query(self, query):
        """ Execute sql query, return the dictified result """
        # Prepare the cursor, execute the query
        cursor = self.cursor()
        cursor.execute(query)
        # Parse columns, fetch rows
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        # Convert longs into ints and dictify the table
        rows = [[int(item) if isinstance(item, long) else item
                for item in row] for row in rows]
        return [dict(zip(columns, row)) for row in rows]

    def run_case_runs(self, testrun):
        """ Fetch case runs for given test run """
        return self.query("""
                SELECT case_run_id, case_id, assignee_id, build_id, notes,
                        sortkey, case_run_status_id, run_id
                FROM test_case_runs
                WHERE run_id = {0}
                """.format(testrun))

    def run_cases(self, testrun):
        """ Fetch test cases for given test run """
        return self.query("""
                SELECT arguments, author_id, test_cases.case_id,
                        case_status_id, category_id, creation_date as
                        create_date, default_tester_id,
                        concat('', estimated_time) as estimated_time,
                        extra_link, isautomated as is_automated,
                        is_automated_proposed, test_cases.notes, priority_id,
                        requirement, script, sortkey, summary
                FROM test_cases
                JOIN test_case_runs
                ON test_cases.case_id = test_case_runs.case_id
                WHERE run_id = {0}
                """.format(testrun))
