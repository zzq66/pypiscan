import argparse
import _main
def main():
    # 创建命令行解析器
    parser = argparse.ArgumentParser(description='本工具用于pypi的库安全检测')

    # 添加命令行参数
    parser.add_argument('-s', '--static_analyse', type=str, help='静态安全检测,输入具体要分析的数据包名，或者本地的数据包路径。')
    parser.add_argument('-d', '--dynamic_analyse', type=str, help='动态安全检测,输入具体要分析的数据包名，或者本地的数据包路径。')
    parser.add_argument('-t', '--typo_analyse', type=str, help='typo攻击安全检测,输入具体要分析的数据包名')
    parser.add_argument('-m', '--meta_analyse', type=str, help='meta攻击安全检测,输入具体要分析的数据包名')
    parser.add_argument('-v', '--version_analyse', type=str, help='版本差异分析安全检测,输入具体要分析的数据包名')
    parser.add_argument('-x', '--all_analyse', type=str, help='全面智能化安全检测,输入具体要分析的数据包名')
    
    #parser.add_argument('positional_arg', type=str, help='位置参数的描述')
    parser.add_argument('--flag', action='store_true', help='开关标志')

    # 解析命令行参数
    args = parser.parse_args()

    # 处理命令行参数并执行相应的操作
    if args.flag:
        print('开关标志已启用')
    
    if args.static_analyse:
        _main.__static_analyse(args.static_analyse)
    if args.typo_analyse:
        _main.__typo_analyse(args.typo_analyse)
    if args.meta_analyse:
        _main.__meta_analyse(args.meta_analyse)
    if args.version_analyse:
        _main.__version_analyse(args.version_analyse)
    if args.dynamic_analyse:
        _main.__dynamic_analyse(args.dynamic_analyse)
    
    #print(f'位置参数的值为: {args.positional_arg}')

if __name__ == '__main__':
    main()
