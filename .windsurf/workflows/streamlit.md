---
description: Streamlit 项目部署和管理
---

# 项目清单

| 项目 | 本地路径 | GitHub 仓库 | Streamlit URL | 状态 |
|------|---------|-------------|---------------|------|
| **个人管理（合并版）** | `C:\Users\sweet\Downloads\CascadeProjects\personal_dashboard` | `uikgtrfdcw-commits/personal_dashboard` | https://personaldashboard-dja2pj9ghq5qpnx5ucwcfw.streamlit.app/ | 当前使用 |
| 任务清单（旧） | 已删除 | `uikgtrfdcw-commits/test_plan_dashboard` | https://test-pan.streamlit.app/ | 已合并到 personal_dashboard |
| 健身计划（旧） | 已删除 | `uikgtrfdcw-commits/fitness_dashboard` | https://uikgtrfdcw-commits-fitness-dashboard-streamlit-app-q04tub.streamlit.app/ | 已合并到 personal_dashboard |

# 共享基础设施

- **GitHub 用户名**: `uikgtrfdcw-commits`
- **Service Account**: `new-bot@poetic-hexagon-486001-s9.iam.gserviceaccount.com`
- **本地代理**: `http://127.0.0.1:7897`（系统全局代理端口）
- **Secrets 格式**: `[connections.gsheets]`，private_key 用 TOML 三引号多行字符串
- **注意**: secrets.toml 必须是 UTF-8 无 BOM 编码，否则 Streamlit 解析报错

# 推送代码到 GitHub

```powershell
git add -A
git commit -m "描述"
git config http.sslBackend schannel
git push origin main
```

Streamlit Cloud 会自动检测 GitHub 推送并重新部署。

# 本地测试

```powershell
python -m streamlit run streamlit_app.py --server.port 8505
```

手机局域网访问: `http://192.168.1.20:<端口>`

# Secrets 管理

- 本地: `.streamlit/secrets.toml`（已在 .gitignore 中，不会上传）
- 线上: Streamlit Cloud → App Settings → Secrets
- 两边内容需保持一致，格式为 TOML 三引号 private_key
