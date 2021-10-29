import ast
import os
from typing import Dict, List, Set, Union

import pandas as pd

# loop through files and, for each file (included in 'file_extensions' variable)
# collect number of lines
# collect the number of modules used, and which ones were
# collect number of functions
# collect number of characters
# collect number of classes
# collect number of ifs


# at the end, calculate the sums
# and return the data for the repository in a single row
def get_modules_used(tree: str) -> List[str]:
    """Collect names imported in given file.

    Collect module first name, i.e. `from foo.bar import baz`
    will only add `foo` to the list.
    """

    top_imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                top_imported.add(name.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                # Relative imports always refer to the current package.
                continue
            assert node.module
            top_imported.add(node.module.split(".")[0])
    return list(top_imported)


def collect_file_data(file_path: str) -> Dict[str, Union[List[str], Dict[str, int]]]:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        f.seek(0)
        tree = ast.parse(f.read())

    line_count = len([l for l in lines if len(l)])
    char_count = sum([len(line.strip()) for line in lines])
    function_count = sum([isinstance(line, ast.FunctionDef) for line in ast.walk(tree)])
    ifs_count = sum([isinstance(line, ast.If) for line in ast.walk(tree)])
    class_count = sum([isinstance(line, ast.ClassDef) for line in tree.body])

    modules_list = get_modules_used(tree)
    module_count = len(modules_list)

    return {
        "numbers": {
            "line_count": line_count,
            "module_count": module_count,
            "function_count": function_count,
            "char_count": char_count,
            "ifs_count": ifs_count,
            "class_count": class_count,
        },
        "modules": modules_list,
    }


def is_folder_valid(dirpath: str, excluded_folders: List[str]) -> bool:

    return not any([excluded_f in dirpath for excluded_f in excluded_folders])


def collect_project_data(
    projectpath: str, excluded_folders: List[str]
) -> Dict[str, Union[Dict[str, int], Set[str]]]:

    modules: Set[str] = set()
    numbers_data = {}

    for dirpath, _, filenames in os.walk(projectpath):
        if not is_folder_valid(dirpath + os.sep, excluded_folders):
            # print(f"SKIPPING {dirpath}")
            continue
        available_files = [x for x in filenames if x.split(".")[-1].lower() == "py"]
        for file in available_files:
            print("VISITING ", file, "FROM ", os.path.basename(projectpath))
            file_path = os.path.join(dirpath, file)
            file_data = collect_file_data(file_path)
            for variable, value in file_data["numbers"].items():
                numbers_data.setdefault(variable, 0)
                numbers_data[variable] += value

            modules.update(file_data["modules"])
    return {"numbers": numbers_data, "modules": modules}


def main() -> None:

    projects_absolute_path = input("Input the absolute path of the root folder: ")

    # TODO: CHANGE THIS AS YOUR WILL
    excluded_folders: List[str] = ["venv"]
    excluded_folders = [os.sep + x.lower() + os.sep for x in excluded_folders]
    projects_data = {
        p: collect_project_data(
            os.path.join(projects_absolute_path, p), excluded_folders
        )
        for p in os.listdir(projects_absolute_path)
    }

    rows: List[pd.DataFrame] = []
    for proj_name, proj_data in projects_data.items():
        row = pd.Series(proj_data["numbers"])
        row["project_name"] = proj_name
        row["modules"] = proj_data["modules"]
        rows.append(row.to_frame().T)

    df = pd.concat(rows)
    df.set_index("project_name", inplace=True)
    df.to_excel("results.xlsx")


if __name__ == "__main__":
    main()
