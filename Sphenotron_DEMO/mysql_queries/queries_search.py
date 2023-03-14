def get_query_name(args):
    """ Renvoie la requete du filtre 'nom'.

    :param args: liste des noms demandes
    """

    beginning = "SELECT rfid FROM birds"
    end = ""
    for index, arg in enumerate(args):
        suite = "name LIKE \"" + arg + "\""
        if index != 0:
            operation = " OR "
        else:
            operation = " WHERE "
        end += operation + suite
    query = beginning + end
    return query


def get_query_rfid(args):
    """ Renvoie la requete du filtre 'rfid'.

    :param args: liste des rfid demandes
    """

    beginning = "SELECT rfid FROM birds"
    end = ""
    for index, arg in enumerate(args):
        suite = "rfid LIKE \"" + arg + "\""
        if index != 0:
            operation = " OR "
        else:
            operation = " WHERE "
        end += operation + suite
    query = beginning + end
    return query


def get_query_dead(args):
    """ Renvoie la requete du filtre 'mort'.

    :param args: 1 si mort, 0 sinon
    """
    if args:
        if args[0]:
            query = "SELECT rfid FROM birds WHERE dead = 1"
        else:
            query = "SELECT rfid FROM birds WHERE dead = 0"
    else:
        query = "SELECT rfid FROM birds"
    return query


def get_query_place(args):
    """ Renvoie la requete du filtre 'lieu actuel'.

    :param args: 'Mer' ou 'Terre'
    """
    if args:
        query = "SELECT rfid FROM birds INNER JOIN antennas ON birds.current_loc = antennas.side WHERE antennas.side = \"" + \
            args[0] + "\""
    else:
        query = "SELECT rfid FROM birds"
    return query


def get_query_transp(args):
    """ Renvoie la requete du filtre 'date de transpondage'.

    :param args: liste des dates
    """
    beginning = "SELECT rfid FROM birds WHERE rfid_date " + args[0]
    if (len(args) > 1):
        query = beginning + " AND rfid_date " + args[1]
    else:
        query = beginning
    return query


def get_query_last_detect(args):
    """ Renvoie la requete du filtre 'date de derniere detection'.

    :param args: liste des dates
    """
    beginning = "SELECT rfid FROM birds WHERE last_detection " + args[0]
    if (len(args) > 1):
        query = beginning + " AND last_detection " + args[1]
    else:
        query = beginning
    return query


def get_query_detect(args):
    """ Renvoie la requete du filtre 'date de detection'.

    :param args: liste des dates
    """
    beginning = "SELECT DISTINCT rfid FROM detections WHERE dtime " + args[0]
    if (len(args) > 1):
        query = beginning + " AND dtime " + args[1]
    else:
        query = beginning
    return query


def get_query_sex(args):
    """ Renvoie la requete du filtre 'sexe'.

    :param args: liste des sexes demandes
    """
    beginning = "SELECT rfid FROM birds"
    end = ""
    for index, arg in enumerate(args):
        suite = "sex = \"" + arg + "\""
        if index != 0:
            operation = " OR "
        else:
            operation = " WHERE "
        end += operation + suite
    query = beginning + end
    return query


def get_query_comment(args):
    """ Renvoie la requete du filtre 'commentaire'.

    :param args: commentaire (partiel ou complet)
    """
    query = "SELECT rfid FROM comments WHERE comment LIKE \"%" + str(args[0]) + "%\""
    return query


def get_query_manip(args):
    """ Renvoie la requete du filtre 'manipulations'.

    :param args: liste des manipulations
    """
    operation = args[0]
    del (args[0])

    if operation == "OR":
        query = "SELECT DISTINCT rfid FROM bird_manips where manip in ('%s')" % "','".join(args)

    elif operation == 'EXCEPT':
        query = "SELECT DISTINCT rfid FROM bird_manips where manip not in (SELECT DISTINCT rfid FROM bird_manips where manip in ('%s'))" % "','".join(
            args)
    elif operation == "AND":
        sub_queries = []
        for arg in args:
            sub_queries.append("(SELECT rfid FROM bird_manips WHERE manip = '%s')" % arg)
        sub_query = ''
        for i in sub_queries:
            sub_query += ('rfid in ' + i + ' AND ')
        sub_query = sub_query[:-5]
        query = "SELECT DISTINCT rfid FROM bird_manips where " + sub_query
    return query


def get_query_alarm(args):
    """ Renvoie la requete du filtre 'son suivi'.

            :param args: son
            """
    if args[0] == 'No alarm':
        query = "SELECT rfid FROM birds WHERE alarm is NULL"
    else:
        query = "SELECT rfid FROM birds WHERE alarm =  \"" + str(args[0]) + "\""
    return query

def get_query_custom_query(args):
    """ Return the custom query"""
    query = "SELECT rfid FROM " + str(args[0])
    return query


