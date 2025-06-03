import json
import xml.etree.ElementTree as ET
import re

def detect_response_format(response: str) -> str:
    """
    检测大模型返回的格式类型
    
    Args:
        response (str): 大模型返回的响应内容
    
    Returns:
        str: 返回格式类型 - "json", "xml", 或 "text"
    """
    response = response.strip()

    def is_json():
        try:
            # 检查是否以JSON典型字符开始和结束
            json_content = response
            if response.startswith('```json') and response.endswith('```'):
                # 提取代码块中的内容
                json_content = response[7:-3].strip()
            
            json.loads(json_content)
            return True
        except (json.JSONDecodeError, ValueError):
            pass
        return False
    
    # 检测XML格式
    def is_xml():
        try:
            xml_content = response
            # 检查是否以```xml开头和```结尾
            if response.startswith('```xml') and response.endswith('```'):
                # 提取代码块中的内容
                xml_content = response[6:-3].strip()
            
            # 检查是否包含XML标签模式
            if re.search(r'<[^>]+>', xml_content):
                # 尝试解析XML
                ET.fromstring(xml_content)
                return True
        except ET.ParseError:
            # 可能是不完整的XML片段，检查是否有XML标签特征
            xml_content = response
            if response.startswith('```xml') and response.endswith('```'):
                xml_content = response[6:-3].strip()
            
            if re.match(r'^\s*<\w+.*>.*</\w+>\s*$', xml_content, re.DOTALL):
                return True
        except Exception:
            pass
        return False
    
    # 按优先级检测格式
    if is_json():
        return "json"
    elif is_xml():
        return "xml"
    else:
        return "text"

# 测试用例
if __name__ == "__main__":
    # JSON格式测试
    json_response = '''[
        {
            "file": "UserController.java",
            "function": "createUser",
            "operation": "update"
        }
    ]'''
    
    # XML格式测试
    xml_response = '''<tool>
        <action type="view">
            <filepath>/home/user/project/src/app.js</filepath>
        </action>
    </tool>'''
    
    # 文本格式测试
    text_response = "我需要更多信息来理解这个提交类型和消息的具体含义。"
    
    print(f"JSON格式检测: {detect_response_format(json_response)}")
    print(f"XML格式检测: {detect_response_format(xml_response)}")
    print(f"文本格式检测: {detect_response_format(text_response)}")