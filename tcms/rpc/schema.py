# -*- coding: utf-8 -*-
#
# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

"""Transport-neutral descriptions of the RPC methods.

The registry only knows names, callables and auth predicates.  This module
turns that into JSON-Schema fragments and a list of :class:`MethodDescription`
objects which can be rendered as OpenAPI, llms.txt or MCP tool definitions.
"""

# pylint: disable=avoid-auto-field,objects-update-used,avoid-list-comprehension

import inspect
import json
import re
from dataclasses import dataclass
from types import NoneType
from typing import Annotated, Any, Union, get_args, get_origin, get_type_hints

from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.lookups import In, IsNull, Range, Transform
from modernrpc.exceptions import RPCInvalidRequest
from modernrpc.introspection import DocstringParser, Introspector

from tcms.rpc import registry
from tcms.rpc.annotations import FormValues, ModelQuery
from tcms.rpc.handlers import KiwiTCMSHandlerMixin

FIELD_TYPES = (
    # ---- model fields ----
    (models.AutoField, "integer", None),  # before IntegerField (subclass)
    (models.IntegerField, "integer", None),
    (models.FloatField, "number", None),
    (models.DecimalField, "number", None),
    (models.BooleanField, "boolean", None),
    (models.DateTimeField, "string", "date-time"),  # before DateField (subclass)
    (models.DateField, "string", "date"),
    (models.TimeField, "string", "time"),
    (models.DurationField, "string", None),
    (models.JSONField, "object", None),
    (models.EmailField, "string", "email"),  # before CharField (subclass)
    (models.SlugField, "string", None),  # before CharField (subclass)
    (models.URLField, "string", None),  # before CharField (subclass)
    (models.ImageField, "string", None),  # before FileField (subclass)
    (models.FileField, "string", None),
    (models.TextField, "string", None),
    (models.OneToOneField, "integer", None),  # before ForeignKey (subclass)
    (models.ForeignKey, "integer", None),
    (models.CharField, "string", None),
    # ---- form fields ----
    (forms.IntegerField, "integer", None),
    (forms.FloatField, "number", None),
    (forms.DecimalField, "number", None),
    (forms.BooleanField, "boolean", None),
    (forms.DateTimeField, "string", "date-time"),  # before DateField (subclass)
    (forms.DateField, "string", "date"),
    (forms.TimeField, "string", "time"),
    (forms.EmailField, "string", "email"),  # before CharField (subclass)
    (forms.ModelChoiceField, "integer", None),
    (forms.CharField, "string", None),
)

QUERY_PATTERN = r"^[a-zA-Z_][a-zA-Z0-9_]*(__[a-zA-Z0-9_]+)+$"


def type_property(field) -> dict:
    """JSON Schema type (and format) for a model or form field."""
    json_type, fmt = next(
        (
            (json_type, fmt)
            for field_type, json_type, fmt in FIELD_TYPES
            if isinstance(field, field_type)
        ),
        ("string", None),
    )
    prop = {"type": json_type}
    if fmt:
        prop["format"] = fmt
    return prop


def field_property(field) -> dict:
    """JSON Schema for a single model or form field."""
    prop = type_property(field)
    if field.choices:
        prop["enum"] = [str(value) for value, _label in field.choices]
    if field.help_text:
        prop["description"] = str(field.help_text)
    return prop


def lookup_property(field, lookup) -> dict:
    """JSON Schema for one lookup or transform registered on `field`."""
    if issubclass(lookup, In):
        return {"type": "array", "items": type_property(field)}
    if issubclass(lookup, Range):
        return {
            "type": "array",
            "items": type_property(field),
            "minItems": 2,
            "maxItems": 2,
        }
    if issubclass(lookup, IsNull):
        return {"type": "boolean"}
    if issubclass(lookup, Transform):
        return type_property(lookup.output_field)
    return type_property(field)


def field_lookup_properties(field, prefix: str) -> dict:
    props = {prefix: field_property(field)}
    for name, lookup in sorted(field.get_lookups().items()):
        props[f"{prefix}__{name}"] = lookup_property(field, lookup)
    return props


def relations(model):
    return [
        field
        for field in model._meta.get_fields()
        if isinstance(field, (models.ForeignKey, models.OneToOneField))
        and not field.auto_created
    ]


def definition_name(model) -> str:
    return f"{model._meta.app_label}.{model.__name__}Lookup"


def reachable_models(model, depth: int | None = None):
    seen = []
    queue = [(model, 0)]
    while queue:
        current, level = queue.pop(0)
        if current in seen:
            continue
        if depth is not None and level > depth:
            continue
        seen.append(current)
        for field in relations(current):
            queue.append((field.related_model, level + 1))
    return seen


def allowed_properties(props: dict, method_name: str, prefix: str = "") -> dict:
    return {
        key: value
        for key, value in props.items()
        if example_is_valid({f"{prefix}{key}": "..."}, method_name)
    }


def one_hop_properties(model, method_name: str, prefix: str = "") -> dict:
    props = {}
    for field in model._meta.concrete_fields:
        props.update(field_lookup_properties(field, field.name))

    props["pk"] = {"type": "integer", "description": "primary key"}
    for field in relations(model):
        target = field.related_model
        props[field.name] = {
            **props[field.name],
            "description": f"{target._meta.label} pk; append '__<field>' to filter through it",
            "x-kiwitcms-ref": definition_name(target),
        }
    return allowed_properties(props, method_name, prefix)


PREFERRED_TEXT_FIELDS = ("name", "summary", "title", "username", "value")


def first_field(model, field_types):
    return next(
        (
            field
            for field in model._meta.concrete_fields
            if isinstance(field, field_types)
        ),
        None,
    )


def text_fields(model):
    """Text fields, with the human-friendly names first."""
    fields = [
        field
        for field in model._meta.concrete_fields
        if isinstance(field, (models.CharField, models.TextField))
    ]
    fields.sort(key=lambda field: field.name not in PREFERRED_TEXT_FIELDS)
    return fields


def example_is_valid(example: dict, method_name: str) -> bool:
    """Reject examples which inspect_rpc_args() would refuse."""
    try:
        KiwiTCMSHandlerMixin.inspect_rpc_args(method_name, [example])
    except RPCInvalidRequest:
        return False
    return True


# pylint: disable-next=too-many-branches
def query_examples(model, method_name: str) -> list[dict]:
    """Illustrative queries for every field kind present on the model."""
    examples = [{}]

    for field in text_fields(model):
        candidates = [
            {f"{field.name}__icontains": "..."},
            {f"{field.name}__in": ["...", "..."]},
        ]
        if all(example_is_valid(example, method_name) for example in candidates):
            examples.extend(candidates)
            break

    number = first_field(
        model, (models.IntegerField, models.FloatField, models.DecimalField)
    )
    if number is not None:
        for example in (
            {f"{number.name}__in": [1, 2, 3]},
            {f"{number.name}__range": [1, 10]},
        ):
            if example_is_valid(example, method_name):
                examples.append(example)

    boolean = first_field(model, (models.BooleanField,))
    if boolean is not None:
        for example in (
            {boolean.name: True},
            {f"{boolean.name}__isnull": False},
        ):
            if example_is_valid(example, method_name):
                examples.append(example)

    temporal = first_field(
        model, (models.DateTimeField, models.DateField, models.TimeField)
    )
    if temporal is not None:
        if isinstance(temporal, models.DateTimeField):
            value = "2026-01-01T00:00:00"
        elif isinstance(temporal, models.DateField):
            value = "2026-01-01"
        else:
            value = "12:00:00"

        candidates = [{f"{temporal.name}__gte": value}]
        if isinstance(temporal, models.DateField):
            candidates.append({f"{temporal.name}__year": 2026})
        else:
            candidates.append({f"{temporal.name}__hour": 12})
        examples.extend(
            example for example in candidates if example_is_valid(example, method_name)
        )

    found = False
    for relation in relations(model):
        for target in text_fields(relation.related_model):
            candidates = [
                {f"{relation.name}__{target.name}": "..."},
                {f"{relation.name}__{target.name}__icontains": "..."},
            ]
            if all(example_is_valid(example, method_name) for example in candidates):
                examples.extend(candidates)
                found = True
                break
        if found:
            break

    return examples


def query_schema(marker: ModelQuery, method_name: str) -> dict:
    model = marker.model
    definitions = {
        definition_name(item): {
            "type": "object",
            "properties": one_hop_properties(item, method_name, "relation__"),
            "additionalProperties": True,
        }
        for item in reachable_models(model, marker.depth)
    }
    examples = query_examples(model, method_name)

    return {
        "type": "object",
        "description": (
            "Django field lookups. Pass {} to return every object. "
            "Keys are <field>__<lookup> or <relation>__<field>__<lookup>; "
            "__in takes an array, __isnull a boolean. "
            "Examples: " + ", ".join(json.dumps(example) for example in examples) + "."
        ),
        "examples": examples,
        "additionalProperties": True,
        "patternProperties": {
            QUERY_PATTERN: {"description": "field__...__lookup path"}
        },
        "properties": one_hop_properties(model, method_name),
        "x-kiwitcms-model": model._meta.label,
        "x-kiwitcms-relations": {
            field.name: field.related_model._meta.label
            for field in relations(model)
            if example_is_valid({field.name: "..."}, method_name)
        },
        "$defs": definitions,
    }


def form_field_schema(field) -> dict:
    if isinstance(field, forms.ModelMultipleChoiceField):
        return {"type": "array", "items": {"type": "integer"}}

    if isinstance(field, forms.MultipleChoiceField):
        prop = {"type": "array", "items": {"type": "string"}}
        if field.choices:
            prop["items"]["enum"] = [str(value) for value, _label in field.choices]
        return prop

    prop = type_property(field)

    if isinstance(field, forms.ModelChoiceField):
        model = getattr(field.queryset, "model", None)
        if model is not None:
            prop["description"] = f"{model._meta.label} primary key"
    elif isinstance(field, forms.ChoiceField) and field.choices:
        prop["enum"] = [str(value) for value, _label in field.choices]

    return prop


def form_instance(form_class):
    """Instantiate a form so __init__-time changes (e.g. update forms) apply."""
    try:
        return form_class()
    except TypeError:
        return form_class(data={})


def first_choice(field):
    choices = field.choices
    if callable(choices):
        choices = choices()
    choices = list(choices)
    return str(choices[0][0]) if choices else "..."


def form_placeholder(field):
    result = "..."
    if isinstance(field, forms.ModelMultipleChoiceField):
        result = [1]
    elif isinstance(field, forms.ModelChoiceField):
        result = 1
    elif isinstance(field, forms.MultipleChoiceField):
        choices = field.choices
        if callable(choices):
            choices = choices()
        choices = list(choices)
        result = [str(choices[0][0])] if choices else ["..."]
    elif isinstance(field, forms.BooleanField):
        result = True
    elif isinstance(field, forms.IntegerField):
        result = 1
    elif isinstance(field, (forms.FloatField, forms.DecimalField)):
        result = 1.0
    elif isinstance(field, forms.DateTimeField):
        result = "2026-01-01T00:00:00"
    elif isinstance(field, forms.DateField):
        result = "2026-01-01"
    elif isinstance(field, forms.TimeField):
        result = "12:00:00"
    elif isinstance(field, forms.EmailField):
        result = "user@example.com"
    elif isinstance(field, forms.ChoiceField):
        result = first_choice(field)
    return result


def form_examples(form_class) -> list[dict]:
    fields = form_instance(form_class).fields
    required = {
        name: form_placeholder(field)
        for name, field in fields.items()
        if field.required
    }

    examples = []
    if required:
        examples.append(required)
        optional = [
            (name, form_placeholder(field))
            for name, field in fields.items()
            if not field.required
        ]
        if optional:
            sample = dict(required)
            sample.update(dict(optional[:2]))
            examples.append(sample)
    else:
        sample = {
            name: form_placeholder(field) for name, field in list(fields.items())[:2]
        }
        if sample:
            examples.append(sample)

    return examples


def form_schema(marker: FormValues) -> dict:
    form_class = marker.form
    instance = form_instance(form_class)
    model = getattr(getattr(form_class, "_meta", None), "model", None)
    properties = {}
    required = []

    for name, field in instance.fields.items():
        model_field = None
        if model is not None:
            try:
                model_field = model._meta.get_field(name)
            except FieldDoesNotExist:
                model_field = None

        prop = (
            field_property(model_field)
            if model_field is not None
            else form_field_schema(field)
        )
        if field.help_text:
            prop.setdefault("description", str(field.help_text))
        elif field.label:
            prop.setdefault("description", str(field.label))
        if field.required:
            required.append(name)
        properties[name] = prop

    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "examples": form_examples(form_class),
        "additionalProperties": True,
        "x-kiwitcms-form": form_class.__name__,
    }


def hint_schema(hint) -> dict:
    result = {}
    if hint is None or hint is Any:
        result = {}
    elif get_origin(hint) is Union:
        args = [item for item in get_args(hint) if item is not NoneType]
        if len(args) == 1:
            result = hint_schema(args[0])
    elif get_origin(hint) is list:
        args = get_args(hint)
        result = {"type": "array", "items": hint_schema(args[0]) if args else {}}
    elif get_origin(hint) is tuple:
        result = {"type": "array"}
    elif get_origin(hint) is dict:
        result = {"type": "object"}
    elif hint is int:
        result = {"type": "integer"}
    elif hint is float:
        result = {"type": "number"}
    elif hint is bool:
        result = {"type": "boolean"}
    elif hint is str:
        result = {"type": "string"}
    return result


DOC_TYPES = {
    "str": {"type": "string"},
    "int": {"type": "integer"},
    "float": {"type": "number"},
    "bool": {"type": "boolean"},
    "list": {"type": "array"},
    "tuple": {"type": "array"},
    "set": {"type": "array"},
    "dict": {"type": "object"},
    "list(dict)": {"type": "array"},
    "list(str)": {"type": "array", "items": {"type": "string"}},
}


def marker_of(hint):
    if hint is None:
        return None
    if get_origin(hint) is Union:
        args = [item for item in get_args(hint) if item is not NoneType]
        if len(args) != 1:
            return None
        hint = args[0]
    if get_origin(hint) is Annotated:
        return get_args(hint)[1]
    return None


FUNCTION_DIRECTIVE = re.compile(r"^\s*\.\. function::.*$", re.MULTILINE)
EXAMPLE_DIRECTIVE = re.compile(r"^\s*(?:Example|Examples|Usage)::\s*$", re.MULTILINE)


def clean_description(text: str) -> str:
    text = FUNCTION_DIRECTIVE.sub("", text)

    lines = text.splitlines()
    result = []
    skipping = False
    for line in lines:
        if EXAMPLE_DIRECTIVE.match(line):
            skipping = True
            continue
        if skipping:
            if line.startswith(".. ") or (line.strip() and not line.startswith(" ")):
                skipping = False
            else:
                continue
        result.append(line)

    text = "\n".join(result)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


@dataclass(frozen=True)
class Parameter:
    name: str
    schema: dict
    required: bool
    description: str


@dataclass(frozen=True)
class MethodDescription:
    name: str
    summary: str
    description: str
    parameters: tuple[Parameter, ...]
    return_doc: str


# pylint: disable-next=too-many-locals
def describe_methods() -> tuple[MethodDescription, ...]:
    """Return a transport-neutral description of every registered RPC method."""
    result = []

    for name, method in sorted(registry.REGISTRY.items()):
        introspector = Introspector(method.func)
        parser = DocstringParser(method.func)
        signature = introspector.signature
        hints = get_type_hints(method.func, include_extras=True)
        parameters = []

        for argument in signature.parameters:
            if argument == method.context_target:
                continue

            hint = hints.get(argument)
            doc_type = parser.args_types.get(argument, "")
            docstring = parser.args_docstrings.get(argument, "")

            marker = marker_of(hint)
            if isinstance(marker, ModelQuery):
                schema = query_schema(marker, name)
            elif isinstance(marker, FormValues):
                schema = form_schema(marker)
            else:
                schema = hint_schema(hint) or DOC_TYPES.get(doc_type, {})

            if docstring:
                schema.setdefault("description", docstring)

            parameters.append(
                Parameter(
                    name=argument,
                    schema=schema,
                    required=signature.parameters[argument].default
                    is inspect.Parameter.empty,
                    description=docstring,
                )
            )

        description = clean_description(parser.docstring)
        summary = (
            description.splitlines()[0].strip()
            if description
            else name.replace(".", " ")
        )

        result.append(
            MethodDescription(
                name=name,
                summary=summary,
                description=description,
                parameters=tuple(parameters),
                return_doc=parser.return_doc,
            )
        )

    return tuple(result)
