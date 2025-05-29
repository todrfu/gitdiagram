# GitDiagram 多AI模型支持

GitDiagram 现已支持多种 AI 模型，让用户可以根据自己的需求和偏好选择不同的 AI 平台生成图表。

## 支持的 AI 平台

目前支持以下 AI 平台：

| 平台 | 模型 | 说明 |
|------|------|------|
| OpenAI | o3-mini, o4-mini | OpenAI 的模型，o3-mini 为默认模型 |
| Claude | claude-3-5-sonnet | Anthropic 提供的 Claude AI 模型 |
| DeepSeek | deepseek-chat | DeepSeek 提供的 AI 模型 |

## 配置方法

### 后端配置

在后端 `.env` 文件中，可以配置以下变量：

```bash
# 默认 AI 平台配置
DEFAULT_AI_PLATFORM=openai  # 可选: openai, claude, deepseek
DEFAULT_AI_MODEL=o3-mini    # 根据平台不同选择相应模型
DEFAULT_REASONING_EFFORT=medium  # 推理努力程度: low, medium, high

# 各平台 API 密钥
OPENAI_API_KEY=your_openai_api_key
CLAUDE_API_KEY=your_claude_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
```

### 推理努力程度

对于不同的需求，可以设置不同的推理努力程度：

- `low`：低 - 速度更快，但质量可能较低
- `medium`：中 - 平衡速度和质量
- `high`：高 - 质量更好，但速度较慢

推理努力程度会根据不同平台转换为相应的参数（如温度值）。

## 使用方式

### 前端选择 AI 平台

在生成图表时，用户可以：

1. 在 API 密钥设置弹窗中选择 AI 平台
2. 提供对应平台的 API 密钥
3. 系统将使用选定的平台生成图表

### 支持的 Git 平台

除了多 AI 模型支持外，GitDiagram 还支持多种 Git 平台：

- GitHub
- GitLab
- Gitea

用户可以在主页上从下拉菜单中选择平台，并输入相应的仓库 URL。