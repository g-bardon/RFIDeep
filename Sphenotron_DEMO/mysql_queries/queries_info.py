from mysql_connection.mysql_connection import *

def get_first_detection(rfid):
    query = "SELECT min(dtime) as min_detection from detections WHERE rfid = '{}'".format(rfid)
    data = execute_fetchall(query)
    return data[0]['min_detection']

def get_last_detection(rfid):
    query = "SELECT last_detection from birds WHERE rfid = '{}'".format(rfid)
    data = execute_fetchall(query)
    return data

def get_all_detections_original(rfid):
    """ Renvoie les detections originales. """
    query = "SELECT rfid, dtime, antenna_id, \"original\" as \"type\" FROM detections WHERE rfid = '{}'".format(rfid)
    data = execute_fetchall(query)
    return data

def get_all_detections_logique(rfid):
    """ Renvoie les detections de type 'logique'. """
    query = "SELECT rfid, dtime, antenna_id, \"logical\" as \"type\" FROM computed_detections WHERE rfid = '{}' and type = 'logical'".format(rfid)
    data = execute_fetchall(query)
    return data


def get_all_detections_calculee(rfid):
    "Renvoie les detections de type 'calculees'. "
    query = "SELECT rfid, dtime, antenna_id, \"computed\" as \"type\" FROM computed_detections WHERE rfid = '{}' and type = 'computed'".format(rfid)
    data = execute_fetchall(query)
    return data

def get_detections(rfid, original=True, logique=True, calculee=True):
    """ Renvoie toutes les detections.

    :param original: True si les detections originales sont a prendre en compte, False sinon
    :param logique: True si les detections logiques sont a prendre en compte, False sinon
    :param calculee: True si les detections calculees sont a prendre en compte, False sinon
    """
    detections_original = get_all_detections_original(rfid)
    detections = []

    if original and detections_original is not None:
        detections += detections_original

    if logique:
        detections_logiques = get_all_detections_logique(rfid)
        if detections_logiques is not None:
            detections += detections_logiques

    if calculee:
        detections_calculees = get_all_detections_calculee(rfid)
        if detections_calculees is not None:
            detections += detections_calculees

    detections_sorted = sorted(detections, key=lambda x: x['dtime'])
    return detections_sorted

def get_manips():
    query = "SELECT * from manips"
    return execute_fetchall(query)

def get_manip_classes():
    query = "SELECT class from manip_classes ORDER BY id ASC"
    return execute_fetchall(query)

def get_info(rfid, cursor):
    query = "SELECT * FROM birds WHERE rfid = '{}'".format(rfid)
    return execute_fetchall_fast(query, cursor)[0]

def get_bird_manips(rfid, cursor):
    query = "SELECT group_concat( '\n', manip) as manips FROM bird_manips where rfid = '{}'".format(rfid)
    manips= execute_fetchall_fast(query, cursor)[0]['manips']
    if manips:
        return manips[1:]
    else:
        return

def get_prefered_antenna(rfid, cursor):
    query = "SELECT a.name antenna_name, c.n count_antenna_id FROM (SELECT antenna_id, COUNT(antenna_id) n FROM detections " \
    f"WHERE rfid = '{rfid}' AND type = 'fixed' GROUP BY antenna_id) AS c, antennas a WHERE c.antenna_id = a.id;"
    print(query)
    k = execute_fetchall_fast(query, cursor)
    print(k)
    return execute_fetchall_fast(query, cursor)

def get_alarms():
    return execute_fetchall("SELECT class from alarms")

def get_comments(rfid):
    return execute_fetchall("SELECT * FROM comments WHERE rfid = '{}'".format(rfid))

def get_handlers():
    return execute_fetchall("SELECT name FROM handlers")

def get_measure_types():
    return execute_fetchall("SELECT * FROM measure_types")

def get_event_types():
    return execute_fetchall("SELECT * FROM event_types")

def get_stages():
    return execute_fetchall("SELECT * FROM stages")

def get_locations():
    return execute_fetchall("SELECT * FROM locations")

def get_sampling():
    return execute_fetchall("SELECT * FROM measure_types WHERE class = 'sampling'")

def get_phenology_types():
    return execute_fetchall("SELECT * FROM phenology_types")

def get_all_cycling(rfid):
    """ Renvoie toutes les donnes de cyclage de l'individu. """
    query = "SELECT * FROM cycling WHERE rfid = '{}' ORDER BY start_dtime ASC".format(rfid)
    return execute_fetchall(query)

def get_all_computed_cycling(rfid):
    query = "SELECT * FROM computed_cycling WHERE rfid = '{}' ORDER BY start_dtime ASC".format(rfid)
    return execute_fetchall(query)