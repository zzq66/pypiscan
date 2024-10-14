# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
# 启动项类
start_keywords = ["Software\Microsoft\Windows\CurrentVersion\Run",
                  "Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run",
                  "Software\Microsoft\Windows\CurrentVersion\RunServicesOnce",
                  "Software\Microsoft\Windows\CurrentVersion\RunServices",
                  "Software\Microsoft\Windows\CurrentVersion\RunOnce",
                  "SOFTWARE\Microsoft\Active Setup\Installed Components",
                  "Software\Microsoft\WindowsNT\CurrentVersion\Windows",
                  "Software\Microsoft\WindowsNT\CurrentVersion\Windows"
                  ]

# 解码类
# rule1
encry_keywords = ["b64decode(",
                  "pycrypto",
                  "decrypt"
                  ]

# rule2
# 网络传输类
net_keywords = ["socket",
                "urllib.request",
                "urllib.urlopen",
                "urllib2.urlopen",
                "requests.get",
                "requests.post",
                "http://",
                "https://",
                ]
# rule3
# 命令执行类
exec_keywords = ["os.system",
                 "os.popen",
                 "commands.getstatusoutput",
                 "commands.getoutput",
                 "commands.getstatus",
                 "os.chmod",
                 "exec(",
                "b64decode(",
                "subprocess",
                "subprocess",
                "eval("
                "__builtins__"
                 ]
# rule4
# 本地敏感文件
local_keywords = [".bashrc","/.ssh/id_rsa","/etc/passwd",
                  ".ssh/","/etc/passwd","/etc/group",
                  "/etc/ld.so.preload","/etc/sysctl.conf",
                  "/etc/shells","/etc/crontab","explorer.exe",
                  "regedit.exe","rundll32.exe"
                  ]
# rule5
# 覆盖setup
setup_overwrite = ["cmdclass",
                   "egg_info",
                   "install",
                   "develop"
                   ]

paste =[
    "pyperclip.paste",
    "pyperclip.copy",
    "pandas.read_clipboard",
    "$VAR.to_clipboard"  
     ]

import re
all_str = start_keywords + encry_keywords + net_keywords + exec_keywords + local_keywords + setup_overwrite + paste
# 定义多个敏感特征正则规则
patterns = [
    r"\bSELECT\b\s+(.+?)\s+\bFROM\b",
    r"\bINSERT INTO\b\s+(\w+)",
    r"\bUPDATE\b\s+(\w+)",
    r"\bUPDATE\b\s+(\w+)",
    r"http(s?)://(.+?).ceye.io",
    
]
confuse_feature = ['__builtins__','__str__','getattr','hex',
                   '<<','|','>>','((((','__class__.','__bases__',
                   '__mro__','__subclasses__','__globals__',
                   '__dict__','getitem','']

def Check(filestr):
    answer = []
    for keyword in all_str:
        if keyword in filestr:
            answer.append('Match malicious word: '+keyword)
    # 逐个匹配规则并输出结果
    for pattern in patterns:
        match = re.search(pattern, filestr, re.IGNORECASE)
        if match:
            result = match.group(1)
            #print("Matched pattern: ", pattern)
            #print("Result: ", result)
            answer.append('Match malicious word: '+result+'\n')
    total_count = 0
    species_number = 0
    total_Threshold = 10
    species_Threshold = 3
    for word in confuse_feature:
        total_count += filestr.count(word)
        if word in filestr:
            species_number += 1
    if species_number >= species_Threshold:
        answer.append(f'Malicious confuse feature species over {species_number}')
    if total_count >= total_Threshold:
        answer.append(f'Malicious confuse feature total over {total_count}')
    if answer !=[]:
        return True,answer
    return False,'No malicious trace match'
        