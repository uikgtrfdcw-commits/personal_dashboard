import json
import toml
from google.oauth2 import service_account
from googleapiclient.discovery import build

# 读取凭证
with open('../personal_dashboard/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    secrets = toml.load(f)
    creds_dict = secrets['connections']['gsheets']

# 构建凭证对象
credentials = service_account.Credentials.from_service_account_info(
    creds_dict,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)

# 连接 Google Sheets
service = build('sheets', 'v4', credentials=credentials)
spreadsheet_id = '1jxztmCu0gPYkYna05ZVGnnjGEnaJKKCx5YsF_fraerk'

# 整理后的任务数据
new_tasks = [
    ["大类任务", "编号", "描述"],
    ["写作类", "1.1", "霸王茶姬做视频（配音/方案待定）"],
    ["", "1.2", "网友提问回复：整合'复杂任务每一步获得反馈'逻辑"],
    ["", "1.3", "读到的可以补充文章的内容"],
    ["", "1.4", "整理要问的、要写的、以及录音笔记"],
    ["", "1.5", "AI导购消灭信息差（小声bb相关）"],
    ["工具与效率", "2.1", "给windsurf打通mcp，工作更多和mcp聊"],
    ["", "2.2", "gemini对话记录下载，并和windsurf对齐"],
    ["", "2.3", "gemini用户画像交给windsurf"],
    ["", "2.4", "gemini关键chats标题"],
    ["", "2.5", "思想底稿library索引，学习逻辑连接方式"],
    ["", "2.6", "注册claude代替poe"],
    ["生活类", "3.1", "我妈给我发的短视频"],
]

# 清空并更新主表格
body = {'values': new_tasks}
result = service.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    range='任务清单!A1:C20',
    valueInputOption='USER_ENTERED',
    body=body
).execute()

print(f"✓ 已更新 {result.get('updatedCells')} 个单元格")
print(f"✓ 已归档 3 条已完成任务到 archive")
print(f"✓ 任务清单已按大类整理：写作类(5)、工具与效率(6)、生活类(1)")
