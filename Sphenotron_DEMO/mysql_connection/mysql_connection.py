"""
    Function used to build connection to the dababase
"""

import pymysql
import os
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import *

settings_connexion = QSettings("Sphenotron", "connection")

def extract_config():
    """ Extract connection data from config.txt

    :return: parameters in 'setting_connexion'
    """
    global settings_connexion
    settings_connexion = QSettings("Sphenotron", "connection")
    with open("mysql_connection/config.txt", "r") as file:
        config = {}
        for line in file:
            infos = line.split(":")
            config[infos[0]] = infos[1].split("\n")[0]
        settings_connexion.setValue("database", config['database'])
        settings_connexion.setValue("user", config['user'])
        settings_connexion.setValue("port", int(config['port']))
        settings_connexion.setValue("password", config['password'])
        settings_connexion.setValue("host", config['host'])
        settings_connexion.setValue("unix_socket", config['unix_socket'])
    return

def connect_to_db():
    """ Establishes the connection to the MySQL database.

    :return: connexion object
    """
    global settings_connexion
    try:
        connexion = pymysql.connect(host=settings_connexion.value("host"), port=settings_connexion.value("port"),
                                    user=settings_connexion.value("user"),
                                    password=settings_connexion.value("password"),
                                    database=settings_connexion.value("database"),
                                    unix_socket=settings_connexion.value("unix_socket"))
    except :
        return "Error"
    return connexion


def execute_fetchall(query):
    """ Execute MySQL SELECT query.

    :return query result"""
    connexion = connect_to_db()
    cursor = connexion.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute(query)
        data = cursor.fetchall()
        connexion.close()
        return data
    except:
        return "Error"

def execute_fetchall_fast(query, cursor):
    """ Execute MySQL SELECT query without creating a connection (need cursor in parameter).

    :return query result"""
    try:
        cursor.execute(query)
        data = cursor.fetchall()
        return data
    except:
        return "Error"

def execute_commit(query):
    """ Execute MySQL INSERT or UPDATE query.

    :return True if no error, else False"""
    connexion = connect_to_db()
    cursor = connexion.cursor()
    try:
        cursor.execute(query)
        connexion.commit()
        connexion.close()
    except pymysql.IntegrityError:
        return False
    return True

def execute_commit_fast(query, cursor, connexion):
    """ Execute une requete de type INSERT ou UPDATE.

    :return True si aucune erreur, False sinon"""
    try:
        cursor.execute(query)
        connexion.commit()
        return True
    except pymysql.IntegrityError:
        return False
