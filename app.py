from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
import time
import yaml

app = Flask(__name__)

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
        print("主文档加载完成")
        
        # 等待页面充分加载
        time.sleep(15)
        
        # 处理所有iframe
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"找到 {len(iframes)} 个iframe")
        
        for idx, iframe in enumerate(iframes):
            try:
                print(f"\n处理 iframe {idx}")
                iframe_src = iframe.get_attribute('src')
                print(f"iframe {idx} src: {iframe_src}")
                
                # 等待iframe加载完成
                WebDriverWait(driver, 30).until(
                    EC.frame_to_be_available_and_switch_to_it(iframe)
                )
                
                # 等待iframe内容加载
                WebDriverWait(driver, wait_time).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # 切回主文档
                driver.switch_to.default_content()
                
                # 设置iframe样式
                driver.execute_script("""
                    var iframe = arguments[0];
                    iframe.style.width = '100%';
                    iframe.style.height = '800px';
                    iframe.style.display = 'block';
                    iframe.style.visibility = 'visible';
                """, iframe)
                
            except Exception as e:
                print(f"处理 iframe {idx} 时出错: {str(e)}")
                driver.switch_to.default_content()
                continue
        
        # 最终处理
        print("\n最终处理...")
        time.sleep(10)
        
        # 获取页面高度
        page_height = driver.execute_script("""
            return Math.max(
                document.documentElement.scrollHeight,
                document.body.scrollHeight
            );
        """)
        
        # 设置窗口大小
        driver.set_window_size(1920, page_height)
        
        # 等待内容渲染
        time.sleep(5)
        
        # 截图
        screenshot = driver.get_screenshot_as_png()
        print("截图完成")
        
        # 转换为base64
        img_base64 = base64.b64encode(screenshot).decode('utf-8')
        
        return {
            'success': True,
            'base64': img_base64,
            'message': 'Screenshot captured successfully'
        }
        
    except Exception as e:
        print(f"截图错误: {str(e)}")
        return {
            'success': False,
            'base64': '',
            'message': f'Error capturing screenshot: {str(e)}'
        }

@app.route('/screenshot', methods=['POST'])
def screenshot():
    """截图服务接口"""
    try:
        # 读取配置文件
        with open('config.test.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 查找test123的配置
        target = next((t for t in config['targets'] if t['name'] == 'test123'), None)
        if not target:
            return jsonify({
                'success': False,
                'message': 'test123 configuration not found'
            }), 400
            
        driver = init_driver()
        try:
            result = take_screenshot(driver, target['url'])
            return jsonify(result)
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"服务错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 