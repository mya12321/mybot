#!/usr/bin/env python3
"""
图片生成脚本 - 使用阶跃星辰(StepFun) step-2x-large 模型
支持文生图和图生图功能
"""

import os
import sys
import json
import base64
import argparse
import urllib.request
from datetime import datetime
from typing import Optional

try:
    import requests
except ImportError:
    print("错误: 请先安装 requests 库: pip install requests")
    sys.exit(1)


class StepFunImageGenerator:
    """阶跃星辰图片生成器"""
    
    BASE_URL = "https://api.stepfun.com/v1"
    MODEL = "step-2x-large"
    
    # 支持的图片尺寸
    VALID_SIZES = ["256x256", "512x512", "768x768", "1024x1024", "1280x800", "800x1280"]
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化生成器
        
        Args:
            api_key: 阶跃星辰API Key，如果不提供则从环境变量获取
        """
        self.api_key = api_key or os.environ.get("STEPFUN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "请提供API Key或通过环境变量 STEPFUN_API_KEY 设置"
            )
    
    def _make_request(self, endpoint: str, data: dict) -> dict:
        """
        发送API请求
        
        Args:
            endpoint: API端点
            data: 请求数据
            
        Returns:
            API响应数据
        """
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json() if e.response.text else {}
            error_msg = error_data.get("error", {}).get("message", str(e))
            raise Exception(f"API请求失败: {error_msg}")
        except Exception as e:
            raise Exception(f"请求异常: {str(e)}")
    
    def _download_image(self, image_url: str, output_path: str):
        """
        下载图片到本地
        
        Args:
            image_url: 图片URL
            output_path: 保存路径
        """
        try:
            urllib.request.urlretrieve(image_url, output_path)
        except Exception as e:
            raise Exception(f"图片下载失败: {str(e)}")
    
    def generate(
        self,
        prompt: str,
        output_path: str = "generated_image.png",
        size: str = "1024x1024",
        n: int = 1
    ) -> str:
        """
        文生图 - 根据文本描述生成图片
        
        Args:
            prompt: 图片生成提示词（建议使用英文）
            output_path: 输出图片路径
            size: 图片尺寸，可选 1024x1024, 1024x1536, 1536x1024
            n: 生成图片数量（1-4）
            
        Returns:
            生成的图片路径
        """
        if size not in self.VALID_SIZES:
            raise ValueError(f"不支持的尺寸: {size}，请使用: {', '.join(self.VALID_SIZES)}")
        
        if not 1 <= n <= 4:
            raise ValueError("n 必须在 1-4 之间")
        
        data = {
            "model": self.MODEL,
            "prompt": prompt,
            "n": n,
            "size": size
        }
        
        print(f"正在生成图片...")
        print(f"提示词: {prompt[:100]}...")
        print(f"尺寸: {size}")
        
        result = self._make_request("images/generations", data)
        
        # 下载图片
        image_url = result["data"][0]["url"]
        self._download_image(image_url, output_path)
        
        print(f"图片已保存: {output_path}")
        return output_path
    
    def edit(
        self,
        image_path: str,
        prompt: str,
        output_path: str = "edited_image.png",
        size: str = "1024x1024",
        n: int = 1
    ) -> str:
        """
        图生图 - 根据输入图片和描述生成新图片
        
        Args:
            image_path: 输入图片路径
            prompt: 编辑提示词（建议使用英文）
            output_path: 输出图片路径
            size: 图片尺寸
            n: 生成图片数量（1-4）
            
        Returns:
            生成的图片路径
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        if size not in self.VALID_SIZES:
            raise ValueError(f"不支持的尺寸: {size}，请使用: {', '.join(self.VALID_SIZES)}")
        
        if not 1 <= n <= 4:
            raise ValueError("n 必须在 1-4 之间")
        
        # 读取图片并转为base64
        with open(image_path, "rb") as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        # 检测图片格式
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"
        
        data = {
            "model": self.MODEL,
            "image": f"data:{mime_type};base64,{image_base64}",
            "prompt": prompt,
            "n": n,
            "size": size
        }
        
        print(f"正在编辑图片...")
        print(f"输入图片: {image_path}")
        print(f"提示词: {prompt[:100]}...")
        
        result = self._make_request("images/edits", data)
        
        # 下载图片
        image_url = result["data"][0]["url"]
        self._download_image(image_url, output_path)
        
        print(f"编辑后的图片已保存: {output_path}")
        return output_path


def save_prompt_to_file(
    original_prompt: str,
    optimized_prompt: str,
    output_dir: str = "."
) -> str:
    """
    将prompt保存到markdown文件
    
    Args:
        original_prompt: 用户原始输入
        optimized_prompt: 优化后的prompt
        output_dir: 输出目录
        
    Returns:
        保存的文件路径
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"prompt_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)
    
    content = f"""# Image Generation Prompt

## 生成时间
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 用户原始描述
{original_prompt}

## 优化后的Prompt
```
{optimized_prompt}
```

## Prompt要素分析
- **主体**: 
- **环境**: 
- **风格**: 
- **光线**: 
- **质量**: 
- **氛围**: 

## 生成参数
- 模型: step-2x-large
- 尺寸: 1024x1024
- 数量: 1
"""
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Prompt已保存: {filepath}")
    return filepath


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="使用阶跃星辰API生成图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 文生图
  python generate_image.py -p "A beautiful sunset over mountains"
  
  # 图生图
  python generate_image.py -i input.png -p "Transform into watercolor style"
  
  # 指定输出路径和尺寸
  python generate_image.py -p "A cute cat" -o mycat.png -s 1024x1536
        """
    )
    
    parser.add_argument(
        "-p", "--prompt",
        required=True,
        help="图片生成提示词（建议使用英文）"
    )
    parser.add_argument(
        "-i", "--image",
        help="输入图片路径（用于图生图）"
    )
    parser.add_argument(
        "-o", "--output",
        default="generated_image.png",
        help="输出图片路径（默认: generated_image.png）"
    )
    parser.add_argument(
        "-s", "--size",
        default="1024x1024",
        choices=["1024x1024", "1024x1536", "1536x1024"],
        help="图片尺寸（默认: 1024x1024）"
    )
    parser.add_argument(
        "-n",
        type=int,
        default=1,
        help="生成数量 1-4（默认: 1）"
    )
    parser.add_argument(
        "--save-prompt",
        action="store_true",
        help="是否保存prompt到markdown文件"
    )
    parser.add_argument(
        "--original-prompt",
        help="用户原始描述（用于保存prompt文件）"
    )
    parser.add_argument(
        "--api-key",
        help="阶跃星辰API Key（默认从环境变量 STEPFUN_API_KEY 获取）"
    )
    
    args = parser.parse_args()
    
    try:
        # 初始化生成器
        generator = StepFunImageGenerator(api_key=args.api_key)
        
        # 保存prompt到文件
        if args.save_prompt:
            original = args.original_prompt or args.prompt
            save_prompt_to_file(original, args.prompt)
        
        # 生成图片
        if args.image:
            # 图生图
            generator.edit(
                image_path=args.image,
                prompt=args.prompt,
                output_path=args.output,
                size=args.size,
                n=args.n
            )
        else:
            # 文生图
            generator.generate(
                prompt=args.prompt,
                output_path=args.output,
                size=args.size,
                n=args.n
            )
        
        print("✓ 完成!")
        
    except Exception as e:
        print(f"✗ 错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
