# -*- coding: utf-8 -*-
#
# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from dataclasses import dataclass

from django.db.models import Model


@dataclass(frozen=True)
class ModelQuery:
    """Annotation for RPC arguments which are Django field lookups.

    ``model`` is the model whose fields the query is applied to. ``depth``
    is reserved for consumers which expand related models; ``None`` means
    follow relations to their full depth, without repeating a model.
    """

    model: type[Model]
    depth: int | None = None
