import scraper
import whois
from packaging import version
from dateutil import parser
import os
import re
import datetime


def analyse_same_meta_fields(meta1, meta2):
    #判断两个包中是否含有相同的重要的meta字段信息
    fields_to_compare = [
        "author_email",
        "author",
        "package_url",
        "description",
        "home_page",
        "summary",
    ]
    if 'info' in meta1:
        meta1_info = meta1['info']
    else:
        meta1_info = {}
    if 'info' in meta2:
        meta2_info = meta2['info']
    else:
        meta2_info = {}
    same_fields = 0
    for field in fields_to_compare:
        if field in meta1_info and field in meta2_info:
            if meta1_info[field] == meta2_info[field]:
                same_fields = same_fields + 1
    if same_fields >= 1:
        return True, "some fields are same with others，possible someone wants to fake the meta info"
    else:
        return False, "Nothing"


def short_information(meta):    # 检测改包是否为空描述信息 如果是空的 返回true 如果大于5字符，返回false
    if 'info' in meta and 'description' in meta['info']:
        if len(meta['info']["description"]) <= 5:
            return True, "Description is few"
        else:
            return False, "nothing"
    return False, " nothing"


def low_version(meta):
    if 'info' in meta and 'version' in meta['info']:
        if meta['info']['version'] in ['0.0', '0', '0.0.0']:
            return True, "0 version shows up"
    return False, "nothing"


def potential_compromised_email(meta):
    if meta == {}:
        return False, "nothing"
    releases = meta["releases"]
    sorted_versions = sorted(
        releases.keys(), key=lambda r: version.parse(r), reverse=True
    )
    earlier_versions = sorted_versions[:-1] if len(sorted_versions) > 1 else sorted_versions
    email_domain_date = ''
    if 'info' in meta:
        if 'author_email' in meta['info']:
            email = meta['info']['author_email']
            if type(email) == str:
                email_domain = email.split("@")[-1]
                email_domain_date = whois.whois(email_domain)["creation_date"]
                if email_domain_date is None:
                    return False, "nothing"
    else:
        return False, "nothing"
    release_date = None
    for early_version in earlier_versions:
        version_release = releases[early_version]
        if len(version_release) > 0:  # if there's a distribution for the package
            upload_time_text = version_release[0]["upload_time_iso_8601"]
            release_date = parser.isoparse(upload_time_text).replace(tzinfo=None)
            break
    if release_date is None:
        return False, "nothing"
    # 比较两个 datetime 对象
    if email_domain_date > release_date:
        return True, "There is potential compromised email"
    return False, "nothing"


def few_files(path):
    count = 0  # 计数器，记录 .py 文件数量
    for dir_path, dir_names, file_names in os.walk(path):
        for filename in file_names:
            if filename.endswith(".py"):
                count += 1
    Min_file_num = 5
    if count <= Min_file_num:
        return True, "Few files,maybe malicious"


def author_analyse(maintainer_upload_times):
    issues = 0 
    message = ''
    for maintainer in maintainer_upload_times:
        print(f"正在分析维护者{maintainer}是否异常")
        num = 0
        for upload_time in maintainer_upload_times[maintainer]:
            time_delta = datetime.datetime.now()- datetime.datetime.strptime(upload_time, '%Y-%m-%dT%H:%M:%S') 
            time_2day = datetime.timedelta(days=2)
            if(time_delta < time_2day):
                num += 1
        if(num > 1):
                message += f'{maintainer}存在短期以内上传多个的package\n'
                print("危险！！存在一天以内上传的package")
    if message == '':
        return False,"nothing"
    else:
        return True,message
            
            