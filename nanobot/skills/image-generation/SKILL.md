---
name: image-generation
description: Generate images using StepFun's step-2x-large model. Use when users ask to generate images, create pictures from text descriptions, or modify existing images. Supports both text-to-image and image-to-image generation.
homepage: https://platform.stepfun.com/docs/zh/api-reference/images/image
metadata: {"nanobot":{"emoji":"🎨","requires":{"bins":["python3"],"env":["STEPFUN_API_KEY"]},"install":[{"id":"pip","kind":"pip","packages":["requests"],"label":"Install requests library"}]}}
---

# Image Generation

使用阶跃星辰（StepFun）的 step-2x-large 模型生成图片。支持文生图和图生图两种模式。

## 环境变量

| 变量 | 用途 | 必需 |
|---|---|---|
| `STEPFUN_API_KEY` | 阶跃星辰 API Key | 是 |

## 工作流程

1. **优化Prompt**：根据用户的简单描述，生成一份详细的英文生图Prompt
2. **保存Prompt**：使用 WriteFileTool 将优化后的Prompt写入md文件
3. **生成图片**：调用Python脚本使用阶跃星辰API生成图片

# Prompt优化指南

当用户提供简单的图片描述时，应该将其扩展为详细的英文Prompt, 需注意prompt最多为1024个字符：

## 示例

**用户输入**: "一只可爱的猫咪"

**优化后的Prompt**:
```
A cute fluffy kitten with big round eyes, sitting on a soft cushion, warm sunlight streaming through a window, cozy indoor setting, highly detailed fur texture, photorealistic style, 8k quality, soft bokeh background
```

**用户输入**: "未来城市"

**优化后的Prompt**:
```
A futuristic cyberpunk cityscape at night, towering neon-lit skyscrapers, flying vehicles between buildings, holographic advertisements, rain-slicked streets reflecting colorful lights, dystopian atmosphere, cinematic composition, highly detailed, 8k resolution, digital art style
```

## Prompt要素

一个好的生图Prompt应包含：
1. **主体** - 主要对象或场景
2. **环境** - 背景、场景设置
3. **风格** - 艺术风格（写实、动漫、油画等）
4. **光线** - 光照条件
5. **质量** - 画质描述（highly detailed, 8k, masterpiece等）
6. **氛围** - 情感、色调

# 调用脚本生成图片

## 文生图脚本调用

```bash
python3 skills/image-generation/scripts/image_generation.py --model "step-2x-large" --promptFile "prompt.md" --outputFile "garden_puppy.png" --size "800x1280"
```

## 图生图脚本调用

```bash
python3 skills/image-generation/scripts/image_generation.py --model "step-2x-large" --promptFile "prompt.md" --outputFile "garden_puppy.png" --sourceFile "source.png" --size "1024x1024"
```

## 脚本参数说明

| 参数 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `model` | string | 是 | 模型名称，当前固定为 `step-2x-large` |
| `promptFile` | string | 是 | 图片描述文件路径, 格式为Markdown |
| `outputFile` | string | 是 | 生成图片的文件路径, 必须是.png文件 |
| `sourceFile` | string | 否 | 图生图的源图文件路径 |
| `size` | string | 否 | 图片尺寸，默认1024x1024 |

## 图片支持的尺寸
- `256x256, 512x512, 768x768, 1024x1024` - 正方形, 默认为1024x1024
- `800x1280` - 竖屏
- `1280x800` - 横屏

## 错误处理

常见错误码：
- `400` - 请求参数错误
- `401` - API Key无效
- `429` - 请求过于频繁
- `500` - 服务器内部错误

# 注意事项

1. Prompt建议使用英文，可以获得更好的生成效果
2. 生成图片可能受内容政策限制
