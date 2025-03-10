from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
import time
import os
import subprocess
from urllib.parse import urlparse

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
    chrome_options.add_argument('--font-render-hinting=medium')
    chrome_options.add_argument('--enable-font-antialiasing')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--force-color-profile=srgb')
    chrome_options.add_argument('--enable-javascript')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    # 增加更多参数
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--remote-debugging-port=9222')
    # 添加DNS配置
    chrome_options.add_argument('--dns-prefetch-disable')
    chrome_options.add_argument('--host-resolver-rules="MAP * 0.0.0.0 , EXCLUDE localhost"')
    # 添加代理服务器（如果需要）
    # chrome_options.add_argument('--proxy-server=your-proxy-server')
    
    # 设置页面加载策略
    chrome_options.page_load_strategy = 'eager'
    
    return webdriver.Chrome(options=chrome_options)

def capture_screenshot(url, max_retries=3):
    """截取指定URL的页面截图"""
    for attempt in range(max_retries):
        driver = None
        try:
            print(f"\nAttempt {attempt + 1} of {max_retries}")
            driver = init_driver()
            
            # 解析URL
            parsed_url = urlparse(url)
            print(f"Accessing host: {parsed_url.netloc}")
            
            # 尝试ping主机
            try:
                subprocess.run(['ping', '-c', '1', parsed_url.netloc], 
                             stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE)
            except:
                print(f"Warning: Could not ping {parsed_url.netloc}")
            
            print(f"Accessing URL: {url}")
            
            # 设置超时时间
            wait_time = 120  # 增加到120秒
            driver.set_page_load_timeout(wait_time)
            driver.set_script_timeout(wait_time)
            
            # 访问页面
            driver.get(url)
            print("Initial page load complete")
            
            # 等待页面加载完成
            WebDriverWait(driver, wait_time).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            print("Main document ready state complete")
            
            # 等待页面充分加载
            time.sleep(30)  # 增加初始等待时间
            
            # 注入辅助函数
            driver.execute_script("""
                window.forceElementDisplay = function(element) {
                    if (element) {
                        element.style.display = 'block';
                        element.style.visibility = 'visible';
                        element.style.opacity = '1';
                        element.style.width = '100%';
                        element.style.height = '800px';
                        element.style.position = 'relative';
                        element.style.zIndex = '9999';
                    }
                }
            """)
            
            # 处理所有iframe
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Found {len(iframes)} iframes")
            
            for idx, iframe in enumerate(iframes):
                try:
                    print(f"\nProcessing iframe {idx}")
                    iframe_src = iframe.get_attribute('src')
                    print(f"iframe {idx} src: {iframe_src}")
                    
                    # 强制显示iframe
                    driver.execute_script("""
                        arguments[0].scrollIntoView(true);
                        window.forceElementDisplay(arguments[0]);
                    """, iframe)
                    
                    # 等待iframe可见
                    WebDriverWait(driver, 30).until(EC.visibility_of(iframe))
                    print(f"iframe {idx} is visible")
                    
                    # 切换到iframe
                    driver.switch_to.frame(iframe)
                    print(f"Switched to iframe {idx}")
                    
                    # 等待iframe内容加载
                    WebDriverWait(driver, wait_time).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                    
                    # 处理iframe内的元素
                    driver.execute_script("""
                        // 强制显示所有元素
                        var elements = document.getElementsByTagName('*');
                        for(var i = 0; i < elements.length; i++) {
                            window.forceElementDisplay(elements[i]);
                        }
                        
                        // 触发各种事件
                        window.dispatchEvent(new Event('resize'));
                        window.dispatchEvent(new Event('load'));
                        document.dispatchEvent(new Event('DOMContentLoaded'));
                    """)
                    
                    # 等待iframe内容渲染
                    time.sleep(20)  # 增加等待时间
                    print(f"iframe {idx} content processed")
                    
                    # 切回主文档
                    driver.switch_to.default_content()
                    
                except Exception as e:
                    print(f"Error processing iframe {idx}: {str(e)}")
                    driver.switch_to.default_content()
                    continue
            
            # 最终处理
            print("\nFinal processing...")
            time.sleep(20)  # 增加等待时间
            
            # 设置最终页面大小
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
            driver.set_window_size(1920, page_height + 200)
            
            # 最终等待
            time.sleep(10)
            print("Taking screenshot...")
            
            # 截图
            screenshot = driver.get_screenshot_as_png()
            
            # 转换为base64
            img_base64 = base64.b64encode(screenshot).decode('utf-8')
            print("Screenshot captured successfully")
            
            # 保存截图和base64数据
            with open('screenshot.png', 'wb') as f:
                f.write(screenshot)
            with open('screenshot.base64', 'w') as f:
                f.write(img_base64)
                
            print("\nFiles saved:")
            print("- screenshot.png")
            print("- screenshot.base64")
            
            return img_base64
            
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                print("All attempts failed")
                return None
            print("Retrying...")
            time.sleep(5)
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

if __name__ == "__main__":
    # 使用IP地址替代域名
    url = "https://132.254.207.139:18080/?token=eyJhbGciOiJIUzUxMiJ9.eyJleHAiOjM2MzQwOTczMzEsInVzZXIiOiJaREhYRFNNMTk5MzA0MjUiLCJuYW1lIjoiWkRIWERTTTE5OTMwNDI1In0.l6krq2_zfT7b9W8h1MZ8pCtUh_QgjIeXxSSh-UArznzUNuqmbutiCMXfhK5VVe1kwzr-WUGJpFyclcG-roRdFQ&type=2&systaffcode=ZDHXDSM19930425#/sample-general-topoCenter/大数据局管理/大数据局管理/江苏省三级行政区域/默认/extSingleTopo"
    
    print("Starting screenshot capture...")
    base64_data = capture_screenshot(url)
    
    if base64_data:
        print("\nSuccess! Base64 data length:", len(base64_data))
    else:
        print("\nFailed to capture screenshot") 