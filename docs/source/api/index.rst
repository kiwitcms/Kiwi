.. _api:

Kiwi TCMS Python API client
===========================

Client side configuration is documented at https://tcms-api.readthedocs.io.
Server side RPC methods are documented in :mod:`tcms.rpc.api`.

Machine-readable description
----------------------------

Static files are generated at build time by
``manage.py generate_rpc_schema`` and served under
``https://<kiwitcms-host>/static/api/``:

- ``https://<kiwitcms-host>/static/api/llms-full.txt``
- ``https://<kiwitcms-host>/static/api/llms.txt``
- ``https://<kiwitcms-host>/static/api/methods/<Method>.md``
- ``https://<kiwitcms-host>/static/api/openapi.json``

The OpenAPI paths identify individual JSON-RPC methods; they are **NOT** REST
routes. The actual endpoint remains ``/json-rpc/``.
