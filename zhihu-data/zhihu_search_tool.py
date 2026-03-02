"""
知乎搜索抓取工具 - 非 headless 模式
使用方法：
1. 运行脚本，Chrome 窗口会自动打开
2. 在弹出的 Chrome 中手动登录知乎（如果需要）
3. 登录完成后回到终端按回车
4. 脚本自动搜索关键词、提取问题列表、获取关注数/回答数/浏览量
5. 结果保存到 CSV 文件

用法：
  python zhihu_search_tool.py "MCP协议" "Cursor 使用" "AI编程工具"
  python zhihu_search_tool.py --file keywords.txt    # 从文件读取关键词，每行一个
  python zhihu_search_tool.py --questions 5290049088 14871840737  # 直接查询问题ID
  python zhihu_search_tool.py --auto "MCP协议"       # 用Cookie自动登录，无需手动操作
"""
import sys
import time
import re
import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ============================================================
# 配置
# ============================================================
COOKIE_STR = '_zap=f70d2cc8-1c1e-4381-8d47-0c9ace806b8a; d_c0=njCUCZdQxxuPTpg4YTKf4D93JPO2vcD67s0=|1770012258; captcha_session_v2=2|1:0|10:1770012258|18:captcha_session_v2|88:MWpYNExKZGgvdkl3VXR5TjFWd2tFNjduL3RSMkRqL0FPa0Z2RGxKQW5iNjd6aEZWR1BmRWxzeDdlTGlOa0l3Rw==|478dc190638d08b0fb17e674ca763ddefe6d2ab60289dc325f2daf47cdb37eab; __snaker__id=6I0ajfiGe69P8tjk; q_c1=f97081cf1a5845cca9aaee5f3c895b60|1770012278000|1770012278000; z_c0=2|1:0|10:1770012934|4:z_c0|92:Mi4xOHZzdkFBQUFBQUNlTUpRSmwxREhHeGNBQUFCZ0FsVk5kWXh0YWdDV2ZReXNpeFY5Zmg3aUU2TW41VEZEY0pQNTFn|70b29f833c24722f7867c04e74c5db665df64a59faf6a3afce1f7f536501d2cb; _xsrf=efc43ffb-b060-49a5-a059-3a5dbcf7f1c5; HMACCOUNT=618EDB8F15DA672D; BEC=e9bdbc10d489caddf435785a710b7029; SESSIONID=V4mhgSdk87QLenHzoIk3Qs2LAVs9R0isnSMYx6y6MbR; JOID=VVscBUPjGsLNJxH-T0xQ2AS-QDJasSSgq09GkCvUKZmOTHCyP1OSSaUsH_tO3aRhGuH2LoYPhf5nS4kqZ9i_84w=; osd=UlwUAE3kHcrIKRb5R0le3wO2RTxdtiylpUhBmC7aLp6GSX61OFuXR6IrF_5A2qNpH-_xKY4Ki_lgQ4wkYN-39oI='
MAX_QUESTIONS_PER_KEYWORD = 20   # 每个关键词最多抓取多少个问题
SCROLL_PAUSE = 2                  # 搜索页滚动间隔（秒）
PAGE_LOAD_WAIT = 3                # 页面加载等待（秒）
BETWEEN_REQUESTS_WAIT = 1.5       # 请求间隔（秒）
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def setup_driver():
    """启动有界面的 Chrome"""
    opts = Options()
    # 不用 headless，让用户能手动登录
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--window-size=1280,900")
    
    # 优先使用本地缓存的 chromedriver，避免网络请求
    local_driver = r"C:\Users\sweet\.wdm\drivers\chromedriver\win64\144.0.7559.133\chromedriver-win32\chromedriver.exe"
    if os.path.exists(local_driver):
        service = Service(local_driver)
    else:
        service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=opts)
    # 隐藏 webdriver 标记
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
        """
    })
    return driver


def inject_cookies(driver):
    """注入 Cookie 实现自动登录"""
    driver.get("https://www.zhihu.com")
    time.sleep(2)
    for cookie_pair in COOKIE_STR.split("; "):
        if "=" in cookie_pair:
            name, value = cookie_pair.split("=", 1)
            try:
                driver.add_cookie({"name": name.strip(), "value": value.strip(), "domain": ".zhihu.com"})
            except:
                pass
    driver.refresh()
    time.sleep(2)


def wait_for_login(driver, auto_mode=False):
    """打开知乎首页，等待用户手动登录或自动注入Cookie"""
    if auto_mode:
        print("[AUTO] 注入 Cookie 登录...")
        inject_cookies(driver)
        if is_logged_in(driver):
            print("[OK] Cookie 登录成功！")
        else:
            print("[WARN] Cookie 可能已过期，继续尝试...")
        return
    
    driver.get("https://www.zhihu.com")
    time.sleep(2)
    
    # 检查是否已登录
    if is_logged_in(driver):
        print("[OK] 已检测到登录状态")
        return
    
    print("\n" + "=" * 50)
    print("请在弹出的 Chrome 窗口中登录知乎")
    print("登录完成后，回到这里按回车继续...")
    print("=" * 50)
    input()
    
    # 验证登录
    driver.get("https://www.zhihu.com")
    time.sleep(2)
    if is_logged_in(driver):
        print("[OK] 登录成功！")
    else:
        print("[WARN] 未检测到登录状态，继续尝试...")


def is_logged_in(driver):
    """检查是否已登录"""
    try:
        # 已登录用户页面会有头像元素
        driver.find_element(By.CSS_SELECTOR, ".AppHeader-profileEntry, .AppHeader-userInfo, img.Avatar")
        return True
    except:
        return False


def parse_number(text):
    """解析 '1,234' / '1.2 万' / '1.2万' 格式"""
    if not text:
        return 0
    text = text.strip().replace(",", "").replace(" ", "").replace("\n", "")
    if "万" in text:
        try:
            return int(float(text.replace("万", "")) * 10000)
        except:
            return 0
    if "亿" in text:
        try:
            return int(float(text.replace("亿", "")) * 100000000)
        except:
            return 0
    try:
        return int(text)
    except:
        return 0


def search_keyword(driver, keyword, max_questions=MAX_QUESTIONS_PER_KEYWORD):
    """搜索关键词，提取问题ID列表"""
    print(f"\n[搜索] {keyword}")
    url = f"https://www.zhihu.com/search?type=content&q={keyword}"
    driver.get(url)
    time.sleep(PAGE_LOAD_WAIT)
    
    question_ids = set()
    last_count = 0
    scroll_attempts = 0
    max_scroll = 8  # 最多滚动8次
    
    while len(question_ids) < max_questions and scroll_attempts < max_scroll:
        # 从当前页面提取问题链接
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/question/']")
        for link in links:
            href = link.get_attribute("href") or ""
            m = re.search(r'/question/(\d+)', href)
            if m:
                question_ids.add(m.group(1))
        
        if len(question_ids) >= max_questions:
            break
        
        # 如果没有新问题出现，再滚动
        if len(question_ids) == last_count:
            scroll_attempts += 1
        else:
            scroll_attempts = 0
        last_count = len(question_ids)
        
        # 滚动加载更多
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)
    
    qids = list(question_ids)[:max_questions]
    print(f"  找到 {len(qids)} 个问题")
    return qids


def get_question_detail(driver, qid):
    """访问问题页面，提取关注数/回答数/浏览量"""
    url = f"https://www.zhihu.com/question/{qid}"
    driver.get(url)
    time.sleep(PAGE_LOAD_WAIT)
    
    page = driver.page_source
    title = ""
    follower_count = 0
    answer_count = 0
    visit_count = 0
    
    # 标题：可能有多个 h1，取非空的那个
    try:
        h1s = driver.find_elements(By.CSS_SELECTOR, "h1.QuestionHeader-title")
        for h in h1s:
            t = h.text.strip()
            if t:
                title = t
                break
    except:
        pass
    if not title:
        m = re.search(r'<title>(.*?)\s*-\s*知乎</title>', page)
        if m:
            title = m.group(1).strip()
    if not title:
        m = re.search(r'"title"\s*:\s*"([^"]{5,})"', page)
        if m:
            title = m.group(1)
    
    # 关注数 + 浏览量（NumberBoard）
    try:
        numbers = driver.find_elements(By.CSS_SELECTOR, ".NumberBoard-itemValue")
        labels = driver.find_elements(By.CSS_SELECTOR, ".NumberBoard-itemName")
        for num_el, label_el in zip(numbers, labels):
            label = label_el.text.strip()
            val = parse_number(num_el.get_attribute("title") or num_el.text)
            if "关注" in label:
                follower_count = val
            elif "浏览" in label:
                visit_count = val
    except:
        pass
    
    # 备用：从页面源码 JSON 提取
    if follower_count == 0:
        m = re.search(r'"followerCount"\s*:\s*(\d+)', page)
        if m:
            follower_count = int(m.group(1))
    if visit_count == 0:
        m = re.search(r'"visitCount"\s*:\s*(\d+)', page)
        if m:
            visit_count = int(m.group(1))
    
    # 回答数
    try:
        m = re.search(r'(\d[\d,]*)\s*个回答', page)
        if m:
            answer_count = parse_number(m.group(1))
    except:
        pass
    if answer_count == 0:
        m = re.search(r'"answerCount"\s*:\s*(\d+)', page)
        if m:
            answer_count = int(m.group(1))
    
    return {
        "id": qid,
        "title": title,
        "follower_count": follower_count,
        "answer_count": answer_count,
        "visit_count": visit_count,
        "url": url,
    }


def save_results(all_questions, filename=None):
    """保存结果到 CSV"""
    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(OUTPUT_DIR, f"zhihu_questions_{ts}.csv")
    
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "keyword", "title", "follower_count", "answer_count",
            "visit_count", "ratio", "url", "id"
        ])
        writer.writeheader()
        for q in all_questions:
            ratio = q["follower_count"] / max(q["answer_count"], 1)
            writer.writerow({**q, "ratio": f"{ratio:.1f}"})
    
    print(f"\n[保存] 结果已写入: {filename}")
    return filename


def print_summary(all_questions):
    """打印汇总"""
    print("\n" + "=" * 80)
    print("=== 全部问题（按关注数排序）===")
    print("=" * 80)
    
    all_questions.sort(key=lambda x: x["follower_count"], reverse=True)
    
    for q in all_questions:
        ratio = q["follower_count"] / max(q["answer_count"], 1)
        print(f"[{q.get('keyword','')}] 关注:{q['follower_count']} 回答:{q['answer_count']} 浏览:{q['visit_count']} 比值:{ratio:.1f}")
        print(f"  {q['title']}")
        print(f"  {q['url']}")
        print()
    
    # 筛选候选
    print("=" * 80)
    print("=== 候选问题（高关注 + 低竞争）===")
    print("=== 条件：关注>30 且 关注/回答比>3 ===")
    print("=" * 80)
    
    candidates = [
        q for q in all_questions
        if q["follower_count"] > 30
        and q["follower_count"] / max(q["answer_count"], 1) > 3
    ]
    candidates.sort(key=lambda x: x["follower_count"] / max(x["answer_count"], 1), reverse=True)
    
    if candidates:
        for i, q in enumerate(candidates, 1):
            ratio = q["follower_count"] / max(q["answer_count"], 1)
            print(f"\n#{i} [{q.get('keyword','')}]")
            print(f"  {q['title']}")
            print(f"  关注:{q['follower_count']} | 回答:{q['answer_count']} | 浏览:{q['visit_count']} | 比值:{ratio:.1f}")
            print(f"  {q['url']}")
    else:
        print("\n没有符合严格条件的问题。以下是关注数最高的前10个：")
        for i, q in enumerate(all_questions[:10], 1):
            ratio = q["follower_count"] / max(q["answer_count"], 1)
            print(f"\n#{i} [{q.get('keyword','')}]")
            print(f"  {q['title']}")
            print(f"  关注:{q['follower_count']} | 回答:{q['answer_count']} | 浏览:{q['visit_count']} | 比值:{ratio:.1f}")
            print(f"  {q['url']}")


def main():
    args = sys.argv[1:]
    
    # 解析参数
    keywords = []
    direct_qids = []
    mode = "search"  # search 或 questions
    auto_mode = False
    
    i = 0
    while i < len(args):
        if args[i] == "--file":
            i += 1
            if i < len(args):
                with open(args[i], "r", encoding="utf-8") as f:
                    keywords = [line.strip() for line in f if line.strip()]
            i += 1
        elif args[i] == "--questions":
            mode = "questions"
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                direct_qids.append(args[i])
                i += 1
        elif args[i] == "--auto":
            auto_mode = True
            i += 1
        else:
            keywords.append(args[i])
            i += 1
    
    if not keywords and not direct_qids:
        # 默认关键词
        keywords = ["MCP协议", "Cursor 使用", "AI编程工具", "Windsurf Cursor"]
        print(f"[INFO] 未指定关键词，使用默认: {keywords}")
    
    # 启动浏览器
    print("[启动] 正在打开 Chrome...")
    driver = setup_driver()
    
    try:
        # 等待登录
        wait_for_login(driver, auto_mode=auto_mode)
        
        all_questions = []
        
        if mode == "questions":
            # 直接查询问题ID
            print(f"\n[模式] 直接查询 {len(direct_qids)} 个问题")
            for qid in direct_qids:
                try:
                    data = get_question_detail(driver, qid)
                    data["keyword"] = "直接查询"
                    all_questions.append(data)
                    print(f"  [{data['follower_count']}关注/{data['answer_count']}回答/{data['visit_count']}浏览] {data['title'][:55]}")
                except Exception as e:
                    print(f"  ERROR qid={qid}: {e}")
                time.sleep(BETWEEN_REQUESTS_WAIT)
        else:
            # 搜索模式
            for kw in keywords:
                qids = search_keyword(driver, kw)
                
                for qid in qids:
                    # 跳过已抓取的
                    if any(q["id"] == qid for q in all_questions):
                        continue
                    
                    try:
                        data = get_question_detail(driver, qid)
                        data["keyword"] = kw
                        all_questions.append(data)
                        print(f"  [{data['follower_count']}关注/{data['answer_count']}回答/{data['visit_count']}浏览] {data['title'][:55]}")
                    except Exception as e:
                        print(f"  ERROR qid={qid}: {e}")
                    time.sleep(BETWEEN_REQUESTS_WAIT)
        
        # 输出结果
        if all_questions:
            print_summary(all_questions)
            save_results(all_questions)
        else:
            print("\n[WARN] 未抓取到任何问题数据")
    
    finally:
        if not auto_mode:
            print("\n[关闭] 按回车关闭浏览器...")
            try:
                input()
            except EOFError:
                pass
        driver.quit()
        print("[完成]")


if __name__ == "__main__":
    main()
