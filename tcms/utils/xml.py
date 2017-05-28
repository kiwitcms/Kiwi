from django.conf import settings
from django.contrib.auth.models import User

from tcms.core.contrib.xml2dict.xml2dict import XML2Dict
from tcms.management.models import Priority, TestTag
from tcms.testcases.models import TestCaseStatus


def clean_xml_file(xml_file):
    xml_file = xml_file.replace('\n', '')
    xml_file = xml_file.replace('&testopia_', '&')
    xml_file = xml_file.encode("utf8")

    xml = XML2Dict()
    xml_data = xml.fromstring(xml_file)
    root_element = xml_data.get('testopia', None)
    if root_element is None:
        raise ValueError('Invalid XML, root should be "testopia"!')
    if not root_element.get('version', None) != settings.TESTOPIA_XML_VERSION:
        raise ValueError('Testopia XML version should be "%s"' % settings.TESTOPIA_XML_VERSION)
    case_elements = root_element.get('testcase', None)
    if case_elements is not None:
        if isinstance(case_elements, list):
            return map(process_case, case_elements)
        elif isinstance(case_elements, dict):
            return map(process_case, (case_elements,))
        else:
            raise ValueError('Element "testcase" is not a list or a dict!')
    else:
        raise ValueError('No case found in XML document.')


def process_case(case):
    # Check author
    author = case.get('author', {}).get('value')
    if author:
        try:
            author = User.objects.get(email=author)
            author_id = author.id
        except User.DoesNotExist:
            raise ValueError('Author "{0}" not found in DB!'.format(author))
    else:
        raise ValueError('Element "author" is required in XML')

    # Check default tester
    default_tester_email = case.get('defaulttester', {}).get('value')
    try:
        default_tester = User.objects.get(email=default_tester_email)
        default_tester_id = default_tester.id
    except User.DoesNotExist:
        default_tester_id = None

    # Check priority
    priority = case.get('priority', {}).get('value')
    if priority:
        try:
            priority = Priority.objects.get(value=priority)
            priority_id = priority.id
        except Priority.DoesNotExist:
            raise ValueError('Priority "{0}" not found in DB!'.format(priority))
    else:
        raise ValueError('Element "priority" is required in XML')

    # Check automated status
    automated = case.get('automated', {}).get('value')
    is_automated = automated == 'Automatic'

    # Check status
    status = case.get('status', {}).get('value')
    try:
        case_status = TestCaseStatus.objects.get(name=status)
    except TestCaseStatus.DoesNotExist:
        case_status = TestCaseStatus.objects.get(name='PROPOSED')
    case_status_id = case_status.id

    # Check category
    # *** Ugly code here ***
    # There is a bug in the XML file, the category is related to product.
    # But unfortunate it did not defined product in the XML file.
    # So we have to define the category_name at the moment then get the product from the plan.
    # If we did not found the category of the product we will create one.
    category_name = case.get('categoryname', {}).get('value')
    if not category_name:
        raise ValueError('Element "categoryname" is required in XML')

    # Check or create the tag
    element = 'tag'
    if case.get(element, {}):
        tags = []
        if isinstance(case[element], dict):
            tag, create = TestTag.objects.get_or_create(name=case[element]['value'])
            tags.append(tag)

        if isinstance(case[element], list):
            for tag_name in case[element]:
                tag, create = TestTag.objects.get_or_create(name=tag_name['value'])
                tags.append(tag)
    else:
        tags = None

    new_case = {
        'summary': case.get('summary', {}).get('value', ''),
        'author_id': author_id,
        'author': author,
        'default_tester_id': default_tester_id,
        'priority_id': priority_id,
        'is_automated': is_automated,
        'case_status_id': case_status_id,
        'category_name': category_name,
        'notes': case.get('notes', {}).get('value', ''),
        'action': case.get('action', {}).get('value', ''),
        'effect': case.get('expectedresults', {}).get('value', ''),
        'setup': case.get('setup', {}).get('value', ''),
        'breakdown': case.get('breakdown', {}).get('value', ''),
        'tags': tags,
    }

    return new_case
