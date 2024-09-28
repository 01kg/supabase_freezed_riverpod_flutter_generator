import os


def snake_to_camel(snake_str):
    if "_" not in snake_str:
        return snake_str
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def capitalize_camel_case(camel_str):
    return camel_str[0].upper() + camel_str[1:]


def snake_to_title_case(snake_str):
    # Split the string by underscores
    words = snake_str.split("_")
    # Capitalize the first letter of each word
    title_case_words = [word.capitalize() for word in words]
    # Join the words with spaces
    title_case_str = " ".join(title_case_words)
    return title_case_str


def extract_last_folder_name(path):
    # Normalize the path to handle different formats
    normalized_path = os.path.normpath(path)
    # Extract the last folder name
    last_folder_name = os.path.basename(normalized_path)
    return last_folder_name
