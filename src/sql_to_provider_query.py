import os
from typing import List

from src.classes import Column, NameVariant
from src.utils import get_foreign_detail_column_name, write_to_file


def sqlToProviderQuery(table_columns: List[Column], providers_folder: str):
    snake_table_name = table_columns[0].table_name.snake
    camel_table_name = table_columns[0].table_name.camel

    related_columns = [col for col in table_columns if col.related_table_name.snake and col.column_name.snake != "user_id"]

    related_query_lines:List[str] = []
    for idx, col in enumerate(related_columns):
        snake_foreign_key_name = col.column_name.snake

        foreign_detail_column_name :NameVariant = get_foreign_detail_column_name(snake_foreign_key_name)
        related_query_lines.append(
            f"{foreign_detail_column_name.snake}:{snake_foreign_key_name} ( * ){'' if idx == len(related_columns) - 1 else ','}"
        )
    related_queries_str = "\n".join(related_query_lines)

    content = f"""
const {camel_table_name}Query = '''
*,
{related_queries_str}

''';
"""

    file_path = os.path.join(
        providers_folder, f"{snake_table_name}_provider_query.dart"
    )
    write_to_file(file_path, content)
