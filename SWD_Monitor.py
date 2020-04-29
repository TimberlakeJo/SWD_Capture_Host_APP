import sys
import serial
import serial.tools.list_ports
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from SWD_Monitor_UI_Widget import Ui_Form


class Pyqt5_SWD_Monitor(QtWidgets.QWidget, Ui_Form):
    def __init__(self):
        super(Pyqt5_SWD_Monitor, self).__init__()
        self.setupUi(self)
        self.init()
        self.setWindowTitle("SWD捕获助手")
        self.ser = serial.Serial()
        self.port_check()

        # 接收数据数目置零
        self.data_num_received = 0
        self.data_num_host_sent = 0
        self.data_num_host_received = 0
        self.data_bytes_num = 0

        # 接收数据字典初始化
        self.Frame_Dict = {}
        self.Frame_Dict_Byte = {}

    def init(self):
        # 串口信息显示
        self.Port_comboBox.currentTextChanged.connect(self.port_imf)

        # 打开串口按钮
        self.Open_Button.clicked.connect(self.port_open)

        # 关闭串口按钮
        self.Close_Button.clicked.connect(self.port_close)

        # 定时器接收数据
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.data_receive)

        # 定时器检测端口
        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(self.port_check)

        # 清除发送窗口
        self.Clear_pushButton_Receive.clicked.connect(self.receive_data_clear)

        # 清除接收窗口
        self.Clear_pushButton_Analyze.clicked.connect(self.analyze_data_clear)

        # 接收数据解析
        self.Receive_listWidget.itemClicked.connect(self.receive_data_analyze)

    # 串口检测
    def port_check(self):
        # 检测所有存在的串口，将信息存储在字典中
        self.Com_Dict = {}
        port_list = list(serial.tools.list_ports.comports())
        self.Port_comboBox.clear()
        for port in port_list:
            self.Com_Dict["%s" % port[0]] = "%s" % port[1]
            self.Port_comboBox.addItem(port[0])

    # 串口信息
    def port_imf(self):
        # 显示选定的串口的详细信息
        imf_s = self.Port_comboBox.currentText()
        if imf_s != "":
            self.PortInfo_Label.setText(self.Com_Dict[self.Port_comboBox.currentText()])

    # 打开串口
    def port_open(self):
        self.ser.port = self.Port_comboBox.currentText()
        self.ser.baudrate = int(self.BaudRate_comboBox.currentText())
        self.ser.bytesize = 8
        self.ser.stopbits = 1
        self.ser.parity = self.ser.PARITIES[0]

        try:
            self.ser.open()
        except:
            QMessageBox.critical(self, "Port Error", "此串口不能被打开！")
            return None

        # 打开串口接收定时器，周期为2ms
        self.timer.start(3)

        if self.ser.isOpen():
            self.Open_Button.setEnabled(False)
            self.Close_Button.setEnabled(True)
            self.Port_Status_Label_2.setText("Opened")

    # 关闭串口
    def port_close(self):
        self.timer.stop()
        try:
            self.ser.close()
        except:
            pass
        self.Open_Button.setEnabled(True)
        self.Close_Button.setEnabled(False)
        # 接收数据和发送数据数目置零
        self.data_num_received = 0
        self.Number_textBrowser.setText(str(self.data_num_received))
        self.data_num_host_sent = 0
        self.Number_textBrowser_2.setText(str(self.data_num_host_sent))
        self.data_num_host_received = 0
        self.Number_textBrowser_3.setText(str(self.data_num_host_received))
        self.Port_Status_Label_2.setText("Closed")

    # 接收数据
    def data_receive(self):
        try:
            num = self.ser.inWaiting()
        except:
            self.port_close()
            return None
        if num > 0:
            data = self.ser.read(num)
            num = len(data)
            # hex显示
            self.out_s = ''
            self.out_b = b''
            for i in range(0, len(data)):
                if ((self.data_bytes_num + 1) % 6) == 0:
                    self.out_s = self.out_s + '{:02X}'.format(data[i]) + ' '
                    self.out_b = self.out_b + '{:02X}'.format(data[i]).encode()
                    self.data_bytes_num += 1
                    data_item = QListWidgetItem(self.out_s)
                    self.Receive_listWidget.addItem(data_item)
                    self.Frame_Dict_Byte[self.data_num_received] = self.out_s
                    self.out_s = ''
                    self.Frame_Dict[self.data_num_received] = self.out_b
                    self.out_b = b''
                    # 统计接收Frame的数量
                    self.data_num_received += 1
                    self.Number_textBrowser.setText(str(self.data_num_received))
                else:
                    self.out_s = self.out_s + '{:02X}'.format(data[i]) + ' '
                    self.out_b = self.out_b + '{:02X}'.format(data[i]).encode()
                    self.data_bytes_num += 1
        else:
            pass

    # 定时发送数据
    def data_send_timer(self):
        if self.timer_send_cb.isChecked():
            self.timer_send.start(int(self.lineEdit_3.text()))
            self.lineEdit_3.setEnabled(False)
        else:
            self.timer_send.stop()
            self.lineEdit_3.setEnabled(True)

    # 清除显示
    def analyze_data_clear(self):
        self.AnalyzetextBrowser.setText("")

    def receive_data_clear(self):
        self.data_num_received = 0
        self.data_bytes_num = 0
        self.Frame_Dict = {}
        self.Frame_Dict_Byte = {}
        frame_count = self.Receive_listWidget.count()
        for count in range(frame_count):
            self.Receive_listWidget.takeItem(0)

    # 解析数据
    def receive_data_analyze(self):
        List_Item = self.Receive_listWidget.currentRow()
        analyze_data = self.Frame_Dict[List_Item]
        list_frame = self.Frame_Dict_Byte[List_Item]
        data = (analyze_data[5] << 40) + (analyze_data[4] << 32) + (analyze_data[3]<<24)\
               + (analyze_data[2] << 16) + (analyze_data[1] << 8) + analyze_data[0]
        Header = (data >> 37) & 0xFF
        self.AnalyzetextBrowser.insertPlainText('Frame: ' + list_frame + '\r\n')
        self.AnalyzetextBrowser.insertPlainText('Frame Type: ')
        if((Header & 0x20) == 0):
            self.AnalyzetextBrowser.insertPlainText('Write\r\n')
            self.AnalyzetextBrowser.insertPlainText('Header:')
            self.AnalyzetextBrowser.insertPlainText(str(bin(Header)) + '\r\n')
            ACK = (data >> 33) & 0x07
            self.AnalyzetextBrowser.insertPlainText('ACK:')
            self.AnalyzetextBrowser.insertPlainText(str(bin(ACK)) + '\r\n')
            WDATA = data & 0xFFFFFFFF
            self.AnalyzetextBrowser.insertPlainText('WDATA:')
            self.AnalyzetextBrowser.insertPlainText('0b' + str('{0:b}'.format(WDATA)).zfill(32) + '\r\n\r\n')
        else:
            self.AnalyzetextBrowser.insertPlainText('Read\r\n')
            self.AnalyzetextBrowser.insertPlainText('Header:')
            self.AnalyzetextBrowser.insertPlainText(str(bin(Header)) + '\r\n')
            ACK = (data >> 33) & 0x07
            self.AnalyzetextBrowser.insertPlainText('ACK:')
            self.AnalyzetextBrowser.insertPlainText(str(bin(ACK)) + '\r\n')
            RDATA = (data >> 1) & 0xFFFFFFFF
            self.AnalyzetextBrowser.insertPlainText('RDATA:')
            self.AnalyzetextBrowser.insertPlainText('0b' + str('{0:b}'.format(RDATA)).zfill(32) + '\r\n\r\n')



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myshow = Pyqt5_SWD_Monitor()
    myshow.show()
    sys.exit(app.exec_())