from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
import time
import requests
import urllib3
import yaml

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def init_driver():
    """初始化 Chrome driver"""
    chrome_options = ChromeOptions()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.binary_location = '/usr/bin/chromium'
    
    return webdriver.Chrome(options=chrome_options)

def take_screenshot(driver, url, wait_time=60):
    """获取网页截图"""
    try:
        print(f"访问URL: {url}")
        
        # 设置超时时间
        driver.set_page_load_timeout(wait_time)
        driver.set_script_timeout(wait_time)
        
        # 访问页面
        driver.get(url)
        print("页面加载完成")
        
        # 等待页面加载
        WebDriverWait(driver, wait_time).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # 额外等待确保内容加载
        time.sleep(10)
        
        # 获取页面高度并设置窗口大小
        page_height = driver.execute_script('''
            return Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.offsetHeight,
                document.body.clientHeight,
                document.documentElement.clientHeight
            );
        ''')
        driver.set_window_size(1920, page_height + 100)
        
        # 重置滚动位置
        driver.execute_script('window.scrollTo(0, 0);')
        
        # 最终等待
        time.sleep(5)
        
        # 截图
        screenshot = driver.get_screenshot_as_png()
        print("截图完成")
        
        # 转换为base64
        img_base64 = base64.b64encode(screenshot).decode('utf-8')
        img_base64_ding = "data:image/png;base64," + img_base64
        
        return True, img_base64_ding
        
    except Exception as e:
        print(f"截图错误: {str(e)}")
        return False, None

def send_to_dingding(image_base64: str, robot_id: str = "1183"):
    """发送图片到钉钉"""
    try:
        # 发送图片，使用图片消息格式
        resp = requests.post(
            'https://cnioc.telecomjs.com:18080/serv/atom-center/atom/v1.0/atom_center/dsjj_message',
            json={
                "content": {
                    "msgtype": "image",
                    "image": {
                        "base64": image_base64.split('base64,')[1],  # 移除 data:image/png;base64, 前缀
                        "title": "test123 页面监控截图"
                    }
                },
                "robot_id": robot_id
            },
            headers={
                "staffCode": "GUOMO",
                "app-key": "B8D16767C25A3C377C2A8F7DBFF68D36"
            },
            verify=False
        )
        print(f"图片发送响应: {resp.text}")
        
        # 发送说明消息
        message = "test123 页面监控截图"
        resp = requests.post(
            'https://cnioc.telecomjs.com:18080/serv/atom-center/atom/v1.0/atom_center/dsjj_message',
            json={
                "content": {
                    "msgtype": "text",
                    "text": {
                        "content": message
                    }
                },
                "robot_id": robot_id
            },
            headers={
                "staffCode": "GUOMO",
                "app-key": "B8D16767C25A3C377C2A8F7DBFF68D36"
            },
            verify=False
        )
        print(f"消息发送响应: {resp.text}")
        
        return True
        
    except Exception as e:
        print(f"发送失败: {str(e)}")
        return False

def main():
    # 读取配置文件
    with open('config.test.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 查找test123的配置
    target = next((t for t in config['targets'] if t['name'] == 'test123'), None)
    if not target:
        print("未找到test123的配置")
        return
    
    # 初始化driver
    driver = init_driver()
    try:
        # 截图
        success, img_base64 = take_screenshot(driver, target['url'])
        if success and img_base64:
            # 发送到钉钉
            if send_to_dingding(img_base64):
                print("截图已成功发送到钉钉")
            else:
                print("发送到钉钉失败")
        else:
            print("截图失败")
    finally:
        driver.quit()

if __name__ == "__main__":
    main() 