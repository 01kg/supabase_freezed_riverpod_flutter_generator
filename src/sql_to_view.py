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

    import_sql_enums_dart_classes_columns: List[SqlEnum] = [] # include enums


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

        if column.is_enum:
            matching_enum = next((enum for enum in enums if column.sql_type == enum.enum_name.snake), None)
            if matching_enum:
                import_sql_enums_dart_classes_columns.append(matching_enum)


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

    # construct import sql enums dart classes
    import_sql_enums_dart_classes_lines:List[str] = []
    for enum in import_sql_enums_dart_classes_columns:
        import_sql_enums_dart_classes_lines.append(
            f"import 'package:{project_name}/sql_enums_dart_classes/{enum.enum_name.snake}_class.dart';"
        )
    # Remove duplicates
    import_sql_enums_dart_classes_lines = list(set(import_sql_enums_dart_classes_lines))
    import_sql_enums_dart_classes_str = "\n".join(import_sql_enums_dart_classes_lines)

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
            matching_enum = next((enum for enum in enums if column.sql_type == enum.enum_name.snake), None)

            if matching_enum:
              text_form_field_lines.append(
                  f"""
                  DropdownButtonFormField<String>(
                  decoration: const InputDecoration(labelText: '{snake_to_title_case(column.column_name.snake)}'),
                  value: current{column.column_name.cap_camel},
                  onChanged: (String? newValue) {{
                      current{column.column_name.cap_camel} = newValue;
                  }},
                  items: {matching_enum.enum_name.cap_camel}.all.map(({matching_enum.enum_name.camel}) {{
                    return DropdownMenuItem(
                      value: {matching_enum.enum_name.camel}.toString(),
                      child: Text({matching_enum.enum_name.camel}.toString()),
                    );
                  }}).toList(),
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
        elif column.is_enum:
            matching_enum = next((enum for enum in enums if column.sql_type == enum.enum_name.snake), None)
            if matching_enum:
                dialog_on_save_controller_param_lines.append(
                    f"{column.column_name.camel}: {matching_enum.enum_name.cap_camel}.fromString({column.column_name.camel}Controller.text),"
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
            f"initial{column.column_name.cap_camel}: value.{column.column_name.camel}{'.toString()' if column.is_enum else ''},"
        )
    edit_button_params_str = "\n".join(edit_button_param_lines)

    ###############################################
    ###############################################

    dart_class = f"""
    import 'package:flutter/material.dart';
    import 'package:flutter_hooks/flutter_hooks.dart';
    import 'package:hooks_riverpod/hooks_riverpod.dart';
    import 'package:{project_name}/models/{snake_table_name}_model.dart';
    import 'package:{project_name}/providers/{snake_table_name}_provider.dart';
    
    {import_providers_str}
    
    {import_sql_enums_dart_classes_str}
    
    class {capitalized_camel_table_name}View extends HookConsumerWidget {{
      static const routeName = '/{snake_table_name}';
    
      const {capitalized_camel_table_name}View({{super.key}});
    
      @override
      Widget build(BuildContext context, WidgetRef ref) {{
        final {camel_table_name}AsyncValue = ref.watch({camel_table_name}Provider);
        final {camel_table_name} = useState<List<{capitalized_camel_table_name}Model>>([]);
    
        useEffect(() {{
          {camel_table_name}.value = {camel_table_name}AsyncValue.maybeWhen(
            data: (values) => values,
            orElse: () => [],
          );
          return null;
        }}, [{camel_table_name}AsyncValue]);
    
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
              return ListView.separated(
                separatorBuilder: (context, index) => const Divider(),
                itemCount: {camel_table_name}.value.length + 1,
                itemBuilder: (context, index) {{
                  if (index == {camel_table_name}.value.length) {{
                    return const SizedBox(
                        height: 70, child: Center(child: Text('The End')));
                  }}
                  final value = {camel_table_name}.value[index];
                  return Dismissible(
                    key: Key(value.id.toString()),
                    direction: DismissDirection.endToStart,
                    background: Container(
                      color: Colors.red,
                      alignment: Alignment.centerRight,
                      padding: const EdgeInsets.symmetric(horizontal: 20.0),
                      child: const Icon(Icons.delete, color: Colors.white),
                    ),
                    confirmDismiss: (direction) async {{
                      bool? confirmDelete = await showDialog<bool>(
                        context: context,
                        builder: (BuildContext context) {{
                          return AlertDialog(
                            title: const Text('Confirm Deletion'),
                            content: const Text('Are you sure you want to delete this?'),
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
                      return confirmDelete;
                    }},
                    onDismissed: (direction) async {{
                      {camel_table_name}.value = List.from({camel_table_name}.value)..removeAt(index);
                      await ref.read({camel_table_name}Provider.notifier).delete(value.id);
                    }},
                    child: ListTile(
                      title: const Text("{snake_table_name}"),
                      subtitle: const Text("subtitle"),
                      onTap: () async {{
                        await showModalBottomSheet<bool>(
                          isScrollControlled: true,
                          context: context,
                          builder: (BuildContext context) {{
                            return _{capitalized_camel_table_name}Modal(
                              context: context,
                              {edit_button_params_str}
                            );
                          }},
                        );
                      }},
                    ),
                  );
                }},
              );
            }},
          ),
          floatingActionButton: FloatingActionButton(
            onPressed: () async {{
              await showModalBottomSheet<bool>(
                isScrollControlled: true,
                context: context,
                builder: (BuildContext context) {{
                  return _{capitalized_camel_table_name}Modal(
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
    
    class _{capitalized_camel_table_name}Modal extends ConsumerWidget {{
      final BuildContext context;
      {dialog_properties_str}
    
      const _{capitalized_camel_table_name}Modal({{
        required this.context,
        {constructor_params_str}
      }});
    
      @override
      Widget build(BuildContext context, WidgetRef ref) {{
        final isEdit = initialId != null;
        {build_vars_str}
    
        {build_controller_str}
    
        {build_providers_str}
    
        return Padding(
          padding: const EdgeInsets.all(16.0),
          child: FractionallySizedBox(
            heightFactor: 0.9,
            child: Column(
              children: [
                Text(isEdit ? 'Edit' : 'Add', style: Theme.of(context).textTheme.titleLarge),
                SizedBox(height: 8),
                Expanded(
                  child: SingleChildScrollView(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        {text_form_fields_str}
                      ],
                    ),
                  ),
                ),
                SizedBox(height: 16),
                Row(
                  children: [
                    TextButton(
                      child: const Text('Cancel'),
                      onPressed: () {{
                        Navigator.of(context).pop(false);
                      }},
                    ),
                    TextButton(
                      child: const Text('Save'),
                      onPressed: () async {{
                        await ref.read({camel_table_name}Provider.notifier).upsert(
                          {capitalized_camel_table_name}Model(
                            {dialog_on_save_params_str}
                          )
                        );
                        Navigator.of(context).pop(true);
                      }},
                    ),
                  ],
                ),
                SizedBox(height: 16),
              ],
            ),
          ),
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
