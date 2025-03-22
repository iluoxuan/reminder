import sys
import json
import os
import schedule
import time
import threading
import random
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QSpinBox, 
                             QComboBox, QSystemTrayIcon, QMenu, QMessageBox,
                             QStackedWidget, QFrame, QLineEdit, QTimeEdit,
                             QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QTimer, QSize, QTime, QEvent, QPropertyAnimation, QPoint, Property
from PySide6.QtGui import QIcon, QFont, QPixmap, QColor, QPalette
import win32com.client
import winreg

class MaterialLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QLineEdit {
                border: none;
                border-bottom: 2px solid #E0E0E0;
                padding: 8px;
                background: transparent;
                color: #333333;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-bottom: 2px solid #2196F3;
            }
        """)

class CardFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            CardFrame {
                background-color: white;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        self.setAttribute(Qt.WA_StyledBackground, True)

class QShowReminderEvent(QEvent):
    """自定义显示提醒事件"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self):
        super().__init__(self.EVENT_TYPE)

class DanmakuLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.85);
                font-size: 32px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # 随机设置初始位置和动画时长
        self.speed = random.randint(6000, 12000)  # 6-12秒穿过屏幕，速度更快
        self.start_pos = random.randint(0, parent.height() - 50) if parent else 0
        
        # 初始透明度为0
        self.setGraphicsEffect(None)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self.opacity_effect)
        
    def start_animation(self, screen_width):
        # 创建位置动画
        self.pos_anim = QPropertyAnimation(self, b"pos")
        self.pos_anim.setDuration(self.speed)
        self.pos_anim.setStartValue(QPoint(screen_width, self.start_pos))
        self.pos_anim.setEndValue(QPoint(-self.width(), self.start_pos))
        
        # 创建透明度动画
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(500)  # 0.5秒淡入，更快的淡入效果
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(0.85)
        
        # 开始动画
        self.fade_in.start()
        self.pos_anim.start()
        self.pos_anim.finished.connect(self.deleteLater)

class ReminderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("提醒助手")
        self.setFixedSize(420, 680)
        
        # Material Design 颜色
        self.colors = {
            'primary': '#2196F3',
            'primary_dark': '#1976D2',
            'accent': '#FF4081',
            'background': '#F5F7FA',
            'card': '#FFFFFF',
            'error': '#F44336',
            'text_primary': '#2C3E50',
            'text_secondary': '#607D8B',
            'divider': '#E0E0E0'
        }
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.colors['background']};
            }}
            QLabel {{
                color: {self.colors['text_primary']};
                font-size: 14px;
            }}
            QPushButton {{
                background-color: {self.colors['primary']};
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['primary_dark']};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['primary']};
                padding: 14px 10px 10px 14px;
            }}
            QSpinBox, QComboBox, QTimeEdit {{
                padding: 8px;
                border: 2px solid {self.colors['divider']};
                border-radius: 6px;
                background-color: white;
                min-height: 20px;
                min-width: 150px;
                font-size: 14px;
                selection-background-color: {self.colors['primary']};
            }}
            QSpinBox:focus, QComboBox:focus, QTimeEdit:focus {{
                border: 2px solid {self.colors['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 20px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 20px;
            }}
            QTimeEdit::up-button, QTimeEdit::down-button {{
                width: 20px;
            }}
        """)
        
        # 设置窗口图标
        self.setWindowIcon(QIcon("icon.ico"))
        
        # 创建并设置系统托盘图标
        self.setup_tray_icon()
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建标题卡片
        title_card = CardFrame()
        title_layout = QVBoxLayout(title_card)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("提醒助手")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: bold;
            color: {self.colors['primary']};
            margin: 10px 0;
        """)
        title_layout.addWidget(title_label)
        main_layout.addWidget(title_card)
        
        # 创建设置卡片
        settings_card = CardFrame()
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setSpacing(20)
        
        # 提醒类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel("提醒类型")
        type_label.setStyleSheet(f"color: {self.colors['text_primary']}; font-weight: bold;")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["喝水", "运动", "休息", "自定义"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        settings_layout.addLayout(type_layout)
        
        # 自定义提醒文本
        self.custom_text_widget = QWidget()
        self.custom_text_layout = QHBoxLayout(self.custom_text_widget)
        self.custom_text_layout.setContentsMargins(0, 0, 0, 0)
        custom_text_label = QLabel("自定义文本")
        custom_text_label.setStyleSheet(f"color: {self.colors['text_primary']}; font-weight: bold;")
        self.custom_text_input = MaterialLineEdit()
        self.custom_text_input.setPlaceholderText("请输入提醒文本")
        self.custom_text_layout.addWidget(custom_text_label)
        self.custom_text_layout.addWidget(self.custom_text_input)
        settings_layout.addWidget(self.custom_text_widget)
        self.custom_text_widget.hide()
        
        # 提醒间隔设置
        interval_layout = QHBoxLayout()
        interval_label = QLabel("提醒间隔")
        interval_label.setStyleSheet(f"color: {self.colors['text_primary']}; font-weight: bold;")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 120)
        self.interval_spin.setValue(30)
        self.interval_spin.setSuffix(" 分钟")
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spin)
        settings_layout.addLayout(interval_layout)
        
        # 添加定时提醒
        time_layout = QHBoxLayout()
        time_label = QLabel("定时提醒")
        time_label.setStyleSheet(f"color: {self.colors['text_primary']}; font-weight: bold;")
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_edit)
        settings_layout.addLayout(time_layout)
        
        main_layout.addWidget(settings_card)
        
        # 创建按钮卡片
        button_card = CardFrame()
        button_layout = QVBoxLayout(button_card)
        button_layout.setSpacing(15)
        
        # 开始/停止提醒按钮
        self.start_button = QPushButton("开始提醒")
        self.start_button.clicked.connect(self.toggle_reminder)
        button_layout.addWidget(self.start_button)
        
        # 打赏支持按钮
        self.donate_button = QPushButton("打赏支持")
        self.donate_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['accent']};
                color: white;
            }}
            QPushButton:hover {{
                background-color: #E91E63;
            }}
        """)
        self.donate_button.clicked.connect(self.show_donate)
        button_layout.addWidget(self.donate_button)
        
        # 开机自启按钮
        self.autostart_button = QPushButton("设置开机自启")
        self.autostart_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['text_secondary']};
                color: white;
            }}
            QPushButton:hover {{
                background-color: #546E7A;
            }}
        """)
        self.autostart_button.clicked.connect(self.toggle_autostart)
        button_layout.addWidget(self.autostart_button)
        
        main_layout.addWidget(button_card)
        
        # 创建状态卡片
        status_card = CardFrame()
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"""
            color: {self.colors['text_secondary']};
            font-size: 13px;
        """)
        status_layout.addWidget(self.status_label)
        main_layout.addWidget(status_card)
        
        # 创建全屏提醒窗口
        self.setup_reminder_window()
        
        # 初始化变量
        self.reminder_active = False
        self.reminder_thread = None
        self.scheduled_time = None
        self.current_language = "中文"
        self.load_language()
        
        # 检查开机自启状态
        self.check_autostart()
        
        # 设置窗口位置
        self.center_window()
        
    def on_type_changed(self, text):
        """当提醒类型改变时调用"""
        self.custom_text_widget.setVisible(text == "自定义")
        
    def center_window(self):
        """将窗口居中显示"""
        screen = QApplication.primaryScreen().geometry()
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(x, y)
        
    def load_language(self):
        """加载语言配置"""
        try:
            with open('language.json', 'r', encoding='utf-8') as f:
                self.language_data = json.load(f)
        except Exception as e:
            print(f"加载语言文件失败: {e}")
            self.language_data = {
                "中文": {
                    "喝水": "喝水",
                    "运动": "运动",
                    "休息": "休息",
                    "自定义": "自定义",
                    "开始提醒": "开始提醒",
                    "停止提醒": "停止提醒",
                    "提醒间隔": "提醒间隔",
                    "分钟": "分钟",
                    "打赏支持": "打赏支持",
                    "显示": "显示",
                    "退出": "退出",
                    "设置开机自启": "设置开机自启",
                    "取消开机自启": "取消开机自启"
                }
            }
            
    def get_text(self, key):
        """获取当前语言的文本"""
        return self.language_data.get(self.current_language, {}).get(key, key)
        
    def toggle_reminder(self):
        """切换提醒状态"""
        if not self.reminder_active:
            self.start_reminder()
        else:
            self.stop_reminder()
            
    def start_reminder(self):
        """开始提醒"""
        self.reminder_active = True
        self.start_button.setText(self.get_text("停止提醒"))
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['error']};
                color: white;
            }}
            QPushButton:hover {{
                background-color: #D32F2F;
            }}
        """)
        self.status_label.setText("提醒已开启")
        self.reminder_thread = threading.Thread(target=self.reminder_loop)
        self.reminder_thread.daemon = True
        self.reminder_thread.start()
        
    def stop_reminder(self):
        """停止提醒"""
        try:
            self.reminder_active = False
            self.start_button.setText(self.get_text("开始提醒"))
            self.start_button.setStyleSheet("")
            self.status_label.setText("提醒已停止")
            if self.reminder_thread and self.reminder_thread.is_alive():
                self.reminder_thread.join(timeout=1)
            self.hide_reminder()
        except Exception as e:
            print(f"停止提醒出错: {e}")
        
    def reminder_loop(self):
        """提醒循环"""
        last_reminder_time = datetime.now()
        
        while self.reminder_active:
            try:
                current_time = datetime.now()
                scheduled_time = self.time_edit.time().toPython()
                
                # 检查是否到达定时提醒时间
                if (current_time.time().hour == scheduled_time.hour and 
                    current_time.time().minute == scheduled_time.minute and
                    (current_time - last_reminder_time).seconds >= 55):  # 避免重复提醒
                    QApplication.instance().postEvent(self, QShowReminderEvent())
                    last_reminder_time = current_time
                    time.sleep(5)  # 等待5秒后继续检查
                    continue
                
                # 检查间隔提醒
                interval_seconds = self.interval_spin.value() * 60
                if (current_time - last_reminder_time).seconds >= interval_seconds:
                    QApplication.instance().postEvent(self, QShowReminderEvent())
                    last_reminder_time = current_time
                
                # 每秒检查一次
                time.sleep(1)
            except Exception as e:
                print(f"提醒循环出错: {e}")
                time.sleep(1)
            
    def show_reminder(self):
        """显示提醒"""
        try:
            reminder_type = self.type_combo.currentText()
            if reminder_type == "自定义":
                reminder_text = self.custom_text_input.text() or "自定义提醒"
            else:
                reminder_text = f"该{reminder_type}了！"
                
            self.reminder_label.setText(reminder_text)
            
            # 设置全屏显示
            screen = QApplication.primaryScreen().geometry()
            self.reminder_window.setGeometry(screen)
            self.reminder_window.show()
            
            # 重置弹幕计数器
            self.danmaku_count = 0
            
            # 开始弹幕效果，每600毫秒添加一个新弹幕
            self.danmaku_timer.start(600)
            
            # 播放提示音
            self.play_sound()
            
            # 30秒后自动隐藏
            self.hide_timer.start(30000)
        except Exception as e:
            print(f"显示提醒窗口出错: {e}")
        
    def hide_reminder(self):
        """隐藏提醒"""
        try:
            self.hide_timer.stop()
            self.danmaku_timer.stop()
            # 清理所有弹幕
            for child in self.reminder_window.findChildren(DanmakuLabel):
                child.deleteLater()
            self.reminder_window.hide()
        except Exception as e:
            print(f"隐藏提醒窗口出错: {e}")
        
    def play_sound(self):
        """播放提示音"""
        try:
            reminder_type = self.type_combo.currentText()
            if reminder_type == "自定义":
                text = self.custom_text_input.text() or "自定义提醒"
            else:
                text = f"该{reminder_type}了"
            self.speaker.Speak(text)
        except Exception as e:
            print(f"播放提示音出错: {e}")
            
    def show_donate(self):
        """显示打赏二维码"""
        try:
            # 创建打赏窗口
            donate_window = QWidget()
            donate_window.setWindowTitle("打赏支持")
            donate_window.setFixedSize(300, 400)
            donate_window.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.colors['background']};
                    border-radius: 8px;
                }}
            """)
            
            # 创建布局
            layout = QVBoxLayout(donate_window)
            layout.setSpacing(20)
            layout.setContentsMargins(30, 30, 30, 30)
            
            # 添加标题
            title = QLabel("感谢支持！")
            title.setAlignment(Qt.AlignCenter)
            title.setStyleSheet(f"""
                font-size: 24px;
                font-weight: bold;
                color: {self.colors['primary']};
            """)
            layout.addWidget(title)
            
            # 添加说明文字
            description = QLabel("您的支持是我持续改进的动力！")
            description.setAlignment(Qt.AlignCenter)
            description.setStyleSheet(f"""
                font-size: 14px;
                color: {self.colors['text_secondary']};
            """)
            layout.addWidget(description)
            
            # 添加二维码
            try:
                qr_label = QLabel()
                qr_pixmap = QPixmap("donate_qr.png")
                qr_label.setPixmap(qr_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                qr_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(qr_label)
            except:
                qr_placeholder = QLabel("二维码加载失败")
                qr_placeholder.setAlignment(Qt.AlignCenter)
                qr_placeholder.setStyleSheet(f"""
                    background-color: {self.colors['surface']};
                    border-radius: 5px;
                    padding: 20px;
                    font-size: 16px;
                    color: {self.colors['text_secondary']};
                """)
                layout.addWidget(qr_placeholder)
            
            # 添加关闭按钮
            close_button = QPushButton("关闭")
            close_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.colors['primary']};
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 4px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors['primary_dark']};
                }}
            """)
            close_button.clicked.connect(donate_window.close)
            layout.addWidget(close_button)
            
            # 显示窗口
            donate_window.show()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"显示打赏二维码失败: {e}")
            
    def toggle_autostart(self):
        """切换开机自启状态"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run",
                               0, winreg.KEY_ALL_ACCESS)
            
            try:
                winreg.QueryValueEx(key, "ReminderApp")
                # 如果存在，则删除
                winreg.DeleteValue(key, "ReminderApp")
                self.autostart_button.setText(self.get_text("设置开机自启"))
                self.status_label.setText("已取消开机自启")
            except:
                # 如果不存在，则添加
                app_path = os.path.abspath(sys.argv[0])
                winreg.SetValueEx(key, "ReminderApp", 0, winreg.REG_SZ, app_path)
                self.autostart_button.setText(self.get_text("取消开机自启"))
                self.status_label.setText("已设置开机自启")
                
            winreg.CloseKey(key)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"设置开机自启失败: {e}")
            
    def check_autostart(self):
        """检查开机自启状态"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run",
                               0, winreg.KEY_READ)
            
            try:
                winreg.QueryValueEx(key, "ReminderApp")
                self.autostart_button.setText(self.get_text("取消开机自启"))
            except:
                self.autostart_button.setText(self.get_text("设置开机自启"))
                
            winreg.CloseKey(key)
        except:
            self.autostart_button.setText(self.get_text("设置开机自启"))
            
    def setup_tray_icon(self):
        """设置系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.ico"))
        self.tray_icon.setToolTip("提醒助手")  # 添加悬停提示
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 添加菜单项
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show_main_window)
        
        tray_menu.addSeparator()  # 添加分隔线
        
        quit_action = tray_menu.addAction("退出程序")
        quit_action.triggered.connect(self.quit_app)
        
        # 设置托盘图标的上下文菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 添加托盘图标的双击事件
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
        
    def show_main_window(self):
        """显示主窗口"""
        self.showNormal()  # 使用showNormal代替show，以确保窗口正常显示
        self.activateWindow()  # 激活窗口
        self.raise_()  # 将窗口提升到最前
        
    def tray_icon_activated(self, reason):
        """处理托盘图标的激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_main_window()
            
    def closeEvent(self, event):
        """关闭窗口事件"""
        if hasattr(event, 'spontaneous') and event.spontaneous():
            # 用户通过任务栏或Alt+F4关闭
            reply = QMessageBox.question(
                self, 
                "确认退出", 
                '是否要完全退出程序？\n选择"否"将最小化到系统托盘。',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.quit_app()
            else:
                event.ignore()
                self.hide()
                self.tray_icon.showMessage(
                    "提醒助手",
                    "程序已最小化到系统托盘，双击图标可重新打开主窗口",
                    QSystemTrayIcon.Information,
                    2000
                )
        else:
            # 程序自身调用close()
            event.accept()

    def quit_app(self):
        """退出应用"""
        try:
            # 停止所有活动
            self.stop_reminder()
            
            # 隐藏托盘图标
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
            
            # 关闭所有窗口
            if hasattr(self, 'reminder_window'):
                self.reminder_window.close()
            
            # 退出应用
            QApplication.quit()
        except Exception as e:
            print(f"退出应用时出错: {e}")
            QApplication.quit()  # 确保应用退出

    def setup_reminder_window(self):
        """设置全屏提醒窗口"""
        self.reminder_window = QWidget()
        self.reminder_window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.reminder_window.setStyleSheet("""
            QWidget {
                background-color: rgba(44, 62, 80, 0.92);  /* 深色背景 */
            }
            QLabel {
                color: rgba(255, 255, 255, 0.95);
                font-size: 48px;
                font-weight: bold;
            }
        """)
        
        reminder_layout = QVBoxLayout(self.reminder_window)
        reminder_layout.setAlignment(Qt.AlignCenter)
        reminder_layout.setSpacing(30)
        
        self.reminder_label = QLabel()
        self.reminder_label.setAlignment(Qt.AlignCenter)
        reminder_layout.addWidget(self.reminder_label)
        
        # 添加关闭按钮
        close_button = QPushButton("我知道了")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                color: white;
                padding: 15px 30px;
                border-radius: 25px;
                font-size: 18px;
                min-width: 200px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.25);
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
        """)
        close_button.clicked.connect(self.hide_reminder)
        reminder_layout.addWidget(close_button, alignment=Qt.AlignCenter)
        
        # 设置定时器用于自动隐藏提醒
        self.hide_timer = QTimer(self)
        self.hide_timer.timeout.connect(self.hide_reminder)
        self.hide_timer.setSingleShot(True)
        
        # 设置定时器用于弹幕效果
        self.danmaku_timer = QTimer(self)
        self.danmaku_timer.timeout.connect(self.add_danmaku)
        
        # 设置定时器用于播放提示音
        self.sound_timer = QTimer(self)
        self.sound_timer.timeout.connect(self.play_sound)
        self.sound_timer.setSingleShot(True)
        
        # 初始化弹幕计数器
        self.danmaku_count = 0
        self.max_danmaku = 30  # 增加最大弹幕数量到30个

    def add_danmaku(self):
        """添加新弹幕"""
        try:
            if self.danmaku_count >= self.max_danmaku:
                self.danmaku_timer.stop()
                return
                
            screen = QApplication.primaryScreen().geometry()
            reminder_type = self.type_combo.currentText()
            if reminder_type == "自定义":
                text = self.custom_text_input.text() or "自定义提醒"
            else:
                text = f"该{reminder_type}了！"
            
            # 创建新的弹幕标签
            danmaku = DanmakuLabel(text, self.reminder_window)
            danmaku.show()
            danmaku.start_animation(screen.width())
            
            self.danmaku_count += 1
        except Exception as e:
            print(f"添加弹幕出错: {e}")

    def event(self, event):
        """处理自定义事件"""
        if event.type() == QShowReminderEvent.EVENT_TYPE:
            self.show_reminder()
            return True
        return super().event(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 检查系统是否支持系统托盘
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "提醒助手", "系统不支持托盘图标功能！")
        sys.exit(1)
        
    # 设置退出时是否显示确认对话框
    QApplication.setQuitOnLastWindowClosed(False)
    
    window = ReminderApp()
    window.show()
    sys.exit(app.exec()) 