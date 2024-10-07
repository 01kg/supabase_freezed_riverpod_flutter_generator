import os
import re
from typing import Any, List

from src.classes import Column, NameVariant, SqlEnum


def snake_to_camel(snake_str: str) -> str:
    if "_" not in snake_str:
        return snake_str
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def capitalize_camel_case(camel_str:str) -> str:
    return camel_str[0].upper() + camel_str[1:]


def snake_to_title_case(snake_str:str) -> str:
    # Split the string by underscores
    words = snake_str.split("_")
    # Capitalize the first letter of each word
    title_case_words = [word.capitalize() for word in words]
    # Join the words with spaces
    title_case_str = " ".join(title_case_words)
    return title_case_str


def extract_last_folder_name(path: str) -> str:
    # Normalize the path to handle different formats
    normalized_path = os.path.normpath(path)
    # Extract the last folder name
    last_folder_name = os.path.basename(normalized_path)
    return last_folder_name


def write_to_file(file_path: str, content: str):
    # Check if the file exists and delete it if it does
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f">> Deleted existing file: {file_path}")

    with open(file_path, "w") as f:
        f.write(content.strip())
    print(f">> Written to {file_path}")


def get_foreign_detail_column_name(snake_column_name: str) -> NameVariant:
    snake_foreign_detail_column_name = snake_column_name + "_detail"
    if snake_column_name.endswith("_id"):
        snake_foreign_detail_column_name = snake_column_name.split("_id")[0]
    return NameVariant(
        snake_name=snake_foreign_detail_column_name,
    )


def parse_table_columns(sql_create_table_statement: str, whole_sql_content: str="", enums: List[SqlEnum]=[]) -> List[Column] | None:
    return_list: List[Column] | None = []
    # Regex pattern to match CREATE TABLE statements
    create_table_pattern = re.compile(
        r"create table (\w+) \(([\s\S]*?)\);", re.IGNORECASE
    )
    match = create_table_pattern.search(sql_create_table_statement)
    if not match:
        return None

    snake_table_name = match.group(1)
    columns = match.group(2).split(",")

    # dbdiagram.io exported postgres SQL file uses an "ALTER TABLE" statement to add foreign keys
    # ALTER TABLE "entries" ADD FOREIGN KEY ("item_id") REFERENCES "items" ("id") ON DELETE CASCADE ON UPDATE CASCADE;
    alter_table_add_foreign_key_pattern = re.compile(
        r'ALTER\s+TABLE\s+\"?(\w+)\"?\s+ADD\s+FOREIGN\s+KEY\s+\(\"?(\w+)\"?\)\s+REFERENCES\s+\"?(\w+\"?\.?\"?\w+)\"?\s+\(\"?(\w+)\"?\)\s?(ON\s+DELETE\s+\w+\s?)?(ON\s+UPDATE\s+\w+\s?)?;', 
        re.IGNORECASE
    )
    alter_table_add_foreign_key_matches:List[Any] = []
    if whole_sql_content:
        whole_sql_content = whole_sql_content.replace('"', "")
        alter_table_add_foreign_key_matches = alter_table_add_foreign_key_pattern.findall(whole_sql_content)

    # Map SQL types to Dart types
    sql_to_dart_type_mapping = {
        "bigint": "int",
        "date": "String",
        "real": "double",
        "double": "double",
        "text": "String",
        "uuid": "String",
    }

    
    for column in columns:
        column = column.strip()
        column_parts = column.split()
        snake_col_name, col_type = column_parts[:2]
        col_type = col_type.strip().lower()
        snake_col_name = snake_col_name.strip()

        snake_related_table_name = ""
        is_foreign_key = False
        if "references" in column_parts:
            snake_related_table_name = column_parts[
                column_parts.index("references") + 1
            ]
            is_foreign_key = True

        is_not_null = "not" in column_parts and "null" in column_parts

        is_primary_key = "primary" in column_parts and "key" in column_parts

        if alter_table_add_foreign_key_matches:
            for alter_table_add_foreign_key_match in alter_table_add_foreign_key_matches:
                if snake_col_name == alter_table_add_foreign_key_match[1] and snake_table_name == alter_table_add_foreign_key_match[0]:
                    snake_related_table_name = alter_table_add_foreign_key_match[2]
                    is_foreign_key = True
                    break

        is_enum = False
        if enums:
            for enum in enums:
                if col_type == enum.enum_name.snake:
                    is_enum = True
                    break

        dart_type = sql_to_dart_type_mapping.get(col_type, "String")

        column_obj = Column(
            table_name=snake_table_name,
            column_name=snake_col_name,
            dart_type=dart_type,
            sql_type=col_type,
            related_table_name=snake_related_table_name,
            is_not_null=is_not_null,
            is_primary_key=is_primary_key,
            is_foreign_key=is_foreign_key,
            is_enum=is_enum,
        )

        return_list.append(column_obj)

    return return_list

def parse_sql_enums(sql_create_enum_statement: str) -> List[SqlEnum]:
    return_list: List[SqlEnum] = []
    # Regex pattern to match CREATE ENUM statements
    create_enum_pattern = re.compile(
        r'CREATE\s+TYPE\s+"?(\w+)"?\s+AS\s+ENUM\s*\(\s*([\s\S]*?)\s*\);', re.IGNORECASE
    )
    matches = create_enum_pattern.findall(sql_create_enum_statement)
    if not matches:
        return []

    for match in matches:
        snake_enum_name = match[0]
        enum_values = match[1].split(",")

        enum_values = [value.strip().replace("'", "") for value in enum_values]

        enum_obj = SqlEnum(
            enum_name=snake_enum_name,
            enum_values=enum_values,
        )

        return_list.append(enum_obj)

    return return_list


def lowercase_sql_keywords(sql_statement: str)->str:
    sql_keywords = [
        "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE", "CREATE", "TABLE", "ALTER", "ADD", "DROP", "COLUMN", "CONSTRAINT", "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "JOIN", "INNER", "LEFT", "RIGHT", "FULL", "OUTER", "ON", "GROUP", "BY", "ORDER", "HAVING", "DISTINCT", "UNION", "ALL", "AND", "OR", "NOT", "NULL", "IS", "IN", "EXISTS", "BETWEEN", "LIKE", "LIMIT", "OFFSET"
    ]

    for keyword in sql_keywords:
        sql_statement = sql_statement.replace(keyword, keyword.lower())
    

    return sql_statement