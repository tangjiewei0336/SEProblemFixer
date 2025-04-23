import os
import json
import javalang
from javalang.tree import MethodDeclaration, FieldDeclaration


def apply_changes(changes_file):
    with open(changes_file, "r") as f:
        changes = json.load(f)

    for op in changes["operations"]:
        file_path = op["file"]

        if op["action"] == "CREATE_FILE":
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write(op["content"])
            print(f"Created file: {file_path}")

        elif op["action"] == "DELETE_FILE":
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")

        elif op["action"] == "UPDATE_CODE":
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                continue

            with open(file_path, "r") as f:
                content = f.read()

            # Parse Java code into AST
            tree = javalang.parse.parse(content)

            modified = False
            new_lines = content.split("\n")

            for change in op["changes"]:
                if change["type"] == "UPDATE_METHOD":
                    # Find the method in AST
                    for path, node in tree.filter(MethodDeclaration):
                        if (
                                node.name == change["method"]
                                and [param.type.name for param in node.parameters] == change["params"]
                                and path[-2].name == change["class"]  # Check enclosing class
                        ):
                            start_line = node.position.line - 1  # 0-based
                            end_line = find_method_end(new_lines, start_line)

                            # Replace the method
                            new_lines[start_line: end_line + 1] = change["new_code"].split("\n")
                            modified = True
                            print(f"Updated method: {change['class']}.{change['method']}")
                            break
                    else:
                        print(f"Method not found: {change['class']}.{change['method']}")

                elif change["type"] == "UPDATE_FIELD":
                    # Find the field in AST
                    for path, node in tree.filter(FieldDeclaration):
                        if (
                                node.declarators[0].name == change["field"]
                                and path[-2].name == change["class"]
                        ):
                            start_line = node.position.line - 1
                            end_line = start_line

                            # Replace the field
                            new_lines[start_line] = change["new_code"]
                            modified = True
                            print(f"Updated field: {change['class']}.{change['field']}")
                            break
                    else:
                        print(f"Field not found: {change['class']}.{change['field']}")

            if modified:
                with open(file_path, "w") as f:
                    f.write("\n".join(new_lines))


def find_method_end(lines, start_line):
    """Find the closing brace of a method (naive approach)"""
    brace_level = 0
    for i in range(start_line, len(lines)):
        brace_level += lines[i].count("{") - lines[i].count("}")
        if brace_level == 0:
            return i
    return start_line  # Fallback


if __name__ == "__main__":
    apply_changes("code_modification_example.json")