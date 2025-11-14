# 快速开始指南

## 一、编译 Docker 镜像

```bash
# 进入服务目录
cd screenshot_service

# 构建镜像
docker build -t screenshot-service:latest .
```

**构建时间**: 约 5-10 分钟（首次构建需要下载基础镜像和依赖）

## 二、运行服务

### 方式1: 直接运行 Docker 容器

```bash
docker run -d \
  --name screenshot-service \
  -p 25000:5000 \
  --restart unless-stopped \
  screenshot-service:latest
```

### 方式2: 使用 Docker Compose

```bash
docker-compose up -d
```

## 三、测试服务

### 1. 健康检查
```bash
curl http://localhost:25000/health
```

预期响应:
```json
{"status":"healthy","timestamp":1234567890.123}
```

### 2. 截图测试（GET 方式）
```bash
# 最简单的用法
curl "http://localhost:25000/screenshot?url=www.baidu.com"

# 带完整参数
curl "http://localhost:25000/screenshot?url=www.baidu.com&wait_time=30&width=1920&height=1080"
```

### 3. 截图测试（POST 方式）
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

### 4. 查看返回结果

返回的 JSON 包含 `base64` 字段，可以解码保存为图片：

```bash
# 获取 base64 并保存为图片
curl -X POST "http://localhost:25000/screenshot" \
  -H "Content-Type: application/json" \
  -d '{"url": "www.baidu.com"}' \
  | jq -r '.base64' \
  | base64 -d > screenshot.png
```

## 四、查看日志

```bash
# 查看容器日志
docker logs screenshot-service

# 实时查看日志
docker logs -f screenshot-service
```

## 五、停止和删除

```bash
# 停止容器
docker stop screenshot-service

# 删除容器
docker rm screenshot-service

# 删除镜像（可选）
docker rmi screenshot-service:latest
```

## 六、访问 API 文档

服务启动后，可以通过浏览器访问：

- **Swagger UI**: http://localhost:25000/docs
- **ReDoc**: http://localhost:25000/redoc

## 常见问题

### Q: 端口被占用怎么办？
A: 修改端口映射，例如使用 25001:
```bash
docker run -d -p 25001:5000 --name screenshot-service screenshot-service:latest
```

### Q: 如何修改默认参数？
A: 在请求时传递参数，或修改 `app.py` 中的默认值

### Q: 截图失败怎么办？
A: 
1. 检查 URL 是否可访问
2. 增加 `wait_time` 参数
3. 查看容器日志: `docker logs screenshot-service`

### Q: 如何查看镜像大小？
A: 
```bash
docker images screenshot-service
```

