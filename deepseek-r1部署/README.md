# 满血版671B DeepSeek R1多机部署

## 环境准备

0. Docker环境准备、IB网络准备。

1. 准备两台机器： 2台 x H800 x 8卡（每卡显存80G）  

3. 提前将模型下载好

4. 在主机拉取SGlang镜像
`registry.cn-hangzhou.aliyuncs.com/morris-share/sglang:v0.5.3-cu129`

## IB网络参数获取

高性能IB网卡获取
```shell
for hca in /sys/class/infiniband/mlx5_*; do
    pid=$(ibv_devinfo -d $(basename $hca) | awk '/vendor_part_id/{print $2}')
    case $pid in
        4129) echo "$(basename $hca)  CX-7   400G";;
        4125) echo "$(basename $hca)  CX-6   200G";;
        4117) echo "$(basename $hca)  CX-4Lx  25G";;
        *)    echo "$(basename $hca)  unknown($pid)";;
    esac
done
```
输出类似内容，将性能最高的选择出来，例如按照下面的输出，性能最高的就是：mlx5_0,mlx5_3,mlx5_5,mlx5_7
```shell
mlx5_0  CX-7   400G
mlx5_3  CX-7   400G
mlx5_4  CX-6   200G
mlx5_5  CX-7   400G
mlx5_6  CX-6   200G
mlx5_7  CX-7   400G
mlx5_bond_0  CX-4Lx  25G
```
NCCL_IB_GID_INDEX
show_gids获取携带IPV4的索引。


##  master节点上运行容器

```
docker run -d \
  --name deepseek-sglang \
  --network host \
  --privileged \
  -e MODEL_NAME=DeepSeek-R1 \
  -e MODEL_PATH=/models/DeepSeek-R1 \
  -e NCCL_IB_HCA=mlx5_0,mlx5_3,mlx5_5,mlx5_7 \
  -e DIST_INIT_ADDR=10.24.9.21 \
  -e NCCL_SOCKET_IFNAME=bond0 \
  -e NCCL_IB_GID_INDEX=3 \
  -e NCCL_IB_TIMEOUT=22 \
  -e NCCL_IB_RETRY_CNT=7 \
  -e NCCL_IB_QPS_PER_CONNECTION=8 \
  -e NCCL_DEBUG=INFO \
  -e NCCL_NET_GDR_LEVEL=2 \
  -e DIST_INIT_PORT=29508 \
  -e NCCL_DEBUG_SUBSYS=INIT,NET,IB \
  -v /cx8k/fs1/solution/model/:/models \
  -v /dev/shm:/dev/shm \
  -v /dev/infiniband:/dev/infiniband \
  --shm-size=128g \
  --gpus all \
  registry.cn-hangzhou.aliyuncs.com/morris-share/sglang:v0.5.3-cu129 \
  /bin/bash -c '
    python3 -m sglang.launch_server \
      --model-path $MODEL_PATH \
      --chunked-prefill-size 8192 \
      --served-model-name $MODEL_NAME \
      --tp 16 \
      --dist-init-addr $DIST_INIT_ADDR:$DIST_INIT_PORT \
      --mem-fraction-static 0.85 \
      --context-length 16384 \
      --nnodes 2 \
      --node-rank 0 \
      --trust-remote-code \
      --host 0.0.0.0 \
      --port 8000 \
      --reasoning-parser deepseek-r1 \
      --speculative-algorithm NEXTN \
      --speculative-num-steps 2 \
      --speculative-eagle-topk 4 \
      --speculative-num-draft-tokens 4
  '
```

## worker节点上运行容器 
```
docker run -d \
  --name deepseek-sglang \
  --network host \
  --privileged \
  -e MODEL_NAME=DeepSeek-R1 \
  -e MODEL_PATH=/models/DeepSeek-R1 \
  -e NCCL_IB_HCA=mlx5_0,mlx5_3,mlx5_5,mlx5_7 \
  -e DIST_INIT_ADDR=10.24.9.21 \
  -e NCCL_SOCKET_IFNAME=bond0 \
  -e NCCL_IB_GID_INDEX=3 \
  -e NCCL_IB_TIMEOUT=22 \
  -e NCCL_IB_RETRY_CNT=7 \
  -e NCCL_IB_QPS_PER_CONNECTION=8 \
  -e NCCL_DEBUG=INFO \
  -e NCCL_NET_GDR_LEVEL=2 \
  -e DIST_INIT_PORT=29508 \
  -e NCCL_DEBUG_SUBSYS=INIT,NET,IB \
  -v /cx8k/fs1/solution/model/:/models \
  -v /dev/shm:/dev/shm \
  -v /dev/infiniband:/dev/infiniband \
  --shm-size=128g \
  --gpus all \
  registry.cn-hangzhou.aliyuncs.com/morris-share/sglang:v0.5.3-cu129 \
  /bin/bash -c '
    python3 -m sglang.launch_server \
      --model-path $MODEL_PATH \
      --chunked-prefill-size 8192 \
      --served-model-name $MODEL_NAME \
      --tp 16 \
      --dist-init-addr $DIST_INIT_ADDR:$DIST_INIT_PORT \
      --mem-fraction-static 0.85 \
      --context-length 16384 \
      --nnodes 2 \
      --node-rank 1 \
      --trust-remote-code \
      --host 0.0.0.0 \
      --port 8000 \
      --reasoning-parser deepseek-r1 \
      --speculative-algorithm NEXTN \
      --speculative-num-steps 2 \
      --speculative-eagle-topk 4 \
      --speculative-num-draft-tokens 4
  '
```

## 测试模型
```
curl -X POST 'http://10.24.9.21:8000/v1/chat/completions' \
-H "Content-Type: application/json" \
-d "{
     \"model\": \"DeepSeek-R1\", 
     \"stream\": \"true\", 
     \"messages\": [
         {\"role\": \"user\", \"content\": \"气候变暖的原因？\"}
     ]
   }"
```