from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QColor, QBrush
from mysql_queries.queries_info import *
from mysql_connection.mysql_connection import *
from tools import tools
from datetime import datetime
import pandas as pd
import numpy as np
import csv
import re

### Functions to manage ADD BIRD tab

def init_add_bird(ui):
    # Initialize view
    ui.add_birth_year_button.setChecked(1)
    ui.add_birth_year_spinBox.setValue(datetime.today().year)
    ui.add_rfid_date_dateEdit.setDate(datetime.now())
    ui.add_ft_date_button.setChecked(1)
    ui.add_ft_date_dateEdit.setDate(datetime.now())
    ui.add_death_date_dateEdit.setDate(datetime.now())

    ui.add_birth_year_spinBox.setEnabled(0)
    ui.add_birth_type_comboBox.setEnabled(0)
    ui.add_ft_date_dateEdit.setEnabled(0)
    ui.add_death_date_dateEdit.hide()

    ui.add_stage_comboBox.clear()
    rfid_stages = get_stages()
    for stage in rfid_stages:
        ui.add_stage_comboBox.addItem(stage['name'])

    ui.add_manip_comboBox.clear()
    manip_list = get_manips()
    for manip in manip_list:
        ui.add_manip_comboBox.addItem(manip['name'])

    ui.add_handler_comboBox.clear()
    handlers = get_handlers()
    for handler in handlers:
        ui.add_handler_comboBox.addItem(handler['name'])

    ui.add_location_comboBox.clear()
    locations = get_locations()
    for location in locations:
        ui.add_location_comboBox.addItem(location['name'])

    ui.add_sampling_comboBox.clear()
    sampling_list = get_sampling()
    for sampling in sampling_list:
        ui.add_sampling_comboBox.addItem(sampling['name'])


def init_signals_add_bird(ui):
    # initialize signals
    ui.add_birth_year_button.toggled.connect(lambda: add_birth_year_buttonClicked(ui))
    ui.add_rfid_date_button.toggled.connect(lambda: add_rfid_date_buttonClicked(ui))
    ui.add_ft_date_button.toggled.connect(lambda: add_ft_date_buttonClicked(ui))

    ui.add_manip_button.clicked.connect(lambda: add_manip_buttonClicked(ui))
    ui.add_manip_remove_button.clicked.connect(lambda: add_manip_remove_buttonClicked(ui))
    ui.add_dead_comboBox.currentIndexChanged.connect(lambda: add_dead_comboBox_currentIndexChanged(ui))
    ui.add_rfid_check_button.clicked.connect(lambda: add_rfid_check_buttonClicked(ui))
    ui.add_rfid_lineEdit.textEdited.connect(lambda: add_rfid_lineEditTextEdited(ui))

    ui.add_name_check_button.clicked.connect(lambda: add_name_check_buttonClicked(ui))
    ui.add_name_lineEdit.textEdited.connect(lambda: add_name_lineEditTextEdited(ui))

    ui.add_sampling_button.clicked.connect(lambda: add_sampling_buttonClicked(ui))
    ui.add_sampling_remove_selected_button.clicked.connect(lambda: add_sampling_remove_selected_buttonClicked(ui))

    ui.add_save_button.clicked.connect(lambda: add_save_buttonClicked(ui))
    ui.add_reset_button.clicked.connect(lambda: add_reset_buttonClicked(ui))

def add_birth_year_buttonClicked(ui):
    if ui.add_birth_year_button.isChecked():
        ui.add_birth_year_spinBox.setEnabled(0)
        ui.add_birth_type_comboBox.setEnabled(0)
    else:
        ui.add_birth_year_spinBox.setEnabled(1)
        ui.add_birth_type_comboBox.setEnabled(1)


def add_rfid_date_buttonClicked(ui):
    if ui.add_rfid_date_button.isChecked():
        ui.add_rfid_date_dateEdit.setEnabled(0)
        ui.groupBox_10.setEnabled(0)
    else:
        ui.add_rfid_date_dateEdit.setEnabled(1)
        ui.groupBox_10.setEnabled(1)


def add_ft_date_buttonClicked(ui):
    if ui.add_ft_date_button.isChecked():
        ui.add_ft_date_dateEdit.setEnabled(0)
    else:
        ui.add_ft_date_dateEdit.setEnabled(1)


def add_manip_buttonClicked(ui):
    manip = ui.add_manip_comboBox.currentText()
    if not ui.add_manip_listWidget.findItems(manip, QtCore.Qt.MatchExactly):
        ui.add_manip_listWidget.addItem(manip)


def add_manip_remove_buttonClicked(ui):
    ui.add_manip_listWidget.takeItem(ui.add_manip_listWidget.currentRow())


def add_dead_comboBox_currentIndexChanged(ui):
    if ui.add_dead_comboBox.currentText() == "Dead and known date of death":
        ui.add_death_date_dateEdit.show()
    else:
        ui.add_death_date_dateEdit.hide()


def add_rfid_check_buttonClicked(ui):
    ### Check if RFID valid -> rfid must be either not in the database or linked with 'auto' name ; must be compatible with accepted format defined in accepted_values.txt file
    rfid = ui.add_rfid_lineEdit.text()
    data_rfid = execute_fetchall("SELECT rfid, name FROM birds WHERE rfid = '{}'".format(rfid))
    if len(data_rfid) > 0:
        if data_rfid[0]['name'][0:4] != 'auto':
            QMessageBox.information(None, 'Error', "RFID already exists")
            ui.add_rfid_check_button.setChecked(0)
            ui.add_rfid_check_button.setText('CHECK')
            return

    accepted_rfid_format = [x[1] for x in tools.get_accepted_values() if x[0] == 'rfid_format']
    for format in accepted_rfid_format:
        spaces = [i for i, j in enumerate(format) if j == ' ']
        if ([i for i, j in enumerate(rfid) if j == ' '] == spaces) and (len(rfid) == len(format)) and (
                format[0] == rfid[0]) and (rfid[1:].replace(' ', '').isdigit()):
            ui.add_rfid_check_button.setChecked(1)
            ui.add_rfid_check_button.setText('VALID')
            return
    QMessageBox.information(None, 'Not valid format',
                            "Accepted format are the following:\n" + '\n'.join(accepted_rfid_format))
    ui.add_rfid_check_button.setChecked(0)
    ui.add_rfid_check_button.setText('CHECK')


def add_rfid_lineEditTextEdited(ui):
    if ui.add_rfid_check_button.isChecked():
        ui.add_rfid_check_button.setChecked(0)
        ui.add_rfid_check_button.setText('Check')


def add_name_check_buttonClicked(ui):
    # Check if name already exists
    name = ui.add_name_lineEdit.text()
    if len(execute_fetchall("SELECT name FROM birds WHERE name = '{}'".format(name))) == 0:
        ui.add_name_check_button.setChecked(1)
        ui.add_name_check_button.setText('VALID')
    else:
        QMessageBox.information(None, 'Error', "Name already exists")
        ui.add_name_check_button.setChecked(0)
        ui.add_name_check_button.setText('CHECK')


def add_name_lineEditTextEdited(ui):
    if ui.add_name_check_button.isChecked():
        ui.add_name_check_button.setChecked(0)
        ui.add_name_check_button.setText('Check')


def add_sampling_buttonClicked(ui):
    sampling = ui.add_sampling_comboBox.currentText()
    if not ui.add_sampling_listWidget.findItems(sampling, QtCore.Qt.MatchExactly):
        ui.add_sampling_listWidget.addItem(sampling)


def add_sampling_remove_selected_buttonClicked(ui):
    ui.add_sampling_listWidget.takeItem(ui.add_sampling_listWidget.currentRow())


def add_save_buttonClicked(ui):
    if ui.add_rfid_check_button.isChecked():
        rfid = ui.add_rfid_lineEdit.text()
    else:
        QMessageBox.information(None, 'Error', "Check RFID before saving")
        return
    if ui.add_name_check_button.isChecked():
        name = ui.add_name_lineEdit.text()
    else:
        QMessageBox.information(None, 'Error', "Check name before saving")
        return

    sex = ui.add_sex_comboBox.currentText()
    if sex == 'Unknown':
        sex = 'Null'
    else:
        sex = "'{}'".format(sex)

    if ui.add_birth_year_button.isChecked():
        birth_year = 'Null'
        birth_year_type = 'Null'
    else:
        birth_year = "'{}'".format(ui.add_birth_year_spinBox.value())
        birth_year_type = "'{}'".format(ui.add_birth_type_comboBox.currentText())

    if ui.add_rfid_date_button.isChecked():
        rfid_date = 'Null'
    else:
        rfid_date = "'{}'".format(ui.add_rfid_date_dateEdit.date().toString("yyyy-MM-dd"))

    stage = ui.add_stage_comboBox.currentText()

    if ui.add_ft_date_button.isChecked():
        ft_date = 'Null'
    else:
        ft_date = "'{}'".format(ui.add_ft_date_dateEdit.date().toString("yyyy-MM-dd"))

    if ui.add_dead_comboBox.currentText() == 'No data':
        dead = 0
        death_date = 'Null'
    elif ui.add_dead_comboBox.currentText() == 'Dead but unknown date of death':
        dead = 1
        death_date = 'Null'
    else:
        dead = 1
        death_date = "'{}'".format(ui.add_death_date_dateEdit.date().toString("yyyy-MM-dd"))

    list_manips = [ui.add_manip_listWidget.item(k).text() for k in range(ui.add_manip_listWidget.count())]

    if ui.add_rfid_date_button.isChecked() is False:
        handler = ui.add_handler_comboBox.currentText()
        location = ui.add_location_comboBox.currentText()
        rfid_packing = ui.add_rfid_packing_comboBox.currentText()
        rfid_desinfectant = ui.add_rfid_desinfectant_comboBox.currentText()
        mass = ui.add_mass_lineEdit.text().replace(',', '.')
        upper_beak = ui.add_beak_upper_length_lineEdit.text()
        lower_beak = ui.add_beak_lower_length_lineEdit.text()
        height_beak = ui.add_beak_height_lineEdit.text()
        width_beak = ui.add_beak_width_lineEdit.text()
        right_flipper = ui.add_flipper_right_lineEdit.text()
        left_flipper = ui.add_flipper_left_lineEdit.text()
        right_htarsus = ui.add_htarsus_right_lineEdit.text()
        left_htarsus = ui.add_htarsus_left_lineEdit.text()
        rep = ui.add_repletion_lineEdit.text()
        circ = ui.add_circonference_lineEdit.text()
        sampling_list = [ui.add_sampling_listWidget.item(k).text() for k in range(ui.add_sampling_listWidget.count())]

        if handler == '':
            QMessageBox.information(None, 'Error', "Missing handler")
            return

        if location == '':
            QMessageBox.information(None, 'Error', "Missing location")
            return

        if stage == '':
            QMessageBox.information(None, 'Error', "Missing stage")
            return

        if mass != '':
            try:
                mass = float(mass)
            except:
                QMessageBox.information(None, 'Error', "Wrong format for mass value, must be float")
                return

        if upper_beak != '':
            try:
                upper_beak = int(upper_beak)
            except:
                QMessageBox.information(None, 'Error', "Wrong format for upper beak length value, must be integer")
                return

        if lower_beak != '':
            try:
                lower_beak = int(lower_beak)
            except:
                QMessageBox.information(None, 'Error', "Wrong format for lower beak length value, must be integer")
                return

        if height_beak != '':
            try:
                height_beak = int(height_beak)
            except:
                QMessageBox.information(None, 'Error', "Wrong format for beak height value, must be integer")
                return

        if width_beak != '':
            try:
                width_beak = int(width_beak)
            except:
                QMessageBox.information(None, 'Error', "Wrong format for beak width value, must be integer")
                return

        if right_flipper != '':
            try:
                right_flipper = int(right_flipper)
            except:
                QMessageBox.information(None, 'Error', "Wrong format for right flipper length value, must be integer")
                return

        if left_flipper != '':
            try:
                left_flipper = int(left_flipper)
            except:
                QMessageBox.information(None, 'Error', "Wrong format for left flipper length value, must be integer")
                return

        if right_htarsus != '':
            try:
                right_htarsus = int(right_htarsus)
            except:
                QMessageBox.information(None, 'Error', "Wrong format for right hemi-tarsus length value, must be integer")
                return

        if left_htarsus != '':
            try:
                left_htarsus = int(left_htarsus)
            except:
                QMessageBox.information(None, 'Error', "Wrong format for left hemi-tarsus length value, must be integer")
                return

        if rep != '':
            try:
                rep = int(rep)
            except:
                QMessageBox.information(None, 'Error', "Wrong format for repletion value, must be integer")
                return

        if circ != '':
            try:
                circ = int(circ)
            except:
                QMessageBox.information(None, 'Error', "Wrong format for circonference value, must be integer")
                return

    data_rfid = execute_fetchall("SELECT rfid, name FROM birds WHERE rfid = '{}'".format(rfid))
    if len(data_rfid) > 0:
        if data_rfid[0]['name'][0:4] == 'auto':
            update_bird_query = "UPDATE birds SET name = '{}', sex = {}, birth_year = {}, birth_year_type = {}," \
                                " rfid_date = {}, ft_date = {}, death_date = {}, dead = {}, rfid_stage = '{}' WHERE rfid = '{}'".format(
                name, sex, birth_year, birth_year_type, rfid_date, ft_date, death_date, dead, stage, rfid)
            execute_commit(update_bird_query)
    else:
        insert_bird_query = "INSERT INTO birds (rfid, name, sex, birth_year, birth_year_type, rfid_date, ft_date, death_date, dead, rfid_stage)" \
                            " VALUES ('{}', '{}', {}, {}, {}, {}, {}, {}, {}, '{}')".format(
            rfid, name, sex, birth_year, birth_year_type, rfid_date, ft_date, death_date, dead, stage)
        execute_commit(insert_bird_query)

    for manip in list_manips:
        insert_manip = 'INSERT INTO bird_manips (rfid, manip) VALUES ("{}", "{}")'.format(rfid, manip)
        execute_commit(insert_manip)

    if ui.add_rfid_date_button.isChecked() is False:
        insert_event = "INSERT INTO events (rfid, event_date, event_type, stage, location, handler) VALUES " \
                       "('{}', {}, '{}', '{}', '{}', '{}')".format(
            rfid, rfid_date, 'pit-tagging', stage, location, handler)
        execute_commit(insert_event)

        event_id = execute_fetchall("SELECT id FROM events WHERE rfid = '{}' AND event_type = '{}'".format(rfid, 'pit-tagging'))[0]['id']

        if mass != '':
            query_mass = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', {})".format(event_id, 'mass', mass)
            execute_commit(query_mass)
        if upper_beak != '':
            query_upper_beak = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', {})".format(event_id, 'ubeak_length', upper_beak)
            execute_commit(query_upper_beak)
        if lower_beak != '':
            query_lower_beak = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', {})".format(event_id, 'lbeak_length', lower_beak)
            execute_commit(query_lower_beak)
        if height_beak != '':
            query_height_beak = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', {})".format(event_id, 'beak_h', height_beak)
            execute_commit(query_height_beak)
        if width_beak != '':
            query_width_beak = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', {})".format(event_id, 'beak_w', width_beak)
            execute_commit(query_width_beak)
        if right_flipper != '':
            query_right_flipper = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', {})".format(event_id, 'flipper_length_r', right_flipper)
            execute_commit(query_right_flipper)
        if left_flipper != '':
            query_left_flipper = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', {})".format(event_id, 'flipper_length_l', left_flipper)
            execute_commit(query_left_flipper)
        if right_htarsus != '':
            query_right_htarsus = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', {})".format(event_id, 'htarsus_length_r', right_htarsus)
            execute_commit(query_right_htarsus)
        if left_htarsus != '':
            query_left_htarsus = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', {})".format(event_id, 'flipper_length_l', left_htarsus)
            execute_commit(query_left_htarsus)
        if rep != '':
            query_rep = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', {})".format(event_id, 'repletion', rep)
            execute_commit(query_rep)
        if circ != '':
            query_circ = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', {})".format(event_id, 'circonference', circ)
            execute_commit(query_circ)

        if rfid_packing != '':
            query_rfid_packing = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', '{}')".format(event_id, 'rfid_packing', rfid_packing)
            execute_commit(query_rfid_packing)

        if rfid_desinfectant != '':
            query_rfid_desinfectant = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', '{}')".format(event_id, 'rfid_desinfectant', rfid_desinfectant)
            execute_commit(query_rfid_desinfectant)

        for sampling in sampling_list:
            query_sampling = "INSERT INTO measures (event_id, name, value) VALUES ({},'{}', {})".format(event_id, sampling, 1)
            execute_commit(query_sampling)

    QMessageBox.information(None, 'Success', "New bird {} has well been inserted into the database ".format(name))
    reset_add_bird(ui)
    ui.groupBox_9.setEnabled(0)
    ui.groupBox_10.setEnabled(0)
    ui.add_reset_button.setEnabled(0)
    ui.add_save_button.setEnabled(0)

def add_reset_buttonClicked(ui):
    ret = QMessageBox.question(None, 'Reset confirmation', "Are you sure you want to reset all fields ?", QMessageBox.Yes | QMessageBox.Cancel, QMessageBox.Cancel)
    if ret == QMessageBox.Yes:
        reset_add_bird(ui)

def reset_add_bird(ui):
    ui.add_rfid_lineEdit.setText('')
    ui.add_rfid_check_button.setChecked(0)
    ui.add_rfid_check_button.setText('Check')
    ui.add_name_lineEdit.setText('')
    ui.add_name_check_button.setChecked(0)
    ui.add_name_check_button.setText('Check')
    ui.add_sex_comboBox.setCurrentIndex(0)
    ui.add_birth_year_button.setChecked(1)
    ui.add_birth_year_spinBox.setValue(datetime.today().year)
    ui.add_birth_type_comboBox.setCurrentIndex(0)
    ui.add_rfid_date_button.setChecked(0)
    ui.add_rfid_date_dateEdit.setDate(datetime.now())
    ui.add_stage_comboBox.setCurrentIndex(0)
    ui.add_ft_date_button.setChecked(1)
    ui.add_ft_date_dateEdit.setDate(datetime.now())
    ui.add_dead_comboBox.setCurrentIndex(0)
    ui.add_death_date_dateEdit.setDate(datetime.now())
    ui.add_manip_listWidget.clear()
    ui.add_manip_comboBox.setCurrentIndex(0)

    ui.add_handler_comboBox.setCurrentIndex(0)
    ui.add_location_comboBox.setCurrentIndex(0)
    ui.add_rfid_packing_comboBox.setCurrentIndex(0)
    ui.add_rfid_desinfectant_comboBox.setCurrentIndex(0)
    ui.add_mass_lineEdit.setText('')
    ui.add_beak_upper_length_lineEdit.setText('')
    ui.add_beak_lower_length_lineEdit.setText('')
    ui.add_beak_height_lineEdit.setText('')
    ui.add_beak_width_lineEdit.setText('')
    ui.add_flipper_right_lineEdit.setText('')
    ui.add_flipper_left_lineEdit.setText('')
    ui.add_htarsus_right_lineEdit.setText('')
    ui.add_htarsus_left_lineEdit.setText('')
    ui.add_repletion_lineEdit.setText('')
    ui.add_circonference_lineEdit.setText('')
    ui.add_sampling_listWidget.clear()
    ui.add_sampling_comboBox.setCurrentIndex(0)

    init_add_bird(ui)

