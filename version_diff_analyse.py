import difflib
import os
from datetime import datetime
import re
from Feature_recognition import Check


def read_one_file(f1):
    with open(f1,'r') as file1:
        new_lines = file1.readlines()
    return new_lines


def diff_two_files(f1,f2):
    # 读取两个文件的内容
    try:
        with open(f1, 'r',encoding='utf8') as file1, open(f2, 'r',encoding='utf8') as file2:
            lines1 = file1.readlines()
            lines2 = file2.readlines()
    except:
        return []
    # 使用 difflib.Differ 来比较两个文件的内容差异
    differ = difflib.Differ()
    diff_result = list(differ.compare(lines2, lines1))
    new_lines=[]
    for line in diff_result:
        if line[0]=='+':
            new_lines.append(line[2:])
    return new_lines


def has_only_one_folder(directory):
    items = os.listdir(directory)
    # 过滤掉以点开头的隐藏文件/文件夹
    visible_items = [item for item in items if not item.startswith('.')]
    if len(visible_items) == 1 and os.path.isdir(os.path.join(directory, visible_items[0])):
        return True , os.path.join(directory, visible_items[0])
    else:
        return False , ''


def remove_comments(content):
    # 去除单行注释
    content = ''.join(content)
    content = re.sub(r'#.*', '', content)
    # 去除多行注释
    content = re.sub(r"'''(.*?)'''", '', content, flags=re.DOTALL)
    content = re.sub(r'"""(.*?)"""', '', content, flags=re.DOTALL)
    return content

  
def version_diff(folder1,folder2):
    #folder1是最新版本的根目录，folder2是次新版本的根目录
    for i in range(10):
        T,Fol = has_only_one_folder(folder1)
        if T:
            folder1 = Fol
            continue
        break
    for i in range(10):
        T,Fol = has_only_one_folder(folder2)
        if T:
            folder2 = Fol
            continue
        break      
    folder1_files=[]
    for foldername, subfolders, filenames in os.walk(folder1):
        for filename in filenames:
            relative_root = os.path.relpath(foldername, folder1)
            file_path = os.path.join(relative_root, filename)
            folder1_files.append(file_path)
            #print("relative File path:", file_path)
    folder2_files=[]
    for foldername, subfolders, filenames in os.walk(folder2):
        for filename in filenames:
            relative_root = os.path.relpath(foldername, folder2)
            file_path = os.path.join(relative_root, filename)
            folder2_files.append(file_path)
            #print("relative File path:", file_path) 
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    version_diff_code_file_name = './tmp/'+time_str+'_version_diff_code.py'
    version_diff_code_file = open(version_diff_code_file_name, 'w')
    version_diff_code =[]
    for file in folder1_files:
        if file.endswith(".py"):
            if file in folder2_files: #上一个版本也存在，那么就比较一下查看新增加的代码加入待检
                f1_real_path = os.path.join(folder1,file)
                f2_real_path = os.path.join(folder2,file)
                new_code = diff_two_files(f1_real_path,f2_real_path)
                if new_code!=[]:
                    #print(file)
                    version_diff_code.append(''.join(new_code))
                    version_diff_code.append('\n')
            elif file not in folder2_files and 'test' not in file:#如果上一个版本不存在，并且不是测试相关代码，全代码加入待检
                f1_real_path = os.path.join(folder1,file)
                with open(f1_real_path) as f:
                    all_code =''.join(f.readlines())
                    version_diff_code.append(all_code)
                    version_diff_code.append('\n')
    remove_comments(version_diff_code)
    version_diff_code_file.write(''.join(version_diff_code))                
    version_diff_code_file.close()  
    return version_diff_code_file_name 
   

def github_diff(folder1,folder2):
    #folder1是待测根目录，folder2github根目录
    for i in range(10):
        T,Fol = has_only_one_folder(folder1)
        if T:
            folder1 = Fol
            continue
        break
    for i in range(10):
        T,Fol = has_only_one_folder(folder2)
        if T:
            folder2 = Fol
            continue
        break      
    folder1_files={}
    for foldername, subfolders, filenames in os.walk(folder1):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            relative_root = os.path.relpath(foldername, folder1)
            file_path = os.path.join(relative_root, filename)
            folder1_files[filename]=file_path
            #print("relative File path:", file_path)
    folder2_files={}
    for foldername, subfolders, filenames in os.walk(folder2):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            relative_root = os.path.relpath(foldername, folder2)
            file_path = os.path.join(relative_root, filename)
            folder2_files[filename]=file_path
            #print("relative File path:", file_path) 
    now = datetime.now()
    time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    version_diff_code_file_name = './tmp/'+time_str+'_version_diff_code.py'
    version_diff_code_file = open(version_diff_code_file_name, 'w')
    version_diff_code =[]
    for file in folder1_files:
        if file.endswith(".py"):
            if file in folder2_files and 'test' not in file: #上一个版本也存在，那么就比较一下查看新增加的代码加入待检
                f1_real_path = os.path.join(folder1,folder1_files[file])
                f2_real_path = os.path.join(folder2,folder2_files[file])
                new_code = diff_two_files(f1_real_path,f2_real_path)
                if new_code!=[]:
                    print(file)
                    print(new_code)
                    version_diff_code.append(''.join(new_code))
                    version_diff_code.append('\n')
            elif file not in folder2_files and 'test' not in file:#如果上一个版本不存在，并且不是测试相关代码，全代码加入待检
                print(file)
                f1_real_path = os.path.join(folder1,folder1_files[file])
                with open(f1_real_path) as f:
                    all_code =''.join(f.readlines())
                    version_diff_code.append(all_code)
                    version_diff_code.append('\n')
    remove_comments(version_diff_code) 
    version_diff_code_file.write(''.join(version_diff_code))                
    version_diff_code_file.close()
    if version_diff_code != []:
        return version_diff_code_file_name     
    return ''    

def version_diff_str(folder1,folder2):
    #folder1是最新版本的根目录，folder2是次新版本的根目录
    for i in range(10):
        T,Fol = has_only_one_folder(folder1)
        if T:
            folder1 = Fol
            continue
        break
    for i in range(10):
        T,Fol = has_only_one_folder(folder2)
        if T:
            folder2 = Fol
            continue
        break      
    folder1_files=[]
    for foldername, subfolders, filenames in os.walk(folder1):
        for filename in filenames:
            relative_root = os.path.relpath(foldername, folder1)
            file_path = os.path.join(relative_root, filename)
            folder1_files.append(file_path)
            #print("relative File path:", file_path)
    folder2_files=[]
    for foldername, subfolders, filenames in os.walk(folder2):
        for filename in filenames:
            relative_root = os.path.relpath(foldername, folder2)
            file_path = os.path.join(relative_root, filename)
            folder2_files.append(file_path)
            #print("relative File path:", file_path) 
    version_diff_code =[]
    for file in folder1_files:
        if file.endswith(".py"):
            if file in folder2_files: #上一个版本也存在，那么就比较一下查看新增加的代码加入待检
                f1_real_path = os.path.join(folder1,file)
                f2_real_path = os.path.join(folder2,file)
                new_code = diff_two_files(f1_real_path,f2_real_path)
                if new_code!=[]:
                    #print(file)
                    version_diff_code.append(''.join(new_code))
                    version_diff_code.append('\n')
            elif file not in folder2_files and 'test' not in file:#如果上一个版本不存在，并且不是测试相关代码，全代码加入待检
                f1_real_path = os.path.join(folder1,file)
                with open(f1_real_path) as f:
                    all_code =''.join(f.readlines())
                    version_diff_code.append(all_code)
                    version_diff_code.append('\n')
    remove_comments(version_diff_code)
    answer = '\n'.join(version_diff_code)
    return answer 



# # version_diff_code_file_name = version_diff('/Users/zhaozhouqiao/Desktop/poisoning_project/my_project/tmp/2023-08-30_20-50-14','/Users/zhaozhouqiao/Desktop/poisoning_project/my_project/tmp/2023-08-30_20-42-15')
# # with open(version_diff_code_file_name,'r') as fr:
# #     file_str = fr.read()
# #diff_two_files("/Users/zhaozhouqiao/Desktop/1.py","/Users/zhaozhouqiao/Desktop/2.py")
# file_list = os.listdir('/Users/zhaozhouqiao/Desktop/poisoning_project/my_project/evil_test/')
# first = ''
# first_name = ''
# second = ''
# second_name = ''


# import csv
# csv_file = open('./version.csv', 'a+')
#     # 创建CSV阅读器
# csv_writer = csv.writer(csv_file)
# flag = 0
# for file in sorted(file_list):
#     if file=='pipstyle-0.1.3.tar.gz':
#         flag = 1
#     if flag ==0:
#         continue
#     second = file
#     second_name  =second.split('-')[0]
#     if second_name == first_name:
#         file_str = version_diff_str('/Users/zhaozhouqiao/Desktop/poisoning_project/my_project/evil_test/'+second,'/Users/zhaozhouqiao/Desktop/poisoning_project/my_project/evil_test/'+first)
#         tmybool,answer = Check(str(file_str))
#         csv_writer.writerow([str(second),str(tmybool),str(' '.join(answer))])
#     first = second
#     first_name = second_name
# csv_file.close()       
# #print(sorted(file_list))