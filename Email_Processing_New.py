from model import Email_Cog_Sim_Model
from chunks import chunktype
from chunks import Chunk
from chunks import makechunk
import pymongo
from secrets import choice as rchoice
import pprint
import os
from shutil import copyfile
import numpy as np
import random



# client = pymongo.MongoClient("192.168.129.129", 27017)#connect MongoDB Database
client = pymongo.MongoClient("localhost", 27017)#connect MongoDB Database
# Chunks = client['Memory_Chunks']#use “Memory_Chunks” scheme
Chunks = client['Email_Memory']#use Email_Memory scheme
Updated_Chunks = client['Updated_Chunks']

collection = Updated_Chunks.Emails
sim_round = 100
sim_round_index = 0
links_lower_bound = 1
links_upper_bound = 14
num_emails = 40
duplicate_level = 5000
# SUS_THRESHOLD = 6
# CUE_THRESHOLD = 11
model_params = {"subsymbolic": True,
                    "rule_firing": 0.05,
                    "latency_factor": 0.1,
                    "latency_exponent": 1.0,
                    "decay": 0.5,
                    "baselevel_learning": True,
                    "optimized_learning": False,
                    "instantaneous_noise": 0.25,
                    "retrieval_threshold": -float('inf'),
                    "buffer_spreading_activation": {},
                    "spreading_activation_restricted": False,
                    "strength_of_association": 0,
                    "association_only_from_chunks": True,
                    "partial_matching": True,
                    # "mismatch_penalty": 1.0,
                    "activation_trace": True,
                    "utility_noise": 0,
                    "utility_learning": False,
                    "utility_alpha": 0.2,
                    "motor_prepared": False,
                    "strict_harvesting": False,
                    "production_compilation": False,
                    "automatic_visual_search": True,
                    "emma": True,
                    "emma_noise": True,
                    "emma_landing_site_noise": False,
                    "eye_mvt_angle_parameter": 1,  # in LispACT-R: 1
                    "eye_mvt_scaling_parameter": 0.01,  # in LispACT-R: 0.01, but dft rule firing -- 0.01
                    }

def ProcessByBatch(list,file,email):
    global model_params
    retrieved_chunk = None
    used_cue = None
    activation_score = float("-inf")
    global current_time
    current_time = current_time + 1
    file.write("Processing Batch: " + list.__repr__() + '\n')
    for cue in list:
        retrieved = retrieval.retrieve1(current_time, cue, model_params, dm, file, email)
        while (retrieved[0] == None):
            retrieved = retrieval.retrieve1(current_time, cue, model_params, dm, file, email)
        if retrieved[1] > activation_score:
                retrieved_chunk = retrieved[0]
                used_cue = cue

    # print("used_cue", used_cue)
    # print("retrieved_chunk",retrieved_chunk)
    dm.add(retrieved_chunk, current_time)
    file.write('____________________________________________________________________________________________________________'+'\n')
    file.write('Email: ' + str(email['Email']) + "\n"+'Used Cue: '+str(used_cue.__repr__())+'\n'+'Retrieved Chunk ' + str(retrieved_chunk.__repr__())+'\n' + 'at current_time: ' + str(current_time) + '\n')


    return retrieved_chunk,used_cue

def ProcessByCue(cue,file,email):
    global current_time
    global sim_round_index
    global model_params
    # a = list()
    # p = list()  # candidate
    # for i in dm:
    #     a.append(i.match(cue, True))
    #
    # for j in dm:
    #     if j.match(cue, True) == max(a) and j.typename == cue.typename:
    #         p.append(j)


    current_time = current_time + 1.0
    file.write("Processing Cue: "+cue.__repr__()+'\n')
    if model_params['activation_trace']:
        file.write("Activation Trace: " + '\n')
    retrieved_elem = retrieval.retrieve1(current_time, cue, model_params, dm,file,email)[0]
    while (retrieved_elem == None):
        retrieved_elem = retrieval.retrieve1(current_time, cue,model_params, dm,file,email)[0]


    dm.add(retrieved_elem, current_time)
    file.write('____________________________________________________________________________________________________________'+'\n')
    file.write('Email: ' + str(email['Email']) + "\n"+'Observed Cue: '+cue.__repr__()+'\n'+'Retrieved Chunk ' + retrieved_elem.__repr__()+'\n' + 'at current_time: ' + str(current_time) + '\n')
    return retrieved_elem

def ProcessByEmail(email,threshold,cue_cutoff,file,fault_level):
    global current_time
    cue_checked = 0
    suspicion_level = 0
    flag = random.random()
    if flag < fault_level:
        sender_chunk   = makechunk("sender_chunk", "IDENTIFY_SENDER_NAME", email['Sender (Text)'],sender=str(1-int(email['Sender'])))
    else:
        sender_chunk   = makechunk("sender_chunk", "IDENTIFY_SENDER_NAME", email['Sender (Text)'],sender=email['Sender'])

    flag = random.random()
    if flag < fault_level:
        subject_chunk  = makechunk("subject_chunk", "IDENTIFY_EMAIL_SUBJECT", email['Subject (Text)'],subject=str(1-int(email['Subject'])))
    else:
        subject_chunk  = makechunk("subject_chunk", "IDENTIFY_EMAIL_SUBJECT", email['Subject (Text)'],subject=email['Subject'])

    flag = random.random()
    if flag < fault_level:
        branding_chunk = makechunk("branding_chunk", "IDENTIFY_BRANDING_LOGOS",email['Branding (Text)'], branding=str(1-int(email['Branding'])))
    else:
        branding_chunk = makechunk("branding_chunk", "IDENTIFY_BRANDING_LOGOS",email['Branding (Text)'], branding=email['Branding'])

    flag = random.random()
    if flag < fault_level:
        design_chunk   = makechunk("design_chunk", "IDENTIFY_POOR_DESIGN", email['Design (Text)'],design=str(1-int(email['Design'])))
    else:
        design_chunk   = makechunk("design_chunk", "IDENTIFY_POOR_DESIGN", email['Design (Text)'],design=email['Design'])

    flag = random.random()
    if flag < fault_level:
        spelling_chunk = makechunk("spelling_chunk", "IDENTIFY_GRAMMAR_ERROR", email['Spelling (Text)'],spelling=str(1-int(email['Spelling'])))
    else:
        spelling_chunk = makechunk("spelling_chunk", "IDENTIFY_GRAMMAR_ERROR", email['Spelling (Text)'],spelling=email['Spelling'])

    flag = random.random()
    if flag < fault_level:
        greeting_chunk = makechunk("greeting_chunk", "IDENTIFY_GENERIC_GREETING",email['Greeting (Text)'], greeting=str(1-int(email['Greeting'])))
    else:
        greeting_chunk = makechunk("greeting_chunk", "IDENTIFY_GENERIC_GREETING",email['Greeting (Text)'], greeting=email['Greeting'])

    flag = random.random()
    if flag < fault_level:
        time_chunk     = makechunk("time_chunk", "IDENTIFY_TIME_PRESSURE", email['Time (Text)'],time=str(1-int(email['Time'])))
    else:
        time_chunk     = makechunk("time_chunk", "IDENTIFY_TIME_PRESSURE", email['Time (Text)'],time=email['Time'])

    flag = random.random()
    if flag < fault_level:
        threat_chunk   = makechunk("threat_chunk", "IDENTIFY_THREAT_LANG", email['Threats (Text)'],threat=str(1-int(email['Threats'])))
    else:
        threat_chunk   = makechunk("threat_chunk", "IDENTIFY_THREAT_LANG", email['Threats (Text)'],threat=email['Threats'])
    
    flag = random.random()
    if flag < fault_level:
        emotion_chunk  = makechunk("emotion_chunk", "IDENTIFY_EMOTION_APPEAL", email['Emotion (Text)'],emotion=str(1-int(email['Emotion'])))
    else:
        emotion_chunk  = makechunk("emotion_chunk", "IDENTIFY_EMOTION_APPEAL", email['Emotion (Text)'],emotion=email['Emotion'])

    flag = random.random()
    if flag < fault_level:
        signer_chunk   = makechunk("signer_chunk", "IDENTIFY_SIGNER_DETAIL", email['Signer (Text)'],signer=str(1-int(email['Signer'])))
    else:
        signer_chunk   = makechunk("signer_chunk", "IDENTIFY_SIGNER_DETAIL", email['Signer (Text)'],signer=email['Signer'])

    flag = random.random()
    if flag < fault_level:
        too_good_chunk = makechunk("too_good_chunk", "IDENTIFY_TOO_GOOD", email['Toogood (Text)'],tg=str(1-int(email['Toogood'])))
    else:
        too_good_chunk = makechunk("too_good_chunk", "IDENTIFY_TOO_GOOD", email['Toogood (Text)'],tg=email['Toogood'])

    flag = random.random()
    if flag < fault_level:
        request_chunk  = makechunk("request_chunk", "IDENTIFY_PERSONAL_REQ", email['Requests (Text)'],request=str(1-int(email['Requests'])))
    else:
        request_chunk  = makechunk("request_chunk", "IDENTIFY_PERSONAL_REQ", email['Requests (Text)'],request=email['Requests'])



    random_list = list()
    linkchunk_list = dict()
    static_list = list()
    links_count = 0
    #static cue list
    static_list.append(branding_chunk)
    static_list.append(design_chunk)
    static_list.append(sender_chunk)
    static_list.append(subject_chunk)
    static_list.append(signer_chunk)
    static_list.append(greeting_chunk)
    #randomized cue list
    random_list.append(time_chunk)
    random_list.append(threat_chunk)
    random_list.append(emotion_chunk)
    random_list.append(too_good_chunk)
    random_list.append(request_chunk)
    random_list.append(spelling_chunk)

    for i in range(links_lower_bound,links_upper_bound):
            if email['Hyperlink (Text) #'+str(i)] != "":
                flag = random.random()
                if flag < fault_level:
                    linkchunk_list['link_chunk'+str(links_count+1)] = makechunk("links_chunk", "IDENTIFY_LINKS", email['Hyperlink (Text) #'+str(i)],link_in_text=email['Hyperlink: Link_In_Text #'+str(links_count+1)],sus_link=str(1-int(email['Hyperlink: Suspicious_Link #'+str(links_count+1)])))
                else:
                    linkchunk_list['link_chunk'+str(links_count+1)] = makechunk("links_chunk", "IDENTIFY_LINKS", email['Hyperlink (Text) #'+str(i)],link_in_text=email['Hyperlink: Link_In_Text #'+str(links_count+1)],sus_link=email['Hyperlink: Suspicious_Link #'+str(links_count+1)])
                links_count = links_count + 1
            else:
                break
    for j in linkchunk_list.keys():
        random_list.append(linkchunk_list[j])

    file.write('Opened Email: '+str(email['Email'])+'\n')

    for i in range(static_list.__len__()):
        cue = static_list[i]
        retrieved = ProcessByCue(cue,file,email)
        cue_checked = cue_checked + 1
        suspicion_level = suspicion_level + int(retrieved.criterion)
        file.write('sus_level: ' + str(suspicion_level)+ '\n')
        file.write('cue_checked: ' + str(cue_checked) + '\n')
        file.write(
            '____________________________________________________________________________________________________________' + '\n')

        if suspicion_level >= threshold:
            classification[email['Email']] = "1"
            file.write('Current Time: '+str(current_time)+' <Classified> Email: ' + '<' + str(
                email['Email']) + '>' + ' to ' + '<Suspicious>' + ' at sus_level ' + str(
                suspicion_level) + " with " + str(cue_checked) + " cues checked" + '\n')
            file.write(
                '____________________________________________________________________________________________________________' + '\n')
            return


    if cue_cutoff-len(static_list) >0:
        for i in range(cue_cutoff-len(static_list)):
            retrieved_entry = ProcessByBatch(random_list, file, email)
            retrieved = retrieved_entry[0]
            used = retrieved_entry[1]
            print(random_list)
            for i in random_list:
                if retrieved.typename == i.typename and retrieved.typename != "IDENTIFY_LINKS" :
                    random_list.remove(i)
                    break
                if retrieved.typename == i.typename and retrieved.typename == "IDENTIFY_LINKS":
                    random_list.remove(used)
                    break
            print(random_list.__len__())
            cue_checked = cue_checked + 1
            suspicion_level = suspicion_level + int(retrieved.criterion)
            file.write('sus_level: ' + str(suspicion_level) + '\n')
            file.write('cue_checked: ' + str(cue_checked) + '\n')
            file.write(
                '____________________________________________________________________________________________________________' + '\n')

            if suspicion_level >= threshold:
                classification[email['Email']] = "1"
                file.write('Current Time: '+str(current_time)+' <Classified> Email: ' + '<'+str(email['Email'])+'>' + ' to ' + '<Suspicious>' + ' at sus_level ' + str(suspicion_level) + " with "+str(cue_checked)+" cues checked"+'\n')
                file.write(
                    '____________________________________________________________________________________________________________' + '\n')
                return





        # cue= random_list[randrange(0,len(random_list),1)]
        # retrieved = ProcessByCue(cue,file,email)
        # suspicion_level = suspicion_level + int(retrieved.criterion)
        # if suspicion_level >= threshold:
        #     classification[email['Email']] = "1"
        #     file.write('email: ' + str(Email_title) + ' sus_level ' + str(suspicion_level) + ' classification: ' + str(
        #         classification[email['Email']])+'\n')
        #     return
        # random_list.remove(cue)
    # if len(linkchunk_list.keys()) >=num_links and len(linkchunk_list.keys()) > 0:
    #     comb = combinations(range(len(linkchunk_list.keys())), num_links)
    #     for i in range(num_links):
    #         cue = makechunk("link_chunk", "IDENTIFY_LINKS", link_in_text=email['Hyperlink: Link_In_Text #'+str(i+1)],sus_link=email['Hyperlink: Suspicious_Link #'+str(i+1)], criterion='')
    #         retrieved = ProcessByCue(cue,file,email)
    #         suspicion_level = suspicion_level + int(retrieved.criterion)
    #         if suspicion_level >= threshold:
    #             classification[email['Email']] = "1"
    #             file.write('email: ' + str(Email_title) + ' sus_level ' + str(suspicion_level) + ' classification: ' + str(
    #                 classification[email['Email']])+'\n')
    #             return
    # else:
    #     print(len(linkchunk_list.keys()))
    #     raise ModelError("The email being processed do not contain as many links" )
    classification[email['Email']] = "0"
    file.write('Current Time: '+str(current_time)+
        ' <Classified> Email: ' + '<' + str(email['Email']) + '>' + ' to ' + '<Keep>' + ' at sus_level ' + str(
            suspicion_level) + " with " + str(cue_checked) + " cues checked" + '\n')
    file.write(
        '____________________________________________________________________________________________________________' + '\n')
    return


if __name__ == '__main__':
    for CUE_THRESHOLD in range(7, 13):
        for SUS_THRESHOLD in range(2,7):
            for mis_coefficient in range(1,4):
                for fault_level in np.arange(0.0, 0.6, 0.1):
                    model_params['mismatch_penalty'] = float(mis_coefficient)
                    # folder_path = str(CUE_THRESHOLD)+'_'+str(SUS_THRESHOLD)+'_'+str(mis_coefficient)
                    folder_path = os.path.join('', str(CUE_THRESHOLD)+'_'+str(SUS_THRESHOLD)+'_'+str(mis_coefficient)+'_'+str("{0:0.1f}".format(fault_level)))
                    file_path = os.path.join(folder_path, "accuracy" + "." + "py")
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)
                        #copyfile("accuracy.py", file_path)
                        os.chdir(folder_path)
                        for _ in range(sim_round):
                            model = Email_Cog_Sim_Model()
                            dm = model.decmem
                            retrieval = model.retrieval
                            activation_history = dm.activations
                            email_list = list(range(num_emails))
                            sim_round_index = (sim_round_index + 1)%100
                            file = open('results-' + str(sim_round_index) + '.txt', 'w', encoding='utf8')
                            current_time = 0
                            classification = dict()  # Store classification result
                            chunktype("IDENTIFY_EMAIL_SUBJECT", "subject")
                            chunktype("IDENTIFY_SENDER_NAME", "sender")
                            chunktype("IDENTIFY_BRANDING_LOGOS", "branding")
                            chunktype("IDENTIFY_POOR_DESIGN", "design")
                            chunktype("IDENTIFY_GRAMMAR_ERROR", "spelling")
                            chunktype("IDENTIFY_GENERIC_GREETING", "greeting")
                            chunktype("IDENTIFY_TIME_PRESSURE", "time")
                            chunktype("IDENTIFY_THREAT_LANG", "threat")
                            chunktype("IDENTIFY_EMOTION_APPEAL", "emotion")
                            chunktype("IDENTIFY_SIGNER_DETAIL", "signer")
                            chunktype("IDENTIFY_TOO_GOOD", "tg")
                            chunktype("IDENTIFY_PERSONAL_REQ", "request")
                            chunktype("IDENTIFY_LINKS", ("sus_link", "link_in_text"))
                            subject = collection.find({},
                                                      {"Subject (Text)": 1, "Subject": 1, "Criterion (Utility)": 1, "_id": 0})
                            sender = collection.find({}, {"Sender (Text)": 1, "Sender": 1, "Criterion (Utility)": 1, "_id": 0})
                            branding = collection.find({}, {"Branding (Text)": 1, "Branding": 1, "Criterion (Utility)": 1,
                                                            "_id": 0})
                            design = collection.find({}, {"Design (Text)": 1, "Design": 1, "Criterion (Utility)": 1, "_id": 0})
                            spelling = collection.find({}, {"Spelling (Text)": 1, "Spelling": 1, "Criterion (Utility)": 1,
                                                            "_id": 0})
                            greeting = collection.find({}, {"Greeting (Text)": 1, "Greeting": 1, "Criterion (Utility)": 1,
                                                            "_id": 0})
                            time = collection.find({}, {"Time (Text)": 1, "Time": 1, "Criterion (Utility)": 1, "_id": 0})
                            threats = collection.find({},
                                                      {"Threats (Text)": 1, "Threats": 1, "Criterion (Utility)": 1, "_id": 0})
                            emotion = collection.find({},
                                                      {"Emotion (Text)": 1, "Emotion": 1, "Criterion (Utility)": 1, "_id": 0})
                            signer = collection.find({}, {"Signer (Text)": 1, "Signer": 1, "Criterion (Utility)": 1, "_id": 0})
                            toogood = collection.find({},
                                                      {"Toogood (Text)": 1, "Toogood": 1, "Criterion (Utility)": 1, "_id": 0})
                            requests = collection.find({}, {"Requests (Text)": 1, "Requests": 1, "Criterion (Utility)": 1,
                                                            "_id": 0})
                            links = dict()
                            for i in range(links_lower_bound, links_upper_bound):
                                links['link' + str(i)] = collection.find({},
                                                                         {"Hyperlink (Text) #" + str(i): 1,
                                                                          "Hyperlink: Link_In_Text #" + str(i): 1,
                                                                          "Hyperlink: Suspicious_Link #" + str(i): 1,
                                                                          "Criterion (Utility)": 1,
                                                                          "_id": 0})
                            for i in range(links_lower_bound, links_upper_bound):
                                for q in links['link' + str(i)]:
                                    if q['Hyperlink (Text) #' + str(i)] != "":
                                        if q['Hyperlink: Suspicious_Link #' + str(i)] == 0:
                                            for duplicate in range(duplicate_level):
                                                dm.add(
                                                    makechunk("link_chunk", "IDENTIFY_LINKS", str((q['Hyperlink (Text) #' + str(i)])),
                                                              q['Criterion (Utility)'],
                                                              link_in_text=q['Hyperlink: Link_In_Text #' + str(i)],
                                                              sus_link=q['Hyperlink: Suspicious_Link #' + str(i)]))
                                        else:
                                            dm.add(
                                                    makechunk("link_chunk", "IDENTIFY_LINKS", str((q['Hyperlink (Text) #' + str(i)])),
                                                              q['Criterion (Utility)'],
                                                              link_in_text=q['Hyperlink: Link_In_Text #' + str(i)],
                                                              sus_link=q['Hyperlink: Suspicious_Link #' + str(i)]))

                            for i in subject:
                                if i['Subject'] == 0:
                                    for duplicate in range(duplicate_level):
                                        dm.add(makechunk("subject_chunk", "IDENTIFY_EMAIL_SUBJECT", i['Subject (Text)'],
                                                         i['Criterion (Utility)'], subject=i['Subject']))
                                else:
                                    dm.add(makechunk("subject_chunk", "IDENTIFY_EMAIL_SUBJECT", i['Subject (Text)'],
                                                 i['Criterion (Utility)'], subject=i['Subject']))
                            for i in sender:
                                if i['Sender'] == 0:
                                    for duplicate in range(duplicate_level):
                                        dm.add(makechunk("sender_chunk", "IDENTIFY_SENDER_NAME", i['Sender (Text)'],
                                                 i['Criterion (Utility)'], sender=i['Sender']))
                                else:
                                    dm.add(makechunk("sender_chunk", "IDENTIFY_SENDER_NAME", i['Sender (Text)'],
                                                 i['Criterion (Utility)'], sender=i['Sender']))
                                
                            for i in branding:
                                if i['Branding'] == 0:
                                    for duplicate in range(duplicate_level):
                                        dm.add(makechunk("branding_chunk", "IDENTIFY_BRANDING_LOGOS", i['Branding (Text)'],
                                                 i['Criterion (Utility)'], branding=i['Branding']))
                                else:
                                    dm.add(makechunk("branding_chunk", "IDENTIFY_BRANDING_LOGOS", i['Branding (Text)'],
                                                 i['Criterion (Utility)'], branding=i['Branding']))

                            for i in design:
                                if i['Design'] == 0:
                                    for duplicate in range(duplicate_level):
                                        dm.add(makechunk("design_chunk", "IDENTIFY_POOR_DESIGN", i['Design (Text)'],
                                                 i['Criterion (Utility)'], design=i['Design']))
                                else:
                                    dm.add(makechunk("design_chunk", "IDENTIFY_POOR_DESIGN", i['Design (Text)'],
                                                 i['Criterion (Utility)'], design=i['Design']))

                            for i in spelling:
                                if i['Spelling'] == 0:
                                    for duplicate in range(duplicate_level):
                                        dm.add(makechunk("spelling_chunk", "IDENTIFY_GRAMMAR_ERROR", i['Spelling (Text)'],
                                                 i['Criterion (Utility)'], spelling=i['Spelling']))
                                else:
                                    dm.add(makechunk("spelling_chunk", "IDENTIFY_GRAMMAR_ERROR", i['Spelling (Text)'],
                                                 i['Criterion (Utility)'], spelling=i['Spelling']))
                                
                            for i in greeting:
                                if i['Greeting'] == 0:
                                    for duplicate in range(duplicate_level):
                                        dm.add(makechunk("greeting_chunk", "IDENTIFY_GENERIC_GREETING", i['Greeting (Text)'],
                                                 i['Criterion (Utility)'], greeting=i['Greeting'], ))
                                else:
                                    dm.add(makechunk("greeting_chunk", "IDENTIFY_GENERIC_GREETING", i['Greeting (Text)'],
                                                 i['Criterion (Utility)'], greeting=i['Greeting'], ))
                                
                            for i in time:
                                if i['Time'] == 0:
                                    for duplicate in range(duplicate_level):
                                        dm.add(makechunk("time_chunk", "IDENTIFY_TIME_PRESSURE", i['Time (Text)'],
                                                 i['Criterion (Utility)'], time=i['Time']))
                                else:
                                    dm.add(makechunk("time_chunk", "IDENTIFY_TIME_PRESSURE", i['Time (Text)'],
                                                 i['Criterion (Utility)'], time=i['Time']))
                                
                            for i in threats:
                                if i['Threats'] == 0:
                                    for duplicate in range(duplicate_level):
                                        dm.add(makechunk("threat_chunk", "IDENTIFY_THREAT_LANG", i['Threats (Text)'],
                                                 i['Criterion (Utility)'], threat=i['Threats']))
                                else:
                                    dm.add(makechunk("threat_chunk", "IDENTIFY_THREAT_LANG", i['Threats (Text)'],
                                                 i['Criterion (Utility)'], threat=i['Threats']))
                                
                            for i in emotion:
                                if i['Emotion'] == 0:
                                    for duplicate in range(duplicate_level):
                                        dm.add(makechunk("emotion_chunk", "IDENTIFY_EMOTION_APPEAL", i['Emotion (Text)'],
                                                 i['Criterion (Utility)'], emotion=i['Emotion']))
                                else:
                                    dm.add(makechunk("emotion_chunk", "IDENTIFY_EMOTION_APPEAL", i['Emotion (Text)'],
                                                 i['Criterion (Utility)'], emotion=i['Emotion']))
                                
                            for i in signer:
                                if i['Signer'] == 0:
                                    for duplicate in range(duplicate_level):
                                        dm.add(makechunk("signer_chunk", "IDENTIFY_SIGNER_DETAIL", i['Signer (Text)'],
                                                 i['Criterion (Utility)'], signer=i['Signer']))
                                else:
                                    dm.add(makechunk("signer_chunk", "IDENTIFY_SIGNER_DETAIL", i['Signer (Text)'],
                                                 i['Criterion (Utility)'], signer=i['Signer']))
                                
                            for i in toogood:
                                if i['Toogood'] == 0:
                                    for duplicate in range(duplicate_level):
                                        dm.add(makechunk("too_good_chunk", "IDENTIFY_TOO_GOOD", i['Toogood (Text)'],
                                                 i['Criterion (Utility)'], tg=i['Toogood']))
                                else:
                                    dm.add(makechunk("too_good_chunk", "IDENTIFY_TOO_GOOD", i['Toogood (Text)'],
                                                 i['Criterion (Utility)'], tg=i['Toogood']))
                                
                            for i in requests:
                                if i['Requests'] == 0:
                                    for duplicate in range(duplicate_level):
                                        dm.add(makechunk("request_chunk", "IDENTIFY_PERSONAL_REQ", i['Requests (Text)'],
                                                 i['Criterion (Utility)'], request=i['Requests']))
                                else:
                                    dm.add(makechunk("request_chunk", "IDENTIFY_PERSONAL_REQ", i['Requests (Text)'],
                                                 i['Criterion (Utility)'], request=i['Requests']))

                            while len(email_list) > 0:
                                choice = rchoice(email_list)
                                Email = collection.find().limit(-1).skip(choice).next()

                                Email_title = collection.find().limit(-1).skip(choice).next()['Email']
                                ProcessByEmail(Email, SUS_THRESHOLD, CUE_THRESHOLD, file, float("{0:0.1f}".format(fault_level)))
                                email_list.remove(choice)
                            file.write("Classification Results" + "\n")
                            file.write(classification.__repr__() + "\n")
                            file.write("Activation History: " + "\n")
                            # file.write(dm.__repr__())
                            pprint.pprint(dm.__repr__(), file)
                            file.close()
                            pprint.pprint(dm.__repr__())
                        os.system("python accuracy.py 1")
                        os.chdir("..")







