import os
import io
import base64
import torch
from PIL import Image
import gradio as gr
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from modelscope import QwenImageEditPlusPipeline
from loguru import logger
from typing import List, Optional

# 全局加载 pipeline
logger.info("正在加载 pipeline...")
pipeline = QwenImageEditPlusPipeline.from_pretrained(
    "/models/Qwen-Image-Edit-2509", torch_dtype=torch.bfloat16
)
logger.info("pipeline 加载完成")

pipeline.to("cuda:0")
pipeline.set_progress_bar_config(disable=None)

# 创建 FastAPI 应用
app = FastAPI(title="Qwen Image Edit Plus API", version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 定义请求模型
class ImageEditRequest(BaseModel):
    """图像编辑请求模型"""

    images: List[str] = Field(
        ...,
        description="base64 编码的图片列表（支持多张），可以包含或不包含 data URI 前缀",
        min_items=1,
    )
    prompt: str = Field(..., description="提示词", min_length=1)
    negative_prompt: Optional[str] = Field(" ", description="负面提示词")
    num_inference_steps: int = Field(40, ge=10, le=100, description="推理步数")
    guidance_scale: float = Field(1.0, ge=0.0, le=10.0, description="引导比例")
    true_cfg_scale: float = Field(4.0, ge=0.0, le=10.0, description="真实 CFG 比例")
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


def base64_to_image(base64_str: str) -> Image.Image:
    """
    将 base64 编码的字符串转换为 PIL Image

    Args:
        base64_str: base64 编码的图片字符串（可以包含或不包含 data URI 前缀）

    Returns:
        PIL Image 对象
    """
    # 移除 data URI 前缀（如果存在）
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]
    img_data = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(img_data))


def process_uploaded_files(files):
    """
    处理上传的文件，转换为 PIL Image 列表

    Args:
        files: 上传的文件列表（可能是文件路径字符串或文件对象）

    Returns:
        PIL Image 列表
    """
    if not files:
        return []

    # 如果 files 是单个文件而不是列表，转换为列表
    if not isinstance(files, list):
        files = [files]

    images = []
    for file in files:
        if file is None:
            continue
        try:
            # 如果已经是 PIL Image，直接使用
            if isinstance(file, Image.Image):
                images.append(file)
            # 如果是文件路径字符串
            elif isinstance(file, str):
                images.append(Image.open(file))
            # 如果是文件对象（有 name 属性）
            elif hasattr(file, "name"):
                images.append(Image.open(file.name))
            # 如果是 numpy array
            else:
                images.append(Image.fromarray(file))
        except Exception as e:
            logger.error(f"处理图片时出错: {e}")
            continue

    return images


def update_gallery(files):
    """
    更新图片预览画廊

    Args:
        files: 上传的文件列表（可能是文件路径字符串或文件对象）

    Returns:
        图片列表用于画廊显示
    """
    if not files:
        return []

    # 如果 files 是单个文件而不是列表，转换为列表
    if not isinstance(files, list):
        files = [files]

    gallery_images = []
    for file in files:
        if file is None:
            continue
        try:
            if isinstance(file, Image.Image):
                gallery_images.append(file)
            elif isinstance(file, str):
                gallery_images.append(Image.open(file))
            elif hasattr(file, "name"):
                gallery_images.append(Image.open(file.name))
            else:
                gallery_images.append(Image.fromarray(file))
        except Exception:
            continue

    return gallery_images


@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy", "pipeline_loaded": pipeline is not None}


@app.post("/v1/images/edits")
async def image_edit(request: ImageEditRequest):
    """
    图像编辑 API 端点

    接收 base64 编码的图片列表（支持多张），返回编辑后的图片（base64 编码）

    请求体示例:
    {
        "images": [
            "data:image/png;base64,iVBORw0KGgoAAAANS...",
            "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
        ],
        "prompt": "The magician bear is on the left",
        "negative_prompt": " ",
        "num_inference_steps": 40,
        "guidance_scale": 1.0,
        "true_cfg_scale": 4.0,
        "seed": 0
    }
    """
    try:
        if not request.images or len(request.images) == 0:
            raise HTTPException(status_code=400, detail="请至少提供一张图片")

        if not request.prompt or request.prompt.strip() == "":
            raise HTTPException(status_code=400, detail="请输入提示词")

        # 处理 base64 编码的图片
        pil_images = []
        for idx, image_base64 in enumerate(request.images):
            try:
                pil_image = base64_to_image(image_base64)
                # 转换为 RGB 模式（如果需要）
                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")
                pil_images.append(pil_image)
            except Exception as e:
                logger.error(f"处理第 {idx + 1} 张图片时出错: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"无法处理第 {idx + 1} 张图片: {str(e)}",
                )

        if len(pil_images) == 0:
            raise HTTPException(
                status_code=400,
                detail="无法处理图片，请确保提供有效的 base64 编码图片",
            )

        logger.info(
            f"API 调用: 图片数量={len(pil_images)}, "
            f"推理步数={request.num_inference_steps}, "
            f"引导比例={request.guidance_scale}, "
            f"CFG比例={request.true_cfg_scale}, "
            f"随机种子={request.seed}"
        )

        # 准备输入
        inputs = {
            "image": pil_images,
            "prompt": request.prompt,
            "generator": torch.manual_seed(request.seed),
            "true_cfg_scale": request.true_cfg_scale,
            "negative_prompt": request.negative_prompt or " ",
            "num_inference_steps": int(request.num_inference_steps),
            "guidance_scale": request.guidance_scale,
            "num_images_per_prompt": 1,
        }

        # 执行推理
        with torch.inference_mode():
            output = pipeline(**inputs)
            output_image = output.images[0]

        # 转换为 base64
        output_base64 = image_to_base64(output_image)

        logger.info(f"API 推理完成！已处理 {len(pil_images)} 张输入图片")

        return JSONResponse(
            {
                "status": "success",
                "message": f"推理完成！已处理 {len(pil_images)} 张输入图片",
                "result": {
                    "image": output_base64,
                    "input_count": len(pil_images),
                },
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API 推理出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"推理出错: {str(e)}")


def inference(
    files,
    prompt,
    negative_prompt=" ",
    num_inference_steps=40,
    guidance_scale=1.0,
    true_cfg_scale=4.0,
    seed=0,
):
    """
    执行图像编辑推理

    Args:
        files: 上传的图片文件列表（可以是任意数量）
        prompt: 提示词
        negative_prompt: 负面提示词
        num_inference_steps: 推理步数
        guidance_scale: 引导比例
        true_cfg_scale: 真实 CFG 比例
        seed: 随机种子

    Returns:
        生成的图片
    """
    if not files or len(files) == 0:
        return None, "请至少上传一张图片"

    if not prompt or prompt.strip() == "":
        return None, "请输入提示词"

    try:
        # 处理上传的图片文件
        images = process_uploaded_files(files)

        if len(images) == 0:
            logger.warning("无法处理上传的图片，请确保上传的是有效的图片文件")
            return None, "无法处理上传的图片，请确保上传的是有效的图片文件"

        logger.info(
            f"开始推理: 图片数量={len(images)}, "
            f"推理步数={num_inference_steps}, "
            f"引导比例={guidance_scale}, "
            f"CFG比例={true_cfg_scale}, "
            f"随机种子={seed}"
        )

        # 准备输入
        inputs = {
            "image": images,
            "prompt": prompt,
            "generator": torch.manual_seed(seed),
            "true_cfg_scale": true_cfg_scale,
            "negative_prompt": negative_prompt,
            "num_inference_steps": int(num_inference_steps),
            "guidance_scale": guidance_scale,
            "num_images_per_prompt": 1,
        }

        # 执行推理
        with torch.inference_mode():
            output = pipeline(**inputs)
            output_image = output.images[0]

        logger.info(f"推理完成！已处理 {len(images)} 张输入图片")
        return output_image, f"推理完成！已处理 {len(images)} 张输入图片"

    except Exception as e:
        logger.error(f"推理出错: {str(e)}")
        return None, f"推理出错: {str(e)}"


# 创建 Gradio 界面
with gr.Blocks(title="Qwen Image Edit Plus") as demo:
    gr.Markdown("# Qwen Image Edit Plus - 图像编辑工具")
    gr.Markdown("上传任意数量的图片并输入提示词来生成编辑后的图像")

    with gr.Row():
        with gr.Column():
            file_input = gr.File(
                label="上传图片（支持多选）",
                file_count="multiple",
                file_types=["image"],
                height=200,
            )
            image_gallery = gr.Gallery(
                label="已上传的图片预览",
                show_label=True,
                elem_id="gallery",
                columns=3,
                rows=2,
                height=400,
            )

        with gr.Column():
            output_image = gr.Image(label="输出图片", height=600)
            status_text = gr.Textbox(
                label="状态", value="等待输入...", interactive=False
            )

    with gr.Row():
        with gr.Column():
            prompt_input = gr.Textbox(
                label="提示词 (Prompt)",
                placeholder=(
                    "例如: The magician bear is on the left, "
                    "the alchemist bear is on the right, "
                    "facing each other in the central park square."
                ),
                lines=3,
            )
            negative_prompt_input = gr.Textbox(
                label="负面提示词 (Negative Prompt)", value=" ", lines=2
            )

    with gr.Row():
        with gr.Accordion("高级参数", open=False):
            with gr.Row():
                num_steps = gr.Slider(
                    label="推理步数 (Num Inference Steps)",
                    minimum=10,
                    maximum=100,
                    value=40,
                    step=1,
                )
                guidance_scale = gr.Slider(
                    label="引导比例 (Guidance Scale)",
                    minimum=0.0,
                    maximum=10.0,
                    value=1.0,
                    step=0.1,
                )
            with gr.Row():
                true_cfg_scale = gr.Slider(
                    label="真实 CFG 比例 (True CFG Scale)",
                    minimum=0.0,
                    maximum=10.0,
                    value=4.0,
                    step=0.1,
                )
                seed_input = gr.Number(label="随机种子 (Seed)", value=0, precision=0)

    with gr.Row():
        submit_btn = gr.Button("生成图像", variant="primary", size="lg")
        clear_btn = gr.Button("清空", variant="secondary")

    # 绑定事件：文件上传时更新预览画廊
    file_input.change(
        fn=update_gallery,
        inputs=[file_input],
        outputs=[image_gallery],
    )

    # 绑定事件：提交推理
    submit_btn.click(
        fn=inference,
        inputs=[
            file_input,
            prompt_input,
            negative_prompt_input,
            num_steps,
            guidance_scale,
            true_cfg_scale,
            seed_input,
        ],
        outputs=[output_image, status_text],
    )

    # 绑定事件：清空所有输入
    clear_btn.click(
        fn=lambda: (None, [], "", " ", 40, 1.0, 4.0, 0, None, "已清空"),
        outputs=[
            file_input,
            image_gallery,
            prompt_input,
            negative_prompt_input,
            num_steps,
            guidance_scale,
            true_cfg_scale,
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
