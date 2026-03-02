"""调试：检查知乎问题页面的DOM结构，找到标题和数字的正确选择器"""
import time
import re
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

# visit question page
driver.get("https://www.zhihu.com/question/5290049088")
time.sleep(5)

page = driver.page_source

print("=== H1 ELEMENTS ===")
h1s = driver.find_elements(By.TAG_NAME, "h1")
for h in h1s:
    cls = h.get_attribute("class") or ""
    print(f"  h1 class=[{cls}] text=[{h.text[:100]}]")

print("\n=== <title> TAG ===")
m = re.search(r"<title>(.*?)</title>", page)
if m:
    print(f"  {m.group(1)[:100]}")

print("\n=== JSON title in page source ===")
titles = re.findall(r'"title"\s*:\s*"([^"]{10,80})"', page)
for t in titles[:5]:
    print(f"  {t}")

print("\n=== NumberBoard ===")
nums = driver.find_elements(By.CSS_SELECTOR, ".NumberBoard-itemValue")
labs = driver.find_elements(By.CSS_SELECTOR, ".NumberBoard-itemName")
for n, l in zip(nums, labs):
    title_attr = n.get_attribute("title") or ""
    print(f"  {l.text}: text=[{n.text}] title=[{title_attr}]")

if not nums:
    print("  (NumberBoard not found, trying alternatives)")
    # try strong tags with numbers
    strongs = driver.find_elements(By.TAG_NAME, "strong")
    for s in strongs:
        txt = s.text.strip()
        if txt and (txt.replace(",", "").isdigit() or "万" in txt):
            parent_text = s.find_element(By.XPATH, "..").text[:50]
            print(f"  strong: [{txt}] parent: [{parent_text}]")

print("\n=== ANSWER COUNT ===")
# search for "个回答" in page text
matches = re.findall(r"(\d[\d,]*)\s*个回答", page)
print(f"  regex matches: {matches[:5]}")

# also try elements
try:
    els = driver.find_elements(By.XPATH, "//*[contains(text(),'个回答')]")
    for el in els[:3]:
        print(f"  element: tag={el.tag_name} text=[{el.text[:60]}]")
except:
    pass

driver.quit()
print("\n[DONE]")
