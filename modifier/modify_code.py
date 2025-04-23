import os
import re
import json
import javalang
from javalang.tree import (
    ClassDeclaration, FieldDeclaration, MethodDeclaration,
    Import, PackageDeclaration, CompilationUnit
)


class JavaCodeModifier:
    def __init__(self, changes_file):
        self.changes_file = changes_file
        self.import_cache = {}

    def apply_changes(self):
        with open(self.changes_file, 'r') as f:
            changes = json.load(f)

        for op in changes["operations"]:
            try:
                if op["action"] == "CREATE_FILE":
                    self._create_file(op)
                elif op["action"] == "DELETE_FILE":
                    self._delete_file(op)
                elif op["action"] == "RENAME_FILE":
                    self._rename_file(op)
                elif op["action"] == "UPDATE_CODE":
                    self._update_code(op)
            except Exception as e:
                print(f"Error processing {op.get('file', 'unknown')}: {str(e)}")

    def _create_file(self, operation):
        os.makedirs(os.path.dirname(operation["file"]), exist_ok=True)
        with open(operation["file"], 'w') as f:
            f.write(operation["content"])
        print(f"Created file: {operation['file']}")

    def _delete_file(self, operation):
        if os.path.exists(operation["file"]):
            os.remove(operation["file"])
            print(f"Deleted file: {operation['file']}")
        else:
            print(f"File not found: {operation['file']}")

    def _rename_file(self, operation):
        if os.path.exists(operation["file"]):
            os.rename(operation["file"], operation["new_path"])
            print(f"Renamed: {operation['file']} -> {operation['new_path']}")
        else:
            print(f"File not found: {operation['file']}")

    def _update_code(self, operation):
        if not os.path.exists(operation["file"]):
            print(f"File not found: {operation['file']}")
            return

        with open(operation["file"], 'r') as f:
            content = f.read()

        try:
            tree = javalang.parse.parse(content)
        except javalang.parser.JavaSyntaxError as e:
            print(f"Syntax error in {operation['file']}: {e}")
            return

        new_lines = content.split('\n')
        modified = False

        for change in operation.get("changes", []):
            try:
                if change["type"] == "ADD_CLASS":
                    modified |= self._add_class(tree, new_lines, change)
                elif change["type"] == "REMOVE_CLASS":
                    modified |= self._remove_class(tree, new_lines, change)
                elif change["type"] == "ADD_FIELD":
                    modified |= self._add_field(tree, new_lines, change)
                elif change["type"] == "REMOVE_FIELD":
                    modified |= self._remove_field(tree, new_lines, change)
                elif change["type"] == "UPDATE_FIELD":
                    modified |= self._update_field(tree, new_lines, change)
                elif change["type"] == "ADD_METHOD":
                    modified |= self._add_method(tree, new_lines, change)
                elif change["type"] == "REMOVE_METHOD":
                    modified |= self._remove_method(tree, new_lines, change)
                elif change["type"] == "UPDATE_METHOD":
                    modified |= self._update_method(tree, new_lines, change)
                elif change["type"] == "ADD_IMPORT":
                    modified |= self._add_import(tree, new_lines, change)
                elif change["type"] == "REMOVE_IMPORT":
                    modified |= self._remove_import(tree, new_lines, change)
            except Exception as e:
                print(f"Error applying {change['type']}: {str(e)}")

        if modified:
            with open(operation["file"], 'w') as f:
                f.write('\n'.join(new_lines))
            print(f"Updated file: {operation['file']}")

    # Implementation of each operation type
    def _add_class(self, tree, lines, change):
        if any(c.name == change["class"] for c in tree.types if isinstance(c, ClassDeclaration)):
            print(f"Class already exists: {change['class']}")
            return False

        package_end = self._find_package_end(tree, lines)
        lines.insert(package_end + 1, change["new_code"])
        return True

    def _remove_class(self, tree, lines, change):
        for class_node in tree.types:
            if isinstance(class_node, ClassDeclaration) and class_node.name == change["class"]:
                start = class_node.position.line - 1
                end = self._find_class_end(lines, start)
                del lines[start:end + 1]
                return True
        print(f"Class not found: {change['class']}")
        return False

    def _add_field(self, tree, lines, change):
        class_node = self._find_class(tree, change["class"])
        if not class_node:
            return False

        for field in class_node.fields:
            if field.declarators[0].name == change.get("field", ""):
                print(f"Field already exists: {change.get('field', '')}")
                return False

        class_start = class_node.position.line - 1
        first_method = next((m for m in class_node.body
                             if isinstance(m, MethodDeclaration)), None)

        insert_pos = first_method.position.line - 2 if first_method else class_start + 1
        lines.insert(insert_pos, "    " + change["new_code"])
        return True

    def _remove_field(self, tree, lines, change):
        class_node = self._find_class(tree, change["class"])
        if not class_node:
            return False

        for field in class_node.fields:
            if field.declarators[0].name == change["field"]:
                start = field.position.line - 1
                end = start
                del lines[start:end + 1]
                return True
        print(f"Field not found: {change['field']}")
        return False

    def _update_field(self, tree, lines, change):
        class_node = self._find_class(tree, change["class"])
        if not class_node:
            return False

        for field in class_node.fields:
            if field.declarators[0].name == change["field"]:
                lines[field.position.line - 1] = "    " + change["new_code"]
                return True
        print(f"Field not found: {change['field']}")
        return False

    def _add_method(self, tree, lines, change):
        class_node = self._find_class(tree, change["class"])
        if not class_node:
            return False

        class_end = self._find_class_end(lines, class_node.position.line - 1)
        lines.insert(class_end - 1, "    " + change["new_code"])
        return True

    def _remove_method(self, tree, lines, change):
        class_node = self._find_class(tree, change["class"])
        if not class_node:
            return False

        for method in class_node.methods:
            if (method.name == change["method"] and
                    [p.type.name for p in method.parameters] == change.get("params", [])):
                start = method.position.line - 1
                end = self._find_method_end(lines, start)
                del lines[start:end + 1]
                return True
        print(f"Method not found: {change['method']}")
        return False

    def _update_method(self, tree, lines, change):
        class_node = self._find_class(tree, change["class"])
        if not class_node:
            return False

        for method in class_node.methods:
            if (method.name == change["method"] and
                    [p.type.name for p in method.parameters] == change.get("params", [])):
                start = method.position.line - 1
                end = self._find_method_end(lines, start)
                new_method_lines = change["new_code"].split('\n')
                lines[start:end + 1] = new_method_lines
                return True
        print(f"Method not found: {change['method']}")
        return False

    def _add_import(self, tree, lines, change):
        import_str = change.get("import", change.get("new_code", ""))
        if any(imp.path == import_str for imp in tree.imports):
            print(f"Import already exists: {import_str}")
            return False

        package_end = self._find_package_end(tree, lines)
        lines.insert(package_end + 1, f"import {import_str};")
        return True

    def _remove_import(self, tree, lines, change):
        import_str = change.get("import", "")
        for imp in tree.imports:
            if imp.path == import_str:
                del lines[imp.position.line - 1]
                return True
        print(f"Import not found: {import_str}")
        return False

    # Helper methods
    def _find_class(self, tree, class_name):
        for type_decl in tree.types:
            if isinstance(type_decl, ClassDeclaration) and type_decl.name == class_name:
                return type_decl
        print(f"Class not found: {class_name}")
        return None

    def _find_package_end(self, tree, lines):
        if tree.package:
            return tree.package.position.line - 1
        return 0

    def _find_class_end(self, lines, start_line):
        brace_level = 0
        for i in range(start_line, len(lines)):
            brace_level += lines[i].count('{') - lines[i].count('}')
            if brace_level == 0:
                return i
        return len(lines) - 1

    def _find_method_end(self, lines, start_line):
        brace_level = 0
        for i in range(start_line, len(lines)):
            brace_level += lines[i].count('{') - lines[i].count('}')
            if brace_level == 0:
                return i
        return len(lines) - 1


if __name__ == "__main__":
    modifier = JavaCodeModifier("code_modification_example.json")
    modifier.apply_changes()