from django.core.serializers.json import Deserializer  # noqa, pylint: disable=unused-import
from django.core.serializers.json import Serializer as JsonSerializer


# todo: start removing xmlrpc.serializer classes in favor of this one
# this will likely cause breakages in our API clients (particularly UI)
# which rely on some foreign key fields being present in the result
class Serializer(JsonSerializer):
    def _value_from_field(self, obj, field):
        """
            For models which use django-vinaigrette override the
            defaults and return non-translated values! This helps with
            XmlrpcAPIBaseTest tests which otherwise will serialize
            translated values to JSON and later queries will fail!
        """
        if hasattr(obj, 'untranslated'):
            return obj.untranslated(field.name)

        return super()._value_from_field(obj, field)
