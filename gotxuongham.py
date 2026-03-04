import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import numpy as np
import math

# ==============================================================================
#  CLASS 1: METADATA
# ==============================================================================
class gotxuongham(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "Gọt Xương Hàm Version 1"
        parent.categories = ["Orthognathic Surgery"]
        parent.dependencies = []
        parent.contributors = ["Tuna"]
        parent.helpText = """
        Module tích hợp:
        1. Gọt hàm V-line (Angle reduction).
        2. Trượt cằm (Genioplasty).
        """
        self.parent = parent

# ==============================================================================
#  CLASS 2: GUI WIDGET (ĐÃ SẮP XẾP LẠI THEO QUY TRÌNH MỚI)
# ==============================================================================
class gotxuonghamWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)
        self.logic = None
        self._currentMode = 3 

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        self.logic = gotxuonghamLogic()

        # --- Layout ---
        uiWidget = qt.QWidget()
        self.layout.addWidget(uiWidget)
        formLayout = qt.QFormLayout(uiWidget)

        # --- SECTION 0: CHẾ ĐỘ ---
        modeGroup = qt.QGroupBox("Chế độ nhập điểm mốc")
        modeLayout = qt.QHBoxLayout()
        modeGroup.setLayout(modeLayout)
        
        self.radio3pt = qt.QRadioButton("3 Điểm (Na, Ba, Op)")
        self.radio3pt.setChecked(True)
        self.radio4pt = qt.QRadioButton("4 Điểm (Na, Ba, Op, IF)")
        
        modeLayout.addWidget(self.radio3pt)
        modeLayout.addWidget(self.radio4pt)
        formLayout.addRow(modeGroup)

        self.radio3pt.toggled.connect(self.onModeChanged)
        self.radio4pt.toggled.connect(self.onModeChanged)

        # --- SECTION 1: INPUT DATA ---
        inputCollapsibleButton = ctk.ctkCollapsibleButton()
        inputCollapsibleButton.text = "1. Tạo MSP và Mirror"
        formLayout.addRow(inputCollapsibleButton)
        inputFormLayout = qt.QFormLayout(inputCollapsibleButton)
        
        self.btnStep1 = qt.QPushButton("Create")
        self.btnStep1.setStyleSheet("background-color: #ffcccc; font-weight: bold")
        inputFormLayout.addRow(self.btnStep1)


        # --- SECTION 1: INPUT DATA ---
        # --- SECTION 2: DISTANCE & ANGLE ---
        inputCollapsibleButton = ctk.ctkCollapsibleButton()
        inputCollapsibleButton.text = "2. Tính khoảng cách và góc"
        formLayout.addRow(inputCollapsibleButton)
        inputFormLayout = qt.QFormLayout(inputCollapsibleButton)

        # Button create Frankfort plane
        self.btnCreateFrankfort = qt.QPushButton("Create Frankfort Plane")
        self.btnCreateFrankfort.setStyleSheet("background-color: #ccffcc; font-weight: bold")
        self.btnCreateFrankfort.clicked.connect(self.onCreateFrankfortPlane)

        # --- Phần chọn điểm để tạo mặt phẳng mới ---
        self.customPlaneLabel = qt.QLabel("Create custom plane from points:")
        self.customPlaneLabel.setStyleSheet("font-weight: bold")

        self.planePoint1Selector = slicer.qMRMLNodeComboBox()
        self.planePoint1Selector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.planePoint1Selector.noneEnabled = True
        self.planePoint1Selector.setMRMLScene(slicer.mrmlScene)

        self.planePoint2Selector = slicer.qMRMLNodeComboBox()
        self.planePoint2Selector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.planePoint2Selector.noneEnabled = True
        self.planePoint2Selector.setMRMLScene(slicer.mrmlScene)

        self.planePoint3Selector = slicer.qMRMLNodeComboBox()
        self.planePoint3Selector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.planePoint3Selector.noneEnabled = True
        self.planePoint3Selector.setMRMLScene(slicer.mrmlScene)

        self.planePoint4Selector = slicer.qMRMLNodeComboBox()
        self.planePoint4Selector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.planePoint4Selector.noneEnabled = True
        self.planePoint4Selector.setMRMLScene(slicer.mrmlScene)

        self.btnCreateCustomPlane = qt.QPushButton("Create Plane from 3 or 4 Points")
        self.btnCreateCustomPlane.setStyleSheet("background-color: #ffe6cc; font-weight: bold")
        self.btnCreateCustomPlane.clicked.connect(self.onCreatePlaneFromPoints)


        # Point selector
        self.pointASelector = slicer.qMRMLNodeComboBox()
        self.pointASelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.pointASelector.setMRMLScene(slicer.mrmlScene)

        self.pointBSelector = slicer.qMRMLNodeComboBox()
        self.pointBSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.pointBSelector.setMRMLScene(slicer.mrmlScene)

        # Plane selector
        self.planeSelector = slicer.qMRMLNodeComboBox()
        self.planeSelector.nodeTypes = ["vtkMRMLMarkupsPlaneNode"]
        self.planeSelector.noneEnabled = True
        self.planeSelector.setMRMLScene(slicer.mrmlScene)

        self.plane2Selector = slicer.qMRMLNodeComboBox()
        self.plane2Selector.nodeTypes = ["vtkMRMLMarkupsPlaneNode"]
        self.plane2Selector.noneEnabled = True
        self.plane2Selector.setMRMLScene(slicer.mrmlScene)


        # Line selector
        self.lineSelector = slicer.qMRMLNodeComboBox()
        self.lineSelector.nodeTypes = ["vtkMRMLMarkupsLineNode"]
        self.lineSelector.noneEnabled = True
        self.lineSelector.setMRMLScene(slicer.mrmlScene)

        self.linePoint1Selector = slicer.qMRMLNodeComboBox()
        self.linePoint1Selector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.linePoint1Selector.setMRMLScene(slicer.mrmlScene)

        self.linePoint2Selector = slicer.qMRMLNodeComboBox()
        self.linePoint2Selector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.linePoint2Selector.setMRMLScene(slicer.mrmlScene)

        self.btnCreateLine = qt.QPushButton("Create Line from 2 Points")
        self.btnCreateLine.setStyleSheet("background-color: #ccccff; font-weight: bold")
        self.btnCreateLine.clicked.connect(self.onCreateLineFromPoints)

        self.resultLabel = qt.QLabel("Distance: — mm\nAngle: — °")
        self.resultLabel.setStyleSheet("font-weight: bold; font-size: 13px")

        # Button
        self.btnStep2 = qt.QPushButton("Calculate")
        self.btnStep2.setStyleSheet("background-color: #ffcccc; font-weight: bold")
        self.btnStep2.clicked.connect(self.onCalculate)

        # Layout
        inputFormLayout.addRow(self.btnCreateFrankfort)
        inputFormLayout.addRow(self.customPlaneLabel)
        inputFormLayout.addRow("Plane Point 1:", self.planePoint1Selector)
        inputFormLayout.addRow("Plane Point 2:", self.planePoint2Selector)
        inputFormLayout.addRow("Plane Point 3:", self.planePoint3Selector)
        inputFormLayout.addRow("Plane Point 4 (optional):", self.planePoint4Selector)
        inputFormLayout.addRow(self.btnCreateCustomPlane)

        inputFormLayout.addRow("Point A:", self.pointASelector)
        inputFormLayout.addRow("Point B:", self.pointBSelector)
        inputFormLayout.addRow("Plane A:", self.planeSelector)
        inputFormLayout.addRow("Plane B:", self.plane2Selector)
        inputFormLayout.addRow("Line Point 1:", self.linePoint1Selector)
        inputFormLayout.addRow("Line Point 2:", self.linePoint2Selector)
        inputFormLayout.addRow(self.btnCreateLine)

        inputFormLayout.addRow("Line:", self.lineSelector)
        inputFormLayout.addRow(self.btnStep2)
        inputFormLayout.addRow(self.resultLabel)


        # --- SECTION 2: GENIOPLASTY (TRƯỢT CẰM) ---
        genioCollapsibleButton = ctk.ctkCollapsibleButton()
        genioCollapsibleButton.text = "3. Genioplasty (Trượt cằm trước)"
        formLayout.addRow(genioCollapsibleButton)
        genioFormLayout = qt.QFormLayout(genioCollapsibleButton)

        # B2.1: Chọn đường cắt L (Tương tự OC)
        self.lCutCurveSelector = slicer.qMRMLNodeComboBox()
        self.lCutCurveSelector.nodeTypes = ["vtkMRMLMarkupsCurveNode", "vtkMRMLMarkupsLineNode"]
        self.lCutCurveSelector.setMRMLScene(slicer.mrmlScene)
        self.lCutCurveSelector.addEnabled = True
        self.lCutCurveSelector.renameEnabled = True
        self.lCutCurveSelector.setToolTip("Chọn đường xác định vị trí L-cut.")
        genioFormLayout.addRow("Đường cắt L (Curve/Line):", self.lCutCurveSelector)

        self.btnMirrorLCut = qt.QPushButton("B3.1: Đối xứng đường L-cut (R -> L)")
        self.btnMirrorLCut.setStyleSheet("background-color: #ffcccc; font-weight: bold")
        genioFormLayout.addRow(self.btnMirrorLCut)
        self.btnMirrorLCut.connect('clicked(bool)', self.onMirrorLCut)

        self.btnInitGenio = qt.QPushButton("B3.2: Tạo mặt phẳng cắt cằm")
        self.btnInitGenio.setStyleSheet("background-color: #ffcccc; font-weight: bold")
        self.btnExecGenio = qt.QPushButton("B3.3: Cắt & Trượt cằm")
        self.btnExecGenio.setStyleSheet("background-color: #ffcccc; font-weight: bold")
        

        genioLabel = qt.QLabel("Lưu ý: Sau khi cắt, hãy kéo Widget để trượt xương.\nĐiểm Me sẽ tự động di chuyển theo mảnh cằm.")
        genioLabel.setStyleSheet("font-style: italic; color: #555;")

        genioFormLayout.addRow(self.btnInitGenio)
        genioFormLayout.addRow(self.btnExecGenio)
        genioFormLayout.addRow(genioLabel)

        # Kết nối tín hiệu
        self.btnInitGenio.connect('clicked(bool)', self.onInitGenio)
        self.btnExecGenio.connect('clicked(bool)', self.onExecGenio)

        # --- SECTION 3: TÍNH TOÁN GO (SAU KHI TRƯỢT CẰM) ---
        paramCollapsibleButton = ctk.ctkCollapsibleButton()
        paramCollapsibleButton.text = "4. Tính toán Go (Dựa trên Me mới)"
        formLayout.addRow(paramCollapsibleButton)
        paramLayout = qt.QFormLayout(paramCollapsibleButton)

        # Góc hàm
        self.angleSlider = ctk.ctkSliderWidget()
        self.angleSlider.singleStep = 1.0
        self.angleSlider.minimum = 90.0
        self.angleSlider.maximum = 160.0
        self.angleSlider.value = 127.0
        self.angleSlider.suffix = " °"
        paramLayout.addRow("Góc hàm mục tiêu:", self.angleSlider)

        # Điểm Lồi cầu
        # self.selectorCoR = self.createFiducialSelector("CoR (Lồi cầu Phải)")
        # paramLayout.addRow("CoR (Phải):", self.selectorCoR)
        # self.selectorCoL = self.createFiducialSelector("CoL (Lồi cầu Trái)")
        # paramLayout.addRow("CoL (Trái):", self.selectorCoL)
        # self.selectorGoR = self.createFiducialSelector("GoR")
        # paramLayout.addRow("GoR (Phải):", self.selectorGoR)
        # self.selectorGoL = self.createFiducialSelector("GoL")
        # paramLayout.addRow("GoL (Trái):", self.selectorGoL)
        
        self.btnStep3 = qt.QPushButton("Tính điểm Go mới")
        self.btnStep3.setStyleSheet("background-color: #ffcccc; font-weight: bold")
        paramLayout.addRow(self.btnStep3)

        # --- SECTION 4: V-LINE CUT ---
        actionsCollapsibleButton = ctk.ctkCollapsibleButton()
        actionsCollapsibleButton.text = "5. Cắt V-Line (Gọt hàm)"
        formLayout.addRow(actionsCollapsibleButton)
        actionsFormLayout = qt.QFormLayout(actionsCollapsibleButton)

        self.curveSelector = slicer.qMRMLNodeComboBox()
        self.curveSelector.nodeTypes = ["vtkMRMLMarkupsCurveNode"]
        self.curveSelector.setMRMLScene(slicer.mrmlScene)
        actionsFormLayout.addRow("Đường cong (OC):", self.curveSelector)

        # Góc cắt (Yaw)
        self.yawSlider = ctk.ctkSliderWidget()
        self.yawSlider.singleStep = 1.0
        self.yawSlider.minimum = -180.0
        self.yawSlider.maximum = 180.0
        self.yawSlider.value = 45.0
        self.yawSlider.suffix = " °"
        actionsFormLayout.addRow("Góc nghiêng cắt (Yaw):", self.yawSlider)

        self.btnStep4 = qt.QPushButton("Tạo mặt cắt & Cắt xương")
        self.btnStep4.setStyleSheet("background-color: #ffcccc; font-weight: bold")
        actionsFormLayout.addRow(self.btnStep4)

        # --- SECTION 5: GUIDE & EXPORT ---
        exportCollapsibleButton = ctk.ctkCollapsibleButton()
        exportCollapsibleButton.text = "6. Guide & Xuất file"
        formLayout.addRow(exportCollapsibleButton)
        exportFormLayout = qt.QFormLayout(exportCollapsibleButton)

        self.btnStep5 = qt.QPushButton("Tạo máng (Band Guide)")
        self.btnStep5.setStyleSheet("background-color: #ffcccc; font-weight: bold")
        self.btnStep6 = qt.QPushButton("Xuất STL")
        self.btnStep6.setStyleSheet("background-color: #ffcccc; font-weight: bold")
        exportFormLayout.addRow(self.btnStep5)
        exportFormLayout.addRow(self.btnStep6)


         # --- SECTION 6: EXPORT REPORT ---
        # --- SECTION 6: EXPORT REPORT ---
        exportREPORT = ctk.ctkCollapsibleButton()
        exportREPORT.text = "7. Xuất báo cáo kết quả"
        formLayout.addRow(exportREPORT)
        exportFormLayout = qt.QFormLayout(exportREPORT)

        # Thêm các ô điền nội dung
        self.patientNameEntry = qt.QLineEdit()
        self.patientNameEntry.placeholderText = "Nhập tên bệnh nhân..."
        exportFormLayout.addRow("Tên bệnh nhân:", self.patientNameEntry)

        self.patientIdEntry = qt.QLineEdit()
        self.patientIdEntry.placeholderText = "Nhập mã số (ID)..."
        exportFormLayout.addRow("Mã số:", self.patientIdEntry)

        self.notesEntry = qt.QTextEdit()
        self.notesEntry.placeholderText = "Nhập ghi chú thêm nếu có..."
        self.notesEntry.setMaximumHeight(60) # Giới hạn chiều cao cho gọn
        exportFormLayout.addRow("Ghi chú:", self.notesEntry)

        
        self.btnStep7 = qt.QPushButton("Xuất XLSX Report")
        self.btnStep7.setStyleSheet("background-color: #ffcccc; font-weight: bold")
        self.btnStep7.clicked.connect(self.onExportXLSX)
        exportFormLayout.addRow(self.btnStep7)


        # Connect signals
        self.btnStep1.connect('clicked(bool)', self.onStep1)
        self.btnStep2.connect('clicked(bool)', self.onStep2)
        self.btnStep3.connect('clicked(bool)', self.onStep3)
        self.btnStep4.connect('clicked(bool)', self.onStep4)
        self.btnStep5.connect('clicked(bool)', self.onStep5)
        self.btnStep6.connect('clicked(bool)', self.onStep6)
        
        # Connect Genio signals
        self.btnInitGenio.connect('clicked(bool)', self.onInitGenio)
        self.btnExecGenio.connect('clicked(bool)', self.onExecGenio)

        self.layout.addStretch(1)


    def getPointToPlaneDistance(self, pointNodeName, planeNodeName):
        import numpy as np
        import slicer

        try:
            pointNode = slicer.util.getNode(pointNodeName)
            planeNode = slicer.util.getNode(planeNodeName)
        except:
            return None

        if pointNode.GetNumberOfControlPoints() == 0:
            return None

        # Lấy tọa độ điểm
        P = np.array(pointNode.GetNthControlPointPosition(0))

        # Lấy origin và normal của plane
        origin = np.array(planeNode.GetOrigin())
        normal = np.array(planeNode.GetNormal())

        norm_length = np.linalg.norm(normal)
        if norm_length == 0:
            return None

        # Khoảng cách có dấu
        distance = np.dot(normal, P - origin) / norm_length

        return round(distance, 2)


    def getDistance(self, nodeName1, nodeName2):

        try:
            node1 = slicer.util.getNode(nodeName1)
            node2 = slicer.util.getNode(nodeName2)
        except:
            return None

        if node1.GetNumberOfControlPoints() == 0 or node2.GetNumberOfControlPoints() == 0:
            return None

        p1 = np.array(node1.GetNthControlPointPosition(0))
        p2 = np.array(node2.GetNthControlPointPosition(0))

        return round(np.linalg.norm(p1 - p2), 2)



    def calculatePatientMetrics(self):
        """
        Hàm này tập trung vào tính toán các chỉ số từ Landmark hoặc Model.
        Trả về một dictionary chứa kết quả.
        """
        results = {}
        
        # Giả sử bạn đã có các biến/hàm tính toán khoảng cách
        # Ví dụ: d_right = self.getDistance("Go_R", "MSP")
        
        results["1.1"] = self.getDistance("N'", "Me'") / self.getDistance("ZyR'", "ZyL'")
        results["1.2"] = self.getDistance("N", "Me") / self.getDistance("ZyR'", "ZyL")


        results["2.1"] = self.getDistance("GoR'", "GoL'") / self.getDistance("ZyR'", "ZyL'")
        results["2.2"] = self.getDistance("GoR", "GoL") / self.getDistance("ZyR", "ZyL")

        results["3.1"] = abs(self.getPointToPlaneDistance("GoR'", "MSP_Auto"))
        results["3.2"] = abs(self.getPointToPlaneDistance("GoL'", "MSP_Auto")  )
        results["3.3"] = abs(self.getPointToPlaneDistance("GoR'", "MSP_Auto")) - abs(self.getPointToPlaneDistance("GoL'", "MSP_Auto"))

        results["3.4"] = abs(self.getPointToPlaneDistance("GoR", "MSP_Auto"))
        results["3.5"] = abs(self.getPointToPlaneDistance("GoL", "MSP_Auto"))
        results["3.6"] = abs(self.getPointToPlaneDistance("GoR", "MSP_Auto")) - abs(self.getPointToPlaneDistance("GoL", "MSP_Auto"))

        results["3.7"] = self.getPointToPlaneDistance("Me", "MSP_Auto")



        results["4.1"] = slicer.util.getNode("Angle_CoR_GoR_N_Me").GetAngleDegrees()
        results["4.2"] = self.getDistance("CoR", "GoR_N")
        results["4.3"] = self.getDistance("GoR_N", "Me")

        results["4.4"] = slicer.util.getNode("Angle_CoL_GoL_N_Me").GetAngleDegrees()
        results["4.5"] = self.getDistance("CoL", "GoL_N")
        results["4.6"] = self.getDistance("GoL_N", "Me")



        results["go_msp"] = "60.8mm / 60.7mm"
        # ... thêm các chỉ số khác vào đây
        
        return results


    def onExportXLSX(self):
        try:
            import pandas as pd
            import datetime
            import qt
            import xlsxwriter
        except ImportError:
            import slicer
            slicer.util.pip_install("pandas openpyxl xlsxwriter")
            import pandas as pd
            import xlsxwriter

        # 1. Thu thập dữ liệu
        name = self.patientNameEntry.text
        patient_id = self.patientIdEntry.text
        notes = self.notesEntry.toPlainText()
        metrics = self.calculatePatientMetrics()

        default_name = f"BaoCao_{patient_id}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
        filePath = qt.QFileDialog.getSaveFileName(None, "Lưu báo cáo", default_name, "*.xlsx")

        if filePath:
            try:
                workbook = xlsxwriter.Workbook(filePath)
                worksheet = workbook.add_worksheet('BaoCao')

                # --- THIẾT LẬP ĐỊNH DẠNG (FORMAT) ---
                # Header chính (Xanh đậm)
                header_fmt = workbook.add_format({'bold': True, 'bg_color': '#1F4E78', 'font_color': 'white', 'border': 1, 'align': 'center'})
                
                # Section chính (Xanh nhạt) - THÔNG TIN BỆNH NHÂN / CHỈ SỐ ĐO ĐẠC
                section_fmt = workbook.add_format({'bold': True, 'bg_color': '#DDEBF7', 'border': 1, 'align': 'center'})
                
                # Sub-header (Màu hồng) - Các mục số 1, 2, 3
                sub_header_fmt = workbook.add_format({'bold': True, 'bg_color': '#FCE4D6', 'font_color': '#C00000', 'border': 1})
                
                # Sub-section (Màu vàng) - 4.1 Góc hàm phải/trái
                sub_section_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFF2CC', 'font_color': '#D6A300', 'border': 1})
                
                # Ô dữ liệu bình thường
                cell_fmt = workbook.add_format({'border': 1, 'valign': 'vcenter'})

                # 2. Cấu trúc dữ liệu (Mỗi tuple: [Dữ liệu], Loại Format)
                # Ta dùng list các tuple để dễ quản lý màu sắc từng dòng
                data_structure = [
                    (["Hạng mục", "Nội dung", "Ghi chú"], header_fmt),
                    (["THÔNG TIN BỆNH NHÂN", "", ""], section_fmt),
                    (["Họ tên", name, ""], cell_fmt),
                    (["Mã ID", patient_id, ""], cell_fmt),
                    (["Ghi chú", notes, ""], cell_fmt),
                    (["", "", ""], None), # Dòng trống
                    (["CHỈ SỐ ĐO ĐẠC", "", ""], section_fmt),

                    (["1.Tỉ lệ khuôn mặt mô mềm và mô xương:", "", ""], sub_header_fmt),
                    (["FI'", metrics.get("1.1", "N/A"), "N-Me'/ ZyR-ZyL'"], cell_fmt),
                    (["FI", metrics.get("1.2", "N/A"), "N-Me/ZyR-ZyL"], cell_fmt),

                    (["2. Tỉ lệ độ rộng góc hàm/ gò má:", "", ""], sub_header_fmt),
                    (["GZI'", metrics.get("2.1", "N/A"), "GoR'-GoL'/ZyR'-ZyL'"], cell_fmt),
                    (["GZI", metrics.get("2.2", "N/A"),  "GoR-GoL/ZyR-ZyL"], cell_fmt),

                    (["3.Khoảng cách từ góc hàm đến mặt phẳng dọc giữa:", "", ""], sub_header_fmt),
                    (["GoR'-MSP", metrics.get("3.1", "N/A"), ""], cell_fmt),
                    (["GoL'- MSP", metrics.get("3.2", "N/A"), ""], cell_fmt),
                    (["Độ lệch", metrics.get("3.3", "N/A"), "|GoR'-MSP| - |GoL'-MSP|"], cell_fmt),
                    (["GoR-MSP", metrics.get("3.4", "N/A"), ""], cell_fmt),
                    (["GoL- MSP", metrics.get("3.5", "N/A"), ""], cell_fmt),
                    (["Độ lệch", metrics.get("3.6", "N/A"), "|GoR-MSP| - |GoL-MSP|"], cell_fmt),
                    (["Me-MSP", metrics.get("3.7", "N/A"), ""], cell_fmt),
                    (["Góc FMA (Frankfort-Mandibular)", "23.3 độ", "Góc mặt phẳng hàm dưới"], cell_fmt),
                    (["Khoảng cách Go-MSP (Phải/Trái)", "60.8mm / 60.7mm", "Mô mềm & Mô xương"], cell_fmt),

                    (["4.Kế hoạch phẫu thuật:", "", ""], sub_header_fmt),
                    (["4.1. Hàm phải", "", ""], sub_section_fmt),
                    (["gCoR-GoR_N-Me", metrics.get("4.1", "N/A"), ""], cell_fmt),
                    (["CoR-GoR_N", metrics.get("4.2", "N/A"), ""], cell_fmt),
                    (["GoR_N-Me", metrics.get("4.3", "N/A"), ""], cell_fmt),
                    (["4.2. Hàm trái", "", ""], sub_section_fmt),
                    (["gCoL-GoL_N-Me", metrics.get("4.4", "N/A"), ""], cell_fmt),
                    (["CoL-GoL_N", metrics.get("4.5", "N/A"), ""], cell_fmt),
                    (["GoL_N-Me", metrics.get("4.6", "N/A"), ""], cell_fmt),
                ]

                # 3. Định dạng độ rộng cột
                worksheet.set_column('A:A', 45)
                worksheet.set_column('B:B', 35)
                worksheet.set_column('C:C', 35)

                # 4. Ghi dữ liệu và Gộp ô (Merge cells) cho các thanh tiêu đề
                for row_num, (row_data, fmt) in enumerate(data_structure):
                    if fmt in [section_fmt, sub_header_fmt, sub_section_fmt] and row_data[1] == "":
                        # Gộp 3 cột lại cho tiêu đề mục
                        worksheet.merge_range(row_num, 0, row_num, 2, row_data[0], fmt)
                    else:
                        for col_num, cell_value in enumerate(row_data):
                            if fmt:
                                worksheet.write(row_num, col_num, cell_value, fmt)
                            else:
                                worksheet.write(row_num, col_num, cell_value)

                workbook.close()
                qt.QMessageBox.information(None, "Thành công", "Báo cáo đã được lưu!")

            except Exception as e:
                qt.QMessageBox.critical(None, "Lỗi", f"Lỗi xuất file: {str(e)}")

    def get_pos(self, node):
        if not node or node.GetNumberOfControlPoints() == 0: return None
        pos = [0, 0, 0]
        # Hàm này lấy World Position, tức là nếu Node bị Transform, nó sẽ lấy toạ độ sau khi dịch chuyển
        node.GetNthControlPointPositionWorld(0, pos)
        return np.array(pos)
    

    def onCreateLineFromPoints(self):
        p1Node = self.linePoint1Selector.currentNode()
        p2Node = self.linePoint2Selector.currentNode()

        if not p1Node or not p2Node:
            slicer.util.errorDisplay("Please select both points to create a line.")
            return

        if p1Node.GetNumberOfControlPoints() == 0 or p2Node.GetNumberOfControlPoints() == 0:
            slicer.util.errorDisplay("Selected fiducials must have at least one control point.")
            return

        # Get coordinates
        p1 = [0.0, 0.0, 0.0]
        p2 = [0.0, 0.0, 0.0]
        p1Node.GetNthControlPointPositionWorld(0, p1)
        p2Node.GetNthControlPointPositionWorld(0, p2)

        # Create Line node
        lineNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsLineNode", "P1nP2")
        lineNode.AddControlPointWorld(p1)
        lineNode.AddControlPointWorld(p2)

        # Optional: select it automatically
        self.lineSelector.setCurrentNode(lineNode)


    def fit_plane_svd(self, points):
        pts = np.array(points); c = np.mean(pts, axis=0)
        _, _, vh = np.linalg.svd(pts - c)
        return c, vh[2, :]



    def onCreateFrankfortPlane(self):

        try:
            planeNode = slicer.util.getNode("Frankfort")
        except:
            planeNode = slicer.mrmlScene.AddNewNodeByClass(
                "vtkMRMLMarkupsPlaneNode", "Frankfort"
            )

        # Lấy các landmark (đúng tên node)
        pPoL_node = slicer.util.getNode('PoL')
        pPoR_node = slicer.util.getNode('PoR')
        pOrL_node = slicer.util.getNode('OrL')
        pOrR_node = slicer.util.getNode('OrR')

        # Lấy tọa độ (dùng hàm có sẵn của bạn)
        pPoL = self.get_pos(pPoL_node)
        pPoR = self.get_pos(pPoR_node)
        pOrL = self.get_pos(pOrL_node)
        pOrR = self.get_pos(pOrR_node)

        # Fit plane (dùng logic có sẵn)
        origin, normal = self.fit_plane_svd([pPoL, pPoR, pOrL, pOrR])

        # Gán cho Markups Plane
        planeNode.SetOriginWorld(origin.tolist())
        planeNode.SetNormalWorld(normal.tolist())
        planeNode.SetDisplayVisibility(True)

        # Auto select trong GUI
        self.planeSelector.setCurrentNode(planeNode)

        slicer.util.infoDisplay("Frankfort plane created from PoL, PoR, OrL, OrR")

    def onCalculate(self):
        pointA = self.pointASelector.currentNode()
        pointB = self.pointBSelector.currentNode()
        lineA = self.lineSelector.currentNode()
        planeA = self.planeSelector.currentNode()
        planeB = self.plane2Selector.currentNode()

        if not planeA or not planeB:
            slicer.util.errorDisplay("Please select Plane A and Plane B")
            return

        resultText = ""

        # ================== NORMALS ==================
        nA = np.array(planeA.GetNormalWorld())
        nB = np.array(planeB.GetNormalWorld())
        nA = nA / np.linalg.norm(nA)
        nB = nB / np.linalg.norm(nB)

        oA = np.array(planeA.GetOriginWorld())
        oB = np.array(planeB.GetOriginWorld())

        # ================== PLANE – PLANE ==================
        cosPP = abs(np.dot(nA, nB))
        cosPP = np.clip(cosPP, -1.0, 1.0)
        anglePA_PB = np.degrees(np.arccos(cosPP))
        anglePA_PB = min(anglePA_PB, 180 - anglePA_PB)

        resultText += f"Góc Plane A – Plane B: {anglePA_PB:.2f}°\n"

        # ================== LINE (OPTIONAL) ==================
        if lineA and lineA.GetNumberOfControlPoints() >= 2:
            p1 = np.array(lineA.GetNthControlPointPositionWorld(0))
            p2 = np.array(lineA.GetNthControlPointPositionWorld(1))
            v = p2 - p1

            if np.linalg.norm(v) > 0:
                v = v / np.linalg.norm(v)

                angleLA_PA = 90 - np.degrees(np.arccos(abs(np.dot(v, nA))))
                angleLA_PB = 90 - np.degrees(np.arccos(abs(np.dot(v, nB))))

                resultText += f"Góc Line A – Plane A: {angleLA_PA:.2f}°\n"
                resultText += f"Góc Line A – Plane B: {angleLA_PB:.2f}°\n"
        else:
            resultText += "(Không có Line)\n"

        # ================== POINT A ==================
        if pointA and pointA.GetNumberOfControlPoints() >= 1:
            pA = np.array(pointA.GetNthControlPointPositionWorld(0))

            dA_PA = abs(np.dot(pA - oA, nA))
            dA_PB = abs(np.dot(pA - oB, nB))

            resultText += f"Point A → Plane A: {dA_PA:.2f} mm\n"
            resultText += f"Point A → Plane B: {dA_PB:.2f} mm\n"

        # ================== POINT B ==================
        if pointB and pointB.GetNumberOfControlPoints() >= 1:
            pB = np.array(pointB.GetNthControlPointPositionWorld(0))

            dB_PA = abs(np.dot(pB - oA, nA))
            dB_PB = abs(np.dot(pB - oB, nB))

            resultText += f"Point B → Plane A: {dB_PA:.2f} mm\n"
            resultText += f"Point B → Plane B: {dB_PB:.2f} mm\n"

        # ================== POINT A – POINT B ==================
        if pointA and pointB and \
        pointA.GetNumberOfControlPoints() >= 1 and \
        pointB.GetNumberOfControlPoints() >= 1:

            dAB = np.linalg.norm(pA - pB)
            resultText += f"Point A – Point B: {dAB:.2f} mm\n"

        self.resultLabel.text = resultText






    def createFiducialSelector(self, tooltip):
        s = slicer.qMRMLNodeComboBox()
        s.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        s.selectNodeUponCreation = True
        s.addEnabled = True
        s.noneEnabled = False
        s.setMRMLScene(slicer.mrmlScene)
        s.setToolTip(tooltip)
        return s

    def onModeChanged(self):
        is4Pt = self.radio4pt.isChecked()
        self._currentMode = 4 if is4Pt else 3
        # self.selectorIF.setEnabled(is4Pt)


    def onStep1(self):
        # if not self._checkInputs(1): return
        try:
            qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
            self.logic.run_step_1_msp(mode=self._currentMode)
            qt.QMessageBox.information(None, "Xong", "Đã tạo MSP và Mirror.")
        except Exception as e:
            qt.QMessageBox.critical(None, "Lỗi B1", str(e))
        finally:
            qt.QApplication.restoreOverrideCursor()

    def onStep2(self):
        return True

    # --- GENIOPLASTY HANDLERS (NEW B2) ---
    def onMirrorLCut(self):
        srcNode = self.lCutCurveSelector.currentNode()
        if not srcNode:
            qt.QMessageBox.warning(None, "Lỗi", "Hãy chọn đường L trước!")
            return
            
        try:
            # Tạo đường đối xứng
            mirrorNode = self.logic.create_mirror_curve_node(srcNode, "L_Mirror")
            
            # Cập nhật lại ComboBox để nó hiển thị L_Mirror ngay lập tức
            self.lCutCurveSelector.setCurrentNode(mirrorNode)
            
            qt.QMessageBox.information(None, "Thành công", "Đã tạo đường L_Mirror đối xứng!")
        except Exception as e:
            qt.QMessageBox.critical(None, "Lỗi logic", str(e))

    def onInitGenio(self):
        try:
            lCutNode = self.lCutCurveSelector.currentNode()
            # Tìm đường đối xứng trong Scene dựa trên tên bạn đã đặt ở bước trước
            lMirrorNode = slicer.util.getNode("L_Mirror") 
            
            if not lCutNode:
                qt.QMessageBox.warning(None, "Thiếu input", "Hãy chọn đường cắt L trước!")
                return

            if lMirrorNode:
                # Nếu đã có đường đối xứng, tạo mặt phẳng qua cả hai
                self.logic.init_genio_plane_from_dual_curves(lCutNode, lMirrorNode)
                msg = "Đã tạo mặt phẳng cân đối dựa trên L và L_Mirror."
            else:
                # Nếu chưa có đối xứng, tạo mặt phẳng dựa trên 1 đường và điểm Me như cũ
                meNode = self.selectorMe.currentNode()
                self.logic.init_genio_plane_from_curve(lCutNode, meNode)
                msg = "Chưa có L_Mirror, mặt phẳng được tạo dựa trên đường L đơn lẻ."

            qt.QMessageBox.information(None, "Genioplasty", msg)
        
        except Exception as e:
            qt.QMessageBox.critical(None, "Lỗi Genio", str(e))

    def onExecGenio(self):
        if not self.mandibleSelector.currentNode():
             qt.QMessageBox.warning(None, "Thiếu input", "Chưa chọn xương hàm!")
             return
        try:
            qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
            
            nodeMe = self.selectorMe.currentNode()
            mandibleNode = self.mandibleSelector.currentNode()
            
            # Thực hiện cắt trên xương gốc
            self.logic.run_genioplasty_cut(
                boneNode=mandibleNode, # Truyền xương gốc
                plane_name="Genio_Cut_Plane",
                nodeMe=nodeMe 
            )
            
            qt.QMessageBox.information(None, "Genioplasty", "Đã cắt cằm thành công! \nHãy kéo Widget trong 3D View để trượt xương. \nĐiểm Me sẽ di chuyển theo.")
        except Exception as e:
             qt.QMessageBox.critical(None, "Lỗi Genio", str(e))
        finally:
            qt.QApplication.restoreOverrideCursor()

    # --- CALC GO HANDLERS (NEW B3) ---
    def onStep3(self):
        # if not self._checkInputs(3): return
        try:
            qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
            target_angle = self.angleSlider.value
            
            # Lưu ý: Lúc này Me đã bị di chuyển bởi Genioplasty
            # Logic get_pos sẽ tự động lấy toạ độ thế giới mới của Me
            
            results = self.logic.run_step_3_calculate_go(
                target_angle_deg=target_angle
            )
            
            msg = f"Đã tính xong điểm Go mới (Góc {target_angle}°).\n"
            if "R" in results: msg += f"- Phải: {results['R']:.1f}°\n"
            if "L" in results: msg += f"- Trái: {results['L']:.1f}°\n"
            qt.QMessageBox.information(None, "Kết quả B3", msg)
        except Exception as e:
            qt.QMessageBox.critical(None, "Lỗi B3", str(e))
        finally:
            qt.QApplication.restoreOverrideCursor()

    def onStep4(self):
        try:
            qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
            
            if not self.logic.msp_origin is not None:
                qt.QMessageBox.warning(None, "Cảnh báo", "Chưa có MSP. Hãy chạy Bước 1 trước!")
                return
            
            if not self.curveSelector.currentNode():
                qt.QMessageBox.warning(None, "Cảnh báo", "Chưa chọn đường cong (Curve) để cắt!")
                return

            yaw_val = self.yawSlider.value
            curveNode = self.curveSelector.currentNode()
            mandibleNode = slicer.util.getNode('Mandible')
            

            # Logic sẽ tự động tìm 'Mandible_Body' (kết quả của genio) để cắt tiếp
            self.logic.run_step_4_create_sheets_and_cut(
                mandibleNode,
                yaw_degrees=yaw_val,
                curveNode=curveNode
            )
            qt.QMessageBox.information(None, "Xong", f"Đã tạo Ribbon (Yaw={yaw_val}°) và cắt xương thành công.")
        except Exception as e:
            qt.QMessageBox.critical(None, "Lỗi B4", str(e))
        finally:
            qt.QApplication.restoreOverrideCursor()

    def onStep5(self):
        """Bước 5: Tạo máng hướng dẫn hiển thị trên màn hình 3D."""
        try:
            qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)
            
            # Cấu hình các thông số máng
            params = {
                "clearance": 0.2,
                "thickness": 1.2,
                "height": 15.0
            }
            
            # Gọi logic tạo máng (View only)
            self.logic.run_step_5_create_fragment_guides(params)
            
            qt.QMessageBox.information(None, "Thành công", "Đã tạo máng hướng dẫn (Guide). Hãy kiểm tra trên màn hình 3D trước khi xuất file.")
            
        except Exception as e:
            qt.QMessageBox.critical(None, "Lỗi B5", f"Không thể tạo máng: {str(e)}")
        finally:
            qt.QApplication.restoreOverrideCursor()

    def onStep6(self):
        outputFolder = qt.QFileDialog.getExistingDirectory(None, "Chọn thư mục lưu STL")
        if not outputFolder: return
        try:
            self.logic.run_step_5_export(outputFolder)
            qt.QMessageBox.information(None, "Xong", f"Đã xuất file vào:\n{outputFolder}")
        except Exception as e:
            qt.QMessageBox.critical(None, "Lỗi Xuất file", str(e))

    def plane_from_three_points(self, p1, p2, p3):
        n = np.cross(p2-p1, p3-p1); n /= np.linalg.norm(n)
        return (p1+p2+p3)/3.0, n

    def onCreatePlaneFromPoints(self):
        p1 = self.planePoint1Selector.currentNode()
        p2 = self.planePoint2Selector.currentNode()
        p3 = self.planePoint3Selector.currentNode()
        p4 = self.planePoint4Selector.currentNode()

        if not (p1 and p2 and p3):
            slicer.util.messageBox("Please select at least 3 points")
            return
        points = []

        for node in [p1, p2, p3]:
            pos = [0, 0, 0]
            node.GetNthControlPointPosition(0, pos)
            points.append(pos)

        if p4:
            pos4 = [0, 0, 0]
            p4.GetNthControlPointPosition(0, pos4)
            points.append(pos4)

        # Tạo plane
        if len(points) == 3:
            origin, normal = self.plane_from_three_points(points[0], points[1], points[2])
        else:
            origin, normal = self.fit_plane_svd(points)

        planeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsPlaneNode")
        planeNode.SetName("CustomPlane")
        planeNode.SetOrigin(origin)
        planeNode.SetNormal(normal)

        slicer.util.messageBox("Custom plane created successfully!")



# ==============================================================================
#  CLASS 3: LOGIC (UPDATED FOR WORKFLOW)
# ==============================================================================
class gotxuonghamLogic(ScriptedLoadableModuleLogic):
    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)
        self.msp_origin = None
        self.msp_normal = None
        self.msp_name = "MSP_Auto"

    def get_pos(self, node):
        if not node or node.GetNumberOfControlPoints() == 0: return None
        pos = [0, 0, 0]
        # Hàm này lấy World Position, tức là nếu Node bị Transform, nó sẽ lấy toạ độ sau khi dịch chuyển
        node.GetNthControlPointPositionWorld(0, pos)
        return np.array(pos)

    # --------------------------------------------------------------------------
    # BƯỚC 1: MSP & MIRROR
    # --------------------------------------------------------------------------
    def run_step_1_msp(self,mode=3):

        pNa_node = slicer.util.getNode('N')
        pBa_node = slicer.util.getNode('Ba')
        pOp_node = slicer.util.getNode('Op')
        pIF_node = slicer.util.getNode('IF')

        pNa = self.get_pos(pNa_node)
        pBa = self.get_pos(pBa_node)
        pOp = self.get_pos(pOp_node)
        pIF = self.get_pos(pIF_node)



        mandibleNode= slicer.util.getNode('Mandible')


        if mode == 3:
            origin, normal = self.plane_from_three_points(pNa, pBa, pOp)
        elif mode == 4:
            origin, normal = self.fit_plane_svd([pNa, pBa, pOp, pIF])
        

        # Định hướng normal: X > 0 (Right)
        if np.dot(normal, [1,0,0]) < 0: normal = -normal
        
        self.msp_origin = origin
        self.msp_normal = normal

        self.create_markups_plane(self.msp_name, origin, normal, size=(250,250))
        self.mirror_model(mandibleNode, origin, normal, suffix="_Mirror")

    # --------------------------------------------------------------------------
    # BƯỚC 2 (MỚI): GENIOPLASTY
    # --------------------------------------------------------------------------

    def onCreatePlaneFromPoints(self):
        p1 = self.planePoint1Selector.currentNode()
        p2 = self.planePoint2Selector.currentNode()
        p3 = self.planePoint3Selector.currentNode()
        p4 = self.planePoint4Selector.currentNode()

        if not (p1 and p2 and p3):
            slicer.util.messageBox("Please select at least 3 points")
            return

        points = [p1, p2, p3]

        # Nếu có chọn thêm điểm thứ 4 thì dùng luôn
        if p4:
            points.append(p4)

        coords = []
        for p in points:
            pos = [0, 0, 0]
            p.GetNthControlPointPosition(0, pos)
            coords.append(pos)

        if len(coords) == 3:
            origin, normal = self.plane_from_three_points(*coords)
        else:
            origin, normal = self.fit_plane_svd(coords)

        planeNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsPlaneNode")
        planeNode.SetOrigin(origin)
        planeNode.SetNormal(normal)

        slicer.util.messageBox("Custom plane created successfully!")

    def init_genio_plane(self, meNode=None):
        planeName = "Genio_Cut_Plane"
        center = [0, 0, 0]
        if meNode:
            meNode.GetNthControlPointPositionWorld(0, center)
            center[2] += 12.0 # Lên trên
            center[1] += 5.0  # Ra sau
        else:
            center = [0, -60, -50]

        normal = [0.0, -0.3, 1.0] 
        norm_len = np.linalg.norm(normal)
        normal = [n/norm_len for n in normal]

        self.create_markups_plane(planeName, center, normal, size=(60, 50))
        print(f"✅ Đã tạo mặt phẳng '{planeName}'.")
        slicer.util.selectModule("Markups")

    def run_genioplasty_cut(self, boneNode, plane_name="Genio_Cut_Plane", nodeMe=None):
        # 1. Check Input
        try:
            planeNode = slicer.util.getNode(plane_name)
        except:
            raise ValueError("Chưa có mặt phẳng cắt (Genio_Cut_Plane)!")

        print(f"🔪 Đang cắt '{boneNode.GetName()}'...")

        # 2. Ẩn xương cũ
        boneNode.GetDisplayNode().SetVisibility(False)

        # 3. Lấy thông số mặt phẳng
        planeNormal = [0.0]*3; planeOrigin = [0.0]*3
        planeNode.GetNormalWorld(planeNormal)
        planeNode.GetOriginWorld(planeOrigin)

        planeUpper = vtk.vtkPlane()
        planeUpper.SetNormal(planeNormal); planeUpper.SetOrigin(planeOrigin)
        planeLower = vtk.vtkPlane()
        planeLower.SetNormal([-n for n in planeNormal]); planeLower.SetOrigin(planeOrigin)

        planesBody = vtk.vtkPlaneCollection(); planesBody.AddItem(planeUpper)
        planesChin = vtk.vtkPlaneCollection(); planesChin.AddItem(planeLower)

        # 4. Clean & Cut
        triFilter = vtk.vtkTriangleFilter()
        triFilter.SetInputData(boneNode.GetPolyData())
        triFilter.Update()
        
        normFilter = vtk.vtkPolyDataNormals()
        normFilter.SetInputData(triFilter.GetOutput())
        normFilter.AutoOrientNormalsOn(); normFilter.ConsistencyOn()
        normFilter.Update()
        cleanInput = normFilter.GetOutput()

        def perform_cut(poly, planes):
            clipper = vtk.vtkClipClosedSurface()
            clipper.SetInputData(poly)
            clipper.SetClippingPlanes(planes)
            clipper.SetGenerateFaces(True) 
            clipper.SetScalarModeToLabels()
            clipper.Update()
            
            # Keep largest region
            conn = vtk.vtkConnectivityFilter()
            conn.SetInputData(clipper.GetOutput())
            conn.SetExtractionModeToLargestRegion()
            conn.Update()
            return conn.GetOutput()

        chinPoly = perform_cut(cleanInput, planesChin)

        if chinPoly.GetNumberOfPoints() == 0:
            raise ValueError("Không cắt được mảnh cằm nào! Hãy chỉnh lại mặt phẳng.")

        # 5. Hiển thị kết quả
        # Quan trọng: Body đặt tên là Mandible_Body để bước sau nhận diện
        chinNode = self.create_model_node("Chin_Fragment", chinPoly, color=(1.0, 0.6, 0.6))
        
        planeNode.GetDisplayNode().SetVisibility(False)

        # 6. Tạo Slider Transform
        try: slicer.mrmlScene.RemoveNode(slicer.util.getNode("Genio_Slider"))
        except: pass

        transformNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode")
        transformNode.SetName("Genio_Slider")
        transformNode.CreateDefaultDisplayNodes()
        
        # Gắn Cằm và điểm Me vào Transform
        chinNode.SetAndObserveTransformNodeID(transformNode.GetID())
        if nodeMe:
            nodeMe.SetAndObserveTransformNodeID(transformNode.GetID())

        # Setup Widget
        dn = transformNode.GetDisplayNode()
        if dn: dn.SetEditorVisibility(True)
        
        mat = vtk.vtkMatrix4x4()
        mat.SetElement(0, 3, planeOrigin[0])
        mat.SetElement(1, 3, planeOrigin[1])
        mat.SetElement(2, 3, planeOrigin[2])
        # transformNode.SetMatrixTransformToParent(mat) 

        print("✅ Genioplasty hoàn tất.")
        slicer.util.selectModule("Transforms")

    # --------------------------------------------------------------------------
    # BƯỚC 3: TÍNH GO (SAU KHI ME ĐÃ DI CHUYỂN)
    # --------------------------------------------------------------------------

    def pick_gonion_outer(self, Me, Co, mand_pd, O_msp, N_msp, side_label, target_angle_deg, ratio=2.0):
        # Code cũ giữ nguyên logic toán học
        Y = np.linalg.norm(Co - Me)
        alpha_rad = math.radians(target_angle_deg)
        denom = 1.0 + ratio**2 - 2.0 * ratio * math.cos(alpha_rad)
        if denom <= 1e-12: raise ValueError("Góc không hợp lệ")
        d = Y / math.sqrt(denom)
        L = ratio * d 
        u = (Me - Co) / Y 
        a = (d**2 - L**2 + Y**2) / (2.0 * Y)
        P0 = Co + a * u

        plane = vtk.vtkPlane()
        plane.SetOrigin(P0); plane.SetNormal(u)
        cutter = vtk.vtkCutter()
        cutter.SetInputData(mand_pd); cutter.SetCutFunction(plane); cutter.Update()
        
        cutPoly = cutter.GetOutput()
        if cutPoly.GetNumberOfPoints() == 0: raise ValueError(f"[{side_label}] Vết cắt rỗng.")

        points = vtk.util.numpy_support.vtk_to_numpy(cutPoly.GetPoints().GetData())
        vec_P_Co = Co - points; vec_P_Me = Me - points
        norm_P_Co = np.linalg.norm(vec_P_Co, axis=1)
        norm_P_Me = np.linalg.norm(vec_P_Me, axis=1)

        mask = (norm_P_Co > 1e-6) & (norm_P_Me > 1e-6)
        points = points[mask]; vec_P_Co = vec_P_Co[mask]; vec_P_Me = vec_P_Me[mask]
        norm_P_Co = norm_P_Co[mask]; norm_P_Me = norm_P_Me[mask]

        dot = np.sum(vec_P_Co * vec_P_Me, axis=1)
        angles = np.degrees(np.arccos(np.clip(dot / (norm_P_Co * norm_P_Me), -1, 1)))

        angle_diff = np.abs(angles - target_angle_deg)
        lat_dist = np.dot(points - O_msp, N_msp)
        side_sign = np.sign(np.dot(Co - O_msp, N_msp))
        penalty = np.where(np.sign(lat_dist) != side_sign, 1000.0, 0.0)
        z_score = (points[:, 2] - np.min(points[:, 2])) / (np.ptp(points[:, 2]) + 1e-6) * 5.0
        
        best_idx = np.argmin(angle_diff + penalty + z_score)
        return points[best_idx]

    

    # --------------------------------------------------------------------------
    # BƯỚC 5: GUIDE & UTILS (GIỮ NGUYÊN)
    # --------------------------------------------------------------------------
    def run_step_4_create_guides_robust(self, mandibleNode=None):
        # Ưu tiên tạo guide trên mandible_final (kết quả cuối cùng của Body)
        target = slicer.util.getNode("mandible_final")
        if not target: target = slicer.util.getNode("Mandible_Body")
        if not target: target = mandibleNode
        
        if not target: raise ValueError("Không tìm thấy xương để tạo guide")
        
        CLEARANCE = 0.2; SHELL = 2.0; H = 18.0
        if slicer.util.getNodes("cut_1") and slicer.util.getNodes("CoR"):
            self.create_band_guide_on_bone(target, "cut_1", "guide_bone_1", "CoR", CLEARANCE, SHELL, H)
        if slicer.util.getNodes("cut_2") and slicer.util.getNodes("CoL"):
            self.create_band_guide_on_bone(target, "cut_2", "guide_bone_2", "CoL", CLEARANCE, SHELL, H)


    def create_band_guide_on_bone(self, boneNode, cutName, guideName, upLandmarkName, 
                                  clearance=0.2, thickness=2.0, height=15.0):
        bonePD = self.ensure_normals(boneNode.GetPolyData())
        cutNode = slicer.util.getNode(cutName)
        cutPD = self.ensure_normals(cutNode.GetPolyData())
        pUp = self.get_pos(slicer.util.getNode(upLandmarkName))
        
        bounds = [0]*6; cutPD.GetBounds(bounds)
        margin = height + 10.0
        bounds = [bounds[0]-margin, bounds[1]+margin, bounds[2]-margin, bounds[3]+margin, bounds[4]-margin, bounds[5]+margin]
        
        impBone = vtk.vtkImplicitPolyDataDistance(); impBone.SetInput(bonePD)
        res = 0.4; dim = [int((bounds[1]-bounds[0])/res), int((bounds[3]-bounds[2])/res), int((bounds[5]-bounds[4])/res)]
        
        sample = vtk.vtkSampleFunction(); sample.SetImplicitFunction(impBone); sample.SetModelBounds(bounds); sample.SetSampleDimensions(dim); sample.ComputeNormalsOff()
        thresh = vtk.vtkImageThreshold(); thresh.SetInputConnection(sample.GetOutputPort())
        thresh.ThresholdBetween(clearance, clearance + thickness); thresh.SetInValue(1); thresh.SetOutValue(0); thresh.SetOutputScalarTypeToUnsignedChar()
        
        mc = vtk.vtkDiscreteMarchingCubes(); mc.SetInputConnection(thresh.GetOutputPort()); mc.SetValue(0, 1); mc.Update()
        smoother = vtk.vtkWindowedSincPolyDataFilter(); smoother.SetInputConnection(mc.GetOutputPort()); smoother.SetNumberOfIterations(10); smoother.NormalizeCoordinatesOn(); smoother.Update()
        shellPD = smoother.GetOutput()
        if shellPD.GetNumberOfPoints() == 0: return

        impCut = vtk.vtkImplicitPolyDataDistance(); impCut.SetInput(cutPD)
        dist_up = impCut.EvaluateFunction(pUp)
        sign_up = 1.0 if dist_up >= 0 else -1.0
        
        clipper1 = vtk.vtkClipPolyData(); clipper1.SetInputData(shellPD); clipper1.SetClipFunction(impCut); clipper1.SetValue(0.0)
        if sign_up > 0: clipper1.InsideOutOn()
        else: clipper1.InsideOutOff()
        clipper1.Update()
        
        clipper2 = vtk.vtkClipPolyData(); clipper2.SetInputData(clipper1.GetOutput()); clipper2.SetClipFunction(impCut)
        cut_value = height if sign_up > 0 else -height
        clipper2.SetValue(cut_value)
        if sign_up > 0: clipper2.InsideOutOff()
        else: clipper2.InsideOutOn()
        clipper2.Update()
        bandShell = clipper2.GetOutput()
        
        if self.msp_origin is not None:
            planeMSP = vtk.vtkPlane(); planeMSP.SetOrigin(self.msp_origin); planeMSP.SetNormal(self.msp_normal)
            vec_lat = pUp - self.msp_origin
            keep_pos = (np.dot(vec_lat, self.msp_normal) >= 0)
            clipper3 = vtk.vtkClipPolyData(); clipper3.SetInputData(bandShell); clipper3.SetClipFunction(planeMSP)
            if keep_pos: clipper3.InsideOutOn()
            else: clipper3.InsideOutOff()
            clipper3.Update()
            finalShell = clipper3.GetOutput()
        else: finalShell = bandShell

        clean = vtk.vtkCleanPolyData(); clean.SetInputData(finalShell); clean.Update()
        conn = vtk.vtkPolyDataConnectivityFilter(); conn.SetInputConnection(clean.GetOutputPort()); conn.SetExtractionModeToLargestRegion(); conn.Update()
        self.create_model_node(guideName, conn.GetOutput(), color=(0.6, 1.0, 0.6), opacity=1.0)

    # --------------------------------------------------------------------------
    # BƯỚC 6: XUẤT TẤT CẢ DỮ LIỆU SANG STL (CẬP NHẬT)
    # --------------------------------------------------------------------------
    def run_step_5_export(self, folder):
        """
        Xuất các mảnh xương và máng hướng dẫn ra thư mục chỉ định.
        """
        # Danh sách các node quan trọng cần xuất
        nodes = [
            "bone_1",           # Mảnh xương gọt phải
            "bone_2",           # Mảnh xương gọt trái
            "Final_Guide_bone_1",     # Máng hướng dẫn phải
            "Final_Guide_bone_2"      # Máng hướng dẫn trái
        ]
        
        count = 0
        if not os.path.exists(folder):
            os.makedirs(folder)

        print(f"--- Đang bắt đầu xuất STL vào: {folder} ---")
        
        for name in nodes:
            try:
                node = slicer.util.getNode(name)
                if node:
                    file_path = os.path.join(folder, f"{name}.stl")
                    # Lưu node dưới dạng STL
                    success = slicer.util.saveNode(node, file_path)
                    if success:
                        print(f"✅ Đã xuất: {file_path}")
                        count += 1
            except Exception as e:
                # Bỏ qua nếu không tìm thấy node (người dùng chưa chạy bước đó)
                pass
        
        print(f"--- Hoàn tất! Đã xuất thành công {count} tệp tin. ---")
        return count

    # --- HELPER UTILS (COPY FROM ORIGINAL) ---
    def mirror_points_array(self, points, plane_org, plane_norm):
        mirrored = []; n = np.array(plane_norm); o = np.array(plane_org)
        for p in points:
            p_arr = np.array(p)
            mirrored.append(p_arr - 2 * np.dot(p_arr - o, n) * n)
        return np.array(mirrored)

    def plane_from_three_points(self, p1, p2, p3):
        n = np.cross(p2-p1, p3-p1); n /= np.linalg.norm(n)
        return (p1+p2+p3)/3.0, n

    def fit_plane_svd(self, points):
        pts = np.array(points); c = np.mean(pts, axis=0)
        _, _, vh = np.linalg.svd(pts - c)
        return c, vh[2, :]

    def create_markups_plane(self, name, o, n, size):
        try: slicer.mrmlScene.RemoveNode(slicer.util.getNode(name))
        except: pass
        p = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsPlaneNode', name)
        p.SetOriginWorld(o); p.SetNormalWorld(n); p.SetSize(*size)

    def mirror_model(self, src, o, n, suffix):
        if not src: return None
        nn = np.array(n).reshape(3,1); oo = np.array(o).reshape(3,1)
        R = np.eye(3) - 2 * np.dot(nn, nn.T); t = 2 * np.dot(nn.T, oo) * nn
        m = vtk.vtkMatrix4x4()
        for r in range(3):
            for c in range(3): m.SetElement(r,c, R[r,c])
            m.SetElement(r, 3, t[r])
        cloned = slicer.mrmlScene.CopyNode(src); cloned.SetName(src.GetName() + suffix)
        trans = vtk.vtkTransform(); trans.SetMatrix(m)
        pdf = vtk.vtkTransformPolyDataFilter(); pdf.SetInputData(cloned.GetPolyData()); pdf.SetTransform(trans); pdf.Update()
        cloned.SetAndObservePolyData(pdf.GetOutput())
        if cloned.GetDisplayNode(): cloned.GetDisplayNode().SetOpacity(0.5); cloned.GetDisplayNode().SetColor(1, 1, 0)
        return cloned

    def ensure_normals(self, pd):
        n=vtk.vtkPolyDataNormals(); n.SetInputData(pd); n.ConsistencyOn(); n.SplittingOff(); n.AutoOrientNormalsOn(); n.Update()
        return n.GetOutput()

    def create_model_node(self, name, pd, color=(1,1,1), opacity=1.0, visibility=True):
        try: slicer.mrmlScene.RemoveNode(slicer.util.getNode(name))
        except: pass
        n = slicer.modules.models.logic().AddModel(pd); n.SetName(name)
        dn = n.GetDisplayNode()
        dn.SetColor(color); dn.SetOpacity(opacity); dn.SetVisibility(visibility); dn.SetBackfaceCulling(0)
        return n

    def split_bone_by_sheet(self, bone, sheet, msp_o, msp_n):
        imp=vtk.vtkImplicitPolyDataDistance(); imp.SetInput(sheet)
        c=vtk.vtkClipPolyData(); c.SetInputData(bone); c.SetClipFunction(imp); c.SetValue(0)
        c.InsideOutOff(); c.Update(); p1=self.keep_largest_island(c.GetOutput())
        c.InsideOutOn(); c.Update(); p2=self.keep_largest_island(c.GetOutput())
        c1=np.array(self.get_center(p1)); c2=np.array(self.get_center(p2))
        if abs(np.dot(c1-msp_o, msp_n)) > abs(np.dot(c2-msp_o, msp_n)): return p1, p2
        return p1, p2

    def keep_largest_island(self, pd):
        c=vtk.vtkPolyDataConnectivityFilter(); c.SetInputData(pd); c.SetExtractionModeToLargestRegion(); c.Update()
        cl=vtk.vtkCleanPolyData(); cl.SetInputConnection(c.GetOutputPort()); cl.Update()
        return cl.GetOutput()

    def get_center(self, pd):
        c=vtk.vtkCenterOfMass(); c.SetInputData(pd); c.Update()
        return c.GetCenter()

    def create_fiducial_node(self, name, pos, color=(1,0,0)):
        try: slicer.mrmlScene.RemoveNode(slicer.util.getNode(name))
        except: pass
        n = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", name)
        n.AddControlPointWorld(vtk.vtkVector3d(pos[0], pos[1], pos[2]))
        n.GetDisplayNode().SetSelectedColor(color)
        
    def create_angle_node(self, name, p1, p2, p3):
        try: slicer.mrmlScene.RemoveNode(slicer.util.getNode(name))
        except: pass
        n = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsAngleNode", name)
        n.AddControlPointWorld(vtk.vtkVector3d(p1)); n.AddControlPointWorld(vtk.vtkVector3d(p2)); n.AddControlPointWorld(vtk.vtkVector3d(p3))
        n.GetDisplayNode().SetColor(1, 1, 0)

    def calculate_angle_deg(self, A, B, C):
        BA = A - B; BC = C - B
        norm1 = np.linalg.norm(BA)
        norm2 = np.linalg.norm(BC)
        if norm1 == 0 or norm2 == 0: return 0.0
        cosine_angle = np.dot(BA, BC) / (norm1 * norm2)
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        return np.degrees(angle)

    def solidify(self, polyData, thickness=1.0):
        extruder = vtk.vtkLinearExtrusionFilter()
        extruder.SetInputData(polyData)
        extruder.SetExtrusionTypeToNormalExtrusion()
        extruder.SetScaleFactor(thickness)
        extruder.Update()
        cleaner = vtk.vtkCleanPolyData()
        cleaner.SetInputData(extruder.GetOutput())
        cleaner.Update()
        return cleaner.GetOutput()
    
    def smooth_model(self, polyData, iterations=30, relaxation=0.2):
        smoothFilter = vtk.vtkSmoothPolyDataFilter()
        smoothFilter.SetInputData(polyData)
        smoothFilter.SetNumberOfIterations(iterations)
        smoothFilter.SetRelaxationFactor(relaxation)
        smoothFilter.FeatureEdgeSmoothingOff()
        smoothFilter.BoundarySmoothingOn()
        smoothFilter.Update()
        cleaner = vtk.vtkCleanPolyData()
        cleaner.SetInputData(smoothFilter.GetOutput())
        cleaner.Update()
        return cleaner.GetOutput()

    def rotate_vector(self, vector, axis, angle_degrees):
        theta = math.radians(angle_degrees)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        cross_prod = np.cross(axis, vector)
        return vector * cos_t + cross_prod * sin_t

    def create_ribbon_polydata(self, curve_node, angle, depth, out, ext_f, ext_b, num_samples=100):
        if not curve_node: return None
        
        # 1. Lấy Tọa độ điểm điều khiển gốc
        control_pts = []
        n_control = curve_node.GetNumberOfControlPoints()
        if n_control < 2: return None
        for i in range(n_control):
            p = [0.0]*3
            curve_node.GetNthControlPointPosition(i, p)
            control_pts.append(np.array(p))
        control_pts = np.array(control_pts)

        # 2. LẤY MẪU LẠI ĐƯỜNG CONG (Resampling)
        # *Sử dụng Cardinal Spline (hoặc logic tương đương) để tạo nhiều điểm mượt hơn.*
        # GIẢ ĐỊNH self.resample_cardinal (từ Bishop Frame script) có sẵn
        if hasattr(self, 'resample_cardinal'):
            pts = self.resample_cardinal(control_pts, num_samples)
        else:
            # Fallback đơn giản: chỉ dùng control points nếu resampling không có
            pts = control_pts
            
        # 3. Kéo dài đầu/đuôi (Extension)
        # GIẢ ĐỊNH self.extend_polyline có sẵn
        if hasattr(self, 'extend_polyline'):
            ext_len = ext_f + ext_b # Chỉ dùng một tham số tổng hợp cho đơn giản
            pts = self.extend_polyline(pts, ext_len/2.0)
        else:
            # Logic kéo dài thủ công gốc (đã được làm mượt hơn do resampling)
            if ext_b > 0:
                v = pts[0] - pts[1]
                nm = np.linalg.norm(v)
                if nm > 0: pts = np.insert(pts, 0, pts[0] + (v/nm)*ext_b, axis=0)
            if ext_f > 0:
                v = pts[-1] - pts[-2]
                nm = np.linalg.norm(v)
                if nm > 0: pts = np.append(pts, [pts[-1] + (v/nm)*ext_f], axis=0)

        # 4. Tính toán Tiếp tuyến (Tangent)
        # GIẢ ĐỊNH self.tangents (từ Bishop Frame script) có sẵn
        if hasattr(self, 'tangents'):
            Tangents = self.tangents(pts)
        else:
            # Fallback: Tính tangents thô
            Tangents = np.zeros_like(pts)
            for i in range(len(pts)):
                if i == 0: v = pts[1] - pts[0]
                elif i == len(pts)-1: v = pts[-1] - pts[-2]
                else: v = pts[i+1] - pts[i-1]
                nm = np.linalg.norm(v)
                Tangents[i] = v / nm if nm > 0 else v


        # 5. Xây dựng PolyData từ các điểm (Ribbon Construction)
        points_vtk = vtk.vtkPoints()
        cells_vtk = vtk.vtkCellArray()

        for i in range(len(pts)):
            curr_p = pts[i]
            tangent = Tangents[i]
            
            # Logic chọn Up vector (giữ nguyên để tránh lỗi singularity)
            if abs(tangent[2]) < 0.9:
                up = np.array([0.0, 0.0, 1.0])
            else:
                up = np.array([0.0, 1.0, 0.0])

            # Base normal (vuông góc với tangent)
            base_cut = np.cross(up, tangent)
            nm_bc = np.linalg.norm(base_cut)
            if nm_bc == 0: continue
            base_cut /= nm_bc

            # Quay base_cut (yaw) quanh tangent
            final_dir = self.rotate_vector(base_cut, tangent, angle)

            # Đảm bảo hướng cắt luôn hướng về trung tâm (Lặp lại logic gốc)
            vec_to_origin = -curr_p
            if np.dot(final_dir, vec_to_origin) < 0: 
                final_dir = -final_dir # Đảo hướng nếu cần

            # Tọa độ điểm IN và OUT
            p_in = curr_p + final_dir * depth
            p_out = curr_p - final_dir * out
            
            # Thêm điểm
            idx_in = points_vtk.InsertNextPoint(p_in)
            idx_out = points_vtk.InsertNextPoint(p_out)
            
            # Nối tam giác (Tessellation)
            if i > 0:
                # Lấy index của điểm trước đó
                idx_in_prev = idx_in - 2
                idx_out_prev = idx_out - 2
                
                # Tam giác 1
                tri1 = vtk.vtkTriangle()
                tri1.GetPointIds().SetId(0, idx_in_prev)
                tri1.GetPointIds().SetId(1, idx_out_prev)
                tri1.GetPointIds().SetId(2, idx_out)
                cells_vtk.InsertNextCell(tri1)
                
                # Tam giác 2
                tri2 = vtk.vtkTriangle()
                tri2.GetPointIds().SetId(0, idx_in_prev)
                tri2.GetPointIds().SetId(1, idx_out)
                tri2.GetPointIds().SetId(2, idx_in)
                cells_vtk.InsertNextCell(tri2)

        # 6. Hoàn thiện PolyData và tính toán Normals
        poly = vtk.vtkPolyData()
        poly.SetPoints(points_vtk)
        poly.SetPolys(cells_vtk)
        
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(poly)
        normals.SetFeatureAngle(60.0)
        normals.Update()
        
        return normals.GetOutput()
    
    
    def unit(self, v):
        v = np.asarray(v, float)
        n = np.linalg.norm(v)
        return v/n if n > 1e-8 else v

    def tangents(self, P):
        T = np.zeros_like(P)
        for i in range(len(P)):
            if i == 0: v = P[1] - P[0]
            elif i == len(P)-1: v = P[-1] - P[-2]
            else: v = P[i+1] - P[i-1]
            T[i] = self.unit(v)
        return T

    def resample_cardinal(self, P, M):
        """Lấy mẫu lại đường cong bằng Cardinal Spline."""
        xs, ys, zs = vtk.vtkCardinalSpline(), vtk.vtkCardinalSpline(), vtk.vtkCardinalSpline()
        for i,(x,y,z) in enumerate(P):
            xs.AddPoint(i,x); ys.AddPoint(i,y); zs.AddPoint(i,z)
        N = len(P)
        out = np.zeros((M,3), float)
        for j in range(M):
            t = j*(N-1)/float(max(M-1,1))
            out[j] = [xs.Evaluate(t), ys.Evaluate(t), zs.Evaluate(t)]
        return out

    def extend_polyline(self, P, ext):
        """Mở rộng đường đa tuyến (polyline) ở hai đầu."""
        if ext <= 0: return P
        T = self.tangents(P)
        return np.vstack([
            P[0]  - T[0]*ext,
            P,
            P[-1] + T[-1]*ext
        ])
    
    def bishop_frame(self, P, O, N):
        """Tính toán hệ trục Bishop (T, U, V) dọc theo đường cong P, đảm bảo U hướng lateral."""
        T = self.tangents(P)
        U = np.zeros_like(T)
        V = np.zeros_like(T)
        up = np.array([0,0,1.0])

        for i in range(len(P)):
            w = P[i] - O             # từ MSP tới điểm trên OC
            side = np.sign(np.dot(w, N)) or 1.0 
            L = side * N             # Lateral sơ bộ (hướng ra khỏi MSP)

            u = L - T[i]*np.dot(L, T[i])
            if np.linalg.norm(u) < 1e-6:
                u = np.cross(up, T[i]) 
            u = self.unit(u)

            if np.dot(u, w) < 0:
                u = -u

            U[i] = u
            V[i] = self.unit(np.cross(T[i], U[i]))
        return U, V, T

    def build_sheet_polydata(self, P, Uo, lat_mm, med_mm):
        """Tạo vtkPolyData của tường cong (sheet) dựa trên P và hướng Uo."""
        N = len(P)
        pts  = vtk.vtkPoints()
        polys= vtk.vtkCellArray()

        for p in (P + Uo*lat_mm):
            pts.InsertNextPoint(*map(float,p))
        for p in (P - Uo*med_mm):
            pts.InsertNextPoint(*map(float,p))

        def tri(a,b,c):
            t = vtk.vtkTriangle()
            t.GetPointIds().SetId(0,a); t.GetPointIds().SetId(1,b); t.GetPointIds().SetId(2,c)
            polys.InsertNextCell(t)

        for i in range(N-1):
            a0,a1 = i, i+1         
            b0,b1 = i+N, i+1+N     
            tri(a0,b0,b1); tri(a0,b1,a1)

        pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(polys)
        return self.ensure_normals(pd)

    def mirror_polydata_about_plane(self, pd, O, N):
        """Phản chiếu PolyData qua mặt phẳng (O, N)."""
        n = N.reshape(3,1); R = np.eye(3) - 2.0*(n @ n.T)
        t = O - R @ O; M = np.eye(4); M[:3,:3] = R; M[:3,3]  = t
        mat = vtk.vtkMatrix4x4()
        for r in range(4):
            for c in range(4): mat.SetElement(r,c,float(M[r,c]))
        tf  = vtk.vtkTransform(); tf.SetMatrix(mat)
        flt = vtk.vtkTransformPolyDataFilter(); flt.SetTransform(tf)
        flt.SetInputData(pd); flt.Update()
        out = vtk.vtkPolyData(); out.DeepCopy(flt.GetOutput())
        return self.ensure_normals(out)

    def clip_by_plane(self, pd, O, N, keep_sign):
        """Cắt PolyData bởi mặt phẳng (O, N). keep_sign > 0: giữ phía cùng phía với N."""
        plane = vtk.vtkPlane(); plane.SetOrigin(*map(float,O)); plane.SetNormal(*map(float,N))
        clip = vtk.vtkClipPolyData(); clip.SetInputData(pd); clip.SetClipFunction(plane); clip.SetValue(0.0)
        if keep_sign > 0: clip.InsideOutOff()
        else: clip.InsideOutOn()
        clip.Update()
        return self.ensure_normals(clip.GetOutput())
    
    def create_mirror_curve_node(self, src_node, name):
        if not src_node or self.msp_origin is None or self.msp_normal is None: return None
        dest_node = slicer.mrmlScene.GetFirstNodeByName(name)
        if not dest_node:
            dest_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsCurveNode", name)
        else:
            dest_node.RemoveAllControlPoints()

        plane_normal = np.array(self.msp_normal, dtype=float)
        plane_normal = plane_normal / np.linalg.norm(plane_normal)
        plane_origin = np.array(self.msp_origin, dtype=float)
        n = src_node.GetNumberOfDefinedControlPoints()

        for i in range(n):
            p_old = [0,0,0]
            src_node.GetNthControlPointPosition(i, p_old)
            p_old = np.array(p_old, dtype=float)
            v = p_old - plane_origin
            dist = np.dot(v, plane_normal)
            p_new = p_old - 2.0 * dist * plane_normal
            dest_node.AddControlPoint(p_new.tolist())
        return dest_node

    def get_pos(self, node):
        if not node or node.GetNumberOfControlPoints() == 0: return None
        pos = [0, 0, 0]
        node.GetNthControlPointPositionWorld(0, pos)
        return np.array(pos)


    def pick_gonion_outer(self, Me, Co, mand_pd, O_msp, N_msp, side_label, target_angle_deg, ratio=2.0):
        # 1. Tính toán khoảng cách lý thuyết
        Y = np.linalg.norm(Co - Me)
        alpha_rad = math.radians(target_angle_deg)
        denom = 1.0 + ratio**2 - 2.0 * ratio * math.cos(alpha_rad)
        
        if denom <= 1e-12: raise ValueError("Thông số góc không hợp lệ.")
        
        d = Y / math.sqrt(denom) # Khoảng cách Co - Go
        L = ratio * d            # Khoảng cách Me - Go

        # 2. Tìm tâm và vector của đường tròn giao tuyến 2 mặt cầu
        u = (Me - Co) / Y 
        a = (d**2 - L**2 + Y**2) / (2.0 * Y)
        P0 = Co + a * u

        # 3. Cắt xương bằng mặt phẳng (P0, normal=u)
        plane = vtk.vtkPlane()
        plane.SetOrigin(P0)
        plane.SetNormal(u)

        cutter = vtk.vtkCutter()
        cutter.SetInputData(mand_pd)
        cutter.SetCutFunction(plane)
        cutter.Update()
        
        cutPoly = cutter.GetOutput()
        if cutPoly.GetNumberOfPoints() == 0:
            raise ValueError(f"[{side_label}] Không tìm thấy giao điểm trên xương (vết cắt rỗng).")

        # 4. Lấy tất cả các điểm trên vết cắt (Candidates)
        points = vtk.util.numpy_support.vtk_to_numpy(cutPoly.GetPoints().GetData())
        
        # Vector từ các điểm candidate đến Co và Me
        vec_P_Co = Co - points  # (N, 3)
        vec_P_Me = Me - points  # (N, 3)

        # Tính độ dài các vector (Norm)
        norm_P_Co = np.linalg.norm(vec_P_Co, axis=1)
        norm_P_Me = np.linalg.norm(vec_P_Me, axis=1)

        mask_valid = (norm_P_Co > 1e-6) & (norm_P_Me > 1e-6)
        points = points[mask_valid]
        vec_P_Co = vec_P_Co[mask_valid]
        vec_P_Me = vec_P_Me[mask_valid]
        norm_P_Co = norm_P_Co[mask_valid]
        norm_P_Me = norm_P_Me[mask_valid]

        dot_product = np.sum(vec_P_Co * vec_P_Me, axis=1)
        cosine_angles = dot_product / (norm_P_Co * norm_P_Me)
        cosine_angles = np.clip(cosine_angles, -1.0, 1.0)
        angles_deg = np.degrees(np.arccos(cosine_angles))

        # 5. Chọn điểm tối ưu (Score function)
        angle_diff = np.abs(angles_deg - target_angle_deg)
        
        lat_dist = np.dot(points - O_msp, N_msp)
        side_sign_Co = np.sign(np.dot(Co - O_msp, N_msp))
        wrong_side_penalty = np.where(np.sign(lat_dist) != side_sign_Co, 1000.0, 0.0)

        z_values = points[:, 2]
        z_score = (z_values - np.min(z_values)) / (np.ptp(z_values) + 1e-6) * 5.0 
        
        final_scores = angle_diff + wrong_side_penalty + z_score
        best_idx = np.argmin(final_scores)
        
        return points[best_idx]

    def run_step_3_calculate_go(self,target_angle_deg=127.0):
        if self.msp_origin is None: raise ValueError("Chưa có MSP. Chạy B1 trước.")
        
        pMe = self.get_pos(slicer.util.getNode('Me'))
        pCoR = self.get_pos(slicer.util.getNode('CoR'))
        pCoL = self.get_pos(slicer.util.getNode('CoL'))
        pGoR_old = self.get_pos(slicer.util.getNode('GoR'))
        pGoL_old = self.get_pos(slicer.util.getNode('GoL'))




        mand_pd = self.ensure_normals(slicer.util.getNode('Mandible').GetPolyData())
        results = {}

        if pCoR is not None:
            try:
                goR = self.pick_gonion_outer(pMe, pCoR, mand_pd, self.msp_origin, self.msp_normal, 'R', target_angle_deg, ratio=2.0)
                self.create_fiducial_node("GoR_N", goR, color=(0,1,0))
                results['R'] = self.calculate_angle_deg(pCoR, goR, pMe)
                self.create_angle_node("Angle_CoR_GoR_Me", pCoR, pGoR_old, pMe)
                self.create_angle_node("Angle_CoR_GoR_N_Me", pCoR, goR, pMe)
            except Exception as e: print(f"Lỗi GoR: {e}")

        if pCoL is not None:
            try:
                goL = self.pick_gonion_outer(pMe, pCoL, mand_pd, self.msp_origin, self.msp_normal, 'L', target_angle_deg, ratio=2.0)
                self.create_fiducial_node("GoL_N", goL, color=(0,1,0))
                results['L'] = self.calculate_angle_deg(pCoL, goL, pMe)
                self.create_angle_node("Angle_CoL_GoL_Me", pCoL, pGoL_old, pMe)
                self.create_angle_node("Angle_CoL_GoL_N_Me", pCoL, goL, pMe)
            except Exception as e: print(f"Lỗi GoL: {e}")

        return results

    # --------------------------------------------------------------------------
    # BƯỚC 3: TẠO SHEET RIBBON & CẮT V-LINE
    # --------------------------------------------------------------------------
    def run_step_4_create_sheets_and_cut(self, mandibleNode, yaw_degrees=45.0, curveNode=None):
        
        # NOTE: Logic này đã thay thế hoàn toàn logic tạo ribbon đối xứng cũ.
        
        if self.msp_origin is None or self.msp_normal is None:
            raise ValueError("Thiếu dữ liệu MSP. Hãy chạy lại bước 1.")

        if not curveNode:
            raise ValueError("Chưa chọn đường cong (Curve).")

        print("\n=== BẮT ĐẦU TẠO SHEET (BISHOP FRAME) & CẮT XƯƠNG ===")

        # ==== CẤU HÌNH BISHOP FRAME ====
        SAMPLES     = 420
        LAT_OUT_MM  = 20.0      # Độ rộng ribbon phía ngoài (Lateral Out)
        MED_IN_MM   = 35.0      # Độ rộng ribbon phía trong/cắt xương (Medial In)
        END_EXT_MM  = 50.0      # Kéo dài đầu/đuôi OC

        O_msp = self.msp_origin
        N_msp = self.msp_normal
        
        # 1. Chuẩn bị đường cong (Resample + Extend)
        P0 = []
        n = curveNode.GetNumberOfControlPoints()
        if n < 2: raise ValueError("OC cần ≥2 điểm.")
        for i in range(n):
            p = [0.0]*3
            curveNode.GetNthControlPointPosition(i, p) 
            P0.append(np.array(p))
        P0 = np.array(P0)

        P = self.resample_cardinal(P0, SAMPLES)
        P = self.extend_polyline(P, END_EXT_MM)
        
        # 2. Bishop frame + hướng nghiêng
        U, V, T = self.bishop_frame(P, O_msp, N_msp)
        
        # NGHIÊNG TỪ NGOÀI → VỀ PHÍA TRONG
        yaw = -math.radians(yaw_degrees) 
        Uo  = np.cos(yaw)*U + np.sin(yaw)*V

        # 3. Tạo Sheet (tường) đầy đủ, chưa bị cắt bởi MSP
        sheet_full_pd = self.build_sheet_polydata(P, Uo, LAT_OUT_MM, MED_IN_MM)
        

        # 4. Xác định hướng cắt theo MSP (Giữ lại phần sheet ở cùng phía với đường cong)
        med_d     = float(np.median(np.dot(P - O_msp.reshape(1,3), N_msp)))
        keep_sign = +1 if med_d >= 0 else -1

        # 5. TẠO RIBBON PHẢI (cut_1) - CLIP SHEET ĐẦY ĐỦ
        ribbon_R_pd = None
        try:
            print("Đang tạo Sheet Phải (cut_1) bằng cách Clip...")
            # Giữ lại phần sheet_full_pd nằm ở cùng phía với đường cong (Phải/Gốc)
            ribbon_R_pd = self.clip_by_plane(sheet_full_pd, O_msp, N_msp, keep_sign=keep_sign)
            ribbon_R_pd = self.ensure_normals(ribbon_R_pd)
            
            self.create_model_node("Ribbon_R", ribbon_R_pd, color=(0.2, 0.8, 1.0), opacity=1)
            self.create_model_node("cut_1", ribbon_R_pd, visibility=False)
        except Exception as e:
            print(f"Lỗi tạo cut_1: {e}")
            ribbon_R_pd = None
            

        # 6. TẠO RIBBON TRÁI (cut_2) - MIRROR/CLIP
        ribbon_L_pd = None
        if ribbon_R_pd:
            try:
                print("Đang tạo Sheet Trái (cut_2 - Mirror)...")
                # Gương cut_1 qua MSP
                cut2_raw = self.mirror_polydata_about_plane(ribbon_R_pd, O_msp, N_msp)
                
                # Clip lại lần nữa để đảm bảo cắt sạch (Giữ lại phía ngược lại)
                ribbon_L_pd = self.clip_by_plane(cut2_raw, O_msp, N_msp, keep_sign=-keep_sign)
                ribbon_L_pd = self.ensure_normals(ribbon_L_pd)
                
                self.create_model_node("Ribbon_L", ribbon_L_pd, color=(1.0, 0.6, 0.6), opacity=1)
                self.create_model_node("cut_2", ribbon_L_pd, visibility=False)
            except Exception as e:
                print(f"Lỗi tạo cut_2: {e}")
                ribbon_L_pd = None


        # 7. TIẾN HÀNH CẮT BOOLEAN
        # Ưu tiên Mandible_Body (sau khi đã cắt genio)
        mand_node_to_cut = mandibleNode 
        try:
            temp_node = slicer.util.getNode("Mandible_Body")
            if temp_node:
                mand_node_to_cut = temp_node
                print("Đang cắt V-Line trên 'Mandible_Body' (sau Genioplasty)...")
            else:
                print("Không tìm thấy 'Mandible_Body'. Đang cắt trên xương gốc.")
        except slicer.util.MRMLNodeNotFoundException:
            print("Không tìm thấy 'Mandible_Body'. Đang cắt trên xương gốc.")
            pass

        mand_pd = self.ensure_normals(mand_node_to_cut.GetPolyData())
        bone_R_pd = None
        bone_L_pd = None
        temp_mand_after_right = mand_pd  # Giữ mô hình gốc nếu không cắt phải
        temp_mand_after_left = mand_pd   # Giữ mô hình gốc nếu không cắt trái
        mand_final = mand_pd

        # --- 1. CẮT BÊN PHẢI (TRÊN MÔ HÌNH GỐC) ---
        if ribbon_R_pd:
            try:
                print("Đang cắt bên phải trên mô hình gốc...")
                # Lấy phần đã cắt (bone_R_pd) và phần còn lại (Trung tâm + Trái)
                bone_R_pd, temp_mand_after_right = self.split_bone_by_sheet(
                    mand_pd, ribbon_R_pd, self.msp_origin, self.msp_normal
                )
            except Exception as e:
                print("Lỗi cắt phải:", e)

        # --- 2. CẮT BÊN TRÁI (TRÊN MÔ HÌNH GỐC) ---
        if ribbon_L_pd:
            try:
                print("Đang cắt bên trái trên mô hình gốc...")
                # Lấy phần đã cắt (bone_L_pd) và phần còn lại (Trung tâm + Phải)
                # CHÚ Ý: Vẫn dùng mand_pd (Mô hình gốc)
                bone_L_pd, temp_mand_after_left = self.split_bone_by_sheet(
                    mand_pd, ribbon_L_pd, self.msp_origin, self.msp_normal
                )
            except Exception as e:
                print("Lỗi cắt trái:", e)


        if bone_R_pd:
            print("Tạo node cho phần xương hàm bên phải (bone_R_pd)")
            try:
                # Tùy chỉnh màu sắc để dễ phân biệt, ví dụ: Đỏ
                self.create_model_node("bone_R_pd", bone_R_pd, color=(1.0, 0.0, 0.0))
                self.create_model_node("temp_mand_after_right", temp_mand_after_right, color=(1.0, 0.0, 0.0))
            except Exception as e:
                print("Lỗi tạo node phải:", e)

        # 4.2. Node Xương Hàm Bên Trái đã cắt
        if bone_L_pd:
            print("Tạo node cho phần xương hàm bên trái (bone_L_pd)")
            try:
                # Tùy chỉnh màu sắc, ví dụ: Xanh lam
                self.create_model_node("bone_L_pd", bone_L_pd, color=(0.0, 0.0, 1.0))
                self.create_model_node("temp_mand_after_left", temp_mand_after_left, color=(1.0, 0.0, 0.0))
            except Exception as e:
                print("Lỗi tạo node trái:", e)

        # --- 3. KẾT HỢP (LẤY PHẦN TRUNG TÂM) ---

        # if ribbon_R_pd and ribbon_L_pd:
        #     # Nếu có cả hai ribbon, dùng phép GIAO (Intersection)
        #     print("Thực hiện phép giao (Intersection) để lấy phần trung tâm...")
            
        #     # Bạn cần một hàm để thực hiện phép GIAO (Boolean Intersection)
        #     try:
        #         # Phần giao của (Trung tâm + Trái) và (Trung tâm + Phải) chính là Phần Trung Tâm
        #         mand_final = self.intersect_polydata(temp_mand_after_right, temp_mand_after_left)
        #     except Exception as e:
        #         print("Lỗi phép giao (Intersection):", e)
        #         # Xử lý lỗi (ví dụ: dùng tạm kết quả sau cắt phải)
        #         mand_final = temp_mand_after_right         
        # elif ribbon_R_pd:
        #     # Chỉ cắt phải, phần trung tâm là phần còn lại sau cắt phải
        #     mand_final = temp_mand_after_right
        # elif ribbon_L_pd:
        #     # Chỉ cắt trái, phần trung tâm là phần còn lại sau cắt trái
        #     mand_final = temp_mand_after_left    
        # else:
        #     # Không có ribbon nào
        #     mand_final = mand_pd

        # Kết quả:
        # bone_R_pd: Phần xương bên phải (đã cắt)
        # bone_L_pd: Phần xương bên trái (đã cắt)
        # mand_final: Phần xương trung tâm (còn lại)

        
        def make_watertight_solid(poly, spacing=0.5, smooth_iterations=100):
            """
            Làm kín polydata hở thành khối đặc (watertight) + làm mịn mạnh.
            """

            if poly is None:
                return None

            # -----------------------------
            # 1. Raster hóa poly thành ảnh
            # -----------------------------
            bounds = [0]*6
            poly.GetBounds(bounds)

            img = vtk.vtkImageData()
            img.SetSpacing(spacing, spacing, spacing)
            img.SetDimensions(
                int((bounds[1]-bounds[0])/spacing)+10,
                int((bounds[3]-bounds[2])/spacing)+10,
                int((bounds[5]-bounds[4])/spacing)+10
            )
            img.SetOrigin(bounds[0]-spacing*5, bounds[2]-spacing*5, bounds[4]-spacing*5)
            img.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)

            # fill = 0
            img.GetPointData().GetScalars().Fill(0)

            # Raster polydata vào ảnh
            pol2stenc = vtk.vtkPolyDataToImageStencil()
            pol2stenc.SetInputData(poly)
            pol2stenc.SetOutputOrigin(img.GetOrigin())
            pol2stenc.SetOutputSpacing(img.GetSpacing())
            pol2stenc.SetOutputWholeExtent(img.GetExtent())
            pol2stenc.Update()

            stenc = vtk.vtkImageStencil()
            stenc.SetInputData(img)
            stenc.SetStencilConnection(pol2stenc.GetOutputPort())
            stenc.ReverseStencilOn()
            stenc.SetBackgroundValue(1)
            stenc.Update()

            # ----------------------------------------
            # 2. Marching Cubes → mesh kín
            # ----------------------------------------
            mc = vtk.vtkMarchingCubes()
            mc.SetInputData(stenc.GetOutput())
            mc.SetValue(0, 0.5)
            mc.Update()
            solid = mc.GetOutput()

            # ----------------------------------------
            # 3. Clean để tránh lỗi topology
            # ----------------------------------------
            clean = vtk.vtkCleanPolyData()
            clean.SetInputData(solid)
            clean.PointMergingOn()
            clean.Update()
            solid = clean.GetOutput()

            # ----------------------------------------
            # 4. Decimate (giảm tam giác nhưng giữ shape)
            # ----------------------------------------
            deci = vtk.vtkDecimatePro()
            deci.SetInputData(solid)
            deci.SetTargetReduction(0.3)  # giảm 30%
            deci.PreserveTopologyOn()     # không làm thủng mesh
            deci.Update()
            solid = deci.GetOutput()

            # ----------------------------------------
            # 5. Smooth mạnh bằng WindowedSinc
            # ----------------------------------------
            smooth = vtk.vtkWindowedSincPolyDataFilter()
            smooth.SetInputData(solid)
            smooth.SetNumberOfIterations(smooth_iterations)
            smooth.SetPassBand(0.01)      # mượt mạnh
            smooth.FeatureEdgeSmoothingOff()
            smooth.BoundarySmoothingOn()
            smooth.NonManifoldSmoothingOn()
            smooth.NormalizeCoordinatesOn()
            smooth.Update()

            return smooth.GetOutput()

    
        bone_R_pd = make_watertight_solid(bone_R_pd)
        bone_L_pd = make_watertight_solid(bone_L_pd)

        # 9. TẠO NODE TRONG SCENE
        if bone_R_pd:
            self.create_model_node("bone_1", bone_R_pd, color=(1.0, 0.9, 0.5), opacity=1)

        if bone_L_pd:
            self.create_model_node("bone_2", bone_L_pd, color=(1.0, 0.9, 0.5), opacity=1)

        # if mand_final:
        #     self.create_model_node("mandible_final", mand_final, color=(0.9, 0.9, 0.9), opacity=1.0)
            
        print("=== KẾT THÚC BƯỚC 3 ===")
   # --------------------------------------------------------------------------
    # BƯỚC 3b: GENIOPLASTY - CẮT NGANG & TRƯỢT CẰM
    # --------------------------------------------------------------------------

    def flip_polydata(self, poly):
        """Lật úp polydata bằng FlipAlongAxis."""
        tf = vtk.vtkTransform()
        tf.Scale(1, -1, 1)   # lật theo trục Y (theo Slicer)

        tfF = vtk.vtkTransformPolyDataFilter()
        tfF.SetInputData(poly)
        tfF.SetTransform(tf)
        tfF.Update()

        # Fix normals
        n = vtk.vtkPolyDataNormals()
        n.SetInputData(tfF.GetOutput())
        n.AutoOrientNormalsOn()
        n.ConsistencyOn()
        n.SplittingOff()
        n.ComputePointNormalsOn()
        n.Update()

        return n.GetOutput()

    def init_genio_plane(self, meNode=None):
        """
        Tạo mặt phẳng cắt ngang (Horizontal Osteotomy) phía trên điểm Me.
        """
        planeName = "Genio_Cut_Plane"
        
        # 1. Xác định vị trí tâm mặt cắt
        center = [0, 0, 0]
        if meNode:
            # Lấy toạ độ điểm Me
            meNode.GetNthControlPointPositionWorld(0, center)
            
            # --- TÙY CHỈNH VỊ TRÍ MẶC ĐỊNH ---
            # Dịch lên trên điểm Me khoảng 12mm (để giữ lại phần chóp cằm)
            # Dịch ra sau 5mm để mặt phẳng nằm giữa xương
            center[2] += 12.0  # Superior (Lên trên)
            center[1] += 5.0   # Posterior (Ra sau)
        else:
            # Vị trí fallback nếu chưa chọn điểm Me
            center = [0, -60, -50]

        # 2. Xác định hướng mặt cắt (Pháp tuyến)
        # Để cắt kiểu trượt (Sliding), mặt phẳng thường hơi nghiêng: 
        # Thấp ở phía trước, cao ở phía sau (hoặc gần như nằm ngang).
        # Normal vector (x, y, z) = (0, -0.3, 1.0) tạo góc nghiêng nhẹ đẹp.
        normal = [0.0, -0.3, 1.0] 
        
        # Chuẩn hóa vector
        norm_len = np.linalg.norm(normal)
        normal = [n/norm_len for n in normal]

        # 3. Tạo Node Mặt phẳng để bạn chỉnh sửa
        self.create_markups_plane(planeName, center, normal, size=(60, 50))
        
        print(f"✅ Đã tạo mặt phẳng '{planeName}'. Hãy xoay chỉnh trong 3D View để đường cắt nằm dưới chân răng.")
        slicer.util.selectModule("Markups")

    def create_cut_plane_sheet(self, center, normal, size=80.0, thickness=1.0):
        """
        Tạo một vtkPolyData là một tấm phẳng hoặc hộp mỏng để làm sheet cắt.
        center: [x,y,z]
        normal: [nx,ny,nz]
        size: bán kính cạnh
        thickness: độ dày tấm (quan trọng để boolean ổn định)
        """
        center = np.array(center, dtype=float)
        normal = np.array(normal, dtype=float)
        n = normal / np.linalg.norm(normal)

        # tạo 2 vector vuông góc
        arbitrary = np.array([1.0, 0.0, 0.0])
        if abs(np.dot(arbitrary, n)) > 0.9:
            arbitrary = np.array([0.0, 1.0, 0.0])

        v1 = np.cross(n, arbitrary)
        v1 /= np.linalg.norm(v1)

        v2 = np.cross(n, v1)
        v2 /= np.linalg.norm(v2)

        half = size
        # 4 điểm mặt trên
        p0 = center + v1*half + v2*half
        p1 = center - v1*half + v2*half
        p2 = center - v1*half - v2*half
        p3 = center + v1*half - v2*half

        # offset 2 mặt theo thickness
        t = thickness / 2.0
        p0a = p0 + n*t
        p1a = p1 + n*t
        p2a = p2 + n*t
        p3a = p3 + n*t

        p0b = p0 - n*t
        p1b = p1 - n*t
        p2b = p2 - n*t
        p3b = p3 - n*t

        points = vtk.vtkPoints()
        for p in (p0a, p1a, p2a, p3a, p0b, p1b, p2b, p3b):
            points.InsertNextPoint(p)

        faces = vtk.vtkCellArray()
        quads = [
            (0,1,2,3),  # mặt trên
            (4,5,6,7),  # mặt dưới
            (0,1,5,4),
            (1,2,6,5),
            (2,3,7,6),
            (3,0,4,7),
        ]

        for f in quads:
            faces.InsertNextCell(4)
            for idx in f:
                faces.InsertCellPoint(idx)

        pd = vtk.vtkPolyData()
        pd.SetPoints(points)
        pd.SetPolys(faces)

        return pd



    def run_genioplasty_cut(self, boneNode, plane_name="Genio_Cut_Plane", nodeMe=None):
        """
        Thực hiện cắt rời cằm, đóng nắp và gắn vào thanh trượt.
        """
        # 1. KIỂM TRA ĐẦU VÀO
        if not boneNode:
            raise ValueError("Chưa chọn xương hàm (boneNode is None)!")
        
        try:
            planeNode = slicer.util.getNode(plane_name)
        except slicer.util.MRMLNodeNotFoundException:
            # Nếu không tìm thấy plane, thử tạo mặc định hoặc báo lỗi
            raise ValueError(f"Chưa có mặt phẳng cắt '{plane_name}'. Hãy chạy B2.1 trước!")

        print(f"🔪 Đang cắt '{boneNode.GetName()}' theo mặt phẳng '{plane_name}'...")

        # 2. ẨN CÁC PHẦN THỪA (RÁC TỪ CÁC BƯỚC TRƯỚC)
        for trash in ["bone_1", "bone_2", "Ribbon_R", "Ribbon_L", "cut_1", "cut_2"]:
            try:
                n = slicer.util.getNode(trash)
                if n: n.GetDisplayNode().SetVisibility(False)
            except: pass

        # 3. LẤY THÔNG SỐ MẶT PHẲNG
        planeNormal = [0.0]*3; planeOrigin = [0.0]*3
        planeNode.GetNormalWorld(planeNormal)
        planeNode.GetOriginWorld(planeOrigin)

        # Tạo 2 mặt phẳng đối nhau để cắt lấy 2 phần
        planeUpper = vtk.vtkPlane()
        planeUpper.SetNormal(planeNormal); planeUpper.SetOrigin(planeOrigin)
        
        planeLower = vtk.vtkPlane()
        planeLower.SetNormal([-n for n in planeNormal]); planeLower.SetOrigin(planeOrigin)

        planesBody = vtk.vtkPlaneCollection(); planesBody.AddItem(planeUpper)
        planesChin = vtk.vtkPlaneCollection(); planesChin.AddItem(planeLower)

        # 4. XỬ LÝ LƯỚI (Triangulate & Normals)
        triFilter = vtk.vtkTriangleFilter()
        triFilter.SetInputData(boneNode.GetPolyData())
        triFilter.Update()

        normFilter = vtk.vtkPolyDataNormals()
        normFilter.SetInputData(triFilter.GetOutput())
        normFilter.AutoOrientNormalsOn(); normFilter.ConsistencyOn(); normFilter.SplittingOff()
        normFilter.Update()
        cleanInput = normFilter.GetOutput()

        # 5. HÀM CẮT & ĐÓNG NẮP (Cut & Cap)
        def perform_cut(poly, planes):
            clipper = vtk.vtkClipClosedSurface()
            clipper.SetInputData(poly)
            clipper.SetClippingPlanes(planes)
            clipper.SetGenerateFaces(True) # Tạo nắp đóng kín lỗ hổng
            clipper.SetScalarModeToLabels()
            clipper.Update()
            return clipper.GetOutput()
        
        def extract_largest_region(poly):
            conn = vtk.vtkConnectivityFilter()
            conn.SetInputData(poly)
            conn.SetExtractionModeToLargestRegion()
            conn.Update()
            return conn.GetOutput()

        bodyPoly_raw = perform_cut(cleanInput, planesBody)
        chinPoly_raw = perform_cut(cleanInput, planesChin)

        # Lấy mảnh lớn nhất
        bodyPoly = extract_largest_region(bodyPoly_raw)
        chinPoly = extract_largest_region(chinPoly_raw)

        # Kiểm tra lỗi cắt hụt
        if chinPoly.GetNumberOfPoints() == 0:
            raise ValueError("Không cắt được mảnh cằm nào! Hãy di chuyển mặt phẳng cắt xuống thấp hơn.")

        # 6. HIỂN THỊ KẾT QUẢ
        boneNode.GetDisplayNode().SetVisibility(False)
        planeNode.GetDisplayNode().SetVisibility(False)

        # Node Thân hàm (Cố định)
        bodyNode = self.create_model_node("Mandible_Body", bodyPoly, color=(0.95, 0.9, 0.8))
        bodyNode.GetDisplayNode().SetBackfaceCulling(0)

        # Node Cằm (Di động)
        chinNode = self.create_model_node("Chin_Fragment", chinPoly, color=(1.0, 0.6, 0.6))
        chinNode.GetDisplayNode().SetBackfaceCulling(0)

        # 7. TẠO THANH TRƯỢT (SLIDER) & GẮN ĐIỂM ME
        try: slicer.mrmlScene.RemoveNode(slicer.util.getNode("Genio_Slider"))
        except: pass

        transformNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode")
        transformNode.SetName("Genio_Slider")
        transformNode.CreateDefaultDisplayNodes()
        
        # Gắn xương Cằm vào Transform
        chinNode.SetAndObserveTransformNodeID(transformNode.GetID())

        # Gắn điểm Me vào Transform (để điểm chạy theo khi kéo)
        if nodeMe:
            nodeMe.SetAndObserveTransformNodeID(transformNode.GetID())

        # Hiển thị Widget điều khiển
        dn = transformNode.GetDisplayNode()
        if dn: dn.SetEditorVisibility(True)
        
        print("✅ Genioplasty hoàn tất.")
        slicer.util.selectModule("Transforms")
    # --------------------------------------------------------------------------
    # BƯỚC 4: TẠO MÁNG BAND GUIDE
    # --------------------------------------------------------------------------
 

    def run_step_4_create_guides_robust(self, mandibleNode):
        CLEARANCE_MM = 0.2
        SHELL_MM     = 2.0
        GUIDE_HEIGHT = 18.0
        
        if not mandibleNode: raise ValueError("Không tìm thấy model xương gốc.")
            
        if slicer.util.getNodes("cut_1") and slicer.util.getNodes("CoR"):
            self.create_band_guide_on_bone(mandibleNode, "cut_1", "guide_bone_1", "CoR", 
                                           CLEARANCE_MM, SHELL_MM, GUIDE_HEIGHT)
        
        if slicer.util.getNodes("cut_2") and slicer.util.getNodes("CoL"):
            self.create_band_guide_on_bone(mandibleNode, "cut_2", "guide_bone_2", "CoL", 
                                           CLEARANCE_MM, SHELL_MM, GUIDE_HEIGHT)

    def create_band_guide_on_bone(self, boneNode, cutName, guideName, upLandmarkName, 
                                  clearance=0.2, thickness=2.0, height=15.0):
        bonePD = self.ensure_normals(boneNode.GetPolyData())
        cutNode = slicer.util.getNode(cutName)
        cutPD = self.ensure_normals(cutNode.GetPolyData())
        pUp = self.get_pos(slicer.util.getNode(upLandmarkName))
        
        # Bounds Optimization
        bounds = [0]*6; cutPD.GetBounds(bounds)
        margin = height + 10.0
        bounds = [bounds[0]-margin, bounds[1]+margin, bounds[2]-margin, bounds[3]+margin, bounds[4]-margin, bounds[5]+margin]
        
        # Distance & Shell
        impBone = vtk.vtkImplicitPolyDataDistance(); impBone.SetInput(bonePD)
        res = 0.4; dim = [int((bounds[1]-bounds[0])/res), int((bounds[3]-bounds[2])/res), int((bounds[5]-bounds[4])/res)]
        
        sample = vtk.vtkSampleFunction(); sample.SetImplicitFunction(impBone); sample.SetModelBounds(bounds); sample.SetSampleDimensions(dim); sample.ComputeNormalsOff()
        thresh = vtk.vtkImageThreshold(); thresh.SetInputConnection(sample.GetOutputPort())
        thresh.ThresholdBetween(clearance, clearance + thickness); thresh.SetInValue(1); thresh.SetOutValue(0); thresh.SetOutputScalarTypeToUnsignedChar()
        
        mc = vtk.vtkDiscreteMarchingCubes(); mc.SetInputConnection(thresh.GetOutputPort()); mc.SetValue(0, 1); mc.Update()
        smoother = vtk.vtkWindowedSincPolyDataFilter(); smoother.SetInputConnection(mc.GetOutputPort()); smoother.SetNumberOfIterations(10); smoother.NormalizeCoordinatesOn(); smoother.Update()
        shellPD = smoother.GetOutput()
        
        if shellPD.GetNumberOfPoints() == 0: return

        # Clip by Cut Sheet
        impCut = vtk.vtkImplicitPolyDataDistance(); impCut.SetInput(cutPD)
        dist_up = impCut.EvaluateFunction(pUp)
        sign_up = 1.0 if dist_up >= 0 else -1.0
        
        # Clip 1: Giữ phần "Trên"
        clipper1 = vtk.vtkClipPolyData(); clipper1.SetInputData(shellPD); clipper1.SetClipFunction(impCut); clipper1.SetValue(0.0)
        if sign_up > 0: clipper1.InsideOutOn()
        else: clipper1.InsideOutOff()
        clipper1.Update()
        
        # Clip 2: Giới hạn chiều cao
        clipper2 = vtk.vtkClipPolyData(); clipper2.SetInputData(clipper1.GetOutput()); clipper2.SetClipFunction(impCut)
        cut_value = height if sign_up > 0 else -height
        clipper2.SetValue(cut_value)
        if sign_up > 0: clipper2.InsideOutOff()
        else: clipper2.InsideOutOn()
        clipper2.Update()
        bandShell = clipper2.GetOutput()
        
        # Clip 3: Giữ mặt ngoài (Lateral) bằng MSP
        if self.msp_origin is not None:
            planeMSP = vtk.vtkPlane(); planeMSP.SetOrigin(self.msp_origin); planeMSP.SetNormal(self.msp_normal)
            vec_lat = pUp - self.msp_origin
            keep_pos = (np.dot(vec_lat, self.msp_normal) >= 0)
            
            clipper3 = vtk.vtkClipPolyData(); clipper3.SetInputData(bandShell); clipper3.SetClipFunction(planeMSP)
            if keep_pos: clipper3.InsideOutOn()
            else: clipper3.InsideOutOff()
            clipper3.Update()
            finalShell = clipper3.GetOutput()
        else: finalShell = bandShell

        # Clean
        clean = vtk.vtkCleanPolyData(); clean.SetInputData(finalShell); clean.Update()
        conn = vtk.vtkPolyDataConnectivityFilter(); conn.SetInputConnection(clean.GetOutputPort()); conn.SetExtractionModeToLargestRegion(); conn.Update()
        self.create_model_node(guideName, conn.GetOutput(), color=(0.6, 1.0, 0.6), opacity=1.0)

    def mirror_points_array(self, points, plane_org, plane_norm):
        mirrored = []; n = np.array(plane_norm); o = np.array(plane_org)
        for p in points:
            p_arr = np.array(p)
            mirrored.append(p_arr - 2 * np.dot(p_arr - o, n) * n)
        return np.array(mirrored)

    def plane_from_three_points(self, p1, p2, p3):
        n = np.cross(p2-p1, p3-p1); n /= np.linalg.norm(n)
        return (p1+p2+p3)/3.0, n

    def fit_plane_svd(self, points):
        pts = np.array(points); c = np.mean(pts, axis=0)
        _, _, vh = np.linalg.svd(pts - c)
        return c, vh[2, :]

    def create_markups_plane(self, name, o, n, size):
        try: slicer.mrmlScene.RemoveNode(slicer.util.getNode(name))
        except: pass
        p = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsPlaneNode', name)
        p.SetOriginWorld(o); p.SetNormalWorld(n); p.SetSize(*size)

    def mirror_model(self, src, o, n, suffix):
        if not src: return None
        nn = np.array(n).reshape(3,1); oo = np.array(o).reshape(3,1)
        R = np.eye(3) - 2 * np.dot(nn, nn.T); t = 2 * np.dot(nn.T, oo) * nn
        m = vtk.vtkMatrix4x4()
        for r in range(3):
            for c in range(3): m.SetElement(r,c, R[r,c])
            m.SetElement(r, 3, t[r])
        cloned = slicer.mrmlScene.CopyNode(src); cloned.SetName(src.GetName() + suffix)
        trans = vtk.vtkTransform(); trans.SetMatrix(m)
        pdf = vtk.vtkTransformPolyDataFilter(); pdf.SetInputData(cloned.GetPolyData()); pdf.SetTransform(trans); pdf.Update()
        cloned.SetAndObservePolyData(pdf.GetOutput())
        if cloned.GetDisplayNode(): cloned.GetDisplayNode().SetOpacity(0.5); cloned.GetDisplayNode().SetColor(1, 1, 0)
        return cloned

    def ensure_normals(self, pd):
        n=vtk.vtkPolyDataNormals(); n.SetInputData(pd); n.ConsistencyOn(); n.SplittingOff(); n.AutoOrientNormalsOn(); n.Update()
        return n.GetOutput()

    def create_model_node(self, name, pd, color=(1,1,1), opacity=1.0, visibility=True):
        try: slicer.mrmlScene.RemoveNode(slicer.util.getNode(name))
        except: pass
        n = slicer.modules.models.logic().AddModel(pd); n.SetName(name)
        dn = n.GetDisplayNode()
        dn.SetColor(color); dn.SetOpacity(opacity); dn.SetVisibility(visibility); dn.SetBackfaceCulling(0)
        return n

    def split_bone_by_sheet(self, bone, sheet, msp_o, msp_n):
        imp=vtk.vtkImplicitPolyDataDistance(); imp.SetInput(sheet)
        c=vtk.vtkClipPolyData(); c.SetInputData(bone); c.SetClipFunction(imp); c.SetValue(0)
        c.InsideOutOff(); c.Update(); p1=self.keep_largest_island(c.GetOutput())
        c.InsideOutOn(); c.Update(); p2=self.keep_largest_island(c.GetOutput())
        c1=np.array(self.get_center(p1)); c2=np.array(self.get_center(p2))
        if abs(np.dot(c1-msp_o, msp_n)) > abs(np.dot(c2-msp_o, msp_n)): return p1, p2
        return p2, p1

    def keep_largest_island(self, pd):
        c=vtk.vtkPolyDataConnectivityFilter(); c.SetInputData(pd); c.SetExtractionModeToLargestRegion(); c.Update()
        cl=vtk.vtkCleanPolyData(); cl.SetInputConnection(c.GetOutputPort()); cl.Update()
        return cl.GetOutput()

    def get_center(self, pd):
        c=vtk.vtkCenterOfMass(); c.SetInputData(pd); c.Update()
        return c.GetCenter()

    def create_fiducial_node(self, name, pos, color=(1,0,0)):
        try: slicer.mrmlScene.RemoveNode(slicer.util.getNode(name))
        except: pass
        n = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", name)
        n.AddControlPointWorld(vtk.vtkVector3d(pos[0], pos[1], pos[2]))
        n.GetDisplayNode().SetSelectedColor(color)
        
    def create_angle_node(self, name, p1, p2, p3):
        try: slicer.mrmlScene.RemoveNode(slicer.util.getNode(name))
        except: pass
        n = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsAngleNode", name)
        n.AddControlPointWorld(vtk.vtkVector3d(p1)); n.AddControlPointWorld(vtk.vtkVector3d(p2)); n.AddControlPointWorld(vtk.vtkVector3d(p3))
        n.GetDisplayNode().SetColor(1, 1, 0)

    def calculate_angle_deg(self, A, B, C):
        BA = A - B; BC = C - B
        norm1 = np.linalg.norm(BA)
        norm2 = np.linalg.norm(BC)
        if norm1 == 0 or norm2 == 0: return 0.0
        cosine_angle = np.dot(BA, BC) / (norm1 * norm2)
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        return np.degrees(angle)

    def solidify(self, polyData, thickness=1.0):
        extruder = vtk.vtkLinearExtrusionFilter()
        extruder.SetInputData(polyData)
        extruder.SetExtrusionTypeToNormalExtrusion()
        extruder.SetScaleFactor(thickness)
        extruder.Update()
        cleaner = vtk.vtkCleanPolyData()
        cleaner.SetInputData(extruder.GetOutput())
        cleaner.Update()
        return cleaner.GetOutput()
    
    def smooth_model(self, polyData, iterations=30, relaxation=0.2):
        smoothFilter = vtk.vtkSmoothPolyDataFilter()
        smoothFilter.SetInputData(polyData)
        smoothFilter.SetNumberOfIterations(iterations)
        smoothFilter.SetRelaxationFactor(relaxation)
        smoothFilter.FeatureEdgeSmoothingOff()
        smoothFilter.BoundarySmoothingOn()
        smoothFilter.Update()
        cleaner = vtk.vtkCleanPolyData()
        cleaner.SetInputData(smoothFilter.GetOutput())
        cleaner.Update()
        return cleaner.GetOutput()

    def rotate_vector(self, vector, axis, angle_degrees):
        theta = math.radians(angle_degrees)
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        cross_prod = np.cross(axis, vector)
        return vector * cos_t + cross_prod * sin_t
    
    # --------------------------------------------------------------------------
    # BƯỚC MỞ RỘNG: TẠO SUPPORT IN 3D (PILLAR)
    # --------------------------------------------------------------------------
    def create_ribbon_polydata(self, curve_node, angle, depth, out, ext_f, ext_b):
        if not curve_node: return None
        pts = []
        n = curve_node.GetNumberOfControlPoints()
        if n < 2: return None
        for i in range(n):
            p = [0.0]*3
            curve_node.GetNthControlPointPosition(i, p)
            pts.append(np.array(p))

        if ext_b > 0:
            v = pts[0] - pts[1]
            nm = np.linalg.norm(v)
            if nm > 0: pts.insert(0, pts[0] + (v/nm)*ext_b)
        if ext_f > 0:
            v = pts[-1] - pts[-2]
            nm = np.linalg.norm(v)
            if nm > 0: pts.append(pts[-1] + (v/nm)*ext_f)

        points_vtk = vtk.vtkPoints()
        cells_vtk = vtk.vtkCellArray()
        up_ref = np.array([0.0, 0.0, 1.0])

        for i in range(len(pts)):
            curr_p = pts[i]
            if i < len(pts)-1: tangent = pts[i+1] - curr_p
            else: tangent = curr_p - pts[i-1]
            nt = np.linalg.norm(tangent)
            if nt == 0: continue
            tangent /= nt
            
            base_cut = np.cross(tangent, up_ref)
            nb = np.linalg.norm(base_cut)
            if nb > 0: base_cut /= nb
            else: base_cut = np.array([1.0, 0.0, 0.0])

            final_dir = self.rotate_vector(base_cut, tangent, angle)
            
            vec_to_origin = -curr_p
            if np.dot(final_dir, vec_to_origin) < 0: final_dir = -final_dir

            p_in = curr_p + final_dir * depth
            p_out = curr_p - final_dir * out
            
            idx_in = points_vtk.InsertNextPoint(p_in)
            idx_out = points_vtk.InsertNextPoint(p_out)
            
            if i > 0:
                tri1 = vtk.vtkTriangle()
                tri1.GetPointIds().SetId(0, idx_in - 2)
                tri1.GetPointIds().SetId(1, idx_out - 2)
                tri1.GetPointIds().SetId(2, idx_out)
                cells_vtk.InsertNextCell(tri1)
                
                tri2 = vtk.vtkTriangle()
                tri2.GetPointIds().SetId(0, idx_in - 2)
                tri2.GetPointIds().SetId(1, idx_out)
                tri2.GetPointIds().SetId(2, idx_in)
                cells_vtk.InsertNextCell(tri2)

        poly = vtk.vtkPolyData()
        poly.SetPoints(points_vtk)
        poly.SetPolys(cells_vtk)
        
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(poly)
        normals.SetFeatureAngle(60.0)
        normals.Update()
        return normals.GetOutput()

    def create_mirror_curve_node(self, src_node, name):
        if not src_node or self.msp_origin is None or self.msp_normal is None: return None
        dest_node = slicer.mrmlScene.GetFirstNodeByName(name)
        if not dest_node:
            dest_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsCurveNode", name)
        else:
            dest_node.RemoveAllControlPoints()

        plane_normal = np.array(self.msp_normal, dtype=float)
        plane_normal = plane_normal / np.linalg.norm(plane_normal)
        plane_origin = np.array(self.msp_origin, dtype=float)
        n = src_node.GetNumberOfDefinedControlPoints()

        for i in range(n):
            p_old = [0,0,0]
            src_node.GetNthControlPointPosition(i, p_old)
            p_old = np.array(p_old, dtype=float)
            v = p_old - plane_origin
            dist = np.dot(v, plane_normal)
            p_new = p_old - 2.0 * dist * plane_normal
            dest_node.AddControlPoint(p_new.tolist())
        return dest_node
    
    def init_genio_plane_from_curve(self, lCutNode, meNode=None):
        planeName = "Genio_Cut_Plane"
        
        # 1. Lấy vị trí trung tâm của đường cong L-cut
        n = lCutNode.GetNumberOfControlPoints()
        if n < 2:
            raise ValueError("Đường cắt L cần ít nhất 2 điểm.")
        
        # Tính điểm trung bình của các điểm điều khiển trên Curve
        sum_pos = np.array([0.0, 0.0, 0.0])
        for i in range(n):
            p = [0.0]*3
            lCutNode.GetNthControlPointPositionWorld(i, p)
            sum_pos += np.array(p)
        center = sum_pos / n

        # 2. Xác định hướng (Normal)
        # Ta có thể lấy vector tiếp tuyến tại điểm giữa của curve để làm hướng tham chiếu
        # Hoặc dùng hướng mặc định tối ưu cho trượt cằm
        normal = [0.0, -0.3, 1.0] 
        norm_len = np.linalg.norm(normal)
        normal = [n/norm_len for n in normal]

        # 3. Tạo/Cập nhật Plane
        self.create_markups_plane(planeName, center.tolist(), normal, size=(60, 50))
        
        # Chuyển sang module Markups để người dùng thấy thanh điều khiển
        slicer.util.selectModule("Markups")

    def init_genio_plane_from_dual_curves(self, lCutNode, lMirrorNode):
        """
        Tạo mặt phẳng cắt đi qua trung bình của cả hai đường L và L_mirror.
        """
        if not lCutNode or not lMirrorNode:
            raise ValueError("Cần cả hai đường L và L_mirror để tính toán mặt phẳng đối xứng.")

        # 1. Thu thập tất cả các điểm từ cả hai đường
        all_points = []
        
        # Lấy điểm từ đường L
        for i in range(lCutNode.GetNumberOfControlPoints()):
            p = [0, 0, 0]
            lCutNode.GetNthControlPointPositionWorld(i, p)
            all_points.append(p)
            
        # Lấy điểm từ đường L_mirror
        for i in range(lMirrorNode.GetNumberOfControlPoints()):
            p = [0, 0, 0]
            lMirrorNode.GetNthControlPointPositionWorld(i, p)
            all_points.append(p)

        if len(all_points) < 3:
            raise ValueError("Không đủ điểm để tạo mặt phẳng (cần ít nhất 3 điểm).")

        center, normal = self.fit_plane_svd(all_points)

        # 3. Định hướng lại pháp tuyến (Normal) 
        # Đảm bảo mặt phẳng hướng lên trên (trục Z dương) để dễ quan sát
        if normal[2] < 0:
            normal = -normal

        # 4. Tạo hoặc cập nhật mặt phẳng Genio_Cut_Plane
        planeName = "Genio_Cut_Plane"
        self.create_markups_plane(planeName, center.tolist(), normal.tolist(), size=(80, 60))
        
        print(f"✅ Đã tạo mặt phẳng cắt cân đối qua L và L_mirror.")
        slicer.util.selectModule("Markups")

    # --------------------------------------------------------------------------
    # BƯỚC 5: TẠO MÁNG PHẪU THUẬT HIỂN THỊ (VIEW ONLY)
    # --------------------------------------------------------------------------

    def run_step_5_create_fragment_guides(self, params):
        """
        Tạo máng hướng dẫn ôm sát và bao phủ toàn bộ bone_1, bone_2.
        Dựa trên thuật toán Implicit Distance (Offsetting).
        """
        # Danh sách các xương cần tạo máng

        # self.create_selected_curves()
        self.guide_bone_1_export(clearance=0.2, shell=2.0, height=18.0)
        self.guide_bone_2_export(clearance=0.2, shell=2.0, height=18.0)

        print("✅ Đã hoàn thành tạo máng ôm toàn bộ bone_1 và bone_2.")

    def guide_bone_1_export(self, clearance=0.2, shell=2.0, height=18.0):
        # 1. Lấy Nodes
        try:
            bone_node = slicer.util.getNode('bone_1')
            curve_node = slicer.util.getNode('OC_R')
            cut_node = slicer.util.getNode('cut_1')
            ribbon_node = slicer.util.getNode('Ribbon_R')
        except:
            print("❌ Lỗi: Thiếu node bone_1, OC_R hoặc cut_1.")
            return

        print("--- Đang tính toán máng hướng dẫn (Manual Logic) ---")

        # 2. Tạo vỏ Shell (Màng bao quanh xương)
        bone_pd = bone_node.GetPolyData()
        imp_bone = vtk.vtkImplicitPolyDataDistance()
        imp_bone.SetInput(bone_pd)
        
        bounds = [0]*6
        bone_pd.GetBounds(bounds)
        margin = 5.0
        padded_bounds = [bounds[i] + (margin if i%2 else -margin) for i in range(6)]
        
        sample = vtk.vtkSampleFunction()
        sample.SetImplicitFunction(imp_bone)
        sample.SetModelBounds(padded_bounds)
        sample.SetSampleDimensions(120, 120, 120) # Giảm nhẹ để tính toán nhanh
        
        thresh = vtk.vtkImageThreshold()
        thresh.SetInputConnection(sample.GetOutputPort())
        thresh.ThresholdBetween(clearance, clearance + shell)
        thresh.SetInValue(1); thresh.SetOutValue(0); thresh.SetOutputScalarTypeToUnsignedChar()
        
        mc = vtk.vtkDiscreteMarchingCubes()
        mc.SetInputConnection(thresh.GetOutputPort())
        mc.Update()
        guide_pd = mc.GetOutput()

        # 3. Giới hạn Chiều cao (Clip theo cao độ)
        cut_pd = cut_node.GetPolyData()
        imp_cut = vtk.vtkImplicitPolyDataDistance()
        imp_cut.SetInput(cut_pd)
        
        clipper_height = vtk.vtkClipPolyData()
        clipper_height.SetInputData(guide_pd)
        clipper_height.SetClipFunction(imp_cut)
        clipper_height.SetValue(height)
        clipper_height.SetInsideOut(True) # lay phan nguoc lai
        clipper_height.Update()

        imp_ribbon = vtk.vtkImplicitPolyDataDistance()
        imp_ribbon.SetInput(ribbon_node.GetPolyData())
        
        clipper_ribbon = vtk.vtkClipPolyData()
        clipper_ribbon.SetInputConnection(clipper_height.GetOutputPort())
        clipper_ribbon.SetClipFunction(imp_ribbon)
        clipper_ribbon.SetInsideOut(False) # Đổi thành True nếu máng bị ngược
        clipper_ribbon.Update()

        # 4. TRÍCH XUẤT CURVE THỦ CÔNG (Dùng Control Points)
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        
        n_points = curve_node.GetNumberOfControlPoints()
        if n_points < 2:
            print("❌ Lỗi: Curve OC_R cần ít nhất 2 điểm.")
            return
            
        for i in range(n_points):
            pos = [0, 0, 0]
            curve_node.GetNthControlPointPositionWorld(i, pos)
            points.InsertNextPoint(pos)
            
        poly_line = vtk.vtkPolyLine()
        poly_line.GetPointIds().SetNumberOfIds(n_points)
        for i in range(n_points):
            poly_line.GetPointIds().SetId(i, i)
            
        lines.InsertNextCell(poly_line)
        
        curve_pd = vtk.vtkPolyData()
        curve_pd.SetPoints(points)
        curve_pd.SetLines(lines)

        # Tạo bức tường cắt (Extrusion)
        # Để an toàn, chúng ta đùn theo hướng Z từ -200 đến +200
        transform = vtk.vtkTransform()
        transform.Translate(0, 0, -200)
        tf_filter = vtk.vtkTransformPolyDataFilter()
        tf_filter.SetInputData(curve_pd)
        tf_filter.SetTransform(transform)
        tf_filter.Update()

        extrude = vtk.vtkLinearExtrusionFilter()
        extrude.SetInputData(tf_filter.GetOutput())
        extrude.SetExtrusionTypeToVectorExtrusion()
        extrude.SetVector(0, 0, 400) 
        extrude.Update()

        imp_curve = vtk.vtkImplicitPolyDataDistance()
        imp_curve.SetInput(extrude.GetOutput())
        
        clipper_final = vtk.vtkClipPolyData()
        clipper_final.SetInputConnection(clipper_ribbon.GetOutputPort())
        clipper_final.SetClipFunction(imp_curve)
        clipper_final.SetInsideOut(False) 
        clipper_final.Update()


        # Đóng nắp lần cuối sau khi cắt bằng Curve
        final_solid = vtk.vtkFillHolesFilter()
        final_solid.SetInputConnection(clipper_final.GetOutputPort())
        final_solid.SetHoleSize(1000.0)
        final_solid.Update()

        # 5. LÀM MƯỢT (SMOOTHING)
        smoother = vtk.vtkWindowedSincPolyDataFilter()
        smoother.SetInputConnection(final_solid.GetOutputPort())
        smoother.SetNumberOfIterations(30)
        smoother.BoundarySmoothingOn()
        smoother.SetPassBand(0.08)
        smoother.Update()

        # 2. Tính toán lại Vector pháp tuyến (Normals) 
        # Bước này cực kỳ quan trọng để đổ bóng bề mặt trông mượt và bóng, không bị loang lổ
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputConnection(smoother.GetOutputPort())
        normals.SetFeatureAngle(60.0)
        normals.SplittingOn()         # Bật chia tách các cạnh sắc
        normals.ConsistencyOn()       # Đảm bảo hướng các mặt đồng nhất
        normals.AutoOrientNormalsOn() # Tự động định hướng pháp tuyến ra ngoài
        normals.ComputePointNormalsOn() # Tính toán pháp tuyến cho điểm để làm mịn
        normals.Update()

        # 5. Hiển thị kết quả
        result_name = "Final_Guide_bone_1"
        try: slicer.mrmlScene.RemoveNode(slicer.util.getNode(result_name))
        except: pass
        
        model_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", result_name)
        model_node.SetAndObservePolyData(normals.GetOutput())
        model_node.CreateDefaultDisplayNodes()
        model_node.GetDisplayNode().SetColor(0.2, 0.9, 0.5)
        
        print(f"✅ Đã tạo xong máng hướng dẫn!")
        
    def guide_bone_2_export(self, clearance=0.2, shell=2.0, height=18.0):
        config = [
            ('bone_2', 'OC_L', 'cut_2', 'GoL')
        ]
        for bone_name, curve_name, cut_name, landmark_name in config:
            print(f"\n>>> ĐANG XỬ LÝ: {bone_name} <<<")
            
            # 0. Lấy các Node đầu vào (Dùng GetFirstNodeByName để tránh Crash)
            bone_node = slicer.mrmlScene.GetFirstNodeByName(bone_name)
            curve_node = slicer.mrmlScene.GetFirstNodeByName(curve_name)
            cut_node = slicer.mrmlScene.GetFirstNodeByName(cut_name)
            landmark_node = slicer.mrmlScene.GetFirstNodeByName(landmark_name)
            ribbon_node = slicer.mrmlScene.GetFirstNodeByName('Ribbon_L')

            if not all([bone_node, curve_node, cut_node, landmark_node]):
                print(f" ERROR: Không tìm thấy đủ nodes đầu vào! Vui lòng kiểm tra tên trong Data Panel.")
                continue
            bone_pd = bone_node.GetPolyData()
            imp_bone = vtk.vtkImplicitPolyDataDistance()
            imp_bone.SetInput(bone_pd)
            
            bounds = [0]*6
            bone_pd.GetBounds(bounds)
            margin = 5.0 
            padded_bounds = [bounds[i] + (margin if i%2 else -margin) for i in range(6)]
            
            sample = vtk.vtkSampleFunction()
            sample.SetImplicitFunction(imp_bone)
            sample.SetModelBounds(padded_bounds)
            sample.SetSampleDimensions(150, 150, 150)
            
            thresh = vtk.vtkImageThreshold()
            thresh.SetInputConnection(sample.GetOutputPort())
            thresh.ThresholdBetween(clearance, clearance + shell)
            thresh.SetInValue(1); thresh.SetOutValue(0)
            thresh.SetOutputScalarTypeToUnsignedChar()
            
            mc = vtk.vtkDiscreteMarchingCubes()
            mc.SetInputConnection(thresh.GetOutputPort())
            mc.Update()
            guide_pd = mc.GetOutput()

            # 2. GỌT MẶT TRÊN (CLIP BY HEIGHT)
            p_lm = [0,0,0]
            landmark_node.GetNthControlPointPositionWorld(0, p_lm)
            
            imp_cut = vtk.vtkImplicitPolyDataDistance()
            imp_cut.SetInput(cut_node.GetPolyData())
            
            clipper_h = vtk.vtkClipPolyData()
            clipper_h.SetInputData(guide_pd)
            clipper_h.SetClipFunction(imp_cut)
            clipper_h.SetValue(height)
            
            dist_lm = imp_cut.EvaluateFunction(p_lm)
            clipper_h.SetInsideOut(dist_lm < height) 
            clipper_h.Update()

            # --- BỔ SUNG: CẮT THEO Ribbon_L ---
            imp_ribbon = vtk.vtkImplicitPolyDataDistance()
            imp_ribbon.SetInput(ribbon_node.GetPolyData())
            
            clipper_ribbon = vtk.vtkClipPolyData()
            clipper_ribbon.SetInputConnection(clipper_h.GetOutputPort())
            clipper_ribbon.SetClipFunction(imp_ribbon)
            clipper_ribbon.SetInsideOut(False) 
            clipper_ribbon.Update()

            curve_pd = vtk.vtkPolyData()

            if hasattr(curve_node, 'GetCurveDisplayPolyData') and curve_node.GetCurveDisplayPolyData():
                curve_pd.DeepCopy(curve_node.GetCurveDisplayPolyData())
            elif hasattr(curve_node, 'GetNavigationPolyData'):
                curve_node.GetNavigationPolyData(curve_pd)
            else:
                # Phương án cuối: Tự dựng PolyData từ điểm điều khiển
                points = vtk.vtkPoints()
                for i in range(curve_node.GetNumberOfControlPoints()):
                    pos = [0,0,0]
                    curve_node.GetNthControlPointPositionWorld(i, pos)
                    points.InsertNextPoint(pos)
                
                lines = vtk.vtkCellArray()
                line = vtk.vtkPolyLine()
                line.GetPointIds().SetNumberOfIds(points.GetNumberOfPoints())
                for i in range(points.GetNumberOfPoints()):
                    line.GetPointIds().SetId(i, i)
                lines.InsertNextCell(line)
                curve_pd.SetPoints(points)
                curve_pd.SetLines(lines)

            extrude = vtk.vtkLinearExtrusionFilter()
            extrude.SetInputData(curve_pd)
            extrude.SetExtrusionTypeToVectorExtrusion()
            extrude.SetVector(0, 0, 150) # Tăng độ dài để cắt xuyên qua xương
            extrude.Update()

            imp_curve = vtk.vtkImplicitPolyDataDistance()
            imp_curve.SetInput(extrude.GetOutput())
            
            clipper_c = vtk.vtkClipPolyData()
            clipper_c.SetInputConnection(clipper_ribbon.GetOutputPort())
            clipper_c.SetClipFunction(imp_curve)
            
            val_lm_curve = imp_curve.EvaluateFunction(p_lm)
            clipper_c.SetInsideOut(val_lm_curve < 0)
            clipper_c.Update()

            # Đóng nắp lần cuối sau khi cắt bằng Curve
            final_solid = vtk.vtkFillHolesFilter()
            final_solid.SetInputConnection(clipper_c.GetOutputPort())
            final_solid.SetHoleSize(1000.0)
            final_solid.Update()

            # 5. LÀM MƯỢT (SMOOTHING)
            smoother = vtk.vtkWindowedSincPolyDataFilter()
            smoother.SetInputConnection(final_solid.GetOutputPort())
            smoother.SetNumberOfIterations(30)
            smoother.BoundarySmoothingOn()
            smoother.SetPassBand(0.08)
            smoother.Update()

            # Tính toán lại Vector pháp tuyến để bề mặt hiển thị bóng mượt
            normals = vtk.vtkPolyDataNormals()
            normals.SetInputConnection(smoother.GetOutputPort())
            normals.SetFeatureAngle(60.0)
            normals.SplittingOn()         # Bật chia tách các cạnh sắc
            normals.ConsistencyOn()       # Đảm bảo hướng các mặt đồng nhất
            normals.AutoOrientNormalsOn() # Tự động định hướng pháp tuyến ra ngoài
            normals.ComputePointNormalsOn() # Tính toán pháp tuyến cho điểm để làm mịn
            normals.Update()

            # 4. HIỂN THỊ KẾT QUẢ (SỬA LỖI TẠI ĐÂY)
            result_name = f"Final_Guide_{bone_name}"
            
            # Tìm node cũ bằng tên một cách an toàn
            existing_node = slicer.mrmlScene.GetFirstNodeByName(result_name)
            if existing_node:
                slicer.mrmlScene.RemoveNode(existing_node)

            final_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", result_name)
            final_node.SetAndObservePolyData(normals.GetOutput())
            final_node.CreateDefaultDisplayNodes()
            final_node.GetDisplayNode().SetColor(0.2, 0.6, 1.0) # Màu xanh dương
            
            print(f" --- XỬ LÝ XONG: {result_name} ---")

