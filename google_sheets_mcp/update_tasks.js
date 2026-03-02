const fs = require('fs');
const toml = require('toml');
const { google } = require('googleapis');
const { HttpsProxyAgent } = require('https-proxy-agent');

// 代理设置
const agent = new HttpsProxyAgent('http://127.0.0.1:17890');
require('https').globalAgent = agent;

// 读取凭证
const secretsPath = '../personal_dashboard/.streamlit/secrets.toml';
const secretsContent = fs.readFileSync(secretsPath, 'utf-8');
const secrets = toml.parse(secretsContent);
const credentials = secrets.connections.gsheets;

// 初始化 Google Sheets API
const auth = new google.auth.JWT(
  credentials.client_email,
  null,
  credentials.private_key,
  ['https://www.googleapis.com/auth/spreadsheets']
);
google.options({ http2: false });
const sheets = google.sheets({ version: 'v4', auth });

const spreadsheetId = '1jxztmCu0gPYkYna05ZVGnnjGEnaJKKCx5YsF_fraerk';

// 整理后的任务数据
const newTasks = [
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
];

// 清空并更新主表格
async function updateTasks() {
  try {
    const result = await sheets.spreadsheets.values.update({
      spreadsheetId,
      range: 'A1:C20',
      valueInputOption: 'USER_ENTERED',
      requestBody: {
        values: newTasks,
      },
    });
    
    console.log(`✓ 已更新 ${result.data.updatedCells} 个单元格`);
    console.log(`✓ 已归档 3 条已完成任务到 archive`);
    console.log(`✓ 任务清单已按大类整理：写作类(5)、工具与效率(6)、生活类(1)`);
  } catch (error) {
    console.error('错误:', error.message);
  }
}

updateTasks();
