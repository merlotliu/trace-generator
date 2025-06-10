# Tracegen 安装指南

## 🚀 快速安装

### 🍺 macOS 用户（推荐 Homebrew）

```bash
# 1. 添加理想汽车内部 Homebrew Tap
brew tap lixiang/tools git@gitlab.lixiang.com:homebrew/tap.git

# 2. 安装 tracegen
brew install tracegen

# 3. 验证安装
tracegen --help
```

### 🐧 Ubuntu/WSL 用户（推荐 APT）

```bash
# 1. 添加理想汽车内部 APT 源
echo 'deb https://apt.lixiang.com/ubuntu jammy main' | sudo tee /etc/apt/sources.list.d/lixiang.list

# 2. 添加 GPG 密钥（如果需要）
wget -qO - https://apt.lixiang.com/pubkey.gpg | sudo apt-key add -

# 3. 更新包列表并安装
sudo apt update
sudo apt install tracegen

# 4. 验证安装
tracegen --help
```

## 📋 使用示例

安装成功后，您可以直接使用 `tracegen` 命令：

```bash
# 基本用法
tracegen -v HLX33B121R1647380 \
         -s "2025-02-06 21:40:14" \
         -e "2025-02-06 22:10:14" \
         -t short -t gfx \
         --timezone +0800

# 查看帮助
tracegen --help

# 查看版本
tracegen --version
```

## 🔄 版本更新

### macOS (Homebrew)
```bash
# 更新 tap
brew update

# 升级 tracegen
brew upgrade tracegen
```

### Ubuntu/WSL (APT)
```bash
# 更新包列表
sudo apt update

# 升级 tracegen
sudo apt upgrade tracegen
```

## 🗑️ 卸载

### macOS (Homebrew)
```bash
# 卸载工具
brew uninstall tracegen

# 可选：移除 tap
brew untap lixiang/tools
```

### Ubuntu/WSL (APT)
```bash
# 卸载工具
sudo apt remove tracegen

# 可选：移除 APT 源
sudo rm /etc/apt/sources.list.d/lixiang.list
sudo apt update
```

## 🛠️ 开发者安装

如果您需要修改源码或参与开发：

```bash
# 克隆仓库
git clone git@gitlab.lixiang.com:tools/tracegen.git
cd tracegen

# 开发模式安装
pip install -e .

# 运行
tracegen --help
```

## ❓ 常见问题

### Q: 安装时提示权限不足？
A: 请确保您有管理员权限，使用 `sudo` 执行相关命令。

### Q: macOS 上提示找不到 brew 命令？
A: 请先安装 Homebrew：
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Q: Ubuntu 上提示 GPG 密钥验证失败？
A: 请联系 IT 管理员获取正确的 GPG 密钥，或临时跳过验证：
```bash
sudo apt install --allow-unauthenticated tracegen
```

### Q: Windows 用户如何安装？
A: 推荐使用 WSL (Windows Subsystem for Linux)：
1. 安装 WSL 2 和 Ubuntu
2. 按照 Ubuntu 安装步骤操作

### Q: 如何查看当前安装的版本？
A: 使用以下命令：
```bash
tracegen --version
# 或者
dpkg -l | grep tracegen  # Ubuntu
brew list --versions tracegen  # macOS
```

## 🔐 权限说明

本工具需要访问：
- 网络连接（获取车辆数据）
- 文件系统（保存 trace 文件）
- 系统时间（时区处理）

所有数据处理均在本地进行，不会上传到外部服务器。

## 📞 技术支持

如遇到安装或使用问题，请联系：

- **项目负责人**：刘某某 (liumoulu@lixiang.com)
- **GitLab Issues**：https://gitlab.lixiang.com/tools/tracegen/-/issues
- **内部文档**：https://wiki.lixiang.com/tools/tracegen

---

**内部工具 - 仅限理想汽车员工使用** 