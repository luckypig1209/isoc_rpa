# This is a sample Python script.
import time
from datetime import datetime

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

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
import cv2
import numpy as np
import glob
import urllib3
from PIL import Image
import io

# 在脚本开始处添加以下代码，禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

cfg_file_path = "config.test.yaml"

# 添加名称映射字典
NAME_MAPPINGS = {
    'ybiframe': '医保局网络监控',
    'dsjiframe': '电子政务外网监控',
    'tciframe': '江苏体彩智能网络监控',
    'gatiframe': '公安二级主干网络监控',
    'wltiframe': '省文旅厅监控项目派单统计',
    'gyiframe': '省高级人民法院',
    'abaaba': '省医保信息系统感知平台'
}

class VideoLoaded:
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        element = driver.find_element(*self.locator)
        ready_state = element.get_attribute("readyState")
        # readyState
        return int(ready_state) >= 4


class ElementLoaded:
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        element = driver.find_element(*self.locator)
        javascript_code = "return window.getComputedStyle(arguments[0]).opacity!== '0'"
        result = driver.execute_script(javascript_code, element)
        return result


class IframeLoaded:
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        try:
            print("等待 iframe 出现...")
            # 先等待一段时间让页面加载
            time.sleep(3)  # 增加初始等待时间
            
            # 尝试查找 iframe
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
                body_element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 等待页面完全加载
                WebDriverWait(driver, 20).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # 检查 iframe 是否有实际内容
                content_elements = driver.find_elements(By.CSS_SELECTOR, "div, canvas, svg, .chart-wrap")
                has_content = len(content_elements) > 0
                
                if has_content:
                    print(f"找到 {len(content_elements)} 个内容元素")
                    # 额外等待确保图表渲染完成
                    time.sleep(2)
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
            # 打印更多调试信息
            print("当前页面 URL:", driver.current_url)
            try:
                all_iframes = driver.find_elements(By.TAG_NAME, "iframe")
                print("页面中的所有 iframe 数量:", len(all_iframes))
                for idx, iframe in enumerate(all_iframes):
                    print(f"iframe {idx} id:", iframe.get_attribute("id"))
            except:
                pass
            return False

# load config
try:
    with open(cfg_file_path, 'r', encoding='utf-8') as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)
        # print(config_data)
except FileNotFoundError:
    workdir = os.getcwd()
    print(f"config file {cfg_file_path} not found, current workdir {workdir}")
    exit(1)
except yaml.YAMLError as e:
    print(f"parse yaml file error: {e}")
    exit(1)


options = OptionsChrome()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--start-maximized')  # 最大化窗口
options.add_argument('--window-size=1920,1080')  # 设置固定窗口大小
options.add_argument('--hide-scrollbars')  # 隐藏滚动条
options.add_argument('--ignore-certificate-errors')
options.binary_location = '/usr/bin/chromium'  # 指定 Chromium 位置

# 使用 ChromeDriver 的路径
driver = webdriver.Chrome(
    options=options,
    service=Service('/usr/bin/chromedriver')  # 指定 chromedriver 路径
)

def cleanup_old_backups(history_dir: str, days: int = 5):
    """清理指定天数之前的备份文件"""
    if not os.path.exists(history_dir):
        return
        
    current_time = datetime.now()
    # 遍历历史目录
    for dirname in os.listdir(history_dir):
        try:
            # 解析目录名中的日期时间（格式：YYYYMMDD-HHMM）
            dir_time = datetime.strptime(dirname, '%Y%m%d-%H%M')
            # 计算目录年龄（天数）
            dir_age = (current_time - dir_time).days
            
            if dir_age >= days:
                dir_path = os.path.join(history_dir, dirname)
                # 删除目录及其内容
                for file in os.listdir(dir_path):
                    os.remove(os.path.join(dir_path, file))
                os.rmdir(dir_path)
                print(f"Cleaned up old backup: {dirname}")
        except ValueError:
            # 如果目录名格式不正确，跳过
            continue

# 清理5天前的备份
history_dir = os.path.join(os.getcwd(), '.history')
cleanup_old_backups(history_dir)

# 在开始执行前创建历史记录目录
timestamp = datetime.now().strftime('%Y%m%d-%H%M')
backup_dir = os.path.join(os.getcwd(), '.history', timestamp)
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

def get_element_dimensions(driver, element):
    """获取元素的实际位置和大小"""
    return driver.execute_script("""
        var rect = arguments[0].getBoundingClientRect();
        return {
            x: rect.left,
            y: rect.top,
            width: rect.width,
            height: rect.height
        };
    """, element)

def take_screenshot(driver, target: any) -> tuple[bool, str, str, str, str, float]:
    try:
        target_name = target['name']
        url = target['url']
        open_wait_secs = target.get('open-wait-secs', 10)
        after_load_wait_secs = target.get('after-load-wait-secs', 0)  # 新增配置项
        elements_check = target.get('elements-check', [])
        
        print(f"\n开始处理目标: {target_name}")
        print(f"访问URL: {url}")
        
        start_time = time.time()
        driver.get(url)
        print(f"页面加载完成，耗时: {time.time() - start_time:.2f}秒")
        
        # 等待页面加载
        if elements_check:  # 只有在有elements_check时才执行等待
            for element_check in elements_check:
                element_type = element_check['type']
                locator = element_check['locator']
                locator_type = locator['type']
                locator_val = locator['value']
                
                # 转换定位器类型
                by_type = getattr(By, locator_type.replace('-', '_').upper())
                
                # 等待元素出现
                ready_wait = WebDriverWait(driver, open_wait_secs)
                
                if element_type == 'video':
                    cond = VideoLoaded((by_type, locator_val))
                elif element_type == 'iframe':
                    cond = IframeLoaded((by_type, locator_val))
                else:
                    cond = ElementLoaded((by_type, locator_val))
                
                ready_wait.until(cond)
        else:
            print("无需等待特定元素，直接截图")
            time.sleep(open_wait_secs)  # 使用配置的等待时间
            
            if after_load_wait_secs > 0:  # 如果配置了额外等待时间
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
                    # 打印页面信息
                    window_size = driver.get_window_size()
                    scroll_position = driver.execute_script('return {x: window.pageXOffset, y: window.pageYOffset};')
                    print(f"Window size: {window_size}")
                    print(f"Scroll position: {scroll_position}")
                    
                    # 使用绝对定位
                    capture_coords = {
                        'x': round(float(capture_config['x'])),
                        'y': round(float(capture_config['y'])),
                        'width': round(float(capture_config['width'])),
                        'height': round(float(capture_config['height']))
                    }
                    
                    print(f"Capturing {target_name} at: {capture_coords}")
                    
                    full_image = Image.open(io.BytesIO(full_img))
                    
                    # 裁剪图片
                    iframe_image = full_image.crop((
                        capture_coords['x'],
                        capture_coords['y'],
                        capture_coords['x'] + capture_coords['width'],
                        capture_coords['y'] + capture_coords['height']
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

def WechatSendImg(b64Img: str, level: str):
    """发送图片到微信"""
    resp = requests.post(r'https://cnioc.telecomjs.com:18080/serv/atom-center/atom/v1.0/atom_center/isoc_message_wx_pic', json={
        "imageBase64": b64Img,
        "wxLevel": level
    }, headers={
        "staffCode": "DINGYU5",
        "app-key": "5269A2FAFFAD01907FA561B808F80918"
    })
    print(resp.text)

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
                    "robot_id": "1183",
                    "robot_user_name": "1"
                },
                headers={
                    "staffCode": "GUOMO",
                    "app-key": "F00BDA1FA533FBDE87F7CB8DC5B7110F"
                },
                verify=False  # 忽略SSL证书验证
            )
            print(resp.text)
            return  # 发送成功，退出重试
            
        except requests.exceptions.RequestException as e:
            print(f"第 {attempt + 1} 次发送图片失败: {str(e)}")
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                print(f"发送图片最终失败，已达到最大重试次数")

def find_latest_image(target_name: str, current_dir: str) -> str:
    """查找最近的历史图片"""
    history_dir = os.path.join(os.getcwd(), '.history')
    print(f"查找历史图片目录: {history_dir}")
    
    if not os.path.exists(history_dir):
        print(f"历史目录不存在: {history_dir}")
        return None
        
    # 获取所有历史目录，按时间排序
    dirs = sorted([d for d in os.listdir(history_dir) if os.path.isdir(os.path.join(history_dir, d))])
    print(f"找到的历史目录: {dirs}")
    
    # 排除当前目录
    current_dirname = os.path.basename(current_dir)
    dirs = [d for d in dirs if d < current_dirname]
    print(f"排除当前目录后的历史目录: {dirs}")
    
    if not dirs:
        print(f"没有找到可用的历史目录")
        return None
        
    # 在最近的目录中查找目标图片
    latest_dir = os.path.join(history_dir, dirs[-1])
    target_image = os.path.join(latest_dir, f'{target_name}_iframe.png')
    print(f"尝试查找历史图片: {target_image}")
    
    exists = os.path.exists(target_image)
    print(f"历史图片{'存在' if exists else '不存在'}: {target_image}")
    
    return target_image if exists else None

def compare_images_sift(img1_path: str, img2_path: str) -> float:
    """使用 SIFT 比较两张图片的相似度"""
    # 读取图片
    img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
    
    if img1 is None or img2 is None:
        raise ValueError("无法读取图片，请检查图片路径是否正确")

    # 创建 SIFT 特征检测器
    sift = cv2.SIFT_create()

    # 检测关键点和计算描述子
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    # 使用 FLANN 进行特征匹配
    index_params = dict(algorithm=1, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    
    matches = flann.knnMatch(des1, des2, k=2)

    # 过滤匹配点
    good_matches = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good_matches.append(m)

    # 计算相似度得分
    similarity = len(good_matches) / max(len(kp1), len(kp2))
    return similarity

def combine_images(images_data: list, titles: list = None) -> str:
    """
    将多张图片垂直合并成一张图片，并返回base64编码
    images_data: 图片数据列表，每个元素可以是PIL Image对象或base64字符串
    titles: 图片标题列表，如果提供则会在每张图片上方添加标题
    """
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
    """截图主函数，包含重试逻辑，并将结果存储在results字典中"""
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
                
                # 如果有iframe截图且不是wltiframe，保存并进行比较
                if iframe_b64_wx and target_name != 'wltiframe':
                    print(f"保存 iframe 截图: {target_name}")
                    iframe_screenshot_path = os.path.join(backup_dir, f'{target_name}_iframe.png')
                    with open(iframe_screenshot_path, 'wb') as f:
                        f.write(base64.b64decode(iframe_b64_wx))
                    
                    # 查找最近的历史图片进行比较
                    latest_image = find_latest_image(target_name, backup_dir)
                    if latest_image:
                        try:
                            print(f"开始比较图片: {target_name}")
                            similarity = compare_images_sift(latest_image, iframe_screenshot_path)
                            print(f"图片比较完成，相似度: {similarity:.2f}")
                            
                            # 存储比对结果
                            results[target_name]['similarity'] = similarity
                            
                        except Exception as e:
                            print(f"图片比较失败: {str(e)}")
                            print(f"Error type: {type(e).__name__}")
                            print(f"Error details: {e.args}")
                    else:
                        print(f"未找到历史图片用于比较: {target_name}")
                
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
            return  # 发送成功，退出重试
            
        except requests.exceptions.RequestException as e:
            print(f"第 {attempt + 1} 次发送消息失败: {str(e)}")
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                print(f"发送消息最终失败，已达到最大重试次数")

# 主执行流程修改
results = {}  # 存储所有结果
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
            display_name = NAME_MAPPINGS.get(target_name, target_name)  # 获取映射名称
            summary_message += f"\n{display_name}:\n"
            summary_message += f"- 加载耗时: {result['load_time']:.2f}秒\n"
            # 只为非wltiframe目标添加相似度信息
            if target_name != 'wltiframe' and 'similarity' in result:
                similarity = result['similarity']
                summary_message += f"- 相似度: {similarity:.2f}"
                if similarity < 0.7:
                    summary_message += " ⚠️ 检测到重大变化！"
                summary_message += "\n"
        
        # 发送合并后的图片和汇总消息到1183群
        DinghatSendImg(combined_b64_ding, "1183")
        send_message_to_dingding(summary_message, "1183")
        
        # 检查是否有需要告警的情况（排除wltiframe）
        alert_needed = any(
            target_name != 'wltiframe' and 
            'similarity' in result and 
            result['similarity'] < 0.7 
            for target_name, result in results.items()
        )
        
        if alert_needed:
            # 发送告警消息和图片到1098群
            DinghatSendImg(combined_b64_ding, "1098")
            alert_message = "⚠️ 警告：检测到以下页面发生重大变化：\n"
            for target_name, result in results.items():
                if target_name != 'wltiframe' and 'similarity' in result and result['similarity'] < 0.7:
                    display_name = NAME_MAPPINGS.get(target_name, target_name)  # 获取映射名称
                    alert_message += f"\n{display_name}:\n"
                    alert_message += f"- ✅相似度: {result['similarity']:.2f}\n"
                    alert_message += f"- 加载耗时: {result['load_time']:.2f}秒\n"
            
            send_message_to_dingding(alert_message, "1098")

driver.quit()

# def print_hi(name):
#     # Use a breakpoint in the code line below to debug your script.
#     print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.
#
#
# # Press the green button in the gutter to run the script.
# if __name__ == '__main__':
#     print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
