import sys

import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QAbstractItemView, QTreeWidgetItem, QVBoxLayout, QWidgetAction, QMenu, QGraphicsRectItem
from PyQt5.QtCore import Qt, pyqtSlot
import pyqtgraph as pg
from PyQt5.QtGui import QFont
from PyQt5 import QtSvg
from animalWidget_view import *
from mysql_queries.queries_info import *
from tools.tools import *
from tools.DateAxis import *
from tools.customViewBox import *
from tools.correction_missing_detections import *
from datetime import datetime
# import datetime
class animalWidget(QWidget):
    def __init__(self, parent=None, rfid=None, partner=None):
        super().__init__(parent)

        self.settings_user = QSettings("sphenotron", "user")
        self.db = settings_connexion.value("database")
        self.rfid = rfid

        ### get instance of the UI (only view, no signals), from animalWidget_view.py (generated by QT Creator)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.init_view()
        self.show_comparison = False
        self.second_rfid = None

        if partner is not None:
            self.show_comparison = True
            self.second_rfid = partner
            self.detections_second_rfid, self.transitions_second_rfid = self.init_detect_transi(self.second_rfid)

        self.min_date = get_first_detection(self.rfid)  # Minimum date of the cycle
        self.date_dd = get_last_detection(self.rfid) # Maximum date of the cycle

        if self.date_dd == ():
            self.max_date = None
        else:
            self.max_date = self.date_dd[0]["last_detection"]  # Maximum date of the cycle
        self.texts = {}

        self.antenna_to_location = from_antenna_to_location()

        # Initialize what type of detections to show
        self.is_original = True
        self.is_logiques = True
        self.is_calculees = False

        self.mysignal = signal_refresh()
        self.mysignal.signal_refresh_cycle.connect(self.refresh_cycling_data)
        # initialization of informations
        self._set_informations()
        self.detections, self.transitions = self.init_detect_transi(self.rfid) ### 50% of time of this step is due to detections fetch and the other half is for correction of detections
        self.cycle_list = []
        self.computed_cycle_list = []
        self.cycle_line_list = []
        self.cycle_text_list = []

        # Start construction of cycle graph
        self._graph_construction()

        # signals
        self.ui.change_alarmPushButton.pressed.connect(self.change_alarm)
        self.ui.cancel_alarmPushButton.pressed.connect(self.close_change_alarm)
        self.ui.save_alarmPushButton.pressed.connect(self.save_alarm)
        self.ui.add_commentPushButton.pressed.connect(self.new_comment)
        self.ui.cancel_new_commentPushButton.pressed.connect(self.close_add_comment)
        self.ui.save_new_commentPushButton.pressed.connect(self.save_new_comment)
        self.ui.compare_rfid_showPushButton.pressed.connect(self.compare_rfid_showPushButtonClicked)
        self.ui.compare_rfid_hidePushButton.pressed.connect(self.compare_rfid_hidePushButtonClicked)
        self.ui.eventListWidget.itemSelectionChanged.connect(self.eventListWidgetSelectionChanged)
        self.ui.logicalDetectionsCheckBox.stateChanged.connect(self.detections_showedChanged)
        self.ui.computedDetectionsCheckBox.stateChanged.connect(self.detections_showedChanged)
        self.ui.show_cyclingCheckbox.stateChanged.connect(self.show_cycling_changed)
        self.ui.show_computed_cyclingCheckbox.stateChanged.connect(self.show_cycling_changed)
        self.ui.modif_cycle_cancel_button.clicked.connect(self.modif_cycle_cancel_buttonClicked)
        self.ui.modif_cycle_delete_button.clicked.connect(self.modif_cycle_delete_buttonClicked)
        self.ui.modif_cycle_save_button.clicked.connect(self.modif_cycle_save_buttonClicked)

    # ------------------------------------------- IMPLEMENTATION DES METHODES DE LA VUE ------------------------------------

    def init_view(self):
        self.ui.change_alarmFrame.hide()
        self.ui.new_commentFrame.hide()
        self.ui.modify_cycleFrame.hide()

        self.ui.bsex_comboBox.addItems(['','M','F'])
        self.ui.cycle_value_comboBox.addItems(['NB', 'F', 'S'])

    def refresh_cycling_data(self):
        self._graph_completion(self.plot)

    def zoom_graph(self):
        """ Update data while zooming on the graph """
        coord = 6.5
        coord_second = 4.5
        if self.show_comparison:
            coord = 9.5

        for i in self.texts:
            self.plot.removeItem(self.texts[i])

        text_default = pg.TextItem("xxxx", anchor=(0.5, 0.5))
        br = text_default.boundingRect()
        sx, sy = self.viewbox.viewPixelSize()
        longueur_text = sx * br.width()
        viewrange = self.viewbox.viewRange()

        def plot_transit(transitions, coord):
            for transition in transitions:
                if transition["text_transition"] != "":
                    time1 = int(transition["date1"].timestamp())
                    time2 = int(transition["date2"].timestamp())
                    if (time1 >= int(viewrange[0][0]) and time2 <= int(viewrange[0][1])) and (
                            time2 - time1) > longueur_text:
                        if transition["departure"] == 0:
                            y_text = coord - 0.25
                        else:
                            y_text = coord + 0.25
                        x_text = int((time1 + time2) / 2)
                        text = pg.TextItem("", anchor=(0.5, 0.5))
                        text.setPos(x_text, y_text)
                        text.setColor('w')
                        self.plot.addItem(text)
                        text.setText(transition["text_transition"])
                        nom = "text_" + str(time1)
                        self.texts[nom] = text

        plot_transit(self.transitions, coord)

        if self.show_comparison:
            plot_transit(self.transitions_second_rfid, coord_second)

        try:
            xpos = self.viewbox.viewRange()[0][0]
            self.text_computed_cycle.setPos(xpos, 2.25)
            self.text_cycle.setPos(xpos, 3.35)
        except:
            pass

    # ------------------------------------------- INITIALISATION ---------------------------------------------

    def init_detect_transi(self, rfid):
        # compute transitions from corrected detections
        det = get_all_detections_original(rfid)
        if det:
            ### Correction of missing detections
            det += fill_gaps(rfid, self.db, det)
            ### Sort of detections
            det = sorted(det, key=lambda x: x['dtime'])
            if not self.ui.logicalDetectionsCheckBox.isChecked():
                det = [x for x in det if x['type'] != 'logical']
            if not self.ui.computedDetectionsCheckBox.isChecked():
                det = [x for x in det if x['type'] != 'probabilistic']
            # Computation of transitions from detections
            trans = compute_transitions(det)
            return det, trans
        else:
            return [], []

    def _graph_construction(self):
        """ Build center graph

        :return: PlotItem, ViewBox and Axis
        """
        self.plot, self.viewbox, self.top_axis = self._graph_initialization()
        self._plot_initialisation(self.plot)
        self.plot.sigXRangeChanged.connect(self.zoom_graph)



    def _graph_initialization(self):
        """ Initialize central graph

        :return: PlotItem, ViewBox and Axis of initialized graph
        """
        try:
            self.window = pg.GraphicsLayout()
            self.ui.graphicsView.setCentralWidget(self.window)
            self.ui.graphicsView.setBackground(None)

            top_axis = DateAxis('top')

            plot = MyPlotItem(axisItems={'top': top_axis}, rfid=self.rfid, mysignal=self.mysignal)
            viewbox = plot.getViewBox()
            viewbox.setMenuEnabled(enableMenu=False)
            viewbox.setLimits(minXRange=1000)
            if len(self.detections) == 0:
                viewbox.setMouseEnabled(x=False, y=False)
            else:
                viewbox.setMouseEnabled(x=True, y=False)
            viewbox.setBackgroundColor(pg.mkBrush(150, 150, 150, 100))
            if self.min_date is None:
                viewbox.setLimits(xMin=int(datetime(2015, 1, 1, 0, 0, 0).timestamp()) - 62536000,
                                  xMax=int(datetime(2017, 12, 31, 0, 0, 0).timestamp()) + 62536000)
            else:
                min_date = self.min_date
                max_date = self.max_date
                if self.show_comparison:
                    min_date_second_rfid = get_first_detection(self.second_rfid)
                    if min_date_second_rfid:
                        min_date = min([self.min_date, min_date_second_rfid])
                    last_det_date = get_last_detection(self.second_rfid)
                    if last_det_date:
                        max_date_second_rfid = last_det_date[0]["last_detection"]
                        max_date = max([self.max_date, max_date_second_rfid])

                viewbox.setLimits(xMin=int(min_date.timestamp()) - 31536000,  # one year before the first detection
                                  xMax=int(max_date.timestamp()) + 31536000)  # one year after the last detection

            left_axis = plot.getAxis('left')
            bottom_axis = plot.getAxis('bottom')
            bottom_axis.hide()
            left_axis.hide()
            top_axis.setStyle(stopAxisAtTick=(True, False), autoExpandTextSpace=False, tickTextHeight=30)
            top_axis.show()
            plot.hideButtons()
            plot.showGrid(x=True, y=False, alpha=0.3)
            plot.setYRange(1, 12)

            if self.min_date is None:
                plot.setXRange(int(datetime(2015, 1, 1, 0, 0, 0).timestamp()),
                               int(datetime(2015, 1, 1, 0, 0, 0).timestamp()))
            else:
                plot.setXRange(int(self.min_date.timestamp()) - 86400000, int(self.max_date.timestamp()) + 86400000)
            self.window.addItem(plot)

        except Exception as e:
            print(e)
        return plot, viewbox, top_axis

    def _plot_initialisation(self, plot):
        """ Build elements of the graph

        :param plot: PlotItem
        """
        self.line = pg.InfiniteLine(pos=0, angle=0, pen='k')
        self._graph_detections(plot, comparison=False)

        if self.show_comparison:
            self._graph_detections(plot, comparison=True)
            self._graph_transitions(plot, comparison=True)
            self._graph_comparison(plot)

        self._graph_transitions(plot, comparison=False)

        self._graph_completion(plot)
        self.window.scene().sigMouseClicked.connect(self.onClick)
        self.LRI_activated = 0  ## Indicate if modification tool is activated or not
        self.line_activated = 0

    def _graph_detections(self, plot, comparison):
        """ Build detections in the graph.

        :param plot: PlotItem
        """
        detections = self.detections

        coord = 6.5
        if self.show_comparison:
            coord = 9.5
        if comparison:
            coord = 4.5
            detections = self.detections_second_rfid

        up = {}
        down = {}
        up_logique = {}
        down_logique = {}
        up_calculee = {}
        down_calculee = {}
        up["x"] = []
        up["y"] = []
        down["x"] = []
        down["y"] = []
        up_logique["x"] = []
        up_logique["y"] = []
        down_logique["x"] = []
        down_logique["y"] = []
        up_calculee["x"] = []
        up_calculee["y"] = []
        down_calculee["x"] = []
        down_calculee["y"] = []
        for detection in detections:
            time = detection["dtime"].timestamp()
            type_detect = str(detection["type"])
            location = self.antenna_to_location[detection["antenna_id"] - 1]["side"]
            if location == "Mer" and type_detect == "original":
                down["x"].append(time)
                down["y"].append(coord - 1)
            elif location == "Terre" and type_detect == "original":
                up["x"].append(time)
                up["y"].append(coord + 1)
            elif location == "Mer" and type_detect == "logical":
                down_logique["x"].append(time)
                down_logique["y"].append(coord - 1)
            elif location == "Terre" and type_detect == "logical":
                up_logique["x"].append(time)
                up_logique["y"].append(coord + 1)
            elif location == "Mer" and type_detect == "probabilistic":
                down_calculee["x"].append(time)
                down_calculee["y"].append(coord - 1)
            elif location == "Terre" and type_detect == "probabilistic":
                up_calculee["x"].append(time)
                up_calculee["y"].append(coord + 1)

        # Colour settings
        brush_down = pg.mkBrush((0, 0, 139), width=10)
        pen_down = pg.mkPen((0, 0, 139), width=0.1)
        brush_up = pg.mkBrush((255, 128, 0), width=10)
        pen_up = pg.mkPen((255, 128, 0), width=0.1)
        brush_calculee = pg.mkBrush((255, 0, 0), width=0.1)
        pen_calculee = pg.mkPen((255, 0, 0), width=0.1)
        brush_down_logique = pg.mkBrush((0, 144, 255), width=0.1)
        pen_down_logique = pg.mkPen((0, 144, 255), width=0.1)
        brush_up_logique = pg.mkBrush((255, 213, 0), width=0.1)
        pen_up_logique = pg.mkPen((255, 213, 0), width=0.1)

        plot.scatterPlot(down["x"], down["y"], brush=brush_down, pen=pen_down, symbol="x", size=10)
        plot.scatterPlot(up["x"], up["y"], brush=brush_up, pen=pen_up, symbol="x", size=10)
        if len(up_calculee["x"]) > 0:
            plot.scatterPlot(up_calculee["x"], up_calculee["y"], brush=brush_calculee, pen=pen_calculee, symbol="x",
                             size=10)
        if len(down_calculee["x"]) > 0:
            plot.scatterPlot(down_calculee["x"], down_calculee["y"], brush=brush_calculee, pen=pen_calculee, symbol="x",
                             size=10)
        if len(up_logique["x"]) > 0:
            plot.scatterPlot(up_logique["x"], up_logique["y"], brush=brush_up_logique, pen=pen_up_logique, symbol="x",
                             size=10)
        if len(down_logique["x"]) > 0:
            plot.scatterPlot(down_logique["x"], down_logique["y"], brush=brush_down_logique, pen=pen_down_logique,
                             symbol="x", size=10)

    def _graph_transitions(self, plot, comparison):
        """ Build transitions in the graph.

        :param plot: PlotItem
        """
        transitions = self.transitions
        coord = 6.5
        if self.show_comparison:
            coord = 9.5
        if comparison:
            coord = 4.5
            transitions = self.transitions_second_rfid

        if transitions:  # If transitions is not empty, initialize the loop
            T = transitions[0]["timestamp1"]

        for transition in transitions:
            time1 = T

            time2 = transition["timestamp2"]
            if transition["duration"] == 1:
                T = time2
                x_fill = [time1, time2]

                if transition["departure"] == 0:
                    y_fill = -0.5
                    if transition["type"] == "original":
                        col = (0, 0, 139)
                    elif transition["type"] == "logical":
                        col = (0, 144, 255)
                    else:
                        col = (255, 0, 0)

                else:
                    y_fill = 0.5
                    if transition["type"] == "original":
                        col = (255, 128, 0)
                    elif transition["type"] == "logical":
                        col = (255, 189, 0)
                    else:
                        col = (255, 0, 0)
                rect = QGraphicsRectItem(x_fill[0], coord, (x_fill[1] - x_fill[0]), y_fill)
                rect.setPen(pg.mkPen(None))
                rect.setBrush(pg.mkBrush(col))
                plot.addItem(rect)

    def _graph_comparison(self, plot):
        """ Build transitions for both birds in comparison mode

        :param plot: PlotItem
        """
        transitions = self.transitions
        transitions_second = self.transitions_second_rfid
        coord = 7

        if transitions: #If transitions is not empty, initialize the loop
            T = transitions[0]["timestamp1"]

        rect = QGraphicsRectItem(T-1000000, coord - 0.25, T, 0.5)
        rect.setPen(pg.mkPen(None))
        rect.setBrush(pg.mkBrush((0, 128, 255)))
        plot.addItem(rect)

        for transition in transitions:
            time1 = T
            time2 = transition["timestamp2"]
            if (transition["duration"] == 1) & (transition["departure"] != 0):
                x_fill = [time1, time2]
                col = (22, 184, 78)
                rect = QGraphicsRectItem(x_fill[0], coord-0.25, (x_fill[1]-x_fill[0]), 0.5)
                rect.setPen(pg.mkPen(None))
                rect.setBrush(pg.mkBrush(col))
                plot.addItem(rect)
            T = time2

        T = transitions_second[0]["timestamp1"]
        for transition in transitions_second:
            time1 = T
            time2 = transition["timestamp2"]
            if (transition["duration"] == 1) & (transition["departure"] != 0):
                x_fill = [time1, time2]
                col = (22, 184, 78)
                rect = QGraphicsRectItem(x_fill[0], coord-0.25, (x_fill[1]-x_fill[0]), 0.5)
                rect.setPen(pg.mkPen(None))
                rect.setBrush(pg.mkBrush(col))
                plot.addItem(rect)
            T = time2

    def _graph_completion(self, plot):
        """ Build event and cycling.

                :param plot: PlotItem
                """

        plot.removeItem(self.line)
        self.line = pg.InfiniteLine(pos=0, angle=0, pen='k')
        plot.addItem(self.line)

        try:
            plot.removeItem(self.text_computed_cycle)
            plot.removeItem(self.line_computed_cycle)
            plot.removeItem(self.scatterplot_breeding_date)
            plot.removeItem(self.scatterplot_end_breeding_date)
            plot.removeItem(self.scatterplot_computed_breeding_date)
            plot.removeItem(self.text_cycle)
            plot.removeItem(self.line_cycle)
        except:
            pass

        for cycle in self.cycle_list:
            plot.removeItem(cycle)

        for cycle in self.computed_cycle_list:
            plot.removeItem(cycle)

        self.cycle_list = []
        self.computed_cycle_list = []

        for cycle_text in self.cycle_text_list:
            plot.removeItem(cycle_text)
        self.cycle_text_list = []

        if self.ui.show_cyclingCheckbox.isChecked():
            self.cycling = get_all_cycling(self.rfid) # Sorted by date
            self._graph_cycling(plot)

        if self.ui.show_computed_cyclingCheckbox.isChecked():
            self.computed_cycling = get_all_computed_cycling(self.rfid)
            self._graph_computed_cycling(plot)


    def _set_informations(self):
        """ Set information of the bird in the right panel"""
        connexion = connect_to_db()
        cursor = connexion.cursor(pymysql.cursors.DictCursor)
        bird_info = get_info(self.rfid, cursor)
        bird_manips = get_bird_manips(self.rfid, cursor)
        bird_antennas = get_prefered_antenna(self.rfid, cursor)
        connexion.close()

        bird_antennas = pd.DataFrame(bird_antennas)
        if len(bird_antennas):
            if 'cro' in self.db:
                bird_antennas['antenna_name'] = [x.replace('_Terre','').replace('_Mer','') for x in bird_antennas['antenna_name']]
            bird_antennas = bird_antennas.groupby('antenna_name').sum('count_antenna_id')
            tot = sum(bird_antennas['count_antenna_id'])
            text_antennas = ''
            for k in range(len(bird_antennas)):
                text_antennas += bird_antennas.index[k] + ': ' + str(round(100*bird_antennas['count_antenna_id'][k]/tot,1))+'%' + '\n'
            text_antennas = text_antennas[:-1]
        else:
            text_antennas = ''
        dead = bird_info["dead"]
        if dead:
            self.ui.rfidLabel.setText(str(self.rfid) + ' †')
        else:
            self.ui.rfidLabel.setText(str(self.rfid))
        self.ui.nameLabel.setText(bird_info['name'])
        self.ui.sexLabel.setText(bird_info['sex'])
        self.ui.rfid_dateLabel.setText(str(bird_info['rfid_date']))
        self.ui.current_locLabel.setText(bird_info['current_loc'])
        self.ui.last_detectionLabel.setText(str(bird_info['last_detection']))
        self.ui.birth_yearLabel.setText(str(bird_info['birth_year_type']) + ': ' + str(bird_info['birth_year']))
        self.ui.manipLabel.setText(bird_manips)
        self.ui.prefered_antennaLabel.setText(text_antennas)
        current_alarm = bird_info['alarm']
        if current_alarm is None:
            self.ui.alarmLabel.setText('No alarm')
        else:
            self.ui.alarmLabel.setText(bird_info['alarm'])
        alarms = get_alarms()
        self.ui.alarmsComboBox.addItem('No alarm')
        for al in alarms:
            self.ui.alarmsComboBox.addItem(al['class'])

        self._init_comments()
        self._init_events()

    def _init_comments(self):
        """ Set the comments in the right panel"""
        items = self.ui.commentsFrame.children()
        for item in items[2:]:
            item.deleteLater()
        comments = get_comments(self.rfid)
        index = 0
        for comment in comments:
            self.groupBox = QtWidgets.QGroupBox(self.ui.commentsFrame)
            dtime = comment['date']
            if dtime is not None:
                dtime = dtime.strftime("%Y-%m-%d")
            self.groupBox.setTitle(comment['handler'] + ' - ' + str(dtime))
            self.horizontalLayout = QtWidgets.QHBoxLayout(self.groupBox)
            self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
            self.horizontalLayout.setSpacing(0)
            self.comment = QtWidgets.QTextBrowser(self.groupBox)
            self.comment.setText(comment['comment'])
            self.comment.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding))
            self.horizontalLayout.addWidget(self.comment)
            self.ui.verticalLayout_5.insertWidget(index, self.groupBox)
            index += 1

    def _init_events(self):
        """Set events in the right panel"""
        self.data_events = execute_fetchall("SELECT id, event_date, event_type, stage, location, handler, comment FROM events WHERE rfid = '{}'".format(self.rfid))

        for event in self.data_events:
            dtime = event['event_date']
            if (dtime is not None) & (dtime != '0000-00-00 00:00:00'):
                dtime = dtime.strftime("%Y-%m-%d")
            self.ui.eventListWidget.addItem(str(event['event_type']) + ' - ' + str(dtime))
        self.ui.eventListWidget.setMaximumHeight(self.ui.eventListWidget.sizeHintForRow(0)*self.ui.eventListWidget.count() + 15)
        self.ui.event_dataGroupBox.hide()
        if len(self.data_events):
            self.ui.event_dataGroupBox.show()
            self.ui.eventListWidget.setCurrentRow(0)
            self._init_selected_event(0)

    def _init_selected_event(self, row):
        """ Show data from selected event in the right panel"""
        event = self.data_events[row]
        dtime = event['event_date']
        if (dtime is not None) & (dtime != '0000-00-00 00:00:00'):
            dtime = dtime.strftime("%Y-%m-%d")
        self.ui.event_dataGroupBox.setTitle(str(event['event_type']) + ' - ' + str(dtime))
        self.ui.stageLabel.setText(event['stage'])
        self.ui.locationLabel.setText(event['location'])
        self.ui.handlerLabel.setText(event['handler'])

        measures = execute_fetchall("SELECT name, value FROM measures WHERE event_id = {}".format(event['id']))
        self.ui.measuresTableWidget.setRowCount(0)
        self.ui.measuresTableWidget.setRowCount(len(measures))
        for line, measure in enumerate(measures):
            self.ui.measuresTableWidget.setItem(line, 0, QTableWidgetItem(measure["name"]))
            self.ui.measuresTableWidget.setItem(line, 1, QTableWidgetItem(measure["value"]))
        self.ui.measuresTableWidget.resizeColumnsToContents()

    def eventListWidgetSelectionChanged(self):
        row = self.ui.eventListWidget.currentRow()
        self._init_selected_event(row)

    def change_alarm(self):
        self.ui.alarmFrame.hide()
        self.ui.change_alarmFrame.show()

    def close_change_alarm(self):
        self.ui.alarmFrame.show()
        self.ui.change_alarmFrame.hide()

    def save_alarm(self):
        "Save alarm change"
        new_alarm = self.ui.alarmsComboBox.currentText()
        if new_alarm == 'No alarm':
            new_alarm = 'NULL'
        else:
            new_alarm = "'{}'".format(new_alarm)
        commit = "UPDATE birds SET alarm = {} WHERE rfid = '{}'".format(new_alarm, self.rfid)
        execute_commit(commit)
        self.ui.alarmLabel.setText(execute_fetchall("SELECT alarm FROM birds WHERE rfid = '{}'".format(self.rfid))[0]['alarm'])
        self.close_change_alarm()

    def new_comment(self):
        self.ui.new_commentFrame.show()
        handlers = get_handlers()
        for handler in handlers:
            self.ui.handlerComboBox.addItem(handler['name'])
        self.ui.handlerComboBox.setCurrentText(self.settings_user.value("user"))
    def close_add_comment(self):
        self.ui.new_commentFrame.hide()

    def save_new_comment(self):
        self.close_add_comment()
        new_comment = self.ui.new_commentLineEdit.text().replace('"','')
        handler = self.ui.handlerComboBox.currentText()
        dtime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = 'INSERT INTO comments (rfid, comment, handler, date) VALUES ("{}","{}","{}","{}")'.format(self.rfid, new_comment, handler, dtime)
        execute_commit(query)
        self.settings_user.setValue("user", handler)
        self._init_comments()

    def compare_rfid_showPushButtonClicked(self):
        """ Open comparison tool"""
        new_rfid_name = self.ui.compare_rfidLineEdit.text()
        is_rfid = execute_fetchall('SELECT rfid from birds WHERE rfid = "{}"'.format(new_rfid_name))
        if len(is_rfid) == 0:
            is_name = execute_fetchall('SELECT rfid from birds WHERE name = "{}"'.format(new_rfid_name))
            if len(is_name):
                new_rfid = is_name[0]['rfid']
            else:
                new_rfid = None
        else:
            new_rfid = new_rfid_name

        if new_rfid is not None:
            if new_rfid != self.second_rfid:
                self.second_rfid = new_rfid
                self.detections_second_rfid, self.transitions_second_rfid = self.init_detect_transi(self.second_rfid)
            self.show_comparison = True
            self._graph_construction()
        else:
            QMessageBox.information(self, 'Error', "Unknown RFID or name")
            return

    def compare_rfid_hidePushButtonClicked(self):
        self.show_comparison = False
        self._graph_construction()

    def detections_showedChanged(self):
        self.detections, self.transitions = self.init_detect_transi(self.rfid)
        if self.show_comparison:
            self.detections_second_rfid, self.transitions_second_rfid = self.init_detect_transi(self.second_rfid)
        self._graph_construction()


    def _graph_cycling(self, plot):
        """ Build cycling elements in the graph.

        :param plot: objet PlotItem
        """
        self.line_cycle = pg.InfiniteLine(pos=3.35, angle=0, pen='k')
        plot.addItem(self.line_cycle)

        self.text_cycle = pg.TextItem("Cycling", anchor=(0, 0), )
        font = QFont()
        font.setPixelSize(8)
        self.text_cycle.setFont(font)
        xpos = self.viewbox.viewRange()[0][0]
        self.text_cycle.setPos(xpos, 3.35)
        plot.addItem(self.text_cycle)

        start_dtime_list = []
        end_dtime_list = []
        for cycle in self.cycling:
            if cycle["value"] != "NB":
                start_dtime_list.append(cycle["start_dtime"].timestamp())
                end_dtime_list.append(cycle["end_dtime"].timestamp())
            time1 = datetime.strptime(str(cycle["season"]-1)+"-10-01", "%Y-%m-%d").timestamp()
            time2 = datetime.strptime(str(cycle["season"]) + "-10-01", "%Y-%m-%d").timestamp()
            if cycle["value"] == "S":
                col = (60,179,113)
            elif cycle["value"] == "F":
                col = (220,20,60)
            else:
                col = (120,120,120)

            rect = QGraphicsRectItem(time1, 2.5, (time2 - time1), 0.6)
            rect.setPen(pg.mkPen('k'))
            rect.setBrush(pg.mkBrush(col))
            plot.addItem(rect)

            x_text = int((time1 + time2) / 2)
            text = pg.TextItem(str(cycle["value"]), anchor=(0.5, 0.5))
            text.setPos(x_text, 2.75)
            text.setColor('w')
            plot.addItem(text)

            self.cycle_list.append(rect)
            self.cycle_text_list.append(text)

        self.scatterplot_breeding_date = pg.ScatterPlotItem(start_dtime_list, [3.1]*len(start_dtime_list), data = ["Breeding Date"]*len(start_dtime_list), symbol="t2", brush=pg.mkBrush((0, 0, 0), width=1), pen= pg.mkPen((0, 0, 0), width=1))
        self.scatterplot_end_breeding_date = pg.ScatterPlotItem(end_dtime_list, [3.1]*len(end_dtime_list), data = ["Breeding Date"]*len(end_dtime_list), symbol="t3", brush=pg.mkBrush((0, 0, 0), width=1), pen= pg.mkPen((0, 0, 0), width=1))

        plot.addItem(self.scatterplot_breeding_date)
        plot.addItem(self.scatterplot_end_breeding_date)


    def _graph_computed_cycling(self, plot):
        """ Build computed cycling view in the cycle graph.

        :param plot: objet PlotItem
        """

        self.line_computed_cycle = pg.InfiniteLine(pos=2.25, angle=0, pen='k')
        plot.addItem(self.line_computed_cycle)

        self.text_computed_cycle = pg.TextItem("Computed cycling", anchor=(0, 0), )
        font = QFont()
        font.setPixelSize(8)
        self.text_computed_cycle.setFont(font)
        xpos = self.viewbox.viewRange()[0][0]
        self.text_computed_cycle.setPos(xpos, 2.25)
        plot.addItem(self.text_computed_cycle)

        start_dtime_list = []
        for cycle in self.computed_cycling:
            if cycle["value"] != "NB":
                start_dtime_list.append(cycle["start_dtime"].timestamp())
            time1 = datetime.strptime(str(cycle["season"]-1)+"-10-01", "%Y-%m-%d").timestamp()
            time2 = datetime.strptime(str(cycle["season"])+"-10-01", "%Y-%m-%d").timestamp()
            if cycle["value"] == "S":
                col = (60,179,113)
            elif cycle["value"] == "F":
                col = (220,20,60)
            else:
                col = (120,120,120)

            rect = QGraphicsRectItem(time1, 1.4, (time2 - time1), 0.6)
            rect.setPen(pg.mkPen('k'))
            rect.setBrush(pg.mkBrush(col))
            plot.addItem(rect)

            x_text = int((time1 + time2) / 2)
            text = pg.TextItem(str(cycle["value"]), anchor=(0.5, 0.5))
            text.setPos(x_text, 1.7)
            text.setColor('w')
            plot.addItem(text)

            self.computed_cycle_list.append(rect)
            self.cycle_text_list.append(text)

        self.scatterplot_computed_breeding_date = pg.ScatterPlotItem(start_dtime_list, [2]*len(start_dtime_list), data = ["Breeding Date"]*len(start_dtime_list), symbol="t2", brush=pg.mkBrush((0, 0, 0), width=1), pen= pg.mkPen((0, 0, 0), width=1))
        plot.addItem(self.scatterplot_computed_breeding_date)

    def show_cycling_changed(self):
        self._graph_completion(self.plot)

    def onClick(self, ev, points=None):
        """ define what to do when user clicks in the graph: open window to add new data on phenology or modify cycling"""
        if points is not None and self.LRI_activated == 0 and self.line_activated == 0:  ## if user clicks on a event point
            self.changing_point = points[0]
            self.line_activated = 1

            self.ui.modify_cycleFrame.show()

            self.movable_line = pg.InfiniteLine(pos=self.changing_point.pos(), movable=True)
            self.plot.addItem(self.movable_line)

        elif ev.button() == 1:
            items = self.window.scene().items(ev.scenePos())
            for item in items:
                if item in self.cycle_list and self.LRI_activated == 0 and self.line_activated == 0: ## if user clicks on a cycle rectangle but not on a point too
                    self.ui.modify_cycleFrame.show()
                    self.changing_item = item
                    season = determine_year(datetime.fromtimestamp(item.boundingRect().x()))
                    query = f"SELECT * FROM cycling where rfid = '{self.rfid}' and season = '{season}'"
                    current_cycle = execute_fetchall(query)[0]
                    self.ui.cycle_value_comboBox.setCurrentText(current_cycle["value"])
                    self.ui.bsex_comboBox.setCurrentText(current_cycle["behavioral_sex"])
                    self.ui.season_label.setText(f'Season: {season}')
                    start = current_cycle["start_dtime"].timestamp()
                    end = current_cycle["end_dtime"].timestamp()
                    self.LRI = pg.LinearRegionItem(orientation="vertical", bounds=(0, self.max_date.timestamp()))
                    self.LRI.setRegion((start, end))
                    self.plot.addItem(self.LRI)
                    self.LRI_activated = 1
        else:
            self.modif_cycle_cancel_buttonClicked()

    def modif_cycle_cancel_buttonClicked(self):
        if self.LRI_activated == 1:
            self.plot.removeItem(self.LRI)
            self.LRI_activated = 0
        self.ui.modify_cycleFrame.hide()

    def modif_cycle_delete_buttonClicked(self):
        season = determine_year(datetime.fromtimestamp(self.changing_item.boundingRect().x()))
        query = f"DELETE FROM cycling where rfid = '{self.rfid}' and season = '{season}'"
        execute_commit(query)
        self.modif_cycle_cancel_buttonClicked()
        self.refresh_cycling_data()

    def modif_cycle_save_buttonClicked(self):
        if self.LRI_activated == 1:
            season = determine_year(datetime.fromtimestamp(self.changing_item.boundingRect().x()))
            new_start_dtime = datetime.fromtimestamp(self.LRI.getRegion()[0]).strftime("%Y-%m-%d %H:%M:%S")
            new_end_dtime = datetime.fromtimestamp(self.LRI.getRegion()[1]).strftime("%Y-%m-%d %H:%M:%S")
            value = self.ui.cycle_value_comboBox.currentText()
            bsex = self.ui.bsex_comboBox.currentText()
            new_season = determine_year(datetime.fromtimestamp(self.LRI.getRegion()[0]))
            query = f"UPDATE cycling SET season = '{new_season}', value = '{value}', behavioral_sex = '{bsex}', start_dtime = '{new_start_dtime}', end_dtime = '{new_end_dtime}' WHERE rfid = '{self.rfid}' and season = '{season}'"
            execute_commit(query)
            self.modif_cycle_cancel_buttonClicked()
            self.refresh_cycling_data()