import pymongo
import time
import csv

# client = pymongo.MongoClient("192.168.129.129", 27017)# connect mongodb
client = pymongo.MongoClient("localhost", 27017)# connect mongodb
Chunks = client['Memory_Chunks']#use “Memory_Chunks”
Memory = client['Email_Memory']
Updated_Chunks = client['Updated_Chunks']


#
#
# while True:
#     time.sleep(1)
#     data = {
#         'Sender_Addr': "info@amazon.com",
#         'Email_Title': "Your Amazon Account is Suspended!"
#     }
#     # db.Employees.insert_one(
#     #     {
#     #     "id": employeeId,
#     #         "name":employeeName,
#     #     "age":employeeAge,
#     #     "country":employeeCountry
#     #     })
#
#     # Try for five minutes to recover from a failed primary
#     for i in range(60):
#         try:
#             Chunks.Emails.insert(data, safe=True)
#             print ('wrote')
#             break # Exit the retry loop
#         except Exception:
#             print ('Warning')
#             time.sleep(5)





input_file = csv.DictReader(open("Email input.csv",encoding="utf-8"))

# for row in input_file:
#     print(row)

collection = Updated_Chunks.Emails

eml_instance1={
"ssdn" :"0", #Suspicious Sender Display Name
"url"  :"0", # URL Hyperlinking
"bl"   :"0", # No Branding/Logos
"pod"  :"0", # Poor Overall Design
"sge"  :"0", # Spelling and Grammar Errors
"gg"   :"0", # Generic Greeting
"uotp" :"0", # Use of Time Pressure
"uotl" :"0", # Use of Threatening Language
"uoea" :"0", # Use of Emotional Appeals
"losd" :"1", # Lack of Signer Details
"tgtt" :"1", # Too-Good-to-be-True Offers
"rfpi" :"1", # Requests for Personal Information
"lit"  :"0", # Link in Text
"sl"   :"1", # Suspicious Link
"truth":"1", # Whether this email is Suspicious or not
}


emls = collection.insert_many(input_file)

# collection.delete_many({ "Hyperlink(Text)": ""})
# post1 = collection.delete_many({})
# post2 = collection.delete_many({"name": "Mr.Shaurya"})
# print("Data inserted with record ids", rec_id1, " ", rec_id2)

# Insert Data
# eml_rec1 = collection.insert_one(eml_instance1)
# post2 = collection.delete_many({"Criterion": '0'})

# Printing the data inserted
cursor = collection.find()
print("-------------------------------------------")
for record in cursor:
    print(record)