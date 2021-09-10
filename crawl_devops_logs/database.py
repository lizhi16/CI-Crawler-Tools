# !/bin/python3
import pymongo

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
        logs.insert_one(log)        #.inserted_id
        return True
    except:
        return False

def delete_database():
    logs.drop()
