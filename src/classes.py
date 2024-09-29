
class NameVariant:
    def __init__(self, snake_name: str):
        self.snake: str = snake_name
        self.camel: str = self.snake_to_camel(snake_name)
        self.cap_camel: str = self.capitalize_camel_case(self.camel)

    @staticmethod
    def snake_to_camel(snake_str: str) -> str:
        if "_" not in snake_str:
            return snake_str
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    @staticmethod
    def capitalize_camel_case(camel_str: str) -> str:
        if not camel_str:
            return ""
        return camel_str[0].upper() + camel_str[1:]


class Column:
    def __init__(
        self,
        table_name: str,
        column_name: str,
        sql_type: str,
        dart_type: str,
        related_table_name: str = "",
    ):
        self.table_name: NameVariant = NameVariant(table_name)
        self.column_name: NameVariant = NameVariant(column_name)
        self.sql_type = sql_type
        self.dart_type = dart_type
        self.related_table_name: NameVariant = (
            NameVariant(related_table_name)
        )


