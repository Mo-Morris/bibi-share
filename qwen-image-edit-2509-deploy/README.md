

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

调用接口测试：
```
python test.py --api-url http://localhost:8100/v1/images/edits \
                 --image 西瓜.png 西红柿.png \
                 --prompt "将西瓜和西红柿放在一个盘子里面"
```