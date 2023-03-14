from main import *
from mysql_connection.mysql_connection import *
from mysql_queries.queries_info import *

from datetime import datetime

# Functions to manage MODIFY BIRD tab

def disconnect_signals(ui):
    ui.modif_eventsTableWidget.itemSelectionChanged.disconnect()
    ui.modif_birthyearButton.clicked.disconnect()
    ui.modif_sexButton.clicked.disconnect()
    ui.modif_nameButton.clicked.disconnect()
    ui.modif_deathdateButton.clicked.disconnect()
    ui.save_birthyearButton.clicked.disconnect()
    ui.save_sexButton.clicked.disconnect()
    ui.save_nameButton.clicked.disconnect()
    ui.save_deathdateButton.clicked.disconnect()


def init_modif(ui):
    ui.save_nameButton.hide()
    ui.save_sexButton.hide()
    ui.save_birthyearButton.hide()
    ui.save_deathdateButton.hide()

    ui.cancel_nameButton.hide()
    ui.cancel_sexButton.hide()
    ui.cancel_birthyearButton.hide()
    ui.cancel_deathdateButton.hide()

    ui.choice_modif_manipComboBox.hide()
    ui.save_modif_manipButton.hide()
    ui.cancel_modif_manipButton.hide()

    ui.modif_sexCombobox.hide()

    ui.modif_birth_yearSpinBox.hide()
    ui.modif_birth_year_typeLabel.hide()
    ui.modif_birth_yearComboBox.hide()
    ui.modif_birth_year_unknownButton.hide()

    ui.modif_deathdateComboBox.hide()
    ui.modif_deathdateDateEdit.hide()

    list_type_birth_year = ['obs', 'infer', 'methyl']
    for k in list_type_birth_year:
        ui.modif_birth_yearComboBox.addItem(k)

    list_sex = ["M","F","Unknown","Mobs","Fobs"]
    for sex in list_sex:
        ui.modif_sexCombobox.addItem(sex)

    ui.modif_eventsTableWidget.setColumnHidden(6, True)
    ui.modif_measuresTableWidget.setColumnHidden(4, True)


def init_signals(ui):
    ui.modif_eventsTableWidget.itemSelectionChanged.connect(lambda: init_measures(ui))
    ui.modif_birthyearButton.clicked.connect(lambda: modify_birthyear(ui))
    ui.modif_sexButton.clicked.connect(lambda: modify_sex(ui))
    ui.modif_nameButton.clicked.connect(lambda: modify_name(ui))
    ui.modif_deathdateButton.clicked.connect(lambda: modify_deathdate(ui))
    ui.save_birthyearButton.clicked.connect(lambda: save_birthyearButtonClicked(ui))
    ui.save_sexButton.clicked.connect(lambda: save_sexButtonClicked(ui))
    ui.save_nameButton.clicked.connect(lambda: save_nameButtonClicked(ui))
    ui.save_deathdateButton.clicked.connect(lambda: save_deathdateButtonClicked(ui))

    ui.modif_birth_year_unknownButton.toggled.connect(lambda: modif_birth_year_unknownButtonClicked(ui))

    ui.modif_deathdateComboBox.currentIndexChanged.connect(lambda: modif_deathdateComboBoxChanged(ui))
    ui.cancel_birthyearButton.clicked.connect(lambda: cancel_birthyearButtonClicked(ui))
    ui.cancel_nameButton.clicked.connect(lambda: cancel_nameButtonClicked(ui))
    ui.cancel_sexButton.clicked.connect(lambda: cancel_sexButtonClicked(ui))
    ui.cancel_deathdateButton.clicked.connect(lambda: cancel_deathdateButtonClicked(ui))

    ui.add_modif_manipButton.clicked.connect(lambda: add_modif_manipButtonClicked(ui))
    ui.remove_select_manipsButton.clicked.connect(lambda: remove_select_manipsButtonClicked(ui))

    ui.delete_measureButton.clicked.connect(lambda: delete_measureButtonClicked(ui))
    ui.add_measureButton.clicked.connect(lambda: add_measureButtonClicked(ui))
    ui.modify_measureButton.clicked.connect(lambda: modify_measureButtonClicked(ui))
    ui.add_new_eventButton.clicked.connect(lambda: add_new_eventButtonClicked(ui))
    ui.delete_eventButton.clicked.connect(lambda: delete_eventButtonClicked(ui))
    ui.modif_eventButton.clicked.connect(lambda: modif_eventButtonClicked(ui))

def init_data_rfid(ui, data_rfid):
    ### Initialize known data of the bird
    ui.modify_eventsGroupBox.setEnabled(1)
    ui.modify_commentsGroupBox.setEnabled(1)
    ui.modify_identityGroupBox.setEnabled(1)
    ui.modify_measuresGroupBox.setEnabled(1)
    ui.modify_manipulationsGroupBox.setEnabled(1)

    ui.rfidlineEdit.setText(data_rfid['rfid'])
    ui.modif_nameLabel.setText(data_rfid['name'])
    if data_rfid['sex'] == '':
        ui.modif_sexLabel.setText('Unknown')
        ui.modif_sexCombobox.setCurrentText('Unknown')
    else:
        ui.modif_sexLabel.setText(data_rfid['sex'])
        ui.modif_sexCombobox.setCurrentText(data_rfid['sex'])
    if data_rfid['birth_year']:
        ui.modif_birth_yearLineEdit.setText(str(data_rfid['birth_year']))
    else:
        ui.modif_birth_yearLineEdit.setText('Unknown')

    if data_rfid['dead'] == 1:
        if data_rfid['death_date'] is None:
            ui.modif_deathdateLineEdit.setText("Dead but unknown date")
            ui.modif_deathdateComboBox.setCurrentText("Dead but unknown date")
        else:
            ui.modif_deathdateLineEdit.setText("Dead on "+ str(data_rfid['death_date']))
            ui.modif_deathdateComboBox.setCurrentText("Dead with death date")
            ui.modif_deathdateDateEdit.setDate(data_rfid['death_date'])
            ui.modif_deathdateDateEdit.hide()
    else:
        ui.modif_deathdateLineEdit.setText("No data")
        ui.modif_deathdateComboBox.setCurrentText("No data")

def init_manip_rfid(ui):
    rfid = ui.rfidlineEdit.text()
    data_manip = execute_fetchall("SELECT manip FROM bird_manips WHERE rfid = '{}'".format(rfid))
    ui.modif_maniplistWidget.clear()
    for manip in data_manip:
        ui.modif_maniplistWidget.addItem(manip["manip"])

def init_measures(ui):
    rfid = ui.rfidlineEdit.text()
    row = ui.modif_eventsTableWidget.currentRow()
    data_events = execute_fetchall("SELECT * FROM events WHERE rfid = '{}'".format(rfid))
    if data_events:
        event = data_events[row]
        measures = execute_fetchall("SELECT * FROM measures WHERE event_id = {}".format(event['id']))
        init_selected_measure(ui, measures)
    else:
        ui.modif_measuresTableWidget.setRowCount(0)

### comment section
def init_comments_rfid(ui, comments):
    items = ui.modify_commentsGroupBox.children()
    for item in items[1:]:
        item.deleteLater()
    index = 0
    list_delete_button = []
    list_comment = []
    for comment in comments:
        groupBox = QtWidgets.QGroupBox(ui.modify_commentsGroupBox)
        dtime = comment['date']
        if dtime is not None:
            dtime = dtime.strftime("%Y-%m-%d")
        groupBox.setTitle(comment['handler'] + ' - ' + str(dtime))
        horizontalLayout = QtWidgets.QHBoxLayout(groupBox)
        horizontalLayout.setContentsMargins(0, 0, 0, 0)
        horizontalLayout.setSpacing(5)
        list_comment.append(QtWidgets.QTextBrowser(groupBox))
        list_comment[index].setText(comment['comment'])
        list_comment[index].setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding))
        horizontalLayout.addWidget(list_comment[index])
        verticalLayout = QtWidgets.QVBoxLayout()
        horizontalLayout.addLayout(verticalLayout)
        list_delete_button.append(QtWidgets.QPushButton('Delete'))
        modify_button = QtWidgets.QPushButton('Modify')
        verticalLayout.addWidget(modify_button)
        verticalLayout.addWidget(list_delete_button[index])
        ui.gridLayout_2.addWidget(groupBox, index, 0, 1, 1)
        ui.gridLayout_2.addLayout(verticalLayout, index, 1, 1, 1)
        list_delete_button[index].clicked.connect(lambda _, comment_id=comment['id']: delete_buttonClicked(ui, comment_id))
        modify_button.clicked.connect(
            lambda _, comment_id=comment['id']: modify_buttonClicked(ui, comment_id))
        index += 1
    add_new_comment = QtWidgets.QPushButton('Add new comment')
    add_new_comment.clicked.connect(lambda :add_new_commentClicked(ui))
    ui.gridLayout_2.addWidget(add_new_comment, index, 0, 1, 1)


def delete_buttonClicked(ui, comment_id):
    msg = QMessageBox()
    msg.setWindowTitle("Confirm delete ?")
    msg.setText("Are you sure you want to delete permanently this comment ?")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
    retval = msg.exec_()
    if (retval == QMessageBox.Yes):
        execute_commit("DELETE FROM comments WHERE id = {}".format(comment_id))
        ui.ok_modifButton.click()

def modify_buttonClicked(ui, comment_id):
    msg = QInputDialog()
    comment = execute_fetchall("SELECT comment FROM comments WHERE id ={}".format(comment_id))[0]['comment']
    text, okPressed = QInputDialog.getMultiLineText(msg, "Modify comment", "Modified comment:", comment)
    if okPressed and text != '':
        execute_commit('UPDATE comments SET comment = "{}" WHERE id = {}'.format(text, comment_id))
        ui.ok_modifButton.click()

def add_new_commentClicked(ui):
    msg = QInputDialog()
    text, okPressed = QInputDialog.getMultiLineText(msg, "New comment", "New comment:", '')
    if okPressed and text != '':
        items = get_handlers()
        items = tuple(['']+[item['name'] for item in items])
        item, ok = QInputDialog.getItem(QInputDialog(), "Confirmation",
                                        "Select your name", items, 0, False)
        if item and ok:
            rfid = ui.rfidlineEdit.text()
            execute_commit('INSERT INTO comments (rfid, comment, handler, date) VALUES ("{}", "{}", "{}", "{}")'.format(rfid, text, item, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            ui.ok_modifButton.click()

def init_events(ui):
    rfid = ui.rfidlineEdit.text()
    data_events = execute_fetchall("SELECT * FROM events WHERE rfid = '{}'".format(rfid))
    row = 0
    ui.modif_eventsTableWidget.setRowCount(0)
    ui.modif_eventsTableWidget.setRowCount(len(data_events))
    ui.modif_eventsTableWidget.setEnabled(1)
    for event in data_events:
        dtime = event['event_date']
        if (dtime is not None) & (dtime != '0000-00-00 00:00:00'):
            dtime = dtime.strftime("%Y-%m-%d")
        ui.modif_eventsTableWidget.setItem(row, 0, QTableWidgetItem(dtime))
        ui.modif_eventsTableWidget.setItem(row, 1, QTableWidgetItem(event['event_type']))
        ui.modif_eventsTableWidget.setItem(row, 2, QTableWidgetItem(event['stage']))
        ui.modif_eventsTableWidget.setItem(row, 3, QTableWidgetItem(event['location']))
        ui.modif_eventsTableWidget.setItem(row, 4, QTableWidgetItem(event['handler']))
        ui.modif_eventsTableWidget.setItem(row, 5, QTableWidgetItem(event['comment']))
        ui.modif_eventsTableWidget.setItem(row, 6, QTableWidgetItem(str(event['id'])))
        row += 1
    ui.modif_eventsTableWidget.resizeRowsToContents()
    if len(data_events):
        ui.modif_eventsTableWidget.selectRow(0)


def init_selected_measure(ui, measures):
    ui.modif_measuresTableWidget.setEnabled(1)
    ui.modif_measuresTableWidget.setRowCount(0)
    ui.modif_measuresTableWidget.setRowCount(len(measures))
    row = 0
    for meas in measures:
        ui.modif_measuresTableWidget.setItem(row, 0, QTableWidgetItem(meas['name']))
        ui.modif_measuresTableWidget.setItem(row, 1, QTableWidgetItem(meas['value']))
        ui.modif_measuresTableWidget.setItem(row, 2, QTableWidgetItem(meas['raw_value']))
        ui.modif_measuresTableWidget.setItem(row, 3, QTableWidgetItem(meas['comment']))
        ui.modif_measuresTableWidget.setItem(row, 4, QTableWidgetItem(str(meas['id'])))
        row += 1

def modif_birth_year_unknownButtonClicked(ui):
    if ui.modif_birth_year_unknownButton.isChecked():
        ui.modif_birth_yearSpinBox.setEnabled(0)
        ui.modif_birth_year_typeLabel.setEnabled(0)
        ui.modif_birth_yearComboBox.setEnabled(0)
    else:
        ui.modif_birth_yearSpinBox.setEnabled(1)
        ui.modif_birth_year_typeLabel.setEnabled(1)
        ui.modif_birth_yearComboBox.setEnabled(1)

def cancel_birthyearButtonClicked(ui):
    ui.modif_birthyearButton.show()
    ui.modif_birth_yearLineEdit.show()
    ui.save_birthyearButton.hide()
    ui.cancel_birthyearButton.hide()
    ui.modif_birth_yearSpinBox.hide()
    ui.modif_birth_year_typeLabel.hide()
    ui.modif_birth_yearComboBox.hide()
    ui.modif_birth_year_unknownButton.hide()


def modify_birthyear(ui):
    ui.modif_birthyearButton.hide()
    ui.modif_birth_yearLineEdit.hide()
    ui.save_birthyearButton.show()
    ui.cancel_birthyearButton.show()
    ui.modif_birth_yearSpinBox.show()
    ui.modif_birth_year_typeLabel.show()
    ui.modif_birth_yearComboBox.show()
    ui.modif_birth_year_unknownButton.show()

    if ui.modif_birth_yearLineEdit.text() == 'Unknown':
        ui.modif_birth_year_unknownButton.setChecked(1)
    else:
        ui.modif_birth_yearSpinBox.setValue(int(ui.modif_birth_yearLineEdit.text()))

def save_birthyearButtonClicked(ui):
    rfid = ui.rfidlineEdit.text()
    items = get_handlers()
    items = tuple(['']+[item['name'] for item in items])
    item, ok = QInputDialog.getItem(QInputDialog(), "Confirmation",
                                    "Select your name", items, 0, False)
    if ok and item:
        if ui.modif_birth_year_unknownButton.isChecked():
            birth_year = 'NULL'
            birth_year_type = 'NULL'
        else:
            birth_year = ui.modif_birth_yearSpinBox.value()
            birth_year_type = ui.modif_birth_yearComboBox.currentText()

        old_data = execute_fetchall("SELECT birth_year, birth_year_type FROM birds WHERE rfid = '{}'".format(rfid))[0]
        comment = "Birth year changed from {} - {} to {} - {}".format(old_data['birth_year'], old_data['birth_year_type'], birth_year, birth_year_type)
        birth_year_type = "'{}'".format(birth_year_type)

        execute_commit("UPDATE birds SET birth_year = {}, birth_year_type = {} WHERE rfid = '{}'".format(birth_year, birth_year_type, rfid))
        dtime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execute_commit("INSERT INTO comments (rfid, comment,handler, date) VALUES ('{}', '{}', '{}', '{}')".format(rfid, comment, item, dtime))
        cancel_birthyearButtonClicked(ui)
        ui.ok_modifButton.click()

def modify_name(ui):
    ui.modif_nameButton.hide()
    ui.save_nameButton.show()
    ui.cancel_nameButton.show()
    ui.modif_nameLabel.setReadOnly(False)


def cancel_nameButtonClicked(ui):
    ui.modif_nameButton.show()
    ui.save_nameButton.hide()
    ui.cancel_nameButton.hide()
    ui.modif_nameLabel.setReadOnly(True)
    rfid = ui.rfidlineEdit.text()
    ui.modif_nameLabel.setText(execute_fetchall("SELECT name FROM birds WHERE rfid = '{}'".format(rfid))[0]['name'])

def save_nameButtonClicked(ui):
    rfid = ui.rfidlineEdit.text()
    items = get_handlers()
    items = tuple(['']+[item['name'] for item in items])
    item, ok = QInputDialog.getItem(QDialog(), "Confirmation",
                                    "Select your name", items, 0, False)
    if ok and item:
        name = ui.modif_nameLabel.text()
        old_name = execute_fetchall("SELECT name FROM birds WHERE rfid = '{}'".format(rfid))[0]['name']
        if name != old_name:
            if len(execute_fetchall("SELECT name FROM birds WHERE name = '{}'".format(name))):
                QMessageBox.information(QMessageBox(), 'Error', "This name already exists")
            else:
                comment = "Name changed from {} to {}".format(old_name,name)
                execute_commit(
                    "UPDATE birds SET name = '{}' WHERE rfid = '{}'".format(name, rfid))
                execute_commit(
                    "INSERT INTO comments (rfid, comment,handler, date) VALUES ('{}', '{}', '{}', '{}')".format(
                        rfid, comment, item, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                ui.modif_nameLabel.setReadOnly(True)
                cancel_nameButtonClicked(ui)
                ui.ok_modifButton.click()


def modify_sex(ui):
    ui.modif_sexButton.hide()
    ui.save_sexButton.show()
    ui.cancel_sexButton.show()
    ui.modif_sexCombobox.show()
    ui.modif_sexCombobox.setEnabled(True)
    ui.modif_sexLabel.hide()


def cancel_sexButtonClicked(ui):
    ui.modif_sexButton.show()
    ui.save_sexButton.hide()
    ui.cancel_sexButton.hide()
    ui.modif_sexCombobox.hide()
    ui.modif_sexLabel.show()

def save_sexButtonClicked(ui):
    rfid = ui.rfidlineEdit.text()
    items = get_handlers()
    items = tuple(['']+[item['name'] for item in items])
    item, ok = QInputDialog.getItem(QDialog(), "Confirmation",
                                    "Select your name", items, 0, False)
    if ok and item:
        sex = ui.modif_sexCombobox.currentText()
        old_sex = ui.modif_sexLabel.text()
        if sex != old_sex:
            comment = "Sex changed from {} to {}".format(old_sex, sex)
            if sex == 'Unknown':
                sex = 'Null'
            else:
                sex = "'{}'".format(sex)
            execute_commit(
                "UPDATE birds SET sex = {} WHERE rfid = '{}'".format(sex, rfid))
            execute_commit(
                "INSERT INTO comments (rfid, comment,handler, date) VALUES ('{}', '{}', '{}', '{}')".format(
                    rfid, comment, item, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        cancel_sexButtonClicked(ui)
        ui.ok_modifButton.click()

def modify_deathdate(ui):
    ui.modif_deathdateButton.hide()
    ui.save_deathdateButton.show()
    ui.cancel_deathdateButton.show()

    ui.modif_deathdateComboBox.show()
    ui.modif_deathdateLineEdit.hide()
    if ui.modif_deathdateComboBox.currentText() == "Dead with death date":
        ui.modif_deathdateDateEdit.show()
    else:
        ui.modif_deathdateDateEdit.hide()

def cancel_deathdateButtonClicked(ui):
    ui.modif_deathdateButton.show()
    ui.save_deathdateButton.hide()
    ui.cancel_deathdateButton.hide()
    ui.modif_deathdateLineEdit.show()
    ui.modif_deathdateDateEdit.hide()
    ui.modif_deathdateComboBox.hide()

def modif_deathdateComboBoxChanged(ui):
    if ui.modif_deathdateComboBox.currentText() == "Dead with death date":
        ui.modif_deathdateDateEdit.show()
    else:
        ui.modif_deathdateDateEdit.hide()

def save_deathdateButtonClicked(ui):
    rfid = ui.rfidlineEdit.text()
    items = get_handlers()
    items = tuple(['']+[item['name'] for item in items])
    item, ok = QInputDialog.getItem(None, "Confirmation",
                                    "Select your name", items, 0, False)
    if ok and item:
        state = ui.modif_deathdateComboBox.currentText()
        if state == "No data":
            dead = 0
            death_date = 'Null'
        elif state == "Dead but unknown date":
            dead = 1
            death_date = 'Null'
        else:
            dead = 1
            death_date = "'{}'".format(ui.modif_deathdateDateEdit.date().toString("yyyy-MM-dd"))
            state = "Dead on "+ str(ui.modif_deathdateDateEdit.date().toString("yyyy-MM-dd"))

        if state != ui.modif_deathdateLineEdit.text():
            comment = "Death changed from {} to {}".format(ui.modif_deathdateLineEdit.text(), state)
            execute_commit(
                "UPDATE birds SET dead = {}, death_date = {} WHERE rfid = '{}'".format(dead, death_date, rfid))
            execute_commit(
                "INSERT INTO comments (rfid, comment,handler, date) VALUES ('{}', '{}', '{}', '{}')".format(
                    rfid, comment, item, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        cancel_deathdateButtonClicked(ui)
        ui.ok_modifButton.click()

def add_modif_manipButtonClicked(ui):
    manips = get_manips()
    manips = tuple([''] + [manip['name'] for manip in manips])
    manip, ok = QInputDialog.getItem(QInputDialog(), "Add to a manipulation",
                                        "Select manipulation", manips, 0, False)

    if manip and ok:
        items = get_handlers()
        items = tuple(['']+[item['name'] for item in items])
        item, ok = QInputDialog.getItem(QInputDialog(), "Confirmation",
                                        "Select your name", items, 0, False)
        if item and ok:
            rfid = ui.rfidlineEdit.text()
            comment = "Added by " + str(item) + "on " + datetime.now().strftime("%Y-%m-%d")
            execute_commit('INSERT INTO bird_manips (rfid, manip, comment) VALUES ("{}", "{}", "{}")'.format(rfid, manip, comment))
            ui.ok_modifButton.click()

def remove_select_manipsButtonClicked(ui):
    if ui.modif_maniplistWidget.currentItem():
        manip = ui.modif_maniplistWidget.currentItem().text()
        rfid = ui.rfidlineEdit.text()
        msg = QMessageBox()
        msg.setWindowTitle("Confirm removing")
        msg.setText("Are you sure you want to remove the bird from {} ?".format(manip))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        retval = msg.exec_()
        if (retval == QMessageBox.Yes):
            execute_commit("DELETE FROM bird_manips WHERE rfid = '{}' AND manip = '{}'".format(rfid, manip))
            ui.ok_modifButton.click()

def delete_measureButtonClicked(ui):
    rfid = ui.rfidlineEdit.text()
    row_event = ui.modif_eventsTableWidget.currentRow()
    event, event_date = ui.modif_eventsTableWidget.item(row_event, 1).text(), ui.modif_eventsTableWidget.item(row_event, 0).text()
    row = ui.modif_measuresTableWidget.currentRow()
    if row == -1:
        return
    measure_id = int(ui.modif_measuresTableWidget.item(row, 4).text())
    measure, value = ui.modif_measuresTableWidget.item(row, 0).text(), ui.modif_measuresTableWidget.item(row, 1).text()
    msg = QMessageBox()
    msg.setWindowTitle("Confirm removing")
    msg.setText("Are you sure you want to delete the measure {} = {} ?".format(measure, value))
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
    retval = msg.exec_()
    if (retval == QMessageBox.Yes):
        items = get_handlers()
        items = tuple(['']+[item['name'] for item in items])
        item, ok = QInputDialog.getItem(QInputDialog(), "Confirmation",
                                        "Select your name", items, 0, False)
        if item and ok:
            comment = "Removing of the measure {} = {} from the {} event of the {}".format(measure, value, event, event_date)
            execute_commit("DELETE FROM measures WHERE id = {}".format(measure_id))
            execute_commit(
                "INSERT INTO comments (rfid, comment,handler, date) VALUES ('{}', '{}', '{}', '{}')".format(
                    rfid, comment, item, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            ui.ok_modifButton.click()

def add_measureButtonClicked(ui):
    items = get_handlers()
    items = tuple(['']+[item['name'] for item in items])
    handler, ok = QInputDialog.getItem(QInputDialog(), "Confirmation",
                                    "Select your name", items, 0, False)
    if handler and ok:
        dial = QInputDialog()
        dial.setWindowTitle("Add new measure")
        dial.setLabelText("")
        dial.show()
        dial.findChild(QtWidgets.QLineEdit).hide()

        layout = QFormLayout(dial)

        measureCombobox = QtWidgets.QComboBox()
        measure_types = get_measure_types()
        for measure in measure_types:
            measureCombobox.addItem(measure['name'] + " ({} ; {})".format(measure['unit'], measure['description']))
        layout.addRow(QtWidgets.QLabel("Measure*: "), measureCombobox)

        value_edit = QtWidgets.QLineEdit()
        layout.addRow(QtWidgets.QLabel("Value*: "), value_edit)

        raw_value_edit = QtWidgets.QLineEdit()
        layout.addRow(QtWidgets.QLabel("Raw value (separated by ;): "), raw_value_edit)

        comment_edit = QtWidgets.QLineEdit("Added by {} the {}".format(handler, datetime.now().strftime("%Y-%m-%d")))
        layout.addRow(QtWidgets.QLabel("Comment: "), comment_edit)

        dial.layout().insertLayout(1, layout)


        row_event = ui.modif_eventsTableWidget.currentRow()
        event_id = ui.modif_eventsTableWidget.item(row_event, 6).text()
        if dial.exec_():
            if value_edit.text != '':
                execute_commit('INSERT INTO measures (event_id, name, value, raw_value, comment) VALUES ({}, "{}", "{}", "{}", "{}")'.format(
                    event_id, measure_types[measureCombobox.currentIndex()]['name'], value_edit.text(), raw_value_edit.text(), comment_edit.text()))
                ui.ok_modifButton.click()


def modify_measureButtonClicked(ui):
    if ui.modif_measuresTableWidget.currentRow() > -1:
        items = get_handlers()
        items = tuple(['']+[item['name'] for item in items])
        handler, ok = QInputDialog.getItem(QInputDialog(), "Confirmation",
                                        "Select your name", items, 0, False)
        if handler and ok:
            dial = QInputDialog()
            dial.setWindowTitle("Modify measure")
            dial.setLabelText("")
            dial.show()
            dial.findChild(QtWidgets.QLineEdit).hide()

            current_row = ui.modif_measuresTableWidget.currentRow()
            layout = QFormLayout(dial)

            measureCombobox = QtWidgets.QComboBox()
            measure_types = get_measure_types()
            old_measure = ui.modif_measuresTableWidget.item(current_row, 0).text()
            for measure in measure_types:
                measureCombobox.addItem(measure['name'] + " ({} ; {})".format(measure['unit'], measure['description']))
                if measure['name'] == old_measure:
                    measureCombobox.setCurrentIndex(measureCombobox.count()-1)
            layout.addRow(QtWidgets.QLabel("Measure*: "), measureCombobox)

            value_edit = QtWidgets.QLineEdit(ui.modif_measuresTableWidget.item(current_row, 1).text())
            layout.addRow(QtWidgets.QLabel("Value*: "), value_edit)

            raw_value_edit = QtWidgets.QLineEdit(ui.modif_measuresTableWidget.item(current_row, 2).text())
            layout.addRow(QtWidgets.QLabel("Raw value (separated by ;): "), raw_value_edit)

            comment_edit = QtWidgets.QLineEdit("Changed by {} the {} ; ".format(handler, datetime.now().strftime("%Y-%m-%d")) + ui.modif_measuresTableWidget.item(current_row, 3).text())
            layout.addRow(QtWidgets.QLabel("Comment: "), comment_edit)

            dial.layout().insertLayout(1, layout)


            row_event = ui.modif_eventsTableWidget.currentRow()
            event_id = ui.modif_eventsTableWidget.item(row_event, 6).text()
            if dial.exec_():
                if value_edit.text != '':
                    execute_commit('UPDATE measures SET name = "{}", value = "{}", raw_value = "{}", comment = "{}" WHERE id = {}'.format(
                        measure_types[measureCombobox.currentIndex()]['name'], value_edit.text(), raw_value_edit.text(),
                        comment_edit.text(), ui.modif_measuresTableWidget.item(current_row, 4).text()))
                    ui.ok_modifButton.click()


def add_new_eventButtonClicked(ui):
    items = get_handlers()
    items = tuple(['']+[item['name'] for item in items])
    user, ok = QInputDialog.getItem(QInputDialog(), "Confirmation",
                                    "Select your name", items, 0, False)
    if user and ok:
        dial = QInputDialog()
        dial.setWindowTitle("Add new event")
        dial.setLabelText("")
        dial.show()
        dial.findChild(QtWidgets.QLineEdit).hide()

        layout = QFormLayout(dial)

        datewidget = QDateEdit()
        layout.addRow(QtWidgets.QLabel("Date: "), datewidget)

        typeCombobox = QtWidgets.QComboBox()
        event_types = get_event_types()
        for type in event_types:
            typeCombobox.addItem(type['name'] + " ({})".format(type['class']))
        layout.addRow(QtWidgets.QLabel("Type: "), typeCombobox)

        stageCombobox = QtWidgets.QComboBox()
        stages = get_stages()
        for stage in stages:
            stageCombobox.addItem(stage['name'] + " ({})".format(stage['class']))
        layout.addRow(QtWidgets.QLabel("Bird stage: "), stageCombobox)

        locationCombobox = QtWidgets.QComboBox()
        locations = get_locations()
        for location in locations:
            locationCombobox.addItem(location['name'] + " ({})".format(location['colony']))
        layout.addRow(QtWidgets.QLabel("Location: "), locationCombobox)

        handlerCombobox = QtWidgets.QComboBox()
        handlers = get_handlers()
        for handler in handlers:
            handlerCombobox.addItem(handler['name'])
        layout.addRow(QtWidgets.QLabel("Handler: "), handlerCombobox)

        comment_edit = QtWidgets.QTextEdit("Added by {} the {}".format(user, datetime.now().strftime("%Y-%m-%d")))
        layout.addRow(QtWidgets.QLabel("Comment: "), comment_edit)

        dial.layout().insertLayout(1, layout)

        if dial.exec_():
            rfid = ui.rfid_modifLineEdit.text()
            date = datewidget.date().toString("yyyy-MM-dd")
            type = event_types[typeCombobox.currentIndex()]['name']
            stage = stages[stageCombobox.currentIndex()]['name']
            location = locations[locationCombobox.currentIndex()]['name']
            handler = handlers[handlerCombobox.currentIndex()]['name']
            comment = comment_edit.toPlainText()
            execute_commit('INSERT INTO events (rfid, event_date, event_type, stage, location, handler, comment) VALUES '
                           '("{}", "{}", "{}", "{}", "{}", "{}", "{}")'.format(rfid, date, type, stage, location, handler, comment))
            ui.ok_modifButton.click()

def delete_eventButtonClicked(ui):
    rfid = ui.rfidlineEdit.text()
    row_event = ui.modif_eventsTableWidget.currentRow()
    event, event_date = ui.modif_eventsTableWidget.item(row_event, 1).text(), ui.modif_eventsTableWidget.item(row_event, 0).text()
    if row_event == -1:
        return

    msg = QMessageBox()
    msg.setWindowTitle("Confirm removing")
    msg.setText("Are you sure you want to delete the event {} and all associated measures ?".format(event))
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
    retval = msg.exec_()
    if (retval == QMessageBox.Yes):
        items = get_handlers()
        items = tuple(['']+[item['name'] for item in items])
        item, ok = QInputDialog.getItem(QInputDialog(), "Confirmation",
                                        "Select your name", items, 0, False)
        if item and ok:
            comment = "Event {} of the {} removed".format(event, event_date)
            execute_commit("DELETE FROM measures WHERE event_id = {}".format(ui.modif_eventsTableWidget.item(row_event, 6).text()))
            execute_commit("DELETE FROM events WHERE id = {}".format(ui.modif_eventsTableWidget.item(row_event, 6).text()))
            execute_commit(
                "INSERT INTO comments (rfid, comment,handler, date) VALUES ('{}', '{}', '{}', '{}')".format(
                    rfid, comment, item, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            ui.ok_modifButton.click()

def modif_eventButtonClicked(ui):
    items = get_handlers()
    items = tuple(['']+[item['name'] for item in items])
    user, ok = QInputDialog.getItem(QInputDialog(), "Confirmation",
                                    "Select your name", items, 0, False)

    row_event = ui.modif_eventsTableWidget.currentRow()
    if user and ok:
        dial = QInputDialog()
        dial.setWindowTitle("Modify event")
        dial.setLabelText("")
        dial.show()
        dial.findChild(QtWidgets.QLineEdit).hide()

        layout = QFormLayout(dial)

        old_date = QDate.fromString(ui.modif_eventsTableWidget.item(row_event,0).text(), "yyyy-MM-dd")
        datewidget = QDateEdit(old_date)
        layout.addRow(QtWidgets.QLabel("Date: "), datewidget)

        typeCombobox = QtWidgets.QComboBox()
        event_types = get_event_types()
        for type in event_types:
            typeCombobox.addItem(type['name'] + " ({})".format(type['class']))
            if type['name'] == ui.modif_eventsTableWidget.item(row_event,1).text():
                typeCombobox.setCurrentIndex(typeCombobox.count()-1)
        layout.addRow(QtWidgets.QLabel("Type: "), typeCombobox)

        stageCombobox = QtWidgets.QComboBox()
        stages = get_stages()
        for stage in stages:
            stageCombobox.addItem(stage['name'] + " ({})".format(stage['class']))
            if stage['name'] == ui.modif_eventsTableWidget.item(row_event,2).text():
                stageCombobox.setCurrentIndex(stageCombobox.count()-1)
        layout.addRow(QtWidgets.QLabel("Bird stage: "), stageCombobox)

        locationCombobox = QtWidgets.QComboBox()
        locations = get_locations()
        for location in locations:
            locationCombobox.addItem(location['name'] + " ({})".format(location['colony']))
            if location['name'] == ui.modif_eventsTableWidget.item(row_event,3).text():
                locationCombobox.setCurrentIndex(locationCombobox.count()-1)
        layout.addRow(QtWidgets.QLabel("Location: "), locationCombobox)

        handlerCombobox = QtWidgets.QComboBox()
        handlers = get_handlers()
        for handler in handlers:
            handlerCombobox.addItem(handler['name'])
            if handler['name'] == ui.modif_eventsTableWidget.item(row_event,4).text():
                handlerCombobox.setCurrentIndex(handlerCombobox.count()-1)
        layout.addRow(QtWidgets.QLabel("Handler: "), handlerCombobox)

        comment_edit = QtWidgets.QTextEdit("Changed by {} the {} ; ".format(user, datetime.now().strftime("%Y-%m-%d")) + ui.modif_eventsTableWidget.item(row_event,5).text())
        layout.addRow(QtWidgets.QLabel("Comment: "), comment_edit)

        dial.layout().insertLayout(1, layout)

        if dial.exec_():
            event_id = ui.modif_eventsTableWidget.item(row_event,6).text()
            rfid = ui.rfid_modifLineEdit.text()
            date = datewidget.date().toString("yyyy-MM-dd")
            type = event_types[typeCombobox.currentIndex()]['name']
            stage = stages[stageCombobox.currentIndex()]['name']
            location = locations[locationCombobox.currentIndex()]['name']
            handler = handlers[handlerCombobox.currentIndex()]['name']
            comment = comment_edit.toPlainText()
            execute_commit('UPDATE events SET rfid = "{}", event_date = "{}", event_type = "{}", stage = "{}", '
                           'location = "{}", handler = "{}", comment = "{}" WHERE id = {}'.format(rfid, date, type, stage, location, handler, comment, event_id))
            ui.ok_modifButton.click()