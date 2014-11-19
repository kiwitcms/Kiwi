-- Upgrade database schemas from v3.8.7 to v3.8.7-hotfix.

-- Convert column `object_pk` data type from text to int.
ALTER TABLE `tcms_linkrefs` MODIFY COLUMN `object_pk` int(11);
ALTER TABLE `tcms_logs` MODIFY COLUMN `object_pk` int(11);
ALTER TABLE `tcms_bookmarks` MODIFY COLUMN `object_pk` int(11);
ALTER TABLE `tcms_contacts` MODIFY COLUMN `object_pk` int(11);
ALTER TABLE django_comments MODIFY object_pk INT NOT NULL;

-- Create composite index to optimize `table join`.
CREATE INDEX `tcms_bookmarks_62ffa694` ON `tcms_bookmarks` (`content_type_id`, `object_pk`, `site_id`);
CREATE INDEX `tcms_logs_62ffa694` ON `tcms_logs` (`content_type_id`, `object_pk`, `site_id`);
CREATE INDEX `tcms_contacts_62ffa694` ON `tcms_contacts` (`content_type_id`, `object_pk`, `site_id`);
CREATE INDEX `tcms_linkrefs_62ffa694` ON `tcms_linkrefs` (`object_pk`, `content_type_id`, `site_id`);
CREATE UNIQUE INDEX uniq_idx_case_run_status_name ON test_case_run_status (name);

-- Index maintenance for django comments
CREATE INDEX idx_comments_site_contenttype_objpk ON django_comments (site_id, content_type_id, object_pk);
DROP INDEX site_id_refs_id_8db720f8 ON django_comments;