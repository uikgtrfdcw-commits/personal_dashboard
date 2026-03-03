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

// 生成简短的大类名称
function generateCategoryName(description) {
  if (description.includes('mcp') || description.includes('windsurf')) return 'AI工具配置';
  if (description.includes('gemini')) return 'AI工具迁移';
  if (description.includes('工作站')) return '设备采购';
  if (description.includes('中药') || description.includes('口腔') || description.includes('健康')) return '家庭健康';
  if (description.includes('AI') && description.includes('文章')) return 'AI文章写作';
  if (description.includes('文章') || description.includes('写作')) return '文章写作';
  if (description.includes('视频')) return '视频制作';
  return '其他任务';
}

async function archiveTasks() {
  try {
    console.log('开始归档任务...');
    
    // 1. 读取主表格
    const mainSheet = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'A1:F50',
    });
    
    const allRows = mainSheet.data.values || [];
    const completedTasks = [];
    const remainingRows = [];
    
    // 2. 分离已完成和未完成任务
    allRows.forEach((row, index) => {
      if (index === 0) {
        remainingRows.push(row); // 保留表头
        return;
      }
      
      const hasCompleted = row.some(cell => cell && cell.includes('已完成'));
      if (hasCompleted) {
        const [category, , description] = row;
        const today = new Date().toISOString().split('T')[0].replace(/-/g, '/');
        
        // 生成简短大类名称
        let newCategory = category || '';
        if (!newCategory || newCategory.includes('新增任务') || newCategory.includes('任务')) {
          newCategory = generateCategoryName(description || '');
        }
        newCategory = newCategory.replace(/^任务[一二三四五六七八九十\d]+[：:]\s*/, '');
        
        completedTasks.push([newCategory, description, today]);
      } else {
        remainingRows.push(row);
      }
    });
    
    console.log(`找到 ${completedTasks.length} 条已完成任务`);
    
    if (completedTasks.length === 0) {
      console.log('没有需要归档的任务');
      return;
    }
    
    // 3. 读取 archive sheet
    const archiveSheet = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range: 'archive!A1:C100',
    });
    
    const archiveRows = archiveSheet.data.values || [];
    const header = archiveRows[0] || ['大类任务', '描述', '完成日期'];
    const existingData = archiveRows.slice(1);
    
    // 4. 合并新旧数据并去重
    const allArchiveData = [...completedTasks, ...existingData];
    const seen = new Set();
    const uniqueData = allArchiveData.filter(row => {
      const key = `${row[1]}|${row[2]}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
    
    // 5. 按日期倒序排序
    uniqueData.sort((a, b) => {
      const dateA = (a[2] || '').replace(/\//g, '-');
      const dateB = (b[2] || '').replace(/\//g, '-');
      return dateB.localeCompare(dateA);
    });
    
    // 6. 更新 archive sheet
    await sheets.spreadsheets.values.clear({
      spreadsheetId,
      range: 'archive!A1:C100',
    });
    
    await sheets.spreadsheets.values.update({
      spreadsheetId,
      range: 'archive!A1',
      valueInputOption: 'USER_ENTERED',
      requestBody: {
        values: [header, ...uniqueData],
      },
    });
    
    console.log(`✓ 已归档 ${completedTasks.length} 条任务到 archive`);
    
    // 7. 更新主表格（删除已完成任务）
    await sheets.spreadsheets.values.clear({
      spreadsheetId,
      range: 'A1:F50',
    });
    
    await sheets.spreadsheets.values.update({
      spreadsheetId,
      range: 'A1',
      valueInputOption: 'USER_ENTERED',
      requestBody: {
        values: remainingRows,
      },
    });
    
    console.log(`✓ 已从主表格删除 ${completedTasks.length} 条已完成任务`);
    console.log('✓ 归档完成！');
    
  } catch (error) {
    console.error('错误:', error.message);
    process.exit(1);
  }
}

archiveTasks();
