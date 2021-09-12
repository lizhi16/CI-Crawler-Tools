from os import replace
import pymongo

# ====== database ======
client = pymongo.MongoClient("mongodb://211.69.198.57:27017/")
db_analysis = client.devops_analysis
dbs_res = db_analysis["base64_results"]

tmp = {}
def base64_db2file():
    with open("base64_results.csv", "w+") as log:
        for content in dbs_res.find():
            resolved = content["resolve_data"]
            github = content["github"]
            log_id = content["log_id"]

            if resolved in tmp:
                continue
            else:
                tmp[resolved] = 1

            results = str(resolved).replace(",", ";") + ", " + str(github) + str(log_id) + "\n"
            log.write(results)

base64_db2file()