import matplotlib.pyplot as plt
import numpy as np
import os
import fnmatch
import collections
import statistics
from statistics import mean

keep_fname = "./keep.txt"
suspicious_fname = "./suspicious.txt"
csv_fname = "./results.csv"


# load suspicous
def load_suspicous():
    sl = list()
    suspicious_lines = open(suspicious_fname, 'r')
    for line in suspicious_lines:
        sl.append(line.rstrip('\r\n'))
    return set(sl)


# load keep
def load_keep():
    kl = list()
    keep_lines = open(keep_fname, 'r')
    for line in keep_lines:
        kl.append(line.rstrip('\r\n'))
    return set(kl)


def find(s, ch):
    return [i for i, ltr in enumerate(s) if ltr == ch]


def subfolder(folderpath, basepath):
    # data result for 100 users in one folder
    suspicious_set = load_suspicous()
    keep_set = load_keep()
    FPR = []
    FNR = []
    Distribution = []
    cue_per_user_all = []
    cue_per_user_susp = []
    cue_per_user_keep = []
    cue_per_user_susp_perception = []
    confidence_perception_susp = []
    confidence_perception_keep = []
    confidence_truth_susp = []
    confidence_truth_keep = []
    suspicion_counter_keep = []
    suspicion_counter_susp = []
    suspicion_counter_keep_perception = []

    # these might not be the best way to handle FNR and FPR
    # but I inherited all code drom 2018 and I do not have the brain to change it now
    # I will do that later (no I won't)
    correctness_all = list()
    correctness_susp = list()
    correctness_keep = list()

    # select all result files
    file_names = fnmatch.filter(os.listdir(folderpath), 'results*')
    print(file_names)
    for name in file_names:
        f = open(os.path.join(folderpath, name), "rt", encoding="utf-8")
        # data collected per user (in one result file)
        user_classification = dict()
        accuracy = dict()
        tn_count = 0
        tp_count = 0
        count = 0
        CUE_CHECKED_ALL = []
        CUE_CHECKED_SUSP = []
        CUE_CHECKED_KEEP = []
        CUE_CHECKED_SUSP_perception = []
        CONFIDENCE_SUSP_perception = []
        CONFIDENCE_KEEP_perception = []
        CONFIDENCE_SUSP_truth = []
        CONFIDENCE_KEEP_truth = []
        SUSPICION_KEEP = []
        SUSPICION_SUSP = []
        SUSPICION_KEEP_perception = []

        if not f:
            print("No such file!")
            exit()

        user_logs_lines = f.readlines()
        for line in user_logs_lines:
            # user perception: suspicious
            if line.find("<Classified>") != -1 and line.find("<Suspicious>") != -1:
                count = count + 1
                index_left_angle_bracket = find(line, "<")[1]
                index_right_angle_bracket = find(line, ">")[1]
                subject = line[index_left_angle_bracket:index_right_angle_bracket + 1]
                subject = subject
                user_classification[subject] = "suspicious"
                # print "\nsuspicious set:\n", suspicious_set
                # print "\nsubject\n", subject
                if subject in suspicious_set:
                    # print "1"
                    accuracy[subject] = "suspicious"

                level_index = line.find("sus_level")
                cues_index = line.find("cues")
                with_index = line[level_index:].find("with") + level_index
                suspicion_counter = line[level_index + 9:with_index]
                cues = line[level_index + 17:cues_index]
                CUE_CHECKED_SUSP_perception.append(int(cues))
                CONFIDENCE_SUSP_perception.append(int(suspicion_counter) / int(cues))

            # user perception: legit
            if line.find("<Classified>") != -1 and line.find("<Keep>") != -1:
                count = count + 1
                index_left_angle_bracket = find(line, "<")[1]
                index_right_angle_bracket = find(line, ">")[1]
                subject = line[index_left_angle_bracket:index_right_angle_bracket + 1]
                subject = subject
                user_classification[subject] = "keep"
                # print "\keep set:\n", keep_set
                # print "\nsubject\n", subject
                if subject in keep_set:
                    # print "2"
                    accuracy[subject] = "keep"

                level_index = line.find("sus_level")
                cues_index = line.find("cues")
                with_index = line[level_index:].find("with") + level_index
                suspicion_counter = line[level_index + 9:with_index]
                SUSPICION_KEEP_perception.append(int(suspicion_counter))
                cues = line[level_index + 17:cues_index]
                CONFIDENCE_KEEP_perception.append(int(suspicion_counter) / int(cues))

            # ground truth
            if line.find("with") != -1 and line.find("cues") != -1:
                level_index = line.find("sus_level")
                cues_index = line.find("cues")
                with_index = line[level_index:].find("with") + level_index
                suspicion_counter = line[level_index + 9:with_index]
                cues = line[level_index + 17:cues_index]
                # print("-----cues-----", level_index,"-----", with_index,"-----", suspicion_counter)
                CUE_CHECKED_ALL.append(int(cues))
                if subject in suspicious_set:
                    CUE_CHECKED_SUSP.append(int(cues))
                    # ground truth: suspicious
                    SUSPICION_SUSP.append(int(suspicion_counter))
                    CONFIDENCE_SUSP_truth.append(int(suspicion_counter) / int(cues))

                if subject in keep_set:
                    CUE_CHECKED_KEEP.append(int(cues))
                    # ground truth: legit
                    SUSPICION_KEEP.append(int(suspicion_counter))
                    CONFIDENCE_KEEP_truth.append(int(suspicion_counter) / int(cues))
                    # print("-------suspicious-------", suspicion_counter, "-----cues--------", cues)

        for sbj, cls in accuracy.items():
            if cls == "keep":
                tn_count = tn_count + 1

        for sbj, cls in accuracy.items():
            if cls == "suspicious":
                tp_count = tp_count + 1

        if len(user_classification) == 40:
            FPR.append((20 - tn_count) / 20.0)
            FNR.append((20 - tp_count) / 20.0)
            correctness_all.append((tp_count + tn_count) / 40.0)
            correctness_susp.append(tp_count / 20.0)
            correctness_keep.append(tn_count / 20.0)
            # if count > 40:
            #     print(name)
        if CUE_CHECKED_ALL != []:
            cue_per_user_all.append(sum(CUE_CHECKED_ALL) / len(CUE_CHECKED_ALL))
        if CUE_CHECKED_SUSP != []:
            cue_per_user_susp.append(sum(CUE_CHECKED_SUSP) / len(CUE_CHECKED_SUSP))
        if CUE_CHECKED_KEEP != []:
            cue_per_user_keep.append(sum(CUE_CHECKED_KEEP) / len(CUE_CHECKED_KEEP))
        if CONFIDENCE_SUSP_perception != []:
            cue_per_user_susp_perception.append(sum(CUE_CHECKED_SUSP_perception) / len(CUE_CHECKED_SUSP_perception))
        # print("-----keep perception-----", CONFIDENCE_KEEP_perception)
        if CONFIDENCE_SUSP_perception != []:
            confidence_perception_susp.append(sum(CONFIDENCE_SUSP_perception) / len(CONFIDENCE_SUSP_perception))
        # NOTICE: keep could be empty
        if CONFIDENCE_KEEP_perception != []:
            confidence_perception_keep.append(sum(CONFIDENCE_KEEP_perception) / len(CONFIDENCE_KEEP_perception))

        if CONFIDENCE_SUSP_truth != []:
            confidence_truth_susp.append(sum(CONFIDENCE_SUSP_truth) / len(CONFIDENCE_SUSP_truth))
        # NOTICE: keep could be empty
        if CONFIDENCE_KEEP_truth != []:
            confidence_truth_keep.append(sum(CONFIDENCE_KEEP_truth) / len(CONFIDENCE_KEEP_truth))

        if SUSPICION_KEEP != []:
            suspicion_counter_keep.append(sum(SUSPICION_KEEP) / len(SUSPICION_KEEP))

        if SUSPICION_SUSP != []:
            suspicion_counter_susp.append(sum(SUSPICION_SUSP) / len(SUSPICION_SUSP))

        if SUSPICION_KEEP_perception != []:
            suspicion_counter_keep_perception.append(sum(SUSPICION_KEEP_perception) / len(SUSPICION_KEEP_perception))

    # print("1. cue_per_user_all, ", mean(cue_per_user_all))
    # print("2. cue_per_user_susp (Tp), ", mean(cue_per_user_susp))
    # print("3. cue_per_user_keep (Tn), ", mean(cue_per_user_keep))
    # print("4. cue_per_user_susp_perception (Tp_perception), ", mean(cue_per_user_susp_perception))
    # print("5. confidence_per_user_susp (cRn_truth): ", mean(confidence_truth_susp))
    # print("6. confidence_per_user_keep (cRp_truth): ", mean(confidence_truth_keep))
    # print("7. confidence_per_user_susp_perception (cRn_perception) ", mean(confidence_perception_susp))
    # print("8. confidence_per_user_keep_perception (cRp_perception): ", mean(confidence_perception_keep))
    # print("9. suspicion_counter_keep, ", mean(suspicion_counter_keep))
    # print("10. suspicion_counter_susp, ", mean(suspicion_counter_susp))
    # print("11. suspicion_counter_keep_perception, ", mean(suspicion_counter_keep_perception))

    last_dir = os.path.basename(folderpath)
    num_cue_processed, suspicion_threshold, similarity_weight, fault_level = last_dir.split('_')

    '''

    plt.title('Inverse Confidence Rating of '+ last_dir + "(perception based)")
    plt.xlabel("users")
    plt.ylabel("confidence (susp/cues_checked)")
    plt.plot(range(100), confidence_perception_susp, label="confidence of phishing emails")
    #plt.plot(range(100), confidence_perception_keep, label="confidence of legitimate emails")
    plt.legend()
    plt.savefig("confidence.png")
    #plot.show()

    #plt.plot(range(100), cue_per_user_all, label="average time of all")
    plt.plot(range(100), cue_per_user_susp, label="average time on phishing emails")
    plt.plot(range(100), cue_per_user_keep, label="average time on legit emails")
    plt.legend()
    plt.savefig("time.png")
    #plt.show()

    plt.title('Tn and TP Graph of '+ last_dir)
    plt.xlabel("users")
    plt.ylabel("average time spent")

    #plt.plot(range(100), cue_per_user_all, label="average time of all")
    plt.plot(range(100), cue_per_user_susp, label="average time on phishing emails")
    plt.plot(range(100), cue_per_user_keep, label="average time on legit emails")
    plt.legend()
    plt.savefig("time.png")
    plt.show()

    print("12. FNR: ", mean(FNR))
    print("13. FPR: ", mean(FPR))
    for i in range(0, len(FNR)):
        Distribution.append((FNR[i], FPR[i]))
    # print(Distribution)
    c = collections.Counter(Distribution)
    # print(c)
    # print(c[(0.5, 0.0)])
    num = len(FNR)
    for i in Distribution:
        plt.scatter(i[0], i[1], alpha=0.90)
    ax = plt.gca()
    ax.set_aspect(1)

    p = np.linspace(0, 1, 100)
    q = 0.1 - p
    plt.plot(p, q)

    p = np.linspace(0, 1, 100)
    q = 0.2 - p
    plt.plot(p, q)

    p = np.linspace(0, 1, 100)
    q = 0.3 - p
    plt.plot(p, q)

    p = np.linspace(0, 1, 100)
    q = 0.4 - p
    plt.plot(p, q)

    p = np.linspace(0, 1, 100)
    q = 0.45 - p
    plt.plot(p, q)

    p = np.linspace(0, 1, 100)
    q = 0.5 - p
    plt.plot(p, q)

    p = np.linspace(0, 1, 100)
    q = 0.6 - p
    plt.plot(p, q)

    p = np.linspace(0, 1, 100)
    q = 0.7 - p
    plt.plot(p, q)

    p = np.linspace(0, 1, 100)
    q = 0.8 - p
    plt.plot(p, q)

    p = np.linspace(0, 1, 100)
    q = 0.9 - p
    plt.plot(p, q)

    p = np.linspace(0, 1, 100)
    q = 1.0 - p
    plt.plot(p, q)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.ylabel('FNR - Identify phishing as legitimate')
    plt.xlabel('FPR - Identify legitimate as phishing ')
    plt.title('FNR-FNP Graph of '+ last_dir)


    plt.text(1.0, 0.0, str(' Stddev='+str(statistics.stdev(FPR))),
             fontsize=10)
    plt.text(1.0, 0.05, str(' FPR='+str(sum(FPR) / len(FPR))),
             fontsize=10)
    plt.text(1.0, 0.1, str(' Stddev='+str(statistics.stdev(FNR))),
             fontsize=10)
    plt.text(1.0, 0.15, str(' FNR='+str(sum(FNR) / len(FNR))),
             fontsize=10)
    plt.text(1.0, 0.2, str(' Stddev='+str(statistics.stdev(correctness_all))),
             fontsize=10)
    plt.text(1.0, 0.25, str(' Accuracy (all)='+str(sum(correctness_all) / len(correctness_all))),
             fontsize=10)
    plt.text(1.0, 0.3, str(' Stddev='+str(statistics.stdev(cue_per_user_all))),
             fontsize=10)
    plt.text(1.0, 0.35, str(' Cues (all)='+str(sum(cue_per_user_all) / len(cue_per_user_all))),
             fontsize=10)
    plt.text(1.0, 0.4, str(' Stddev='+str(statistics.stdev(correctness_keep))),
             fontsize=10)
    plt.text(1.0, 0.45, str(' Accuracy (keep)='+str(sum(correctness_keep) / len(correctness_keep))),
             fontsize=10)
    plt.text(1.0, 0.5, str(' Stddev='+str(statistics.stdev(cue_per_user_keep))),
             fontsize=10)
    plt.text(1.0, 0.55, str(' Cues (keep)='+str(sum(cue_per_user_keep) / len(cue_per_user_keep))),
             fontsize=10)
    plt.text(1.0, 0.6, str(' Stddev='+str(statistics.stdev(correctness_susp))),
             fontsize=10)
    plt.text(1.0, 0.65, str(' Accuracy (susp)='+str(sum(correctness_susp) / len(correctness_susp))),
             fontsize=10)
    plt.text(1.0, 0.7, str(' Stddev='+str(statistics.stdev(cue_per_user_susp))),
             fontsize=10)
    plt.text(1.0, 0.75, str(' Cues (susp)='+str(sum(cue_per_user_susp) / len(cue_per_user_susp))),
             fontsize=10)

    for i in c:
        plt.text(i[0], i[1], c[i])
        print(i)
        print(c[i])

    plt.savefig('accuracy.png')
    # plt.show()


    print(FPR)
    print(len(FPR))
    print(sum(FPR) / len(FPR))
    print(FNR)
    print(len(FNR))
    print(sum(FNR) / len(FNR))
    print(correctness_all)
    print(len(correctness_all))
    print(sum(correctness_all) / len(correctness_all))
    '''

    result_file = open(csv_fname, 'a')
    result_file.write(','.join((num_cue_processed, suspicion_threshold, similarity_weight, fault_level,
                                str(mean(cue_per_user_all)), str(mean(cue_per_user_susp)),
                                str(mean(cue_per_user_keep)), str(mean(cue_per_user_susp_perception)),
                                str(mean(FNR)), str(mean(FPR)),
                                str(mean(confidence_truth_susp)), str(mean(confidence_truth_keep)),
                                str(mean(confidence_perception_susp)), str(mean(confidence_perception_keep)),
                                str(mean(suspicion_counter_keep)), str(mean(suspicion_counter_susp)),
                                str(mean(suspicion_counter_keep_perception))
                                )))
    result_file.write('\n')
    result_file.close()


rootdir = '.'
rootdir_absolute = os.path.abspath(rootdir)
subdir = [f.path for f in os.scandir(rootdir) if f.is_dir()]
for folders in subdir:
    subfolder(folders, rootdir_absolute)