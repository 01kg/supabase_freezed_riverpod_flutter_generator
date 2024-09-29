import os
import re
from src.conf import DEBUG_PRINT_IN_PROVIDER
from src.utils import capitalize_camel_case, snake_to_camel


def sqlToProvider(sql_statement: str, providers_directory: str, project_name: str):
    # Extract table name using regex
    table_name_match = re.search(r"create table (\w+)", sql_statement, re.IGNORECASE)
    if not table_name_match:
        raise ValueError("Table name not found in SQL statement")

    table_name = table_name_match.group(1)
    camel_case_table_name = snake_to_camel(table_name)
    capitalized_camel_case_table_name = capitalize_camel_case(camel_case_table_name)

    import_for_debug = "import 'package:flutter/widgets.dart';" if DEBUG_PRINT_IN_PROVIDER else ""
    debug_print = f"debugPrint(\">> {table_name}_provider response[0]:\\n${{(response.isNotEmpty ? response[0] : 'empty')}}\\n\");" if DEBUG_PRINT_IN_PROVIDER else ""

    # Dart provider template
    provider_template = f"""
import 'dart:async';

{import_for_debug}
import 'package:{project_name}/models/{table_name}_model.dart';
import 'package:{project_name}/providers/{table_name}_provider_query.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

part '{table_name}_provider.g.dart';

final supabase = Supabase.instance.client;

@riverpod
class {capitalized_camel_case_table_name} extends _${capitalized_camel_case_table_name} {{
  @override
  Future<List<{capitalized_camel_case_table_name}Model>> build() async {{
    final response = await supabase.from('{table_name}').select({camel_case_table_name}Query);
    {debug_print}
    return response.map({capitalized_camel_case_table_name}Model.fromJson).toList();
  }}

  String? getUserId() {{
    return supabase.auth.currentUser?.id;
  }}

  Future<void> upsert({capitalized_camel_case_table_name}Model type) async {{
    await supabase
        .from('{table_name}')
        .upsert(type.toJson(), onConflict: "id");

    ref.invalidateSelf();
    await future;
  }}

  Future<void> delete(int? id) async {{
    if (id != null) {{
      await supabase.from('{table_name}').delete().eq('id', id);
    }}

    ref.invalidateSelf();
    await future;
  }}
}}
"""

    output_file = os.path.join(providers_directory, f"{table_name}_provider.dart")

    # Check if the file exists and delete it if it does
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Deleted existing file: {output_file}")

    with open(output_file, "w") as f:
        f.write(provider_template.strip())
    print(f"Model written to {output_file}")
