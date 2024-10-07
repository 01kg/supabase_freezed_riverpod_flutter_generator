import os
from typing import List

from src.classes import Column, SqlEnum
from src.utils import snake_to_title_case




def sqlToView(table_columns: List[Column],  views_directory: str, project_name: str, enums: List[SqlEnum]=[]):
    # if no column named id, return
    if not any(column.column_name.snake == "id" for column in table_columns):
        print("No id column found. Skipping view generation.")
        return

    snake_table_name = table_columns[0].table_name.snake
    camel_table_name = table_columns[0].table_name.camel
    capitalized_camel_table_name = table_columns[0].table_name.cap_camel

    dialog_property_columns: List[Column] = [] # exclude user_id

    build_var_columns: List[Column] = [] # include related tables and enums, exept user_id

    build_controller_columns: List[Column] = [] # exclude id

    text_form_field_columns: List[Column] = [] # exclude id and user_id

    import_provider_columns: List[Column] = [] # include related tables, exclude user_id
    # edit_button_param_columns: List[Column] = []
    # edit_button_param_column_includes = []
    # edit_button_param_column_excludes = [r"id"]

    for column in table_columns:

        related_table_name = column.related_table_name.snake

        if column.related_table_name.snake != "auth.users":
            dialog_property_columns.append(column)
        # dialog_property_columns.append(column if column.related_table_name.snake != "auth.users" else []) 

        if column.is_enum:
            build_var_columns.append(column)

        # filter out columns that are not needed to be the build vars
        if related_table_name and related_table_name != "auth.users":
            build_var_columns.append(column)
            import_provider_columns.append(column)

        # filter out columns that are not needed to be the build controllers
        if not column.is_primary_key and not column.is_foreign_key:
            build_controller_columns.append(column)

        if column.column_name.snake != "id" and related_table_name != "auth.users":
            text_form_field_columns.append(column)


    # construct dialog properties
    dialog_property_lines:List[str] = []
    for column in dialog_property_columns:
        dialog_property_lines.append(
            f"final {column.dart_type}? initial{column.column_name.cap_camel};"
        )
    dialog_properties_str = "\n".join(dialog_property_lines)

    # construct constructor parameters
    constructor_param_columns = dialog_property_columns
    constructor_param_lines:List[str] = []
    for column in constructor_param_columns:
        constructor_param_lines.append(f"this.initial{column.column_name.cap_camel},")
    constructor_params_str = "\n".join(constructor_param_lines)

    # construct build vars
    build_var_lines:List[str] = []
    for column in build_var_columns:
        build_var_lines.append(
            f"{column.dart_type}? current{column.column_name.cap_camel} = initial{column.column_name.cap_camel};"
        )
    build_vars_str = "\n".join(build_var_lines)

    # construct build controllers
    build_controller_lines:List[str] = []
    for column in build_controller_columns:
        if column.dart_type == "String":
            text = f"initial{column.column_name.cap_camel}"
        else:
            text = f"initial{column.column_name.cap_camel}?.toString()"
        build_controller_lines.append(
            f"final TextEditingController {column.column_name.camel}Controller = TextEditingController(text: {text});"
        )
    build_controller_str = "\n".join(build_controller_lines)

    # construct build providers
    build_provider_columns = build_var_columns
    build_provider_lines:List[str] = []
    for column in build_provider_columns:
        snake_related_table_name = column.related_table_name.snake
        if snake_related_table_name:
            camel_related_table_name = column.related_table_name.camel

            build_provider_lines.append(
                f"final {column.column_name.camel}AsyncValue = ref.watch({camel_related_table_name}Provider);"
            )
    build_providers_str = "\n".join(build_provider_lines)

    # construct import providers
    import_provider_lines:List[str] = []
    for column in import_provider_columns:
        if column.is_enum:
            continue
        snake_col_name_without_id = column.column_name.snake[:-3]

        import_provider_lines.append(
            f"import 'package:{project_name}/providers/{column.related_table_name.snake}_provider.dart';"
        )
    import_provider_lines = list(set(import_provider_lines))
    import_providers_str = "\n".join(import_provider_lines)

    # construct TextFormFields for each column
    text_form_field_lines:List[str] = []
    for column in text_form_field_columns:
        snake_col_name_without_id = ""
        camel_related_table_name = ""
        if column.column_name.snake.endswith("_id"):
            snake_col_name_without_id = column.column_name.snake[:-3]
            camel_related_table_name = column.related_table_name.camel

        if column.sql_type == "date":
            text_form_field_lines.append(
                f"""
                TextFormField(
                controller: {column.column_name.camel}Controller,
                decoration: const InputDecoration(labelText: '{snake_to_title_case(column.column_name.snake)}'),
                readOnly: true,
                onTap: () async {{
                    DateTime? pickedDate = await showDatePicker(
                    context: context,
                    initialDate: DateTime.tryParse(initial{column.column_name.cap_camel} ?? "") ??
                        DateTime.now(),
                    firstDate: DateTime(1900),
                    lastDate: DateTime(2200),
                    );
                    if (pickedDate != null) {{
                    {column.column_name.camel}Controller.text = pickedDate.toIso8601String();
                    }}
                }},
                ),
                """
            )
        if column.sql_type == "bigint" and column.column_name.snake.endswith("_id"):
            text_form_field_lines.append(
                f"""
                {column.column_name.camel}AsyncValue.when(
                loading: () => const CircularProgressIndicator(),
                error: (err, stack) => Text('Error: $err'),
                data: (items) => DropdownButtonFormField<int>(
                    decoration: const InputDecoration(labelText: '{snake_to_title_case(snake_col_name_without_id)}'),
                    value: current{column.column_name.cap_camel},
                    onChanged: (int? newValue) {{
                    current{column.column_name.cap_camel} = newValue;
                    }},
                    items: items.map<DropdownMenuItem<int>>((item) {{
                    return DropdownMenuItem<int>(
                        value: item.id,
                        child: const Text('An item'),
                    );
                    }}).toList(),
                    hint: const Text('Select {snake_to_title_case(snake_col_name_without_id)}'),
                ),
                ),
                """
            )

        if column.is_enum:
            enum_values:List[str] = []
            for enum in enums:
                if column.sql_type == enum.enum_name.snake:
                    enum_values = enum.enum_values

            dropdown_items_str = ",\n".join([f"DropdownMenuItem(value: '{enum_value}', child: Text('{enum_value}'))" for enum_value in enum_values])
            text_form_field_lines.append(
                f"""
                DropdownButtonFormField<String>(
                decoration: const InputDecoration(labelText: '{snake_to_title_case(column.column_name.snake)}'),
                value: current{column.column_name.cap_camel},
                onChanged: (String? newValue) {{
                    current{column.column_name.cap_camel} = newValue;
                }},
                items: const [{dropdown_items_str}],
                hint: const Text('Select {snake_to_title_case(column.column_name.snake)}'),
                ),
                """
            )


        if column.sql_type == "text":
            text_form_field_lines.append(
                f"""
                TextFormField(
                controller: {column.column_name.camel}Controller,
                decoration: const InputDecoration(labelText: '{snake_to_title_case(column.column_name.snake)}'),
                keyboardType: TextInputType.multiline,
                minLines: 2,
                maxLines: 8,
                ),
                """
            )
        if column.sql_type == "varchar":
            text_form_field_lines.append(
                f"""
                TextFormField(
                controller: {column.column_name.camel}Controller,
                decoration: const InputDecoration(labelText: '{snake_to_title_case(column.column_name.snake)}'),
                ),
                """
            )
        if (
            column.sql_type == "real"
            or column.sql_type == "double"
            or (column.sql_type == "bigint" and not column.column_name.snake.endswith("_id"))
        ):
            text_form_field_lines.append(
                f"""
                TextFormField(
                controller: {column.column_name.camel}Controller,
                decoration: const InputDecoration(labelText: '{snake_to_title_case(column.column_name.snake)}'),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                ),
                """
            )

    text_form_fields_str = "\n".join(text_form_field_lines)

    # construct dialog on save params
    dialog_on_save_controller_param_columns = table_columns
    dialog_on_save_controller_param_lines:List[str] = []
    for column in dialog_on_save_controller_param_columns:
        try_parse_or_parse = "tryParse" if not column.is_not_null else "parse"

        if column.column_name.snake == "id":
            dialog_on_save_controller_param_lines.append(
                f"{column.column_name.camel}: initial{column.column_name.cap_camel},"
            )
        elif column.related_table_name.snake == "auth.users":
            dialog_on_save_controller_param_lines.append(
                f"{column.column_name.camel}: ref.read({camel_table_name}Provider.notifier).getUserId()!,"
            )
        elif column.dart_type == "String":
            dialog_on_save_controller_param_lines.append(
                f"{column.column_name.camel}: {column.column_name.camel}Controller.text,"
            )
        elif column.dart_type == "int" and not column.column_name.snake.endswith("_id"):
            dialog_on_save_controller_param_lines.append(
                f"{column.column_name.camel}: int.{try_parse_or_parse}({column.column_name.camel}Controller.text),"
            )
        elif column.dart_type == "double":
            dialog_on_save_controller_param_lines.append(
                f"{column.column_name.camel}: double.{try_parse_or_parse}({column.column_name.camel}Controller.text),"
            )
        elif column.column_name.snake.endswith("_id"):
            esclam = "!" if column.is_not_null else ""
            dialog_on_save_controller_param_lines.append(
                f"{column.column_name.camel}: current{column.column_name.cap_camel}{esclam},"
            )

    dialog_on_save_params_str = "\n".join(dialog_on_save_controller_param_lines)

    # construct the edit button params
    edit_button_param_columns = dialog_property_columns
    edit_button_param_lines:List[str]= []
    for column in edit_button_param_columns:
        edit_button_param_lines.append(
            f"initial{column.column_name.cap_camel}: value.{column.column_name.camel},"
        )
    edit_button_params_str = "\n".join(edit_button_param_lines)

    ###############################################
    ###############################################

    dart_class = f"""
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:{project_name}/models/{snake_table_name}_model.dart';
import 'package:{project_name}/providers/{snake_table_name}_provider.dart';

{import_providers_str}




class {capitalized_camel_table_name}View extends ConsumerWidget {{
  static const routeName = '/{snake_table_name}';

  const {capitalized_camel_table_name}View({{super.key}});

  @override
  Widget build(BuildContext context, WidgetRef ref) {{
    final {camel_table_name}AsyncValue = ref.watch({camel_table_name}Provider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('{snake_to_title_case(snake_table_name)}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {{
              // ignore: unused_result
              ref.refresh({camel_table_name}Provider.future);
            }},
          ),
        ],
      ),
      body: {camel_table_name}AsyncValue.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(child: Text('Error: $error')),
        data: (values) {{
          return ListView.builder(
            itemCount: values.length,
            itemBuilder: (context, index) {{
              final value = values[index];
              return ListTile(
                title: const Text("{snake_table_name}"),
                subtitle: const Text("subtitle"),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.edit),
                      onPressed: () async {{
                        await showDialog<bool>(
                          context: context,
                          builder: (BuildContext context) {{
                            return _{capitalized_camel_table_name}Dialog(
                              context: context,
                              {edit_button_params_str}
                            );
                          }},
                        );
                      }},
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete),
                      onPressed: () async {{
                        bool? confirmDelete = await showDialog<bool>(
                          context: context,
                          builder: (BuildContext context) {{
                            return AlertDialog(
                              title: const Text('Confirm Deletion'),
                              content: const Text(
                                  'Are you sure you want to delete this?'),
                              actions: <Widget>[
                                TextButton(
                                  child: const Text('Cancel'),
                                  onPressed: () {{
                                    Navigator.of(context).pop(false);
                                  }},
                                ),
                                TextButton(
                                  child: const Text('Delete'),
                                  onPressed: () {{
                                    Navigator.of(context).pop(true);
                                  }},
                                ),
                              ],
                            );
                          }},
                        );
                        if (confirmDelete == true) {{
                          await ref
                              .read({camel_table_name}Provider.notifier)
                              .delete(value.id);
                        }}
                      }},
                    ),
                  ],
                ),
              );
            }},
          );
        }},
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {{
          await showDialog<bool>(
            context: context,
            builder: (BuildContext context) {{
              return _{capitalized_camel_table_name}Dialog(
                context: context,
              );
            }},
          );
        }},
        child: const Icon(Icons.add),
      ),
    );
  }}
}}



class _{capitalized_camel_table_name}Dialog extends ConsumerWidget {{
  final BuildContext context;
  {dialog_properties_str}

  const _{capitalized_camel_table_name}Dialog({{
    required this.context,
    {constructor_params_str}
  }});

  @override
  Widget build(BuildContext context, WidgetRef ref) {{
    {build_vars_str}

    {build_controller_str}

    {build_providers_str}

    return AlertDialog(
      title: Text(initialId == null
          ? 'Add {snake_to_title_case(snake_table_name)[:-1]}'
          : 'Edit {snake_to_title_case(snake_table_name)[:-1]}'),
      content: SingleChildScrollView(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
        {text_form_fields_str}
        ])),
      actions: <Widget>[
        TextButton(
          child: const Text('Cancel'),
          onPressed: () {{
            Navigator.of(context).pop(false);
          }},
        ),
        TextButton(
          child: const Text('Save'),
          onPressed: () async {{
            await ref
                .read({camel_table_name}Provider.notifier)
                .upsert({capitalized_camel_table_name}Model(
                  {dialog_on_save_params_str}
                ));
            Navigator.of(context).pop(true);
          }},
        ),
      ],
    );
  }}
}}
"""

    output_file = os.path.join(views_directory, f"{snake_table_name}_view.dart")

    # Check if the file exists and delete it if it does
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Deleted existing file: {output_file}")

    with open(output_file, "w") as f:
        f.write(dart_class.strip())
    print(f">> View written to {output_file}")
