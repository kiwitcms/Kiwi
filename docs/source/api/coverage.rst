XMl-RPC object/attribute coverage
---------------------------------

This is an overview of the object/attribute coverage. Useful to
compare the actual names used for different xmlrpc calls.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 Test Plan Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FIELD             CREATE                    GET                         UPDATE
id                ---                       plan_id                     ---
author            ---                       author_id                   ---
name              name*                     name                        name
parent            parent                    parent_id                   parent
product           product*                  product_id                  product
product.version   default_product_version*  default_product_version     default_product_version
type              type*                     type_id                     type
---               text*                     TestPlan.get_text           TestPlan.store_text
---               is_active                 is_active                   is_active
---               ---                       create_date                 ---
---               ---                       extra_link                  ---
---               ---                       ---                         env_group

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 Test Run Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FIELD         CREATE              GET                 UPDATE
id            ---                 run_id              ---
testplan      plan*               plan_id             plan?
build         build*              build_id            build
manager       manager*            manager_id          manager
summary       summary*            summary             summary
product       product*            ---                 product
---           product_version*    product_version     product_version
tester        default_tester      default_tester_id   default_tester
---           plan_text_version                       plan_text_version
time          estimated_time      estimated_time      estimated_time
notes         notes               notes               notes
status        status              ---                 status
caseruns      case                ---                 ---
tags          tag                 ---                 ---
---           ---                 environment_id      ---
---           ---                 plan_text_version   ---
---           ---                 start_date          ---
---           ---                 stop_date           ---

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 Test Case Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FIELD         CREATE              GET                 UPDATE
id            ---                 case_id             ---
arguments     arguments           arguments           arguments
author        ---                 author_id           ---
automated     is_automated        is_automated        is_automated
bugs          bug                 ---                 ---
category      category*           category_id         category
components    component           ---                 ---
notes         notes               notes               notes
testplans     plan                ---                 ---
priority      priority*           priority_id         priority
---           product*            ---                 product
script        script              script              script
sortkey       sortkey             sortkey             sortkey
status        case_status         case_status_id      case_status
summary       summary*            summary             summary
tags          tag                 ---                 ---
tester        default_tester      default_tester_id   default_tester
time          estimated_time      estimated_time      estimated_time
---           is_automated_pro... is_automated_pro... is_automated_pro...
---           requirement         requirement         requirement
---           alias               alias               alias
---           action              text.action         ---
---           effect              text.effect         ---
---           setup               text.setup          ---
---           breakdown           text.breakdown      ---
---           ---                 create_date         ---
---           ---                 reviewer_id         ---

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 Case Run Properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FIELD         CREATE              GET                 UPDATE
id            ---                 case_run_id         ---
assignee      assignee            assignee_id         assignee
build         build*              build_id            build
notes         notes               notes               notes
sortkey       sortkey             sortkey             sortkey
status        case_run_status     case_run_status_id  case_run_status
testcase      case*               case_id             ---
testrun       run*                run_id              ---
---           case_text_version   case_text_version   ---
