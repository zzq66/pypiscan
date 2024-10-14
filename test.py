import os
import tarsafe
dir = '/Users/zhaozhouqiao/Downloads/pypi_malregistry-main'
import static_analyse
import csv
import os

extract_dir_path = './evil_test/randrange-0.0.1.tar.gz'
print(static_analyse.static_analyse(extract_dir_path))
exit(0)


file = open('./example.csv', 'a+')
    # 创建CSV阅读器
csv_writer = csv.writer(file)

for root, dir, files in os.walk(dir, topdown=False):
    for name in files:
        print(os.path.join(root, name))
        if name.endswith('.tar.gz') or name.endswith('.tgz') or name.endswith('.tar') or name.endswith('.rar') or name.endswith('.7z'):
            extract_dir_path = "./evil_test/"+name
            if not os.path.exists(extract_dir_path):
                try:
                    os.mkdir(extract_dir_path)
                    tarsafe.open(os.path.join(root, name)).extractall(extract_dir_path)
                    issues,answer = static_analyse.static_analyse(extract_dir_path)    
                    tmp_row = [str(name),str(issues),str(answer)]
                    csv_writer.writerow(tmp_row)
                except:
                    pass
    for name in dir:
        pass
        #print(os.path.join(root, name))
       
file.close()