# GitHub Actions 自动归档设置

## 快速开始

### 1. 推送代码到 GitHub

```bash
cd C:\Users\sweet\Downloads\CascadeProjects
git add .
git commit -m "Add task archiving automation"
git push origin main
```

### 2. 设置 GitHub Secrets

在 GitHub 仓库页面：**Settings** → **Secrets and variables** → **Actions** → **New repository secret**

需要添加的 Secrets（从 `personal_dashboard/.streamlit/secrets.toml` 复制）：

- `GSHEET_TYPE` = `service_account`
- `GSHEET_PROJECT_ID`
- `GSHEET_PRIVATE_KEY_ID`
- `GSHEET_PRIVATE_KEY`（完整内容，包括 `-----BEGIN PRIVATE KEY-----` 和 `-----END PRIVATE KEY-----`）
- `GSHEET_CLIENT_EMAIL`
- `GSHEET_CLIENT_ID`
- `GSHEET_AUTH_URI` = `https://accounts.google.com/o/oauth2/auth`
- `GSHEET_TOKEN_URI` = `https://oauth2.googleapis.com/token`
- `GSHEET_AUTH_PROVIDER_CERT_URL` = `https://www.googleapis.com/oauth2/v1/certs`
- `GSHEET_CLIENT_CERT_URL`
- `GSHEET_UNIVERSE_DOMAIN` = `googleapis.com`

### 3. 测试运行

在 GitHub 仓库的 **Actions** 标签页：
1. 选择 "归档已完成任务"
2. 点击 **Run workflow**
3. 查看运行结果

## 功能说明

- **自动运行**：每天下午 3 点（北京时间）
- **归档逻辑**：
  - 找出所有包含"已完成"的任务
  - 生成简短的大类名称
  - 追加到 archive sheet
  - 从主表格删除
  - 按日期倒序排序
  - 自动去重

## 本地测试

```bash
cd google_sheets_mcp
node archive_tasks.js
```

## 修改定时时间

编辑 `.github/workflows/archive-tasks.yml`：

```yaml
schedule:
  - cron: '0 7 * * *'  # UTC 7:00 = 北京时间 15:00
```

改为每天早上 9 点：`cron: '0 1 * * *'`
