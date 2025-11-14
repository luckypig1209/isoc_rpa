#!/bin/bash

# 下载 Swagger UI 和 ReDoc 静态文件到本地

STATIC_DIR="static"
SWAGGER_DIR="$STATIC_DIR/swagger-ui"
REDOC_DIR="$STATIC_DIR/redoc"

mkdir -p $SWAGGER_DIR
mkdir -p $REDOC_DIR

echo "正在下载 Swagger UI 静态文件..."

# Swagger UI 5.10.3
wget -q https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.3/swagger-ui-bundle.min.js -O $SWAGGER_DIR/swagger-ui-bundle.min.js
wget -q https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.3/swagger-ui.min.css -O $SWAGGER_DIR/swagger-ui.min.css
wget -q https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.3/favicon-32x32.png -O $SWAGGER_DIR/favicon-32x32.png
wget -q https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.3/favicon-16x16.png -O $SWAGGER_DIR/favicon-16x16.png

# ReDoc 2.1.3
echo "正在下载 ReDoc 静态文件..."
wget -q https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js -O $REDOC_DIR/redoc.standalone.js

echo "下载完成！"
echo "文件位置："
ls -lh $SWAGGER_DIR/
ls -lh $REDOC_DIR/

