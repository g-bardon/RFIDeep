from mysql_connection.mysql_connection import *

def from_antenna_to_location():
    """ Give ID, name and location of each antenna """
    query = "SELECT id, name, side FROM antennas ORDER BY id ASC"
    data = execute_fetchall(query)
    return data

def compute_transitions(detections):
    """ Compute transition from detections

    :return List of dictionnaries
    """
    antenna_to_location_table = from_antenna_to_location()
    transitions = []

    for line in range(len(detections)-1):
        transition = {}

        if detections[line]["type"] == "original" and detections[line + 1]["type"] == "original":
            transition["type"] = "original"
        elif detections[line]["type"] == "computed" or detections[line + 1]["type"] == "computed":
            transition["type"] = "computed"
        else:
            transition["type"] = "logical"

        transition["date1"] = detections[line]["dtime"]
        transition["date2"] = detections[line+1]["dtime"]

        transition["timestamp1"] = transition["date1"].timestamp()
        transition["timestamp2"] = transition["date2"].timestamp()

        transition["antenne1"] = detections[line]["antenna_id"]
        transition["antenne2"] = detections[line+1]["antenna_id"]

        if transition["timestamp2"] - transition["timestamp1"] <= 90:
            transition["duration"] = 0
        else:
            transition["duration"] = 1

        if antenna_to_location_table[detections[line]["antenna_id"]-1]["side"] == "Mer" and antenna_to_location_table[detections[line+1]["antenna_id"]-1]["side"] == "Terre":
            transition["departure"] = 0
            transition["arrival"] = 1

        elif antenna_to_location_table[detections[line]["antenna_id"]-1]["side"] == "Terre" and antenna_to_location_table[detections[line+1]["antenna_id"]-1]["side"] == "Mer":
            transition["departure"] = 1
            transition["arrival"] = 0

        else:
            if antenna_to_location_table[detections[line]["antenna_id"]-1]["side"] == "Mer":
                transition["departure"] = 0
                transition["arrival"] = 0
            else:
                transition["departure"] = 1
                transition["arrival"] = 1

        transition["text_transition"] = ""
        if (transition["timestamp2"] - transition["timestamp1"]) > 90:
            if int((transition["timestamp2"] - transition["timestamp1"])/(3600 * 24)) > 0:
                transition["text_transition"] = str(int((transition["timestamp2"] - transition["timestamp1"]) / (3600 * 24))) + " d"
            else:
                transition["text_transition"] = str(int((transition["timestamp2"] - transition["timestamp1"]) / 3600)) + " h"
        transitions.append(transition)
    return transitions

def get_list_antennas(rfid):
    query = "SELECT antenna_id FROM detections WHERE rfid = '{}'".format(rfid)
    data = execute_fetchall(query)
    return [ant['antenna_id'] for ant in data]

def get_accepted_values():
    with open("accepted_values.txt", "r") as file:
        config = []
        for line in file:
            infos = line.split(":")
            config.append([infos[0], infos[1].split("\n")[0]])
    return(config)


def determine_year(date):
    """ Give the breeding year associated with a date """
    if date.month > 8:
        year = int(date.year)+1
    else:
        year = int(date.year)
    return year
