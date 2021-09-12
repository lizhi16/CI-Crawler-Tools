import re
import pymongo
import threading

# ==== search pattern ====
patterns = {}
# patterns["base64"] = r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$'
patterns["base64"] = r'^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$'
patterns["url"] = r'(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]'

# ====== database ======
client = pymongo.MongoClient("mongodb://211.69.198.57:27017/")

# target logs to be analyzed
db_logs = client.devops_logs
logs = db_logs.logs

# save results database
db_analysis = client.devops_analysis
dbs_res = {}
for type in patterns:
    dbs_res[type] = db_analysis[type]


# threads for analyzer
class analyzer_threading(threading.Thread):
    def __init__(self, content):
        threading.Thread.__init__(self)

        # init the content for next analysis
        try:
            self.log_id = content["log_id"]
            self.github = content["github"]
            self.log_text = content["author"] # error happend in init database
        except:
            return
        
    def run(self):
        # get build infos of the whole project
        for type in patterns:
            results = catch_c2_payload(self.log_text, type)

            if results:
                print ("[INFO] " + self.github + " find " + type + " info.")

            # save to database
            self.results2db(type, results)
    
    def results2db(self, type, results):
        for item in results:
            log = {
                "type": type,
                "github": self.github,
                "match": item,
                "origin": results[item],
                "log_id": self.log_id,
            }

            try:
                dbs_res[type].insert_one(log)        #.inserted_id
            except:
                continue

# search any C2 payload-ish content shown in "log_text"
def catch_c2_payload(content, type):
    # results of analysis
    results = {}

    # start to analyze
    for line in content.split("\n"):
        line = line.replace("\r", " ").strip()

        # get the regex pattern of the specific type
        pattern = patterns[type]
        for item in line.split(" "):
            # search text fitting the type = "base64"
            if re.match(pattern, item):
                if type == "base64" and len(item) < 20:
                    continue
                if item not in results:
                    results[item] = line

    return results

def Start_logs_analysis():
    index = 0
    total = logs.count()

    analyze_thread = []
    for content in logs.find():
        index += 1
        if index < 41713:
            continue
        print ("[INFO] Start to get index: [" + str(index) + "/" + str(total) + "]")
        thread = analyzer_threading(content)
            
        # keep the threads < cores numbers
        if len(threading.enumerate()) <= 32:
            thread.start()
            analyze_thread.append(thread)
        else:
            for t in analyze_thread:
                t.join()

            analyze_thread = []
            thread.start()
            analyze_thread.append(thread)
        
        # if index == 1:
        #     break

    for t in analyze_thread:
        t.join()

Start_logs_analysis()
