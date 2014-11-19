ALTER TABLE `test_case_bug_systems` ADD COLUMN `validate_reg_exp` varchar(128) NOT NULL;
UPDATE `test_case_bug_systems`
SET    `validate_reg_exp` = '^\\d{1,7}$',
       `name` = 'Bugzilla',
       `description` = '1-7 digit, e.g. 1001234'
WHERE  id = 1;

UPDATE `test_case_bug_systems`
SET    `validate_reg_exp` = '^[A-Z0-9]+-\\d+$',
       `name` = 'JIRA',
       `description` = 'e.g. TCMS-222'
WHERE  id = 2;