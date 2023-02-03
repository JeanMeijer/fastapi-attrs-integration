from typing import Type

import attrs
from fastapi import FastAPI

from schema.schema_encoder import Ref


class SchemaBase:
    models: dict[Type[attrs.AttrsInstance], Ref] = {}

    def ref(self, model: Type[attrs.AttrsInstance], mime_type: str = "application/json") -> dict:
        ref = Ref(model, mime_type)
        self.models[model] = ref

        if len(ref.references) > 0:
            for model, ref1 in ref.references.items():
                self.models[model] = ref1

        return ref.as_schema_ref()

    def generate_component_schemas(self) -> dict:
        schemas = {}

        for model, ref in self.models.items():
            schemas[model.__name__] = ref.generate_schema()

        return schemas


class RouterSchema(SchemaBase):
    pass


class AppSchema(SchemaBase):
    def include_router_schema(self, router_schema: RouterSchema):
        self.models.update(router_schema.models)

    def add_component_schema(self, app: FastAPI, openapi_schema=None):
        if openapi_schema is None:
            openapi_schema = app.openapi()

        if "components" not in openapi_schema:
            openapi_schema["components"] = {}

        if "schemas" not in openapi_schema["components"]:
            openapi_schema["components"]["schemas"] = {}

        openapi_schema["components"]["schemas"].update(self.generate_component_schemas())

        app.openapi_schema = openapi_schema

        return app.openapi_schema
