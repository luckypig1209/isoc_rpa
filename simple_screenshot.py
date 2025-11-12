# 简化版截图脚本 - 专门用于新URL，直接截图发送到钉钉群
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as OptionsChrome
import requests
import base64
import os
import urllib3
from PIL import Image
import io

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置参数
TARGET_URL = "http://177.11.176.11:23343/yitu/#/chart/publishShort/4ujd3lwbaow000"
TARGET_NAME = "new_chart"
DINGDING_ROBOT_ID = "1183"  # 新的钉钉群ID
WAIT_TIME = 30  # 等待页面加载的时间
AFTER_LOAD_WAIT = 10  # 加载后的额外等待时间

class IframeLoaded:
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        try:
            print("等待 iframe 出现...")
            time.sleep(3)
            
            print(f"尝试查找 iframe: {self.locator[1]}")
            element = driver.find_element(*self.locator)
            if not element:
                print("未找到 iframe")
                return False
                
            print("找到 iframe，等待内容加载...")
            
            # 切换到 iframe
            driver.switch_to.frame(element)
            
            try:
                # 等待 iframe 内容加载
                body_element = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 等待页面完全加载
                WebDriverWait(driver, 30).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # 检查 iframe 是否有实际内容
                content_elements = driver.find_elements(By.CSS_SELECTOR, "div, canvas, svg, .chart-wrap")
                has_content = len(content_elements) > 0
                
                if has_content:
                    print(f"找到 {len(content_elements)} 个内容元素")
                    time.sleep(5)  # 等待渲染完成
                else:
                    print("未找到内容元素")
                
                # 切回主文档
                driver.switch_to.default_content()
                return has_content
                
            finally:
                # 确保切回主文档
                driver.switch_to.default_content()
                
        except Exception as e:
            print(f"Iframe load check failed: {str(e)}")
            print("当前页面 URL:", driver.current_url)
            try:
                all_iframes = driver.find_elements(By.TAG_NAME, "iframe")
                print("页面中的所有 iframe 数量:", len(all_iframes))
                for idx, iframe in enumerate(all_iframes):
                    print(f"iframe {idx} id:", iframe.get_attribute("id"))
            except:
                pass
            return False

# Chrome配置
options = OptionsChrome()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--start-maximized')
options.add_argument('--window-size=1920,1080')
options.add_argument('--hide-scrollbars')
options.add_argument('--ignore-certificate-errors')
options.binary_location = '/usr/bin/chromium'

# 创建Chrome驱动
driver = webdriver.Chrome(
    options=options,
    service=Service('/usr/bin/chromedriver')
)

# 创建历史记录目录
timestamp = datetime.now().strftime('%Y%m%d-%H%M')
backup_dir = os.path.join(os.getcwd(), '.history', timestamp)
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

def take_screenshot():
    """截图函数"""
    try:
        print(f"\n开始处理目标: {TARGET_NAME}")
        print(f"访问URL: {TARGET_URL}")
        
        start_time = time.time()
        driver.get(TARGET_URL)
        print(f"页面加载完成，耗时: {time.time() - start_time:.2f}秒")
        
        # 等待页面加载
        print(f"等待页面加载 {WAIT_TIME} 秒...")
        time.sleep(WAIT_TIME)
        
        # 尝试查找并等待iframe
        try:
            iframe_locator = (By.CSS_SELECTOR, "#h74i8m87jvc00 iframe")
            iframe_loaded = IframeLoaded(iframe_locator)
            iframe_loaded(driver)
            print("iframe 加载检查完成")
        except Exception as e:
            print(f"iframe 检查失败，继续截图: {str(e)}")
        
        # 额外等待时间
        if AFTER_LOAD_WAIT > 0:
            print(f"额外等待 {AFTER_LOAD_WAIT} 秒...")
            time.sleep(AFTER_LOAD_WAIT)
        
        # 等待渲染完成
        print("等待渲染完成...")
        time.sleep(2)
        
        # 重置滚动位置
        driver.execute_script('window.scrollTo(0, 0);')
        print("页面滚动重置完成")
        
        # 获取全页面截图
        print("开始截取全页面...")
        full_img = driver.get_screenshot_as_png()
        full_b64 = base64.b64encode(full_img).decode('utf-8')
        print("截图的base64编码:\n")
        print(full_b64)
        full_b64_ding = "data:image/png;base64," + full_b64
        print("全页面截图完成")
        
        return True, full_b64, full_b64_ding, "", "", time.time() - start_time
        
    except Exception as e:
        print(f"处理失败: {TARGET_NAME}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e.args}")
        return False, "", "", "", "", 0

def DinghatSendImg(b64Img: str, robot_id: str):
    """发送图片到钉钉"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                r'https://cnioc.telecomjs.com:18080/serv/atom-center/atom/v1.0/atom_center/isoc_message_ding_pic',
                json={
                    "imageBase64": b64Img,
                    "robot_id": robot_id,
                    "robot_user_name": "1"
                },
                headers={
                    "staffCode": "GUOMO",
                    "app-key": "F00BDA1FA533FBDE87F7CB8DC5B7110F"
                },
                verify=False
            )
            
            print(f"图片发送响应: {resp.text}")
            
            # 检查响应状态
            if resp.status_code == 200:
                try:
                    resp_data = resp.json()
                    # 检查钉钉API的返回状态
                    if resp_data.get('resCode') == '200':
                        atom_data = resp_data.get('data', {}).get('atom_data', {})
                        if atom_data.get('result_code') == 1:
                            print("✅ 图片发送成功！")
                            return True
                        else:
                            print(f"❌ 图片发送失败: atom_data.result_code = {atom_data.get('result_code')}")
                    else:
                        print(f"❌ 图片发送失败: resCode = {resp_data.get('resCode')}")
                except Exception as e:
                    print(f"❌ 解析响应失败: {str(e)}")
            else:
                print(f"❌ HTTP状态码错误: {resp.status_code}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            
        except requests.exceptions.RequestException as e:
            print(f"第 {attempt + 1} 次发送图片失败: {str(e)}")
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
    
    print(f"❌ 发送图片最终失败，已达到最大重试次数")
    return False

def send_message_to_dingding(message: str, robot_id: str):
    """发送消息到钉钉群"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                'https://cnioc.telecomjs.com:18080/serv/atom-center/atom/v1.0/atom_center/dsjj_message',
                json={
                    "content": message,
                    "robot_id": robot_id
                },
                headers={
                    "staffCode": "GUOMO",
                    "app-key": "B8D16767C25A3C377C2A8F7DBFF68D36"
                },
                verify=False
            )
            print(f"消息发送响应: {resp.text}")
            return
            
        except requests.exceptions.RequestException as e:
            print(f"第 {attempt + 1} 次发送消息失败: {str(e)}")
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                print(f"发送消息最终失败，已达到最大重试次数")

def save_screenshots(full_img):
    """保存截图到本地"""
    try:
        # 保存全页面截图
        full_screenshot_path = os.path.join(backup_dir, f'{TARGET_NAME}_full.png')
        with open(full_screenshot_path, 'wb') as f:
            f.write(full_img)
        print(f"全页面截图已保存: {full_screenshot_path}")
            
    except Exception as e:
        print(f"保存截图失败: {str(e)}")

# 主执行流程
def main():
    print("开始执行简化版截图脚本...")
    print(f"目标URL: {TARGET_URL}")
    print(f"钉钉群ID: {DINGDING_ROBOT_ID}")
    print(f"等待时间: {WAIT_TIME}秒")
    print(f"额外等待时间: {AFTER_LOAD_WAIT}秒")
    
    try:
        # 执行截图
        success, full_b64, full_b64_ding, _, _, load_time = take_screenshot()
        
        if success:
            print(f"成功截图: {TARGET_NAME}")
            
            # 保存截图到本地
            full_img = base64.b64decode(full_b64)
            save_screenshots(full_img)
            
            # 构建消息
            summary_message = "苏州产数运营驾驶舱巡检正常！"
            
            # 发送截图到钉钉群
            print(f"发送图片到钉钉群 {DINGDING_ROBOT_ID}")
            # 只发送全页面截图
            img_sent = DinghatSendImg(full_b64_ding, DINGDING_ROBOT_ID)
            
            if not img_sent:
                print("⚠️ 图片发送失败，但继续发送文字消息")
            
            # 发送汇总消息
            print(f"发送汇总消息到钉钉群 {DINGDING_ROBOT_ID}")
            send_message_to_dingding(summary_message, DINGDING_ROBOT_ID)
            
            print("所有操作完成！")
        else:
            print("截图失败")
            
    except Exception as e:
        print(f"执行过程中发生错误: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main() 