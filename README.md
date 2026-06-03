# AI4VideoSummarize

自动视频转录与摘要工具。利用 Whisper API 进行语音转文字，LLM API 进行智能摘要，支持中英文视频。

## 功能特性

- **多源输入**：本地视频文件、YouTube 链接、Bilibili 链接、直接视频 URL
- **语音转录**：基于 Whisper API，支持中英文自动识别
- **智能摘要**：基于 LLM API，自动提取关键信息并生成结构化摘要
- **长视频支持**：自动分片处理超大音频文件
- **断点恢复**：支持从中断的任务目录恢复处理，自动跳过已完成步骤
- **灵活配置**：YAML 配置文件管理 API 地址和密钥，支持环境变量覆盖

## 环境要求

- Python 3.10+
- ffmpeg（音频提取）
- 网络可访问的 Whisper API 和 LLM API

## 安装

```bash
# 克隆项目
git clone <repo-url>
cd AI4VideoSummarize

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 ffmpeg（如尚未安装）
# Ubuntu/Debian:
sudo apt install ffmpeg
# macOS:
brew install ffmpeg
```

## 配置

1. 复制配置模板：

```bash
cp config.yaml.example config.yaml
```

2. 编辑 `config.yaml`，填入你的 API 信息：

```yaml
whisper:
  base_url: "https://api.openai.com/v1"   # Whisper API 地址
  api_key: "sk-your-key"                   # Whisper API Key
  model: "whisper-1"                        # 模型名称

llm:
  base_url: "https://api.openai.com/v1"   # LLM API 地址
  api_key: "sk-your-key"                   # LLM API Key
  model: "gpt-4o"                           # 模型名称

output:
  base_dir: "./output"                      # 默认输出目录

download:
  proxy: ""                                 # 代理地址（可选）
  cookies_file: ""                          # Cookies 文件路径（可选）
```

你也可以通过环境变量覆盖 API 配置：

```bash
export WHISPER_API_KEY="sk-xxx"
export WHISPER_BASE_URL="https://your-whisper-api.com/v1"
export LLM_API_KEY="sk-xxx"
export LLM_BASE_URL="https://your-llm-api.com/v1"
```

## 使用方法

### 基本用法

```bash
# 处理本地视频
python main.py /path/to/video.mp4

# 处理 YouTube 视频
python main.py "https://www.youtube.com/watch?v=3cRgQ9ohxYQ"

# 处理 Bilibili 视频
python main.py "https://www.bilibili.com/video/BV1xx411c7mD"

# 处理直接视频 URL
python main.py "https://example.com/video.mp4"
```

### 恢复处理

如果之前的处理中断，可以使用 `--resume` 从已有的任务目录恢复：

```bash
# 从已有目录恢复（自动检测进度并继续）
python main.py --resume ./output/20240101_120000_video_title
```

工具会自动检测目录中已有的文件（视频、音频、转录文本、摘要），跳过已完成的步骤，从中断处继续执行。

### 可选参数

```bash
# 指定配置文件
python main.py --config ./my_config.yaml "https://..."

# 指定输出目录
python main.py --output ./my_results "https://..."

# 仅转录，不生成摘要
python main.py --no-summary "https://..."

# 处理完成后不保留视频文件
python main.py --no-keep-video "https://..."
```

### 完整参数列表

| 参数 | 缩写 | 说明 |
|------|------|------|
| `source` | - | 视频来源（与 `--resume` 二选一）：本地路径、URL、YouTube/Bilibili 链接 |
| `--resume` | `-r` | 从已有任务目录恢复处理（与 `source` 二选一） |
| `--config` | `-c` | 配置文件路径，默认 `./config.yaml` |
| `--output` | `-o` | 输出基础目录，默认从配置文件读取 |
| `--no-summary` | - | 跳过摘要生成，仅执行转录 |
| `--no-keep-video` | - | 处理完成后删除视频文件 |

## 输出结构

每次运行会在输出目录下创建一个以时间戳命名的子目录：

```
output/
└── 20240101_120000_video_title/
    ├── video.mp4          # 下载/复制的视频文件
    ├── audio.mp3          # 提取的音频
    ├── transcript.txt     # 转录文本
    ├── transcript.srt     # 带时间戳的字幕（如支持）
    └── summary.txt        # 摘要文本
```

例如，执行下面的命令

```bash
python main.py "https://www.youtube.com/watch?v=3cRgQ9ohxYQ"
```

最后会得到如下的摘要：

```markdown
## 主题
本视频总结“如何为钢琴演出做准备”：从作品学习、分段练习，到模拟演出与正式上台前的心理建设。

## 关键方法
作者先回顾前两期：决定是否背谱、研究作品背景、分析结构与音型，再进入“深度学习”。核心是“三个S”：**慢练**、**分开练**、**分段练**，避免工作记忆超载。分开练不只左右手分练，还可做“zigzag”交错练习；配合“控制停顿”检查音高、节奏、指法、力度、风格，以及“听起来/弹起来是否舒服”。

## 重要细节
以斯卡拉蒂奏鸣曲K513末段为例，强调边练边修正薄弱点。演出准备要**设定明确截止日期**，避免帕金森定律拖延。建议正式演出前至少**6周达到完整熟练**，并安排**3次模拟run-through**，最好在陌生钢琴、陌生环境、面对安全观众进行。

## 演出流程与结论
每次模拟后要**反思**：记录成功之处与问题点，再做针对性“spot practice”，连续一周效果佳，之后进入维护练习，如慢练、记忆强化。正式演出前保持积极暗示，如“我已准备充分，也值得享受演出”。结论是：演出中不要执着于错音，重点是**传达音乐、投入激情**；若演奏者享受演出，观众也会感受到。
```


## 支持的 API

本工具使用 OpenAI 兼容的 API 接口，因此你可以使用：

- **Whisper API**：OpenAI 官方、Azure OpenAI、或任何兼容 `/v1/audio/transcriptions` 接口的服务
- **LLM API**：OpenAI 官方、Azure OpenAI、或任何兼容 `/v1/chat/completions` 接口的服务（如 DeepSeek、通义千问等）

## 注意事项

- Bilibili 或部分视频网站可能需要提供 cookies 才能下载，请在配置文件中设置 `cookies_file`
- 如需代理访问 YouTube，请在配置文件中设置 `proxy`
- `config.yaml` 包含敏感信息（API Key），已在 `.gitignore` 中排除
- 长视频会自动分片处理，但可能需要较长时间

## 项目结构

```
AI4VideoSummarize/
├── main.py                  # CLI 入口
├── config.yaml.example      # 配置模板
├── requirements.txt         # Python 依赖
├── develop.md               # 开发文档
├── src/
│   ├── __init__.py
│   ├── config.py            # 配置加载
│   ├── downloader.py        # 视频下载
│   ├── audio_extractor.py   # 音频提取
│   ├── transcriber.py       # 语音转录
│   ├── summarizer.py        # 文本摘要
│   └── pipeline.py          # 流程编排
└── output/                  # 默认输出目录
```

## License

MIT
