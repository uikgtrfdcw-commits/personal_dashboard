# GitHub Actions 定时任务设置指南

## 前提条件

你需要有一个 GitHub 仓库来存放这个项目。如果还没有，需要先创建一个。

## 设置步骤

### 1. 推送代码到 GitHub

将整个 `CascadeProjects` 文件夹推送到 GitHub 仓库：

```bash
cd C:\Users\sweet\Downloads\CascadeProjects
git init
git add .
git commit -m "Initial commit: Google Sheets task automation"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

### 2. 设置 GitHub Secrets

GitHub Actions 需要 Google Sheets API 凭证才能访问你的表格。这些凭证需要作为 Secrets 存储。

#### 2.1 获取凭证信息

打开 `personal_dashboard/.streamlit/secrets.toml` 文件，你会看到类似这样的内容：

```toml
[connections.gsheets]
type = "service_account"
project_id = "poetic-hexagon-486001-s9"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "new-bot@poetic-hexagon-486001-s9.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

#### 2.2 在 GitHub 添加 Secrets

1. 打开你的 GitHub 仓库页面
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. 逐个添加以下 Secrets（名称必须完全一致）：

| Secret 名称 | 值（从 secrets.toml 复制） |
|---|---|
| `GSHEET_TYPE` | `service_account` |
| `GSHEET_PROJECT_ID` | 你的 project_id |
| `GSHEET_PRIVATE_KEY_ID` | 你的 private_key_id |
| `GSHEET_PRIVATE_KEY` | 你的 private_key（完整内容，包括 BEGIN 和 END） |
| `GSHEET_CLIENT_EMAIL` | 你的 client_email |
| `GSHEET_CLIENT_ID` | 你的 client_id |
| `GSHEET_AUTH_URI` | `https://accounts.google.com/o/oauth2/auth` |
| `GSHEET_TOKEN_URI` | `https://oauth2.googleapis.com/token` |
| `GSHEET_AUTH_PROVIDER_CERT_URL` | `https://www.googleapis.com/oauth2/v1/certs` |
| `GSHEET_CLIENT_CERT_URL` | 你的 client_x509_cert_url |
| `GSHEET_UNIVERSE_DOMAIN` | `googleapis.com` |

**重要提示**：
- `GSHEET_PRIVATE_KEY` 的值需要保留所有的 `\n` 换行符
- 复制时确保没有多余的空格或换行

### 3. 验证 workflow 文件

确认 `.github/workflows/organize-tasks.yml` 文件已经推送到仓库。

### 4. 测试运行

#### 手动触发测试

1. 在 GitHub 仓库页面，点击 **Actions** 标签
2. 在左侧选择 **整理 Google Sheets 任务清单**
3. 点击右侧的 **Run workflow** 按钮
4. 选择 `main` 分支，点击 **Run workflow**
5. 等待几秒，刷新页面，查看运行结果

如果运行成功，你会看到绿色的 ✓ 标记。点击进去可以查看详细日志。

#### 自动定时运行

设置完成后，GitHub Actions 会：
- **每天下午 3 点**（北京时间）自动运行
- 归档所有标记"已完成"的任务
- 从主表格删除已归档任务
- 整理 archive sheet（改名、去重、排序）

### 5. 查看执行日志

每次运行后，可以在 GitHub Actions 页面查看：
- 归档了多少条任务
- 删除了多少行
- 是否有错误

## 故障排查

### 错误：API 认证失败

检查：
1. 所有 Secrets 是否都正确设置
2. `GSHEET_PRIVATE_KEY` 是否包含完整的 private key（包括 BEGIN 和 END 行）
3. Google Sheets API 是否已启用

### 错误：找不到 spreadsheet

检查：
1. Service Account 邮箱（`client_email`）是否已添加到 Google Sheets 的共享权限
2. Spreadsheet ID 是否正确（在脚本中硬编码为 `1jxztmCu0gPYkYna05ZVGnnjGEnaJKKCx5YsF_fraerk`）

### 修改定时时间

如果想改变执行时间，编辑 `.github/workflows/organize-tasks.yml`：

```yaml
schedule:
  # cron 格式：分 时 日 月 周
  # 下午3点北京时间 = UTC 7:00
  - cron: '0 7 * * *'
```

例如改为每天早上 9 点（北京时间）：
```yaml
- cron: '0 1 * * *'  # UTC 1:00 = 北京时间 9:00
```

## 关于费用

GitHub Actions 对公开仓库完全免费，私有仓库每月有 2000 分钟免费额度。这个任务每次只需几秒钟，完全在免费额度内。

---

**设置完成后，你就可以关机了，GitHub Actions 会在云端自动运行！**
