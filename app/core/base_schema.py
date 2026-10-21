"""Modelo Pydantic base de la API.

Convención del contrato JSON:
- Campos de entidades en **camelCase** en el wire (``spaceId``, ``startDate``, ...)
  gracias al ``alias_generator``.
- ``populate_by_name=True``: también se aceptan los nombres snake_case
  (``space_id``, ``start_date``), por lo que clientes antiguos no se rompen.
- ``from_attributes=True``: permite serializar los dataclasses del dominio
  directamente con ``response_model``, sin dicts intermedios.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
