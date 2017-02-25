TC_REMOVE_CC = '''
DELETE contact
FROM `testcases_testcaseemailsettings` eset
JOIN `tcms_contacts` contact ON (eset.id = contact.object_pk)
WHERE eset.case_id IN (%s)
  AND contact.email IN (%s);
'''