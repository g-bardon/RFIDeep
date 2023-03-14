from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QColor, QBrush
from mysql_queries.queries_info import *
from mysql_connection.mysql_connection import *
from tools import tools
from datetime import datetime
import pandas as pd
import numpy as np

### Functions to manage IMPORT DATA tab
### 3 types of imports: new pit-tagged birds, fish-tagged birds and recaptures

def init_import_csv(ui):
    # Initialize view and signals
    ui.hide_help_import_csv_button.hide()
    ui.help_import_csv_textBrowser.hide()

    ui.hide_help_import_csv_button.clicked.connect(ui.help_import_csv_textBrowser.hide)
    ui.hide_help_import_csv_button.clicked.connect(ui.show_help_import_csv_button.show)
    ui.hide_help_import_csv_button.clicked.connect(ui.hide_help_import_csv_button.hide)

    ui.show_help_import_csv_button.clicked.connect(ui.help_import_csv_textBrowser.show)
    ui.show_help_import_csv_button.clicked.connect(ui.hide_help_import_csv_button.show)
    ui.show_help_import_csv_button.clicked.connect(ui.show_help_import_csv_button.hide)

    help_text = open('db_managment/help_import.txt').read()
    ui.help_import_csv_textBrowser.setPlainText(help_text)

    ui.import_type_comboBox.currentIndexChanged.connect(lambda: import_type_comboBoxCurrentIndexChanged(ui))
    import_type_comboBoxCurrentIndexChanged(ui)

    ui.open_csv_button.clicked.connect(lambda: open_csv_buttonClicked(ui))
    ui.check_table_add_birds_csv_button.clicked.connect(lambda: check_table_add_birds_csv_buttonClicked(ui))
    ui.save_table_add_birds_csv_button.clicked.connect(lambda: save_table_add_birds_csv_buttonClicked(ui))

def import_type_comboBoxCurrentIndexChanged(ui):
    if ui.import_type_comboBox.currentText() == '':
        ui.open_csv_button.setEnabled(0)
        ui.save_table_add_birds_csv_button.setEnabled(0)
        ui.check_table_add_birds_csv_button.setEnabled(0)
    else:
        ui.open_csv_button.setEnabled(1)
        ui.save_table_add_birds_csv_button.setEnabled(1)
        ui.check_table_add_birds_csv_button.setEnabled(1)


def open_csv_buttonClicked(ui):
    # Open csv, populate table and put headers
    import_type = ui.import_type_comboBox.currentText()
    if import_type == 'NEW PIT-TAGGED BIRDS':
        list_possible_headers = ['', 'rfid', 'name', 'manipulation', 'rfid_date', 'rfid_stage', 'location', 'handler',
                                 'comment', 'sex', 'birth_year', 'birth_year_type', 'dead', 'death_date'] +\
                                [x['name'].lower() for x in get_measure_types()]
    elif import_type == 'FISH-TAGGED BIRDS':
        list_possible_headers = ['', 'rfid', 'name', 'ft_date', 'stage', 'manipulation', 'location', 'handler',
                                 'comment', 'dead', 'death_date', ] + \
                                [x['name'].lower() for x in get_measure_types()]
    else:
        list_possible_headers = ['', 'rfid', 'event_type', 'manipulation', 'location', 'handler', 'stage', 'date',
                                 'comment'] + \
                                [x['name'].lower() for x in get_measure_types()]

    ui.csv_add_birds_tableWidget.setRowCount(0)
    ui.save_table_add_birds_csv_button.setEnabled(0)

    file = QFileDialog.getOpenFileName(None, "Choose a file", filter="*.csv")
    if not file[0]:
        return
    csv_birds_data = pd.read_csv(file[0], sep=None, engine='python')
    headers = [x.lower() for x in list(csv_birds_data.columns)]
    ui.csv_add_birds_tableWidget.setRowCount(len(csv_birds_data)+2)
    ui.csv_add_birds_tableWidget.setColumnCount(len(headers))

    list_combobox_header = []
    for col, item in enumerate(headers):
        ui.csv_add_birds_tableWidget.setItem(1,col,QTableWidgetItem(item))
        list_combobox_header.append(QComboBox())
        list_combobox_header[-1].addItems(list_possible_headers)
        ui.csv_add_birds_tableWidget.setCellWidget(0, col, list_combobox_header[-1])
        if item in list_possible_headers:
            list_combobox_header[-1].setCurrentText(item)
    csv_birds_data_array = csv_birds_data.values
    for row in range(csv_birds_data.shape[0]):
        for col in range(csv_birds_data.shape[1]):
            ui.csv_add_birds_tableWidget.setItem(row + 2, col, QTableWidgetItem(str(csv_birds_data_array[row, col])))
    ui.csv_add_birds_tableWidget.resizeColumnsToContents()


def check_table_add_birds_csv_buttonClicked(ui):
    # Check integrity of the table:
    ### all headers are completed
    ### formats, unicity, measures scale, foreign keys, mandatory columns

    table = ui.csv_add_birds_tableWidget
    nrow = table.rowCount()
    headers = [table.cellWidget(0, col).currentText() for col in range(table.columnCount())]

    # CHECKS ON COLUMNS
    if '' in headers:
        QMessageBox.information(None, 'Error', "Not all column headers are filled in")
        return

    if len(headers) != len(set(headers)):
        QMessageBox.information(None, 'Error', "Some column headers are duplicated")
        return

    import_type = ui.import_type_comboBox.currentText()
    if import_type == 'NEW PIT-TAGGED BIRDS':
        required_columns = ['rfid', 'name', 'rfid_date', 'location', 'handler']
        import_type = 'pt'
    elif import_type == 'FISH-TAGGED BIRDS':
        required_columns = ['rfid', 'name', 'ft_date', 'stage', 'location', 'handler']
        import_type = 'ft'
    else:
        required_columns = ['rfid', 'stage', 'location', 'handler', 'event_type', 'date']
        import_type = 'data'


    for col in required_columns:
        if col not in headers:
            QMessageBox.information(None, 'Error', "The following column are mandatory: "+ ' ; '.join(required_columns))
            return

    ### CHECKS ON RFID ###
    rfid_col = headers.index('rfid')

    list_rfid = [table.item(row, rfid_col).text() for row in range(2,nrow)]
    dup = [x for x in list_rfid if list_rfid.count(x) > 1]
    if len(dup):
        QMessageBox.information(None, 'Error', 'RFID {} is duplicated'.format(dup[0]))
        return

    # pit-tagging import
    if import_type == 'pt':
        accepted_rfid_format = [x[1] for x in tools.get_accepted_values() if x[0] == 'rfid_format']
        connexion = connect_to_db()
        cursor = connexion.cursor(pymysql.cursors.DictCursor)
        for row in range(2,nrow):
            rfid = table.item(row, rfid_col).text()
            rfid_data = execute_fetchall_fast("SELECT rfid, name FROM birds WHERE rfid = '{}'".format(rfid), cursor)
            if rfid_data:
                if rfid_data[0]['name'][:4] != 'auto':
                    QMessageBox.information(None, 'Error', "RFID {} already exists in the database".format(rfid))
                    connexion.close()
                    return
            checked_format_rfid = 0
            for format in accepted_rfid_format:
                spaces = [i for i, j in enumerate(format) if j == ' ']
                if ([i for i, j in enumerate(rfid) if j == ' '] == spaces) and (len(rfid) == len(format)) and (
                        format[0] == rfid[0]) and (rfid[1:].replace(' ', '').isdigit()):
                    checked_format_rfid = 1
            if checked_format_rfid == 0:
                QMessageBox.information(None, 'Not valid format',
                            "Not valid format for RFID {}".format(rfid) + "\nAccepted format are the following:\n" + '\n'.join(accepted_rfid_format))
                connexion.close()
                return

        connexion.close()

    if import_type =='ft':
        # fish-tagging import
        ### CHECK IF fish-tagging event already exists for the bird
        connexion = connect_to_db()
        cursor = connexion.cursor(pymysql.cursors.DictCursor)
        for row in range(2,nrow):
            rfid = table.item(row, rfid_col).text()
            rfid_data = execute_fetchall_fast("SELECT rfid, name FROM birds WHERE rfid = '{}'".format(rfid), cursor)
            if rfid_data:
                if rfid_data[0]['name'][:4] == 'auto':
                    QMessageBox.information(None, 'Error', "The RFID {} already exists in the database and is associated with an 'auto' bird. Add pit-tagging data first and then add fish-tagging data.".format(rfid))
                    connexion.close()
                    return
            else:
                if rfid[:9] != "A 99999 9":
                    QMessageBox.information(None, 'Error',
                                            "The RFID {} does not fit with non pit-tagged nomenclature (A 99999 9%) or do not already exists in the database".format(
                                                rfid))
                    connexion.close()
                    return
        connexion.close()

    if import_type == 'data':
        # data import
        connexion = connect_to_db()
        cursor = connexion.cursor(pymysql.cursors.DictCursor)
        for row in range(2,nrow):
            rfid = table.item(row, rfid_col).text()
            rfid_data = execute_fetchall_fast("SELECT rfid, name FROM birds WHERE rfid = '{}'".format(rfid), cursor)
            if len(rfid_data) < 1:
                QMessageBox.information(None, 'Error',
                                        "The RFID {} does not exist in the database.".format(
                                            rfid))

                return
        connexion.close()

    ### CHECKS ON NAMES ###
    if 'name' in headers:
        name_col = headers.index('name')
        list_name = [table.item(row, name_col).text() for row in range(2,nrow)]
        dup = [x for x in list_name if list_name.count(x) > 1]
        if len(dup):
            QMessageBox.information(None, 'Error', 'Name {} is duplicated'.format(dup[0]))
            return

        if import_type == 'pt':
            connexion = connect_to_db()
            cursor = connexion.cursor(pymysql.cursors.DictCursor)
            for row in range(2,nrow):
                name = table.item(row, name_col).text()
                if execute_fetchall_fast("SELECT name FROM birds WHERE name = '{}'".format(name), cursor):
                    QMessageBox.information(None, 'Error', "Name {} already exists in the database".format(name))
                    return
            connexion.close()
        elif import_type == 'ft':
            connexion = connect_to_db()
            cursor = connexion.cursor(pymysql.cursors.DictCursor)
            for row in range(2,nrow):
                name = table.item(row, name_col).text()
                rfid_name = execute_fetchall_fast("SELECT rfid, name FROM birds WHERE name = '{}'".format(name), cursor)
                if rfid_name:
                    if table.item(row, rfid_col).text() != rfid_name[0]['rfid']:
                        QMessageBox.information(None, 'Error', "Name {} already exists in the database and is associated with another RFID".format(name))
                        return
            connexion.close()

    ### CHECK ON OTHER COLUMNS
    if 'rfid_date' in headers:
        rfid_date_col = headers.index('rfid_date')
        for row in range(2, nrow):
            rfid_date = table.item(row, rfid_date_col).text()
            try:
                pd.to_datetime(rfid_date)
            except:
                QMessageBox.information(None, 'Error', "RFID date is in the wrong format (RFID: {})".format(table.item(row, rfid_col).text()))
                return
            if pd.to_datetime(rfid_date) > datetime.now():
                QMessageBox.information(None, 'Error', "RFID date is in the future (RFID: {})".format(table.item(row, rfid_col).text()))

    if 'date' in headers:
        date_col = headers.index('date')
        for row in range(2, nrow):
            date = table.item(row, date_col).text()
            try:
                pd.to_datetime(date)
            except:
                QMessageBox.information(None, 'Error', "Date is in the wrong format (RFID: {})".format(table.item(row, rfid_col).text()))
                return
            if pd.to_datetime(date) > datetime.now():
                QMessageBox.information(None, 'Error', "Date is in the future (RFID: {})".format(table.item(row, rfid_col).text()))

    if 'rfid_stage' in headers:
        rfid_stage_col = headers.index('rfid_stage')
        allowed_stages = [x['name'] for x in execute_fetchall('SELECT name FROM stages')]
        for row in range(2, nrow):
            rfid_stage = table.item(row, rfid_stage_col).text()
            if rfid_stage not in allowed_stages:
                QMessageBox.information(None, 'Error', "RFID stage does not exist in accepted stages (RFID: {})".format(
                    table.item(row, rfid_col).text()) + "\nAccepted stages are the following:\n" + '\n'.join(allowed_stages))
                return

    if 'stage' in headers:
        stage_col = headers.index('stage')
        allowed_stages = [x['name'] for x in execute_fetchall('SELECT name FROM stages')]
        for row in range(2, nrow):
            stage = table.item(row, stage_col).text()
            if stage not in allowed_stages:
                QMessageBox.information(None, 'Error', "Stage does not exist in accepted stages (RFID: {})".format(
                    table.item(row, rfid_col).text()) + "\nAccepted stages are the following:\n" + '\n'.join(allowed_stages))
                return

    if 'location' in headers:
        location_col = headers.index('location')
        allowed_locations = [x['name'] for x in execute_fetchall('SELECT name FROM locations')]
        for row in range(2, nrow):
            location = table.item(row, location_col).text()
            if location not in allowed_locations:
                QMessageBox.information(None, 'Error', "Location does not exist in accepted locations (RFID: {})".format(
                    table.item(row, rfid_col).text()) + "\nAccepted locations are the following:\n" + '\n'.join(allowed_locations))
                return

    if 'manipulation' in headers:
        manip_col = headers.index('manipulation')
        allowed_manips = [x['name'] for x in execute_fetchall('SELECT name FROM manips')]
        for row in range(2, nrow):
            manip = table.item(row, manip_col).text()
            if manip not in allowed_manips:
                QMessageBox.information(None, 'Error',"Manipulation does not exist in accepted manipulations (RFID: {})".format(
                                            table.item(row,rfid_col).text()) + "\nAccepted manipulations are the following:\n" + '\n'.join(allowed_manips))
                return

    if 'handler' in headers:
        handler_col = headers.index('handler')
        allowed_handlers = [x['name'] for x in execute_fetchall('SELECT name FROM handlers')]
        for row in range(2, nrow):
            handler = table.item(row, handler_col).text()
            if handler not in allowed_handlers:
                QMessageBox.information(None, 'Error',
                                        "Handler does not exist in accepted handlers (RFID: {})".format(table.item(row,rfid_col).text()) +
                                        "\nAccepted handlers are the following:\n" + '\n'.join( allowed_handlers))
                return

    if 'ft_date' in headers:
        ft_date_col = headers.index('ft_date')
        for row in range(2, nrow):
            ft_date = table.item(row, ft_date_col).text()
            if ft_date != '':
                try:
                    pd.to_datetime(ft_date)
                except:
                    QMessageBox.information(None, 'Error', "Fish-tagging date is in the wrong format (RFID: {})".format(
                        table.item(row, rfid_col).text()))
                    return
                if pd.to_datetime(ft_date) > datetime.now():
                    QMessageBox.information(None, 'Error', "RFID date is in the future (RFID: {})".format(
                        table.item(row, rfid_col).text()))

    if 'sex' in headers:
        sex_col = headers.index('sex')
        for row in range(2, nrow):
            sex = table.item(row, sex_col).text()
            if sex not in ['', 'M', 'F', 'Mobs', 'Fobs']:
                    QMessageBox.information(None, 'Error', "Allowed sexes are 'M', 'F', 'Mobs', 'Fobs' or nothing (RFID: {})".format(
                        table.item(row, rfid_col).text()))
                    return


    if 'death_date' in headers:
        death_date_col = headers.index('death_date')
        for row in range(2, nrow):
            death_date = table.item(row, death_date_col).text()
            if death_date != '':
                try:
                    pd.to_datetime(death_date)
                except:
                    QMessageBox.information(None, 'Error', "Death date is in the wrong format (RFID: {})".format(
                        table.item(row, rfid_col).text()))
                    return
                if pd.to_datetime(death_date) > datetime.now():
                    QMessageBox.information(None, 'Error', "Death date is in the future (RFID: {})".format(
                        table.item(row, rfid_col).text()))

    if 'dead' in headers:
        dead_col = headers.index('dead')
        for row in range(2, nrow):
            dead = table.item(row, dead_col).text()
            if dead not in ['0', '1']:
                    QMessageBox.information(None, 'Error', "Allowed values for dead are 0 and 1 (RFID: {})".format(
                        table.item(row, rfid_col).text()))
                    return

    if 'birth_year' in headers:
        birth_year_col = headers.index('birth_year')
        for row in range(2, nrow):
            birth_year = table.item(row, birth_year_col).text()
            if birth_year != '':
                try:
                    int(birth_year)
                except:
                    QMessageBox.information(None, 'Error', "Birth year must be integer (RFID: {})".format(
                        table.item(row, rfid_col).text()))
                    return
                if int(birth_year) < 1970:
                    QMessageBox.information(None, 'Error', "Birth year is too old (RFID: {})".format(
                        table.item(row, rfid_col).text()))
                if int(birth_year) > datetime.now().year:
                    QMessageBox.information(None, 'Error', "Birth year is in the future (RFID: {})".format(
                        table.item(row, rfid_col).text()))

    if 'birth_year_type' in headers:
        birth_year_type_col = headers.index('birth_year_type')
        for row in range(2, nrow):
            birth_year_type = table.item(row, birth_year_type_col).text()
            if birth_year_type not in ['', 'obs', 'infer', 'methyl']:
                    QMessageBox.information(None, 'Error', "Allowed birth_year_type are 'obs', 'infer', 'methyl' or nothing (RFID: {})".format(
                        table.item(row, rfid_col).text()))
                    return
    if 'event_type' in headers:
        event_type_col = headers.index('event_type')
        list_event_types = [x['name'].lower() for x in execute_fetchall("SELECT name FROM event_types") if x['name'].lower() not in ['pit-tagging', 'fish-tagging']]
        for row in range(2, nrow):
            event_type = table.item(row, event_type_col).text()
            if event_type not in list_event_types:
                QMessageBox.information(None, 'Error',
                                        "Error for RFID: {}".format(table.item(row,rfid_col).text()) +",\nallowed event_types are:\n" + '\n'.join(list_event_types))
                return


    if import_type == 'ft':
        #check existing fish-tagging events
        connexion = connect_to_db()
        cursor = connexion.cursor(pymysql.cursors.DictCursor)
        for row in range(2, nrow):
            if execute_fetchall_fast("SELECT * FROM events WHERE rfid = '{}' AND event_type = 'fish-tagging'".format(table.item(row, rfid_col).text()), cursor):
                QMessageBox.information(None, 'Error',
                                        "Bird with RFID: {} has already a fish-tagging event in the database".format(
                                            table.item(row, rfid_col).text()))
                connexion.close()
                return
        connexion.close()

    if import_type == 'data':
        #check existing events
        connexion = connect_to_db()
        cursor = connexion.cursor(pymysql.cursors.DictCursor)
        for row in range(2, nrow):
            event_type = table.item(row, event_type_col).text()
            date = table.item(row, date_col).text()
            if execute_fetchall_fast("SELECT * FROM events WHERE rfid = '{}' AND event_type = '{}' AND event_date = '{}'".format(table.item(row, rfid_col).text(), event_type, date), cursor):
                QMessageBox.information(None, 'Error',
                                        "Bird with RFID: {} has already a {} event in the database at the same date".format(event_type,
                                            table.item(row, rfid_col).text()))
                connexion.close()
                return
        connexion.close()

    ### WARNINGS ON VALUES

    warning_value = []
    for col in range(table.columnCount()):
        if headers[col] in ['mass', 'flipper_length_r', 'flipper_length_l', 'flipper_length_r',
                            'htarsus_length_r', 'htarsus_length_l', 'ftarsus_length_r', 'ftarsus_length_l',
                            'ubeak_length', 'lbeak_length', 'beak_w', 'beak_h', 'circonference', 'repletion']:
            measure_type = headers[col]
            if import_type == 'ft':
                existing_measures = [float(x['value']) for x in
                                     execute_fetchall("SELECT value FROM measures where name = '{}' "
                                                      "AND event_id in (SELECT id FROM events where event_type = 'fish-tagging')".format(
                                         measure_type))]
            else:
                existing_measures = [float(x['value']) for x in execute_fetchall("SELECT value FROM measures where name = '{}' "
                                                                      "AND event_id in (SELECT id FROM events where event_type = 'pit-tagging')".format(measure_type))]
            if len(existing_measures):
                quantile_5 = np.quantile(existing_measures, 0.05)
                quantile_95 = np.quantile(existing_measures, 0.95)
            for row in range(2, nrow):
                measure_value = table.item(row, col).text()
                try:
                    float(measure_value)
                except:
                    QMessageBox.information(None, 'Error', "{} value is in the wrong format (RFID: {})".format(measure_type,
                        table.item(row, rfid_col).text()))
                    return
                if len(existing_measures):
                    if float(measure_value) < quantile_5:
                        warning_value.append(['small value', measure_type, measure_value, table.item(row, rfid_col).text()])
                    if float(measure_value) > quantile_95:
                        warning_value.append(['big value', measure_type, measure_value, table.item(row, rfid_col).text()])
                if measure_value == 'nan':
                    warning_value.append(
                        ['no data', measure_type, measure_value, table.item(row, rfid_col).text()])

    if len(warning_value):
        dial = QInputDialog()
        dial.setWindowTitle("Check values")
        dial.setLabelText("")
        dial.show()
        dial.findChild(QtWidgets.QLineEdit).hide()
        dial.layout().insertWidget(0, QLabel("Please review the following values and correct your CSV file if necessary"))
        warning_table = QTableWidget()
        warning_table.setColumnCount(4)
        warning_table.setRowCount(len(warning_value))
        warning_table.setHorizontalHeaderLabels(["RFID", "Measure", "Value", "Warning"])
        warning_table.horizontalHeader().setVisible(True)
        warning_table.verticalHeader().setVisible(False)
        warning_table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        warning_table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        for row, warn in enumerate(warning_value):
            warning_table.setItem(row, 0, QTableWidgetItem(warning_value[row][3]))
            warning_table.setItem(row, 1, QTableWidgetItem(warning_value[row][1]))
            warning_table.setItem(row, 2, QTableWidgetItem(warning_value[row][2]))
            warning_table.setItem(row, 3, QTableWidgetItem(warning_value[row][0]))
        warning_table.resizeColumnsToContents()
        warning_table.resizeRowsToContents()
        dial.layout().insertWidget(1, warning_table)
        dial.layout().setSizeConstraint(QLayout.SetDefaultConstraint)
        dial.setFixedSize(warning_table.sizeHint().width()+250, warning_table.sizeHintForRow(0)*warning_table.rowCount() + 200)
        if dial.exec_() & dial.Accepted:
            ui.save_table_add_birds_csv_button.setEnabled(1)
        else:
            ui.save_table_add_birds_csv_button.setEnabled(0)
    else:
        ui.save_table_add_birds_csv_button.setEnabled(1)

###TODO: SEE HOW TO HANDLE SAMPLES
def save_table_add_birds_csv_buttonClicked(ui):
    table = ui.csv_add_birds_tableWidget
    nrow = table.rowCount()
    headers = [table.cellWidget(0, col).currentText() for col in range(table.columnCount())]

    possible_measure_columns = [x['name'] for x in get_measure_types()]

    # mandatory birds
    rfid = get_column_info('rfid', headers, table)
    name = get_column_info('name', headers, table)
    rfid_date = get_column_info('rfid_date', headers, table)
    rfid_stage = get_column_info('rfid_stage', headers, table)

    # mandatory event
    handler = get_column_info('handler', headers, table)
    location = get_column_info('location', headers, table)
    event_type = get_column_info('event_type', headers, table)

    # optionnal
    sex = get_column_info('sex', headers, table)
    birth_year = get_column_info('birth_year', headers, table)
    birth_year_type = get_column_info('birth_year_type', headers, table)
    dead = get_column_info('dead', headers, table)
    if 'dead' not in headers:
        dead = [0]*ui.csv_add_birds_tableWidget.rowCount()
    death_date = get_column_info('death_date', headers, table)
    ft_date = get_column_info('ft_date', headers, table)
    stage = get_column_info('stage', headers, table)
    date = get_column_info('date', headers, table)
    manipulation = get_column_info('manipulation', headers, table)
    comment = get_column_info('comment', headers, table)

    measure_columns = [[ind, col] for ind, col in enumerate(headers) if col in possible_measure_columns]

    import_type = ui.import_type_comboBox.currentText()
    if import_type == 'NEW PIT-TAGGED BIRDS':
        for row in range(nrow-2):
            query_birds = "INSERT INTO birds (rfid, name, sex, birth_year, birth_year_type, rfid_date, ft_date, death_date, dead, rfid_stage) VALUES " \
                          "({},{},{},{},{},{},{},{},{},{})".format(rfid[row], name[row], sex[row], birth_year[row], birth_year_type[row], rfid_date[row], ft_date[row], death_date[row], dead[row], rfid_stage[row])
            try:
                execute_commit(query_birds)
            except:
                QMessageBox.information(None, 'Error', "The bird {} has not been inserted into the database but all previous birds have been inserted.".format(name[row]))
                return
            if 'manipulation' in headers:
                query_manip = "INSERT INTO bird_manips (rfid, manip) VALUES ({},{})".format(rfid[row], manipulation[row])
                try:
                    execute_commit(query_manip)
                except:
                    QMessageBox.information(None, 'Error',
                                            "The bird {} has not been inserted into the database (an error happened with manipulation table). All previous birds have been correctly inserted.".format(
                                                name[row]))
                    execute_commit("DELETE FROM birds WHERE rfid = {}".format(rfid[row]))
                    return
            query_event = "INSERT INTO events (rfid, event_date, event_type, stage, location, handler, comment) VALUES " \
                          "({},{},'pit-tagging', {},{},{},{})".format(rfid[row], rfid_date[row], rfid_stage[row], location[row], handler[row], comment[row])
            try:
                execute_commit(query_event)
            except:
                QMessageBox.information(None, 'Error',
                                        "The bird {} has not been inserted into the database (an error happened with event table). All previous birds have been correctly inserted.".format(
                                            name[row]))
                execute_commit("DELETE FROM birds WHERE rfid = {}".format(rfid[row]))
                return
            for measure in measure_columns:
                value = table.item(row+2, measure[0]).text()
                if value != 'nan':
                    value = "'{}'".format(value)
                    event_id = execute_fetchall("SELECT id FROM events WHERE rfid = {} AND event_type = 'pit-tagging' AND event_date = {}".format(rfid[row], rfid_date[row]))[0]['id']
                    query_measure = "INSERT INTO measures (event_id, name, value) VALUES ({},{},{})".format(event_id, "'{}'".format(measure[1]), value)
                    try:
                        execute_commit(query_measure)
                    except:
                        QMessageBox.information(None, 'Error',
                                                "The bird {} has not been inserted into the database (an error happened with measures table). All previous birds have been correctly inserted.".format(
                                                    name[row]))
                        execute_commit("DELETE FROM birds WHERE rfid = {}".format(rfid[row]))
                        return

        QMessageBox.information(None, 'Success',
                                "All birds have been correctly inserted into the database.".format(
                                    name))

    elif import_type == 'FISH-TAGGED BIRDS':
        for row in range(nrow - 2):
            query_birds = "INSERT INTO birds (rfid, name, sex, birth_year, birth_year_type, rfid_date, ft_date, death_date, dead, rfid_stage) VALUES " \
                          "({},{},{},{},{},{},{},{},{},{}) ON DUPLICATE KEY UPDATE ft_date = {}".format(rfid[row], name[row], sex[row], birth_year[row],
                                                                   birth_year_type[row], rfid_date[row], ft_date[row],
                                                                   death_date[row], dead[row], rfid_stage[row], ft_date[row])
            try:
                execute_commit(query_birds)
            except:
                QMessageBox.information(None, 'Error',
                                        "Data of the bird {} has not been inserted into the database but all previous birds data have been inserted.".format(
                                            rfid[row]))
                return
            if 'manipulation' in headers:
                query_manip = "INSERT INTO bird_manips (rfid, manip) VALUES ({},{}) ON DUPLICATE KEY UPDATE manip = {}".format(
                    rfid[row],manipulation[row], manipulation[row])
                try:
                    execute_commit(query_manip)
                except:
                    QMessageBox.information(None, 'Error',
                                            "The bird {} has not been inserted into the manipulation table. All previous birds have been correctly inserted.".format(
                                                rfid[row]))

            query_event = "INSERT INTO events (rfid, event_date, event_type, stage, location, handler, comment) VALUES " \
                          "({},{},'fish-tagging', {},{},{},{})".format(rfid[row], ft_date[row], stage[row],
                                                                      location[row], handler[row], comment[row])
            try:
                execute_commit(query_event)
            except:
                QMessageBox.information(None, 'Error',
                                        "The fish-tagging event for the bird {} has not been inserted into the database. All previous birds have been correctly inserted.".format(
                                            rfid[row]))
                return
            for measure in measure_columns:
                value = table.item(row + 2, measure[0]).text()
                if value != 'nan':
                    value = "'{}'".format(value)
                    event_id = execute_fetchall(
                        "SELECT id FROM events WHERE rfid = {} AND event_type = 'fish-tagging' AND event_date = {}".format(
                            rfid[row], ft_date[row]))[0]['id']
                    query_measure = "INSERT INTO measures (event_id, name, value) VALUES ({},{},{})".format(
                        event_id, "'{}'".format(measure[1]),value)
                    try:
                        execute_commit(query_measure)
                    except:
                        QMessageBox.information(None, 'Error',
                                                "An error occured with measures import of the bird {}. All previous birds have been correctly inserted.".format(
                                                    rfid[row]))
                        execute_commit("DELETE FROM events WHERE id = {}".format(event_id))
                        return
        QMessageBox.information(None, 'Success',
                                "All data have been correctly inserted into the database.")
    else: ### DATA OF ALREADY PIT-TAGGED BIRDS
        for row in range(nrow - 2):
            if 'manipulation' in headers:
                query_manip = "INSERT INTO bird_manips (rfid, manip) VALUES ({},{}) ON DUPLICATE KEY UPDATE manip = {}".format(rfid[row], manipulation[row], manipulation[row])
                try:
                    execute_commit(query_manip)
                except:
                    QMessageBox.information(None, 'Error',
                                            "The bird {} has not been inserted into the manipulation table. All previous birds have been correctly inserted.".format(
                                                rfid[row]))

            query_event = "INSERT INTO events (rfid, event_date, event_type, stage, location, handler, comment) VALUES " \
                          "({},{},{},{},{},{},{})".format(rfid[row], date[row], event_type[row], stage[row],
                                                                       location[row], handler[row], comment[row])
            try:
                execute_commit(query_event)
            except:
                QMessageBox.information(None, 'Error',
                                        "The  event {} for the bird {} has not been inserted into the database. All previous birds have been correctly inserted.".format(
                                            event_type[row], rfid[row]))
                return
            for measure in measure_columns:
                value = table.item(row + 2, measure[0]).text()
                if value != 'nan':
                    value = "'{}'".format(value)
                    event_id = execute_fetchall(
                        "SELECT id FROM events WHERE rfid = {} AND event_type = {} AND event_date = {}".format(
                            rfid[row], event_type[row], date[row]))[0]['id']
                    query_measure = "INSERT INTO measures (event_id, name, value) VALUES ({},{},{})".format(
                        event_id, "'{}'".format(measure[1]), value)
                    try:
                        execute_commit(query_measure)
                    except:
                        QMessageBox.information(None, 'Error',
                                                "An error occured with measures import of the bird {}. All previous birds have been correctly inserted.".format(
                                                    rfid[row]))
                        execute_commit("DELETE FROM events WHERE id = {}".format(event_id))
                        return
        QMessageBox.information(None, 'Success',
                                "All data have been correctly inserted into the database.")


def get_column_info(column_name, headers, table):
    nrow = table.rowCount()
    if column_name in headers:
        col = headers.index(column_name)
        data = ["'{}'".format(table.item(row, col).text()) if table.item(row, col).text() != 'nan' else 'Null' for row in range(2,nrow)]
    else:
        data = ['Null' for row in range(nrow)]
    return data