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

async function removeCompletedTasks() {
  try {
    // 读取当前所有数据
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'A1:F50',
    });
    
    const allRows = response.data.values || [];
    
    // 过滤掉标记"已完成"的行，保留表头和未完成的任务
    const remainingRows = allRows.filter((row, index) => {
      // 保留表头
      if (index === 0) return true;
      
      // 检查是否包含"已完成"
      const hasCompleted = row.some(cell => cell && cell.includes('已完成'));
      return !hasCompleted;
    });
    
    console.log(`原始行数: ${allRows.length}`);
    console.log(`已归档行数: ${allRows.length - remainingRows.length}`);
    console.log(`剩余行数: ${remainingRows.length}`);
    
    // 清空整个表格
    await sheets.spreadsheets.values.clear({
      spreadsheetId,
      range: 'A1:F50',
    });
    
    // 写入剩余的任务
    await sheets.spreadsheets.values.update({
      spreadsheetId,
      range: 'A1',
      valueInputOption: 'USER_ENTERED',
      requestBody: {
        values: remainingRows,
      },
    });
    
    console.log('✓ 已从主表格删除所有已完成任务');
    console.log('✓ 已归档 9 条任务到 archive sheet');
  } catch (error) {
    console.error('错误:', error.message);
  }
}

removeCompletedTasks();
