import os
import re
import argparse
from typing import List

from src.sql_to_provider_query import sqlToProviderQuery
from src.classes import Column
from src.sql_to_view import sqlToView
from src.sql_to_model import sqlToModel
from src.sql_to_provider import sqlToProvider

from src.utils import extract_last_folder_name, parse_table_columns


parser = argparse.ArgumentParser(description="Process the FLUTTER_PROJECT_ROOT_PATH.")
parser.add_argument(
    "FLUTTER_PROJECT_ROOT_PATH", type=str, help="The root path of the Flutter project"
)

args = parser.parse_args()

FLUTTER_PROJECT_ROOT_PATH = args.FLUTTER_PROJECT_ROOT_PATH


if not os.path.exists(FLUTTER_PROJECT_ROOT_PATH):
    raise FileNotFoundError(f"Directory not found: {FLUTTER_PROJECT_ROOT_PATH}")

# if in the dir does not find a folder called "lib", and no pub.yaml / pub.yml file then it is not a flutter project, raise an error
if not os.path.exists(os.path.join(FLUTTER_PROJECT_ROOT_PATH, "lib")):
    raise FileNotFoundError(
        f"Directory does not contain a 'lib' folder: {FLUTTER_PROJECT_ROOT_PATH}, maybe it is not a Flutter project."
    )


PROJECT_NAME = extract_last_folder_name(FLUTTER_PROJECT_ROOT_PATH)

sqls_directory = os.path.join(FLUTTER_PROJECT_ROOT_PATH, "lib", "sqls")

if not os.path.exists(sqls_directory):
    raise FileNotFoundError(
        f"Directory not found: {sqls_directory}, please create a 'sqls' folder under 'lib' and add your SQL files."
    )

models_directory = os.path.join(FLUTTER_PROJECT_ROOT_PATH, "lib", "models")
providers_directory = os.path.join(FLUTTER_PROJECT_ROOT_PATH, "lib", "providers")
views_directory = os.path.join(FLUTTER_PROJECT_ROOT_PATH, "lib", "views")

directories = [models_directory, providers_directory, views_directory]

for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
    else:
        print(f"Directory already exists: {directory}")

# Regex pattern to match CREATE TABLE statements
create_table_pattern = re.compile(
    r"(?<!-- )create table \w+ \([\s\S]*?\);", re.IGNORECASE
)

# Loop through each file in the directory
for file in os.listdir(sqls_directory):
    file_path = os.path.join(sqls_directory, file)
    if os.path.isfile(file_path):
        with open(file_path, "r") as f:
            content = f.read()
            # Find all CREATE TABLE statements
            create_table_statements = create_table_pattern.findall(content)
            # Loop through and print each statement
            for statement in create_table_statements:
                print(f"\n\n>> create table statement: \n\n{statement}")
                table_columns: List[Column] = parse_table_columns(statement) or []

                sqlToModel(statement, models_directory, PROJECT_NAME)
                # sqlToProvider(statement, providers_directory, PROJECT_NAME)
                # sqlToProviderQuery(table_columns, providers_directory)
                # sqlToView(statement, views_directory, PROJECT_NAME)
