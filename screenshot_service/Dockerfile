# 使用官方Python镜像
FROM python:3.11-slim

# 可选代理参数（构建时传入）
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG ALL_PROXY

# 设置工作目录
WORKDIR /app

# 设置时区为中国时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


# 安装 Google Chrome 及必要依赖（让 apt 解析正确的 t64 依赖）
RUN set -eux; \
    if [ -n "$HTTP_PROXY" ]; then \
      echo "Acquire::http::Proxy \"${HTTP_PROXY}\";" > /etc/apt/apt.conf.d/proxy.conf; \
    fi; \
    if [ -n "$HTTPS_PROXY" ]; then \
      echo "Acquire::https::Proxy \"${HTTPS_PROXY}\";" >> /etc/apt/apt.conf.d/proxy.conf; \
    fi; \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    # 字体（中文）
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fonts-liberation \
    locales \
    # 便利工具
    curl && \
    # 安装 Google Chrome（使用官方源，新方式添加 GPG 密钥）
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-chrome-stable && \
    apt-get clean && \
    rm -f /etc/apt/apt.conf.d/proxy.conf && \
    rm -rf /var/lib/apt/lists/*

# 生成中文语言环境
RUN sed -i '/zh_CN.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=zh_CN.UTF-8 LANGUAGE=zh_CN:zh LC_ALL=zh_CN.UTF-8

# 设置环境变量
ENV CHROME_BIN=/usr/bin/google-chrome \
    CHROMIUM_PATH=/usr/bin/google-chrome \
    CHROMEDRIVER_PATH=/usr/local/bin/chromedriver \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    LANG=zh_CN.UTF-8 \
    LANGUAGE=zh_CN:zh \
    LC_ALL=zh_CN.UTF-8

# 安装匹配 Google Chrome 的 ChromeDriver
# 1) 优先尝试 Chrome for Testing 的文件；2) 回退到传统 chromedriver 仓库
RUN set -eux; \
    # 配置 wget 使用代理（如果提供了代理参数）
    if [ -n "$HTTP_PROXY" ] || [ -n "$HTTPS_PROXY" ]; then \
        if [ -n "$HTTP_PROXY" ]; then export http_proxy="$HTTP_PROXY"; export HTTP_PROXY="$HTTP_PROXY"; fi; \
        if [ -n "$HTTPS_PROXY" ]; then export https_proxy="$HTTPS_PROXY"; export HTTPS_PROXY="$HTTPS_PROXY"; fi; \
    fi; \
    # 获取 Chrome 版本（直接使用路径，不依赖环境变量）
    CHROME_VERSION=$(/usr/bin/google-chrome --version | awk '{print $3}') && \
    CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1) && \
    echo "Detected Chrome version: $CHROME_VERSION (major: $CHROME_MAJOR_VERSION)" && \
    FETCHED=0; \
    URL1="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip"; \
    URL2_MAJOR=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}" 2>/dev/null || echo "") && \
    if wget -q --spider "$URL1" 2>/dev/null; then \
        echo "Downloading ChromeDriver from Chrome for Testing..." && \
        wget -q "$URL1" -O /tmp/chromedriver.zip && FETCHED=1; \
    elif [ -n "$URL2_MAJOR" ]; then \
        echo "Downloading ChromeDriver from legacy repository..." && \
        wget -q "https://chromedriver.storage.googleapis.com/${URL2_MAJOR}/chromedriver_linux64.zip" -O /tmp/chromedriver.zip && FETCHED=1; \
    fi; \
    if [ "$FETCHED" -ne 1 ]; then \
        echo "ERROR: Failed to fetch matching chromedriver for Chrome $CHROME_VERSION" && \
        echo "Tried URLs:" && \
        echo "  - $URL1" && \
        echo "  - https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}" && \
        exit 1; \
    fi; \
    unzip -q /tmp/chromedriver.zip -d /tmp && \
    if [ -d /tmp/chromedriver-linux64 ]; then \
        mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/; \
    else \
        mv /tmp/chromedriver /usr/local/bin/; \
    fi && \
    chmod +x /usr/local/bin/chromedriver && \
    /usr/local/bin/chromedriver --version && \
    rm -rf /tmp/chromedriver* /tmp/__MACOSX

# 复制并安装Python依赖（使用阿里云PyPI镜像）
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 复制应用文件和静态资源（Swagger UI 和 ReDoc）
COPY app.py .
COPY static ./static

# 设置非root用户（在复制文件之后，确保权限正确）
RUN useradd -m -s /bin/bash appuser \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app
USER appuser

# 暴露端口
EXPOSE 5000

# 运行FastAPI应用
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]

