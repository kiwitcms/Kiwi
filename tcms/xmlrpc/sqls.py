TP_CLEAR_ENV_GROUP = '''
DELETE FROM `tcms_env_plan_map` where plan_id in (%s)
'''

TP_ADD_ENV_GROUP = '''
INSERT INTO `tcms_env_plan_map` (`plan_id`, `group_id`) values %s
'''

TC_REMOVE_CC = '''
DELETE contact
FROM `testcases_testcaseemailsettings` eset
JOIN `tcms_contacts` contact ON (eset.id = contact.object_pk)
WHERE eset.case_id IN (%s)
  AND contact.email IN (%s);
'''