import re

from src.utils import lowercase_sql_keywords

def parse_sql_enum(sql_file_path):
    with open(sql_file_path, 'r') as file:
        sql_content = file.read()

    # Regex to match the enum values
    enum_pattern = re.compile(r"CREATE TYPE \"\w+\" AS ENUM \(([^)]+)\);", re.MULTILINE)
    match = enum_pattern.search(sql_content)
    
    if not match:
        raise ValueError("No ENUM type found in the SQL file.")
    
    # Extract and clean the enum values
    enum_values = match.group(1).split(',')
    enum_values = [value.strip().strip("'") for value in enum_values]
    
    return enum_values

def generate_dart_enum(enum_name, enum_values):
    dart_enum = f"enum {enum_name} {{\n"
    for value in enum_values:
        dart_enum += f"  {value},\n"
    dart_enum += "}\n"
    return dart_enum

def sql_to_enum(whole_sql_content: str):

    create_enum_pattern = re.compile(
        r"CREATE TYPE \"?(\w+)\"? AS ENUM \(([^)]+)\);", re.MULTILINE
    )
    create_enum_statements = create_enum_pattern.findall(whole_sql_content)

    for statement in create_enum_statements:
        statement = lowercase_sql_keywords(statement)
        print(f"\n\n>> create enum statement: \n\n{statement}")
    enum_name = 'Categories'
    
    enum_values = parse_sql_enum(sql_file_path)
    dart_enum = generate_dart_enum(enum_name, enum_values)
    
    with open('categories.dart', 'w') as file:
        file.write(dart_enum)
    
    print(f"Dart enum generated and saved to categories.dart")

if __name__ == "__main__":
    main()