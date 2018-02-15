

def post_run_saved(sender, *args, **kwargs):
    instance = kwargs['instance']

    if kwargs.get('created'):
        instance.mail(
            template='mail/new_run.txt',
            subject='New run create from plan %s: %s' % (
                instance.plan_id, instance.summary
            ),
            context={'test_run': instance, }
        )
    else:
        instance.mail(
            template='mail/update_run.txt',
            subject='Test Run %s - %s has been updated' % (
                instance.pk, instance.summary
            ),
            context={'test_run': instance, }
        )


def post_case_run_saved(sender, *args, **kwargs):
    instance = kwargs['instance']
    if kwargs.get('created'):
        tr = instance.run
        tr.update_completion_status(is_auto_updated=True)


def post_case_run_deleted(sender, **kwargs):
    instance = kwargs['instance']
    tr = instance.run
    tr.update_completion_status(is_auto_updated=True)


def post_update_handler(sender, **kwargs):
    instances = kwargs['instances']
    instance = instances[0]
    tr = instance.run
    tr.update_completion_status(is_auto_updated=True)


def pre_save_clean(sender, **kwargs):
    instance = kwargs['instance']
    instance.clean()
