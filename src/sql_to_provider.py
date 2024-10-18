import os
from typing import List
from src.classes import Column
from src.sql_to_provider_query import sqlToProviderQuery
from src.conf import DEBUG_PRINT_IN_PROVIDER


def sqlToProvider(table_columns: List[Column], providers_directory: str, project_name: str):


    snake_table_name = table_columns[0].table_name.snake
    camel_table_name = table_columns[0].table_name.camel
    cap_camel_table_name = table_columns[0].table_name.cap_camel

    import_for_debug = "import 'package:flutter/widgets.dart';" if DEBUG_PRINT_IN_PROVIDER else ""
    debug_print = f"debugPrint(\">> {snake_table_name}_provider response[0]:\\n${{(response.isNotEmpty ? response[0] : 'empty')}}\\n\");" if DEBUG_PRINT_IN_PROVIDER else ""

    query_content = sqlToProviderQuery(table_columns=table_columns)

    # Dart provider template
    provider_template = f"""
import 'dart:async';

{import_for_debug}
import 'package:{project_name}/models/{snake_table_name}_model.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

part '{snake_table_name}_provider.g.dart';

final supabase = Supabase.instance.client;

{query_content}

@riverpod
class {cap_camel_table_name} extends _${cap_camel_table_name} {{
  @override
  Future<List<{cap_camel_table_name}Model>> build() async {{
    final response = await supabase.from('{snake_table_name}').select({camel_table_name}Query);
    {debug_print}
    return response.map({cap_camel_table_name}Model.fromJson).toList();
  }}

  String? getUserId() {{
    return supabase.auth.currentUser?.id;
  }}

  Future<void> upsert({cap_camel_table_name}Model type) async {{
    await supabase
        .from('{snake_table_name}')
        .upsert(type.toJson(), onConflict: "id");

    ref.invalidateSelf();
    await future;
  }}

  Future<void> delete(int? id) async {{
    if (id != null) {{
      await supabase.from('{snake_table_name}').delete().eq('id', id);
    }}

    ref.invalidateSelf();
    await future;
  }}
}}
"""

    output_file = os.path.join(providers_directory, f"{snake_table_name}_provider.dart")

    # Check if the file exists and delete it if it does
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Deleted existing file: {output_file}")

    with open(output_file, "w") as f:
        f.write(provider_template.strip())
    print(f">> Provider written to {output_file}")
