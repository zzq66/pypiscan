
import static_analyse
import scraper
import dynamic_exec
import typo_analyse
import Meta_analyse
import integrity_check
import version_diff_analyse
import Feature_recognition


# 定义颜色转义序列
class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'  # 重置颜色

# 使用颜色输出文本
#print(f"{Color.OKGREEN}这是绿色的文本{Color.ENDC}")
#print(f"{Color.FAIL}这是红色的文本{Color.ENDC}")


def __static_analyse(target:str):
    if target.startswith('/'):
        issues,answer = static_analyse.static_analyse(target)
        print(f'there is {issues} malicious position')
        print('--------------------------')
        for item in answer:
            for i in answer[item]:
                print(f'{Color.FAIL}'+item +f'{Color.ENDC}  location: '+i['location'])
            print('--------------------------')
    else:
        try:
            path = scraper.download_newest_and_unzip(target)
            issues,answer = static_analyse.static_analyse(path)
            print(f'there is {issues} malicious position')
            print('--------------------------')
            for item in answer:
                for i in answer[item]:
                    print(f'{Color.FAIL}'+item +f'{Color.ENDC}  location: '+i['location'])
                print('--------------------------')
        except:
            print('网络出错，下载并解压失败，可以考虑手动解压到本地')
      
            
def __dynamic_analyse(target:str):
    if target.startswith('/'):
        answer = dynamic_exec.dynamic_exec(local_path=target)
    else:
        answer = dynamic_exec.dynamic_exec(local_path=target)
    print('执行日志在： '+answer)
    
    
def __typo_analyse(name):
    print('正在进行typo扫描单个数据包是否存在恶意typo攻击行为')
    answer = typo_analyse.single_package_typo_detect(name)
    top_package = scraper.get_top_package_name()
    print('扫描结果如下:（ps:标红代表目前非常流行的数据包,可疑度极高')
    print('--------------------------')
    for ans in answer:
        if ans in top_package:
            print(f"{Color.FAIL}{ans} {Color.ENDC}",end=' ')
    for ans in answer:
        if not ans in top_package:
            print(f"{ans}",end=' ')
    print('\n--------------------------')
    

def __meta_analyse(name):
    issues = 0
    answer = []
    print('start')
    meta = scraper.get_meta_data(name)
    path = scraper.download_newest_and_unzip(name)
    print("正在分析包Meta信息是否存在异常")
    tmp_bool,tmp_answer=Meta_analyse.short_information(meta)
    issues += int(tmp_bool)
    if tmp_bool:
        answer.append(tmp_answer)
        
    tmp_bool,tmp_answer=Meta_analyse.low_version(meta)
    issues += int(tmp_bool)
    if tmp_bool:
        answer.append(tmp_answer)
        
    tmp_bool,tmp_answer=Meta_analyse.potential_compromised_email(meta)
    issues += int(tmp_bool)
    if tmp_bool:
        answer.append(tmp_answer)
        
    tmp_bool,tmp_answer = Meta_analyse.few_files(path)
    issues += int(tmp_bool)
    if tmp_bool:
        answer.append(tmp_answer)
    
    maintainer_upload_times = scraper.get_maintainer_upload_time(name)
    tmp_bool,tmp_answer = Meta_analyse.author_analyse(maintainer_upload_times)
    issues += int(tmp_bool)
    if tmp_bool:
        answer.append(tmp_answer)
    print(f'一共有'+str(issues)+'个问题')
    for i in answer:
        print(f"{Color.FAIL}"+i+f"{Color.ENDC}")
    # 可以增加 integrity_check 


def __version_analyse(name):
    path_new = scraper.download_newest_and_unzip(name)
    path_second = scraper.download_second_newest_and_unzip(name)
    version_diff_code_file_name = version_diff_analyse.version_diff(path_new,path_second)
    tmpbool,answer = Feature_recognition.Check(version_diff_code_file_name)
    if tmpbool :
        for i in answer:
            print(i)
    else:
        print(answer)
        

