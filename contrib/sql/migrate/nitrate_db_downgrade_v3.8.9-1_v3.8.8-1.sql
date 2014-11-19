ALTER TABLE `test_runs` ADD COLUMN  `product_version` varchar(192);

UPDATE test_runs tr
INNER JOIN versions v 
ON (tr.product_version_id = v.id)
SET tr.product_version = v.value;

ALTER TABLE `test_runs` DROP FOREIGN KEY `product_version_id_refs_id_04d78037`;
ALTER TABLE `test_runs` DROP `product_version_id`;

ALTER TABLE `test_plans` ADD COLUMN  `default_product_version` varchar(192) NOT NULL;

UPDATE test_plans tp
INNER JOIN versions v 
ON (tp.product_version_id = v.id)
SET tp.default_product_version = v.value;

DROP INDEX test_case_script_idx ON test_cases;