
# Git WorkTree, AI Coding时代效率提升利器

## Git WorkTree 是什么？

git worktree 作用是管理多个代码分支。但是你不用checkout分支，也不用`git clone`多份代码，就可以灵活在多个分支之间随意切换，然后在任意分支修改代码，是不是听起来就感觉很厉害。下面我们来通过项目实战加深理解。

## Hermes Git Worktree实战演示

通过hermes，先创建一个项目叫 `hermes-demo`。

```md
提示词：帮我在github创建一个名为hermes-demo的项目
```

将项目克隆到本地，初始化一个简单 Node 项目：

```bash
cat > package.json <<'EOF'
{
  "name": "hermes-demo",
  "version": "1.0.0",
  "scripts": {
    "start": "node app.js"
  }
}
EOF

cat > app.js <<'EOF'
function greet(name) {
  return `Hello, ${name}!`;
}

console.log(greet("Hermes"));
EOF

```

现在目录结构是：

```text
hermes-demo/
  app.js
  package.json
```

实现功能比较简单，就是打印"Hello Hermes"

---

现在我们需要给项目新增需求，用git worktree分别创建两个工作空间和分支。


创建第一个功能分支：添加中文问候。

```bash
git worktree add ../hermes-demo-feature-cn -b feature/chinese-greeting
```

创建第二个功能分支：添加 CLI 参数支持。

```bash
git worktree add ../hermes-demo-feature-cli -b feature/cli-name
```

---

**在 feature/chinese-greeting 开发**

```bash
cd ../hermes-demo-feature-cn
```


修改 `app.js`：

```js
function greet(name, lang = "en") {
  if (lang === "zh") {
    return `你好，${name}！`;
  }

  return `Hello, ${name}!`;
}

console.log(greet("Hermes", "zh"));
```

提交代码

---

**在 feature/cli-name 开发**

切到另一个 worktree：

```bash
cd ../hermes-demo-feature-cli
```

修改 `app.js`：

```js
function greet(name) {
  return `Hello, ${name}!`;
}

const name = process.argv[2] || "Hermes";

console.log(greet(name));
```

提交代码

运行：

```bash
node app.js Morris
```

输出：

```text
Hello, Morris!
```

---

假设我们在已经发布的main分支上，用户反馈了bug，然后我们可以随时从 main 创建 bugfix worktree

假设此时线上 main 有 bug：传空字符串时输出 `Hello, !`，我们要修成默认 `Guest`。

创建 bugfix 分支：

```bash
git  worktree add ../hermes-demo-bugfix-empty-name -b bugfix/empty-name
```

进入 bugfix worktree：

```bash
cd ../hermes-demo-bugfix-empty-name
```

修改 `app.js`：

```js
function greet(name) {
  const safeName = name && name.trim() ? name : "Guest";
  return `Hello, ${safeName}!`;
}

console.log(greet("Hermes"));
```

提交：

```bash
git add app.js
git commit -m "fix empty name greeting"
```

---

**合并 bugfix 回 main**

```bash
cd ../hermes-demo
git merge bugfix/empty-name
```

如果确认 bugfix worktree 不需要了，可以删除：

```bash
git worktree remove ../hermes-demo-bugfix-empty-name
```

删除本地分支：

```bash
git branch -d bugfix/empty-name
```

---

## git worktree 命令总结
```shell
# 查看所有worktree
git worktree list

# Create a new worktree
git worktree add ../repo-experiment-a -b feature/hermes-a

# Remove a worktree
git worktree remove <path>

# Prune stale worktree references
git worktree prune
```