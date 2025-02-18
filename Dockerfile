# 使用 Python 3.9 镜像
FROM python:3.9

ENV http_proxy=http://10.123.26.113:7890
ENV https_proxy=http://10.123.26.113:7890
ENV all_proxy=socks5://10.123.26.113:7890


# 设置工作目录
WORKDIR /app

# 设置时区为中国时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 使用国内镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装必要的系统依赖
RUN apt-get update -y && apt-get install -y \
    wget \
    gnupg2 \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    chromium \
    chromium-driver \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
COPY main.py .
COPY config.test.yaml .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建历史记录目录并设置权限
RUN mkdir -p .history && chmod 777 .history

# 设置非root用户
RUN useradd -m -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# 设置健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ps aux | grep python | grep main.py || exit 1

# 运行脚本
CMD ["python", "main.py"]
