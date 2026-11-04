# -*- coding: utf-8 -*-
#
# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

"""Generate static API descriptions (OpenAPI and llms.txt) from the registry."""

# pylint: disable=objects-update-used

import json
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from tcms import __version__
from tcms.rpc.schema import describe_methods

OPENAPI_DESCRIPTION = """
Kiwi TCMS exposes a JSON-RPC 2.0 API at /json-rpc/.

The path keys below identify individual API methods and are not REST routes.
Every operation is a POST to /json-rpc/ with a JSON-RPC envelope. Authentication
is done with Auth.login, which sets a session cookie.

Every operation documents two HTTP headers used for access-log correlation:

- Referer: <Method>@<kiwitcms-host>
- User-Agent: <agent-or-model>/<version>

These headers are metadata only and do not change JSON-RPC semantics.
""".strip()

LLMS_HEADER = """# Kiwi TCMS API

> JSON-RPC 2.0 API for test management.

Transport: POST JSON-RPC requests to `/json-rpc/`.
Authentication: `Auth.login` returns a session cookie.
Query arguments are Django field lookups: `<field>__<lookup>` or `<relation>__<field>__<lookup>`.

## HTTP headers

Set these headers on every request so access logs identify the API method and
the calling agent:

- `Referer: <Method>@<kiwitcms-host>`
- `User-Agent: <agent-or-model>/<version>`

They are metadata only and do not change JSON-RPC semantics.

## Methods
"""


def parameter_schema(method) -> dict:
    schema = {"type": "object", "properties": {}, "required": []}
    for parameter in method.parameters:
        value = dict(parameter.schema)
        value.pop("$defs", None)
        schema["properties"][parameter.name] = value
        if parameter.required:
            schema["required"].append(parameter.name)
    return schema


def render_openapi(methods, base_url="/") -> str:
    components = {}
    paths = {}

    for method in methods:
        params = parameter_schema(method)
        for parameter in method.parameters:
            components.update(parameter.schema.get("$defs", {}))

        paths[f"/json-rpc/{method.name}"] = {
            "post": {
                "operationId": method.name,
                "summary": method.summary,
                "description": method.description,
                "tags": [method.name.split(".", 1)[0]],
                "parameters": [
                    {
                        "name": "Referer",
                        "in": "header",
                        "required": False,
                        "description": (
                            f"Set to '{method.name}@<kiwitcms-host>' so access logs "
                            "identify the API method."
                        ),
                        "schema": {"type": "string"},
                        "example": (f"{method.name}@<kiwitcms-host>"),
                    },
                    {
                        "name": "User-Agent",
                        "in": "header",
                        "required": False,
                        "description": (
                            "Identify the calling agent or model and its version."
                        ),
                        "schema": {"type": "string"},
                        "example": "<agent-or-model>/<version>",
                    },
                ],
                "x-jsonrpc-method": method.name,
                "x-jsonrpc-endpoint": "/json-rpc/",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["jsonrpc", "method", "params"],
                                "properties": {
                                    "jsonrpc": {"const": "2.0"},
                                    "id": {"type": ["integer", "string", "null"]},
                                    "method": {"const": method.name},
                                    "params": params,
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "JSON-RPC 2.0 response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["jsonrpc"],
                                    "properties": {
                                        "jsonrpc": {"const": "2.0"},
                                        "id": {"type": ["integer", "string", "null"]},
                                        "result": {},
                                        "error": {"type": "object"},
                                    },
                                }
                            }
                        },
                    }
                },
            }
        }

    document = {
        "openapi": "3.1.0",
        "info": {
            "title": "Kiwi TCMS API",
            "version": __version__,
            "description": OPENAPI_DESCRIPTION,
        },
        "servers": [{"url": base_url}],
        "paths": paths,
        "components": {"schemas": dict(sorted(components.items()))},
        "x-kiwitcms-http-conventions": {
            "referer": "{method}@{kiwitcms_host}",
            "userAgent": "{agent_or_model}/{version}",
        },
    }
    return json.dumps(document, indent=2, sort_keys=False) + "\n"


def query_keys(parameter) -> list[str]:
    if parameter.schema.get("x-kiwitcms-model") is None:
        return []
    return sorted(parameter.schema.get("properties", {}))


def render_method(method) -> str:
    lines = [f"# {method.name}", "", method.description, "", "## Parameters", ""]

    if not method.parameters:
        lines += ["None.", ""]

    for parameter in method.parameters:
        lines.append(f"### `{parameter.name}`")
        lines.append("")
        if parameter.description:
            lines.append(parameter.description)
            lines.append("")
        lines.append(f"Required: {'yes' if parameter.required else 'no'}")
        lines.append("")
        examples = parameter.schema.get("examples")
        if examples:
            rendered = ", ".join(f"`{json.dumps(example)}`" for example in examples)
            lines.append("Examples: " + rendered)
            lines.append("")
        keys = query_keys(parameter)
        if keys:
            lines.append("Allowed query keys: " + ", ".join(f"`{key}`" for key in keys))
            lines.append("")
        relations = parameter.schema.get("x-kiwitcms-relations")
        if relations:
            lines.append(
                "Relations: "
                + ", ".join(
                    f"`{name}` -> {target}" for name, target in relations.items()
                )
            )
            lines.append("")

    lines += ["## Returns", "", method.return_doc or "See the method description.", ""]
    return "\n".join(lines)


def render_llms_index(methods) -> str:
    lines = [LLMS_HEADER, f"Methods: {len(methods)}", ""]
    for method in methods:
        lines.append(f"- [{method.name}](methods/{method.name}.md): {method.summary}")
    lines.append("")
    return "\n".join(lines)


def render_llms_full(methods) -> str:
    lines = [LLMS_HEADER]
    for method in methods:
        lines.append(render_method(method))
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


class Command(BaseCommand):
    help = "Generate static OpenAPI and llms.txt descriptions of the RPC API"

    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=Path(settings.STATIC_ROOT) / "api",
            help="Output directory (default: <STATIC_ROOT>/api)",
        )

    def handle(self, *args, **options):
        output = Path(options["output"])
        methods = describe_methods()

        methods_dir = output / "methods"
        if methods_dir.exists():
            shutil.rmtree(methods_dir)
        methods_dir.mkdir(parents=True, exist_ok=True)
        output.mkdir(parents=True, exist_ok=True)

        (output / "openapi.json").write_text(render_openapi(methods), encoding="utf-8")
        (output / "llms.txt").write_text(render_llms_index(methods), encoding="utf-8")
        (output / "llms-full.txt").write_text(
            render_llms_full(methods), encoding="utf-8"
        )

        for method in methods:
            (methods_dir / f"{method.name}.md").write_text(
                render_method(method), encoding="utf-8"
            )

        self.stdout.write(f"Generated {len(methods)} methods in {output}")
