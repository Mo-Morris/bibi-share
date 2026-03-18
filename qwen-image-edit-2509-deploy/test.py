#!/usr/bin/env python3
"""
测试脚本：用于测试 /v1/images/edits 接口
"""

import os
import sys
import base64
import argparse
import requests
from typing import List, Optional


def image_to_base64(image_path: str) -> str:
    """
    将图片文件转换为 base64 编码的字符串（包含 data URI 前缀）

    Args:
        image_path: 图片文件路径

    Returns:
        base64 编码的图片字符串（包含 data URI 前缀）
    """
    with open(image_path, "rb") as image_file:
        img_data = image_file.read()
        img_base64 = base64.b64encode(img_data).decode()

        # 根据文件扩展名确定 MIME 类型
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(ext, "image/png")

        return f"data:{mime_type};base64,{img_base64}"


def base64_to_image_file(base64_str: str, output_path: str):
    """
    将 base64 编码的字符串保存为图片文件

    Args:
        base64_str: base64 编码的图片字符串（可以包含或不包含 data URI 前缀）
        output_path: 输出文件路径
    """
    # 移除 data URI 前缀（如果存在）
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]

    img_data = base64.b64decode(base64_str)
    with open(output_path, "wb") as f:
        f.write(img_data)


def test_image_edit(
    api_url: str,
    image_paths: List[str],
    prompt: str,
    negative_prompt: Optional[str] = " ",
    num_inference_steps: int = 40,
    guidance_scale: float = 1.0,
    true_cfg_scale: float = 4.0,
    seed: int = 0,
    output_path: Optional[str] = None,
):
    """
    测试图像编辑 API

    Args:
        api_url: API 端点 URL（例如：http://localhost:8100/v1/images/edits）
        image_paths: 图片文件路径列表
        prompt: 提示词
        negative_prompt: 负面提示词
        num_inference_steps: 推理步数
        guidance_scale: 引导比例
        true_cfg_scale: 真实 CFG 比例
        seed: 随机种子
        output_path: 输出图片保存路径（如果为 None，则自动生成）

    Returns:
        响应数据（字典）
    """
    # 检查图片文件是否存在
    for img_path in image_paths:
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"图片文件不存在: {img_path}")

    # 将图片转换为 base64
    print(f"正在读取 {len(image_paths)} 张图片...")
    images_base64 = []
    for img_path in image_paths:
        try:
            img_base64 = image_to_base64(img_path)
            images_base64.append(img_base64)
            print(f"  ✓ 已读取: {img_path}")
        except Exception as e:
            print(f"  ✗ 读取失败: {img_path} - {e}")
            raise

    # 构建请求体
    request_data = {
        "images": images_base64,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "num_inference_steps": num_inference_steps,
        "guidance_scale": guidance_scale,
        "true_cfg_scale": true_cfg_scale,
        "seed": seed,
    }

    print(f"\n正在发送请求到: {api_url}")
    print(f"提示词: {prompt}")
    params_msg = (
        f"参数: 推理步数={num_inference_steps}, "
        f"引导比例={guidance_scale}, "
        f"CFG比例={true_cfg_scale}, 随机种子={seed}"
    )
    print(params_msg)

    # 发送 POST 请求
    try:
        response = requests.post(api_url, json=request_data, timeout=300)
        response.raise_for_status()

        result = response.json()

        if result.get("status") == "success":
            print("\n✓ 请求成功！")
            print(f"  {result.get('message', '')}")

            # 保存结果图片
            if "result" in result and "image" in result["result"]:
                output_image_base64 = result["result"]["image"]

                # 如果没有指定输出路径，自动生成
                if output_path is None:
                    base_name = os.path.splitext(os.path.basename(image_paths[0]))[0]
                    output_path = f"output_{base_name}.png"

                base64_to_image_file(output_image_base64, output_path)
                print(f"  ✓ 结果图片已保存到: {output_path}")
            else:
                print("  ⚠ 响应中未找到图片数据")
        else:
            print(f"\n✗ 请求失败: {result}")

        return result

    except requests.exceptions.Timeout:
        print("\n✗ 请求超时（超过 300 秒）")
        raise
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ HTTP 错误: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"  错误详情: {error_detail}")
            except Exception:
                print(f"  响应内容: {e.response.text}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"\n✗ 请求异常: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="测试 Qwen Image Edit Plus API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 基本用法（单张图片）
  python test.py --api-url http://localhost:8100/v1/images/edits \
                 --image test.jpg \\
                 --prompt "The magician bear is on the left"

  # 多张图片
  python test.py --api-url http://localhost:8100/v1/images/edits \
                 --image img1.jpg img2.jpg \
                 --prompt "The magician bear is on the left, " \
                          "the alchemist bear is on the right"

  # 自定义参数
  python test.py --api-url http://localhost:8100/v1/images/edits \
                 --image test.jpg \
                 --prompt "The magician bear is on the left" \
                 --num-inference-steps 50 \
                 --guidance-scale 1.5 \
                 --true-cfg-scale 5.0 \
                 --seed 42 \
                 --output result.png
        """,
    )

    parser.add_argument(
        "--api-url",
        type=str,
        required=True,
        help="API 端点 URL（例如：http://localhost:8100/v1/images/edits）",
    )
    parser.add_argument(
        "--image",
        type=str,
        nargs="+",
        required=True,
        help="输入图片文件路径（支持多张）",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="提示词",
    )
    parser.add_argument(
        "--negative-prompt",
        type=str,
        default=" ",
        help="负面提示词（默认：空格）",
    )
    parser.add_argument(
        "--num-inference-steps",
        type=int,
        default=40,
        help="推理步数（默认：40）",
    )
    parser.add_argument(
        "--guidance-scale",
        type=float,
        default=1.0,
        help="引导比例（默认：1.0）",
    )
    parser.add_argument(
        "--true-cfg-scale",
        type=float,
        default=4.0,
        help="真实 CFG 比例（默认：4.0）",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="随机种子（默认：0）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出图片保存路径（默认：自动生成）",
    )

    args = parser.parse_args()

    try:
        test_image_edit(
            api_url=args.api_url,
            image_paths=args.image,
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            num_inference_steps=args.num_inference_steps,
            guidance_scale=args.guidance_scale,
            true_cfg_scale=args.true_cfg_scale,
            seed=args.seed,
            output_path=args.output,
        )
        print("\n测试完成！")
        return 0
    except Exception as e:
        print(f"\n测试失败: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
