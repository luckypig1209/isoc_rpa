# 使用官方Python镜像
FROM python:3.9-slim

# 添加构建参数用于代理设置
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG ALL_PROXY

# 设置工作目录
WORKDIR /app

# 设置时区为中国时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 设置apt代理
RUN echo "Acquire::http::Proxy \"${HTTP_PROXY}\";" > /etc/apt/apt.conf.d/proxy.conf && \
    echo "Acquire::https::Proxy \"${HTTPS_PROXY}\";" >> /etc/apt/apt.conf.d/proxy.conf

# 安装必要依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    fonts-liberation \
    libnss3 \
    libglib2.0-0 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libgtk-3-0 \
    libxss1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/apt/apt.conf.d/proxy.conf

# 设置环境变量
ENV CHROME_BIN=/usr/bin/chromium \
    CHROMIUM_PATH=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 复制并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY main.py config.test.yaml ./

# 创建历史记录目录
RUN mkdir -p .history && chmod 777 .history

# 设置非root用户
RUN useradd -m -s /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# 运行脚本
CMD ["/bin/bash"]