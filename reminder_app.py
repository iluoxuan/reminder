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
                             QGraphicsOpacityEffect, QTabWidget, QGraphicsDropShadowEffect)
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
                border-radius: 4px;
                padding: 8px 12px;
                background: #F5F6F7;
                color: #1F2329;
                font-size: 14px;
                min-height: 20px;
            }
            QLineEdit:focus {
                background: #FFFFFF;
                border: 1px solid #1677FF;
            }
            QLineEdit:hover {
                background: #FFFFFF;
                border: 1px solid #4096FF;
            }
        """)

class CardFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            CardFrame {
                background-color: white;
                border-radius: 8px;
                border: none;
            }
        """)
        # 更柔和的阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
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
        self.setFixedSize(680, 580)
        
        # 初始化语音引擎
        self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
        
        # 配色方案 - 清新简约风格
        self.colors = {
            'primary': '#1890FF',      # 主色调：清新蓝
            'background': '#F5F7FA',   # 背景色：浅灰白
            'sidebar': '#FFFFFF',      # 侧边栏：纯白
            'card': '#FFFFFF',         # 卡片色：纯白
            'text': '#1D2129',         # 主要文字：深灰
            'text_secondary': '#4E5969', # 次要文字：中灰
            'border': '#E5E6EB',       # 边框色：浅灰
            'hover': '#E8F3FF',        # 悬停色：淡蓝
            'input_bg': '#F5F7FA',     # 输入框背景：浅灰
            'success': '#52C41A',      # 成功色：清新绿
            'error': '#FF4D4F',        # 错误色：点睛红
        }
        
        # 设置全局样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.colors['background']};
            }}
            QLabel {{
                color: {self.colors['text']};
                font-size: 14px;
                font-weight: 400;
            }}
            QPushButton {{
                background-color: {self.colors['primary']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: #40A9FF;
            }}
            QPushButton:pressed {{
                background-color: #096DD9;
            }}
            QSpinBox, QComboBox, QTimeEdit {{
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 4px 12px;
                background-color: white;
                color: {self.colors['text']};
                min-height: 36px;
                font-size: 14px;
            }}
            QSpinBox:focus, QComboBox:focus, QTimeEdit:focus {{
                border: 1px solid {self.colors['primary']};
            }}
            QSpinBox:hover, QComboBox:hover, QTimeEdit:hover {{
                border: 1px solid {self.colors['primary']};
            }}
        """)
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建左侧边栏
        sidebar = QWidget()
        sidebar.setFixedWidth(60)  # 恢复原来的宽度
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {self.colors['sidebar']};
                border-right: 1px solid {self.colors['border']};
            }}
            QPushButton {{
                background-color: transparent;
                color: {self.colors['text_secondary']};
                border: none;
                border-radius: 4px;
                text-align: center;
                padding: 12px 0;
                font-size: 13px;
                min-height: 24px;
                margin: 4px 8px;
            }}
            QPushButton:hover {{
                color: {self.colors['primary']};
                background-color: {self.colors['hover']};
            }}
            QPushButton[selected=true] {{
                color: {self.colors['primary']};
                background-color: {self.colors['hover']};
                font-weight: 500;
            }}
        """)
        
        # 创建侧边栏布局
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加功能按钮
        self.reminder_btn = QPushButton("提醒")
        self.reminder_btn.setProperty("selected", True)
        self.reminder_btn.clicked.connect(lambda: self.switch_page(0))
        
        self.sleep_btn = QPushButton("计划")
        self.sleep_btn.setProperty("selected", False)
        self.sleep_btn.clicked.connect(lambda: self.switch_page(1))
        
        self.settings_btn = QPushButton("设置")
        self.settings_btn.setProperty("selected", False)
        self.settings_btn.clicked.connect(lambda: self.switch_page(2))
        
        sidebar_layout.addWidget(self.reminder_btn)
        sidebar_layout.addWidget(self.sleep_btn)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.settings_btn)
        
        # 创建右侧内容区
        content = QWidget()
        content.setStyleSheet(f"""
            QWidget {{
                background-color: {self.colors['background']};
            }}
        """)
        
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建堆叠部件用于切换页面
        self.stack = QStackedWidget()
        
        # 创建提醒设置页面
        reminder_page = QWidget()
        reminder_layout = QVBoxLayout(reminder_page)
        reminder_layout.setSpacing(20)
        reminder_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建提醒设置卡片
        settings_card = CardFrame()
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setSpacing(20)
        settings_layout.setContentsMargins(24, 24, 24, 24)
        
        # 提醒类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel("提醒类型")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["喝水", "运动", "休息", "自定义"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        type_layout.setStretchFactor(type_label, 1)
        type_layout.setStretchFactor(self.type_combo, 2)
        settings_layout.addLayout(type_layout)
        
        # 自定义提醒文本
        self.custom_text_widget = QWidget()
        self.custom_text_layout = QHBoxLayout(self.custom_text_widget)
        self.custom_text_layout.setContentsMargins(0, 0, 0, 0)
        custom_text_label = QLabel("自定义文本")
        self.custom_text_input = MaterialLineEdit()
        self.custom_text_input.setPlaceholderText("请输入提醒文本")
        self.custom_text_layout.addWidget(custom_text_label)
        self.custom_text_layout.addWidget(self.custom_text_input)
        self.custom_text_layout.setStretchFactor(custom_text_label, 1)
        self.custom_text_layout.setStretchFactor(self.custom_text_input, 2)
        settings_layout.addWidget(self.custom_text_widget)
        self.custom_text_widget.hide()
        
        # 提醒间隔设置
        interval_layout = QHBoxLayout()
        interval_label = QLabel("提醒间隔")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 120)
        self.interval_spin.setValue(30)
        self.interval_spin.setSuffix(" 分钟")
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spin)
        interval_layout.setStretchFactor(interval_label, 1)
        interval_layout.setStretchFactor(self.interval_spin, 2)
        settings_layout.addLayout(interval_layout)
        
        # 定时提醒设置
        time_layout = QHBoxLayout()
        time_label = QLabel("定时提醒")
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_edit)
        time_layout.setStretchFactor(time_label, 1)
        time_layout.setStretchFactor(self.time_edit, 2)
        settings_layout.addLayout(time_layout)
        
        # 添加按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        
        # 开始/停止按钮
        self.toggle_button = QPushButton("启动专注时段")
        self.toggle_button.setFixedWidth(160)  # 增加按钮宽度
        self.toggle_button.clicked.connect(self.toggle_reminder)
        button_layout.addWidget(self.toggle_button)
        
        button_layout.addStretch()
        settings_layout.addLayout(button_layout)
        
        reminder_layout.addWidget(settings_card)
        reminder_layout.addStretch()
        
        # 创建睡眠设置页面
        sleep_page = QWidget()
        sleep_layout = QVBoxLayout(sleep_page)
        sleep_layout.setSpacing(20)
        sleep_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建睡眠设置卡片
        sleep_card = CardFrame()
        sleep_settings_layout = QVBoxLayout(sleep_card)
        sleep_settings_layout.setSpacing(20)
        sleep_settings_layout.setContentsMargins(24, 24, 24, 24)
        
        # 睡眠时间设置
        sleep_time_layout = QHBoxLayout()
        sleep_time_label = QLabel("睡眠时间")
        sleep_time_label.setStyleSheet(f"""
            QLabel {{
                color: {self.colors['text']};
                font-size: 14px;
                font-weight: 400;
            }}
        """)
        self.sleep_time_spin = QSpinBox()
        self.sleep_time_spin.setRange(1, 120)
        self.sleep_time_spin.setValue(20)
        self.sleep_time_spin.setSuffix(" 分钟")
        self.sleep_time_spin.setStyleSheet(f"""
            QSpinBox {{
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 4px 12px;
                background-color: white;
                color: {self.colors['text']};
                min-height: 36px;
                font-size: 24px;
                font-weight: 500;
            }}
            QSpinBox:hover {{
                border: 1px solid {self.colors['primary']};
            }}
            QSpinBox:focus {{
                border: 1px solid {self.colors['primary']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 0;
                border: none;
                background: transparent;
            }}
            QSpinBox::up-arrow, QSpinBox::down-arrow {{
                width: 0;
                height: 0;
                border: none;
            }}
        """)
        sleep_time_layout.addWidget(sleep_time_label)
        sleep_time_layout.addWidget(self.sleep_time_spin)
        sleep_time_layout.setStretchFactor(sleep_time_label, 1)
        sleep_time_layout.setStretchFactor(self.sleep_time_spin, 2)
        sleep_settings_layout.addLayout(sleep_time_layout)
        
        # 添加睡眠按钮布局
        sleep_button_layout = QHBoxLayout()
        sleep_button_layout.setSpacing(16)
        
        # 设置睡眠按钮
        self.sleep_button = QPushButton("设置睡眠")
        self.sleep_button.setFixedWidth(160)  # 增加按钮宽度
        self.sleep_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['primary']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                min-height: 40px;
                text-align: left;
                padding-left: 20px;
                background-image: url(play.png);
                background-repeat: no-repeat;
                background-position: 120px center;
                background-size: 16px 16px;
            }}
            QPushButton:hover {{
                background-color: #40A9FF;
            }}
            QPushButton:pressed {{
                background-color: #096DD9;
            }}
        """)
        self.sleep_button.clicked.connect(self.set_sleep)
        sleep_button_layout.addWidget(self.sleep_button)
        
        # 取消睡眠按钮
        self.cancel_sleep_button = QPushButton("取消睡眠")
        self.cancel_sleep_button.setFixedWidth(160)  # 增加按钮宽度
        self.cancel_sleep_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #FF4D4F;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                min-height: 40px;
                text-align: left;
                padding-left: 20px;
                background-image: url(stop.png);
                background-repeat: no-repeat;
                background-position: 120px center;
                background-size: 16px 16px;
            }}
            QPushButton:hover {{
                background-color: #ff7875;
            }}
            QPushButton:pressed {{
                background-color: #d4380d;
            }}
            QPushButton:disabled {{
                background-color: #FFB5B5;
                color: rgba(255, 255, 255, 0.65);
            }}
        """)
        self.cancel_sleep_button.clicked.connect(self.cancel_sleep)
        self.cancel_sleep_button.setEnabled(False)
        sleep_button_layout.addWidget(self.cancel_sleep_button)
        
        sleep_button_layout.addStretch()
        sleep_settings_layout.addLayout(sleep_button_layout)
        
        sleep_layout.addWidget(sleep_card)
        sleep_layout.addStretch()
        
        # 创建设置页面
        settings_page = QWidget()
        settings_page_layout = QVBoxLayout(settings_page)
        settings_page_layout.setSpacing(20)
        settings_page_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建设置卡片
        settings_card = CardFrame()
        settings_card_layout = QVBoxLayout(settings_card)
        settings_card_layout.setSpacing(20)
        settings_card_layout.setContentsMargins(24, 24, 24, 24)
        
        # 开机自启动设置
        self.autostart_button = QPushButton("设置开机自启")
        self.autostart_button.clicked.connect(self.toggle_autostart)
        settings_card_layout.addWidget(self.autostart_button)
        
        settings_page_layout.addWidget(settings_card)
        settings_page_layout.addStretch()
        
        # 将页面添加到堆叠部件
        self.stack.addWidget(reminder_page)
        self.stack.addWidget(sleep_page)
        self.stack.addWidget(settings_page)
        
        content_layout.addWidget(self.stack)
        
        # 添加到主布局
        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)
        
        # 初始化其他变量和设置
        self.reminder_thread = None
        self.reminder_running = False
        self.reminder_window = None
        self.shell = win32com.client.Dispatch("WScript.Shell")
        self.sleep_timer = None
        
        # 设置窗口图标
        self.setWindowIcon(QIcon("icon.ico"))
        
        # 创建并设置系统托盘图标
        self.setup_tray_icon()
        
        # 检查开机自启动状态
        self.check_autostart()
        
        # 设置窗口居中
        self.center_window()
        
        # 设置提醒窗口
        self.setup_reminder_window()

        # 修改启动按钮样式
        self.toggle_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #1890FF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                min-height: 40px;
                text-align: left;
                padding-left: 20px;
                background-image: url(play.png);
                background-repeat: no-repeat;
                background-position: 120px center;
                background-size: 16px 16px;
            }}
            QPushButton:hover {{
                background-color: #40A9FF;
            }}
            QPushButton:pressed {{
                background-color: #096DD9;
            }}
        """)

        # 修改停止按钮样式
        self.stop_button_style = f"""
            QPushButton {{
                background-color: #FF4D4F;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                min-height: 40px;
                text-align: left;
                padding-left: 20px;
                background-image: url(stop.png);
                background-repeat: no-repeat;
                background-position: 120px center;
                background-size: 16px 16px;
            }}
            QPushButton:hover {{
                background-color: #FF7875;
            }}
            QPushButton:pressed {{
                background-color: #D4380D;
            }}
        """

        # 修改卡片样式
        settings_card.setStyleSheet("""
            CardFrame {
                background-color: white;
                border-radius: 8px;
                border: none;
            }
        """)

        # 修改下拉框样式
        self.type_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 4px 12px;
                background-color: white;
                color: {self.colors['text']};
                min-height: 36px;
                font-size: 14px;
            }}
            QComboBox:hover {{
                border: 1px solid {self.colors['primary']};
            }}
            QComboBox:focus {{
                border: 1px solid {self.colors['primary']};
            }}
            QComboBox::drop-down {{
                width: 0;
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                width: 0;
                height: 0;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {self.colors['border']};
                background-color: white;
                color: {self.colors['text']};
                selection-background-color: {self.colors['hover']};
                selection-color: {self.colors['primary']};
            }}
        """)

        # 修改数字输入框样式
        self.interval_spin.setStyleSheet(f"""
            QSpinBox {{
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 4px 12px;
                background-color: white;
                color: {self.colors['text']};
                min-height: 36px;
                font-size: 24px;
                font-weight: 500;
            }}
            QSpinBox:hover {{
                border: 1px solid {self.colors['primary']};
            }}
            QSpinBox:focus {{
                border: 1px solid {self.colors['primary']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 0;
                border: none;
                background: transparent;
            }}
            QSpinBox::up-arrow, QSpinBox::down-arrow {{
                width: 0;
                height: 0;
                border: none;
            }}
        """)

        # 修改时间输入框样式
        self.time_edit.setStyleSheet(f"""
            QTimeEdit {{
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                padding: 4px 12px;
                background-color: white;
                color: {self.colors['text']};
                min-height: 36px;
                font-size: 14px;
            }}
            QTimeEdit:hover {{
                border: 1px solid {self.colors['primary']};
            }}
            QTimeEdit:focus {{
                border: 1px solid {self.colors['primary']};
            }}
            QTimeEdit::up-button, QTimeEdit::down-button {{
                width: 0;
                border: none;
                background: transparent;
            }}
            QTimeEdit::up-arrow, QTimeEdit::down-arrow {{
                width: 0;
                height: 0;
                border: none;
            }}
        """)

    def switch_page(self, index):
        """切换页面"""
        self.stack.setCurrentIndex(index)
        
        # 更新按钮选中状态
        self.reminder_btn.setProperty("selected", index == 0)
        self.sleep_btn.setProperty("selected", index == 1)
        self.settings_btn.setProperty("selected", index == 2)
        
        # 刷新样式
        self.reminder_btn.style().unpolish(self.reminder_btn)
        self.reminder_btn.style().polish(self.reminder_btn)
        self.sleep_btn.style().unpolish(self.sleep_btn)
        self.sleep_btn.style().polish(self.sleep_btn)
        self.settings_btn.style().unpolish(self.settings_btn)
        self.settings_btn.style().polish(self.settings_btn)

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
        if not self.reminder_running:
            self.start_reminder()
        else:
            self.stop_reminder()
            
    def start_reminder(self):
        """开始提醒"""
        self.reminder_running = True
        self.toggle_button.setText("停止专注时段")
        self.toggle_button.setStyleSheet(self.stop_button_style)
        if hasattr(self, 'status_label'):
            self.status_label.setText("提醒已开启")
        self.reminder_thread = threading.Thread(target=self.reminder_loop)
        self.reminder_thread.daemon = True
        self.reminder_thread.start()
        
    def stop_reminder(self):
        """停止提醒"""
        try:
            self.reminder_running = False
            self.toggle_button.setText("启动专注时段")
            self.toggle_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #1890FF;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-size: 14px;
                    min-height: 40px;
                    text-align: left;
                    padding-left: 20px;
                    background-image: url(play.png);
                    background-repeat: no-repeat;
                    background-position: 120px center;
                    background-size: 16px 16px;
                }}
                QPushButton:hover {{
                    background-color: #40A9FF;
                }}
                QPushButton:pressed {{
                    background-color: #096DD9;
                }}
            """)
            if hasattr(self, 'status_label'):
                self.status_label.setText("提醒已停止")
            if self.reminder_thread and self.reminder_thread.is_alive():
                self.reminder_thread.join(timeout=1)
            self.hide_reminder()
        except Exception as e:
            print(f"停止提醒出错: {e}")
        
    def reminder_loop(self):
        """提醒循环"""
        last_reminder_time = datetime.now()
        
        while self.reminder_running:
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
            if not hasattr(self, 'speaker'):
                self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
            
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
                self.autostart_button.setText("设置开机自启")
            except:
                # 如果不存在，则添加
                app_path = os.path.abspath(sys.argv[0])
                winreg.SetValueEx(key, "ReminderApp", 0, winreg.REG_SZ, app_path)
                self.autostart_button.setText("取消开机自启")
                
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
                self.autostart_button.setText("取消开机自启")
            except:
                self.autostart_button.setText("设置开机自启")
                
            winreg.CloseKey(key)
        except:
            self.autostart_button.setText("设置开机自启")
            
    def setup_tray_icon(self):
        """设置系统托盘图标"""
        try:
            self.tray_icon = QSystemTrayIcon(self)
            icon = QIcon("icon.ico")
            if icon.isNull():
                # 如果图标文件不存在，创建一个默认图标
                pixmap = QPixmap(32, 32)
                pixmap.fill(QColor(self.colors['primary']))
                icon = QIcon(pixmap)
            self.tray_icon.setIcon(icon)
            self.tray_icon.setToolTip("提醒助手")
            
            # 创建托盘菜单
            tray_menu = QMenu()
            
            # 添加菜单项
            show_action = tray_menu.addAction("显示主窗口")
            show_action.triggered.connect(self.show_main_window)
            
            tray_menu.addSeparator()
            
            quit_action = tray_menu.addAction("退出程序")
            quit_action.triggered.connect(self.quit_app)
            
            # 设置托盘图标的上下文菜单
            self.tray_icon.setContextMenu(tray_menu)
            
            # 添加托盘图标的双击事件
            self.tray_icon.activated.connect(self.tray_icon_activated)
            
            # 显示托盘图标
            self.tray_icon.show()
        except Exception as e:
            print(f"设置系统托盘图标出错: {e}")
        
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

    def set_sleep(self):
        """设置系统睡眠"""
        minutes = self.sleep_time_spin.value()
        self.sleep_button.setEnabled(False)
        self.cancel_sleep_button.setEnabled(True)
        
        # 创建定时器
        self.sleep_timer = QTimer()
        self.sleep_timer.timeout.connect(self.execute_sleep)
        self.sleep_timer.start(minutes * 60 * 1000)  # 转换为毫秒
        
        QMessageBox.information(self, "睡眠设置", f"系统将在 {minutes} 分钟后进入睡眠模式")
        
    def cancel_sleep(self):
        """取消系统睡眠"""
        if self.sleep_timer:
            self.sleep_timer.stop()
            self.sleep_timer = None
            self.sleep_button.setEnabled(True)
            self.cancel_sleep_button.setEnabled(False)
            QMessageBox.information(self, "睡眠设置", "已取消睡眠设置")
            
    def execute_sleep(self):
        """执行系统睡眠"""
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        self.sleep_button.setEnabled(True)
        self.cancel_sleep_button.setEnabled(False)
        self.sleep_timer = None

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