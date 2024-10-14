需要python3.10以上
需要安装semgrep

Usage：
    使用python cli.py -s target  表示对目标进行静态安全检测，当target为本地路径时，会进行本地检测，若target为一个包名称，则会先从pypi远端爬取该包文件
    使用python cli.py -d   表示对目标进行动态安全检测(最好在沙箱中或者虚拟机中进行)
    使用python cli.py -t   表示对目标进行typo安全检测
    使用python cli.py -m   表示对目标进行meta安全分析
    使用python cli.py -f   表示对目标版本差异安全分析

