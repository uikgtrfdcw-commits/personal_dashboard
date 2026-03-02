"""读取知乎专栏文章内容"""
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

COOKIE_STR = '_zap=f70d2cc8-1c1e-4381-8d47-0c9ace806b8a; d_c0=njCUCZdQxxuPTpg4YTKf4D93JPO2vcD67s0=|1770012258; z_c0=2|1:0|10:1770012934|4:z_c0|92:Mi4xOHZzdkFBQUFBQUNlTUpRSmwxREhHeGNBQUFCZ0FsVk5kWXh0YWdDV2ZReXNpeFY5Zmg3aUU2TW41VEZEY0pQNTFn|70b29f833c24722f7867c04e74c5db665df64a59faf6a3afce1f7f536501d2cb; _xsrf=efc43ffb-b060-49a5-a059-3a5dbcf7f1c5; SESSIONID=V4mhgSdk87QLenHzoIk3Qs2LAVs9R0isnSMYx6y6MbR'

local_driver = r"C:\Users\sweet\.wdm\drivers\chromedriver\win64\144.0.7559.133\chromedriver-win32\chromedriver.exe"

opts = Options()
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)
opts.add_argument("--window-size=1280,900")

driver = webdriver.Chrome(service=Service(local_driver), options=opts)
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": 'Object.defineProperty(navigator, "webdriver", {get: () => undefined});'
})

# inject cookies
driver.get("https://www.zhihu.com")
time.sleep(2)
for c in COOKIE_STR.split("; "):
    if "=" in c:
        n, v = c.split("=", 1)
        try:
            driver.add_cookie({"name": n, "value": v, "domain": ".zhihu.com"})
        except:
            pass
driver.refresh()
time.sleep(2)

# visit article
driver.get("https://zhuanlan.zhihu.com/p/149751089")
time.sleep(5)

# scroll to bottom to load all content
for _ in range(5):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
driver.execute_script("window.scrollTo(0, 0);")
time.sleep(1)

# extract content - get full HTML to preserve structure
try:
    article = driver.find_element(By.CSS_SELECTOR, ".Post-RichTextContainer, .RichText, article")
    # get innerHTML to see headings and links
    html = article.get_attribute("innerHTML")
    # save to file for analysis
    with open("article_content.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML saved to article_content.html")
    # also print text
    print("\n=== FULL TEXT ===")
    print(article.text)
except Exception as e:
    print(f"ERROR: {e}")
    body = driver.find_element(By.TAG_NAME, "body")
    print(body.text[:30000])

driver.quit()
