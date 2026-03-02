"""
知乎问题数据查询 - 用 Selenium 模拟浏览器批量获取关注数/回答数/浏览量
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import time
import re
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

COOKIE_STR = '_zap=f70d2cc8-1c1e-4381-8d47-0c9ace806b8a; d_c0=njCUCZdQxxuPTpg4YTKf4D93JPO2vcD67s0=|1770012258; captcha_session_v2=2|1:0|10:1770012258|18:captcha_session_v2|88:MWpYNExKZGgvdkl3VXR5TjFWd2tFNjduL3RSMkRqL0FPa0Z2RGxKQW5iNjd6aEZWR1BmRWxzeDdlTGlOa0l3Rw==|478dc190638d08b0fb17e674ca763ddefe6d2ab60289dc325f2daf47cdb37eab; __snaker__id=6I0ajfiGe69P8tjk; q_c1=f97081cf1a5845cca9aaee5f3c895b60|1770012278000|1770012278000; z_c0=2|1:0|10:1770012934|4:z_c0|92:Mi4xOHZzdkFBQUFBQUNlTUpRSmwxREhHeGNBQUFCZ0FsVk5kWXh0YWdDV2ZReXNpeFY5Zmg3aUU2TW41VEZEY0pQNTFn|70b29f833c24722f7867c04e74c5db665df64a59faf6a3afce1f7f536501d2cb; _xsrf=efc43ffb-b060-49a5-a059-3a5dbcf7f1c5; HMACCOUNT=618EDB8F15DA672D; BEC=e9bdbc10d489caddf435785a710b7029; SESSIONID=V4mhgSdk87QLenHzoIk3Qs2LAVs9R0isnSMYx6y6MbR; JOID=VVscBUPjGsLNJxH-T0xQ2AS-QDJasSSgq09GkCvUKZmOTHCyP1OSSaUsH_tO3aRhGuH2LoYPhf5nS4kqZ9i_84w=; osd=UlwUAE3kHcrIKRb5R0le3wO2RTxdtiylpUhBmC7aLp6GSX61OFuXR6IrF_5A2qNpH-_xKY4Ki_lgQ4wkYN-39oI='

# 问题列表
question_ids = {
    "AI编程普通人": [
        "638375888",    # 有了AI，普通人还有必要学编程吗
        "655956420",    # 有了chatgpt4o，普通人还需要学代码吗
        "625532967",    # 不懂编程，如何使用AI编程
    ],
    "AI办公效率": [
        "595668645",    # 如何使用AI提升我的办公效率
        "11243913549",  # 对于普通的上班族，如何高效使用各类AI工具
        "588712985",    # 有哪些AI工具能帮你更高效地完成工作
        "594717201",    # AI大火，有哪些真正可以提高办公效率的AI软件或工具
        "592131252",    # 有哪些好用的ai工具，可以提升科研学习办公效率
    ],
    "AI普通人机遇": [
        "647132504",    # 普通人如何利用好AI帮自己搞钱
        "591256543",    # 普通人如何抓住AI这个风口
        "656761347",    # 如何利用ai提高工作效率
    ],
}

def setup_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    
    # 先访问知乎首页设置cookie
    driver.get("https://www.zhihu.com")
    time.sleep(2)
    for cookie_pair in COOKIE_STR.split("; "):
        if "=" in cookie_pair:
            name, value = cookie_pair.split("=", 1)
            try:
                driver.add_cookie({"name": name.strip(), "value": value.strip(), "domain": ".zhihu.com"})
            except:
                pass
    return driver

def parse_number(text):
    """解析 '1,234' 或 '1.2万' 格式的数字"""
    text = text.strip().replace(",", "").replace(" ", "")
    if "万" in text:
        return int(float(text.replace("万", "")) * 10000)
    if "亿" in text:
        return int(float(text.replace("亿", "")) * 100000000)
    try:
        return int(text)
    except:
        return 0

def get_question_data(driver, qid):
    """通过Selenium获取问题页面数据"""
    url = f"https://www.zhihu.com/question/{qid}"
    driver.get(url)
    time.sleep(3)
    
    page_source = driver.page_source
    title = "?"
    follower_count = 0
    answer_count = 0
    visit_count = 0
    
    # 提取标题
    try:
        title_el = driver.find_element("css selector", "h1.QuestionHeader-title")
        title = title_el.text
    except:
        try:
            m = re.search(r'<h1[^>]*class="QuestionHeader-title"[^>]*>(.*?)</h1>', page_source, re.DOTALL)
            if m:
                title = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        except:
            pass
    
    # 提取关注数和浏览量 - 通常在 QuestionFollowStatus 或 NumberBoard 区域
    # 格式通常是: "XX 关注" 和 "XX 浏览"
    try:
        # 方法1: 从 NumberBoard 提取
        numbers = driver.find_elements("css selector", ".NumberBoard-itemValue")
        labels = driver.find_elements("css selector", ".NumberBoard-itemName")
        for num_el, label_el in zip(numbers, labels):
            label = label_el.text.strip()
            val = parse_number(num_el.get_attribute("title") or num_el.text)
            if "关注" in label:
                follower_count = val
            elif "浏览" in label:
                visit_count = val
    except:
        pass
    
    # 提取回答数
    try:
        # 方法1: 从页面文本匹配
        m = re.search(r'(\d[\d,]*)\s*个回答', page_source)
        if m:
            answer_count = parse_number(m.group(1))
        else:
            # 方法2: 从 Answers 标签
            ans_els = driver.find_elements("css selector", "[class*='List-headerText'] span")
            for el in ans_els:
                txt = el.text
                m2 = re.search(r'(\d[\d,]*)', txt)
                if m2:
                    answer_count = parse_number(m2.group(1))
                    break
    except:
        pass
    
    # 备用: 从 initialData JSON 提取
    if follower_count == 0:
        try:
            m = re.search(r'"followerCount"\s*:\s*(\d+)', page_source)
            if m:
                follower_count = int(m.group(1))
        except:
            pass
    if visit_count == 0:
        try:
            m = re.search(r'"visitCount"\s*:\s*(\d+)', page_source)
            if m:
                visit_count = int(m.group(1))
        except:
            pass
    if answer_count == 0:
        try:
            m = re.search(r'"answerCount"\s*:\s*(\d+)', page_source)
            if m:
                answer_count = int(m.group(1))
        except:
            pass
    
    return {
        "id": qid,
        "title": title,
        "follower_count": follower_count,
        "answer_count": answer_count,
        "visit_count": visit_count,
        "url": url,
    }

print("Starting Chrome...")
driver = setup_driver()
print("Chrome ready.\n")

all_questions = []

try:
    for category, qids in question_ids.items():
        print(f"\n{'='*60}")
        print(f"=== {category} ({len(qids)} questions) ===")
        print(f"{'='*60}")
        
        for qid in qids:
            try:
                data = get_question_data(driver, qid)
                data["category"] = category
                all_questions.append(data)
                print(f"  [{data['follower_count']}关注/{data['answer_count']}回答/{data['visit_count']}浏览] {data['title'][:55]}")
            except Exception as e:
                print(f"  ERROR qid={qid}: {e}")
            time.sleep(1)
finally:
    driver.quit()
    print("\nChrome closed.")

# 汇总
print("\n\n" + "="*80)
print("=== 全部问题（按关注数排序）===")
print("="*80)

all_questions.sort(key=lambda x: x["follower_count"], reverse=True)

for q in all_questions:
    ratio = q["follower_count"] / max(q["answer_count"], 1)
    print(f"[{q['category']}] 关注:{q['follower_count']} 回答:{q['answer_count']} 浏览:{q['visit_count']} 关注/回答:{ratio:.1f}")
    print(f"  {q['title']}")
    print(f"  {q['url']}")
    print()

# 筛选候选
print("\n" + "="*80)
print("=== 候选问题（高关注 + 低竞争）===")
print("=== 筛选条件：关注>50 且 关注/回答比>3 ===")
print("="*80)

candidates = [q for q in all_questions if q["follower_count"] > 50 and q["follower_count"] / max(q["answer_count"], 1) > 3]
candidates.sort(key=lambda x: x["follower_count"] / max(x["answer_count"], 1), reverse=True)

for i, q in enumerate(candidates, 1):
    ratio = q["follower_count"] / max(q["answer_count"], 1)
    print(f"\n#{i} [{q['category']}]")
    print(f"  {q['title']}")
    print(f"  关注:{q['follower_count']} | 回答:{q['answer_count']} | 浏览:{q['visit_count']} | 比值:{ratio:.1f}")
    print(f"  {q['url']}")

if not candidates:
    print("\n(没有符合严格筛选条件的问题，以下是关注数最高的前10个)")
    for i, q in enumerate(all_questions[:10], 1):
        ratio = q["follower_count"] / max(q["answer_count"], 1)
        print(f"\n#{i} [{q['category']}]")
        print(f"  {q['title']}")
        print(f"  关注:{q['follower_count']} | 回答:{q['answer_count']} | 浏览:{q['visit_count']} | 比值:{ratio:.1f}")
        print(f"  {q['url']}")
