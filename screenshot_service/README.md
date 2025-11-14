# 网页截图服务

一个基于 FastAPI 和 Selenium 的网页截图微服务，支持通过 REST API 对任意 URL 进行截图并返回 base64 编码的图片。

## 功能特性

- ✅ 支持 GET 和 POST 两种请求方式
- ✅ 自动处理 URL（自动添加 https:// 协议）
- ✅ 支持自定义等待时间、窗口大小
- ✅ 自动处理 iframe 加载
- ✅ 返回 base64 编码的 PNG 图片
- ✅ 健康检查接口
- ✅ Docker 容器化部署

## 快速开始

### 1. 构建 Docker 镜像

```bash
cd screenshot_service
docker build -t screenshot-service:latest .
```

### 2. 运行容器

```bash
docker run -d \
  --name screenshot-service \
  -p 25000:5000 \
  --restart unless-stopped \
  screenshot-service:latest
```

### 3. 测试服务

#### 健康检查
```bash
curl http://localhost:25000/health
```

#### 通过 GET 方式截图
```bash
# 基本用法
curl "http://localhost:25000/screenshot?url=www.baidu.com"

# 带参数
curl "http://localhost:25000/screenshot?url=www.baidu.com&wait_time=30&width=1920&height=1080"
```

#### 通过 POST 方式截图
```bash
curl -X POST "http://localhost:25000/screenshot" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "www.baidu.com",
    "wait_time": 30,
    "width": 1920,
    "height": 1080
  }'
```

## API 文档

### 根路径
- **URL**: `/`
- **方法**: `GET`
- **说明**: 返回服务信息和可用端点

### 健康检查
- **URL**: `/health`
- **方法**: `GET`
- **响应**: 
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123
}
```

### 截图接口（GET）
- **URL**: `/screenshot`
- **方法**: `GET`
- **参数**:
  - `url` (必需): 要截图的URL地址
  - `wait_time` (可选): 等待时间（秒），默认30，范围1-300
  - `width` (可选): 窗口宽度，默认1920，范围100-3840
  - `height` (可选): 窗口高度，默认1080，范围100-2160

**示例**:
```bash
curl "http://localhost:25000/screenshot?url=www.baidu.com&wait_time=30"
```

### 截图接口（POST）
- **URL**: `/screenshot`
- **方法**: `POST`
- **Content-Type**: `application/json`
- **请求体**:
```json
{
  "url": "www.baidu.com",
  "wait_time": 30,
  "width": 1920,
  "height": 1080
}
```

**响应**:
```json
{
  "success": true,
  "base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "message": "Screenshot captured successfully"
}
```

## 使用示例

### Python 示例

```python
import requests
import base64
from PIL import Image
import io

# 调用截图服务
response = requests.post(
    "http://localhost:25000/screenshot",
    json={
        "url": "www.baidu.com",
        "wait_time": 30
    }
)

result = response.json()
if result['success']:
    # 解码base64图片
    img_data = base64.b64decode(result['base64'])
    img = Image.open(io.BytesIO(img_data))
    
    # 保存图片
    img.save('screenshot.png')
    print("截图已保存")
else:
    print(f"截图失败: {result['message']}")
```

### Shell 脚本示例

```bash
#!/bin/bash

# 调用截图服务
RESPONSE=$(curl -s -X POST "http://localhost:25000/screenshot" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"www.baidu.com\", \"wait_time\": 30}")

# 提取base64数据
BASE64=$(echo $RESPONSE | jq -r '.base64')

# 保存为图片
echo $BASE64 | base64 -d > screenshot.png
```

## Docker Compose 部署

创建 `docker-compose.yml`:

```yaml
version: '3'
services:
  screenshot-service:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "25000:5000"
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
```

运行:
```bash
docker-compose up -d
```

## 开发模式

### 本地运行（需要安装 Chrome/Chromium）

```bash
# 安装依赖
pip install -r requirements.txt

# 运行服务
python app.py
# 或
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

### 访问 API 文档

服务启动后，访问：
- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

## 注意事项

1. **URL 格式**: 如果 URL 不包含协议（http:// 或 https://），服务会自动添加 https://
2. **等待时间**: 建议根据目标网站的加载速度设置合适的 `wait_time`
3. **窗口大小**: 默认 1920x1080，可根据需要调整
4. **资源限制**: 建议在 Docker 中设置适当的内存限制（至少 512MB）

## 故障排除

### 容器无法启动
- 检查端口是否被占用
- 查看容器日志: `docker logs screenshot-service`

### 截图失败
- 检查 URL 是否可访问
- 增加 `wait_time` 参数
- 查看服务日志获取详细错误信息

### 中文显示问题
- 确保 Dockerfile 中已安装中文字体
- 检查环境变量 `LANG=zh_CN.UTF-8`

## 技术栈

- **FastAPI**: 现代、快速的 Web 框架
- **Selenium**: 浏览器自动化
- **Chromium**: 无头浏览器
- **Python 3.9**: 运行环境

## 许可证

MIT

