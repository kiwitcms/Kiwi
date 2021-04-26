# -*- coding: utf-8 -*-
from django.forms import EmailField, ValidationError


class MultipleEmailField(EmailField):
    """Holding mulitple email addresses"""

    delimiter = ","

    default_error_messages = {
        "invalid": u"%(value)s is/are not valid email addresse(s).",
    }

    def to_python(self, value):
        if not value:
            return []

        if not isinstance(value, str):
            raise ValidationError("%s is not a valid string value." % str(value))

        result = []

        for item in value.split(self.delimiter):
            if item.strip() != "":
                result.append(item.strip())

        return result

    def clean(self, value):
        email_addrs = self.to_python(value)
        super_instance = super()

        valid_email_addrs = []
        invalid_email_addrs = []

        self.validate(email_addrs)

        for email_addr in email_addrs:
            try:
                super_instance.run_validators(email_addr)
            except ValidationError:
                invalid_email_addrs.append(email_addr)
            else:
                valid_email_addrs.append(email_addr)

        if invalid_email_addrs:
            raise ValidationError(
                self.error_messages["invalid"]
                % {"value": ", ".join(invalid_email_addrs)}
            )

        return self.delimiter.join(valid_email_addrs)
