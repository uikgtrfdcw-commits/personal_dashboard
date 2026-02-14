import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from streamlit_js_eval import streamlit_js_eval

# ============================================================
# Google Sheets 配置
# ============================================================
FITNESS_SPREADSHEET_ID = "1Mej0V4ql4P6hFDPstAJX-aD_Uea3ualUWgSJun6qHjs"
TASK_SPREADSHEET_ID = "1jxztmCu0gPYkYna05ZVGnnjGEnaJKKCx5YsF_fraerk"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

st.set_page_config(page_title="个人管理", page_icon="📋", layout="wide")


# ============================================================
# 数据加载
# ============================================================
@st.cache_resource
def _get_client() -> gspread.Client:
    conn_secrets = dict(st.secrets["connections"]["gsheets"])
    creds = Credentials.from_service_account_info(conn_secrets, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_data(ttl=300)
def load_sheet(_gc, spreadsheet_id, title):
    sh = _gc.open_by_key(spreadsheet_id)
    ws = sh.worksheet(title)
    values = ws.get_all_values()
    if not values or len(values) < 2:
        return pd.DataFrame()
    return pd.DataFrame(values[1:], columns=values[0])


def get_day_data(df):
    """将周训练计划按训练日分组"""
    df.iloc[:, 0] = df.iloc[:, 0].replace("", pd.NA).ffill().fillna("")
    days = df.iloc[:, 0].unique().tolist()
    return {day: df[df.iloc[:, 0] == day].reset_index(drop=True) for day in days}


# ============================================================
# 颜色/样式映射（健身）
# ============================================================
DAY_COLORS = {
    "每日通用热身": ("#1565c0", "#f5f7fa", "🔥"),
    "每日练后拉伸": ("#1565c0", "#f5f7fa", "🧘"),
    "第1天：下肢+核心": ("#1565c0", "#f5f7fa", "🦵"),
    "第2天：上肢拉": ("#1565c0", "#f5f7fa", "💪"),
    "第3天：轻量全身+恢复": ("#1565c0", "#f5f7fa", "🌿"),
    "第4天：上肢推": ("#1565c0", "#f5f7fa", "🏋️"),
    "第5天：后链+下肢": ("#1565c0", "#f5f7fa", "🔗"),
    "第6天：灵活性+松解": ("#1565c0", "#f5f7fa", "🧘"),
    "第7天：完全休息": ("#1565c0", "#f5f7fa", "😴"),
}

TYPE_BADGES = {
    "💪": ("复合", "#555", "#f0f0f0"),
    "🎯": ("孤立", "#555", "#f0f0f0"),
    "🔧": ("激活", "#555", "#f0f0f0"),
    "🧘": ("拉伸", "#555", "#f0f0f0"),
}

CATEGORY_COLORS = {
    "🔴 伤病状况": ("#c62828", "#fef5f5"),
    "🚫 训练禁忌": ("#c62828", "#fef5f5"),
    "🟡 环境因素": ("#555", "#f5f7fa"),
    "🟢 恢复策略": ("#555", "#f5f7fa"),
    "🔵 营养与作息": ("#555", "#f5f7fa"),
    "📋 训练原则": ("#555", "#f5f7fa"),
}

PRIORITY_STYLE = {
    "高": ("#c62828", "#fff0f0"),
    "中": ("#e65100", "#fff3e0"),
    "低": ("#2e7d32", "#e8f5e9"),
}

STATUS_STYLE = {
    "执行中": ("#1565c0", "#e3f2fd"),
    "已修正": ("#2e7d32", "#e8f5e9"),
    "观察中": ("#f57f17", "#fffde7"),
    "每次练前": ("#6a1b9a", "#f3e5f5"),
    "条件跳过": ("#e65100", "#fff3e0"),
    "长期执行": ("#00695c", "#e0f7fa"),
    "备选方案": ("#546e7a", "#eceff1"),
    "推荐使用": ("#2e7d32", "#e8f5e9"),
    "谨慎使用": ("#e65100", "#fff3e0"),
}


def _get_type_badge(action_type: str) -> str:
    for emoji, (label, color, bg) in TYPE_BADGES.items():
        if emoji in str(action_type):
            return f'<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600;color:{color};background:{bg};">{emoji} {label}</span>'
    if action_type.strip():
        return f'<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;background:#f5f5f5;">{action_type}</span>'
    return ""


def _badge(text, color, bg):
    return f'<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600;color:{color};background:{bg};">{text}</span>'


# ============================================================
# 手机端：卡片式渲染（健身）
# ============================================================
def render_mobile_exercise_card(row, header, index):
    name = row[header.index("动作名称")] if "动作名称" in header else ""
    action_type = row[header.index("动作类型")] if "动作类型" in header else ""
    sets = row[header.index("组数x次数")] if "组数x次数" in header else ""
    tempo = row[header.index("节奏/要点")] if "节奏/要点" in header else ""
    rpe = row[header.index("目标RPE")] if "目标RPE" in header else ""
    progression = row[header.index("渐进规则")] if "渐进规则" in header else ""
    note = row[header.index("注意事项")] if "注意事项" in header else ""
    phase = row[header.index("阶段")] if "阶段" in header else ""

    border_color = "#ddd"
    for emoji, (_, color, _) in TYPE_BADGES.items():
        if emoji in str(action_type):
            border_color = color
            break

    badge = _get_type_badge(action_type)

    rpe_html = ""
    if rpe.strip():
        rpe_html = f'<span style="font-size:13px;color:#666;">RPE {rpe}</span>'

    has_warning = "⚠️" in note
    warning_border = "border-left:4px solid #ff9800;" if has_warning else f"border-left:4px solid {border_color};"

    card_html = f'''
    <div style="{warning_border}background:white;border-radius:8px;padding:12px 14px;margin-bottom:8px;box-shadow:0 1px 2px rgba(0,0,0,0.06);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <span style="font-size:14px;font-weight:600;color:#333;">{index}. {name}</span>
            {badge}
        </div>'''

    if sets.strip():
        card_html += f'<div style="font-size:14px;color:#333;margin-bottom:3px;">{sets}</div>'
    if tempo.strip():
        card_html += f'<div style="font-size:13px;color:#666;margin-bottom:3px;">{tempo}</div>'
    if rpe_html:
        card_html += f'<div style="margin-bottom:3px;">{rpe_html}</div>'
    if progression.strip():
        card_html += f'<div style="font-size:13px;color:#666;margin-bottom:3px;">{progression}</div>'
    if note.strip():
        note_bg = "#fef5f5" if has_warning else "#f5f7fa"
        note_color = "#c62828" if has_warning else "#555"
        card_html += f'<div style="font-size:13px;color:{note_color};background:{note_bg};padding:6px 10px;border-radius:4px;margin-top:4px;line-height:1.5;">{note}</div>'

    card_html += '</div>'
    return card_html


def render_mobile_day(day_name, day_df, header):
    color, bg, icon = DAY_COLORS.get(day_name, ("#333", "#f5f5f5", "📋"))

    html = f'''
    <div style="background:{bg};border-radius:8px;padding:12px;margin-bottom:12px;">
        <div style="font-size:15px;font-weight:700;color:{color};text-align:center;">
            {icon} {day_name}
        </div>
    </div>'''
    st.markdown(html, unsafe_allow_html=True)

    phase_col = header.index("阶段") if "阶段" in header else -1
    current_phase = ""
    exercise_num = 1

    for _, row_series in day_df.iterrows():
        row = row_series.tolist()
        if phase_col >= 0:
            phase = row[phase_col]
            if phase and phase != current_phase:
                current_phase = phase
                st.markdown(
                    f'<div style="font-size:14px;font-weight:600;color:#333;padding:6px 0 4px 0;border-bottom:1px solid #ddd;margin:10px 0 6px 0;">{phase}</div>',
                    unsafe_allow_html=True,
                )

        name = row[header.index("动作名称")] if "动作名称" in header else ""
        if name.strip() and "严禁" not in name:
            card = render_mobile_exercise_card(row, header, exercise_num)
            st.markdown(card, unsafe_allow_html=True)
            exercise_num += 1
        elif "严禁" in name:
            note = row[header.index("注意事项")] if "注意事项" in header else ""
            st.markdown(
                f'<div style="background:#fef5f5;border-left:3px solid #c62828;padding:8px 12px;border-radius:4px;margin-bottom:8px;font-size:14px;color:#c62828;">🚫 {name}：{note}</div>',
                unsafe_allow_html=True,
            )


def render_mobile_body(df):
    df.iloc[:, 0] = df.iloc[:, 0].replace("", pd.NA).ffill().fillna("")
    current_cat = ""
    for _, row in df.iterrows():
        cat = str(row.iloc[0])
        item = str(row.iloc[1])
        detail = str(row.iloc[2]) if len(row) > 2 else ""

        if cat != current_cat:
            current_cat = cat
            color, bg = CATEGORY_COLORS.get(cat, ("#333", "#f5f7fa"))
            st.markdown(
                f'<div style="background:{bg};padding:8px 12px;border-radius:6px;margin:12px 0 6px 0;font-size:14px;font-weight:600;color:{color};">{cat}</div>',
                unsafe_allow_html=True,
            )

        if item.strip():
            st.markdown(
                f'''<div style="background:white;border-left:2px solid #ddd;padding:8px 12px;margin-bottom:6px;border-radius:4px;">
                    <div style="font-size:14px;font-weight:600;color:#333;margin-bottom:2px;">{item}</div>
                    <div style="font-size:13px;color:#666;line-height:1.5;">{detail}</div>
                </div>''',
                unsafe_allow_html=True,
            )


def render_mobile_lib(df):
    for _, row in df.iterrows():
        name = str(row.get("动作名称", ""))
        atype = str(row.get("动作类型", ""))
        muscle = str(row.get("目标肌群", ""))
        note = str(row.get("道长专属注意事项", ""))
        badge = _get_type_badge(atype)

        st.markdown(
            f'''<div style="background:white;border-radius:6px;padding:10px 12px;margin-bottom:6px;box-shadow:0 1px 2px rgba(0,0,0,0.06);">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">
                    <span style="font-size:14px;font-weight:600;color:#333;">{name}</span>
                    {badge}
                </div>
                <div style="font-size:13px;color:#666;margin-bottom:3px;">{muscle}</div>
                <div style="font-size:13px;color:#666;line-height:1.5;">{note}</div>
            </div>''',
            unsafe_allow_html=True,
        )


def render_mobile_notes(df):
    for _, row in df.iterrows():
        date = str(row.get("日期", ""))
        name = str(row.get("动作名称", ""))
        problem = str(row.get("问题发现", ""))
        fix = str(row.get("修正建议", ""))
        priority = str(row.get("优先级", "")).strip()
        status = str(row.get("状态", "")).strip()

        p_color, p_bg = PRIORITY_STYLE.get(priority, ("#333", "#f5f5f5"))
        s_color, s_bg = STATUS_STYLE.get(status, ("#333", "#f5f5f5"))

        is_general = name.startswith("[")
        border_color = "#00695c" if is_general else p_color

        card = f'''
        <div style="border-left:3px solid #ddd;background:white;border-radius:6px;padding:10px 12px;margin-bottom:8px;box-shadow:0 1px 2px rgba(0,0,0,0.06);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                <span style="font-size:14px;font-weight:600;color:#333;">{name}</span>
                <span style="font-size:13px;color:#666;">{priority}</span>
            </div>
            <div style="font-size:13px;color:#888;margin-bottom:4px;">{date} · {status}</div>
            <div style="font-size:13px;color:#c62828;background:#fef5f5;padding:6px 10px;border-radius:4px;margin-bottom:4px;line-height:1.5;">{problem}</div>
            <div style="font-size:13px;color:#2e7d32;background:#f5faf5;padding:6px 10px;border-radius:4px;line-height:1.5;">{fix}</div>
        </div>'''
        st.markdown(card, unsafe_allow_html=True)


# ============================================================
# 电脑端：表格渲染
# ============================================================
def render_table_with_rowspan(df: pd.DataFrame, merge_col: int = 0) -> str:
    if df.empty:
        return "<p>无数据</p>"

    html = ['<table class="fit-table">']
    html.append('<thead><tr>')
    for col in df.columns:
        html.append(f'<th>{col}</th>')
    html.append('</tr></thead>')

    html.append('<tbody>')
    first_col = df.iloc[:, merge_col].tolist()
    i = 0
    while i < len(df):
        curr_val = first_col[i]
        span = 1
        while i + span < len(df) and first_col[i + span] == curr_val:
            span += 1

        html.append('<tr>')
        for j in range(len(df.columns)):
            if j == merge_col:
                css = _get_category_css(curr_val)
                html.append(f'<td rowspan="{span}" class="merged-cell" {css}>{curr_val}</td>')
            else:
                cell = str(df.iloc[i, j])
                cell = _style_cell(cell, df.columns[j])
                html.append(f'<td>{cell}</td>')
        html.append('</tr>')

        for k in range(1, span):
            html.append('<tr>')
            for j in range(len(df.columns)):
                if j == merge_col:
                    continue
                cell = str(df.iloc[i + k, j])
                cell = _style_cell(cell, df.columns[j])
                html.append(f'<td>{cell}</td>')
            html.append('</tr>')

        i += span

    html.append('</tbody></table>')
    return ''.join(html)


def render_simple_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p>无数据</p>"

    html = ['<table class="fit-table">']
    html.append('<thead><tr>')
    for col in df.columns:
        html.append(f'<th>{col}</th>')
    html.append('</tr></thead><tbody>')

    for i in range(len(df)):
        html.append('<tr>')
        for j in range(len(df.columns)):
            cell = str(df.iloc[i, j])
            cell = _style_cell(cell, df.columns[j])
            html.append(f'<td>{cell}</td>')
        html.append('</tr>')

    html.append('</tbody></table>')
    return ''.join(html)


def _get_category_css(val: str) -> str:
    val = str(val)
    if "伤病" in val or "🔴" in val:
        return 'style="background-color:#fff0f0; color:#c0392b;"'
    elif "禁忌" in val or "🚫" in val or "⚠️" in val:
        return 'style="background-color:#fff3e0; color:#e65100;"'
    elif "恢复" in val or "🟢" in val:
        return 'style="background-color:#e8f5e9; color:#2e7d32;"'
    elif "环境" in val or "🟡" in val:
        return 'style="background-color:#fffde7; color:#f57f17;"'
    elif "营养" in val or "🔵" in val:
        return 'style="background-color:#e3f2fd; color:#1565c0;"'
    elif "原则" in val or "📋" in val:
        return 'style="background-color:#f3e5f5; color:#6a1b9a;"'
    elif "练后拉伸" in val:
        return 'style="background-color:#efebe9; color:#5d4037;"'
    elif "热身" in val:
        return 'style="background-color:#e0f7fa; color:#00695c;"'
    elif "第7天" in val or "完全休息" in val:
        return 'style="background-color:#fce4ec; color:#880e4f;"'
    elif "第6天" in val:
        return 'style="background-color:#f3e5f5; color:#4a148c;"'
    elif "第1天" in val or "第5天" in val:
        return 'style="background-color:#e8eaf6; color:#283593;"'
    elif "第2天" in val:
        return 'style="background-color:#e0f2f1; color:#004d40;"'
    elif "第3天" in val:
        return 'style="background-color:#f1f8e9; color:#33691e;"'
    elif "第4天" in val:
        return 'style="background-color:#fff8e1; color:#ff6f00;"'
    return 'style="background-color:#fafafa;"'


def _style_cell(cell: str, col_name: str) -> str:
    if "💪" in cell:
        return f'<span style="color:#1565c0; font-weight:600;">{cell}</span>'
    elif "🎯" in cell:
        return f'<span style="color:#e65100; font-weight:600;">{cell}</span>'
    elif "🔧" in cell:
        return f'<span style="color:#2e7d32; font-weight:600;">{cell}</span>'
    elif "🧘" in cell:
        return f'<span style="color:#6a1b9a; font-weight:600;">{cell}</span>'
    if col_name == "目标RPE":
        cell = cell.strip()
        if cell in ("7-8", "8-9", "8"):
            return f'<span style="color:#c62828; font-weight:bold;">{cell}</span>'
        elif cell in ("4-5", "4", "5", "5-6"):
            return f'<span style="color:#2e7d32;">{cell}</span>'
    return cell


# ============================================================
# 任务清单：表格渲染
# ============================================================
def render_task_table(df: pd.DataFrame, title: str, is_mobile: bool) -> None:
    if df.empty:
        st.info("无数据")
        return

    if is_mobile:
        # 手机端：卡片式
        df.iloc[:, 0] = df.iloc[:, 0].replace("", pd.NA).ffill().fillna("")
        current_cat = ""
        for _, row in df.iterrows():
            cat = str(row.iloc[0])
            if cat != current_cat:
                current_cat = cat
                st.markdown(
                    f'<div style="background:#f5f7fa;padding:8px 12px;border-radius:6px;margin:12px 0 6px 0;font-size:14px;font-weight:600;color:#333;">{cat}</div>',
                    unsafe_allow_html=True,
                )
            # 显示其余列
            card_content = ""
            for j in range(1, len(df.columns)):
                col_name = df.columns[j]
                val = str(row.iloc[j]).strip()
                if val:
                    card_content += f'<div style="font-size:14px;color:#444;margin-bottom:2px;"><b>{col_name}</b>：{val}</div>'
            if card_content:
                st.markdown(
                    f'<div style="background:white;border-left:2px solid #ddd;padding:8px 12px;margin-bottom:6px;border-radius:4px;">{card_content}</div>',
                    unsafe_allow_html=True,
                )
    else:
        # 电脑端：表格
        df.iloc[:, 0] = df.iloc[:, 0].replace("", pd.NA).ffill().fillna("")
        html = ['<table class="fit-table">']
        html.append('<thead><tr>')
        for col in df.columns:
            html.append(f'<th>{col}</th>')
        html.append('</tr></thead>')

        html.append('<tbody>')
        first_col = df.iloc[:, 0].tolist()
        i = 0
        while i < len(df):
            curr_val = first_col[i]
            span = 1
            while i + span < len(df) and first_col[i + span] == curr_val:
                span += 1

            html.append('<tr>')
            html.append(f'<td rowspan="{span}" class="merged-cell" style="background-color:#fafafa;">{curr_val}</td>')
            for j in range(1, len(df.columns)):
                html.append(f'<td>{df.iloc[i, j]}</td>')
            html.append('</tr>')

            for k in range(1, span):
                html.append('<tr>')
                for j in range(1, len(df.columns)):
                    html.append(f'<td>{df.iloc[i + k, j]}</td>')
                html.append('</tr>')

            i += span

        html.append('</tbody></table>')
        st.markdown(''.join(html), unsafe_allow_html=True)


# ============================================================
# CSS
# ============================================================
GLOBAL_CSS = """
<style>
/* 隐藏 Streamlit 默认 UI */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden !important;}
[data-testid="stToolbar"] {display: none;}
[data-testid="stDecoration"] {display: none;}
[data-testid="stStatusWidget"] {display: none;}
.stDeployButton {display: none !important;}
[data-testid="stAppDeployButton"] {display: none !important;}
.viewerBadge_container__r5tak {display: none !important;}
.stApp > footer {display: none !important;}
a[href*="streamlit.io"] {display: none !important;}

/* 侧边栏缩窄 */
[data-testid="stSidebar"] {
    min-width: 160px !important;
    max-width: 160px !important;
}
[data-testid="stSidebar"] .block-container {
    padding: 1rem 0.8rem !important;
}

/* 全局字体 */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* 表格 */
.fit-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    line-height: 1.6;
}
.fit-table th {
    background-color: #f8f9fa;
    color: #333;
    padding: 10px 12px;
    text-align: left;
    font-weight: 600;
    font-size: 14px;
    border-bottom: 2px solid #dee2e6;
}
.fit-table td {
    padding: 8px 10px;
    border-bottom: 1px solid #eee;
    vertical-align: middle;
    font-size: 14px;
    color: #333;
}
.fit-table .merged-cell {
    font-weight: 600;
    font-size: 14px;
    vertical-align: middle;
    text-align: center;
    border-right: 2px solid #dee2e6;
}
.fit-table tr:hover td {
    background-color: #f8f9fa;
}

@media (max-width: 768px) {
    .block-container { padding: 0.5rem 0.8rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { font-size: 14px; padding: 8px 10px; }
}
</style>
"""


# ============================================================
# 主应用
# ============================================================
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# 检测屏幕宽度
screen_width = streamlit_js_eval(js_expressions="window.innerWidth", key="screen_width")
is_mobile = screen_width is not None and screen_width < 768

# 侧边栏导航
with st.sidebar:
    page = st.radio("导航", ["💪 健身计划", "📋 任务清单"], label_visibility="collapsed")

try:
    gc = _get_client()

    if page == "💪 健身计划":
        # ============================================================
        # 健身计划页面
        # ============================================================
        tab_plan, tab_warmup, tab_stretch, tab_lib, tab_body, tab_notes_tab, tab_tnotes = st.tabs([
            "📅 训练计划",
            "🔥 热身",
            "🧘 拉伸",
            "📚 动作库",
            "🏥 身体状况",
            "📝 备注",
            "🔬 训练笔记",
        ])

        # --- 加载周训练数据（多个 tab 共用） ---
        df_weekly = load_sheet(gc, FITNESS_SPREADSHEET_ID, "周训练计划")
        header = df_weekly.columns.tolist() if not df_weekly.empty else []
        day_data = get_day_data(df_weekly) if not df_weekly.empty else {}
        day_names = list(day_data.keys())

        # --- Tab: 训练计划（仅训练日，不含热身/拉伸） ---
        with tab_plan:
            if not df_weekly.empty:
                training_days = [d for d in day_names if "热身" not in d and "练后拉伸" not in d]

                if is_mobile:
                    selected_day = st.selectbox(
                        "训练日",
                        options=training_days,
                        index=0,
                        key="mobile_day",
                        label_visibility="collapsed",
                    )
                    if selected_day in day_data:
                        render_mobile_day(selected_day, day_data[selected_day], header)
                else:
                    df_weekly.iloc[:, 0] = df_weekly.iloc[:, 0].replace("", pd.NA).ffill().fillna("")
                    selected = st.multiselect(
                        "筛选训练日",
                        options=training_days,
                        default=training_days,
                        key="day_filter",
                    )
                    df_filtered = df_weekly[df_weekly.iloc[:, 0].isin(selected)]
                    html = render_table_with_rowspan(df_filtered, merge_col=0)
                    st.markdown(html, unsafe_allow_html=True)
            else:
                st.info("无数据")

        # --- Tab: 热身 ---
        with tab_warmup:
            warmup_keys = [d for d in day_names if "热身" in d]
            if warmup_keys:
                if is_mobile:
                    render_mobile_day(warmup_keys[0], day_data[warmup_keys[0]], header)
                else:
                    df_w = df_weekly.copy()
                    df_w.iloc[:, 0] = df_w.iloc[:, 0].replace("", pd.NA).ffill().fillna("")
                    df_warmup = df_w[df_w.iloc[:, 0].isin(warmup_keys)]
                    html = render_table_with_rowspan(df_warmup, merge_col=0)
                    st.markdown(html, unsafe_allow_html=True)
            else:
                st.info("无热身数据")

        # --- Tab: 拉伸 ---
        with tab_stretch:
            stretch_keys = [d for d in day_names if "练后拉伸" in d]
            if stretch_keys:
                if is_mobile:
                    render_mobile_day(stretch_keys[0], day_data[stretch_keys[0]], header)
                else:
                    df_s = df_weekly.copy()
                    df_s.iloc[:, 0] = df_s.iloc[:, 0].replace("", pd.NA).ffill().fillna("")
                    df_stretch = df_s[df_s.iloc[:, 0].isin(stretch_keys)]
                    html = render_table_with_rowspan(df_stretch, merge_col=0)
                    st.markdown(html, unsafe_allow_html=True)
            else:
                st.info("无拉伸数据")

        # --- Tab: 动作库 ---
        with tab_lib:
            df_lib = load_sheet(gc, FITNESS_SPREADSHEET_ID, "动作库")
            if not df_lib.empty:
                if is_mobile:
                    if "动作类型" in df_lib.columns:
                        types = df_lib["动作类型"].unique().tolist()
                        selected_type = st.selectbox("筛选类型", ["全部"] + types, key="mobile_type")
                        if selected_type != "全部":
                            df_lib = df_lib[df_lib["动作类型"] == selected_type]
                    render_mobile_lib(df_lib)
                else:
                    if "动作类型" in df_lib.columns:
                        types = df_lib["动作类型"].unique().tolist()
                        selected_types = st.multiselect(
                            "按动作类型筛选", options=types, default=types, key="type_filter",
                        )
                        df_lib = df_lib[df_lib["动作类型"].isin(selected_types)]
                    html = render_simple_table(df_lib)
                    st.markdown(html, unsafe_allow_html=True)
                    st.caption(f"共 {len(df_lib)} 个动作")
            else:
                st.info("无数据")

        # --- Tab: 身体状况与禁忌 ---
        with tab_body:
            df_body = load_sheet(gc, FITNESS_SPREADSHEET_ID, "身体状况与禁忌")
            if not df_body.empty:
                if is_mobile:
                    render_mobile_body(df_body)
                else:
                    df_body.iloc[:, 0] = df_body.iloc[:, 0].replace("", pd.NA).ffill().fillna("")
                    html = render_table_with_rowspan(df_body, merge_col=0)
                    st.markdown(html, unsafe_allow_html=True)
            else:
                st.info("无数据")

        # --- Tab: 备注与说明 ---
        with tab_notes_tab:
            df_notes = load_sheet(gc, FITNESS_SPREADSHEET_ID, "备注与说明")
            if not df_notes.empty:
                for _, row in df_notes.iterrows():
                    topic = str(row.iloc[0]).strip()
                    content = str(row.iloc[1]).strip()
                    if topic == "" and content == "":
                        st.markdown("---")
                    elif content == "":
                        st.subheader(topic)
                    else:
                        if is_mobile:
                            st.markdown(
                                f'<div style="margin-bottom:6px;"><span style="font-weight:600;font-size:14px;color:#333;">{topic}</span><br><span style="font-size:13px;color:#666;">{content}</span></div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(f"**{topic}**：{content}")
            else:
                st.info("无数据")

        # --- Tab: 训练笔记 ---
        with tab_tnotes:
            df_tnotes = load_sheet(gc, FITNESS_SPREADSHEET_ID, "训练笔记")
            if not df_tnotes.empty:
                if is_mobile:
                    priorities = df_tnotes["优先级"].unique().tolist() if "优先级" in df_tnotes.columns else []
                    sel_pri = st.selectbox("按优先级筛选", ["全部"] + priorities, key="note_pri")
                    if sel_pri != "全部":
                        df_tnotes = df_tnotes[df_tnotes["优先级"] == sel_pri]
                    render_mobile_notes(df_tnotes)
                else:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        priorities = df_tnotes["优先级"].unique().tolist() if "优先级" in df_tnotes.columns else []
                        sel_pri = st.multiselect("按优先级筛选", priorities, default=priorities, key="note_pri_d")
                    with col_b:
                        statuses = df_tnotes["状态"].unique().tolist() if "状态" in df_tnotes.columns else []
                        sel_sta = st.multiselect("按状态筛选", statuses, default=statuses, key="note_sta_d")
                    df_tnotes = df_tnotes[
                        df_tnotes["优先级"].isin(sel_pri) & df_tnotes["状态"].isin(sel_sta)
                    ]
                    html = render_simple_table(df_tnotes)
                    st.markdown(html, unsafe_allow_html=True)
                    st.caption(f"共 {len(df_tnotes)} 条训练笔记")
            else:
                st.info("无训练笔记")

    elif page == "📋 任务清单":
        # ============================================================
        # 任务清单页面
        # ============================================================
        if is_mobile:
            st.markdown(
                '<div style="text-align:center;padding:8px 0;"><span style="font-size:18px;font-weight:700;color:#333;">任务清单</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("### 任务清单")

        tab_active, tab_archive = st.tabs(["📌 进行中", "✅ 已完成"])

        with tab_active:
            df_active = load_sheet(gc, TASK_SPREADSHEET_ID, "Sheet1")
            if not df_active.empty:
                render_task_table(df_active, "进行中", is_mobile)
            else:
                st.info("无数据")

        with tab_archive:
            df_archive = load_sheet(gc, TASK_SPREADSHEET_ID, "Archive")
            if not df_archive.empty:
                render_task_table(df_archive, "已完成", is_mobile)
            else:
                st.info("无数据")

except Exception as e:
    st.error(f"连接失败：{e}")
    st.info("请检查 Streamlit Secrets 中的 Google Sheet 凭证配置。")
