# pylint: disable=unused-argument, no-self-use, avoid-list-comprehension
from django.db.models import signals
from simple_history.models import HistoricalRecords
from simple_history.admin import SimpleHistoryAdmin


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
        change_reason = []

        if hasattr(instance, 'previous'):
            for field in self.fields_included(instance):
                old_value = getattr(instance.previous, field.attname)
                new_value = getattr(instance, field.attname)
                if old_value != new_value:
                    change_reason.append("%s: %s -> %s" % (field.attname, old_value, new_value))
        instance.changeReason = "; ".join(change_reason)
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
