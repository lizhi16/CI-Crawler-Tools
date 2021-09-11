import pymongo

# save the devops logs
client = pymongo.MongoClient("mongodb://211.69.198.57:27017/")
db = client.devops_logs
logs = db.logs

logs.drop()

for i in logs.find():
    print (i) 
