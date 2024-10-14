import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import tarsafe
import zipfile
import sys
import warnings
import re
import tarfile
from bs4 import BeautifulSoup
warnings.simplefilter("ignore")


def get_all_pypi_names():
    page = "https://pypi.org/simple/"
    try:
        pypi_raw_page = requests.get(page, verify=False)  # 可以禁用 SSL 验证
        soup = BeautifulSoup(pypi_raw_page.content, "html.parser")
        links = soup.find_all("a")
        package_names = []
        for link in links:
            package_names.append(link.get_text())
        package_names.sort()
        return package_names
    except requests.exceptions.ConnectionError:
        print("网络连接出现问题，爬取所有包名称失败")
        pass


def get_meta_data(package_name):
    package_meta_url = "https://pypi.org/pypi/" + package_name + "/json"
    try:
        package_meta_json = requests.get(package_meta_url).content
        package_meta_dict = json.loads(package_meta_json)
    except Exception:
        package_meta_dict = {}
    return package_meta_dict


def download_second_newest_and_unzip(package_name):
    package_name = 'requests'
    page_all_version = "https://pypi.org/simple/" + package_name
    try:
        raw_page = requests.get(page_all_version, verify=False)
        soup = BeautifulSoup(raw_page.content, "html.parser")
        links = soup.find_all("a")
        newest_source_code_name = links[-1].get_text()
        pattern = r'-(\d+(\.\d+)*)'
        newest_version_match = re.search(pattern, newest_source_code_name)
        if newest_version_match:
            newest_version = newest_version_match.group(1)
        else:
            print("Version not found in filename")
        links_len = len(links)
        second_newest_url = ''
        for i in range(2,links_len):
            second_newest_source_code_name = links[-i].get_text()
            second_newest_version_match = re.search(pattern, second_newest_source_code_name)
            if second_newest_version_match:
                second_newest_version = second_newest_version_match.group(1)
            else:
                print("second Version not found in filename")
            if second_newest_version != newest_version:
                second_newest_url = links[-i].get("href")
                break
    except Exception:
        print("未成功获取次新包文件下载链接")
        exit(0)
    tz_data = ""
    if second_newest_url == 0:
        print("未成功获取包文件下载链接")
        exit(0)
    else:
        try:
            tz_data = requests.get(second_newest_url).content
        except Exception:
            print("未成功下载代码压缩包")
            exit(0)
    zip_name = "./tmp/" + newest_source_code_name
    with open(zip_name, 'wb') as f:
        f.write(tz_data)
    extract_dir_path = ""
    if zip_name.endswith('.tar.gz') or zip_name.endswith('.tgz') or zip_name.endswith('.tar') or zip_name.endswith('.rar') or zip_name.endswith('.7z'):
        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        extract_dir_path = f"./tmp/{time_str}"
        os.mkdir(extract_dir_path)
        tarsafe.open(zip_name).extractall(extract_dir_path)
    elif zip_name.endswith('.zip') or zip_name.endswith('.whl'):
        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        extract_dir_path = f"./tmp/{time_str}"
        os.mkdir(extract_dir_path)
        with zipfile.ZipFile(zip_name, 'r') as zip_file:
            for file in zip_file.namelist():
                zip_file.extract(file, path=os.path.join(extract_dir_path, file))
    else:
        extract_dir_path = ""
    os.remove(zip_name)
    return extract_dir_path


def download_newest_and_unzip(package_name):
    page_all_version = "https://pypi.org/simple/" + package_name
    try:
        raw_page = requests.get(page_all_version, verify=False)
        soup = BeautifulSoup(raw_page.content, "html.parser")
        links = soup.find_all("a")
        newest_source_code_url = links[-1].get("href")
        newest_source_code_name = links[-1].get_text()
    except Exception:
        print("未成功获取包文件下载链接")
        exit(0)
    tz_data = ""
    if newest_source_code_url == 0:
        print("未成功获取包文件下载链接")
        exit(0)
    else:
        try:
            tz_data = requests.get(newest_source_code_url).content
        except Exception:
            print("未成功下载代码压缩包")
            exit(0)
    zip_name = "./tmp/" + newest_source_code_name
    with open(zip_name, 'wb') as f:
        f.write(tz_data)
    if zip_name.endswith('.tar.gz') or zip_name.endswith('.tgz') or zip_name.endswith('.tar'):
        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        extract_dir_path = f"./tmp/{time_str}"
        os.mkdir(extract_dir_path)
        tarsafe.open(zip_name).extractall(extract_dir_path)
    elif zip_name.endswith('.zip') or zip_name.endswith('.whl'):
        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        extract_dir_path = f"./tmp/{time_str}"
        os.mkdir(extract_dir_path)
        with zipfile.ZipFile(zip_name, 'r') as zip_file:
            zip_file.extractall(extract_dir_path)
    else:
        extract_dir_path = ""
    os.remove(zip_name)
    return extract_dir_path



def get_top_package_name(top_n=50, stored=False, stored_file_name=""):  # 返回的 包名称 顺序 的字典
    if stored:
        with open(stored_file_name) as f:
            data_json = json.load(f)
    else:
        top_n_url = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.json"
        try:
            with requests.get(top_n_url) as raw_page:
                data_json = json.loads(raw_page.content)
        except Exception as e:
            print("获取top n数据包信息失败")
            sys.exit(1)
    top_n_package_no = {}
    for i in range(0, top_n):
        package_name = data_json['rows'][i]['project']
        top_n_package_no[package_name] = i + 1
    return top_n_package_no


def get_maintainer_upload_time(package_name):
    url = 'https://pypi.org/project/'+package_name+ '#history'
    headers = {'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; InfoPath.3)'}
    retries = 0
    flag = 0
    while retries < 5 :
        retries += 1
        try:
            package_homepage = str(requests.get(url,headers=headers,timeout=2).content)
            flag = 1
            print("爬取该包维护者的信息成功")
            break
        except Exception as e:
            pass
    if(flag == 0):
        print("爬取该包维护者的信息失败")
        return 0     #爬取失败嘞。
    #package_homepage = 'href="/user//"  e1e1231'
    link_pattern = r'href="/user/([^\/]+)/"'
    #print(link_pattern)
    names = re.findall(link_pattern, package_homepage, re.IGNORECASE)
    maintainer_upload_times = {}
    for name in names:
        for i in range(0,3):
            try:
                user_page = str(requests.get('https://pypi.org/user/'+name,timeout=2).text)
            #print(user_page.replace('\n',''))
                link_pattern2 = r'Last released <time datetime="([^"]*)\+0000" '
            #print(link_pattern)
                upload_times = re.findall(link_pattern2, user_page, re.IGNORECASE)
                maintainer_upload_times[name] = upload_times
                break
            except:
                pass
    return maintainer_upload_times

