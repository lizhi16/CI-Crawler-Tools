# !/bin/python3
import requests
import threading
from database import insert_logs2db

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

# threads for crawler on TravisCI
class travis_threading(threading.Thread):
    def __init__(self, log_id):
        threading.Thread.__init__(self)
        # url pattern of the logs in TravisCI
        travis_url = "https://api.travis-ci.org/v3/job/{}/log.txt"
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

        repo_link, author = self.resolve_repo_address(content)
        log_text = content.encode('utf-8').decode("utf-8")
        status = insert_logs2db(self.log_id, repo_link, author, log_text)
        if status:
            print ("[INFO] " + str(self.log_id) + " save into database success.")
            return 1
        else:
            print ("[ERROR] " + str(self.log_id) + " save into database failed...")
            return 0

        return 1
    
    def resolve_repo_address(self, content):
        repo_link = ""
        author = ""
        for line in content.split("\n"):
            if "git clone --depth=50" in line:
                repo_link = line.strip().rsplit(" ", 2)[1]
                author = line.strip().rsplit(" ", 1)[1]

        return repo_link, author


# index in range(440080000, 440900000):
# "step" is used to control sampling 
def Start_analyze_travis(start_id, end_id, step):
    analyze_thread = []
    for index in range(int(start_id), int(end_id) + 1, int(step)):
        thread = travis_threading(index)
        print ("[INFO] Start to get index: " + str(index))
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