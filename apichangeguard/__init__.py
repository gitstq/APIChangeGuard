"""
APIChangeGuard - 轻量级API变更智能检测与影响分析引擎

一个零依赖的Python CLI工具，用于智能检测API变更、分析影响范围、生成兼容性报告。
"""

__version__ = "1.0.0"
__author__ = "APIChangeGuard Team"
__license__ = "MIT"

from .core import APIDiffEngine, ChangeClassifier, ImpactAnalyzer
from .parsers import OpenAPIParser, GraphQLParser, RESTParser
from .reporters import ConsoleReporter, JSONReporter, HTMLReporter, SARIFReporter

__all__ = [
    "APIDiffEngine",
    "ChangeClassifier", 
    "ImpactAnalyzer",
    "OpenAPIParser",
    "GraphQLParser",
    "RESTParser",
    "ConsoleReporter",
    "JSONReporter",
    "HTMLReporter",
    "SARIFReporter",
]
