import os
import re

from src.utils import snake_to_camel


def sqlToModel(sql:str, models_directory:str):
    # Regex pattern to match CREATE TABLE statements
    create_table_pattern = re.compile(r"create table (\w+) \(([\s\S]*?)\);", re.IGNORECASE)

    match = create_table_pattern.search(sql)
    if not match:
        return None

    table_name = match.group(1)
    columns = match.group(2).split(',')

    dart_columns = []
    for column in columns:
        column = column.strip()
        col_name, col_type = column.split()[:2]
        col_name = col_name.strip()
        col_name_in_snake = snake_to_camel(col_name)
        col_type = col_type.strip().lower()

        if col_type.startswith('bigint'):
            dart_type = 'int'
        elif col_type.startswith('varchar') or col_type.startswith('uuid') or col_type.startswith('text') or col_type.startswith('date'):
            dart_type = 'String'
        elif col_type.startswith('real') or col_type.startswith('double'):
            dart_type = 'double'
        # elif col_type.startswith('date'):
        #     dart_type = 'DateTime'
        else:
            dart_type = 'dynamic'

        json_key = f"@JsonKey(name: '{col_name}')" if '_' in col_name else ''
        dart_columns.append(f"    {json_key} {dart_type}? {col_name_in_snake},")

    dart_columns_str = '\n'.join(dart_columns)
    model_name = ''.join([word.capitalize() for word in table_name.split('_')]) + 'Model'

    dart_model = f"""
import 'package:freezed_annotation/freezed_annotation.dart';

part '{table_name}_model.freezed.dart';
part '{table_name}_model.g.dart';

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

    output_file = os.path.join(models_directory, f"{table_name}_model.dart")

    # Check if the file exists and delete it if it does
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Deleted existing file: {output_file}")

    with open(output_file, 'w') as f:
        f.write(dart_model.strip())
    print(f"Model written to {output_file}")
