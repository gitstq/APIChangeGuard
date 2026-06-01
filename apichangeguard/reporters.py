"""
报告生成器模块 - 支持多种格式输出
"""

import json
import html
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core import AnalysisReport, APIChange, ChangeType, Severity


class BaseReporter(ABC):
    """报告生成器基类"""
    
    @abstractmethod
    def generate(self, report: AnalysisReport, output_path: Optional[Path] = None) -> str:
        """生成报告"""
        pass
    
    def _get_severity_emoji(self, severity: Severity) -> str:
        """获取严重程度的表情符号"""
        emoji_map = {
            Severity.CRITICAL: "🔴",
            Severity.HIGH: "🟠",
            Severity.MEDIUM: "🟡",
            Severity.LOW: "🔵",
            Severity.INFO: "⚪"
        }
        return emoji_map.get(severity, "⚪")
    
    def _get_change_type_emoji(self, change_type: ChangeType) -> str:
        """获取变更类型的表情符号"""
        emoji_map = {
            ChangeType.ADDED: "➕",
            ChangeType.REMOVED: "➖",
            ChangeType.MODIFIED: "📝",
            ChangeType.DEPRECATED: "⚠️",
            ChangeType.UNCHANGED: "➖"
        }
        return emoji_map.get(change_type, "📝")


class ConsoleReporter(BaseReporter):
    """控制台报告生成器"""
    
    def generate(self, report: AnalysisReport, output_path: Optional[Path] = None) -> str:
        """生成控制台格式报告"""
        lines = []
        
        # 标题
        lines.append("=" * 80)
        lines.append("🛡️  APIChangeGuard - API变更检测报告")
        lines.append("=" * 80)
        lines.append("")
        
        # 概览
        lines.append("📊 变更概览")
        lines.append("-" * 80)
        lines.append(f"  总变更数:     {report.total_changes}")
        lines.append(f"  破坏性变更:   {report.breaking_changes} {'⚠️' if report.breaking_changes > 0 else '✅'}")
        lines.append(f"  新增:         {report.additions}")
        lines.append(f"  删除:         {report.removals}")
        lines.append(f"  修改:         {report.modifications}")
        lines.append(f"  废弃:         {report.deprecations}")
        lines.append("")
        
        # 兼容性评分
        lines.append("🎯 兼容性评分")
        lines.append("-" * 80)
        score = report.compatibility_score
        score_bar = self._render_score_bar(score)
        lines.append(f"  评分: {score:.1f}/100 {score_bar}")
        
        if "compatibility_level" in report.summary:
            lines.append(f"  等级: {report.summary['compatibility_level']}")
        if "risk_assessment" in report.summary:
            lines.append(f"  风险: {report.summary['risk_assessment']}")
        lines.append("")
        
        # 分类统计
        if "category_distribution" in report.summary:
            lines.append("📁 变更分类统计")
            lines.append("-" * 80)
            for category, count in report.summary["category_distribution"].items():
                lines.append(f"  {category:20s}: {count:3d}")
            lines.append("")
        
        # 严重程度分布
        if "severity_distribution" in report.summary:
            lines.append("⚡ 严重程度分布")
            lines.append("-" * 80)
            for sev, count in report.summary["severity_distribution"].items():
                emoji = self._get_severity_emoji(Severity(sev))
                lines.append(f"  {emoji} {sev:12s}: {count:3d}")
            lines.append("")
        
        # 详细变更列表
        if report.changes:
            lines.append("🔍 详细变更列表")
            lines.append("-" * 80)
            
            # 按严重程度排序
            severity_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]
            sorted_changes = sorted(report.changes, 
                                  key=lambda x: severity_order.index(x.severity) if x.severity in severity_order else 999)
            
            for i, change in enumerate(sorted_changes, 1):
                sev_emoji = self._get_severity_emoji(change.severity)
                type_emoji = self._get_change_type_emoji(change.change_type)
                breaking = " [破坏性]" if change.breaking else ""
                
                lines.append(f"\n  {i}. {sev_emoji} {type_emoji} {change.category.value.upper()}{breaking}")
                lines.append(f"     路径: {change.path}")
                lines.append(f"     描述: {change.description}")
                
                if change.old_value is not None or change.new_value is not None:
                    lines.append(f"     变更: {change.old_value} → {change.new_value}")
                
                if change.migration_guide:
                    lines.append(f"     迁移: {change.migration_guide}")
            
            lines.append("")
        
        # 建议
        if report.recommendations:
            lines.append("💡 建议")
            lines.append("-" * 80)
            for rec in report.recommendations:
                lines.append(f"  • {rec}")
            lines.append("")
        
        # 页脚
        lines.append("=" * 80)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        
        output = "\n".join(lines)
        
        if output_path:
            output_path.write_text(output, encoding='utf-8')
        
        return output
    
    def _render_score_bar(self, score: float, width: int = 30) -> str:
        """渲染评分条"""
        filled = int(score / 100 * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"


class JSONReporter(BaseReporter):
    """JSON报告生成器"""
    
    def generate(self, report: AnalysisReport, output_path: Optional[Path] = None) -> str:
        """生成JSON格式报告"""
        data = {
            "metadata": {
                "tool": "APIChangeGuard",
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat()
            },
            "summary": {
                "total_changes": report.total_changes,
                "breaking_changes": report.breaking_changes,
                "additions": report.additions,
                "removals": report.removals,
                "modifications": report.modifications,
                "deprecations": report.deprecations,
                "compatibility_score": round(report.compatibility_score, 2)
            },
            "analysis": report.summary,
            "recommendations": report.recommendations,
            "changes": [
                {
                    "type": c.change_type.name,
                    "category": c.category.value,
                    "path": c.path,
                    "description": c.description,
                    "severity": c.severity.value,
                    "breaking": c.breaking,
                    "old_value": c.old_value,
                    "new_value": c.new_value,
                    "migration_guide": c.migration_guide,
                    "line_number": c.line_number
                }
                for c in report.changes
            ]
        }
        
        output = json.dumps(data, indent=2, ensure_ascii=False)
        
        if output_path:
            output_path.write_text(output, encoding='utf-8')
        
        return output


class HTMLReporter(BaseReporter):
    """HTML报告生成器"""
    
    def generate(self, report: AnalysisReport, output_path: Optional[Path] = None) -> str:
        """生成HTML格式报告"""
        
        # 计算颜色
        score_color = self._get_score_color(report.compatibility_score)
        
        # 生成变更表格行
        change_rows = []
        for change in report.changes:
            sev_class = f"severity-{change.severity.value}"
            type_class = f"type-{change.change_type.name.lower()}"
            breaking_badge = '<span class="badge breaking">破坏性</span>' if change.breaking else ''
            
            change_rows.append(f"""
                <tr class="{sev_class}">
                    <td>{self._get_severity_emoji(change.severity)} {change.severity.value.upper()}</td>
                    <td>{self._get_change_type_emoji(change.change_type)} {change.change_type.name}</td>
                    <td>{change.category.value}</td>
                    <td><code>{html.escape(change.path)}</code></td>
                    <td>{html.escape(change.description)} {breaking_badge}</td>
                </tr>
            """)
        
        changes_table = "\n".join(change_rows) if change_rows else "<tr><td colspan=\"5\" class=\"no-data\">无变更</td></tr>"
        
        # 生成建议列表
        recommendations_html = "\n".join([f"<li>{html.escape(rec)}</li>" for rec in report.recommendations]) if report.recommendations else "<li>无特别建议</li>"
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APIChangeGuard - API变更检测报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; font-size: 1.1em; }}
        .content {{ padding: 40px; }}
        .score-card {{
            background: linear-gradient(135deg, {score_color} 0%, {self._lighten_color(score_color)} 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .score-value {{ font-size: 4em; font-weight: bold; }}
        .score-label {{ font-size: 1.2em; opacity: 0.9; margin-top: 10px; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .severity-critical {{ border-left: 4px solid #dc3545; }}
        .severity-high {{ border-left: 4px solid #fd7e14; }}
        .severity-medium {{ border-left: 4px solid #ffc107; }}
        .severity-low {{ border-left: 4px solid #17a2b8; }}
        .severity-info {{ border-left: 4px solid #6c757d; }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: 600;
        }}
        .badge.breaking {{
            background: #dc3545;
            color: white;
        }}
        .recommendations {{
            background: #e7f3ff;
            border-left: 4px solid #0066cc;
            padding: 20px;
            border-radius: 8px;
        }}
        .recommendations ul {{
            list-style: none;
            padding-left: 0;
        }}
        .recommendations li {{
            padding: 8px 0;
            border-bottom: 1px dashed #ccc;
        }}
        .recommendations li:last-child {{ border-bottom: none; }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Consolas", "Monaco", monospace;
            font-size: 0.9em;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            border-top: 1px solid #e9ecef;
        }}
        .no-data {{
            text-align: center;
            color: #666;
            padding: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ APIChangeGuard</h1>
            <p>API变更智能检测与影响分析报告</p>
        </div>
        
        <div class="content">
            <div class="score-card">
                <div class="score-value">{report.compatibility_score:.1f}</div>
                <div class="score-label">兼容性评分 / 100</div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{report.total_changes}</div>
                    <div class="stat-label">总变更</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: {'#dc3545' if report.breaking_changes > 0 else '#28a745'}">{report.breaking_changes}</div>
                    <div class="stat-label">破坏性变更</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{report.additions}</div>
                    <div class="stat-label">新增</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{report.removals}</div>
                    <div class="stat-label">删除</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{report.modifications}</div>
                    <div class="stat-label">修改</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{report.deprecations}</div>
                    <div class="stat-label">废弃</div>
                </div>
            </div>
            
            <div class="section">
                <h2>🔍 详细变更列表</h2>
                <table>
                    <thead>
                        <tr>
                            <th>严重程度</th>
                            <th>变更类型</th>
                            <th>类别</th>
                            <th>路径</th>
                            <th>描述</th>
                        </tr>
                    </thead>
                    <tbody>
                        {changes_table}
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>💡 建议</h2>
                <div class="recommendations">
                    <ul>
                        {recommendations_html}
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | APIChangeGuard v1.0.0</p>
        </div>
    </div>
</body>
</html>"""
        
        if output_path:
            output_path.write_text(html_content, encoding='utf-8')
        
        return html_content
    
    def _get_score_color(self, score: float) -> str:
        """根据评分获取颜色"""
        if score >= 90:
            return "#28a745"
        elif score >= 70:
            return "#17a2b8"
        elif score >= 50:
            return "#ffc107"
        elif score >= 30:
            return "#fd7e14"
        else:
            return "#dc3545"
    
    def _lighten_color(self, hex_color: str) -> str:
        """简化颜色变亮"""
        # 简化实现，返回相近的浅色
        color_map = {
            "#28a745": "#34ce57",
            "#17a2b8": "#1fc8e3",
            "#ffc107": "#ffce3a",
            "#fd7e14": "#ff9a47",
            "#dc3545": "#e4606d"
        }
        return color_map.get(hex_color, hex_color)


class SARIFReporter(BaseReporter):
    """SARIF格式报告生成器 (用于安全工具集成)"""
    
    def generate(self, report: AnalysisReport, output_path: Optional[Path] = None) -> str:
        """生成SARIF格式报告"""
        
        # SARIF版本 2.1.0
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "APIChangeGuard",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/yourusername/APIChangeGuard",
                        "rules": self._generate_rules(report)
                    }
                },
                "results": self._generate_results(report),
                "properties": {
                    "compatibilityScore": report.compatibility_score,
                    "totalChanges": report.total_changes,
                    "breakingChanges": report.breaking_changes
                }
            }]
        }
        
        output = json.dumps(sarif, indent=2, ensure_ascii=False)
        
        if output_path:
            output_path.write_text(output, encoding='utf-8')
        
        return output
    
    def _generate_rules(self, report: AnalysisReport) -> List[Dict]:
        """生成SARIF规则定义"""
        rules = []
        
        # 为每种变更类型创建规则
        rule_definitions = {
            "breaking-change": {
                "id": "API-BREAKING-001",
                "name": "BreakingChange",
                "shortDescription": {"text": "破坏性API变更"},
                "fullDescription": {"text": "此变更会破坏现有API兼容性，需要客户端修改代码"},
                "defaultConfiguration": {"level": "error"}
            },
            "deprecated-api": {
                "id": "API-DEPRECATED-001",
                "name": "DeprecatedAPI",
                "shortDescription": {"text": "废弃的API"},
                "fullDescription": {"text": "此API已被标记为废弃，建议迁移到新接口"},
                "defaultConfiguration": {"level": "warning"}
            },
            "endpoint-removed": {
                "id": "API-ENDPOINT-001",
                "name": "EndpointRemoved",
                "shortDescription": {"text": "端点被删除"},
                "fullDescription": {"text": "API端点已被删除"},
                "defaultConfiguration": {"level": "error"}
            },
            "schema-changed": {
                "id": "API-SCHEMA-001",
                "name": "SchemaChanged",
                "shortDescription": {"text": "数据模型变更"},
                "fullDescription": {"text": "API数据模型结构发生变更"},
                "defaultConfiguration": {"level": "warning"}
            }
        }
        
        for rule_def in rule_definitions.values():
            rules.append(rule_def)
        
        return rules
    
    def _generate_results(self, report: AnalysisReport) -> List[Dict]:
        """生成SARIF结果"""
        results = []
        
        severity_map = {
            Severity.CRITICAL: "error",
            Severity.HIGH: "error",
            Severity.MEDIUM: "warning",
            Severity.LOW: "note",
            Severity.INFO: "note"
        }
        
        for change in report.changes:
            # 确定规则ID
            if change.breaking:
                rule_id = "API-BREAKING-001"
            elif change.change_type == ChangeType.DEPRECATED:
                rule_id = "API-DEPRECATED-001"
            elif change.change_type == ChangeType.REMOVED and change.category.value == "endpoint":
                rule_id = "API-ENDPOINT-001"
            else:
                rule_id = "API-SCHEMA-001"
            
            result = {
                "ruleId": rule_id,
                "level": severity_map.get(change.severity, "warning"),
                "message": {
                    "text": change.description
                },
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": change.path
                        }
                    }
                }],
                "properties": {
                    "category": change.category.value,
                    "changeType": change.change_type.name,
                    "breaking": change.breaking
                }
            }
            
            if change.migration_guide:
                result["properties"]["migrationGuide"] = change.migration_guide
            
            results.append(result)
        
        return results
