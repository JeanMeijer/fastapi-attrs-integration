from typing import Type

import attrs


# https://docs.pydantic.dev/usage/schema/#json-schema-types
class JsonSchemaType:
    def __init__(self, json_type: str, additional: dict | None = None):
        self.additional = additional
        self.json_type = json_type

    def create_field_schema(self) -> dict:
        schema = {
            "type": self.json_type
        }

        if self.additional is not None:
            schema.update(self.additional)

        return schema


class EnumJsonSchemaType(JsonSchemaType):
    def __init__(self, enum: list, json_type: str, additional: dict | None = None):
        super().__init__(json_type, additional)
        self.enum = enum

    def create_field_schema(self) -> dict:
        schema = super().create_field_schema()
        schema["enum"] = self.enum

        return schema


class ArrayJsonSchemaType(JsonSchemaType):
    def __init__(self, items: dict, json_type: str, additional: dict | None = None):
        super().__init__(json_type, additional)
        self.items = items

    def create_field_schema(self) -> dict:
        schema = super().create_field_schema()
        schema["items"] = self.items

        return schema


SCHEMA_FIELD_TYPES = {
    "NoneType": JsonSchemaType("null"),
    "bool": JsonSchemaType("boolean"),
    "str": JsonSchemaType("string"),
    "float": JsonSchemaType("number"),
    "int": JsonSchemaType("integer"),
    "dict": JsonSchemaType("object"),

    "list": JsonSchemaType("array"),
    "tuple": JsonSchemaType("array"),
    "set": JsonSchemaType("array"),
    "frozenset": JsonSchemaType("array"),

    "datetime": JsonSchemaType("string", {"format": "date-time"}),
    "date": JsonSchemaType("string", {"format": "date"}),
    "time": JsonSchemaType("string", {"format": "time"}),
    "timedelta": JsonSchemaType("string", {"format": "duration"}),
}


class Ref:
    name: str
    model: Type[attrs.AttrsInstance]
    mime_type: str
    references = {}

    def __init__(self, model: Type[attrs.AttrsInstance], mime_type):
        self.name = model.__name__
        self.model = model
        self.mime_type = mime_type
        self.ref = f"#/components/schemas/{self.name}"

    # https://swagger.io/docs/specification/data-models/
    def generate_schema(self) -> dict:
        schema = {
            "title": self.name,
            "type": "object",
            "properties": {},
            "required": []
        }

        for attribute in attrs.fields(self.model):
            field = FieldInfo(attribute)

            if field.is_required:
                schema["required"].append(field.name)

            schema["properties"][field.name] = field.schema

            if len(field.references) > 0:
                # for x, y in field.references.items():
                #     print("dssdadsadas")
                #     print(x, y)
                self.references.update(map(lambda x: (x[0], Ref(x[1], self.mime_type)), field.references.items()))

        return schema

    def as_schema_ref(self) -> dict:
        return {
            "content": {
                self.mime_type: {
                    "schema": {
                        "$ref": self.ref
                    }
                }
            }
        }

    def as_schema(self) -> dict:
        return {
            "content": {
                self.mime_type: {
                    "schema": self.generate_schema()
                }
            }
        }


class FieldInfo:
    name: str
    schema = dict
    is_required = bool
    references: dict[str, Type] = {}

    def __init__(self, attribute: attrs.Attribute):
        self.name = attribute.name

        schema = {
            "title": attribute.name.replace("_", " ").title(),
        }

        if attrs.has(attribute.type):
            self.references.update({schema['title']: attribute.type})

            schema.update({"$ref": f"#/components/schemas/{attribute.type.__name__}"})

            # raise NotImplementedError("Nested models are not supported yet")
        else:
            schema_type = self.map_type(attribute.type.__name__)

            schema.update(schema_type.create_field_schema())

        self.schema = schema
        self.is_required = attribute.default is attrs.NOTHING

    def map_type(self, type_name: str) -> JsonSchemaType:
        if type_name in SCHEMA_FIELD_TYPES:
            return SCHEMA_FIELD_TYPES[type_name]

        raise NotImplementedError(f"Type {type_name} is not supported yet")
