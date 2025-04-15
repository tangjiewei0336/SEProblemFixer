import xml.etree.ElementTree as ET


class ParserError(Exception):
    pass


class ToolParser:
    def __init__(self, xml_string):
        self.xml_string = xml_string
        self.tool_info = {}

    def parse(self):
        """
        解析XML工具调用格式
        """
        try:
            root = ET.fromstring(self.xml_string)
            if root.tag != "tool":
                raise ValueError("无效的XML结构：根节点必须是<tool>")

            action = root.find("action")
            if action is None or action.get("type") != "view":
                raise ValueError("无效的动作类型")

            self.tool_info = {
                "filepath": action.find("filepath").text,
                "filename": action.find("filename").text,
                "start_line": int(action.find("start_line").text),
                "end_line": int(action.find("end_line").text),
            }

            self._validate_input()

        except ET.ParseError as e:
            raise ParserError("XML解析失败") from e

    def _validate_input(self):
        """
        验证提取的工具调用信息
        """
        # 验证路径和文件名
        if not isinstance(self.tool_info["filepath"], str) or not isinstance(
            self.tool_info["filename"], str
        ):
            raise ValueError("filepath和filename必须是字符串类型")

        # 验证行号
        if not (1 <= self.tool_info["start_line"] <= self.tool_info["end_line"]):
            raise ValueError("无效的行号范围")

    def get_tool_info(self):
        """
        返回解析后的工具信息
        """
        return self.tool_info


def get_file_content(filepath, filename, start_line, end_line):
    """
    根据工具调用信息，返回指定文件的内容
    """
    # 确保行号为1-based
    start_line = max(1, start_line)
    end_line = max(start_line, end_line)

    try:
        # 使用绝对路径读取文件
        file_path = f"{filepath}/{filename}"
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

            # 检查行号范围
            if start_line > len(lines):
                raise ValueError("起始行号超出文件范围")
            if end_line > len(lines):
                end_line = len(lines)

            # 提取指定行范围的内容
            content = "".join(lines[start_line - 1 : end_line])
            return content

    except FileNotFoundError:
        raise FileNotFoundError(f"文件 {file_path} 不存在")
    except PermissionError:
        raise PermissionError(f"没有权限读取文件 {file_path}")
    except UnicodeDecodeError:
        raise ValueError(f"无法读取文件 {file_path}，可能是二进制文件")
    except Exception as e:
        raise RuntimeError(f"读取文件 {file_path} 时发生错误：{str(e)}") from e
