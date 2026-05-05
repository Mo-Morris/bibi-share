# 大模型网关LiteLLM路由策略

## 背景说明
目前大模型是越做越大，普通人甚至公司，都是没有那么多算力部署这些模型的。所以首先想到的都是接入模型供应商提供的模型。
像DeepSeek、Qwen这样，因为模型本身就是开源的，所以我们可以从注册多家模型供应商来提升自家业务的稳定性。
当管理多个模型供应商的API之后，如何分配这些API的调用，这就要用到LiteLLM提供的路由策略，根据业务场景不同，我们可以使用LiteLLM的多种路由策略。
如果还不会使用LiteLLM的同学，欢迎我的主页 [大模型网关 LiteLLM 零基础快速上手教程](bilibili.com/video/BV1EGNGzhEQj/?spm_id_from=333.1387.upload.video_card.click)。

下面用DeepSeek V4 Flash举例，注册三个供应商：
1. [deepseek官方网站](https://api-docs.deepseek.com/)
2. [百炼平台](https://bailian.console.aliyun.com/)
3. [硅基流动](https://www.siliconflow.cn/)

> 参考LiteLLM官方文档：https://docs.litellm.ai/docs/routing

## 最基础的负载均衡
model_name相同，注册多个源，会以负载均衡的方式，分别方案三个模型供应商。
```yaml
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: azure/<your-deployment-name>
      api_base: <your-azure-endpoint>
      api_key: <your-azure-api-key>
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: azure/gpt-turbo-small-ca
      api_base: https://my-endpoint-canada-berri992.openai.azure.com/
      api_key: <your-azure-api-key>
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: azure/gpt-turbo-large
      api_base: https://openai-france-1234.openai.azure.com/
      api_key: <your-azure-api-key>
```
分别发起多次请求，然后去查看调用日志验证路由策略：
```shell
curl -X POST 'http://0.0.0.0:4000/chat/completions' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer sk-1234' \
-d '{
  "model": "gpt-3.5-turbo",
  "messages": [
        {"role": "user", "content": "hi"}
    ]
}'
```

## 根据RMP来分配

```shell
model_list:
	- model_name: gpt-3.5-turbo
	  litellm_params:
	  	model: azure/chatgpt-v-2
		api_key: os.environ/AZURE_API_KEY
		api_version: os.environ/AZURE_API_VERSION
		api_base: os.environ/AZURE_API_BASE
		rpm: 900 
	- model_name: gpt-3.5-turbo
	  litellm_params:
	  	model: azure/chatgpt-functioncalling
		api_key: os.environ/AZURE_API_KEY
		api_version: os.environ/AZURE_API_VERSION
		api_base: os.environ/AZURE_API_BASE
		rpm: 10 
```