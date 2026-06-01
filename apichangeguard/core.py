"""
核心引擎模块 - 实现API差异检测、变更分类和影响分析
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pathlib import Path


class ChangeType(Enum):
    """变更类型枚举"""
    ADDED = auto()      # 新增
    REMOVED = auto()    # 删除
    MODIFIED = auto()   # 修改
    DEPRECATED = auto() # 废弃
    UNCHANGED = auto()  # 未变更


class Severity(Enum):
    """严重程度枚举"""
    CRITICAL = "critical"    # 破坏性变更
    HIGH = "high"           # 高风险
    MEDIUM = "medium"       # 中等风险
    LOW = "low"             # 低风险
    INFO = "info"           # 信息


class ChangeCategory(Enum):
    """变更分类枚举"""
    ENDPOINT = "endpoint"           # 端点变更
    PARAMETER = "parameter"         # 参数变更
    RESPONSE = "response"           # 响应变更
    SCHEMA = "schema"               # 模型变更
    SECURITY = "security"           # 安全变更
    DOCUMENTATION = "documentation" # 文档变更


@dataclass
class APIChange:
    """API变更数据类"""
    change_type: ChangeType
    category: ChangeCategory
    path: str
    description: str
    severity: Severity
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    breaking: bool = False
    migration_guide: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class AnalysisReport:
    """分析报告数据类"""
    total_changes: int = 0
    breaking_changes: int = 0
    additions: int = 0
    removals: int = 0
    modifications: int = 0
    deprecations: int = 0
    compatibility_score: float = 100.0
    changes: List[APIChange] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class APIDiffEngine:
    """API差异检测引擎"""
    
    def __init__(self):
        self.changes: List[APIChange] = []
    
    def compare(self, old_api: Dict[str, Any], new_api: Dict[str, Any]) -> List[APIChange]:
        """
        比较两个API定义，返回变更列表
        
        Args:
            old_api: 旧版本API定义
            new_api: 新版本API定义
            
        Returns:
            List[APIChange]: 变更列表
        """
        self.changes = []
        self._compare_paths(old_api, new_api)
        self._compare_schemas(old_api, new_api)
        self._compare_security(old_api, new_api)
        return self.changes
    
    def _compare_paths(self, old_api: Dict, new_api: Dict):
        """比较API路径/端点"""
        old_paths = old_api.get("paths", {})
        new_paths = new_api.get("paths", {})
        
        # 检测删除的路径
        for path in old_paths:
            if path not in new_paths:
                self.changes.append(APIChange(
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.ENDPOINT,
                    path=path,
                    description=f"端点 {path} 已被删除",
                    severity=Severity.CRITICAL,
                    breaking=True
                ))
        
        # 检测新增的路径
        for path in new_paths:
            if path not in old_paths:
                self.changes.append(APIChange(
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.ENDPOINT,
                    path=path,
                    description=f"新增端点 {path}",
                    severity=Severity.INFO
                ))
            else:
                # 比较路径下的方法
                self._compare_methods(path, old_paths[path], new_paths[path])
    
    def _compare_methods(self, path: str, old_methods: Dict, new_methods: Dict):
        """比较HTTP方法"""
        http_methods = ["get", "post", "put", "delete", "patch", "head", "options"]
        
        for method in http_methods:
            old_method = old_methods.get(method)
            new_method = new_methods.get(method)
            
            if old_method and not new_method:
                self.changes.append(APIChange(
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.ENDPOINT,
                    path=f"{path}.{method}",
                    description=f"删除 {method.upper()} 方法",
                    severity=Severity.CRITICAL,
                    breaking=True
                ))
            elif not old_method and new_method:
                self.changes.append(APIChange(
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.ENDPOINT,
                    path=f"{path}.{method}",
                    description=f"新增 {method.upper()} 方法",
                    severity=Severity.INFO
                ))
            elif old_method and new_method:
                self._compare_method_details(path, method, old_method, new_method)
    
    def _compare_method_details(self, path: str, method: str, old: Dict, new: Dict):
        """比较方法详情"""
        full_path = f"{path}.{method}"
        
        # 比较参数
        old_params = {p.get("name", ""): p for p in old.get("parameters", [])}
        new_params = {p.get("name", ""): p for p in new.get("parameters", [])}
        self._compare_parameters(full_path, old_params, new_params)
        
        # 比较响应
        old_responses = old.get("responses", {})
        new_responses = new.get("responses", {})
        self._compare_responses(full_path, old_responses, new_responses)
        
        # 检测废弃标记
        if new.get("deprecated") and not old.get("deprecated"):
            self.changes.append(APIChange(
                change_type=ChangeType.DEPRECATED,
                category=ChangeCategory.ENDPOINT,
                path=full_path,
                description=f"{method.upper()} 方法已标记为废弃",
                severity=Severity.MEDIUM,
                migration_guide=new.get("x-deprecated-message", "请查看文档迁移到新端点")
            ))
    
    def _compare_parameters(self, path: str, old_params: Dict, new_params: Dict):
        """比较参数"""
        # 检测必需参数变更
        for name, param in new_params.items():
            if param.get("required") and name not in old_params:
                self.changes.append(APIChange(
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.PARAMETER,
                    path=f"{path}.params.{name}",
                    description=f"新增必需参数 '{name}'",
                    severity=Severity.HIGH,
                    breaking=True
                ))
        
        for name, param in old_params.items():
            if name not in new_params:
                severity = Severity.CRITICAL if param.get("required") else Severity.MEDIUM
                self.changes.append(APIChange(
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.PARAMETER,
                    path=f"{path}.params.{name}",
                    description=f"删除参数 '{name}'",
                    severity=severity,
                    breaking=param.get("required", False)
                ))
            else:
                # 比较参数类型变更
                old_type = param.get("schema", {}).get("type", param.get("type"))
                new_type = new_params[name].get("schema", {}).get("type", new_params[name].get("type"))
                if old_type != new_type:
                    self.changes.append(APIChange(
                        change_type=ChangeType.MODIFIED,
                        category=ChangeCategory.PARAMETER,
                        path=f"{path}.params.{name}",
                        description=f"参数 '{name}' 类型从 {old_type} 变更为 {new_type}",
                        severity=Severity.HIGH,
                        breaking=True,
                        old_value=old_type,
                        new_value=new_type
                    ))
    
    def _compare_responses(self, path: str, old_responses: Dict, new_responses: Dict):
        """比较响应定义"""
        for code in old_responses:
            if code not in new_responses:
                self.changes.append(APIChange(
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.RESPONSE,
                    path=f"{path}.responses.{code}",
                    description=f"删除响应状态码 {code}",
                    severity=Severity.MEDIUM
                ))
        
        for code in new_responses:
            if code not in old_responses:
                self.changes.append(APIChange(
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.RESPONSE,
                    path=f"{path}.responses.{code}",
                    description=f"新增响应状态码 {code}",
                    severity=Severity.LOW
                ))
    
    def _compare_schemas(self, old_api: Dict, new_api: Dict):
        """比较数据模型"""
        old_schemas = old_api.get("components", {}).get("schemas", {})
        new_schemas = new_api.get("components", {}).get("schemas", {})
        
        for name in old_schemas:
            if name not in new_schemas:
                self.changes.append(APIChange(
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.SCHEMA,
                    path=f"schemas.{name}",
                    description=f"删除数据模型 '{name}'",
                    severity=Severity.CRITICAL,
                    breaking=True
                ))
            else:
                self._compare_schema_properties(name, old_schemas[name], new_schemas[name])
        
        for name in new_schemas:
            if name not in old_schemas:
                self.changes.append(APIChange(
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.SCHEMA,
                    path=f"schemas.{name}",
                    description=f"新增数据模型 '{name}'",
                    severity=Severity.INFO
                ))
    
    def _compare_schema_properties(self, schema_name: str, old: Dict, new: Dict):
        """比较模型属性"""
        old_props = old.get("properties", {})
        new_props = new.get("properties", {})
        
        required_old = set(old.get("required", []))
        required_new = set(new.get("required", []))
        
        # 检测新增必需字段
        for prop in required_new - required_old:
            self.changes.append(APIChange(
                change_type=ChangeType.ADDED,
                category=ChangeCategory.SCHEMA,
                path=f"schemas.{schema_name}.properties.{prop}",
                description=f"模型 '{schema_name}' 新增必需字段 '{prop}'",
                severity=Severity.HIGH,
                breaking=True
            ))
        
        # 检测删除字段
        for prop in old_props:
            if prop not in new_props:
                severity = Severity.CRITICAL if prop in required_old else Severity.MEDIUM
                self.changes.append(APIChange(
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.SCHEMA,
                    path=f"schemas.{schema_name}.properties.{prop}",
                    description=f"模型 '{schema_name}' 删除字段 '{prop}'",
                    severity=severity,
                    breaking=prop in required_old
                ))
    
    def _compare_security(self, old_api: Dict, new_api: Dict):
        """比较安全定义"""
        old_security = old_api.get("security", [])
        new_security = new_api.get("security", [])
        
        if old_security != new_security:
            self.changes.append(APIChange(
                change_type=ChangeType.MODIFIED,
                category=ChangeCategory.SECURITY,
                path="security",
                description="安全认证方式发生变更",
                severity=Severity.HIGH,
                breaking=True,
                old_value=old_security,
                new_value=new_security
            ))


class ChangeClassifier:
    """变更分类器"""
    
    def classify(self, changes: List[APIChange]) -> Dict[str, List[APIChange]]:
        """
        按类别对变更进行分类
        
        Args:
            changes: 变更列表
            
        Returns:
            Dict[str, List[APIChange]]: 分类后的变更
        """
        classified = {
            "breaking": [],
            "deprecated": [],
            "additions": [],
            "modifications": [],
            "removals": []
        }
        
        for change in changes:
            if change.breaking:
                classified["breaking"].append(change)
            elif change.change_type == ChangeType.DEPRECATED:
                classified["deprecated"].append(change)
            elif change.change_type == ChangeType.ADDED:
                classified["additions"].append(change)
            elif change.change_type == ChangeType.MODIFIED:
                classified["modifications"].append(change)
            elif change.change_type == ChangeType.REMOVED:
                classified["removals"].append(change)
        
        return classified


class ImpactAnalyzer:
    """影响分析器"""
    
    def analyze(self, changes: List[APIChange]) -> AnalysisReport:
        """
        分析变更影响并生成报告
        
        Args:
            changes: 变更列表
            
        Returns:
            AnalysisReport: 分析报告
        """
        report = AnalysisReport()
        report.changes = changes
        report.total_changes = len(changes)
        
        breaking_count = sum(1 for c in changes if c.breaking)
        report.breaking_changes = breaking_count
        report.additions = sum(1 for c in changes if c.change_type == ChangeType.ADDED)
        report.removals = sum(1 for c in changes if c.change_type == ChangeType.REMOVED)
        report.modifications = sum(1 for c in changes if c.change_type == ChangeType.MODIFIED)
        report.deprecations = sum(1 for c in changes if c.change_type == ChangeType.DEPRECATED)
        
        # 计算兼容性评分 (0-100)
        if report.total_changes == 0:
            report.compatibility_score = 100.0
        else:
            # 破坏性变更权重更高
            breaking_weight = 3.0
            deprecation_weight = 0.5
            removal_weight = 2.0
            modification_weight = 1.0
            addition_weight = 0.0  # 新增不影响兼容性
            
            weighted_issues = (
                breaking_count * breaking_weight +
                report.deprecations * deprecation_weight +
                sum(1 for c in changes if c.change_type == ChangeType.REMOVED and not c.breaking) * removal_weight +
                report.modifications * modification_weight
            )
            
            max_penalty = report.total_changes * breaking_weight
            report.compatibility_score = max(0, 100 - (weighted_issues / max_penalty * 100))
        
        # 生成摘要
        report.summary = self._generate_summary(report)
        
        # 生成建议
        report.recommendations = self._generate_recommendations(report)
        
        return report
    
    def _generate_summary(self, report: AnalysisReport) -> Dict[str, Any]:
        """生成摘要"""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        category_counts = {}
        
        for change in report.changes:
            severity_counts[change.severity.value] += 1
            cat = change.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return {
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "compatibility_level": self._get_compatibility_level(report.compatibility_score),
            "risk_assessment": self._assess_risk(report)
        }
    
    def _get_compatibility_level(self, score: float) -> str:
        """获取兼容性等级"""
        if score >= 90:
            return "优秀 - 完全兼容"
        elif score >= 70:
            return "良好 - 轻微影响"
        elif score >= 50:
            return "一般 - 需要关注"
        elif score >= 30:
            return "较差 - 需要修改"
        else:
            return "严重 - 破坏性变更"
    
    def _assess_risk(self, report: AnalysisReport) -> str:
        """风险评估"""
        if report.breaking_changes > 5:
            return "高风险 - 存在大量破坏性变更"
        elif report.breaking_changes > 0:
            return "中风险 - 存在破坏性变更"
        elif report.deprecations > 3:
            return "低风险 - 存在较多废弃接口"
        else:
            return "安全 - 无重大风险"
    
    def _generate_recommendations(self, report: AnalysisReport) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if report.breaking_changes > 0:
            recommendations.append(
                f"⚠️ 检测到 {report.breaking_changes} 个破坏性变更，建议发布主版本更新 (MAJOR version bump)"
            )
        
        if report.deprecations > 0:
            recommendations.append(
                f"📋 有 {report.deprecations} 个接口已废弃，建议在文档中明确标注并提供迁移指南"
            )
        
        if report.compatibility_score < 70:
            recommendations.append(
                "🔧 兼容性评分较低，建议在发布前进行充分的回归测试"
            )
        
        if report.additions > 10:
            recommendations.append(
                f"✨ 新增 {report.additions} 个功能点，建议发布次版本更新 (MINOR version bump)"
            )
        
        if not recommendations:
            recommendations.append("✅ API变更良好，可以安全发布")
        
        return recommendations
