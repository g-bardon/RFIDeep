"""
    Function used to correct missing detections
"""


from mysql_queries.queries_info import *
import copy
import datetime
import time
import pandas as pd
import numpy as np
from tools.tools import *

def define_distribution(date_before, date_after):
    """
    :param tim_par: the time before the filling gap
    :return: the higher probability of the time
    """
    year = date_before.year
    if datetime.datetime(year, 1, 15) < date_before < datetime.datetime(year, 8, 1):
        temp = abs((int(round(date_before.timestamp()))) - int(round(date_after.timestamp())))
        temp = temp/2 + time.mktime(date_before.timetuple())
        new_time = datetime.datetime.fromtimestamp(temp)
    else:
        temp = abs((int(round(date_before.timestamp()))) - int(round(date_after.timestamp())))
        temp = temp / 2 + time.mktime(date_before.timetuple())
        new_time = datetime.datetime.fromtimestamp(temp)
    return new_time


def define_gate(rfid, bd):
    """
    :param rfid: rfid of the bird
    :return: the gate (sea side, for example 1 or 4 or 7 at ddu) with the highest probability (based on habits)
    """
    gate_all = get_list_antennas(rfid)

    if 'ddu' in bd and gate_all:
        gate = [1, 4, 7]
        gate_count_13 = gate_all.count(1) + gate_all.count(3)
        gate_count_46 = gate_all.count(4) + gate_all.count(6)
        gate_count_79 = gate_all.count(7) + gate_all.count(9)
        habit_gate = [gate_count_13, gate_count_46, gate_count_79]
        i = habit_gate.index(max(habit_gate))

    elif 'cro' in bd and gate_all:
        gate = [1, 3, 5, 7]
        gate_count_12 = gate_all.count(1) + gate_all.count(2)
        gate_count_34 = gate_all.count(3) + gate_all.count(4)
        gate_count_56 = gate_all.count(5) + gate_all.count(6)
        gate_count_78 = gate_all.count(7) + gate_all.count(8)
        habit_gate = [gate_count_12, gate_count_34, gate_count_56, gate_count_78]
        i = habit_gate.index(max(habit_gate))

    else:
        gate = [0]
        i = 0

    return gate[i]


def convert_clean_data(data, bd):
    """
    :param data: database that come from the query
    :return: clean and list (format) the same database
    """

    new_data = copy.deepcopy(data)
    # convert all way from sea in 0 and all way from earth in 1
    if 'ddu' in bd:
        for i in range(len(new_data)):
            if (new_data[i][2]) in [3,6,9]:
                new_data[i][2] = 1
            else:
                new_data[i][2] = 0

    elif 'cro' in bd:
        for i in range(len(new_data)):
            if (new_data[i][2]) in [2,4,6,8]:
                new_data[i][2] = 1
            else:
                new_data[i][2] = 0
    else:
        new_data = []
    return new_data


def transition_fun(data, bd):
    """
    :param data: list of the detections of the bird for the season
    :param bd: database
    :return: the list composed of the departure, time and arrival of the birds (binary, 0 or 1)
    """
    # Init
    x = []
    temp = []
    if 'ddu' in bd:
        time_estimated = 300  # time we estimate for a penguin to get through a gate (5 mns)
    elif 'cro' in bd:
        time_estimated = 600  # time we estimate for a penguin to get through a gate (10 mns)
    else:
        time_estimated = 3

    # Convert the datetime in s, if datetime object doesnt exist we take the nearest value
    for z in range(len(data)):
        if data[z][1] is not None:
            temp.append(int(round(data[z][1].timestamp())))
        elif data[z+1][1] is None:
            v = datetime.datetime(2015,2,24,11,0,0)
            data[z][1] = v
            temp.append(int(round(v.timestamp())))
            x.append([data[z][2], data[z][0], v, "logical"])
        elif data[z-1][1] is None:
            y = datetime.datetime(2015,2,24,11,0,0) + datetime.timedelta(milliseconds=3000)
            data[z][1] = y
            temp.append(int(round(y.timestamp())))
            x.append([data[z][2], data[z][0], y, "logical"])
        else:
            w = (data[z + 1][1] - datetime.timedelta(milliseconds=3000))
            data[z][1] = w
            temp.append(int(round(w.timestamp())))
            x.append([data[z][2], data[z][0], w, "logical"])

    transit = [[0] * 3 for _ in range(len(data))]
    transit_length = [0 for _ in range(len(data))]
    for z in range(len(data) - 1):
        transit_length[z] = data[z+1][1].timestamp()-data[z][1].timestamp()
        # if the bird is coming from sea (0) to earth (1)
        if (data[z][2] - data[z + 1][2]) < 0:
            transit[z][0] = 0
            transit[z][2] = 1

            # if the bird is coming from earth to sea
        elif (data[z][2] - data[z + 1][2]) > 0:
            transit[z][0] = 1
            transit[z][2] = 0

        elif (data[z][2] - data[z + 1][2]) == 0:
            # if the bird is coming from sea to sea
            if (data[z][2]) == 0:
                transit[z][0] = 0
                transit[z][2] = 0

            # if the bird is coming from earth to earth
            elif (data[z][2]) == 1:
                transit[z][0] = 1
                transit[z][2] = 1

        # if the time is short (0) or long (1)
        if (temp[z + 1] - temp[z]) <= time_estimated:
            transit[z][1] = 0
        else:
            transit[z][1] = 1

    return transit, x, transit_length


def binary_fun(vect):
    """
    :param vect: list of the transition
    :return: the list of 3bit coming from transition
    """
    sum = [[0] * 1 for _ in range(len(vect))]

    for i in range(len(vect)):
        sum[i] = vect[i][0] * 4 + vect[i][1] * 2 + vect[i][2]
    return sum

def repair_missing_data(list, data_list, rfid, bd):
    gap = copy.deepcopy(list)

    gate = define_gate(rfid, bd)

    if 'ddu' in bd:
        diff_gate = 2  # diff between gate 1 and gate 2
    elif 'cro' in bd:
        diff_gate = 1  # diff between gate 1 and gate 2
    else:
        diff_gate = 0

    comp = len(gap)
    index_of_transition = [i for i in range(comp)]  # here we register the index of the the transition in the data_list before removing the 0 and 5 transitions

    x = 0
    # Here we remove the short transition "terre-terre" and "mer-mer" because it corresponds to a double detection
    while x < comp:
        if gap[x] == 0 or gap[x] == 5:
            del gap[x]
            del index_of_transition[x]  ## for the transition gap[i], we have date and gate information in data_list[index_of_transition[i]]
            comp = comp - 1
            x = x - 1
        x = x + 1


    data_rebuild = [] # the detections that we add
    i=2
    while i < comp - 5 : #stop 5 detections before the end to avoid border issues

        # 161
        if gap[i] == 6 and gap[i-1] == 1 and gap[i+1] == 1:
            # correction of transition list
            gap[i] = 7
            gap.insert(i + 1, 4)
            gap.insert(i + 2, 2)

            # Adding of missing detections

            data_rebuild.append(
                [gate + diff_gate, rfid,
                 define_distribution(data_list[index_of_transition[i - comp]][1], ##we take into account the new transitions that was previously added
                                     data_list[index_of_transition[i - comp] + 1][1]), 'probabilistic'])
            data_rebuild.append(
                [gate, rfid, data_rebuild[-1][2] + datetime.timedelta(
                    milliseconds=3000), 'probabilistic'])
            comp += 2  ## 2 new transitions

        # 162
        elif gap[i] == 6 and gap[i - 1] == 1 and gap[i + 1] == 2:
            gap[i] = 7
            gap.insert(i + 1, 4)

            data_rebuild.append(
                [data_list[index_of_transition[i-comp] + 1][2] + diff_gate, rfid,
                 data_list[index_of_transition[i-comp] + 1][1] - datetime.timedelta(
                     milliseconds=3000), 'logical'])
            comp = comp + 1

        # 163 we correct only the 6
        elif gap[i] == 6 and gap[i - 1] == 1 and gap[i + 1] == 3:
            gap[i] = 7
            gap.insert(i + 1, 4)

            data_rebuild.append(
                [data_list[index_of_transition[i-comp] + 1][2] + diff_gate, rfid,
                 data_list[index_of_transition[i-comp] + 1][1] - datetime.timedelta(
                     milliseconds=3000), 'logical'])
            comp = comp + 1
        # 234
        elif gap[i] == 3 and gap[i - 1] == 2 and gap[i + 1] == 4:
            gap[i] = 1
            gap.insert(i + 1, 7)
            data_rebuild.append(
                [data_list[index_of_transition[i-comp]][2] + diff_gate, rfid,
                 data_list[index_of_transition[i-comp]][1] + datetime.timedelta(
                     milliseconds=3000), 'logical'])
            comp = comp + 1

        # 236
        elif gap[i] == 3 and gap[i - 1] == 2 and gap[i + 1] == 6:
            gap[i] = 1
            gap.insert(i + 1, 7)
            gap[i+2] = 4
            gap.insert(i+3,2)

            data_rebuild.append(
                [data_list[index_of_transition[i-comp]][2] + diff_gate, rfid,
                 data_list[index_of_transition[i-comp]][1] + datetime.timedelta(
                     milliseconds=3000), 'logical'])
            data_rebuild.append(
                [data_list[index_of_transition[i + 1-comp]][2] - diff_gate, rfid,
                 data_list[index_of_transition[i + 1-comp]][1] + datetime.timedelta(
                     milliseconds=3000), 'logical'])
            comp = comp + 2

        # 434
        elif gap[i] == 3 and gap[i - 1] == 4 and gap[i + 1] == 4:
            gap[i] = 2
            gap.insert(i + 1, 1)
            gap.insert(i + 2, 7)

            data_rebuild.append(
                [gate, rfid, define_distribution(data_list[index_of_transition[i-comp]][1],
                                                 data_list[index_of_transition[i-comp] + 1][1]), 'probabilistic'])
            data_rebuild.append(
                [gate + diff_gate, rfid, data_rebuild[-1][2] + datetime.timedelta(
                    milliseconds=3000), 'probabilistic'])
            comp = comp + 2

        # 436
        elif gap[i] == 3 and gap[i - 1] == 4 and gap[i + 1] == 6:
            gap[i] = 2
            gap.insert(i + 1, 1)

            data_rebuild.append(
                [data_list[index_of_transition[i-comp] + 1][2] - diff_gate, rfid,
                 data_list[index_of_transition[i-comp] + 1][1] - datetime.timedelta(
                     milliseconds=3000), 'logical'])
            comp = comp + 1

        # 437
        elif gap[i] == 3 and gap[i - 1] == 4 and gap[i + 1] == 7:
            gap[i] = 2
            gap.insert(i + 1, 1)

            data_rebuild.append(
                [data_list[index_of_transition[i-comp] + 1][2] - diff_gate, rfid,
                 data_list[index_of_transition[i-comp] + 1][1] - datetime.timedelta(
                     milliseconds=3000), 'logical'])
            comp = comp + 1

        # 761
        elif gap[i] == 6 and gap[i - 1] == 7 and gap[i + 1] == 1 :
            gap[i] = 4
            gap.insert(i + 1, 2)

            data_rebuild.append(
                [data_list[index_of_transition[i-comp]][2] - diff_gate, rfid,
                 data_list[index_of_transition[i-comp]][1] + datetime.timedelta(
                     milliseconds=3000), 'logical'])
            comp = comp + 1

        # 763
        elif gap[i] == 6 and gap[i - 1] == 7 and gap[i + 1] == 3:
            gap[i] = 4
            gap.insert(i + 1, 2)
            gap[i+2] = 1
            gap.insert(i+3, 7)

            data_rebuild.append(
                [data_list[index_of_transition[i-comp]][2] - diff_gate, rfid,
                 data_list[index_of_transition[i-comp]][1] + datetime.timedelta(
                     milliseconds=3000), 'logical'])
            data_rebuild.append(
                [data_list[index_of_transition[i + 1 - comp]][2] + diff_gate, rfid,
                 data_list[index_of_transition[i + 1 - comp]][1] + datetime.timedelta(
                     milliseconds=3000), 'logical'])
            comp = comp + 2

        # successives 2
        elif gap[i] == 2 and gap[i+1] == 2:
            j = 0
            while i+j+1 <= comp-3 and gap[i+j] == gap[i+j+1]: ## count number of successives 2 and stop if it is at the end of the transition list
                j=j+1
            if i+j+1 == comp:
                break # don't repair successives 2-2 if it is at the end

            if j % 2 == 0: ## j even number so odd numbers of successives 2 transitions
                if gap[i - 1] == 6 and gap[i +j +1] == 1: # 6-2-2-2-1
                    gap[i-1] = 7
                    del gap[i:i+j+1]
                    gap[i:i] = [4,2,1,7] * (j//2) + [4,2]

                    data_rebuild.append(
                        [data_list[index_of_transition[i - 1 - comp] + 1][2] + diff_gate, rfid,
                         data_list[index_of_transition[i - 1 - comp] + 1][1] - datetime.timedelta(
                             milliseconds=3000), 'logical'])
                    for k in range(1, j // 2 + 1):
                        data_rebuild.append(
                            [data_list[index_of_transition[i + 2 * k -1- comp]][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + 2 * k -1- comp]][1] + datetime.timedelta(
                                 milliseconds=3000), 'logical'])
                        data_rebuild.append(
                            [data_list[index_of_transition[i + 2 * k -1- comp] + 1][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + 2 * k -1- comp] + 1][1] - datetime.timedelta(
                                 milliseconds=3000), 'logical'])
                    comp += 1 + j

                elif gap[i-1] == 4 and gap[i +j +1] == 3: # 4-2-2-2-3
                    del gap[i+1:i+j+2]
                    gap[i+1:i+1] = [1,7,4,2] * (j//2) + [1,7]

                    for k in range(0,(j//2)):
                        data_rebuild.append(
                            [data_list[index_of_transition[i + k*2 +1- comp]][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + k*2 +1- comp]][1] + datetime.timedelta(
                                 milliseconds=3000), 'logical'])
                        data_rebuild.append(
                            [data_list[index_of_transition[i + k*2 +1- comp]+1][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + k*2 +1- comp]+1][1] - datetime.timedelta(
                                 milliseconds=3000), 'logical'])
                    data_rebuild.append(
                        [data_list[index_of_transition[i + j +1- comp]][2] + diff_gate, rfid,
                         data_list[index_of_transition[i + j +1- comp]][1] + datetime.timedelta(
                             milliseconds=3000), 'logical'])
                    comp += j + 1

                elif gap[i-1] == 6 and gap[i +j +1] == 3: # 6-2-2-2-3
                    del gap[i-1:i+j+2]
                    gap[i-1:i-1] = [4,2,1,7]*((j//2)+1)+[4,2,1]

                    data_rebuild.append(
                        [data_list[index_of_transition[i-1-comp]][2] - diff_gate, rfid,
                         data_list[index_of_transition[i-1-comp]][1] + datetime.timedelta(
                             milliseconds=3000), 'logical'])
                    for k in range(0, j // 2 + 1):
                        data_rebuild.append(
                            [data_list[index_of_transition[i + 2 * k -comp]][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + 2 * k -comp]][1] + datetime.timedelta(
                                 milliseconds=3000), 'logical'])
                        data_rebuild.append(
                            [data_list[index_of_transition[i + 2 * k -comp] + 1][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + 2 * k -comp] + 1][1] - datetime.timedelta(
                                 milliseconds=3000), 'logical'])

                    data_rebuild.append(
                        [data_list[index_of_transition[i + j + 1 - comp] + 1][2] - diff_gate, rfid,
                         data_list[index_of_transition[i + j + 1 - comp] + 1][1] - datetime.timedelta(
                             milliseconds=3000), 'logical'])
                    comp += j + 4

                elif gap[i-1] == 4 and gap[i +j +1] == 1: # 4-2-2-2-1
                    del gap[i+1:i + j + 1]
                    gap[i +1:i + 1] = [1,7,4,2] * (j//2)

                    for k in range(0,(j//2)):
                        data_rebuild.append(
                            [data_list[index_of_transition[i + k*2 +1- comp]][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + k*2 +1- comp]][1] + datetime.timedelta(
                                 milliseconds=3000), 'logical'])
                        data_rebuild.append(
                            [data_list[index_of_transition[i + k*2 +1- comp]+1][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + k*2 +1- comp]+1][1] - datetime.timedelta(
                                 milliseconds=3000), 'logical'])
                    comp += j

            else:## j odd number so even number of successives 2 transitions
                if gap[i - 1] == 6 and gap[i + j + 1] == 1:
                    gap[i-1] = 4
                    del gap[i:i+j+1]
                    gap[i:i] = [2,1,7,4] * ((j//2)+1) + [2]

                    data_rebuild.append(
                        [data_list[index_of_transition[i-1-comp]][2] - diff_gate, rfid,
                         data_list[index_of_transition[i-1-comp]][1] + datetime.timedelta(
                             milliseconds=3000), 'logical'])
                    for k in range(0, (j + 1) // 2):
                        data_rebuild.append(
                            [data_list[index_of_transition[i + 2 * k - comp]][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + 2 * k - comp]][1] + datetime.timedelta(
                                 milliseconds=3000), 'logical'])
                        data_rebuild.append(
                            [data_list[index_of_transition[i + 2 * k - comp] + 1][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + 2 * k - comp] + 1][1] - datetime.timedelta(
                                 milliseconds=3000), 'logical'])
                    comp += 2 + j


                elif gap[i - 1] == 4 and gap[i + j + 1] == 3 and gap[i + j + 2] != 4:
                    del gap[i+1:i+j+2]
                    gap[i+1:i+1] = [1,7,4,2]*((j//2)+1)+[1]

                    for k in range((j+1)//2):
                        data_rebuild.append(
                            [data_list[index_of_transition[i + k * 2 + 1 - comp]][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + k * 2 + 1 - comp]][1] + datetime.timedelta(
                                 milliseconds=3000), 'logical'])
                        data_rebuild.append(
                            [data_list[index_of_transition[i + k * 2 + 1 - comp] + 1][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + k * 2 + 1 - comp] + 1][1] - datetime.timedelta(
                                 milliseconds=3000), 'logical'])
                    data_rebuild.append(
                        [data_list[index_of_transition[i + j + 1 - comp]+1][2] - diff_gate, rfid,
                         data_list[index_of_transition[i + j + 1 - comp]+1][1] - datetime.timedelta(
                             milliseconds=3000), 'logical'])

                    comp += j + 2

                elif gap[i - 1] == 6 and gap[i + j + 1] == 3:
                    # normally always a 7 before as already corrected
                    del gap[i-1:i+j+2]
                    gap[i-1:i-1] = [4,2,1,7] * ((j//2)+2)

                    data_rebuild.append(
                        [data_list[index_of_transition[i-1-comp]][2] - diff_gate, rfid,
                         data_list[index_of_transition[i-1-comp]][1] + datetime.timedelta(
                             milliseconds=3000), 'logical'])
                    for k in range(0, (j + 1) // 2):
                        data_rebuild.append(
                            [data_list[index_of_transition[i + 2 * k-comp]][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + 2 * k-comp]][1] + datetime.timedelta(
                                 milliseconds=3000), 'logical'])
                        data_rebuild.append(
                            [data_list[index_of_transition[i + 2 * k-comp] + 1][2] + diff_gate, rfid,
                             data_list[index_of_transition[i + 2 * k-comp] + 1][1] - datetime.timedelta(
                                 milliseconds=3000), 'logical'])

                    data_rebuild.append(
                        [data_list[index_of_transition[i + j + 1-comp]][2] + diff_gate, rfid,
                         data_list[index_of_transition[i + j + 1-comp]][1] + datetime.timedelta(
                             milliseconds=3000), 'logical'])

                    comp += j+3

                ## we not repair if it is 4-2-2-1 because we don't know what transition is false

            # successives 7
        elif gap[i] == 7 and gap[i + 1] == 7:
            j = 0
            while i + j + 1 <= comp-3 and gap[i + j] == gap[i + j + 1] :  ## count number of successives 7 and stop if it is at the end of the transition list
                j = j + 1
            if i+j+1 == comp:
                break # don't repair successives 7-7 if it is at the end

            if j % 2 == 0:  ## j even number so odd numbers of successives 2 transitions
                if gap[i - 1] == 3 and gap[i + j + 1] == 4:  # 3-7-7-7-4
                    gap[i - 1] = 2
                    del gap[i:i + j + 1]
                    gap[i:i] = [1, 7, 4, 2] * (j // 2) + [1, 7]

                    data_rebuild.append(
                        [data_list[index_of_transition[i - 1 - comp] + 1][2] - diff_gate, rfid,
                            data_list[index_of_transition[i - 1 - comp] + 1][1] - datetime.timedelta(
                                milliseconds=3000), 'logical'])
                    for k in range(1, j // 2 + 1):
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + 2 * k - 1 - comp]][2] - diff_gate, rfid,
                                     data_list[index_of_transition[i + 2 * k - 1 - comp]][1] + datetime.timedelta(
                                         milliseconds=3000), 'logical'])
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + 2 * k - 1 - comp] + 1][2] - diff_gate,
                                     rfid,
                                     data_list[index_of_transition[i + 2 * k - 1 - comp] + 1][
                                         1] - datetime.timedelta(
                                         milliseconds=3000), 'logical'])
                    comp += 1 + j

                elif gap[i - 1] == 1 and gap[i + j + 1] == 6:  # 1-7-7-7-6
                    del gap[i + 1:i + j + 2]
                    gap[i + 1:i + 1] = [4, 2, 1, 7] * (j // 2) + [4, 2]

                    for k in range(0, (j // 2)):
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + k * 2 + 1 - comp]][2] - diff_gate, rfid,
                                     data_list[index_of_transition[i + k * 2 + 1 - comp]][1] + datetime.timedelta(
                                         milliseconds=3000), 'logical'])
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + k * 2 + 1 - comp] + 1][2] - diff_gate,
                                     rfid,
                                     data_list[index_of_transition[i + k * 2 + 1 - comp] + 1][
                                         1] - datetime.timedelta(
                                         milliseconds=3000), 'logical'])
                    data_rebuild.append(
                                [data_list[index_of_transition[i + j + 1 - comp]][2] - diff_gate, rfid,
                                 data_list[index_of_transition[i + j + 1 - comp]][1] + datetime.timedelta(
                                     milliseconds=3000), 'logical'])
                    comp += j + 1

                elif gap[i - 1] == 3 and gap[i + j + 1] == 6:  # 3-7-7-7-6
                    del gap[i - 1:i + j + 2]
                    gap[i - 1:i - 1] = [1, 7, 4, 2] * ((j // 2) + 1) + [1, 7, 4]

                    data_rebuild.append(
                                [data_list[index_of_transition[i - 1 - comp]][2] + diff_gate, rfid,
                                 data_list[index_of_transition[i - 1 - comp]][1] + datetime.timedelta(
                                     milliseconds=3000), 'logical'])
                    for k in range(0, j // 2 + 1):
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + 2 * k - comp]][2] - diff_gate, rfid,
                                     data_list[index_of_transition[i + 2 * k - comp]][1] + datetime.timedelta(
                                         milliseconds=3000), 'logical'])
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + 2 * k - comp] + 1][2] - diff_gate, rfid,
                                     data_list[index_of_transition[i + 2 * k - comp] + 1][1] - datetime.timedelta(
                                         milliseconds=3000), 'logical'])

                    data_rebuild.append(
                                [data_list[index_of_transition[i + j + 1 - comp] + 1][2] + diff_gate, rfid,
                                 data_list[index_of_transition[i + j + 1 - comp] + 1][1] - datetime.timedelta(
                                     milliseconds=3000), 'logical'])
                    comp += j + 4

                elif gap[i - 1] == 1 and gap[i + j + 1] == 4:  # 1-7-7-7-4
                    del gap[i + 1:i + j + 1]
                    gap[i + 1:i + 1] = [4, 2, 1, 7] * (j // 2)

                    for k in range(0, (j // 2)):
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + k * 2 + 1 - comp]][2] - diff_gate, rfid,
                                     data_list[index_of_transition[i + k * 2 + 1 - comp]][1] + datetime.timedelta(
                                         milliseconds=3000), 'logical'])
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + k * 2 + 1 - comp] + 1][2] - diff_gate,
                                     rfid,
                                     data_list[index_of_transition[i + k * 2 + 1 - comp] + 1][
                                         1] - datetime.timedelta(
                                         milliseconds=3000), 'logical'])
                    comp += j

            else:  ## j odd number so even number of successives 2 transitions
                if gap[i - 1] == 3 and gap[i + j + 1] == 7:
                    gap[i - 1] = 1
                    del gap[i:i + j + 1]
                    gap[i:i] = [7, 4, 2, 1] * ((j // 2) + 1) + [7]

                    data_rebuild.append(
                                [data_list[index_of_transition[i - 1 - comp]][2] + diff_gate, rfid,
                                 data_list[index_of_transition[i - 1 - comp]][1] + datetime.timedelta(
                                     milliseconds=3000), 'logical'])
                    for k in range(0, (j + 1) // 2):
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + 2 * k - comp]][2] - diff_gate, rfid,
                                     data_list[index_of_transition[i + 2 * k - comp]][1] + datetime.timedelta(
                                         milliseconds=3000), 'logical'])
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + 2 * k - comp] + 1][2] - diff_gate, rfid,
                                     data_list[index_of_transition[i + 2 * k - comp] + 1][1] - datetime.timedelta(
                                         milliseconds=3000), 'logical'])
                    comp += 2 + j


                elif gap[i - 1] == 1 and gap[i + j + 1] == 6 and gap[i + j + 1] != 1:
                    del gap[i+1:i + j + 2]
                    gap[i + 1:i + 1] = [4, 2, 1, 7] * ((j // 2) + 1) + [4]

                    for k in range((j + 1) // 2):
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + k * 2 + 1 - comp]][2] - diff_gate, rfid,
                                     data_list[index_of_transition[i + k * 2 + 1 - comp]][1] + datetime.timedelta(
                                         milliseconds=3000), 'logical'])
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + k * 2 + 1 - comp] + 1][2] - diff_gate,
                                     rfid,
                                     data_list[index_of_transition[i + k * 2 + 1 - comp] + 1][
                                         1] - datetime.timedelta(
                                         milliseconds=3000), 'logical'])
                    data_rebuild.append(
                                [data_list[index_of_transition[i + j + 1 - comp] + 1][2] + diff_gate, rfid,
                                 data_list[index_of_transition[i + j + 1 - comp] + 1][1] - datetime.timedelta(
                                     milliseconds=3000), 'logical'])

                    comp += j + 2

                elif gap[i - 1] == 3 and gap[i + j + 1] == 6:
                            # normally always a 2 before as already corrected
                    del gap[i - 1:i + j + 2]
                    gap[i - 1:i - 1] = [1, 7, 4, 2] * ((j // 2) + 2)

                    data_rebuild.append(
                                [data_list[index_of_transition[i - 1 - comp]][2] + diff_gate, rfid,
                                 data_list[index_of_transition[i - 1 - comp]][1] + datetime.timedelta(
                                     milliseconds=3000), 'logical'])
                    for k in range(0, (j + 1) // 2):
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + 2 * k - comp]][2] - diff_gate, rfid,
                                     data_list[index_of_transition[i + 2 * k - comp]][1] + datetime.timedelta(
                                         milliseconds=3000), 'logical'])
                        data_rebuild.append(
                                    [data_list[index_of_transition[i + 2 * k - comp] + 1][2] - diff_gate, rfid,
                                     data_list[index_of_transition[i + 2 * k - comp] + 1][1] - datetime.timedelta(
                                         milliseconds=3000), 'logical'])

                    data_rebuild.append(
                                [data_list[index_of_transition[i + j + 1 - comp]][2] - diff_gate, rfid,
                                 data_list[index_of_transition[i + j + 1 - comp]][1] + datetime.timedelta(
                                     milliseconds=3000), 'logical'])

                    comp += j + 3

                        ## we not repair if it is 4-2-2-1 because we don't know what transition is false
        i = i+1

    if len(gap) != comp:
        print("Error")
    return data_rebuild

def fill_gaps(rfid, bd, detections):
    """
    :param rfid: rfid is a list define in the main file
    :param db: database where we choose to calculate the missing gaps
    :return: dataframe of the gaps filled (4 row : antenna_id, rfid, dtime, type)
    """
    data = np.array(pd.DataFrame(detections))
    data_return = []
    df = pd.DataFrame()
    if data is not None:
        data_init = sorted(data, key=lambda colonnes: colonnes[1])
        data_temp = convert_clean_data(data_init, bd)
        transition, missing_date, transition_lenght = transition_fun(data_temp,bd)
        binary = binary_fun(transition)
        data_return = repair_missing_data(binary, data_init, rfid, bd)
        data_return = data_return + missing_date
    if data_return:
        data_return_sort = sorted(data_return, key=lambda colonnes: colonnes[2])
        data_return_inv = list(map(list, zip(*data_return_sort)))

        dtimes = [pd.Timestamp(dtime).to_pydatetime() for dtime in data_return_inv[2]]
        return [{'antenna_id': data_return_inv[0][i], 'rfid': data_return_inv[1][i], 'dtime': dtimes[i], 'type': data_return_inv[3][i]} for i in range(len(data_return_inv[0]))]
    else:
        return []


