import os
import re

from src.utils import capitalize_camel_case, snake_to_camel, snake_to_title_case


class Column:
    def __init__(self, snake_name, camel_name, cap_camel_name, sql_type, dart_type):
        self.snake_name = snake_name
        self.camel_name = camel_name
        self.cap_camel_name = cap_camel_name
        self.sql_type = sql_type
        self.dart_type = dart_type


def filter_columns(
    snake_col_name,
    camel_col_name,
    capitalized_camel_col_name,
    col_type,
    dart_type,
    include_patterns=None,
    exclude_patterns=None,
):
    columns = []

    # Handle empty or null include list
    if not include_patterns:
        include_patterns = [r".*"]  # Match everything if include list is empty or null

    # Handle empty or null exclude list
    if not exclude_patterns:
        exclude_patterns = []  # No exclusions if exclude list is empty or null

    for include_pattern in include_patterns:
        for exclude_pattern in exclude_patterns:
            if re.search(exclude_pattern, snake_col_name):
                break  # Skip this column if it matches any exclude pattern
        else:
            if re.search(include_pattern, snake_col_name):
                columns.append(
                    Column(
                        snake_name=snake_col_name,
                        camel_name=camel_col_name,
                        cap_camel_name=capitalized_camel_col_name,
                        sql_type=col_type,
                        dart_type=dart_type,
                    )
                )
    return columns


def sqlToView(sql: str, views_directory: str, project_name: str):
    # Regex pattern to match CREATE TABLE statements
    create_table_pattern = re.compile(
        r"create table (\w+) \(([\s\S]*?)\);", re.IGNORECASE
    )

    match = create_table_pattern.search(sql)
    if not match:
        return None

    snake_table_name = match.group(1)
    camel_table_name = snake_to_camel(snake_table_name)
    capitalized_camel_table_name = capitalize_camel_case(camel_table_name)

    # print(f"Snake Table Name: {snake_table_name}")
    # print(f"Camel Table Name: {camel_table_name}")
    # print(f"Capitalized Camel Table Name: {capitalized_camel_table_name}")

    # Map SQL types to Dart types
    sql_to_dart_type_mapping = {
        "bigint": "int",
        "date": "String",
        "real": "double",
        "double": "double",
        "text": "String",
        "uuid": "String",
    }

    columns = match.group(2).split(",")

    dialog_property_columns = []
    dialog_property_column_includes = []
    dialog_property_column_excludes = [r"user_id"]

    build_var_columns = []
    build_var_column_includes = [r"_id"]
    build_var_column_excludes = [r"user_id"]

    build_controller_columns = []
    build_controller_column_includes = []
    build_controller_column_excludes = [r"id"]

    text_form_field_columns = []
    text_form_field_column_includes = []
    text_form_field_column_excludes = [r"(?<!_)id", r"user_id"]

    for column in columns:
        column = column.strip()
        snake_col_name, col_type = column.split()[:2]
        col_type = col_type.strip().lower()
        snake_col_name = snake_col_name.strip()

        camel_col_name = snake_to_camel(snake_col_name)
        capitalized_camel_col_name = capitalize_camel_case(camel_col_name)

        dart_type = sql_to_dart_type_mapping.get(col_type, "String")

        # filter out columns that are not needed to be the dialog properties
        # for i in dialog_property_column_excludes:
        #     if i in snake_col_name:
        #         continue
        #     dialog_property_columns.append(
        #         Column(
        #             snake_name=snake_col_name,
        #             camel_name=camel_col_name,
        #             cap_camel_name=capitalized_camel_col_name,
        #             sql_type=col_type,
        #             dart_type=dart_type,
        #         )
        #     )
        dialog_property_columns += filter_columns(
            snake_col_name,
            camel_col_name,
            capitalized_camel_col_name,
            col_type,
            dart_type,
            dialog_property_column_includes,
            dialog_property_column_excludes,
        )

        # filter out columns that are not needed to be the build vars
        build_var_columns += filter_columns(
            snake_col_name,
            camel_col_name,
            capitalized_camel_col_name,
            col_type,
            dart_type,
            build_var_column_includes,
            build_var_column_excludes,
        )

        # filter out columns that are not needed to be the build controllers
        build_controller_columns += filter_columns(
            snake_col_name,
            camel_col_name,
            capitalized_camel_col_name,
            col_type,
            dart_type,
            build_controller_column_includes,
            build_controller_column_excludes,
        )

        # filter out columns that are not needed to be the text form fields
        text_form_field_columns += filter_columns(
            snake_col_name,
            camel_col_name,
            capitalized_camel_col_name,
            col_type,
            dart_type,
            text_form_field_column_includes,
            text_form_field_column_excludes,
        )

    # construct dialog properties
    dialog_property_lines = []
    for column in dialog_property_columns:
        dialog_property_lines.append(
            f"final {column.dart_type}? initial{column.cap_camel_name};"
        )
    dialog_properties_str = "\n".join(dialog_property_lines)

    # construct constructor parameters
    constructor_param_columns = dialog_property_columns
    constructor_param_lines = []
    for column in constructor_param_columns:
        constructor_param_lines.append(f"this.initial{column.cap_camel_name},")
    constructor_params_str = "\n".join(constructor_param_lines)

    # construct build vars
    build_var_lines = []
    for column in build_var_columns:
        build_var_lines.append(
            f"{column.dart_type}? current{column.cap_camel_name} = initial{column.cap_camel_name};"
        )
    build_vars_str = "\n".join(build_var_lines)

    # construct build controllers
    build_controller_lines = []
    for column in build_controller_columns:
        if column.dart_type == "String":
            text = f"initial{column.cap_camel_name}"
        else:
            text = f"initial{column.cap_camel_name}?.toString()"
        build_controller_lines.append(
            f"final TextEditingController {column.camel_name}Controller = TextEditingController(text: {text});"
        )
    build_controller_str = "\n".join(build_controller_lines)

    # construct build providers
    build_provider_columns = build_var_columns
    build_provider_lines = []
    for column in build_provider_columns:
        snake_col_name_withou_id = column.snake_name[:-3]
        camel_col_name_without_id = snake_to_camel(snake_col_name_withou_id)

        build_provider_lines.append(
            f"final {camel_col_name_without_id}sAsyncValue = ref.watch({camel_col_name_without_id}sProvider);"
        )
    build_providers_str = "\n".join(build_provider_lines)

    # construct import providers
    import_provider_columns = build_var_columns
    import_provider_lines = []
    for column in import_provider_columns:
        snake_col_name_withou_id = column.snake_name[:-3]

        import_provider_lines.append(
            f"import 'package:{project_name}/providers/{snake_col_name_withou_id}s_provider.dart';"
        )
    import_providers_str = "\n".join(import_provider_lines)

    # construct TextFormFields for each column
    text_form_field_lines = []
    for column in text_form_field_columns:
        if column.snake_name.endswith("_id"):
            snake_col_name_withou_id = column.snake_name[:-3]
            camel_col_name_without_id = snake_to_camel(snake_col_name_withou_id)

        if column.sql_type == "date":
            text_form_field_lines.append(
                f"""
                TextFormField(
                controller: {column.camel_name}Controller,
                decoration: const InputDecoration(labelText: '{snake_to_title_case(column.snake_name)}'),
                readOnly: true,
                onTap: () async {{
                    DateTime? pickedDate = await showDatePicker(
                    context: context,
                    initialDate: DateTime.tryParse(initialTransactionDate ?? "") ??
                        DateTime.now(),
                    firstDate: DateTime(1900),
                    lastDate: DateTime(2200),
                    );
                    if (pickedDate != null) {{
                    {column.camel_name}Controller.text = pickedDate.toIso8601String();
                    }}
                }},
                ),
                """
            )
        if column.sql_type == "bigint":
            text_form_field_lines.append(
                f"""
                {camel_col_name_without_id}sAsyncValue.when(
                loading: () => const CircularProgressIndicator(),
                error: (err, stack) => Text('Error: $err'),
                data: (items) => DropdownButtonFormField<int>(
                    decoration: const InputDecoration(labelText: '{snake_to_title_case(snake_col_name_withou_id)}'),
                    value: current{column.cap_camel_name},
                    onChanged: (int? newValue) {{
                    current{column.cap_camel_name} = newValue;
                    }},
                    items: items.map<DropdownMenuItem<int>>((item) {{
                    return DropdownMenuItem<int>(
                        value: item.id,
                        child: const Text('An item'),
                    );
                    }}).toList(),
                    hint: const Text('Select {snake_to_title_case(snake_col_name_withou_id)}'),
                ),
                ),
                """
            )
        if column.sql_type == "text":
            text_form_field_lines.append(
                f"""
                TextFormField(
                controller: {column.camel_name}Controller,
                decoration: const InputDecoration(labelText: '{snake_to_title_case(column.snake_name)}'),
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
                controller: {column.camel_name}Controller,
                decoration: const InputDecoration(labelText: '{snake_to_title_case(column.snake_name)}'),
                ),
                """
            )
        if column.sql_type == "real" or column.sql_type == "double":
            text_form_field_lines.append(
                f"""
                TextFormField(
                controller: {column.camel_name}Controller,
                decoration: const InputDecoration(labelText: '{snake_to_title_case(column.snake_name)}'),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                ),
                """
            )

    text_form_fields_str = "\n".join(text_form_field_lines)

    # construct dialog on save params
    dialog_on_save_controller_param_columns = text_form_field_columns
    dialog_on_save_controller_param_lines = []
    for column in dialog_on_save_controller_param_columns:
        if column.dart_type == "String":
            dialog_on_save_controller_param_lines.append(
                f"{column.camel_name}: {column.camel_name}Controller.text,"
            )
        if column.dart_type == "int" and not column.snake_name.endswith("_id"):
            dialog_on_save_controller_param_lines.append(
                f"{column.camel_name}: int.tryParse({column.camel_name}Controller.text),"
            )
        if column.dart_type == "double":
            dialog_on_save_controller_param_lines.append(
                f"{column.camel_name}: double.tryParse({column.camel_name}Controller.text),"
            )
        if column.snake_name.endswith("_id"):
            dialog_on_save_controller_param_lines.append(
                f"{column.camel_name}: current{column.cap_camel_name},"
            )
    dialog_on_save_params_str = "\n".join(dialog_on_save_controller_param_lines)

    # construct the edit button params
    edit_button_param_columns = text_form_field_columns
    edit_button_param_lines = []
    for column in edit_button_param_columns:
        edit_button_param_lines.append(
            f"initial{column.cap_camel_name}: value.{column.camel_name},"
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
                              initialId: value.id,
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
                  id: initialId,
                  {dialog_on_save_params_str}
                  userId:
                      ref.read({camel_table_name}Provider.notifier).getUserId(),
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
    print(f"Model written to {output_file}")
