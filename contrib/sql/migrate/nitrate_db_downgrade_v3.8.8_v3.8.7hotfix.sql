-- Drop index on dt_insert.
DROP INDEX `xmlrpc_xmlrpclog_62ffa694` ON `xmlrpc_xmlrpclog`;

-- Drop django-celery schemas
DROP TABLE IF EXISTS `celery_taskmeta`;
DROP TABLE IF EXISTS `celery_tasksetmeta`;
DROP TABLE IF EXISTS `djcelery_periodictask`;
DROP TABLE IF EXISTS `djcelery_crontabschedule`;
DROP TABLE IF EXISTS `djcelery_intervalschedule`;
DROP TABLE IF EXISTS `djcelery_periodictasks`;
DROP TABLE IF EXISTS `djcelery_taskstate`;
DROP TABLE IF EXISTS `djcelery_workerstate`;
DROP TABLE IF EXISTS `djkombu_message`;
DROP TABLE IF EXISTS `djkombu_queue`;

-- Drop change test_case_bugs.bug_id to varchar
ALTER table test_case_bugs modify column bug_id int(11);   
