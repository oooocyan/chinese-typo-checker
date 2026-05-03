# 中文错别字检查工具

一个基于 Streamlit 的中文错别字检查工具，支持自动场景识别和上下文语义检验。

## 功能特点

- **全面检测**：错别字、标点符号、语法问题、语义问题
- **自动场景识别**：自动识别文本类型（剧本/小说/散文）和表达风格（口语化/书面化）
- **上下文语义检验**：结合语境判断"的地得"等易混淆用法
- **交互式界面**：点击定位、一键应用、快速忽略
- **长文本支持**：最大支持一万字中文

## 快速开始

### 1. 安装依赖

```bash
cd typo_checker
pip install -r requirements.txt
```

### 2. 本地运行

```bash
streamlit run app.py
```

### 3. 使用方法

1. 在左侧文本框粘贴你的文本
2. 点击"开始检查"按钮
3. 查看右侧检测结果
4. 点击"应用"自动修正，或点击"忽略"跳过

## 项目结构

```
typo_checker/
├── app.py               # Streamlit 主入口
├── config.py            # 配置文件
├── requirements.txt     # 依赖清单
├── checker/             # 检测模块
│   ├── typo.py          # 错别字检测
│   ├── punctuation.py   # 标点检查
│   ├── grammar.py       # 语法检查
│   └── context.py       # 上下文语义检验
├── ai/                  # AI 模块
│   ├── optimizer.py     # AI 优化建议
│   └── semantic.py      # 语义分析
├── scene/               # 场景识别
│   ├── detector.py      # 自动场景识别
│   ├── script.py        # 剧本场景规则
│   ├── novel.py         # 小说场景规则
│   └── rules.py         # 口语/书面语规则
├── data/                # 数据文件
│   ├── typos.json       # 错别字词典
│   ├── confusion.json   # 易混淆词对
│   └── scene_rules.json # 场景规则配置
└── utils/               # 工具函数
    ├── text_utils.py    # 文本处理工具
    └── chunker.py       # 长文本分段处理
```

## 部署到 Streamlit Cloud

### 1. 创建 GitHub 仓库

将整个 `typo_checker` 目录推送到 GitHub。

### 2. 部署

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 连接你的 GitHub 账号
3. 选择仓库和 `app.py` 文件
4. 点击 Deploy

### 3. 配置 API Key（可选）

如果需要使用 AI 优化建议功能：

1. 在 Streamlit Cloud 的 Settings → Secrets 中添加：
```
DASHSCOPE_API_KEY = "your-api-key"
```

## 检测类型说明

| 类型 | 颜色 | 说明 |
|------|------|------|
| 错别字 | 红色 | 同音字、形近字、易混淆词等 |
| 标点 | 橙色 | 中英文标点混用、标点缺失、配对错误等 |
| 语法 | 蓝色 | 冗余表达、重复词语、语法错误模式等 |
| 语义 | 紫色 | 人称不一致、时态混乱、口语化表达等 |
| AI建议 | 绿色 | AI 提供的润色建议（需配置 API Key） |

## 扩展词典

可以编辑 `data/typos.json` 文件添加自定义的错别字词典：

```json
{
  "错误词": {
    "correct": "正确词",
    "type": "错误类型",
    "example": "示例"
  }
}
```

## 许可证

MIT License
