#!/usr/bin/env python3
"""OpenAI Responses API 调用示例.

运行前:
  pip install openai

用法:
  python codex/call-llm-api.py
  python codex/call-llm-api.py "用一句话介绍 Responses API"
"""

import argparse
import sys

from openai import OpenAI


API_BASE = "http://127.0.0.1:3000"
API_KEY = "sk-6t1GxJj1JD2h1WlU0RPgwBpQIFDq8fKHHmPexVVoZDPsS4V0"
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_PROMPT = "介绍一下自己"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Call OpenAI's Responses API and print the model output."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=DEFAULT_PROMPT,
        help="要发送给模型的输入文本",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"模型名称，默认使用 {DEFAULT_MODEL}",
    )
    return parser.parse_args()


def main() -> int:
    if not API_KEY or API_KEY == "your_api_key_here":
        print("请先在代码中填写 API_KEY。", file=sys.stderr)
        return 1

    args = parse_args()
    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE,
    )

    response = client.responses.create(
        model=args.model,
        input=args.prompt,
    )

    print(response.output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
