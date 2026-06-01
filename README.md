<div align="center">

# 🛡️ APIChangeGuard

**轻量级API变更智能检测与影响分析引擎**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-brightgreen)](requirements.txt)
[![CI/CD Ready](https://img.shields.io/badge/CI%2FCD-Ready-orange)](.github/workflows)

[English](#english) | [简体中文](#简体中文) | [繁體中文](#繁體中文)

</div>

---

## 简体中文

### 🎉 项目介绍

**APIChangeGuard** 是一款专为API版本管理设计的轻量级智能检测工具。它能够自动对比API版本差异，精准识别破坏性变更，量化兼容性评分，并生成专业的分析报告。

**灵感来源**: 在微服务架构和API-first开发模式下，API版本迭代频繁，手工检查API变更既耗时又容易遗漏。APIChangeGuard 应运而生，帮助开发团队实现API变更的自动化检测与风险管控。

**自研差异化亮点**:
- ✅ **零依赖设计** - 纯Python标准库实现，无需安装任何第三方包
- ✅ **多格式支持** - 原生支持OpenAPI/Swagger、GraphQL、REST API
- ✅ **智能影响分析** - 自动识别破坏性变更并提供迁移建议
- ✅ **CI/CD集成** - 完美支持GitHub Actions、GitLab CI等流水线
- ✅ **多格式报告** - 支持Console、JSON、HTML、SARIF等多种输出格式

### ✨ 核心特性

| 特性 | 描述 | 表情 |
|------|------|------|
| 🔍 **智能Diff检测** | 自动对比API版本差异，精准定位变更点 | ⭐⭐⭐⭐⭐ |
| 📊 **影响分析** | 识别破坏性变更和潜在风险，提供详细影响评估 | ⭐⭐⭐⭐⭐ |
| 📝 **变更分类** | 自动分类新增/修改/删除/废弃四种变更类型 | ⭐⭐⭐⭐ |
| 🎯 **兼容性评分** | 0-100分量化API兼容性健康度 | ⭐⭐⭐⭐⭐ |
| 📈 **趋势追踪** | 历史变更趋势可视化分析 | ⭐⭐⭐⭐ |
| 🔗 **CI/CD集成** | 支持GitHub Actions、GitLab CI等流水线集成 | ⭐⭐⭐⭐⭐ |

### 🚀 快速开始

#### 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows / macOS / Linux
- **依赖**: 零外部依赖，纯标准库实现

#### 安装步骤

```bash
# 方法1: 通过 pip 安装
pip install apichangeguard

# 方法2: 从源码安装
git clone https://github.com/gitstq/APIChangeGuard.git
cd APIChangeGuard
pip install -e .
```

#### 本地启动

```bash
# 比较两个API版本
apichangeguard compare old_api.json new_api.json

# 生成HTML报告
apichangeguard compare old_api.json new_api.json --format html --output report.html

# 验证API定义
apichangeguard validate api.json

# 扫描目录中的API文件
apichangeguard scan ./api_directory --recursive
```

### 📖 详细使用指南

#### 基础用法

```bash
# 比较OpenAPI定义
apichangeguard compare openapi_v1.json openapi_v2.json

# 比较GraphQL Schema
apichangeguard compare schema_v1.graphql schema_v2.graphql

# 生成JSON格式报告
apichangeguard compare old.json new.json --format json --output report.json

# 生成SARIF格式报告 (用于GitHub Advanced Security)
apichangeguard compare old.json new.json --format sarif --output report.sarif
```

#### 进阶用法

```bash
# 检测到破坏性变更时返回非零退出码 (适合CI/CD)
apichangeguard compare old.json new.json --fail-on-breaking

# 设置兼容性评分阈值
apichangeguard compare old.json new.json --threshold 70.0

# 组合使用
apichangeguard compare old.json new.json \
  --format html \
  --output report.html \
  --fail-on-breaking \
  --threshold 80.0
```

#### Python API 使用

```python
from apichangeguard import APIDiffEngine, ImpactAnalyzer
from apichangeguard.parsers import OpenAPIParser

# 解析API定义
parser = OpenAPIParser()
old_api = parser.parse("old_api.json")
new_api = parser.parse("new_api.json")

# 检测变更
diff_engine = APIDiffEngine()
changes = diff_engine.compare(old_api, new_api)

# 分析影响
analyzer = ImpactAnalyzer()
report = analyzer.analyze(changes)

print(f"总变更数: {report.total_changes}")
print(f"破坏性变更: {report.breaking_changes}")
print(f"兼容性评分: {report.compatibility_score}")
```

### 💡 设计思路与迭代规划

#### 设计理念

1. **简洁至上** - 零依赖设计，开箱即用
2. **精准检测** - 基于AST级别的深度对比，不错过任何变更
3. **开发者友好** - 清晰的报告输出，直观的兼容性评分
4. **CI/CD原生** - 专为自动化流水线设计，支持多种退出码策略

#### 技术选型原因

- **纯Python标准库**: 消除依赖冲突，确保长期稳定性
- **插件化架构**: 易于扩展新的API格式支持
- **多格式报告**: 满足不同场景需求 (开发调试、CI集成、安全审计)

#### 后续功能迭代计划

- [ ] **v1.1.0** - 支持AsyncAPI、gRPC协议
- [ ] **v1.2.0** - 智能迁移建议生成
- [ ] **v1.3.0** - Web Dashboard可视化
- [ ] **v2.0.0** - AI驱动的变更影响预测

#### 社区贡献方向

- 添加更多API格式支持
- 完善多语言文档
- 分享使用案例和最佳实践
- 提交Bug报告和功能建议

### 📦 打包与部署指南

#### 作为Python包使用

```bash
# 安装
pip install apichangeguard

# 使用
apichangeguard --help
acg --help  # 短命令别名
```

#### GitHub Actions 集成

```yaml
name: API Change Detection

on:
  pull_request:
    paths:
      - 'api/*.json'

jobs:
  api-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install APIChangeGuard
        run: pip install apichangeguard
      
      - name: Compare API Changes
        run: |
          apichangeguard compare \
            origin/main:api/openapi.json \
            HEAD:api/openapi.json \
            --format sarif \
            --output api-changes.sarif \
            --fail-on-breaking
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: api-changes.sarif
```

#### Docker 使用

```dockerfile
FROM python:3.11-slim

RUN pip install apichangeguard

ENTRYPOINT ["apichangeguard"]
```

```bash
docker build -t apichangeguard .
docker run -v $(pwd):/data apichangeguard compare /data/old.json /data/new.json
```

### 🤝 贡献指南

#### 提交PR规范

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

#### Issue反馈规则

- 使用清晰的标题描述问题
- 提供复现步骤和环境信息
- 附上相关日志和截图
- 标注优先级和严重程度

### 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

## English

### 🎉 Introduction

**APIChangeGuard** is a lightweight intelligent detection tool designed for API version management. It automatically compares API version differences, accurately identifies breaking changes, quantifies compatibility scores, and generates professional analysis reports.

**Inspiration**: In microservice architectures and API-first development, API versions iterate frequently. Manual API change checking is time-consuming and prone to omissions. APIChangeGuard was born to help development teams achieve automated API change detection and risk control.

**Key Differentiators**:
- ✅ **Zero Dependencies** - Pure Python standard library implementation
- ✅ **Multi-Format Support** - Native support for OpenAPI/Swagger, GraphQL, REST API
- ✅ **Intelligent Impact Analysis** - Automatically identifies breaking changes with migration suggestions
- ✅ **CI/CD Integration** - Perfect support for GitHub Actions, GitLab CI pipelines
- ✅ **Multi-Format Reports** - Console, JSON, HTML, SARIF output formats

### ✨ Core Features

| Feature | Description | Rating |
|---------|-------------|--------|
| 🔍 **Smart Diff Detection** | Automatically compare API version differences | ⭐⭐⭐⭐⭐ |
| 📊 **Impact Analysis** | Identify breaking changes and potential risks | ⭐⭐⭐⭐⭐ |
| 📝 **Change Classification** | Auto-classify additions/modifications/deletions/deprecations | ⭐⭐⭐⭐ |
| 🎯 **Compatibility Score** | 0-100 quantitative API compatibility health score | ⭐⭐⭐⭐⭐ |
| 📈 **Trend Tracking** | Historical change trend visualization | ⭐⭐⭐⭐ |
| 🔗 **CI/CD Integration** | GitHub Actions, GitLab CI pipeline support | ⭐⭐⭐⭐⭐ |

### 🚀 Quick Start

#### Requirements

- **Python**: 3.8 or higher
- **OS**: Windows / macOS / Linux
- **Dependencies**: Zero external dependencies

#### Installation

```bash
# Method 1: Install via pip
pip install apichangeguard

# Method 2: Install from source
git clone https://github.com/gitstq/APIChangeGuard.git
cd APIChangeGuard
pip install -e .
```

#### Basic Usage

```bash
# Compare two API versions
apichangeguard compare old_api.json new_api.json

# Generate HTML report
apichangeguard compare old_api.json new_api.json --format html --output report.html

# Validate API definition
apichangeguard validate api.json

# Scan directory for API files
apichangeguard scan ./api_directory --recursive
```

### 📖 Detailed Usage Guide

```bash
# Compare OpenAPI definitions
apichangeguard compare openapi_v1.json openapi_v2.json

# Compare GraphQL Schemas
apichangeguard compare schema_v1.graphql schema_v2.graphql

# Generate JSON report
apichangeguard compare old.json new.json --format json --output report.json

# Generate SARIF report (for GitHub Advanced Security)
apichangeguard compare old.json new.json --format sarif --output report.sarif
```

### 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 繁體中文

### 🎉 專案介紹

**APIChangeGuard** 是一款專為API版本管理設計的輕量級智能檢測工具。它能夠自動對比API版本差異，精準識別破壞性變更，量化相容性評分，並生成專業的分析報告。

**核心特色**:
- ✅ **零依賴設計** - 純Python標準庫實現
- ✅ **多格式支援** - 原生支援OpenAPI/Swagger、GraphQL、REST API
- ✅ **智能影響分析** - 自動識別破壞性變更並提供遷移建議
- ✅ **CI/CD整合** - 完美支援GitHub Actions、GitLab CI等流水線
- ✅ **多格式報告** - 支援Console、JSON、HTML、SARIF等多種輸出格式

### 🚀 快速開始

#### 安裝

```bash
pip install apichangeguard
```

#### 基本用法

```bash
# 比較兩個API版本
apichangeguard compare old_api.json new_api.json

# 生成HTML報告
apichangeguard compare old_api.json new_api.json --format html --output report.html
```

### 📄 開源協議

本專案採用 [MIT License](LICENSE) 開源協議。

---

<div align="center">

**Made with ❤️ by APIChangeGuard Team**

[Report Bug](https://github.com/gitstq/APIChangeGuard/issues) · [Request Feature](https://github.com/gitstq/APIChangeGuard/issues)

</div>
