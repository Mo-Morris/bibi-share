

## 环境准备
0. 显存80GB及以上的显卡（显示环境H800x1卡）  
1. 拉取镜像：`registry.cn-hangzhou.aliyuncs.com/morris-share/sglang:v0.5.3-cu129 `
2. Docker环境

## 启动基础容器
sglang容器已经把cuda、pytorch、transformer等环境都已经安装好了，直接用更为方便。  
docker 启动命令：
```shell
docker run -itd --rm --network host \
--privileged \
--name sglang \
-e GRADIO_PORT="8099" \
-e API_PORT="8100" \
-e MODEL_PATH=/workspace/FLUX___1-dev \
--shm-size=16g \
--gpus all \
-v /workspace:/workspace \
registry.cn-hangzhou.aliyuncs.com/morris-share/sglang:v0.5.3-cu129 \
/bin/bash -c 'tail -f /dev/null'
```
> 进入容器检查显存是否加载

## 在容器内安装环境

安装diffusers库
```shell
# diffusers来源：https://github.com/huggingface/diffusers
cd  /workspace/diffusers 
pip install -e .
```
安装gradio库
```shell
pip install gradio -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 启动服务

```shell
cd /workspace/app
python main.py
```
终端：
![](./startapp.png)

## 测试功能

打开网页：http://localhost:8099  
![](./gradio.png)

提示词：
中文提示词： "威严而优雅的中国龙盘旋于祥云之上，龙身覆盖翡翠色鳞片，金色龙须随风飘动，爪如鹰隼目露金光。背景融合水墨山水与火焰纹样，传统宫殿屋檐若隐若现。采用超高清4K画质，动态光影效果突出龙鳞质感，新国风水墨风格搭配动态构图，展现东方神话的磅礴气势。"

English Prompt: "A majestic yet graceful Chinese dragon coils through auspicious clouds, its emerald-scaled body glistening with golden whiskers flowing in the wind. Razor-sharp claws and piercing golden eyes radiate power. The background blends ink-wash mountains with flaming motifs, where traditional palace eaves emerge mistily. Rendered in ultra HD 4K with dynamic lighting highlighting scale textures, combining neo-Chinese ink aesthetics with cinematic composition to embody the grandeur of Eastern mythology."

提示词设计说明：

文化元素：融合祥云、水墨、宫殿等典型中国意象
视觉特征：强调翡翠鳞片与金色龙须的经典配色
画质要求：4K超清配合动态光影提升质感
风格平衡：传统水墨技法与现代动态构图结合
氛围营造：通过若隐若现的背景元素增强神秘感

调用接口测试：

```
python test.py --api-url http://localhost:8100/v1/images/generations \
                 --prompt "A cat holding a sign that says hello world"
```