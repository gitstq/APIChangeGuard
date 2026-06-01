"""
API解析器模块 - 支持多种API格式解析
"""

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


class BaseParser(ABC):
    """解析器基类"""
    
    @abstractmethod
    def parse(self, source: Union[str, Path, Dict]) -> Dict[str, Any]:
        """解析API定义"""
        pass
    
    @abstractmethod
    def validate(self, data: Dict) -> bool:
        """验证API定义格式"""
        pass
    
    def _load_file(self, source: Union[str, Path]) -> str:
        """加载文件内容"""
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {source}")
        return path.read_text(encoding='utf-8')


class OpenAPIParser(BaseParser):
    """OpenAPI/Swagger解析器"""
    
    SUPPORTED_VERSIONS = ["2.0", "3.0.0", "3.0.1", "3.0.2", "3.0.3", "3.1.0"]
    
    def parse(self, source: Union[str, Path, Dict]) -> Dict[str, Any]:
        """
        解析OpenAPI定义
        
        Args:
            source: OpenAPI文件路径或JSON/YAML字符串或字典
            
        Returns:
            Dict: 标准化的API定义
        """
        if isinstance(source, dict):
            data = source
        elif isinstance(source, (str, Path)):
            content = self._load_file(source) if Path(source).exists() else source
            data = self._parse_content(content)
        else:
            raise ValueError(f"不支持的数据源类型: {type(source)}")
        
        if not self.validate(data):
            raise ValueError("无效的OpenAPI定义")
        
        return self._normalize(data)
    
    def _parse_content(self, content: str) -> Dict:
        """解析内容"""
        # 尝试JSON解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 尝试YAML解析 (简化实现)
        return self._parse_yaml(content)
    
    def _parse_yaml(self, content: str) -> Dict:
        """简化YAML解析"""
        # 这是一个简化实现，实际项目中可以使用PyYAML
        # 这里仅处理基本的YAML结构
        result = {}
        current_key = None
        current_list = None
        indent_stack = [0]
        
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            
            # 跳过空行和注释
            if not stripped or stripped.startswith('#'):
                i += 1
                continue
            
            indent = len(line) - len(stripped)
            
            # 处理列表项
            if stripped.startswith('- '):
                value = stripped[2:].strip()
                if ':' in value:
                    key, val = value.split(':', 1)
                    if current_list is not None:
                        current_list.append({key.strip(): val.strip().strip('"\'')})
                else:
                    if current_list is not None:
                        current_list.append(value.strip().strip('"\''))
            else:
                # 处理键值对
                if ':' in stripped:
                    key, value = stripped.split(':', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    if value:
                        result[key] = value
                    else:
                        # 可能是嵌套结构
                        result[key] = {}
                        current_key = key
            
            i += 1
        
        return result
    
    def validate(self, data: Dict) -> bool:
        """验证OpenAPI格式"""
        # 检查OpenAPI版本
        if "openapi" in data:
            version = data["openapi"]
            return any(version.startswith(v) for v in self.SUPPORTED_VERSIONS)
        elif "swagger" in data:
            version = data["swagger"]
            return version in self.SUPPORTED_VERSIONS
        return False
    
    def _normalize(self, data: Dict) -> Dict[str, Any]:
        """标准化为统一格式"""
        normalized = {
            "openapi": data.get("openapi", data.get("swagger", "unknown")),
            "info": data.get("info", {}),
            "paths": data.get("paths", {}),
            "components": data.get("components", data.get("definitions", {})),
            "security": data.get("security", []),
            "servers": data.get("servers", data.get("host", ""))
        }
        return normalized


class GraphQLParser(BaseParser):
    """GraphQL Schema解析器"""
    
    def parse(self, source: Union[str, Path, Dict]) -> Dict[str, Any]:
        """解析GraphQL Schema"""
        if isinstance(source, dict):
            return source
        
        if isinstance(source, (str, Path)) and Path(source).exists():
            content = self._load_file(source)
        else:
            content = str(source)
        
        return self._parse_schema(content)
    
    def _parse_schema(self, content: str) -> Dict[str, Any]:
        """解析GraphQL SDL"""
        schema = {
            "types": {},
            "queries": {},
            "mutations": {},
            "subscriptions": {},
            "directives": []
        }
        
        # 解析类型定义
        type_pattern = r'type\s+(\w+)\s*(?:implements\s+([\w&\s]+))?\s*\{([^}]+)\}'
        for match in re.finditer(type_pattern, content, re.DOTALL):
            type_name = match.group(1)
            implements = match.group(2)
            fields_str = match.group(3)
            
            fields = self._parse_graphql_fields(fields_str)
            schema["types"][type_name] = {
                "fields": fields,
                "implements": implements.strip().split() if implements else []
            }
        
        # 解析Query类型
        query_match = re.search(r'type\s+Query\s*\{([^}]+)\}', content, re.DOTALL)
        if query_match:
            schema["queries"] = self._parse_graphql_fields(query_match.group(1))
        
        # 解析Mutation类型
        mutation_match = re.search(r'type\s+Mutation\s*\{([^}]+)\}', content, re.DOTALL)
        if mutation_match:
            schema["mutations"] = self._parse_graphql_fields(mutation_match.group(1))
        
        # 解析Subscription类型
        subscription_match = re.search(r'type\s+Subscription\s*\{([^}]+)\}', content, re.DOTALL)
        if subscription_match:
            schema["subscriptions"] = self._parse_graphql_fields(subscription_match.group(1))
        
        # 解析枚举
        enum_pattern = r'enum\s+(\w+)\s*\{([^}]+)\}'
        for match in re.finditer(enum_pattern, content, re.DOTALL):
            enum_name = match.group(1)
            values = [v.strip() for v in match.group(2).split() if v.strip()]
            schema["types"][enum_name] = {"kind": "enum", "values": values}
        
        # 解析输入类型
        input_pattern = r'input\s+(\w+)\s*\{([^}]+)\}'
        for match in re.finditer(input_pattern, content, re.DOTALL):
            input_name = match.group(1)
            fields = self._parse_graphql_fields(match.group(2))
            schema["types"][input_name] = {"kind": "input", "fields": fields}
        
        # 转换为标准格式
        return self._normalize_graphql(schema)
    
    def _parse_graphql_fields(self, fields_str: str) -> Dict[str, Dict]:
        """解析GraphQL字段"""
        fields = {}
        lines = fields_str.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 匹配字段定义: fieldName(args): Type
            field_pattern = r'(\w+)\s*(?:\(([^)]+)\))?\s*:\s*([\w\[\]!]+)'
            match = re.match(field_pattern, line)
            if match:
                field_name = match.group(1)
                args_str = match.group(2)
                field_type = match.group(3)
                
                field_def = {"type": field_type}
                
                if args_str:
                    field_def["args"] = self._parse_graphql_args(args_str)
                
                # 检查废弃标记
                if '@deprecated' in line:
                    field_def["deprecated"] = True
                    dep_match = re.search(r'@deprecated\s*\(\s*reason:\s*"([^"]+)"\s*\)', line)
                    if dep_match:
                        field_def["deprecation_reason"] = dep_match.group(1)
                
                fields[field_name] = field_def
        
        return fields
    
    def _parse_graphql_args(self, args_str: str) -> Dict[str, Dict]:
        """解析GraphQL参数"""
        args = {}
        # 简化解析，处理 arg: Type 格式
        arg_pattern = r'(\w+)\s*:\s*([\w\[\]!]+)(?:\s*=\s*(\w+))?'
        for match in re.finditer(arg_pattern, args_str):
            arg_name = match.group(1)
            arg_type = match.group(2)
            default_value = match.group(3)
            
            args[arg_name] = {
                "type": arg_type,
                "default": default_value
            }
        
        return args
    
    def _normalize_graphql(self, schema: Dict) -> Dict[str, Any]:
        """标准化GraphQL为统一格式"""
        normalized = {
            "openapi": "graphql",
            "info": {"title": "GraphQL Schema", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": schema["types"]},
            "security": [],
            "servers": "",
            "graphql": {
                "queries": schema["queries"],
                "mutations": schema["mutations"],
                "subscriptions": schema["subscriptions"]
            }
        }
        
        # 将GraphQL操作转换为类REST路径格式
        for query_name, query_def in schema["queries"].items():
            normalized["paths"][f"/graphql/query/{query_name}"] = {
                "post": {
                    "operationId": query_name,
                    "parameters": list(query_def.get("args", {}).keys()),
                    "responses": {"200": {"description": "Success"}}
                }
            }
        
        for mutation_name, mutation_def in schema["mutations"].items():
            normalized["paths"][f"/graphql/mutation/{mutation_name}"] = {
                "post": {
                    "operationId": mutation_name,
                    "parameters": list(mutation_def.get("args", {}).keys()),
                    "responses": {"200": {"description": "Success"}}
                }
            }
        
        return normalized
    
    def validate(self, data: Dict) -> bool:
        """验证GraphQL格式"""
        return "types" in data or ("openapi" in data and data.get("openapi") == "graphql")


class RESTParser(BaseParser):
    """REST API解析器 - 从代码注释或文档提取"""
    
    def parse(self, source: Union[str, Path, Dict]) -> Dict[str, Any]:
        """解析REST API定义"""
        if isinstance(source, dict):
            return source
        
        if isinstance(source, (str, Path)) and Path(source).exists():
            content = self._load_file(source)
        else:
            content = str(source)
        
        # 尝试解析为JSON
        try:
            data = json.loads(content)
            return self._normalize_rest(data)
        except json.JSONDecodeError:
            pass
        
        # 尝试从代码注释解析
        return self._parse_from_comments(content)
    
    def _parse_from_comments(self, content: str) -> Dict[str, Any]:
        """从代码注释解析API定义"""
        api_def = {
            "openapi": "3.0.0",
            "info": {"title": "REST API", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}}
        }
        
        # 解析JSDoc/Docstring风格的注释
        # @route GET /api/users
        # @param {string} name - User name
        # @returns {Object} User object
        
        route_pattern = r'@route\s+(\w+)\s+(/[\w/{}]+)'
        param_pattern = r'@param\s+\{([^}]+)\}\s+(\w+)\s*-?\s*(.*)'
        returns_pattern = r'@returns?\s+\{([^}]+)\}\s*(.*)'
        
        routes = re.finditer(route_pattern, content)
        for route_match in routes:
            method = route_match.group(1).lower()
            path = route_match.group(2)
            
            if path not in api_def["paths"]:
                api_def["paths"][path] = {}
            
            endpoint = {
                "operationId": f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '')}",
                "parameters": [],
                "responses": {"200": {"description": "Success"}}
            }
            
            api_def["paths"][path][method] = endpoint
        
        return api_def
    
    def _normalize_rest(self, data: Dict) -> Dict[str, Any]:
        """标准化REST定义"""
        return {
            "openapi": data.get("openapi", "3.0.0"),
            "info": data.get("info", {"title": "REST API", "version": "1.0.0"}),
            "paths": data.get("paths", {}),
            "components": data.get("components", {"schemas": {}}),
            "security": data.get("security", []),
            "servers": data.get("servers", "")
        }
    
    def validate(self, data: Dict) -> bool:
        """验证REST格式"""
        return "paths" in data


def auto_detect_parser(source: Union[str, Path]) -> BaseParser:
    """
    自动检测并返回合适的解析器
    
    Args:
        source: API定义文件路径
        
    Returns:
        BaseParser: 合适的解析器实例
    """
    path = Path(source)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {source}")
    
    content = path.read_text(encoding='utf-8').lower()
    
    # 检测GraphQL
    if path.suffix in ['.graphql', '.gql'] or 'type query' in content or 'type mutation' in content:
        return GraphQLParser()
    
    # 检测OpenAPI
    if '"openapi"' in content or '"swagger"' in content or 'openapi:' in content:
        return OpenAPIParser()
    
    # 默认使用OpenAPI解析器
    return OpenAPIParser()
