# 部署指南

## 第一步：创建 GitHub 仓库

1. 访问 [github.com](https://github.com) 并登录
2. 点击右上角 "+" → "New repository"
3. 仓库名称填：`chinese-typo-checker`
4. 选择 "Public"（公开）
5. 点击 "Create repository"

## 第二步：上传代码

### 方法 A：使用 GitHub Desktop（推荐新手）

1. 下载安装 [GitHub Desktop](https://desktop.github.com/)
2. 登录你的 GitHub 账号
3. 点击 "File" → "Add Local Repository"
4. 选择 `d:\textVScode\typo_checker` 文件夹
5. 点击 "Publish repository" 上传

### 方法 B：使用命令行

```bash
cd d:\textVScode\typo_checker
git init
git add .
git commit -m "初始化中文错别字检查工具"
git branch -M main
git remote add origin https://github.com/你的用户名/chinese-typo-checker.git
git push -u origin main
```

## 第三步：部署到 Streamlit Cloud

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 使用 GitHub 账号登录
3. 点击 "New app"
4. 选择：
   - Repository: `你的用户名/chinese-typo-checker`
   - Branch: `main`
   - Main file path: `app.py`
5. 点击 "Deploy"

## 第四步：获取永久链接

部署完成后（约 2-5 分钟），你会获得一个永久链接：
```
https://chinese-typo-checker-你的用户名.streamlit.app
```

这个链接可以：
- 直接在浏览器中打开使用
- 添加到浏览器收藏夹
- 分享给其他人使用

## 可选：配置 AI 功能

如果需要 AI 优化建议功能：

1. 在 Streamlit Cloud 中打开你的应用
2. 点击右上角 "Settings"
3. 点击 "Secrets"
4. 添加以下内容：
```toml
DASHSCOPE_API_KEY = "你的通义千问API密钥"
```
5. 点击 "Save"

获取通义千问 API Key：[dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/)

---

## 注意事项

- 免费版 Streamlit Cloud 每月有 1000 小时运行时间
- 应用长时间无人访问会进入睡眠，首次访问需要等待几秒唤醒
- 如果部署失败，检查 `requirements.txt` 中的依赖是否正确
