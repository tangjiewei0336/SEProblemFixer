import os
import json
import javalang
from collections import defaultdict

# === 构建类名和接口名的索引 ===
def build_class_index(root_dir):
    class_index = defaultdict(list)
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith('.java'):
                full_path = os.path.join(dirpath, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    tree = javalang.parse.parse(code)
                    package = tree.package.name if tree.package else ''
                    for type_decl in tree.types:
                        if isinstance(type_decl, (javalang.tree.ClassDeclaration, javalang.tree.InterfaceDeclaration)):
                            fqcn = f"{package}.{type_decl.name}" if package else type_decl.name
                            class_index[type_decl.name].append({
                                "fqcn": fqcn,
                                "file": os.path.relpath(full_path, root_dir),
                                "kind": "interface" if isinstance(type_decl, javalang.tree.InterfaceDeclaration) else "class"
                            })
                except:
                    print(f"跳过 {full_path}: 解析错误")
                    continue
    return class_index

# === 分析单个 Java 文件 ===
def analyze_java_code(code, class_index):
    try:
        tree = javalang.parse.parse(code)
    except:
        return None

    injections = []
    manual_inits = []

    for _, node in tree.filter(javalang.tree.FieldDeclaration):
        for annotation in node.annotations:
            if annotation.name in ['Autowired', 'Inject']:
                for decl in node.declarators:
                    class_name = node.type.name
                    match = class_index.get(class_name, [])
                    injections.append({
                        'type': class_name,
                        'fqcn': match[0]['fqcn'] if match else None,
                        'name': decl.name,
                        'definition_file': match[0]['file'] if match else None,
                        'kind': match[0]['kind'] if match else None
                    })

    for _, node in tree.filter(javalang.tree.VariableDeclarator):
        if isinstance(node.initializer, javalang.tree.ClassCreator):
            class_name = node.initializer.type.name
            match = class_index.get(class_name, [])
            manual_inits.append({
                'type': class_name,
                'fqcn': match[0]['fqcn'] if match else None,
                'name': node.name,
                'definition_file': match[0]['file'] if match else None,
                'kind': match[0]['kind'] if match else None
            })

    return {
        'injections': injections,
        'manual_instantiations': manual_inits
    }

# === Step 3: 分析整个项目 ===
def analyze_project(root_dir):
    class_index = build_class_index(root_dir)
    result = {}
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith('.java'):
                filepath = os.path.join(dirpath, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        code = f.read()
                    analysis = analyze_java_code(code, class_index)
                    if analysis:
                        result[os.path.relpath(filepath, root_dir)] = analysis
                except Exception as e:
                    print(f"跳过 {filepath}: {e}")
    return result

def save_to_json(data, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# === 用法 ===
project_path = '/Users/tangxiaoxia/IdeaProjects/autodrive'  # 替换为实际路径
output_json_path = 'di_with_fqcn_and_interfaces.json'

result = analyze_project(project_path)
save_to_json(result, output_json_path)
print(f'分析完成，结果已保存至 {output_json_path}')
