
const fs = require('fs');
const path = require('path');
const toml = require('toml');
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const { google } = require('googleapis');

// 代理设置：国内访问 Google API 必需
const proxyUrl = process.env.HTTPS_PROXY || process.env.https_proxy || 'http://127.0.0.1:17890';
try {
  const { HttpsProxyAgent } = require('https-proxy-agent');
  const agent = new HttpsProxyAgent(proxyUrl);
  google.options({ http2: false });
  require('https').globalAgent = agent;
} catch (e) {
  // 如果没有代理模块，继续使用直连
}

// 1. 读取 secrets.toml
const secretsPath = 'C:\\Users\\sweet\\Downloads\\CascadeProjects\\personal_dashboard\\.streamlit\\secrets.toml';
let credentials = null;

try {
  const secretsContent = fs.readFileSync(secretsPath, 'utf-8');
  const secrets = toml.parse(secretsContent);
  // Streamlit secrets format: [connections.gsheets]
  if (secrets.connections && secrets.connections.gsheets) {
    credentials = secrets.connections.gsheets;
  } else {
    console.error('Error: secrets.toml format not recognized');
    process.exit(1);
  }
} catch (error) {
  console.error('Error reading secrets.toml:', error);
  process.exit(1);
}

// 2. 初始化 Google Sheets API
const auth = new google.auth.JWT(
  credentials.client_email,
  null,
  credentials.private_key,
  ['https://www.googleapis.com/auth/spreadsheets']
);
const sheets = google.sheets({ version: 'v4', auth });

// 3. 初始化 MCP Server
const server = new Server(
  {
    name: "google-sheets-mcp",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// 4. 定义工具
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "read_sheet",
        description: "Read data from a Google Sheet",
        inputSchema: {
          type: "object",
          properties: {
            spreadsheetId: { type: "string" },
            range: { type: "string" },
          },
          required: ["spreadsheetId", "range"],
        },
      },
      {
        name: "append_row",
        description: "Append a row to a Google Sheet",
        inputSchema: {
          type: "object",
          properties: {
            spreadsheetId: { type: "string" },
            range: { type: "string" },
            values: { type: "array", items: { type: "string" } },
          },
          required: ["spreadsheetId", "range", "values"],
        },
      },
      {
        name: "update_range",
        description: "Update a range in a Google Sheet with new values (2D array)",
        inputSchema: {
          type: "object",
          properties: {
            spreadsheetId: { type: "string" },
            range: { type: "string" },
            values: { type: "array", items: { type: "array", items: { type: "string" } } },
          },
          required: ["spreadsheetId", "range", "values"],
        },
      },
    ],
  };
});

// 5. 实现工具逻辑
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    if (request.params.name === "read_sheet") {
      const { spreadsheetId, range } = request.params.arguments;
      const response = await sheets.spreadsheets.values.get({
        spreadsheetId,
        range,
      });
      return {
        content: [{ type: "text", text: JSON.stringify(response.data.values) }],
      };
    } else if (request.params.name === "append_row") {
      const { spreadsheetId, range, values } = request.params.arguments;
      const response = await sheets.spreadsheets.values.append({
        spreadsheetId,
        range,
        valueInputOption: "USER_ENTERED",
        requestBody: {
          values: [values],
        },
      });
      return {
        content: [{ type: "text", text: JSON.stringify(response.data) }],
      };
    } else if (request.params.name === "update_range") {
      const { spreadsheetId, range, values } = request.params.arguments;
      const response = await sheets.spreadsheets.values.update({
        spreadsheetId,
        range,
        valueInputOption: "USER_ENTERED",
        requestBody: {
          values: values,
        },
      });
      return {
        content: [{ type: "text", text: JSON.stringify(response.data) }],
      };
    }
  } catch (error) {
    return {
      content: [{ type: "text", text: `Error: ${error.message}` }],
      isError: true,
    };
  }
});

// 6. 启动 Server
async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

run().catch(console.error);
