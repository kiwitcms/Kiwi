ALTER TABLE `test_runs` ADD COLUMN `product_version_id` integer NOT NULL;

ALTER TABLE `test_runs` ADD CONSTRAINT `product_version_id_refs_id_04d78037` FOREIGN KEY (`product_version_id`) REFERENCES `versions` (`id`);

UPDATE test_runs tr 
INNER JOIN test_builds tb 
ON (tr.build_id = tb.build_id) 
INNER JOIN versions v 
ON (tb.product_id=v.product_id and tr.product_version=v.value) 
SET tr.product_version_id = v.id;

ALTER TABLE test_runs DROP `product_version`;

ALTER TABLE `test_plans` DROP `default_product_version`; 
ALTER TABLE `test_plans` MODIFY `product_version_id` integer NOT NULL;
ALTER TABLE `test_plans` ADD CONSTRAINT `product_version_id_refs_id_41bac2c2` FOREIGN KEY (`product_version_id`) REFERENCES `versions` (`id`);

CREATE FULLTEXT INDEX test_case_script_idx ON test_cases(script);

INSERT into products(`name`, `classification_id`, `description`, `disallownew`, `votestoconfirm`) values ("Archive Product", 5, "A dummy proudct, the runs with invalid product_verison will blong to this product.", 0, 0);

INSERT into versions(`value`, `product_id`) values ("dummy version", (SELECT id from `products` where name="Archive Product"));

UPDATE test_runs tr
SET tr.product_version_id = CASE
WHEN tr.product_version_id = 0 THEN (select id from `versions` where value = "dummy version")
ELSE tr.product_version_id
END;
