import os
from typing import List
import re
from src.classes import SqlEnum

def sqlEnumsToDartClasses(sql_enums: List[SqlEnum], enums_directory: str):

    for sql_enum in sql_enums:
        # Convert enum name to CamelCase for Dart class name
        cap_camel_enum_name = sql_enum.enum_name.cap_camel
        dart_class_name = cap_camel_enum_name
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
            dart_static_vars.append(f'  static const {dart_class_name} {var_name} = {dart_class_name}._("{value}");')
            var_names.append(var_name)

        dart_static_vars_str = '\n'.join(dart_static_vars)
        # Construct the static list
        # dart_static_list_str = '  static const List<{dart_class_name}> all = [\n' + ',\n'.join(f'    {name}' for name in var_names) + '\n  ];'

        dart_static_list_str = f"""
        static const List<{dart_class_name}> all = [
            {',\n'.join(var_names)}
        ];
        """

        # Construct Dart class
        # dart_class_str = f'class {dart_class_name} {{\n' + '\n'.join(dart_static_vars) + '\n\n' + dart_static_list_str + '\n}'

        dart_class_str = f"""
        class {dart_class_name} {{
        
            final String name;

            const {dart_class_name}._(this.name);

            @override
            String toString() => name;

            {dart_static_vars_str}
            {dart_static_list_str}

            static {dart_class_name} fromJson(String value) {{
                return {dart_class_name}._(value);
            }}

            static String toJson({dart_class_name} {snake_enum_name}) {{
                return {snake_enum_name}.toString();
            }}

            static {dart_class_name} fromString(String value) {{
                return {dart_class_name}.fromJson(value);
            }}


        }}
        """

        

        output_file = os.path.join(enums_directory, f"{snake_enum_name}_class.dart")

        # Check if the file exists and delete it if it does
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"Deleted existing file: {output_file}")

        with open(output_file, "w") as f:
            f.write(dart_class_str.strip())
        print(f">> SQL Enum Dart Class written to {output_file}")
