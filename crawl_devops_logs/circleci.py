# !/bin/python3
import time
import requests
import threading
from database import insert_logs2db

#-------------------------------------------------------------------#
#                                                                   #
#       need a program analyze the content of project url           #   
#       "https://circleci.com/api/v1.1/project/github/{}"           #
#                                                                   #
#-------------------------------------------------------------------#

# url pattern of the logs in CircleCI
# {} is the repo_name, such as "zawiszaty/cqrs-blog"
circleci_url = "https://circleci.com/api/v1.1/project/github/{}" 

# https://circleci.com/api/v1.1/project/github/{repo_name}/{build_times}/output/102/0?file=true
logs_url = "https://circleci.com/api/v1.1/project/github/{}/{}/output/{}/0?file=true"


# get the content from a url
def get_url_content(url):
    headers = {
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }
    content = requests.get(url, headers=headers)

    # WARN: for high frequency requests
    while content.status_code == 429:
        print("[WARN] High frequncy requests!")
        time.sleep(60)
        content = requests.get(url,headers=headers)

    if content.status_code == 200:
        return content
    else:
        #print ("[ERROR] Can't resolve url:", url)
        return None

# threads for crawler on CircleCI
class circleci_threading(threading.Thread):
    def __init__(self, repo_name):
        threading.Thread.__init__(self)

        # use to get the log url of each building
        self.repo_name = str(repo_name)
        self.project_url = circleci_url.format(self.repo_name)
        
        # the real url of building logs
        self.build_nums = {}
        self.build_author = {}    
        self.logs_url = ""

        # data for database
        self.log_id = ""            # project_url + build_num
        self.author = ""            
        self.repo_link = ""
        self.log_text = ""
        
    def run(self):
        # get build infos of the whole project
        status = self.get_build_records()
        if not status:
            return

        # get output of each build
        self.circleci_log_analysis()

    def get_build_records(self):
        # 1: judge if the project exists
        records = get_url_content(self.project_url)
        if records == None:
            print ("[INFO] " + str(self.repo_name) + " didn't use CircleCI...")
            return False

        # 2: get the information of each building process
        records = records.json()
        for record in records:
            # get build_num
            if "build_num" in record:
                build_num = record["build_num"]
            else:
                continue
            
            # get commit_url and author to this build
            if "all_commit_details" in record and len(record["all_commit_details"]) > 0:
                commit = record["all_commit_details"][0]['commit_url']
            else:
                commit = "https://github.com/" + self.repo_name

            if "author_email" in record:
                author = record["author_email"]
            else:
                author = ""
            
            if build_num not in self.build_nums:
                self.build_nums[build_num] = commit
                self.build_author[build_num] = author

        # self.build_nums is not empty
        if self.build_nums:
            return True
        else:
            return False
        
    def circleci_log_analysis(self):
        # [TEST] control the number of sampling
        sample_num = 1
        # -------------------

        for num in self.build_nums:
            # ----- [TEST] -----
            if sample_num <= 0:
                break
            sample_num -= 1
            # ------------------

            self.log_id = self.project_url + "/" + str(num)
            self.author = self.build_author[num]
            self.repo_link = self.build_nums[num]

            # why this scope is 101, I don't know...
            for index in range(101, 115):
                self.logs_url = logs_url.format(self.repo_name, str(num), str(index))
                content = get_url_content(self.logs_url)
                if content == None:
                    break

                self.log_text = self.log_text + "\n\n\n" + content.text.encode('utf-8').decode("utf-8")

            # print (self.log_id)
            # print (self.author)
            # print (self.repo_link)
            # print (self.log_text)

            status = insert_logs2db(str(self.log_id), str(self.repo_link), str(self.author), str(self.log_text))
            if status:
                print ("[INFO] " + str(self.log_id) + " save into database success.")
            else:
                print ("[ERROR] " + str(self.log_id) + " save into database failed...")


# "path" contain the github repo link for circleci
def Start_analyze_circleci(path):
    with open(path, "r") as log:
        analyze_thread = []
        for line in log.readlines():
            try:
                if "https://" in line:
                    repo_name = line.split("/")[3].strip() + "/" + line.split("/")[4].strip()
                else:
                    repo_name = line.strip()
            except:
                continue

            print ("[INFO] Start to get index: " + str(repo_name))
            thread = circleci_threading(repo_name)
            
            # keep the threads < cores numbers
            if len(threading.enumerate()) <= 32:
                thread.start()
                analyze_thread.append(thread)
            else:
                for t in analyze_thread:
                    t.join()

                thread.start()
                analyze_thread.append(thread)

        for t in analyze_thread:
            t.join()
