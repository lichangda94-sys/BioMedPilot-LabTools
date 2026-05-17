# BioMedPilot-LabTools / 医研智析实验工具模块

BioMedPilot-LabTools 是 **BioMedPilot / 医研智析** 的开源实验工具模块。

本仓库是一个独立的 Python package，提供本地化、可测试、可复核的实验室计算工具和生物医学科研辅助工具。当前模块主要包括通用实验计算器、试剂模板、Western Blot 相关计算、BCA 辅助计算、SDS-PAGE 胶配制辅助、qPCR mix 计算和细胞铺板计算等。

本项目面向医学科研人员、博士生、临床研究者、实验室用户和开发者。

## 当前状态

Developer Preview / 开发预览版。

当前代码已经作为独立公开包整理，支持本地安装、测试和 smoke test。

当前验证状态：

```bash
pytest
python -m labtools --smoke-test
```

最近公开包验证结果：

```text
pytest: 124 passed
python -m labtools --smoke-test: passed
```

## 功能范围

当前已包含或已整理的主要方向包括：

- 通用实验计算器
- 浓度计算
- 稀释计算
- 溶液配制计算
- 计算记录模型
- 试剂模板 models / calculator / store
- Western Blot loading calculator
- Western Blot protein loading helpers
- BCA assay helper
- SDS-PAGE gel template helper
- qPCR mix calculator
- Cell seeding calculator
- 单位换算工具
- package smoke test
- 测试用例

## 安装与开发

克隆仓库：

```bash
git clone https://github.com/lichangda94-sys/BioMedPilot-LabTools.git
cd BioMedPilot-LabTools
```

创建虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

安装开发依赖：

```bash
pip install -e ".[dev]"
```

运行测试：

```bash
pytest
```

运行 smoke test：

```bash
python -m labtools --smoke-test
```

## 项目结构

当前公开包结构大致如下：

```text
BioMedPilot-LabTools/
  labtools/
    __init__.py
    __main__.py
    calculators/
    reagent_templates/
    western_blot/
    pcr_qpcr/
    cell_culture/
    elisa/
    shared/

  tests/
    test_*.py

  README.md
  README_zh.md
  CONTRIBUTING.md
  SECURITY.md
  LICENSE
  pyproject.toml
```

## 适合贡献的方向

欢迎以下类型的贡献：

- 报告 bug
- 改进文档
- 补充测试
- 审核公式
- 添加试剂模板
- 添加示例计算
- 优化中英文文案
- 改进单位换算
- 改进验证和警告规则
- 新增实验计算器
- 提供非机密的实验流程反馈

你不需要是专业程序员也可以参与。医学科研人员、博士生、实验室用户和文档贡献者都可以通过问题反馈、公式检查、文档改进和示例补充参与项目。

## 适合新手的任务

适合新手的任务包括：

- 添加 PBS 试剂模板示例
- 添加 TBS / TBST 模板
- 添加 RIPA buffer 模板
- 改进 Western Blot 使用说明
- 添加 BCA 示例数据
- 添加 qPCR 计算示例
- 添加细胞铺板计算示例
- 改进 README
- 增加测试用例
- 检查公式和单位说明

更多新手任务可以放在：

```text
docs/good_first_issues.md
```

## 设计原则

BioMedPilot-LabTools 遵循以下原则：

- 本地优先：尽量在本地完成计算和数据处理。
- 公式透明：用户应该能够理解结果是如何计算出来的。
- 必须人工复核：工具只辅助研究者，不能替代实验判断。
- 计算逻辑可测试：核心计算应尽量有单元测试覆盖。
- 符合实验习惯：工具设计应尽量贴近真实实验室工作流程。
- 模块化设计：每个计算器应尽量独立、可维护、可测试。
- 安全边界清晰：本项目不提供临床诊断、治疗建议或受监管医疗决策。

## 与 BioMedPilot 的关系

BioMedPilot-LabTools 是 BioMedPilot / 医研智析 的开源实验工具模块。

本仓库可以作为独立的开源科研工具使用，也可能被集成进 BioMedPilot 及其相关版本中，包括免费版、商业版、AI 辅助版、高级版、云端版或未来版本。

本仓库不包含 BioMedPilot 私有商业模块，例如：

- 会员系统
- 支付系统
- 授权服务器
- 云端 AI 服务
- 私有 prompt
- 商业报告模板
- 私有主程序壳
- 用户数据或测试反馈后台

## 贡献条款

所有贡献均为自愿贡献。

当你向本仓库提交 Issue、Pull Request、代码、文档、设计、测试用例、公式、模板、示例或其他内容时，即表示你同意你的贡献按照本仓库相同许可证进行授权。

提交贡献不代表与项目所有者形成雇佣、外包、合伙、报酬、股权、所有权或收入分成关系。

项目维护者可以使用、修改、分发、再授权，并将已接受的贡献集成到 BioMedPilot 及其相关版本中，包括免费版、商业版、AI 辅助版、云端版、高级版或未来版本。

## 非临床用途声明

BioMedPilot-LabTools 用于生物医学科研辅助、实验流程支持、教学和软件开发预览。

本项目不用于：

- 临床诊断
- 治疗决策
- 患者管理
- 受监管医疗用途
- 无人工审核的自动实验执行
- 替代实验室 SOP 或机构规范
- 替代研究者判断

用户在使用前应自行复核所有计算结果、公式、单位、警告和实验条件。

## 许可证

本项目采用 Apache License 2.0。

详情见 LICENSE 文件。
