from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
import time
import os
from typing import Optional
from pydantic import BaseModel, HttpUrl

# 配置 FastAPI，禁用自动文档（我们将自定义）
app = FastAPI(
    title="Screenshot Service", 
    description="网页截图服务",
    docs_url=None,  # 禁用默认的 /docs
    redoc_url=None,  # 禁用默认的 /redoc
)

# 挂载静态文件目录（用于提供 Swagger UI 和 ReDoc 的静态资源）
app.mount("/static", StaticFiles(directory="static"), name="static")

# 自定义 Swagger UI，使用本地静态文件
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """自定义 Swagger UI，使用本地静态文件（完全本地化）"""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.min.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.min.css",
        swagger_favicon_url="/static/swagger-ui/favicon-32x32.png",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """ReDoc 文档页面，使用本地静态文件"""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc/redoc.standalone.js",
        redoc_favicon_url="/static/swagger-ui/favicon-32x32.png",
    )

class ScreenshotRequest(BaseModel):
    url: str
    wait_time: Optional[int] = 30  # 等待时间（秒），默认30秒
    width: Optional[int] = 1920  # 窗口宽度，默认1920
    height: Optional[int] = 1080  # 窗口高度，默认1080

def init_driver(width: int = 1920, height: int = 1080):
    """初始化 Chrome driver"""
    chrome_options = ChromeOptions()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument(f'--window-size={width},{height}')
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument('--ignore-certificate-errors')
    # 允许通过环境变量覆盖浏览器二进制路径
    chrome_bin = os.getenv('CHROME_BIN', '/usr/bin/google-chrome')
    chrome_options.binary_location = chrome_bin
    
    # 明确指定chromedriver路径
    chromedriver_path = os.getenv('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver')
    service = Service(chromedriver_path)
    
    return webdriver.Chrome(options=chrome_options, service=service)

def take_screenshot(driver, url: str, wait_time: int = 30):
    """获取网页截图"""
    try:
        print(f"访问URL: {url}")
        
        # 确保URL有协议
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
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
        
        # 等待页面充分加载（等待动态内容）
        time.sleep(5)
        
        # 处理所有iframe，确保它们都加载完成
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"找到 {len(iframes)} 个iframe")
        
        for idx, iframe in enumerate(iframes):
            try:
                print(f"处理 iframe {idx}")
                # 等待iframe加载完成
                WebDriverWait(driver, 10).until(
                    EC.frame_to_be_available_and_switch_to_it(iframe)
                )
                # 等待iframe内容加载
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                # 切回主文档
                driver.switch_to.default_content()
            except Exception as e:
                print(f"处理 iframe {idx} 时出错: {str(e)}")
                driver.switch_to.default_content()
                continue
        
        # 最终等待，确保所有内容渲染完成
        print("等待内容渲染...")
        time.sleep(3)
        
        # 确保滚动到顶部
        driver.execute_script("window.scrollTo(0, 0);")
        
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

@app.get("/")
def root():
    """根路径，返回服务信息"""
    return {
        "service": "Screenshot Service",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "健康检查",
            "GET /screenshot": "通过GET方式截图（url参数）",
            "POST /screenshot": "通过POST方式截图（JSON body）"
        }
    }

@app.get("/health")
def health_check():
    """健康检查接口"""
    return {
        'status': 'healthy',
        'timestamp': time.time()
    }

@app.get("/screenshot")
def screenshot_get(
    url: str = Query(..., description="要截图的URL地址"),
    wait_time: int = Query(30, ge=1, le=300, description="等待时间（秒），1-300"),
    width: int = Query(1920, ge=100, le=3840, description="窗口宽度，100-3840"),
    height: int = Query(1080, ge=100, le=2160, description="窗口高度，100-2160")
):
    """通过GET方式截图"""
    driver = None
    try:
        driver = init_driver(width, height)
        result = take_screenshot(driver, url, wait_time)
        
        if result['success']:
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=500, detail=result['message'])
    except Exception as e:
        print(f"服务错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')
    finally:
        if driver:
            driver.quit()

@app.post("/screenshot")
def screenshot_post(request: ScreenshotRequest):
    """通过POST方式截图"""
    driver = None
    try:
        driver = init_driver(request.width, request.height)
        result = take_screenshot(driver, request.url, request.wait_time)
        
        if result['success']:
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=500, detail=result['message'])
    except Exception as e:
        print(f"服务错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f'Server error: {str(e)}')
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)

