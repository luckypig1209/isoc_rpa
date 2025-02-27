
#目前dev_docker分支中的代码及dockerfile已经支持了docker中无GUI也能完成截图巡检的场景

编写该自动化巡检脚本，主要用于网页截图和页面加载时间的监控，结合 Selenium 和其他一些库来进行页面操作和图像处理。捕获指定网页的截图（包括全页面截图和 iframe 部分截图），并对截图进行比较以检测页面内容的变化，将消息发送到钉钉及微信群内。

依赖中的chromedriver.exe需要拷贝出来，配合机器上的chrome使用。
main.py中，
# options.add_argument("--headless=new")
driver = webdriver.Chrome(service=Service(executable_path="D:\\Programs\\BrowserDrivers\\chromedriver.exe"), options=options)
需要根据实际修改chromedriver.exe的路径。

依赖中，有个miniconda，直接安装，之后配置环境变量，添加3个本地文件目录地址进去，miniconda文件夹位置、miniconda/Library/bin、miniconda/Scripts

miniconda起来后，在conda的环境中，直接执行
pip install -r requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple/
