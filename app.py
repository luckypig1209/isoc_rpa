from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
import time
import io
from PIL import Image

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
    
    return webdriver.Chrome(options=chrome_options)

def take_screenshot(driver, url, wait_time=10):
    """获取网页截图"""
    try:
        driver.get(url)
        time.sleep(wait_time)  # 等待页面加载
        
        # 获取页面实际高度
        page_height = driver.execute_script('return document.documentElement.scrollHeight')
        # 设置窗口大小以适应整个页面
        driver.set_window_size(1920, page_height)
        
        # 截取全页面图片
        screenshot = driver.get_screenshot_as_png()
        
        # 转换为base64
        img_base64 = base64.b64encode(screenshot).decode('utf-8')
        return {
            'success': True,
            'base64': img_base64,
            'message': 'Screenshot captured successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'base64': '',
            'message': f'Error capturing screenshot: {str(e)}'
        }

@app.route('/screenshot', methods=['POST'])
def screenshot():
    """
    截图服务接口
    
    请求体JSON格式：
    {
        "url": "要截图的URL",
        "wait_time": 10  // 可选，等待时间（秒）
    }
    """
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'message': 'URL is required'
            }), 400
            
        url = data['url']
        wait_time = data.get('wait_time', 10)
        
        driver = init_driver()
        try:
            result = take_screenshot(driver, url, wait_time)
            return jsonify(result)
        finally:
            driver.quit()
            
    except Exception as e:
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