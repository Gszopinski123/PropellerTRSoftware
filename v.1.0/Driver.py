from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow,
    QPushButton, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QMenu,QToolButton,QLineEdit,QGridLayout
)
from PySide6.QtCore import Qt
import sys
from prop_lib import openAsReadJson,jsonFillFile
import CurrentTester as ct
import CellTester as cellt
import Cellcalibration as cellc
import CurrentCalibration as cc
import dataLogger as dl

def clear_layout(layout):
    if layout is None:
        return
    
    while layout.count():
        item = layout.takeAt(0)
        

        widget = item.widget()
        if widget is not None:
            widget.setParent(None)

        child_layout = item.layout()
        if child_layout is not None:
            clear_layout(child_layout)



class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Propeller Testing")
        self.resize(1000, 700)

        container = QWidget()
        mainLayout = QVBoxLayout()
        container.setLayout(mainLayout)
        self.setCentralWidget(container)

        self.stack = QStackedWidget()
        self.buttonLayout = QHBoxLayout()
        
        self.buttonLayout.addStretch(1)
        labelsWithButtons : list[str] = ["Calibration","Testing","Collect","Configuration"]
        labelsWithoutButtons : list[tuple[str,tuple[str,str]]] = [("Calibration",("Cell Calibration","Current Calibration")),
                                ("Testing",("Current Testing","Cell Testing")),
                                ("Collect",("Collect",)),
                                ("Configuration",("Calibration Configuration","Main Config"))]
        widgets_btns : tuple[QWidget,QToolButton] = [self.setupPage(x) for x in labelsWithButtons]
        pageNum : int = len(labelsWithButtons)-1
        pages_without_btns : list[tuple[str,int,QWidget,str]] = \
        [(x,pageNum := pageNum+1,self.setupPageWithoutButton(w),w) for (x,y) in labelsWithoutButtons for w in y]
        self.buttonLayout.addStretch(1)
        page_to_setup = {"Main Config" : self.setupMainConfig,
                         "Calibration Configuration":self.setupCalibrationConfig,
                         "Current Testing": self.setupCurrentTest,
                         "Cell Testing": self.setupCellTest,
                         "Cell Calibration": self.setupCellCalibration,
                         "Current Calibration":self.setupCurrentCalibration,
                         "Collect":self.setupCollect}
        label_to_Button : dict[str,tuple[QToolButton,QMenu]] = {}
        mainLayout.addLayout(self.buttonLayout)

        
        for x in range(len(widgets_btns)):
            self.stack.addWidget(widgets_btns[x][0])
            widgets_btns[x][1].clicked.connect(lambda checked=False, i=x: self.stack.setCurrentIndex(i))
            label_to_Button[labelsWithButtons[x]] = (widgets_btns[x][1], QMenu(widgets_btns[x][1]))

        
        for x in range(len(pages_without_btns)):
            self.stack.addWidget(pages_without_btns[x][2])
            menu = label_to_Button[pages_without_btns[x][0]][1]
            menu.addAction(pages_without_btns[x][3], lambda checked=False, i=pages_without_btns[x][1] : self.stack.setCurrentIndex(i))
        for x in range(len(labelsWithButtons)):
            btn = label_to_Button[labelsWithButtons[x]][0]
            menu = label_to_Button[labelsWithButtons[x]][1]
            btn.setMenu(menu)
        for x in range(len(pages_without_btns)):
            if pages_without_btns[x][3] in page_to_setup:
                page_to_setup[pages_without_btns[x][3]](pages_without_btns[x][2])
    
        mainLayout.addWidget(self.stack)
    def setupCollect(self,widget:QWidget,msg=""):
        grid = QGridLayout()
        prop_name = QLabel("Enter Propeller name")
        prop_name_field = QLineEdit()
        grid.addWidget(prop_name,0,0)
        grid.addWidget(prop_name_field,0,1)
        lr_option = QLabel("Enter left or right")
        lr_field = QLineEdit()
        grid.addWidget(lr_option,1,0)
        grid.addWidget(lr_field,1,1)
        btn_start = QPushButton("Start")
        btn_start.clicked.connect(
            lambda _,widget=widget,prop=prop_name_field, lr=lr_field: 
            self.collectSetup(widget,prop,lr))
        errorMsg = QLabel(f"{msg}")
        layout = QVBoxLayout()
        layout.addLayout(grid)
        main_layout = widget.layout()
        layout.addWidget(btn_start,alignment=Qt.AlignCenter)
        layout.addWidget(errorMsg,alignment=Qt.AlignCenter)
        layout.addStretch(1)
        main_layout.addLayout(layout)

    def collectSetup(self,widget,prop,lr):
        msg = ""
        failureFlag = 0
        main_layout = widget.layout()
        try:
            dl.main(prop,lr)
        except Exception as e:
            msg = e
        last_btn = main_layout.takeAt(main_layout.count() - 1)
        clear_layout(last_btn)
        self.setupCollect(widget,msg)

    def setupCurrentCalibration(self,widget:QWidget,msg=""):
        grid = QGridLayout()
        csv_option = QLabel("Enter List of Measured current in AMPS in csv (i.e., 10,20,30,40)")
        csv_field = QLineEdit()
        grid.addWidget(csv_option,0,0)
        grid.addWidget(csv_field,0,1)
        btn_start = QPushButton("Start")
        btn_start.clicked.connect(
            lambda _,widget=widget,ls=csv_field: 
            self.currentCalibrationSetup(widget,ls))
        errorMsg = QLabel(f"{msg}")
        layout = QVBoxLayout()
        layout.addLayout(grid)
        main_layout = widget.layout()
        layout.addWidget(btn_start,alignment=Qt.AlignCenter)
        layout.addWidget(errorMsg,alignment=Qt.AlignCenter)
        layout.addStretch(1)
        main_layout.addLayout(layout)

    def currentCalibrationSetup(self,widget,ls):
        msg = ""
        failureFlag = 0
        main_layout = widget.layout()
        lst = []
        try:
            lst = [int(x) for x in ls.text().split(",")]
        except Exception as e:
            msg = e
            failureFlag = 1
        if failureFlag == 1:
            last_btn = main_layout.takeAt(main_layout.count() - 1)
            clear_layout(last_btn)
            self.setupCurrentCalibration(widget,msg)
            return
        try:
            cc.calibrate(lst)
        except Exception as e:
            msg = e
        
        
        last_btn = main_layout.takeAt(main_layout.count() - 1)
        clear_layout(last_btn)
        self.setupCurrentCalibration(widget,msg)

    def setupCellCalibration(self,widget:QWidget,msg=""):
        grid = QGridLayout()
        option = QLabel("Torque or Thrust [0 or 1]")
        option_field = QLineEdit()
        grid.addWidget(option,0,0)
        grid.addWidget(option_field,0,1)
        torque_arm_option = QLabel("Torque Arm Length [if using torque]")
        torque_arm_field = QLineEdit()
        grid.addWidget(torque_arm_option,1,0)
        grid.addWidget(torque_arm_field,1,1)
        csv_option = QLabel("Enter List of Masses in grams in csv (i.e., 10,20,30,40)")
        csv_field = QLineEdit()
        grid.addWidget(csv_option,2,0)
        grid.addWidget(csv_field,2,1)
        btn_start = QPushButton("Start")
        btn_start.clicked.connect(
            lambda _,widget=widget,option=option_field,torque_arm=torque_arm_field,ls=csv_field: 
            self.cellCalibrationSetup(widget,option,torque_arm,ls))
        errorMsg = QLabel(f"{msg}")
        layout = QVBoxLayout()
        layout.addLayout(grid)
        main_layout = widget.layout()
        layout.addWidget(btn_start,alignment=Qt.AlignCenter)
        layout.addWidget(errorMsg,alignment=Qt.AlignCenter)
        layout.addStretch(1)
        main_layout.addLayout(layout)
    
    def cellCalibrationSetup(self,widget,option_field,torque_arm_field,csv_field):
        msg = ""
        failureFlag = 0
        main_layout = widget.layout()
        lst = []
        try:
            lst = [int(x) for x in csv_field.text().split(",")]
        except Exception as e:
            msg = e
            failureFlag = 1
        try:
            option_field = int(option_field.text())
        except Exception as e:
            msg = e
            failureFlag = 1
        if option_field == 0 :
            try:
                torque_arm_field = float(torque_arm_field.text())
            except Exception as e:
                msg = e
                failureFlag = 1
        if failureFlag == 1:
            last_btn = main_layout.takeAt(main_layout.count() - 1)
            clear_layout(last_btn)
            self.setupCellCalibration(widget,msg)
            return
        try:
            cellc.setup(option_field,torque_arm_field,lst)
        except Exception as e:
            msg = e
        
        
        last_btn = main_layout.takeAt(main_layout.count() - 1)
        clear_layout(last_btn)
        self.setupCellCalibration(widget,msg)
        
    def setupCellTest(self,widget:QWidget,wasSuccess=None,msg=None):
        label = QLabel("")
        failureMsg = QLabel("")
        main_layout = widget.layout()
        if wasSuccess == None:
            label = QLabel("Run A Test!")
        elif wasSuccess:
            label = QLabel("Test was a Success!")
        elif not wasSuccess:
            label = QLabel("Test was a Failure!")
            failureMsg = QLabel(msg)
        grid = QGridLayout()
        modes = QLabel("Modes [Torque: 0, Thrust: 1, BOTH: 2]")
        grid.addWidget(modes,0,0)
        modes_field = QLineEdit()
        grid.addWidget(modes_field,0,1)
        unit_label = QLabel("UNITS [SI/I]")
        grid.addWidget(unit_label,1,0)
        unit_field = QLineEdit()
        grid.addWidget(unit_field,1,1)
        btn_start = QPushButton("Start")
        btn_start.clicked.connect(lambda _,units=unit_field,mode=modes_field: self.startCellTest(widget,mode.text(),units.text()))
        layout = QVBoxLayout()
        layout.addLayout(grid)
        layout.addWidget(label,alignment=Qt.AlignCenter)
        layout.addWidget(btn_start,alignment=Qt.AlignCenter)
        layout.addWidget(failureMsg,alignment=Qt.AlignCenter)
        layout.addStretch(1)
        main_layout.addLayout(layout)    
    def startCellTest(self,widget,mode,units):
        msg = ""
        value = 0
        if units == "":
            msg = f"INVALID UNIT"
            main_layout = widget.layout()
            last_item = main_layout.takeAt(main_layout.count() - 1)
            clear_layout(last_item)
            self.setupCellTest(widget,value,msg)
            return
        try:
            mode = int(mode)
        except Exception as e:
            msg = f"{e}"
            main_layout = widget.layout()
            last_item = main_layout.takeAt(main_layout.count() - 1)
            clear_layout(last_item)
            self.setupCellTest(widget,value,msg)
            return
        try:
            value = cellt.tester(mode,units)
        except Exception as e:
            msg = f"{e}"
        main_layout = widget.layout()
        last_item = main_layout.takeAt(main_layout.count() - 1)
        clear_layout(last_item)
        self.setupCellTest(widget,value,msg)

    def setupCurrentTest(self,widget:QWidget,wasSuccess=None,msg=None):
        label = QLabel("")
        failureMsg = QLabel("")
        main_layout = widget.layout()
        if wasSuccess == None:
            label = QLabel("Run A Test!")
        elif wasSuccess:
            label = QLabel("Test was a Success!")
        elif not wasSuccess:
            label = QLabel("Test was a Failure!")
            failureMsg = QLabel(msg)
        
        btn_start = QPushButton("Start")
        btn_start.clicked.connect(lambda : self.startCurrentTest(widget))
        layout = QVBoxLayout()
        layout.addWidget(label,alignment=Qt.AlignCenter)
        layout.addWidget(btn_start,alignment=Qt.AlignCenter)
        layout.addWidget(failureMsg,alignment=Qt.AlignCenter)
        layout.addStretch(1)
        main_layout.addLayout(layout)
    
    def startCurrentTest(self,widget):
        msg = ""
        value = 0
        try:
            value = ct.setup()
        except Exception as e:
            msg = f"{e}"
        main_layout = widget.layout()
        last_item = main_layout.takeAt(main_layout.count() - 1)
        clear_layout(last_item)
        self.setupCurrentTest(widget,value,msg)
    
    
    def setupCalibrationConfig(self,widget:QWidget):
        cfgjson = openAsReadJson("cfg.json")
        calibration_data = cfgjson["CELL_CAL_FILE"]
        calibration_json = openAsReadJson(calibration_data)
        layout = widget.layout()
        grid = QGridLayout()
        for index,x in enumerate(calibration_json.keys()):
            grid.addWidget(QLabel(f"{x}"),index,0)
            grid.addWidget(QLabel(f"{calibration_json[x]}"),index,1)
        layout.addLayout(grid)
        btn_update = QPushButton("Update")
        btn_update.clicked.connect(lambda _, widget=widget : self.updateCalibrationConfig(widget))
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_update,alignment=Qt.AlignCenter)
        layout.addLayout(btn_layout)
        layout.addStretch(1)

    def updateCalibrationConfig(self,widget:QWidget) -> None:
        main_layout = widget.layout()
        last_layout = main_layout.takeAt(main_layout.count() - 3)
        last_btn_layout = main_layout.takeAt(main_layout.count() - 2)
        last_item = main_layout.takeAt(main_layout.count() - 1)
        del last_item
        clear_layout(last_layout)
        clear_layout(last_btn_layout)
        self.setupCalibrationConfig(widget)
    
    def setupMainConfig(self,widget:QWidget) -> None:
        cfgjson = openAsReadJson("cfg.json")
        layout = widget.layout()
        grid = QGridLayout()
        for index,x in enumerate(cfgjson.keys()):
            grid.addWidget(QLabel(x),index,0)
            grid.addWidget(QLabel(f"{cfgjson[x]}"),index,1)
            line_edit = QLineEdit()
            grid.addWidget(line_edit,index,2)
            extract_btn = QPushButton("Change Data")
            delete_btn = QPushButton("Remove")
            extract_btn.clicked.connect(
                lambda _,widget=widget,label=x,le=line_edit: self.refreshScreenMainConfig(label,le.text(),"extract",widget))
            delete_btn.clicked.connect(
                lambda _,widget=widget,label=x: self.refreshScreenMainConfig(label,None,"delete",widget))
            grid.addWidget(extract_btn,index,3)
            grid.addWidget(delete_btn,index,4)
        num_of_keys = len(cfgjson.keys())
        line_edit_field = QLineEdit()
        line_edit_value = QLineEdit()
        add_btn = QPushButton("Add Field")
        add_btn.clicked.connect(
            lambda _,widget=widget,label=line_edit_field,value=line_edit_value: self.refreshScreenMainConfig(label.text(),value.text(),"add",widget))
        grid.addWidget(QLabel("FIELD_NAME:"),num_of_keys,0)
        grid.addWidget(line_edit_field,num_of_keys,1)
        grid.addWidget(QLabel("VALUE_NAME:"),num_of_keys,2)
        grid.addWidget(line_edit_value,num_of_keys,3)
        grid.addWidget(add_btn,num_of_keys,4)
        layout.addLayout(grid)
        layout.addStretch(1)
        
    def refreshScreenMainConfig(self,label,data,dtype,widget):        
        cfgJson = openAsReadJson("cfg.json")
        main_layout = widget.layout()
        last_layout = main_layout.takeAt(main_layout.count() - 2)
        last_item = main_layout.takeAt(main_layout.count() - 1)
        del last_item
        clear_layout(last_layout)
        if (dtype == "extract"):
            if (type(cfgJson[label]) == type(data)):
                cfgJson[label] = data
            else:
                cfgJson[label] = type(cfgJson[label])(data)
        elif (dtype == "delete"):
            cfgJson.pop(label)
        elif (dtype == "add"):
            cfgJson[label] = data
        else:
            print("WHAT HAPPENED!")
            pass
        jsonFillFile("cfg.json",cfgJson)
        self.setupMainConfig(widget)

    
    
    
    def setupPageWithoutButton(self,name:str) -> QWidget:
        Testing = QWidget()
        Testing_Layout = QVBoxLayout()
        Testing_Layout.addWidget(QLabel(name),alignment=Qt.AlignCenter | Qt.AlignTop)
        Testing.setLayout(Testing_Layout)
        return Testing
    def setupPage(self,name: str) -> tuple[QWidget,QToolButton]:
        btn_Testing = QToolButton()
        btn_Testing.setText(name)
        btn_Testing.setFixedSize(145, 40)
        self.buttonLayout.setSpacing(20)
        self.buttonLayout.addWidget(btn_Testing,alignment=Qt.AlignBottom)
        
        btn_Testing.setPopupMode(QToolButton.InstantPopup)
        
        Testing = QWidget()
        Testing_Layout = QVBoxLayout()
        Testing_Layout.addWidget(QLabel(f"{name}"),alignment=Qt.AlignCenter | Qt.AlignTop)
        Testing_Layout.addStretch(1) 
        Testing.setLayout(Testing_Layout)
        return Testing,btn_Testing
    
    def setupCalibrationPages(self,main_widget,main_layout) -> tuple[QWidget, QVBoxLayout]:
        buttonLayout = QVBoxLayout()
        btn_CurrentCalibration = QPushButton("Current Calibration")
        btn_CellCalibration = QPushButton("Cell Calibration")


        buttonLayout.addWidget(btn_CellCalibration,alignment=Qt.AlignLeft | Qt.AlignTop)
        buttonLayout.addWidget(btn_CurrentCalibration,alignment=Qt.AlignLeft | Qt.AlignTop)
        buttonLayout.addStretch()

        calibration_stack = QStackedWidget()
       
        # Page for Cell
        CellCalibration = QWidget()
        CellCalibration_Layout = QVBoxLayout()
        CellCalibration_Layout.addWidget(QLabel("This is Cell Calibration"))
        CellCalibration.setLayout(CellCalibration_Layout)
        # Page for Current
        CurrentCalibration = QWidget()
        CurrentCalibration_Layout = QVBoxLayout()
        CurrentCalibration_Layout.addWidget(QLabel("This is Current Calibration"))
        CurrentCalibration.setLayout(CurrentCalibration_Layout)

        calibration_stack.addWidget(CellCalibration)
        calibration_stack.addWidget(CurrentCalibration)

        btn_CellCalibration.clicked.connect(lambda: calibration_stack.setCurrentIndex(0))
        btn_CurrentCalibration.clicked.connect(lambda: calibration_stack.setCurrentIndex(1))
        
        main_layout.addLayout(buttonLayout)
        main_layout.addWidget(calibration_stack)
        return main_widget,main_layout




if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    sys.exit(app.exec())




# change offset time -> #changed to 5 seconds