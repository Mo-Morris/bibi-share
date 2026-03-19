
安装飞书插件：
```shell
docker compose -f docker-compose.yml run --rm openclaw-cli \
  plugins install @openclaw/feishu
```

导入如下权限：
```json
{
  "scopes": {
    "tenant": [
      "aily:file:read",
      "aily:file:write",
      "application:application.app_message_stats.overview:readonly",
      "application:application:self_manage",
      "application:bot.menu:write",
      "cardkit:card:read",
      "cardkit:card:write",
      "contact:user.employee_id:readonly",
      "corehr:file:download",
      "event:ip_list",
      "im:chat.access_event.bot_p2p_chat:read",
      "im:chat.members:bot_access",
      "im:message",
      "im:message.group_at_msg:readonly",
      "im:message.p2p_msg:readonly",
      "im:message:readonly",
      "im:message:send_as_bot",
      "im:resource"
    ],
    "user": [
      "aily:file:read",
      "aily:file:write",
      "im:chat.access_event.bot_p2p_chat:read"
    ]
  }
}
```

修改配置
```shell
docker compose -f docker-compose.yml run --rm openclaw-cli \
  config
```

设置配对码
```shell
docker compose -f docker-compose.yml run --rm openclaw-cli \
    pairing approve feishu <your pair code>
```










----