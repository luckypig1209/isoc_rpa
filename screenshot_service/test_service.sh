#!/bin/bash

# 截图服务测试脚本
SERVICE_URL="http://localhost:25000"

echo "=========================================="
echo "截图服务测试脚本"
echo "=========================================="
echo ""

# 1. 健康检查
echo "1. 健康检查..."
curl -s "${SERVICE_URL}/health" | jq .
echo ""
echo "----------------------------------------"
echo ""

# 2. 测试 GET 方式
echo "2. 测试 GET 方式截图 (www.baidu.com)..."
RESPONSE=$(curl -s "${SERVICE_URL}/screenshot?url=www.baidu.com&wait_time=10")
SUCCESS=$(echo $RESPONSE | jq -r '.success')
if [ "$SUCCESS" = "true" ]; then
    echo "✅ 截图成功"
    BASE64=$(echo $RESPONSE | jq -r '.base64')
    echo $BASE64 | base64 -d > test_baidu_get.png
    echo "📸 图片已保存为: test_baidu_get.png"
else
    echo "❌ 截图失败: $(echo $RESPONSE | jq -r '.message')"
fi
echo ""
echo "----------------------------------------"
echo ""

# 3. 测试 POST 方式
echo "3. 测试 POST 方式截图 (www.baidu.com)..."
RESPONSE=$(curl -s -X POST "${SERVICE_URL}/screenshot" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "www.baidu.com",
    "wait_time": 10,
    "width": 1920,
    "height": 1080
  }')
SUCCESS=$(echo $RESPONSE | jq -r '.success')
if [ "$SUCCESS" = "true" ]; then
    echo "✅ 截图成功"
    BASE64=$(echo $RESPONSE | jq -r '.base64')
    echo $BASE64 | base64 -d > test_baidu_post.png
    echo "📸 图片已保存为: test_baidu_post.png"
else
    echo "❌ 截图失败: $(echo $RESPONSE | jq -r '.message')"
fi
echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="

