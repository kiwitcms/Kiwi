# pylint: disable=unused-argument, no-self-use, avoid-list-comprehension
import difflib

from django.db.models import signals
from simple_history.models import HistoricalRecords
from simple_history.admin import SimpleHistoryAdmin


def diff_objects(old_instance, new_instance, fields):
    """
        Diff two objects by examining the given fields and
        return a string.
    """
    full_diff = []

    for field in fields:
        field_diff = []
        old_value = getattr(old_instance, field.attname)
        new_value = getattr(new_instance, field.attname)
        for line in difflib.unified_diff([str(old_value)],
                                         [str(new_value)],
                                         fromfile=field.attname,
                                         tofile=field.attname,
                                         lineterm="",
                                        ):
            field_diff.append(line)
        full_diff.extend(field_diff)

    return "\n".join(full_diff)


class KiwiHistoricalRecords(HistoricalRecords):
    """
        This class will keep track of what fields were changed
        inside of the ``history_change_reason`` field. This gives us
        a crude changelog until upstream introduces their new interface.
    """

    def pre_save(self, instance, **kwargs):
        """
            Signal handlers don't have access to the previous version of
            an object so we have to load it from the database!
        """
        if instance.pk and hasattr(instance, 'history'):
            instance.previous = instance.__class__.objects.get(pk=instance.pk)

    def post_save(self, instance, created, **kwargs):
        """
            Calculate the changelog and call the inherited method to
            write the data into the database.
        """
        if hasattr(instance, 'previous'):
            instance.changeReason = diff_objects(instance.previous,
                                                 instance,
                                                 self.fields_included(instance))
        super().post_save(instance, created, **kwargs)

    def finalize(self, sender, **kwargs):
        """
            Connect the pre_save signal handler after calling the inherited method.
        """
        super().finalize(sender, **kwargs)
        signals.pre_save.connect(self.pre_save, sender=sender, weak=False)


class ReadOnlyHistoryAdmin(SimpleHistoryAdmin):
    """
        Custom history admin which shows all fields
        as read-only.
    """
    history_list_display = ['history_change_reason']

    def get_readonly_fields(self, request, obj=None):
        # make all fields readonly
        readonly_fields = list(set(
            [field.name for field in self.opts.local_fields] +
            [field.name for field in self.opts.local_many_to_many]
        ))
        return readonly_fields
