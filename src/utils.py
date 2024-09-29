import os
import re
from typing import List

from src.classes import Column, NameVariant


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
    print(f">> Model written to {file_path}")


def get_foreign_detail_column_name(snake_column_name: str) -> NameVariant:
    snake_foreign_detail_column_name = snake_column_name + "_detail"
    if snake_column_name.endswith("_id"):
        snake_foreign_detail_column_name = snake_column_name.split("_id")[0]
    return NameVariant(
        snake_name=snake_foreign_detail_column_name,
    )


def parse_table_columns(sql_create_table_statement: str) -> List[Column] | None:
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
        if "references" in column_parts:
            snake_related_table_name = column_parts[
                column_parts.index("references") + 1
            ]

        dart_type = sql_to_dart_type_mapping.get(col_type, "String")

        column_obj = Column(
            table_name=snake_table_name,
            column_name=snake_col_name,
            dart_type=dart_type,
            sql_type=col_type,
            related_table_name=snake_related_table_name,
        )

        return_list.append(column_obj)

    return return_list
