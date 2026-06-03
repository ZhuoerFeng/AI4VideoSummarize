# AI4VideoSummarize 开发方案

## 项目概述

利用 Video LLM 对带讲话/演讲的视频（中英文）进行自动转录（transcript）和摘要（summary）。

## 核心功能

1. **视频输入**：支持本地路径、直接 URL、Bilibili 链接、YouTube 链接
2. **自动转录**：调用 Video LLM API 对视频音频内容进行语音转文字
3. **自动摘要**：对转录文本进行智能摘要
4. **输出管理**：为每次任务创建独立输出目录，保存 transcript、summary 及中间文件

## 技术选型

| 组件 | 方案 |
|------|------|
| 语言 | Python 3.10+ |
| 视频下载 | yt-dlp（支持 YouTube、Bilibili 等） |
| 音频提取 | ffmpeg |
| 语音转文字 | OpenAI Whisper API（兼容接口） |
| 文本摘要 | LLM API（OpenAI 兼容接口） |
| 配置管理 | YAML 配置文件 |
| CLI | argparse |

## 项目结构

```
AI4VideoSummarize/
├── config.yaml              # 配置文件（API keys, base URLs）
├── config.yaml.example      # 配置文件模板
├── main.py                  # CLI 入口
├── src/
│   ├── __init__.py
│   ├── config.py            # 配置加载
│   ├── downloader.py        # 视频下载（yt-dlp）
│   ├── audio_extractor.py   # 音频提取（ffmpeg）
│   ├── transcriber.py       # 语音转文字（Whisper API）
│   ├── summarizer.py        # 文本摘要（LLM API）
│   └── pipeline.py          # 主流程编排
├── output/                  # 默认输出目录
├── requirements.txt
├── develop.md
└── README.md
```

## 配置文件设计 (config.yaml)

```yaml
whisper:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-xxx"
  model: "whisper-1"

llm:
  base_url: "https://api.openai.com/v1"
  api_key: "sk-xxx"
  model: "gpt-4o"

output:
  base_dir: "./output"

download:
  proxy: ""  # 可选代理
  cookies_file: ""  # 可选 cookies 文件路径
```

## 处理流程

```
输入 (路径/URL/视频站链接)
    │
    ▼
[1] 视频获取
    ├── 本地文件 → 直接使用
    └── URL/视频站 → yt-dlp 下载
    │
    ▼
[2] 音频提取
    └── ffmpeg 提取音频 (mp3/wav)
    │
    ▼
[3] 语音转录
    └── Whisper API 转文字 → transcript.txt
    │
    ▼
[4] 文本摘要
    └── LLM API 生成摘要 → summary.txt
    │
    ▼
输出目录结构:
    output/<task_id>/
    ├── video.*          # 原始/下载的视频（可选保留）
    ├── audio.mp3        # 提取的音频
    ├── transcript.txt   # 转录文本
    ├── transcript.srt   # 带时间戳的字幕（如API支持）
    └── summary.txt      # 摘要
```

## CLI 使用设计

```bash
# 本地视频
python main.py /path/to/video.mp4

# YouTube
python main.py "https://www.youtube.com/watch?v=xxxxx"

# Bilibili
python main.py "https://www.bilibili.com/video/BVxxxxx"

# 指定输出目录
python main.py --output ./my_output "https://..."

# 指定配置文件
python main.py --config ./my_config.yaml "https://..."

# 仅转录不摘要
python main.py --no-summary "https://..."
```

## 开发计划

1. **Phase 1**: 项目骨架 — 配置管理、CLI 入口、目录结构
2. **Phase 2**: 视频下载 — yt-dlp 集成，支持 YouTube/Bilibili/直接 URL
3. **Phase 3**: 音频提取 — ffmpeg 提取音频
4. **Phase 4**: 语音转录 — Whisper API 调用，支持长音频分片
5. **Phase 5**: 文本摘要 — LLM API 调用，支持长文本分段摘要
6. **Phase 6**: 流程串联 — pipeline 编排，错误处理
7. **Phase 7**: 文档完善 — README、使用示例

## 注意事项

- 长视频音频需分片上传（Whisper API 限制 25MB）
- 支持断点续传/跳过已完成步骤
- 敏感信息（API key）不入版本控制
- 输出文件使用 UTF-8 编码
