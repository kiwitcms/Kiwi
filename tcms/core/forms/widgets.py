# -*- coding: utf-8 -*-
import datetime

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

SECONDS_PER_MIN = 60
SECONDS_PER_HOUR = 3600  # SECONDS_PER_MIN * 60
SECONDS_PER_DAY = 86400  # SECONDS_PER_HOUR * 24


class TimedeltaWidget(forms.Widget):
    INPUTS = ['days', 'hours', 'minutes', 'seconds']
    MULTIPLY = [SECONDS_PER_DAY, SECONDS_PER_HOUR, SECONDS_PER_MIN, 1]

    ESTIMATED_DAYS_CHOICE = [(x, x) for x in range(0, 10)]
    ESTIMATED_HOURS_CHOICE = [(x, x) for x in range(0, 24)]
    ESTIMATED_MINUTES_CHOICE = [(x, x) for x in range(0, 60)]
    ESTIMATED_SECONDS_CHOICE = [(x, x) for x in range(0, 60)]

    def __init__(self, attrs=None):
        self.widgets = []
        if not attrs:
            attrs = {}
        inputs = attrs.get('inputs', self.INPUTS)
        multiply = []
        for input in inputs:
            assert input in self.INPUTS, (input, self.INPUT)
            self.widgets.append(
                forms.Select(
                    attrs=attrs,
                    choices=getattr(
                        self,
                        'ESTIMATED_' + input.upper() + '_CHOICE'
                    )
                )
            )
            multiply.append(self.MULTIPLY[self.INPUTS.index(input)])
        self.inputs = inputs
        self.multiply = multiply
        super(TimedeltaWidget, self).__init__(attrs)

    def render(self, name, value, attrs):
        if value is None:
            values = [0 for i in self.inputs]
        elif isinstance(value, datetime.timedelta):
            values = split_seconds(
                value.days * SECONDS_PER_DAY + value.seconds,
                self.inputs, self.multiply
            )
        elif isinstance(value, int):
            # initial data from model
            values = split_seconds(value, self.inputs, self.multiply)
        else:
            assert isinstance(value, tuple), (value, type(value))
            assert len(value) == len(self.inputs), (value, self.inputs)
            values = value
        id = attrs.pop('id')
        assert not attrs, attrs
        rendered = []
        for input, widget, val in zip(self.inputs, self.widgets, values):
            rendered.append(u'%s %s' % (
                widget.render('%s_%s' % (name, input), val), _(input)))
        return mark_safe('<div id="%s">%s</div>' % (id, ' '.join(rendered)))

    def value_from_datadict(self, data, files, name):
        # Don't throw ValidationError here, just return a tuple of strings.
        ret = []
        for input, multi in zip(self.inputs, self.multiply):
            ret.append(data.get('%s_%s' % (name, input), 0))
        return tuple(ret)

    def _has_changed(self, initial_value, data_value):
        # data_value comes from value_from_datadict(): A tuple of strings.
        assert isinstance(initial_value, datetime.timedelta), initial_value
        initial = tuple([unicode(i) for i in split_seconds(
            initial_value.days * SECONDS_PER_DAY + initial_value.seconds,
            self.inputs, self.multiply)])
        assert len(initial) == len(data_value)
        # assert False, (initial, data_value)
        return bool(initial != data_value)


def split_seconds(secs, inputs=TimedeltaWidget.INPUTS,
                  multiply=TimedeltaWidget.MULTIPLY):
    ret = []
    for input, multi in zip(inputs, multiply):
        count, secs = divmod(secs, multi)
        ret.append(count)
    return ret
