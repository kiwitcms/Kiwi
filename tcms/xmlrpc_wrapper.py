# Copyright (c) 2023 Alexander Todorov <atodorov@otb.bg>

# B411:blacklist
# CWE: CWE-20 (https://cwe.mitre.org/data/definitions/20.html)
# https://bandit.readthedocs.io/en/1.7.6/blacklists/blacklist_imports.html#b411-import-xmlrpclib
import defusedxml.xmlrpc

defusedxml.xmlrpc.monkey_patch()

__all__ = ("XmlRPCFault",)

XmlRPCFault = defusedxml.xmlrpc.xmlrpc_client.Fault
