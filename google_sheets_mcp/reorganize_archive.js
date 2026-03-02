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

// 给任务描述生成简短的大类名称
function generateCategoryName(description) {
  if (description.includes('mcp') || description.includes('windsurf')) return 'AI工具配置';
  if (description.includes('gemini') && description.includes('对话记录')) return 'AI工具迁移';
  if (description.includes('gemini') && description.includes('用户画像')) return 'AI工具迁移';
  if (description.includes('gemini') && description.includes('chats')) return 'AI工具迁移';
  if (description.includes('工作站')) return '设备采购';
  if (description.includes('中药') || description.includes('口腔')) return '家庭健康';
  if (description.includes('AI') && description.includes('文章')) return 'AI文章写作';
  return '其他任务';
}

async function reorganizeArchive() {
  try {
    // 读取 archive 所有数据
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'archive!A1:C100',
    });
    
    const allRows = response.data.values || [];
    const header = allRows[0];
    const dataRows = allRows.slice(1);
    
    // 处理数据：修改大类名称、去重
    const processedRows = [];
    const seen = new Set();
    
    for (const row of dataRows) {
      if (!row || row.length === 0) continue;
      
      const [category, description, date] = row;
      
      // 跳过空行
      if (!description && !date) continue;
      
      // 生成唯一键用于去重
      const key = `${description}|${date}`;
      if (seen.has(key)) continue;
      seen.add(key);
      
      // 如果大类是"新增任务"或为空，且是今天归档的，生成新的大类名称
      let newCategory = category;
      if ((category === '新增任务' || category === '' || category === '任务一：AI相关文章' || category === '任务二：工作站' || category === '生活类') && date === '2026/03/02') {
        newCategory = generateCategoryName(description);
      }
      
      // 去掉所有"任务X："前缀
      newCategory = newCategory.replace(/^任务[一二三四五六七八九十\d]+[：:]\s*/, '');
      
      // 不保存编号列（用户已删除）
      processedRows.push([newCategory, description, date]);
    }
    
    // 按日期倒序排序（最新的在前）
    processedRows.sort((a, b) => {
      const dateA = a[2] || ''; // 第3列是日期（索引2）
      const dateB = b[2] || '';
      
      // 标准化日期格式为 YYYY/MM/DD
      const normalizeDate = (dateStr) => {
        const parts = dateStr.split('/');
        if (parts.length === 3) {
          const [year, month, day] = parts;
          return `${year}/${month.padStart(2, '0')}/${day.padStart(2, '0')}`;
        }
        return dateStr;
      };
      
      const normalizedA = normalizeDate(dateA);
      const normalizedB = normalizeDate(dateB);
      
      return normalizedB.localeCompare(normalizedA);
    });
    
    // 合并表头和数据
    const finalRows = [header, ...processedRows];
    
    console.log(`原始数据行数: ${dataRows.length}`);
    console.log(`去重后行数: ${processedRows.length}`);
    console.log(`已删除重复项: ${dataRows.length - processedRows.length}`);
    
    // 清空 archive sheet
    await sheets.spreadsheets.values.clear({
      spreadsheetId,
      range: 'archive!A1:C100',
    });
    
    // 写入整理后的数据
    await sheets.spreadsheets.values.update({
      spreadsheetId,
      range: 'archive!A1',
      valueInputOption: 'USER_ENTERED',
      requestBody: {
        values: finalRows,
      },
    });
    
    console.log('✓ archive 已按日期倒序排序');
    console.log('✓ 大类名称已更新为简短总结');
    console.log('✓ 已去除重复条目');
  } catch (error) {
    console.error('错误:', error.message);
  }
}

reorganizeArchive();
