import base64
import chardet
import pymongo
import threading

# ====== database ======
client = pymongo.MongoClient("mongodb://211.69.198.57:27017/")
db_analysis = client.devops_analysis
dbs_org = db_analysis["base64"]

# save the resolving results
dbs_res = db_analysis["base64_results"]

# threads for resolving
class analyzer_threading(threading.Thread):
    def __init__(self, content):
        threading.Thread.__init__(self)

        try:
            # init the content for next analysis
            self.match = str(content["match"])
            self.github = content["github"]
            self.log_id = content["log_id"]

            # resolve results
            self.decode = ""
        except:
            return
        
    def run(self):
        if self.match == "":
            return

        if self.resolve_base64():
            # print ("[INFO] " + str(self.log_id) + " has meaningful base64.")
            if self.results2db():
                print ("[INFO] " + str(self.log_id) + " add to database successful.")

    def resolve_base64(self):
        # base64 decode
        try:
            decoder = base64.b64decode(self.match)
            self.decode = decoder.decode('utf-8')      # byte to str
        except:
            return False

        # judge if the str contain bad code
        readable = chardet.detect(decoder)
        if "confidence" in readable and readable["confidence"] == 0:
            return False

        return True

    def results2db(self):
        log = {
            "resolve_data": self.decode,
            "github": self.github,
            "match": self.match,
            "log_id": self.log_id,
        }

        try:
            dbs_res.insert_one(log)        #.inserted_id
            return True
        except:
            return False

def Start_base64_analysis():
    index = 0
    total = dbs_org.count()

    analyze_thread = []
    for content in dbs_org.find():
        index += 1
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

Start_base64_analysis()

# { "_id" : ObjectId("613d77eb1220e1c89f4149cb"), "resolve_data" : "800Z0,1\u001c0\r\u0006\u0003U\u0004\u000b\u0013\u0006client0\u000b\u0006\u0003U\u0004\u000b\u0013\u0004org11\f0\n\u0006\u0003U\u0004\u0003\u0013\u0003s", "github" : "hyperledger/composer", "match" : "ODAwWjAsMRwwDQYDVQQLEwZjbGllbnQwCwYDVQQLEwRvcmcxMQwwCgYDVQQDEwNz", "log_id" : "440030838" }
