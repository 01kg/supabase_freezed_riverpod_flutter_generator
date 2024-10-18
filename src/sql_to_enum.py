import os
from typing import List
import re
from src.classes import SqlEnum

def sqlEnumsToDartClasses(sql_enums: List[SqlEnum], enums_directory: str):

    for sql_enum in sql_enums:
        # Convert enum name to CamelCase for Dart class name
        dart_class_name = sql_enum.enum_name.cap_camel
        snake_enum_name = sql_enum.enum_name.snake

        # Convert enum values to Dart static variables
        dart_static_vars: List[str] = []
        var_names: List[str] = []
        
        for value in sql_enum.enum_values:
            # Split the value into words
            words: List[str] = re.split(r'\W+', value)
            # Convert value to camelCase for Dart variable name
            var_name = ''.join(word.capitalize() for word in words).replace(' ', '')
            var_name = var_name[0].lower() + var_name[1:]
            dart_static_vars.append(f'  static const String {var_name} = "{value}";')
            var_names.append(var_name)

        # Construct the static list
        dart_static_list = '  static const List<String> all = [\n' + ',\n'.join(f'    {name}' for name in var_names) + '\n  ];'

        # Construct Dart class
        dart_class_str = f'class {dart_class_name} {{\n' + '\n'.join(dart_static_vars) + '\n\n' + dart_static_list + '\n}'

        output_file = os.path.join(enums_directory, f"{snake_enum_name}_class.dart")

        # Check if the file exists and delete it if it does
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"Deleted existing file: {output_file}")

        with open(output_file, "w") as f:
            f.write(dart_class_str.strip())
        print(f">> SQL Enum Dart Class written to {output_file}")
