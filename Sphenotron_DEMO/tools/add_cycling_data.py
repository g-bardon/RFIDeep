from main import *
from tools.tools import determine_year

def add_cycle(rfid, start_dtime, end_dtime, type):
    dial = QInputDialog()
    dial.setWindowTitle("Add breeding data")
    dial.setLabelText("")
    dial.show()
    dial.findChild(QtWidgets.QLineEdit).hide()

    layout = QFormLayout(dial)

    start_dtimeDateEdit = QtWidgets.QDateTimeEdit(start_dtime)

    if type == 'breeding':
        layout.addRow(QtWidgets.QLabel("Start date*: "), start_dtimeDateEdit)
        end_dtimeDateEdit = QtWidgets.QDateTimeEdit(end_dtime)
        layout.addRow(QtWidgets.QLabel("End date*: "), end_dtimeDateEdit)
        season = determine_year(start_dtime)
    else:
        layout.addRow(QtWidgets.QLabel("Date*: "), start_dtimeDateEdit)


    comment_edit = QtWidgets.QLineEdit()

    handlerCombobox = QtWidgets.QComboBox()
    handlerCombobox.currentIndexChanged.connect(lambda: handlerComboboxChanged(comment_edit, handlerCombobox))
    list_handlers = get_handlers()
    for handler in list_handlers:
        handlerCombobox.addItem(handler['name'])
    layout.addRow(QtWidgets.QLabel("Handler*: "), handlerCombobox)

    if type == 'breeding':
        valueCombobox = QtWidgets.QComboBox()
        valueCombobox.addItems(['NB','F','S'])
        layout.addRow(QtWidgets.QLabel("Value*: "), valueCombobox)

        bsexCombobox = QtWidgets.QComboBox()
        bsexCombobox.addItems(['Unknown', 'Male', 'Female'])
        layout.addRow(QtWidgets.QLabel("Behavioral sex*: "), bsexCombobox)
    else:
        phenology_typeComboBox = QtWidgets.QComboBox()
        phenology_type_list = [k['name'] for k in get_phenology_types()]
        phenology_typeComboBox.addItems(phenology_type_list)
        layout.addRow(QtWidgets.QLabel("Name: "), phenology_typeComboBox)
        typeComboBox = QtWidgets.QComboBox()
        typeComboBox.addItems(['Observation', 'Cycling'])
        layout.addRow(QtWidgets.QLabel("Type: "), typeComboBox)

    layout.addRow(QtWidgets.QLabel("Comment: "), comment_edit)

    dial.layout().insertLayout(1, layout)


    if dial.exec_():
        comment = comment_edit.text().replace("'","").replace('"','')
        if type == 'breeding':
            bsex = bsexCombobox.currentText()
            bsex = bsex.replace('Female','"F"')
            bsex = bsex.replace('Male', '"M"').replace('Unknown','Null')
            query = f'INSERT INTO cycling (rfid, season, value, behavioral_sex, start_dtime, end_dtime, comment) VALUES ' \
                f'("{rfid}",{season},"{valueCombobox.currentText()}",{bsex},"{start_dtimeDateEdit.dateTime().toPyDateTime()}","{end_dtimeDateEdit.dateTime().toPyDateTime()}","{comment}")'
            execute_commit(query)
        else:
            # change type format
            # remove ' and " from comment
            type = typeComboBox.currentText().replace("Observation", "obs").replace('Cycling', 'cycle')
            query = f'INSERT INTO phenology (rfid, name, type, date, comment) VALUES ' \
                    f'("{rfid}","{phenology_typeComboBox.currentText()}","{type}","{start_dtimeDateEdit.dateTime().toPyDateTime()}","{comment}")'
            execute_commit(query)
        return 1
    else:
        return 0

def handlerComboboxChanged(comment_edit,handlerCombobox):
    handler = handlerCombobox.currentText()
    comment_edit.setText(f'Added by {handler}')
