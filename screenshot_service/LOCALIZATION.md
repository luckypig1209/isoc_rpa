# 完全本地化说明

## 概述

本项目已实现完全本地化的 Swagger UI 和 ReDoc 文档，不依赖任何外部 CDN，可以在完全离线的内网环境中使用。

## 本地化内容

### 静态文件

所有 Swagger UI 和 ReDoc 的静态资源都已下载到本地：

```
static/
├── swagger-ui/
│   ├── swagger-ui-bundle.min.js    # Swagger UI JavaScript (1.3MB)
│   ├── swagger-ui.min.css          # Swagger UI CSS (149KB)
│   ├── favicon-32x32.png           # 图标
│   └── favicon-16x16.png           # 图标
└── redoc/
    └── redoc.standalone.js         # ReDoc JavaScript (850KB)
```

### 下载静态文件

如果静态文件不存在，运行以下命令下载：

```bash
cd screenshot_service
./download_static_files.sh
```

或者手动下载：

```bash
mkdir -p static/swagger-ui static/redoc

# Swagger UI
wget https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.3/swagger-ui-bundle.min.js -O static/swagger-ui/swagger-ui-bundle.min.js
wget https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.3/swagger-ui.min.css -O static/swagger-ui/swagger-ui.min.css
wget https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.3/favicon-32x32.png -O static/swagger-ui/favicon-32x32.png
wget https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.3/favicon-16x16.png -O static/swagger-ui/favicon-16x16.png

# ReDoc
wget https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js -O static/redoc/redoc.standalone.js
```

## 代码实现

### app.py 中的关键配置

1. **挂载静态文件目录**：
```python
app.mount("/static", StaticFiles(directory="static"), name="static")
```

2. **自定义 Swagger UI 路由**：
```python
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        ...
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.min.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.min.css",
        swagger_favicon_url="/static/swagger-ui/favicon-32x32.png",
    )
```

3. **自定义 ReDoc 路由**：
```python
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        ...
        redoc_js_url="/static/redoc/redoc.standalone.js",
        redoc_favicon_url="/static/swagger-ui/favicon-32x32.png",
    )
```

## Docker 构建

静态文件会自动包含在 Docker 镜像中：

```dockerfile
# 复制应用文件和静态资源
COPY app.py .
COPY static ./static
```

## 优势

✅ **完全离线可用**：不依赖任何外部 CDN  
✅ **内网环境友好**：适合企业内网部署  
✅ **加载速度快**：本地文件加载更快  
✅ **安全性高**：不向外部发送请求  
✅ **稳定性好**：不受 CDN 服务影响  

## 验证

构建并运行后，访问：

- Swagger UI: http://your-server:25000/docs
- ReDoc: http://your-server:25000/redoc

打开浏览器开发者工具（F12），检查 Network 标签页，应该看到所有资源都从 `/static/` 路径加载，而不是外部 CDN。

## 更新静态文件

如果需要更新 Swagger UI 或 ReDoc 版本：

1. 修改 `download_static_files.sh` 中的版本号
2. 运行脚本重新下载
3. 重新构建 Docker 镜像

## 注意事项

- 静态文件总大小约 2.3MB，会增加镜像体积
- 如果不需要文档功能，可以删除 `static/` 目录和相关的路由代码
- 静态文件已包含在 `.dockerignore` 的注释中，确保会被复制到镜像

