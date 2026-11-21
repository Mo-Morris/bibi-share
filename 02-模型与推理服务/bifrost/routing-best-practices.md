# Bifrost路由策略实战演示

接入多个供应商后，同一个模型往往会有几条可用的调用渠道。各渠道的价格、稳定性和并发额度不同，需要根据业务需求分配请求，并为故障准备备用路径。

本文以 `demo-model` 为例，接入四个模拟来源，分别配置价格优先、稳定性优先、高并发和权重分流策略，再通过请求日志验证路由与回退结果。实操使用开源版，企业版自适应负载均衡放在最后简要介绍。

## 场景与来源配置

四个来源均提供 `demo-model`，参数如下。价格和成功率为模拟设定，不代表真实供应商数据。


| 来源  | Bifrost Provider 名 | 输入价格（元/百万 Token） | 输出价格（元/百万 Token） | 模拟基础成功率 | 上游并发上限 | 适合的角色       |
| --- | ------------------ | ---------------- | ---------------- | ------- | ------ | ----------- |
| A   | `source-a`         | 1                | 2                | 90%     | 5      | 低成本首选       |
| B   | `source-b`         | 2                | 4                | 98%     | 20     | 价格和稳定性比较均衡  |
| C   | `source-c`         | 3                | 6                | 96%     | 100    | 批量任务和大并发    |
| D   | `source-d`         | 5                | 10               | 99.9%   | 40     | 关键业务首选及可靠备用 |


A 的价格最低，但并发额度小，适合对成本敏感、允许重试的任务。D 更稳定，适合关键业务。C 可以承接更多并发请求，适合批量处理。B 的价格与稳定性较为均衡，可以承担部分日常流量。

路由规则据此选择首次调用的来源，Fallbacks 则规定失败后的尝试顺序。

### 模拟服务行为

模拟服务按固定频率返回 503：A 每接纳 10 个请求失败一次，B 每 50 个、C 每 25 个、D 每 1000 个失败一次。

每个请求默认耗时 2 秒，超过并发上限的新请求返回 429。表中的基础成功率仅对应固定失败频率，不包含并发超限和手动设置的故障。

服务返回固定文本和模拟 Token 用量，不调用真实模型。表中价格仅用于制定路由策略，不会写入 Bifrost 的计费配置。

## 环境准备

配套模拟程序只需要 Python 3，不需要额外安装依赖。

将配套的 `routing-demo` 目录放在工作目录中，然后启动模拟服务：

```bash
python3 routing-demo/mock_sources.py
```

保持终端运行，按 `Ctrl+C` 可以一次关闭四个来源。

### 添加 Provider

Bifrost 与模拟程序都运行在本机时，按下面填写：


| Provider 名 | Base Format | Base URL                    | API Key    | 允许模型         |
| ---------- | ----------- | --------------------------- | ---------- | ------------ |
| `source-a` | OpenAI      | `http://127.0.0.1:18081/v1` | `demo-key` | `demo-model` |
| `source-b` | OpenAI      | `http://127.0.0.1:18082/v1` | `demo-key` | `demo-model` |
| `source-c` | OpenAI      | `http://127.0.0.1:18083/v1` | `demo-key` | `demo-model` |
| `source-d` | OpenAI      | `http://127.0.0.1:18084/v1` | `demo-key` | `demo-model` |


在 Providers 中分别创建四个 Custom Provider，启用模型列表和 Chat Completions 接口。模拟服务支持非流式调用，后续请求统一使用 `stream: false`。

### 创建 Virtual Key

在 Virtual Keys 中创建 `four-sources-demo`：

1. 添加四个 Provider。
2. 每个 Provider 都允许 `demo-model`。
3. 明确选择允许使用的上游 Key。
4. 记录 Virtual Key 的调用密钥及内部 ID。

后续规则的 Scope 均绑定此 Virtual Key。内部 ID 用于绑定规则，调用密钥用于发送请求。

四个 Provider 的 VK 权重留空，由后续的 Routing Rules 选择来源。保留各 Provider 的模型和 Key 授权。

将四个 Provider 的 Max Retries 设为 0，使请求在来源失败后直接进入回退流程，方便观察尝试顺序。

Bifrost 的并发配置应能承接后续测试流量，避免网关自身成为瓶颈。

### 验证连接

将 `BASE_URL` 改为 Bifrost 的访问地址，`BF_VK` 填入刚创建的调用密钥：

```bash
export BASE_URL='http://127.0.0.1:8081'
export BF_VK='替换成演示Virtual Key的调用密钥'

for source in source-a source-b source-c source-d; do
  curl --fail-with-body -sS "$BASE_URL/v1/chat/completions" \
    -H "x-bf-vk: $BF_VK" \
    -H 'Content-Type: application/json' \
    -d "{\"model\":\"$source/demo-model\",\"messages\":[{\"role\":\"user\",\"content\":\"测试连接\"}],\"stream\":false}"
  printf '\n'
done
```

四次调用的回答应分别包含 `source-a` 到 `source-d`。来源标记由模拟服务返回，也可以在 Bifrost 请求日志中核对实际 Provider。

## 价格优先

离线内容生成等任务通常允许一定等待和重试，可以优先使用价格较低的 A，失败后按价格顺序尝试 B、C、D。

在 Routing Rules 中新建规则：


| 字段              | 填写内容                                                              |
| --------------- | ----------------------------------------------------------------- |
| Name            | 四源价格优先                                                            |
| Scope           | Virtual Key，选择 `four-sources-demo`                                |
| Priority        | 10                                                                |
| Enabled         | 开启                                                                |
| Chain Rule      | 关闭                                                                |
| Target Provider | `source-a`                                                        |
| Target Model    | `demo-model`                                                      |
| Target Weight   | 100%                                                              |
| Fallbacks 顺序    | `source-b/demo-model`、`source-c/demo-model`、`source-d/demo-model` |


CEL 表达式：

```cel
model == "demo-model" && "x-demo-policy" in headers && headers["x-demo-policy"] == "cost"
```

请求头 `x-demo-policy: cost` 用于匹配这条规则。来源顺序由管理员根据报价配置，Bifrost 按规则执行。

验证命令：

```bash
python3 routing-demo/probe.py --policy cost --count 20 --concurrency 1
```

检查请求日志：首次目标应为 A，A 返回 503 时继续尝试 B。整个过程中，请求的模型名保持为 `demo-model`。

实际选择低价来源时，还需考虑失败尝试的费用与回退耗时。失败频繁的渠道可能抵消单价优势。

## 稳定性优先

关键在线业务更重视请求成功率，可以优先使用 D，再按稳定性顺序尝试 B、C、A。

在相同 Scope 下新增规则，Enabled 保持开启，Chain Rule 保持关闭：


| 字段           | 填写内容                                                              |
| ------------ | ----------------------------------------------------------------- |
| Name         | 四源稳定性优先                                                           |
| Scope        | 同一把演示 Virtual Key                                                 |
| Priority     | 20                                                                |
| CEL          | 下方表达式                                                             |
| Target       | `source-d / demo-model`，100%                                      |
| Fallbacks 顺序 | `source-b/demo-model`、`source-c/demo-model`、`source-a/demo-model` |


```cel
model == "demo-model" && "x-demo-policy" in headers && headers["x-demo-policy"] == "stable"
```

发送带有 `x-demo-policy: stable` 的请求：

```bash
python3 routing-demo/probe.py --policy stable --count 10 --concurrency 1
```

日志中的首次目标应为 D；出现失败时，再按配置顺序回退。与价格优先相比，这条规则接受更高的单价，以减少首次调用失败的概率。

## 高并发任务

批量任务会在短时间内产生较多请求。A 的并发上限为 5，C 为 100，因此将 C 设为批量任务首选，D、B、A 依次作为备用。

新增以下规则，保持 Enabled 开启、Chain Rule 关闭：


| 字段           | 填写内容                                                              |
| ------------ | ----------------------------------------------------------------- |
| Name         | 四源高并发任务                                                           |
| Scope        | 同一把演示 Virtual Key                                                 |
| Priority     | 30                                                                |
| CEL          | 下方表达式                                                             |
| Target       | `source-c / demo-model`，100%                                      |
| Fallbacks 顺序 | `source-d/demo-model`、`source-b/demo-model`、`source-a/demo-model` |


```cel
model == "demo-model" && "x-demo-policy" in headers && headers["x-demo-policy"] == "throughput"
```

备用来源的容量较小，C 故障时可能无法承接全部流量。正式使用时，应为批量任务设置合适的入口并发上限。

对比两次测试：

```bash
# 价格优先，但一次发来 20 个并发请求
python3 routing-demo/probe.py --policy cost --count 60 --concurrency 20

# 同样的请求规模，改用高并发策略
python3 routing-demo/probe.py --policy throughput --count 60 --concurrency 20
```

查看每个源的统计：

```bash
for port in 18081 18082 18083 18084; do
  curl -sS "http://127.0.0.1:$port/demo/stats"
  printf '\n'
done
```

记录两轮测试前后的统计，比较 `rejected_429` 的增量、失败次数和实际来源，同时查看测试脚本输出的平均耗时与 P95。模拟服务的统计从启动后累计，因此需要按前后差值比较。

价格优先策略下，A 更容易触发 429，部分请求需要通过回退完成。改为高并发策略后，首次请求直接进入 C，可以减少因 A 容量不足而产生的额外尝试。

### 并发与请求速率

并发指同一时刻正在处理的请求数，RPM 指一分钟内请求的数量。两者不是一个指标。

平均并发大致等于“每秒请求数 × 平均处理时间”。同样每秒 10 个请求，每次耗时 0.2 秒与 20 秒，对上游并发的需求完全不同。

这里的 `throughput` 标记用于识别批量任务，规则根据已知容量选择 C，并不实时计算上游的剩余并发。

## 按权重分配日常流量

没有指定策略的日常请求，按权重分配给 B 和 C。B 价格较低，承担 25% 的首次请求；C 容量较大，承担 75%。D 和 A 作为备用。

新增默认规则，保持 Enabled 开启、Chain Rule 关闭：


| 字段           | 填写内容                                        |
| ------------ | ------------------------------------------- |
| Name         | 四源默认均衡分流                                    |
| Scope        | 同一把演示 Virtual Key                           |
| Priority     | 100                                         |
| CEL          | `model == "demo-model"`                     |
| Target 1     | `source-b / demo-model`，25%                 |
| Target 2     | `source-c / demo-model`，75%                 |
| Fallbacks 顺序 | `source-d/demo-model`、`source-a/demo-model` |


25% 和 75% 是本例的初始比例，可根据实际流量、容量余量和费用调整。界面按百分比填写；JSON 模板中对应 `0.25` 和 `0.75`。

验证：

```bash
python3 routing-demo/probe.py --policy default --count 80 --concurrency 10
```

权重表示首次选择的概率，不保证每四个请求就严格一个 B、三个 C，也不保证某个来源永远不超并发。

测试脚本统计最终成功来源，结果可能包含回退到 D、A 的请求。验证权重时，应以路由日志中的首次 Target 为准。

### 规则优先级


| Priority | 策略标记         | 首次目标        | 回退顺序      |
| -------- | ------------ | ----------- | --------- |
| 10       | `cost`       | A           | B → C → D |
| 20       | `stable`     | D           | B → C → A |
| 30       | `throughput` | C           | D → B → A |
| 100      | 未被前面规则匹配的请求  | B 25%、C 75% | D → A     |


所有规则都关闭 Chain Rule。同一个 Scope 内数字越小越先匹配，命中就结束本轮选择。默认规则必须放在最后，否则它会先匹配全部 `demo-model` 请求。

没有携带策略标记，或者标记没有匹配前三条规则时，请求都会进入默认分流规则。

## 验证故障回退

将 A 临时设为持续返回 503，再发送价格优先请求：

```bash
curl -sS http://127.0.0.1:18081/demo/control \
  -H 'Content-Type: application/json' \
  -d '{"always_fail":true}'

python3 routing-demo/probe.py --policy cost --count 6 --concurrency 1
```

在 Bifrost 请求日志中确认尝试顺序：A 返回 503 后调用 B；如果 B 也失败，再继续尝试 C、D。

规则的首次目标仍为 A，因此后续请求也会先调用 A，再按需回退。

恢复 A：

```bash
curl -sS http://127.0.0.1:18081/demo/control \
  -H 'Content-Type: application/json' \
  -d '{"always_fail":false}'
```

如果 A 持续故障，也可以把规则的 Target 暂时改为 B，待 A 恢复后再切回。

## 按 Virtual Key 固定业务策略

前面的 `x-demo-policy` 用于在演示中方便地切换策略。实际接入时，如果每个业务有固定的路由需求，可以为业务分配不同的 Virtual Key，并把路由规则绑定到对应的 Key。调用方使用分配给自己的调用密钥即可，无需额外填写策略 Header。

例如，可以按以下方式配置。Virtual Key 的名称仅用于管理，实际策略由绑定的 Routing Rule 决定。


| 业务场景            | Virtual Key 名称   | 首次目标                          | Fallbacks 顺序 |
| --------------- | ---------------- | ----------------------------- | ------------ |
| 对成本敏感、允许重试的离线任务 | `cost-key`       | `source-a / demo-model`，100%  | B → C → D    |
| 更重视成功率的在线业务     | `stable-key`     | `source-d / demo-model`，100%  | B → C → A    |
| 大并发批量处理         | `throughput-key` | `source-c / demo-model`，100%  | D → B → A    |
| 日常均衡分流          | `default-key`    | B 25%、C 75%，模型均为 `demo-model` | D → A        |




### 配置方式

1. 在 Virtual Keys 中创建上述业务需要的 Key。每把 Key 都授权其 Target 和 Fallbacks 涉及的 Provider、`demo-model` 及上游 Key。本例四个来源都会用到，因此都需要授权；Provider 的 VK 权重仍可留空。
2. 为每把 Key 创建一条 Routing Rule，Scope 选择 **Virtual Key**，再选择对应的 Key。通过 API 配置时，`scope_id` 填该 Key 的内部 ID，调用时使用的是调用密钥。
3. 按表格填写 Routing Targets 和 Fallbacks。单一 Target 的权重为 `1`；默认分流的两个 Target 分别为 `0.25`、`0.75`。Fallbacks 中的模型均填写 `demo-model`。
4. 开启 Enabled，关闭 Chain Rule。每把 Key 只有这一条规则时，Priority 均可设为 `10`。

这些规则的 CEL 都可以简化为：

```cel
model == "demo-model"
```

请求使用的 Virtual Key 决定匹配哪一组规则，CEL 检查模型是否符合条件，Target 和 Fallbacks 再决定调用来源及失败后的尝试顺序。

四条规则需要分别绑定不同的 Virtual Key。若把它们都绑定到同一把 Key，并使用相同的 CEL，就会由优先匹配的规则决定目标，无法按业务区分。匹配的 Virtual Key 规则也会先于 Global 规则执行；Priority 数字只用于同一 Scope 内的排序。

### 调用与验证

以在线业务为例，将 `BF_VK` 设置为 `stable-key` 的调用密钥，继续使用前文的 `BASE_URL`，不再发送 `x-demo-policy`：

```bash
export BF_VK='替换成stable-key的调用密钥'

curl --fail-with-body -sS "$BASE_URL/v1/chat/completions" \
  -H "x-bf-vk: $BF_VK" \
  -H 'Content-Type: application/json' \
  -d '{"model":"demo-model","messages":[{"role":"user","content":"测试稳定性优先"}],"stream":false}'
```

该请求应命中绑定到 `stable-key` 的规则，首次调用 D，失败后依次尝试 B、C、A。换成 `cost-key` 的调用密钥，则使用价格优先规则，模型名仍为 `demo-model`。

也可以复用探测脚本：

```bash
python3 routing-demo/probe.py --policy default --count 10 --concurrency 1
```

这里的 `--policy default` 仅表示脚本不发送 `x-demo-policy`，并不强制网关使用 B/C 默认分流。实际匹配哪条规则取决于 `BF_VK`；当前使用 `stable-key`，日志中的首次目标仍应为 D。

如果同一个业务需要按任务切换策略，也可以继续保留 Header 方式，由业务后端根据任务类型自动填写，最终用户无需手动选择。

按 Virtual Key 绑定策略仍然是在执行管理员预先配置的目标、权重和回退顺序，不会自动查询报价或根据来源表现调整分配。

## 企业版自适应负载均衡

企业版的 Adaptive Load Balancing 根据来源实际的错误率、响应延迟等表现，自动调整流量分配。

例如，C 持续报错或响应变慢时，系统可以减少分配给它的流量，让其他表现更好的来源承接请求；C 恢复后，再根据后续请求的表现调整分配。

它和 Fallback 的区别是：Fallback 处理当前请求失败后的下一步，自适应负载均衡还会影响后续请求优先选择谁。

自适应负载均衡主要优化运行表现，价格优先和业务等级仍需单独配置，不会自动按供应商报价选择最低价来源。