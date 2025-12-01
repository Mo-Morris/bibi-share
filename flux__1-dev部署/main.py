import os
import io
import base64
import time
import torch
from PIL import Image
import gradio as gr
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from modelscope import FluxPipeline
from loguru import logger

# 全局加载 pipeline
logger.info("正在加载 pipeline...")
# 获取环境变量MODEL_PATH
model_path = os.getenv("MODEL_PATH")
if model_path is None:
    raise ValueError("MODEL_PATH 环境变量未设置")
pipeline = FluxPipeline.from_pretrained(model_path, torch_dtype=torch.bfloat16)
pipeline.to("cuda")
logger.info("pipeline 加载完成")

# 启用模型 CPU offload 以节省 VRAM（如果 GPU 足够可以移除这行）
pipeline.enable_model_cpu_offload()

# 创建 FastAPI 应用
app = FastAPI(title="FLUX.1-dev API", version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 定义请求模型
class ImageGenerationRequest(BaseModel):
    """图像生成请求模型"""

    prompt: str = Field(..., description="提示词", min_length=1)
    height: int = Field(1024, ge=256, le=2048, description="图片高度")
    width: int = Field(1024, ge=256, le=2048, description="图片宽度")
    guidance_scale: float = Field(3.5, ge=0.0, le=20.0, description="引导比例")
    num_inference_steps: int = Field(50, ge=10, le=100, description="推理步数")
    max_sequence_length: int = Field(512, ge=128, le=1024, description="最大序列长度")
    seed: int = Field(0, description="随机种子")


def image_to_base64(image: Image.Image) -> str:
    """
    将 PIL Image 转换为 base64 编码的字符串

    Args:
        image: PIL Image 对象

    Returns:
        base64 编码的图片字符串（包含 data URI 前缀）
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy", "pipeline_loaded": pipeline is not None}


@app.post("/v1/images/generations")
async def image_generation(request: ImageGenerationRequest):
    """
    图像生成 API 端点

    根据文本提示词生成图片，返回生成的图片（base64 编码）

    请求体示例:
    {
        "prompt": "A cat holding a sign that says hello world",
        "height": 1024,
        "width": 1024,
        "guidance_scale": 3.5,
        "num_inference_steps": 50,
        "max_sequence_length": 512,
        "seed": 0
    }
    """
    try:
        if not request.prompt or request.prompt.strip() == "":
            raise HTTPException(status_code=400, detail="请输入提示词")

        logger.info(
            f"API 调用: 提示词={request.prompt[:50]}..., "
            f"尺寸={request.width}x{request.height}, "
            f"推理步数={request.num_inference_steps}, "
            f"引导比例={request.guidance_scale}, "
            f"最大序列长度={request.max_sequence_length}, "
            f"随机种子={request.seed}"
        )

        # 准备输入
        generator = torch.Generator("cpu").manual_seed(request.seed)

        # 执行推理并准确测量时间
        inference_start_time = time.time()
        with torch.inference_mode():
            output = pipeline(
                request.prompt,
                height=request.height,
                width=request.width,
                guidance_scale=request.guidance_scale,
                num_inference_steps=request.num_inference_steps,
                max_sequence_length=request.max_sequence_length,
                generator=generator,
            )
            output_image = output.images[0]
        inference_end_time = time.time()
        inference_duration = inference_end_time - inference_start_time

        # 转换为 base64
        base64_start_time = time.time()
        output_base64 = image_to_base64(output_image)
        base64_duration = time.time() - base64_start_time

        logger.info(
            f"API 推理完成！推理时间: {inference_duration:.2f}秒, "
            f"编码时间: {base64_duration:.2f}秒, "
            f"总耗时: {inference_duration + base64_duration:.2f}秒"
        )

        return JSONResponse(
            {
                "status": "success",
                "message": "推理完成！",
                "result": {
                    "image": output_base64,
                    "inference_time_seconds": round(inference_duration, 2),
                    "encoding_time_seconds": round(base64_duration, 2),
                    "total_time_seconds": round(
                        inference_duration + base64_duration, 2
                    ),
                },
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API 推理出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"推理出错: {str(e)}")


def inference(
    prompt,
    height=1024,
    width=1024,
    guidance_scale=3.5,
    num_inference_steps=50,
    max_sequence_length=512,
    seed=0,
):
    """
    执行图像生成推理

    Args:
        prompt: 提示词
        height: 图片高度
        width: 图片宽度
        guidance_scale: 引导比例
        num_inference_steps: 推理步数
        max_sequence_length: 最大序列长度
        seed: 随机种子

    Returns:
        生成的图片和状态消息
    """
    if not prompt or prompt.strip() == "":
        return None, "请输入提示词"

    try:
        logger.info(
            f"开始推理: 提示词={prompt[:50]}..., "
            f"尺寸={width}x{height}, "
            f"推理步数={num_inference_steps}, "
            f"引导比例={guidance_scale}, "
            f"最大序列长度={max_sequence_length}, "
            f"随机种子={seed}"
        )

        # 准备生成器
        generator = torch.Generator("cpu").manual_seed(seed)

        # 执行推理并准确测量时间
        inference_start_time = time.time()
        with torch.inference_mode():
            output = pipeline(
                prompt,
                height=height,
                width=width,
                guidance_scale=guidance_scale,
                num_inference_steps=int(num_inference_steps),
                max_sequence_length=max_sequence_length,
                generator=generator,
            )
            output_image = output.images[0]
        inference_end_time = time.time()
        inference_duration = inference_end_time - inference_start_time

        logger.info(f"推理完成！实际推理时间: {inference_duration:.2f}秒")
        return (
            output_image,
            f"推理完成！实际耗时: {inference_duration:.2f}秒",
        )

    except Exception as e:
        logger.error(f"推理出错: {str(e)}")
        return None, f"推理出错: {str(e)}"


# 创建 Gradio 界面
with gr.Blocks(title="FLUX.1-dev") as demo:
    gr.Markdown("# FLUX.1-dev - 文本生成图像工具")
    gr.Markdown("输入提示词来生成图像")

    with gr.Row():
        with gr.Column():
            prompt_input = gr.Textbox(
                label="提示词 (Prompt)",
                placeholder="例如: A cat holding a sign that says hello world",
                lines=3,
            )
            output_image = gr.Image(label="生成的图片", height=600)
            status_text = gr.Textbox(
                label="状态", value="等待输入...", interactive=False
            )

    with gr.Row():
        with gr.Accordion("高级参数", open=False):
            with gr.Row():
                height_input = gr.Slider(
                    label="图片高度 (Height)",
                    minimum=256,
                    maximum=2048,
                    value=1024,
                    step=64,
                )
                width_input = gr.Slider(
                    label="图片宽度 (Width)",
                    minimum=256,
                    maximum=2048,
                    value=1024,
                    step=64,
                )
            with gr.Row():
                num_steps = gr.Slider(
                    label="推理步数 (Num Inference Steps)",
                    minimum=10,
                    maximum=100,
                    value=50,
                    step=1,
                )
                guidance_scale = gr.Slider(
                    label="引导比例 (Guidance Scale)",
                    minimum=0.0,
                    maximum=20.0,
                    value=3.5,
                    step=0.1,
                )
            with gr.Row():
                max_sequence_length = gr.Slider(
                    label="最大序列长度 (Max Sequence Length)",
                    minimum=128,
                    maximum=1024,
                    value=512,
                    step=64,
                )
                seed_input = gr.Number(label="随机种子 (Seed)", value=0, precision=0)

    with gr.Row():
        submit_btn = gr.Button("生成图像", variant="primary", size="lg")
        clear_btn = gr.Button("清空", variant="secondary")

    # 绑定事件：提交推理
    submit_btn.click(
        fn=inference,
        inputs=[
            prompt_input,
            height_input,
            width_input,
            guidance_scale,
            num_steps,
            max_sequence_length,
            seed_input,
        ],
        outputs=[output_image, status_text],
    )

    # 绑定事件：清空所有输入
    clear_btn.click(
        fn=lambda: ("", 1024, 1024, 3.5, 50, 512, 0, None, "已清空"),
        outputs=[
            prompt_input,
            height_input,
            width_input,
            guidance_scale,
            num_steps,
            max_sequence_length,
            seed_input,
            output_image,
            status_text,
        ],
    )


if __name__ == "__main__":
    import uvicorn
    import threading

    # 获取配置
    host = os.getenv("GRADIO_HOST", "0.0.0.0")

    # Gradio 端口
    gradio_port_env = os.getenv("GRADIO_PORT")
    if gradio_port_env:
        try:
            gradio_port = int(gradio_port_env)
            logger.info(f"从环境变量 GRADIO_PORT 获取端口: {gradio_port}")
        except ValueError:
            logger.warning(
                f"环境变量 GRADIO_PORT 的值 '{gradio_port_env}' 不是有效数字，使用默认端口 8099"
            )
            gradio_port = 8099
    else:
        gradio_port = 8099
        logger.info(f"环境变量 GRADIO_PORT 未设置，使用默认端口: {gradio_port}")

    # API 端口（默认比 Gradio 端口大 1）
    api_port_env = os.getenv("API_PORT")
    if api_port_env:
        try:
            api_port = int(api_port_env)
            logger.info(f"从环境变量 API_PORT 获取端口: {api_port}")
        except ValueError:
            logger.warning(
                f"环境变量 API_PORT 的值 '{api_port_env}' "
                f"不是有效数字，使用默认端口 {gradio_port + 1}"
            )
            api_port = gradio_port + 1
    else:
        api_port = gradio_port + 1
        logger.info(f"环境变量 API_PORT 未设置，使用默认端口: {api_port}")

    # 在后台线程启动 Gradio
    def run_gradio():
        logger.info(f"正在启动 Gradio 服务器，地址: http://{host}:{gradio_port}")
        demo.launch(
            server_name=host,
            server_port=gradio_port,
            share=False,
        )

    gradio_thread = threading.Thread(target=run_gradio, daemon=True)
    gradio_thread.start()

    # 启动 FastAPI 服务器
    logger.info(f"正在启动 FastAPI 服务器，地址: http://{host}:{api_port}")
    logger.info(f"API 文档地址: http://{host}:{api_port}/docs")
    logger.info(f"Gradio 界面地址: http://{host}:{gradio_port}")

    uvicorn.run(app, host=host, port=api_port, log_level="info")
