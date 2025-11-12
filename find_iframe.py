from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def find_iframe_id(url):
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        print(f"\n检查URL: {url}")
        driver.get(url)
        time.sleep(10)  # 等待页面加载
        
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"找到 {len(iframes)} 个iframe")
        
        for idx, iframe in enumerate(iframes):
            iframe_id = iframe.get_attribute('id')
            parent_id = iframe.find_element(By.XPATH, "..").get_attribute('id')
            print(f"Iframe {idx}:")
            print(f"  - ID: {iframe_id}")
            print(f"  - Parent ID: {parent_id}")
            print(f"  - CSS Selector: #{parent_id} iframe")
            
    finally:
        driver.quit()

# 测试两个URL
urls = [
    "http://132.254.207.139:38080/yitu/index.html#/chart/publishShort/521k2hs8qh0000",
    "http://132.254.207.139:38080/yitu/index.html#/chart/publishShort/5u6xbvxhmts000"
]

for url in urls:
    find_iframe_id(url) 