"""从目录文章HTML中提取分类和文章标题"""
import re

html = open(r"c:\Users\sweet\Downloads\CascadeProjects\zhihu-data\article_content.html", "r", encoding="utf-8").read()

# Split by bold tags which are category headers
categories = [
    "复杂系统", "中国经济", "经济学", "个人主义", "概率统计", "AI",
    "德先生", "制度的细节", "笔记法", "心理学", "重新理解游戏",
    "作家", "传统", "长生", "宗教", "中医", "苏联", "一战", "大革命", "历史", "好好说话"
]

# Find positions of each category in text
text = re.sub(r"<[^>]+>", "\n", html)
text = re.sub(r"\n+", "\n", text).strip()

lines = text.split("\n")
current_cat = None
cat_articles = {}

for line in lines:
    line = line.strip()
    if not line:
        continue
    if line in categories:
        current_cat = line
        if current_cat not in cat_articles:
            cat_articles[current_cat] = []
    elif current_cat and len(line) > 8 and "?" in line or "？" in line or "！" in line or len(line) > 15:
        # likely an article title
        if line not in ["目录", "钓线沉流", "博客", "检索", "文章目录"] and not line.startswith("http"):
            cat_articles.setdefault(current_cat, []).append(line)

# Print in order
for cat in categories:
    if cat in cat_articles and cat_articles[cat]:
        print(f"\n=== {cat} ===")
        for a in cat_articles[cat]:
            print(f"- {a}")
