# TypeScript/Agent开发的Node环境管理工具：nvm使用教程

## 1. 背景说明

随着 AI Agent 应用的发展，TypeScript 已经逐渐成为 Agent 开发中的最主流的语言。Node.js 是TypeScript的运行基础，而 `nvm` 是管理 Node.js 环境最常用、最方便的工具之一。

很多同学对 Python 比较熟悉，会自然地使用 `venv`、`conda`、`uv` 等虚拟环境来隔离依赖和运行时版本。Node.js 的项目也类似：同样需要管理和隔离运行时版本，避免不同项目之间相互影响。隔离环境就是本期要讲解的nvm。

本期视频详细讲解安装、使用技巧、常见问题解决方案等方面为大家详细讲解。

## 2. nvm是什么

`nvm` 是 [Node Version Manager](https://github.com/nvm-sh/nvm) 的缩写，用来在同一台电脑上安装、切换和管理多个 Node.js 版本。

在实际开发中，不同项目经常依赖不同的 Node 版本：

- 老项目可能只能在 Node 14 或 Node 16 下正常运行。
- 新项目可能需要 Node 18、Node 20 或更高版本。
- 公司项目通常会在 `.nvmrc` 中固定 Node 版本，避免团队成员环境不一致。

使用 `nvm` 后，不需要反复卸载和重装 Node，只要一条命令就能切换版本。

## 3. 适用环境

官方 `nvm` 主要适用于：

- macOS
- Linux
- Windows WSL

如果是原生 Windows，可以使用 `nvm-windows`，命令和本文略有差异。

## 4. 安装nvm

### 4.1 macOS / Linux安装

执行官方安装脚本：

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
```

如果没有 `curl`，也可以使用 `wget`：

```bash
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
```

安装完成后，重新打开终端，或者手动加载配置。

如果使用的是 `zsh`：

```bash
source ~/.zshrc
```

如果使用的是 `bash`：

```bash
source ~/.bashrc
```

### 4.2 验证安装

```bash
command -v nvm
```

如果输出：

```bash
nvm
```

说明安装成功。

注意：不要用 `which nvm` 验证，因为 `nvm` 是 shell 函数，不是普通可执行文件。

## 5. 安装Node.js版本

### 5.1 安装最新LTS版本

```bash
nvm install --lts
```

LTS 是 Long Term Support 的缩写，表示长期支持版本，适合大多数生产项目。

### 5.2 安装指定版本

```bash
nvm install 16
nvm install 18
nvm install 20
nvm install 20.11.1
```

只写主版本号时，`nvm` 会安装该主版本下可用的最新小版本。

### 5.3 查看远程可安装版本

```bash
nvm ls-remote
```

只查看 LTS 版本：

```bash
nvm ls-remote --lts
```

## 6. 查看和切换Node版本

### 6.1 查看本机已安装版本

```bash
nvm ls
```

示例输出：

```bash
       v14.21.3
       v16.20.2
->     v20.11.1
default -> 20
node -> stable
```

其中 `->` 表示当前正在使用的版本。

### 6.2 切换到指定版本

```bash
nvm use 16
node -v
```

示例输出：

```bash
Now using node v16.20.2
v16.20.2
```

切换到 Node 20：

```bash
nvm use 20
node -v
```

### 6.3 设置默认Node版本

```bash
nvm alias default 20
```

设置后，每次打开新终端都会默认使用 Node 20。

也可以设置为最新 LTS：

```bash
nvm alias default 'lts/*'
```

## 7. 实际案例：两个项目使用不同Node版本

下面用一个真实开发场景演示：同一台电脑上有两个项目。

- `old-vue-project`：老 Vue CLI 项目，需要 Node 18。
- `new-vite-project`：新 Vite 项目，需要 Node 20。

### 7.1 准备两个项目目录

```bash
mkdir -p ~/demo-nvm/old-vue-project
mkdir -p ~/demo-nvm/new-vite-project
```

### 7.2 为老项目指定Node 14

```bash
cd ~/demo-nvm/old-vue-project
echo "18" > .nvmrc
nvm install
nvm use
node -v
```

创建一个简单的测试文件：

```bash
cat > index.js <<'EOF'
console.log('old project node version:', process.version)
EOF
node index.js
```

### 7.3 为新项目指定Node 20

```bash
cd ~/demo-nvm/new-vite-project
echo "20" > .nvmrc
nvm install
nvm use
node -v
```

示例输出：

```bash
Found '/Users/yourname/demo-nvm/new-vite-project/.nvmrc' with version <20>
Now using node v20.11.1
v20.11.1
```

创建一个简单的测试文件：

```bash
cat > index.js <<'EOF'
console.log('new project node version:', process.version)
EOF
node index.js
```

示例输出：

```bash
new project node version: v20.11.1
```

### 7.4 在两个项目之间切换

回到老项目：

```bash
cd ~/demo-nvm/old-vue-project
nvm use
node index.js
```

示例输出：

```bash
Now using node v14.21.3
old project node version: v14.21.3
```

切到新项目：

```bash
cd ~/demo-nvm/new-vite-project
nvm use
node index.js
```

示例输出：

```bash
Now using node v20.11.1
new project node version: v20.11.1
```

只要每个项目维护自己的 `.nvmrc`，就可以在不同项目之间安全切换 Node 版本。

## 8. 全局npm包和Node版本的关系

使用 `nvm` 时，每个 Node 版本都有自己独立的全局 npm 包目录。

例如在 Node 16 下安装：

```bash
nvm use 16
npm install -g pnpm
```

切换到 Node 20 后：

```bash
nvm use 20
pnpm -v
```

可能会提示找不到 `pnpm`，因为 Node 20 下还没有安装这个全局包。

解决方式是在当前版本下重新安装：

```bash
npm install -g pnpm
```

如果安装新 Node 版本时想迁移旧版本的全局包，可以使用：

```bash
nvm install 20 --reinstall-packages-from=16
```

## 9. 常用命令速查


| 命令                     | 说明                   |
| ---------------------- | -------------------- |
| `nvm --version`        | 查看 nvm 版本            |
| `nvm install --lts`    | 安装最新 LTS Node        |
| `nvm install 20`       | 安装 Node 20           |
| `nvm use 20`           | 切换到 Node 20          |
| `nvm use`              | 使用当前目录 `.nvmrc` 中的版本 |
| `nvm install`          | 安装当前目录 `.nvmrc` 中的版本 |
| `nvm ls`               | 查看本机已安装 Node 版本      |
| `nvm ls-remote`        | 查看远程可安装 Node 版本      |
| `nvm ls-remote --lts`  | 查看远程 LTS 版本          |
| `nvm alias default 20` | 设置默认 Node 版本         |
| `nvm current`          | 查看当前正在使用的版本          |
| `nvm uninstall 16`     | 卸载 Node 16           |
| `nvm which 20`         | 查看 Node 20 的安装路径     |
| `nvm exec 20 node -v`  | 临时用 Node 20 执行命令     |


## 10. 常见问题

### 10.1 nvm: command not found

原因通常是 shell 配置没有加载。

如果是 `zsh`：

```bash
source ~/.zshrc
```

如果是 `bash`：

```bash
source ~/.bashrc
```

如果仍然不行，检查配置文件里是否有下面内容：

```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
```

macOS 用户如果没有 `.zshrc`，可以先创建：

```bash
touch ~/.zshrc
```

然后重新执行安装脚本。

### 10.2 npm全局安装需要sudo吗

使用 `nvm` 后，一般不需要 `sudo`：

```bash
npm install -g pnpm
```

不要写成：

```bash
sudo npm install -g pnpm
```

因为 `nvm` 管理的 Node 安装在用户目录下，使用 `sudo` 反而可能导致权限混乱。

### 10.3 为什么切换版本后npm包不见了?

因为每个 Node 版本有独立的全局包目录。

查看当前全局包：

```bash
npm list -g --depth=0
```

需要哪个版本使用这些工具，就在哪个 Node 版本下重新安装。

### 10.4 如何删除不需要的Node版本?

先切换到其他版本：

```bash
nvm use 20
```

再删除旧版本：

```bash
nvm uninstall 14
```

## 11. 总结

`nvm` 的核心使用流程很简单：

```bash
nvm install 20
nvm use 20
nvm alias default 20
```

项目中推荐增加 `.nvmrc`：

```bash
echo "20" > .nvmrc
```

以后进入项目后执行：

```bash
nvm use
```

就可以自动切换到项目需要的 Node 版本。