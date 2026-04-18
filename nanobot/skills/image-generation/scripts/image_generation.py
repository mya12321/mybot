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
import mimetypes
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
    
    def _save_image(self, image_b64: str, output_path: str):
        """
        将base64的图片保存成图片文件
        
        Args:
            image_b64: 图片base64编码字符串
            output_path: 保存路径
        """
        try:
            image_data = base64.b64decode(image_b64)
            with open(output_path, "wb") as f:
                f.write(image_data)
        except Exception as e:
            raise Exception(f"保存图片失败: {str(e)}")

    
    def text_to_image(
        self,
        model: str,
        prompt: str,
        output_path: str = "generated_image.png",
        size: str = "1024x1024"
    ) -> str:
        """
        文生图 - 根据文本描述生成图片
        
        Args:
            prompt: 图片生成提示词（建议使用英文）
            output_path: 输出图片路径
            size: 图片尺寸
            
        Returns:
            生成的图片路径
        """
        if size not in self.VALID_SIZES:
            raise ValueError(f"不支持的尺寸: {size}，请使用: {', '.join(self.VALID_SIZES)}")
        
        data = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "response_format": "b64_json",
            "size": size
        }
        
        print(f"正在生成图片...")
        print(f"提示词: {prompt[:80]}...")
        print(f"尺寸: {size}")
        
        result = self._make_request("images/generations", data)
        
        image_b64 = result["data"][0]["b64_json"]
        self._save_image(image_b64, output_path)
        
        print(f"图片已保存: {output_path}")
        return output_path
    
    def image_to_image(
        self,
        model: str,
        source_image_path: str,
        prompt: str,
        output_path: str = "edited_image.png",
        size: str = "1024x1024"
    ) -> str:
        """
        图生图 - 根据输入图片和描述生成新图片
        
        Args:
            source_image_path: 输入图片路径
            prompt: 编辑提示词（建议使用英文）
            output_path: 输出图片路径
            size: 图片尺寸
            
        Returns:
            生成的图片路径
        """
        if not os.path.exists(source_image_path):
            raise FileNotFoundError(f"源图片不存在: {source_image_path}")
        
        if size not in self.VALID_SIZES:
            raise ValueError(f"不支持的尺寸: {size}，请使用: {', '.join(self.VALID_SIZES)}")
        
        with open(source_image_path, "rb") as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        mime_type, _ = mimetypes.guess_type(source_image_path)
               
        data = {
            "model": model,
            "source_url": f"data:{mime_type};base64,{image_base64}",
            "source_weight": 0.5,
            "prompt": prompt,
            "n": 1,
            "response_format": "b64_json",
            "size": size
        }
        
        print(f"正在生成图片...")
        print(f"输入图片: {source_image_path}")
        print(f"提示词: {prompt[:80]}...")
        
        result = self._make_request("images/image2image", data)
        
        image_b64 = result["data"][0]["b64_json"]
        self._save_image(image_b64, output_path)
        
        print(f"编辑后的图片已保存: {output_path}")
        return output_path


def read_prompt_file(prompt_file: str) -> str:
    """
    读取prompt文件内容
    
    Args:
        prompt_file: prompt文件路径
        
    Returns:
        prompt内容
    """
    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Prompt文件不存在: {prompt_file}")
    
    with open(prompt_file, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.strip()
    if len(content) > 1024:
        raise ValueError("Prompt内容最多为1024个字符")
    
    return content


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="使用阶跃星辰API生成图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 文生图
  python image_generation.py --model "step-2x-large" --promptFile "prompt.md" --outputFile "garden_puppy.png" --size "800x1280"
  
  # 图生图
  python image_generation.py --model "step-2x-large" --promptFile "prompt.md" --outputFile "garden_puppy.png" --sourceFile "source.png" --size "1024x1024"
        """
    )
    
    parser.add_argument(
        "--model",
        required=True,
        help="模型名称，当前固定为 step-2x-large"
    )
    parser.add_argument(
        "--promptFile",
        required=True,
        help="图片描述文件路径, 格式为Markdown"
    )
    parser.add_argument(
        "--outputFile",
        required=True,
        help="生成图片的文件路径"
    )
    parser.add_argument(
        "--sourceFile",
        help="图生图的源图文件路径"
    )
    parser.add_argument(
        "--size",
        default="1024x1024",
        help="图片尺寸，默认1024x1024"
    )
    
    args = parser.parse_args()
    
    try:
        generator = StepFunImageGenerator()
        
        if not args.outputFile.endswith(".png"):
            raise ValueError("输出文件必须必须是.png文件")

        prompt = read_prompt_file(args.promptFile)
        
        if args.sourceFile:
            generator.image_to_image(
                model=args.model,
                source_image_path=args.sourceFile,
                prompt=prompt,
                output_path=args.outputFile,
                size=args.size
            )
        else:
            generator.text_to_image(
                model=args.model,
                prompt=prompt,
                output_path=args.outputFile,
                size=args.size
            )
        
        print("✓ 完成!")
        
    except Exception as e:
        print(f"✗ 错误: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
