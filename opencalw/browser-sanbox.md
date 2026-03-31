


开启沙箱浏览器工具配置
```json
 "tools": {
    "profile": "coding",
    "sandbox": {
      "tools": {
        "allow": [
          "exec",
          "process",
          "read",
          "write",
          "edit",
          "apply_patch",
          "sessions_list",
          "sessions_history",
          "sessions_send",
          "sessions_spawn",
          "session_status",
          "browser"
        ],
        "deny": [
          "canvas",
          "nodes",
          "cron",
          "discord",
          "gateway"
        ]
      }
    }
  }
```