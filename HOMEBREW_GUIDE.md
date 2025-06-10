# Tracegen Homebrew 发布指南

## 前提条件

1. ✅ 已创建 `setup.py` 
2. ✅ 已构建包文件（`python -m build`）
3. ✅ 已创建 `tracegen.rb` formula 文件
4. ⏳ 需要发布到 PyPI
5. ⏳ 需要创建 Homebrew Tap

## 发布步骤

### 1. 发布到 PyPI

```bash
# 创建 PyPI 账号：https://pypi.org/account/register/
# 创建 API Token：https://pypi.org/manage/account/token/

# 配置 twine 认证
echo "[pypi]" > ~/.pypirc
echo "username = __token__" >> ~/.pypirc
echo "password = your-api-token-here" >> ~/.pypirc

# 发布
python -m twine upload dist/*
```

### 2. 创建 Homebrew Tap (推荐)

#### 方式A：个人 Tap（简单）

1. 在 GitHub 创建仓库：`homebrew-tools`
2. 将 `tracegen.rb` 上传到仓库
3. 用户安装命令：`brew install yourusername/tools/tracegen`

#### 方式B：官方 Homebrew Core（复杂）

1. Fork [homebrew-core](https://github.com/Homebrew/homebrew-core)
2. 添加 formula 到 `Formula/` 目录
3. 提交 Pull Request

### 3. 测试安装

```bash
# 本地测试
brew install --build-from-source ./tracegen.rb

# 测试命令
tracegen --help
```

## Formula 文件说明

您的 `tracegen.rb` 已配置好：
- SHA256: `e1dd1e21c963c29fb64a87f0e52010ff94c2615fa93f052720a5493fb2395125`
- 依赖：Python 3.11+
- 入口点：`tracegen` 命令

## 注意事项

1. 更新 `tracegen.rb` 中的 GitHub URL
2. 选择合适的开源许可证
3. 每次发布新版本时更新 SHA256 和版本号

## 用户使用方式

安装您的工具后，用户可以：

```bash
# 直接使用
tracegen -v HLX33B121R1647380 -s "2025-02-06 21:40:14" -e "2025-02-06 22:10:14" -t short -t gfx

# 查看帮助
tracegen --help
``` 