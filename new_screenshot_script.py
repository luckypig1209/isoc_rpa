# 新的截图脚本 - 不进行相似度比对，直接截图发送到钉钉群
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
import yaml
import os
import glob
import urllib3
from PIL import Image
import io

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置文件路径
cfg_file_path = "config.new.yaml"

# 新的URL配置
NEW_URL = "http://177.11.176.11:23343/yitu/#/chart/publishShort/4ujd3lwbaow000"
NEW_TARGET_NAME = "new_chart"
DINGDING_ROBOT_ID = "2206"  # 新的钉钉群ID

class IframeLoaded:
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        try:
            print("等待 iframe 出现...")
            time.sleep(3)
            
            print(f"尝试查找: {self.locator[1]}")
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

# 加载配置
try:
    with open(cfg_file_path, 'r', encoding='utf-8') as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)
except FileNotFoundError:
    workdir = os.getcwd()
    print(f"config file {cfg_file_path} not found, current workdir {workdir}")
    exit(1)
except yaml.YAMLError as e:
    print(f"parse yaml file error: {e}")
    exit(1)

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

def take_screenshot(driver, target: any) -> tuple[bool, str, str, str, str, float]:
    """截图函数"""
    try:
        target_name = target['name']
        url = target['url']
        open_wait_secs = target.get('open-wait-secs', 10)
        after_load_wait_secs = target.get('after-load-wait-secs', 0)
        elements_check = target.get('elements-check', [])
        
        print(f"\n开始处理目标: {target_name}")
        print(f"访问URL: {url}")
        
        start_time = time.time()
        driver.get(url)
        print(f"页面加载完成，耗时: {time.time() - start_time:.2f}秒")
        
        # 等待页面加载
        if elements_check:
            for element_check in elements_check:
                element_type = element_check['type']
                locator = element_check['locator']
                locator_type = locator['type']
                locator_val = locator['value']
                
                # 转换定位器类型
                by_type = getattr(By, locator_type.replace('-', '_').upper())
                
                # 等待元素出现
                ready_wait = WebDriverWait(driver, open_wait_secs)
                
                if element_type == 'iframe':
                    cond = IframeLoaded((by_type, locator_val))
                else:
                    cond = EC.presence_of_element_located((by_type, locator_val))
                
                ready_wait.until(cond)
        else:
            print("无需等待特定元素，直接截图")
            time.sleep(open_wait_secs)
            
            if after_load_wait_secs > 0:
                print(f"额外等待 {after_load_wait_secs} 秒...")
                time.sleep(after_load_wait_secs)
        
        # 等待渲染完成
        print("等待渲染完成...")
        time.sleep(2)
        
        # 重置滚动位置
        driver.execute_script('window.scrollTo(0, 0);')
        print("页面滚动重置完成")
        
        # 获取全页面截图
        print("开始截取全页面...")
        full_img = driver.get_screenshot_as_png()
        full_b64_wx = base64.b64encode(full_img).decode('utf-8')
        full_b64_ding = "data:image/png;base64," + full_b64_wx
        print("全页面截图完成")
        
        # 如果没有 elements_check，直接返回全页面截图
        if not elements_check:
            return True, full_b64_wx, full_b64_ding, full_b64_wx, full_b64_ding, time.time() - start_time
            
        # 初始化iframe截图的base64字符串
        iframe_b64_wx = ""
        iframe_b64_ding = ""
        
        try:
            for element_check in elements_check:
                capture_config = element_check.get('capture')
                
                if capture_config:
                    print(f"Capturing {target_name} at: {capture_config}")
                    
                    full_image = Image.open(io.BytesIO(full_img))
                    
                    # 裁剪图片
                    iframe_image = full_image.crop((
                        int(capture_config['x']),
                        int(capture_config['y']),
                        int(capture_config['x']) + int(capture_config['width']),
                        int(capture_config['y']) + int(capture_config['height'])
                    ))
                    
                    # 转换为base64
                    buffered = io.BytesIO()
                    iframe_image.save(buffered, format="PNG")
                    iframe_b64_wx = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    iframe_b64_ding = "data:image/png;base64," + iframe_b64_wx
                    
        except Exception as e:
            print(f"iframe截图失败: {str(e)}")
        
        return True, full_b64_wx, full_b64_ding, iframe_b64_wx, iframe_b64_ding, time.time() - start_time
        
    except Exception as e:
        print(f"处理失败: {target_name}")
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
            return
            
        except requests.exceptions.RequestException as e:
            print(f"第 {attempt + 1} 次发送图片失败: {str(e)}")
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                print(f"发送图片最终失败，已达到最大重试次数")

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

def combine_images(images_data: list, titles: list = None) -> str:
    """将多张图片垂直合并成一张图片，并返回base64编码"""
    # 转换所有图片为PIL Image对象
    pil_images = []
    for img_data in images_data:
        if isinstance(img_data, str) and img_data.startswith('data:image'):
            # 处理base64格式的图片
            img_data = img_data.split('base64,')[1]
            img_bytes = base64.b64decode(img_data)
            img = Image.open(io.BytesIO(img_bytes))
        elif isinstance(img_data, str):
            # 处理普通base64格式
            img_bytes = base64.b64decode(img_data)
            img = Image.open(io.BytesIO(img_bytes))
        elif isinstance(img_data, Image.Image):
            img = img_data
        else:
            img_bytes = img_data
            img = Image.open(io.BytesIO(img_bytes))
        pil_images.append(img)

    # 计算合并后图片的尺寸
    max_width = max(img.width for img in pil_images)
    total_height = sum(img.height for img in pil_images)
    
    # 如果有标题，为每个标题预留空间
    title_height = 30 if titles else 0
    total_height += len(pil_images) * title_height

    # 创建新图片
    combined_image = Image.new('RGB', (max_width, total_height), 'white')
    
    # 绘制图片和标题
    current_y = 0
    for i, img in enumerate(pil_images):
        if titles and i < len(titles):
            # 如果有标题，添加标题文本
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(combined_image)
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
            draw.text((10, current_y), titles[i], fill='black', font=font)
            current_y += title_height

        # 调整图片大小以匹配最大宽度
        if img.width != max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        combined_image.paste(img, (0, current_y))
        current_y += img.height

    # 转换为base64
    buffer = io.BytesIO()
    combined_image.save(buffer, format='PNG')
    combined_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return combined_b64

def screenshot_it(target: any, results: dict):
    """截图主函数，包含重试逻辑"""
    target_name = target["name"]
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            success, full_b64_wx, full_b64_ding, iframe_b64_wx, iframe_b64_ding, load_time = take_screenshot(driver, target)
            
            if success:
                print(f"成功截图: {target_name}")
                # 保存全页面截图
                full_screenshot_path = os.path.join(backup_dir, f'{target_name}_full.png')
                driver.save_screenshot(full_screenshot_path)
                
                # 存储结果
                results[target_name] = {
                    'full_path': full_screenshot_path,
                    'load_time': load_time
                }
                
                # 如果有iframe截图，保存
                if iframe_b64_wx:
                    print(f"保存 iframe 截图: {target_name}")
                    iframe_screenshot_path = os.path.join(backup_dir, f'{target_name}_iframe.png')
                    with open(iframe_screenshot_path, 'wb') as f:
                        f.write(base64.b64decode(iframe_b64_wx))
                
                return
                
        except Exception as e:
            print(f"处理失败: {target_name}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error details: {e.args}")
            
        if attempt < max_retries - 1:
            print(f"重试截图: {target_name}")
            time.sleep(5)
        else:
            print(f"截图失败，已达到最大重试次数: {target_name}")

# 主执行流程
print("开始执行新的截图脚本...")
print(f"目标URL: {NEW_URL}")
print(f"钉钉群ID: {DINGDING_ROBOT_ID}")

results = {}  # 存储所有结果

# 执行截图
for target in config_data["targets"]:
    screenshot_it(target, results)

# 在所有截图完成后处理结果
if results:
    # 合并所有全页面截图
    full_images = []
    titles = []
    for target_name, result in results.items():
        if os.path.exists(result['full_path']):
            full_images.append(Image.open(result['full_path']))
            titles.append(target_name)
    
    # 合并图片
    if full_images:
        combined_b64 = combine_images(full_images, titles)
        combined_b64_ding = "data:image/png;base64," + combined_b64
        
        # 构建汇总消息
        summary_message = "监控结果汇总：\n"
        for target_name, result in results.items():
            summary_message += f"\n{target_name}:\n"
            summary_message += f"- 加载耗时: {result['load_time']:.2f}秒\n"
        
        # 发送合并后的图片和汇总消息到新的钉钉群
        print(f"发送图片到钉钉群 {DINGDING_ROBOT_ID}")
        DinghatSendImg(combined_b64_ding, DINGDING_ROBOT_ID)
        
        print(f"发送汇总消息到钉钉群 {DINGDING_ROBOT_ID}")
        send_message_to_dingding(summary_message, DINGDING_ROBOT_ID)
        
        print("所有操作完成！")
    else:
        print("没有找到可用的截图")
else:
    print("没有成功截图")

driver.quit() 