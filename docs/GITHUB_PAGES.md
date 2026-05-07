# GitHub Pages 部署指南

## 快速部署

### 1. Fork 仓库

点击右上角的 **Fork** 按钮，将本项目复制到你的 GitHub 账号下。

### 2. 启用 GitHub Pages

1. 进入你 Fork 的仓库
2. 点击 **Settings** → **Pages**
3. **Source** 选择 **Deploy from a branch**
4. **Branch** 选择 **main** → **/(root)**
5. 点击 **Save**

### 3. 等待部署

大约 1-2 分钟后，访问：
```
https://yourusername.github.io/ai-image-lab
```

将 `yourusername` 替换为你的 GitHub 用户名。

## 自定义域名（可选）

1. 在 `docs/` 目录下创建 `CNAME` 文件
2. 写入你的域名，如：`ai.yourdomain.com`
3. 在域名 DNS 设置中添加 CNAME 记录指向 `yourusername.github.io`

## 注意事项

1. **模型文件较大** - GitHub 对单个文件限制 100MB，本项目模型文件均在限制内
2. **首次加载慢** - 需要下载模型文件到浏览器缓存
3. **缓存策略** - 模型文件会被浏览器缓存，后续访问秒开

## 更新部署

每次推送代码到 main 分支，GitHub Pages 会自动重新部署。
