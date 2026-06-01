"""
命令行接口模块
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .core import APIDiffEngine, ChangeClassifier, ImpactAnalyzer
from .parsers import auto_detect_parser, OpenAPIParser, GraphQLParser
from .reporters import ConsoleReporter, JSONReporter, HTMLReporter, SARIFReporter


def create_parser() -> argparse.ArgumentParser:
    """创建参数解析器"""
    parser = argparse.ArgumentParser(
        prog="apichangeguard",
        description="🛡️ APIChangeGuard - 轻量级API变更智能检测与影响分析引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s compare old_api.json new_api.json
  %(prog)s compare old.yaml new.yaml --format html --output report.html
  %(prog)s compare old.graphql new.graphql --format sarif
  %(prog)s validate api.json
  %(prog)s scan ./api_directory --recursive

支持格式:
  • OpenAPI 2.0/3.0/3.1 (JSON/YAML)
  • GraphQL Schema
  • REST API 文档
        """
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # compare 命令
    compare_parser = subparsers.add_parser(
        "compare",
        help="比较两个API版本",
        description="比较两个API定义文件，检测变更并生成报告"
    )
    compare_parser.add_argument(
        "old_api",
        type=str,
        help="旧版本API文件路径"
    )
    compare_parser.add_argument(
        "new_api",
        type=str,
        help="新版本API文件路径"
    )
    compare_parser.add_argument(
        "-f", "--format",
        choices=["console", "json", "html", "sarif"],
        default="console",
        help="输出格式 (默认: console)"
    )
    compare_parser.add_argument(
        "-o", "--output",
        type=str,
        help="输出文件路径"
    )
    compare_parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="检测到破坏性变更时返回非零退出码"
    )
    compare_parser.add_argument(
        "--threshold",
        type=float,
        default=0.0,
        help="兼容性评分阈值，低于此值返回非零退出码 (默认: 0)"
    )
    
    # validate 命令
    validate_parser = subparsers.add_parser(
        "validate",
        help="验证API定义格式",
        description="验证API定义文件格式是否正确"
    )
    validate_parser.add_argument(
        "api_file",
        type=str,
        help="API定义文件路径"
    )
    
    # scan 命令
    scan_parser = subparsers.add_parser(
        "scan",
        help="扫描目录中的API文件",
        description="扫描目录自动发现API定义文件"
    )
    scan_parser.add_argument(
        "directory",
        type=str,
        help="要扫描的目录"
    )
    scan_parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="递归扫描子目录"
    )
    scan_parser.add_argument(
        "--pattern",
        type=str,
        default="*.json,*.yaml,*.yml,*.graphql",
        help="文件匹配模式 (默认: *.json,*.yaml,*.yml,*.graphql)"
    )
    
    # init 命令
    init_parser = subparsers.add_parser(
        "init",
        help="初始化配置文件",
        description="创建APIChangeGuard配置文件"
    )
    init_parser.add_argument(
        "--global",
        dest="global_config",
        action="store_true",
        help="创建全局配置文件"
    )
    
    return parser


def cmd_compare(args) -> int:
    """执行compare命令"""
    try:
        old_path = Path(args.old_api)
        new_path = Path(args.new_api)
        
        if not old_path.exists():
            print(f"❌ 错误: 旧版本文件不存在: {old_path}", file=sys.stderr)
            return 1
        
        if not new_path.exists():
            print(f"❌ 错误: 新版本文件不存在: {new_path}", file=sys.stderr)
            return 1
        
        # 自动检测解析器
        parser = auto_detect_parser(old_path)
        
        print(f"🔍 正在解析旧版本API: {old_path}")
        old_api = parser.parse(old_path)
        
        print(f"🔍 正在解析新版本API: {new_path}")
        new_api = parser.parse(new_path)
        
        # 执行差异检测
        print("🔍 正在检测API变更...")
        diff_engine = APIDiffEngine()
        changes = diff_engine.compare(old_api, new_api)
        
        # 执行影响分析
        print("📊 正在分析影响范围...")
        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(changes)
        
        # 生成报告
        print(f"📝 正在生成{args.format}格式报告...")
        
        if args.format == "console":
            reporter = ConsoleReporter()
        elif args.format == "json":
            reporter = JSONReporter()
        elif args.format == "html":
            reporter = HTMLReporter()
        elif args.format == "sarif":
            reporter = SARIFReporter()
        else:
            reporter = ConsoleReporter()
        
        output_path = Path(args.output) if args.output else None
        output = reporter.generate(report, output_path)
        
        if not output_path:
            print(output)
        else:
            print(f"✅ 报告已保存: {output_path}")
        
        # 检查退出条件
        if args.fail_on_breaking and report.breaking_changes > 0:
            print(f"\n⚠️ 检测到 {report.breaking_changes} 个破坏性变更", file=sys.stderr)
            return 2
        
        if args.threshold > 0 and report.compatibility_score < args.threshold:
            print(f"\n⚠️ 兼容性评分 {report.compatibility_score:.1f} 低于阈值 {args.threshold}", file=sys.stderr)
            return 3
        
        return 0
        
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        return 1


def cmd_validate(args) -> int:
    """执行validate命令"""
    try:
        api_path = Path(args.api_file)
        
        if not api_path.exists():
            print(f"❌ 错误: 文件不存在: {api_path}", file=sys.stderr)
            return 1
        
        parser = auto_detect_parser(api_path)
        api_def = parser.parse(api_path)
        
        print(f"✅ API定义验证通过: {api_path}")
        
        # 显示基本信息
        if "info" in api_def:
            info = api_def["info"]
            print(f"   标题: {info.get('title', 'N/A')}")
            print(f"   版本: {info.get('version', 'N/A')}")
        
        print(f"   端点数: {len(api_def.get('paths', {}))}")
        print(f"   模型数: {len(api_def.get('components', {}).get('schemas', {}))}")
        
        return 0
        
    except Exception as e:
        print(f"❌ 验证失败: {e}", file=sys.stderr)
        return 1


def cmd_scan(args) -> int:
    """执行scan命令"""
    try:
        directory = Path(args.directory)
        
        if not directory.exists():
            print(f"❌ 错误: 目录不存在: {directory}", file=sys.stderr)
            return 1
        
        if not directory.is_dir():
            print(f"❌ 错误: 不是目录: {directory}", file=sys.stderr)
            return 1
        
        patterns = args.pattern.split(",")
        found_files = []
        
        if args.recursive:
            for pattern in patterns:
                found_files.extend(directory.rglob(pattern))
        else:
            for pattern in patterns:
                found_files.extend(directory.glob(pattern))
        
        # 去重并保持顺序
        found_files = sorted(set(found_files))
        
        if not found_files:
            print(f"📂 在 {directory} 中未找到API定义文件")
            return 0
        
        print(f"📂 在 {directory} 中找到 {len(found_files)} 个API定义文件:\n")
        
        for file_path in found_files:
            try:
                parser = auto_detect_parser(file_path)
                api_def = parser.parse(file_path)
                
                info = api_def.get("info", {})
                title = info.get("title", "Unknown")
                version = info.get("version", "Unknown")
                endpoints = len(api_def.get("paths", {}))
                
                print(f"  ✅ {file_path}")
                print(f"     类型: {api_def.get('openapi', 'unknown')}")
                print(f"     标题: {title}")
                print(f"     版本: {version}")
                print(f"     端点: {endpoints}")
                print()
                
            except Exception as e:
                print(f"  ⚠️  {file_path} (解析失败: {e})")
                print()
        
        return 0
        
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        return 1


def cmd_init(args) -> int:
    """执行init命令"""
    try:
        if args.global_config:
            config_path = Path.home() / ".apichangeguard.json"
        else:
            config_path = Path(".apichangeguard.json")
        
        if config_path.exists():
            print(f"⚠️ 配置文件已存在: {config_path}")
            return 0
        
        config = {
            "version": "1.0.0",
            "default_format": "console",
            "thresholds": {
                "compatibility_score": 70.0,
                "max_breaking_changes": 0
            },
            "rules": {
                "check_deprecated": True,
                "check_security": True,
                "check_documentation": False
            },
            "reporters": {
                "console": {
                    "colors": True,
                    "verbose": False
                },
                "html": {
                    "theme": "default"
                }
            }
        }
        
        import json
        config_path.write_text(json.dumps(config, indent=2), encoding='utf-8')
        
        print(f"✅ 配置文件已创建: {config_path}")
        return 0
        
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """主入口函数"""
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    if not parsed_args.command:
        parser.print_help()
        return 0
    
    command_map = {
        "compare": cmd_compare,
        "validate": cmd_validate,
        "scan": cmd_scan,
        "init": cmd_init
    }
    
    handler = command_map.get(parsed_args.command)
    if handler:
        return handler(parsed_args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
