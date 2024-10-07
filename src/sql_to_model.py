import os
from typing import List

from src.classes import Column
from src.utils import snake_to_camel


def sqlToModel(table_columns: List[Column], models_directory: str, project_name: str):
    snake_table_name = table_columns[0].table_name.snake


    import_related_model_lines:List[str] = []
    model_attritute_lines: List[str] = []
    for column in table_columns:
        snake_column_name = column.column_name.snake
        camel_column_name = column.column_name.camel
        dart_type = column.dart_type

        question_mark = "?" if not column.is_not_null else ""
        required_mark = "required" if column.is_not_null else ""

        # if snake_column_name not in ["id"] and column.related_table_name.snake:
        #     if MODEL_HAS_DEFAULT_VALUE:
        #         question_mark = ""
        #     if (
        #         col_type.startswith("varchar")
        #         or col_type.startswith("uuid")
        #         or col_type.startswith("text")
        #         or col_type.startswith("date")
        #     ):
        #         default_value_str = f"@Default('No {col_type} provided')"
        #     elif (col_type.startswith("bigint") or col_type.startswith("real") or col_type.startswith("double")):
        #         default_value_str = "@Default(0)"

        json_key = f"@JsonKey(name: '{snake_column_name}')" if "_" in snake_column_name else ""

        model_attritute_lines.append(f"{json_key} {required_mark} {dart_type}{question_mark} {camel_column_name},")

        snake_related_table_name:str = column.related_table_name.snake
        if snake_related_table_name and snake_related_table_name != "auth.users":

            import_related_model = f"import 'package:{project_name}/models/{snake_related_table_name}_model.dart';"
            import_related_model_lines.append(import_related_model)

            if snake_column_name.endswith("_id"):
                snake_related_row_detail_name = snake_column_name.split("_id")[0]
            else:
                snake_related_row_detail_name = snake_column_name + "_detail"
            camel_related_row_detail_name = snake_to_camel(
                snake_related_row_detail_name
            )

            json_key = (
                f"@JsonKey(name: '{snake_related_row_detail_name}')"
                if "_" in snake_column_name
                else ""
            )
            model_attritute_lines.append(
                f"{json_key} {column.related_table_name.cap_camel}Model? {camel_related_row_detail_name},"
            )

        # if is_foreign_key:

    dart_columns_str = "\n".join(model_attritute_lines)
    model_name = (
        "".join([word.capitalize() for word in snake_table_name.split("_")]) + "Model"
    )

    import_related_models_str = "\n".join(import_related_model_lines)

    dart_model = f"""
import 'package:freezed_annotation/freezed_annotation.dart';
{import_related_models_str}

part '{snake_table_name}_model.freezed.dart';
part '{snake_table_name}_model.g.dart';

@freezed
class {model_name} with _${model_name} {{
  @JsonSerializable(includeIfNull: false)
  factory {model_name}({{
{dart_columns_str}
  }}) = _{model_name};

  factory {model_name}.fromJson(Map<String, dynamic> json) =>
      _${model_name}FromJson(json);
}}
"""

    output_file = os.path.join(models_directory, f"{snake_table_name}_model.dart")

    # Check if the file exists and delete it if it does
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Deleted existing file: {output_file}")

    with open(output_file, "w") as f:
        f.write(dart_model.strip())
    print(f">> Model written to {output_file}")
