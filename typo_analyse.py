import Levenshtein
import itertools
import jellyfish
import scraper
import warnings
from stdlib_list import stdlib_list
from mrs_spellings import MrsWord
warnings.simplefilter("ignore")


def similar_attack_cal_distance(package_name, package_list, distance=1):
    close_package = []
    for package_item in package_list:
        if Levenshtein.distance(package_name, package_item) <= distance:
            close_package.append(package_item)
    if package_name in close_package:
        close_package.remove(package_name)
    return sorted(close_package)


def permutation(package_list=None):
    if package_list is None:
        package_list = []
    perms_list = list(itertools.permutations(package_list))
    re_permu_list = []
    for perm in perms_list:
        re_permu_list.append("-".join(perm))
        re_permu_list.append("_".join(perm))
    return re_permu_list


def order_attack_detect(package_name="", package_list=None):
    if package_list is None:
        package_list = []
    order_attack_candidates = []
    if "-" in package_name:
        package_name_split = package_name.split("-")
        possible_attacks = permutation(package_name_split)
        for possible_attack in possible_attacks:
            if possible_attack in package_list:
                order_attack_candidates.append(possible_attack)
    if "_" in package_name:
        package_name_split = package_name.split("_")
        possible_attacks = permutation(package_name_split)
        for possible_attack in possible_attacks:
            if possible_attack in package_list:
                order_attack_candidates.append(possible_attack)
    if package_name in order_attack_candidates:
        order_attack_candidates.remove(package_name)
    return order_attack_candidates


def homophone_attack_detect(package_name="", package_list=None):
    if package_list is None:
        package_list = []
    homophone_attack_candidate = []
    homophone_interest = jellyfish.metaphone(package_name)
    for item in package_list:
        if homophone_interest == jellyfish.metaphone(item):
            homophone_attack_candidate.append(item)
    if package_name in homophone_attack_candidate:
        homophone_attack_candidate.remove(package_name)
    return homophone_attack_candidate

def Combosquatting_attack_detect(package_name="", package_list=None):
    ##检测利用知名包，加一个后缀啥的，比如nmap 变成nmap-dev
    if package_list is None:
        package_list = []
    Combosquatting_attack_candidate = []
    for item in package_list:
        if package_name+'-' in item or '-'+package_name in item:
            Combosquatting_attack_candidate.append(item)
        if package_name+'_' in item or '_'+package_name in item:
            Combosquatting_attack_candidate.append(item)
    return Combosquatting_attack_candidate

def Same_with_stdlib(package_name):
    libraries = stdlib_list()
    if package_name in libraries:
        return package_name
    return []

def single_package_typo_detect(package_name):
    detect_results = []
    #top_package = scraper.get_top_package_name()
    all_package = scraper.get_all_pypi_names()
    detect_results.extend(similar_attack_cal_distance(package_name, all_package, 1))
    detect_results.extend(order_attack_detect(package_name, all_package))
    detect_results.extend(Combosquatting_attack_detect(package_name, all_package))
    detect_results.extend(Same_with_stdlib(package_name))
    detect_results = set(detect_results)
    detect_results = list(detect_results)  
    return sorted(detect_results)


def single_package_protect(package_name):
    protect_name = MrsWord(package_name).qwerty_swap()
    protect_name = set(protect_name)
    protect_name = list(protect_name)
    return protect_name


import os
import glob

# 获取当前文件夹下所有文件名

def single_package_typo_detect2():
    detect_results = []
    #top_package = scraper.get_top_package_name()
    all_package = scraper.get_top_package_name()
    answer = []
    file_list = os.listdir('/Users/zhaozhouqiao/Desktop/poisoning_project/my_project/evil_test/')
    for file in file_list:
            filename  =file.split('-')[0]
            detect_results = []
            detect_results.extend(similar_attack_cal_distance(filename, all_package, 1))
            detect_results.extend(order_attack_detect(filename, all_package))
            detect_results.extend(Combosquatting_attack_detect(filename, all_package))
            detect_results.extend(Same_with_stdlib(filename))
            detect_results = set(detect_results)
            detect_results = list(detect_results)
            if detect_results!=[]:
                answer.append(file)
    return answer

