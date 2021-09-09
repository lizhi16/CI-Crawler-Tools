# Crawling dockerhub for all Dockerfile, and checking this Dockerfile whether has malicious behaviors
import sys
import time
import requests
import threading
import pymongo
import gzip

# save the devops logs
client = pymongo.MongoClient("mongodb://211.69.198.57:27017/")
db = client.devops_logs
logs = db.logs

# insert log to database
def insert_logs2db(log_id, log_text, repo_link, author):
    log = {
        "log_id": log_id,
        "github": repo_link,
        "author": author,
        "log_text": log_text,
    }

    try:
        logs.insert_one(log).inserted_id
        return True
    except:
        return False

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
        return content.text
    else:
        print ("[ERROR] Can't resolve url:", url)
        return None

def resolve_repo_address(content):
    repo_link = ""
    author = ""
    for line in content.split("\n"):
        if "git clone --depth=50" in line:
            repo_link = line.strip().rsplit(" ", 2)[1]
            author = line.strip().rsplit(" ", 1)[1]

    return repo_link, author

travis_url = "https://api.travis-ci.org/v3/job/{}/log.txt"
class travis_threading(threading.Thread):
    def __init__(self, log_id):
        threading.Thread.__init__(self)
        self.log_id = str(log_id)
        self.url = travis_url.format(str(log_id))

    def run(self):
        flag = self.travis_log_analysis()
        if flag == -1:
            print ("[INFO] " + str(self.log_id) + " doesn't exist.")
        
    def travis_log_analysis(self):
        # get log
        content = get_url_content(self.url)
        if content == None:
            return -1

        if "Sorry, we experienced an error." in content:
            return -1

        repo_link, author = resolve_repo_address(content)
        log_text = content.encode('utf-8').decode("utf-8")
        status = insert_logs2db(self.log_id, repo_link, author, log_text)
        if status:
            print ("[INFO] " + str(self.log_id) + " save into database success.")
            return 1
        else:
            print ("[ERROR] " + str(self.log_id) + " save into database failed...")
            return 0

        return 1

def start_analyze_travis():
    analyze_thread = []
    for index in range(440000000, 440070000):
        thread = travis_threading(index)
        print ("[INFO] Start to get index: " + str(index))
        # keep the threads < cores numbers
        if len(threading.enumerate()) <= 30:
            thread.start()
            analyze_thread.append(thread)
        else:
            for t in analyze_thread:
                t.join()

            thread.start()
            analyze_thread.append(thread)

    for t in analyze_thread:
        t.join()

if __name__ == '__main__':
    start_analyze_travis()