ALTER TABLE `test_cases` MODIFY `estimated_time` time;
ALTER TABLE `test_runs` MODIFY `estimated_time` time;
Alter TABLE `test_case_runs` ADD COLUMN `iscurrent` tinyint(4) NOT NULL;
ALTER TABLE `test_plan_texts` DROP `checksum`;
ALTER TABLE `test_case_texts` DROP `action_checksum`;
ALTER TABLE `test_case_texts` DROP `effect_checksum`;
ALTER TABLE `test_case_texts` DROP `setup_checksum`;
ALTER TABLE `test_case_texts` DROP `breakdown_checksum`;