# di_analyzer.py - 依赖注入分析模块
import os
import re
import json
from typing import Dict, List


class DependencyContext:
    """依赖注入上下文分析器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.bean_cache = {}  # 缓存已识别的Bean
        self.class_cache = {}  # 缓存类信息
        self.package_cache = {}  # 缓存包名到类的映射
        self.bean_annotations = [
            "Service",
            "Component",
            "Repository",
            "Controller",
            "RestController",
            "Configuration",
            "DubboService",
        ]
        self.injection_annotations = [
            "Autowired",
            "Resource",
            "Inject",
            "DubboReference",
        ]
        self._init_project_scan()

    def _init_project_scan(self):
        """初始化扫描项目，建立基本索引"""
        print(f"初始化扫描项目: {self.project_root}")
        java_files = self._find_java_files(self.project_root)

        # 第一遍扫描：建立类名索引和Bean索引
        for file_path in java_files:
            self._scan_class_info(file_path)

        print(
            f"项目扫描完成，找到 {len(self.class_cache)} 个类，其中 {len(self.bean_cache)} 个Bean"
        )

    def _find_java_files(self, dir_path: str) -> List[str]:
        """查找目录中的所有Java文件"""
        java_files = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".java"):
                    java_files.append(os.path.join(root, file))
        return java_files

    def _scan_class_info(self, file_path: str) -> None:
        """扫描类信息，建立索引"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取包名
            package_match = re.search(r"package\s+([\w.]+);", content)
            package_name = package_match.group(1) if package_match else ""

            # 提取类名
            class_matches = re.finditer(
                r"(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)",
                content,
            )
            for class_match in class_matches:
                simple_name = class_match.group(1)
                full_name = f"{package_name}.{simple_name}"

                # 记录类信息
                self.class_cache[full_name] = {
                    "file_path": file_path,
                    "package": package_name,
                    "simple_name": simple_name,
                }

                # 包名索引
                if package_name not in self.package_cache:
                    self.package_cache[package_name] = set()
                self.package_cache[package_name].add(full_name)

                # 检查是否为Bean
                class_annotations = self._extract_annotations(
                    content, class_match.start()
                )
                is_bean = any(
                    anno in self.bean_annotations for anno in class_annotations
                )

                if is_bean:
                    self.bean_cache[full_name] = {
                        "type": ",".join(class_annotations),
                        "file_path": file_path,
                    }

        except Exception as e:
            print(f"扫描文件 {file_path} 时出错: {e}")

    def _extract_annotations(self, content: str, start_pos: int) -> List[str]:
        """提取类注解"""
        search_area = content[max(0, start_pos - 2000) : start_pos]
        annotations = []

        for match in re.finditer(r"@(\w+)(?:\([^)]*\))?", search_area):
            annotations.append(match.group(1))

        return annotations

    def _resolve_type_name(
        self, type_name: str, current_package: str, imports: List[str]
    ) -> str:
        """解析类型的完整名称"""
        # 如果已经是完整类名
        if "." in type_name:
            return type_name

        # 移除泛型部分
        base_type = re.sub(r"<.*>", "", type_name)

        # 在导入中查找
        for imp in imports:
            if imp.endswith("." + base_type):
                return imp

        # 假设同包
        potential_full_name = f"{current_package}.{base_type}"
        if potential_full_name in self.class_cache:
            return potential_full_name

        # 在java.lang包中查找
        if base_type in ["String", "Integer", "Boolean", "Object", "Exception"]:
            return f"java.lang.{base_type}"

        # 最后返回原始名称
        return type_name

    def _extract_imports(self, content: str) -> List[str]:
        """提取导入语句"""
        imports = []
        for match in re.finditer(r"import\s+([\w.]+);", content):
            imports.append(match.group(1))
        return imports

    def analyze_file_dependencies(self, file_path: str) -> Dict:
        """分析单个文件的依赖注入情况"""
        file_path = self.project_root + file_path
        print(file_path)
        if not os.path.exists(file_path):
            return {"error": f"文件不存在: {file_path}"}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取包名和导入
            package_match = re.search(r"package\s+([\w.]+);", content)
            package_name = package_match.group(1) if package_match else ""
            imports = self._extract_imports(content)

            # 提取类名
            class_match = re.search(
                r"(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)",
                content,
            )
            if not class_match:
                return {"error": "无法找到类定义"}

            class_name = class_match.group(1)
            full_class_name = f"{package_name}.{class_name}"

            # 分析结果
            result = {
                "class_name": full_class_name,
                "file_path": file_path,
                "package": package_name,
                "is_bean": full_class_name in self.bean_cache,
                "bean_type": self.bean_cache.get(full_class_name, {}).get("type", ""),
                "dependencies": [],
                "dependents": [],
                "interfaces": [],
                "implements": [],
            }

            # 分析依赖注入
            # 1. 分析字段注入
            field_pattern = (
                r"@(?:"
                + "|".join(self.injection_annotations)
                + r")\s*(?:\([^)]*\))?\s*(?:private|protected|public)?\s*(\w+(?:<[^>]+>)?)\s+(\w+)\s*;"
            )
            for field_match in re.finditer(field_pattern, content):
                field_type = field_match.group(1)
                field_name = field_match.group(2)
                full_type = self._resolve_type_name(field_type, package_name, imports)

                result["dependencies"].append(
                    {
                        "type": full_type,
                        "name": field_name,
                        "injection_type": "field",
                        "is_bean": full_type in self.bean_cache,
                    }
                )

            # 2. 分析构造函数注入
            constructor_pattern = rf"(?:@Autowired\s*)?(?:public|private|protected)?\s*{class_name}\s*\((.*?)\)"
            constructor_matches = re.finditer(constructor_pattern, content, re.DOTALL)
            for constructor_match in constructor_matches:
                params = constructor_match.group(1).strip()
                if params:
                    param_matches = re.finditer(
                        r"(?:final\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)", params
                    )
                    for param_match in param_matches:
                        param_type = param_match.group(1)
                        param_name = param_match.group(2)
                        full_type = self._resolve_type_name(
                            param_type, package_name, imports
                        )

                        result["dependencies"].append(
                            {
                                "type": full_type,
                                "name": param_name,
                                "injection_type": "constructor",
                                "is_bean": full_type in self.bean_cache,
                            }
                        )

            # 3. 分析接口实现
            implements_pattern = rf"class\s+{class_name}\s+(?:extends\s+(\w+)\s+)?implements\s+([\w\s,]+)"
            implements_match = re.search(implements_pattern, content)
            if implements_match:
                # 处理extends
                if implements_match.group(1):
                    parent_class = implements_match.group(1)
                    full_parent = self._resolve_type_name(
                        parent_class, package_name, imports
                    )
                    result["implements"].append(
                        {"type": full_parent, "relation": "extends"}
                    )

                # 处理implements
                interfaces = implements_match.group(2).split(",")
                for interface in interfaces:
                    interface = interface.strip()
                    if interface:
                        full_interface = self._resolve_type_name(
                            interface, package_name, imports
                        )
                        result["implements"].append(
                            {"type": full_interface, "relation": "implements"}
                        )

            # 查找依赖此类的其他Bean
            if full_class_name in self.bean_cache:
                # 这部分可能需要扫描所有文件，这里简化处理
                # 实际实现可能需要预先建立反向索引
                for bean_name, bean_info in self.bean_cache.items():
                    if bean_name == full_class_name:
                        continue

                    # 简单检查是否有依赖关系
                    if os.path.exists(bean_info["file_path"]):
                        with open(bean_info["file_path"], "r", encoding="utf-8") as f:
                            other_content = f.read()

                        # 检查是否依赖当前类
                        simple_check = class_name in other_content
                        if simple_check:
                            result["dependents"].append(
                                {"type": bean_name, "file_path": bean_info["file_path"]}
                            )

            return result

        except Exception as e:
            return {"error": f"分析文件时出错: {str(e)}"}

    def get_dependency_context(self, file_path: str) -> Dict:
        """获取文件的依赖注入上下文"""
        dependencies = self.analyze_file_dependencies(file_path)

        # 添加相关的Bean信息
        if "dependencies" in dependencies:
            related_beans = []
            for dep in dependencies["dependencies"]:
                if dep["is_bean"]:
                    bean_type = dep["type"]
                    bean_info = self.bean_cache.get(bean_type, {})
                    related_beans.append(
                        {
                            "name": bean_type,
                            "type": bean_info.get("type", ""),
                            "file_path": bean_info.get("file_path", ""),
                        }
                    )

            dependencies["related_beans"] = related_beans

        return dependencies


def get_di_context(project_root: str, file_path: str) -> Dict:
    """API函数：获取文件的依赖注入上下文"""
    analyzer = DependencyContext(project_root)
    return analyzer.get_dependency_context(file_path)


def get_di_context_json(project_root: str, file_path: str) -> str:
    """API函数：获取文件的依赖注入上下文的JSON字符串"""
    context = get_di_context(project_root, file_path)
    return json.dumps(context, indent=2, ensure_ascii=False)


# 命令行工具入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="依赖注入上下文分析工具")
    parser.add_argument("project_path", type=str, help="Java项目根目录")
    parser.add_argument("file_path", type=str, help="要分析的Java文件路径")

    args = parser.parse_args()

    context = get_di_context(args.project_path, args.file_path)
    print(json.dumps(context, indent=2, ensure_ascii=False))
