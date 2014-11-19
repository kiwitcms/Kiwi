ALTER TABLE `test_cases` MODIFY `estimated_time` integer NOT NULL;
ALTER TABLE `test_runs` MODIFY `estimated_time` integer NOT NULL;
ALTER TABLE `test_case_runs` DROP `iscurrent`;
ALTER TABLE `test_plan_texts` ADD COLUMN `checksum` varchar(32) NOT NULL;
ALTER TABLE `test_case_texts` ADD COLUMN `action_checksum` varchar(32) NOT NULL;
ALTER TABLE `test_case_texts` ADD COLUMN `effect_checksum` varchar(32) NOT NULL;
ALTER TABLE `test_case_texts` ADD COLUMN `setup_checksum` varchar(32) NOT NULL;
ALTER TABLE `test_case_texts` ADD COLUMN `breakdown_checksum` varchar(32) NOT NULL;