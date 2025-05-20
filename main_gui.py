import sys
import os
import traceback # traceback 임포트 추가
import winreg # winreg 모듈 임포트 추가
import json # json 모듈 임포트 추가
# import tkinter as tk # Tkinter 제거
# from tkinter import messagebox # Tkinter 제거
# import ttkbootstrap as ttk # ttkbootstrap 제거
# from ttkbootstrap.constants import * # ttkbootstrap 제거

# PyQt5 임포트
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QSlider, QFrame, QSplitter, QStyleFactory,
    QMessageBox, QSystemTrayIcon, QMenu, QAction, QStyle, QCheckBox # QCheckBox 추가
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread, QUrl # QThread, QUrl 추가
from PyQt5.QtGui import QIcon, QDesktopServices # QDesktopServices 추가

# 기존 모듈 임포트 (유지)
from keyboard_listener import KeyboardListener
from sound_player import SoundPlayer
from pynput import keyboard
from mouse_listener import MouseListener

# 작업 스케줄러 모듈 import 추가
import task_scheduler

# --- 리소스 경로 헬퍼 함수 --- #
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Not packaged, use normal path relative to this script
        # __file__ 사용 고려: 현재 파일 위치 기준
        base_path = os.path.abspath(os.path.dirname(__file__))
        # 또는 main.py와 동일하게 os.path.abspath(".") 사용 (실행 위치 기준)
        # base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# --- 헬퍼 함수 끝 --- #

# --- 레지스트리 상수 --- #
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "KeyboardMouseSoundPAAK"
SETTINGS_FOLDER = os.path.join(os.getenv('APPDATA'), APP_NAME)
SETTINGS_FILE = os.path.join(SETTINGS_FOLDER, "settings.json")
# --- 레지스트리 상수 끝 --- #

# --- 상수 정의 (필요시 유지 또는 PyQt5 스타일로 변경) ---
# KEY_ROW_MAP, SPECIAL_KEY_MAP 등은 로직 마이그레이션 시 함께 검토
KEY_ROW_MAP = {
    # 행 0
    'ESC': 0, 'F1': 0, 'F2': 0, 'F3': 0, 'F4': 0, 'F5': 0, 'F6': 0, 'F7': 0, 'F8': 0, 'F9': 0, 'F10': 0, 'F11': 0, 'F12': 0,
    'PRTSC': 0, 'SCROLLLOCK': 0, 'PAUSE': 0,
    # 행 1
    'BACK_QUOTE': 1, '1': 1, '2': 1, '3': 1, '4': 1, '5': 1, '6': 1, '7': 1, '8': 1, '9': 1, '0': 1, 'MINUS': 1, 'EQUALS': 1, 'BACKSPACE': 1,
    'INSERT': 1, 'HOME': 1, 'PGUP': 1,
    'NUMLOCK': 1, 'DIVIDE': 1, 'SUBTRACT': 1, # 숫자패드 ('MULTIPLY' 제거)
    # -- 추가: Numpad Multiply, Add --
    'NUMPAD_MULTIPLY': 1, 'NUMPAD_ADD': 1,
    # 행 2
    'TAB': 2, 'Q': 2, 'W': 2, 'E': 2, 'R': 2, 'T': 2, 'Y': 2, 'U': 2, 'I': 2, 'O': 2, 'P': 2, 'OPEN_BRACKET': 2, 'CLOSE_BRACKET': 2, 'BACK_SLASH': 2,
    'DELETE': 2, 'END': 2, 'PGDN': 2,
    'NUMPAD7': 2, 'NUMPAD8': 2, 'NUMPAD9': 2, # 숫자패드 Add는 행 1로 이동
    # 행 3
    'CAPSLOCK': 3, 'A': 3, 'S': 3, 'D': 3, 'F': 3, 'G': 3, 'H': 3, 'J': 3, 'K': 3, 'L': 3, 'SEMICOLON': 3, 'QUOTE': 3, 'ENTER': 3,
    'NUMPAD4': 3, 'NUMPAD5': 3, 'NUMPAD6': 3, # 숫자패드
    # 행 4 (Bottom Row 포함, kbsim GENERICR4 사용)
    'SHIFT': 4, 'Z': 4, 'X': 4, 'C': 4, 'V': 4, 'B': 4, 'N': 4, 'M': 4, 'COMMA': 4, 'PERIOD': 4, 'SLASH': 4,
    'UP': 4,
    'NUMPAD1': 4, 'NUMPAD2': 4, 'NUMPAD3': 4,
    'CTRL': 4, 'WIN': 4, 'ALT': 4, 'SPACE': 4, # 이전 행 5 -> 행 4 로 변경
    'MENU': 4, 'LEFT': 4, 'DOWN': 4, 'RIGHT': 4, # 이전 행 5 -> 행 4 로 변경
    # -- 추가: 한/영, 한자 키 --
    'HANGUL': 4, 'HANJA': 4,
    'NUMPAD0': 4, 'DECIMAL': 4, # 이전 행 5 -> 행 4 로 변경 (Numpad Enter는 'ENTER'로 매핑되어 행 3 사용)
}

# pynput 특수 키 -> kbsim 키 이름 매핑 (수정됨)
SPECIAL_KEY_MAP = {
    # Function Keys
    keyboard.Key.f1: 'F1', keyboard.Key.f2: 'F2', keyboard.Key.f3: 'F3', keyboard.Key.f4: 'F4',
    keyboard.Key.f5: 'F5', keyboard.Key.f6: 'F6', keyboard.Key.f7: 'F7', keyboard.Key.f8: 'F8',
    keyboard.Key.f9: 'F9', keyboard.Key.f10: 'F10', keyboard.Key.f11: 'F11', keyboard.Key.f12: 'F12',
    # Other Top Row Keys
    keyboard.Key.esc: 'ESC',
    keyboard.Key.print_screen: 'PRTSC', keyboard.Key.scroll_lock: 'SCROLLLOCK', keyboard.Key.pause: 'PAUSE',
    # Editing & Navigation Keys
    keyboard.Key.backspace: 'BACKSPACE', keyboard.Key.insert: 'INSERT', keyboard.Key.home: 'HOME', keyboard.Key.page_up: 'PGUP',
    keyboard.Key.tab: 'TAB', keyboard.Key.delete: 'DELETE', keyboard.Key.end: 'END', keyboard.Key.page_down: 'PGDN',
    keyboard.Key.caps_lock: 'CAPSLOCK', keyboard.Key.enter: 'ENTER', # Main Enter
    # Modifier Keys (Left/Right variants explicitly added)
    keyboard.Key.shift: 'SHIFT', keyboard.Key.shift_l: 'SHIFT', keyboard.Key.shift_r: 'SHIFT',
    keyboard.Key.ctrl: 'CTRL', keyboard.Key.ctrl_l: 'CTRL', keyboard.Key.ctrl_r: 'CTRL',
    keyboard.Key.alt: 'ALT', keyboard.Key.alt_l: 'ALT', keyboard.Key.alt_r: 'ALT', keyboard.Key.alt_gr: 'ALT',
    keyboard.Key.cmd: 'WIN', keyboard.Key.cmd_l: 'WIN', keyboard.Key.cmd_r: 'WIN', # Windows/Command keys
    # Arrow Keys
    keyboard.Key.up: 'UP', keyboard.Key.down: 'DOWN', keyboard.Key.left: 'LEFT', keyboard.Key.right: 'RIGHT',
    # Bottom Row Keys
    keyboard.Key.space: 'SPACE',
    keyboard.Key.menu: 'MENU',
    # Numpad Lock Key
    keyboard.Key.num_lock: 'NUMLOCK',
    # !!! Numpad Keys (Key.kp_*) 제거 -> vk 코드로 처리 !!!
}

# --- 리스너 실행을 위한 QThread --- #
class ListenerThread(QThread):
    """pynput 리스너를 별도 스레드에서 실행하기 위한 클래스"""
    def __init__(self, listener):
        super().__init__()
        self.listener = listener
        self._is_running = True

    def run(self):
        print(f"Starting listener thread: {self.listener.__class__.__name__}")
        try:
            self.listener.start_listening() # pynput 리스너의 블로킹 join/listen
        except Exception as e:
            print(f"!!! EXCEPTION IN LISTENER THREAD ({self.listener.__class__.__name__}) !!!")
            import traceback
            traceback.print_exc() # 콘솔에 직접 트레이스백 출력
        finally:
            print(f"Listener thread finished: {self.listener.__class__.__name__}")

    def stop(self):
        print(f"Stopping listener thread: {self.listener.__class__.__name__}")
        if self.listener:
            self.listener.stop_listening()
        self._is_running = False
        # self.wait() # 종료 대기 (필요시, GUI 멈춤 유발 가능성)

# --- PyQt5 MainWindow 클래스 정의 ---
class MainWindow(QMainWindow):
    # GUI 업데이트를 위한 시그널 정의 (백그라운드 스레드에서 사용)
    update_keyboard_button_signal = pyqtSignal(bool)
    update_mouse_button_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        # --- 애플리케이션 아이콘 경로 가져오기 --- #
        # main.py에서 정의된 ICON_PATH를 가져오거나, 여기서 직접 정의
        # 여기서는 main.py의 경로를 사용한다고 가정 (더 안정적인 방법은 설정 파일 등 사용)
        # self.icon_path = os.path.abspath(os.path.join("assets", "icon.ico")) # 기존 코드
        self.icon_path = resource_path(os.path.join("assets", "icon.ico")) # resource_path 사용

        # --- 인스턴스 변수 초기화 (기존 로직 참고) ---
        self.sound_player = SoundPlayer()
        self.keyboard_listener_thread = None # 스레드 변수 추가
        self.keyboard_listener = None
        self.keyboard_is_running = False
        self.keyboard_selected_pack = "None" # 선택된 팩 이름 저장
        self.keyboard_volume = 100
        self.keyboard_sound_options = self._find_available_keyboard_packs()
        self.mouse_listener_thread = None # 스레드 변수 추가
        self.mouse_listener = None
        self.mouse_is_running = False
        self.mouse_selected_sound = "None" # 선택된 사운드 파일 이름 저장
        self.mouse_volume = 100
        self.mouse_sound_options = self._find_available_mouse_sounds()
        self.pressed_keys = set() # 현재 눌린 키 추적용 집합
        # -------------------------------------------

        self.init_ui()
        self.connect_signals()
        self.init_tray_icon() # 트레이 아이콘 초기화 호출

        # --- 시작 시 자동 시작 상태 확인 및 체크박스 설정 --- #
        try:
            is_startup_enabled = self._check_startup_status()
            self.start_on_boot_checkbox.setChecked(is_startup_enabled)
            print(f"Initial 'Start on Boot' status: {is_startup_enabled}")
        except Exception as e:
            print(f"Error checking startup status: {e}")
            # 오류 발생 시 기본값 false 유지
        # --- 상태 확인 끝 --- #

        # --- 스타일시트 적용 --- #
        self.apply_stylesheet()
        # -----------------------

        # --- 설정 로드 및 적용 --- #
        self._load_settings()
        # --- 설정 로드 끝 --- #

        self.tray_icon.show() # 트레이 아이콘 표시

    def init_tray_icon(self):
        """시스템 트레이 아이콘과 메뉴를 설정합니다."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("Warning: System tray not available.")
            self.tray_icon = None
            return

        # 트레이 아이콘 생성
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(self.icon_path):
            self.tray_icon.setIcon(QIcon(self.icon_path))
            print(f"Tray icon set from: {self.icon_path}")
        else:
            # 표준 아이콘 사용 (경로 없을 시)
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
            print(f"Warning: Icon file not found at {self.icon_path}. Using standard icon.")

        self.tray_icon.setToolTip("KeyboardMouseSoundPAAK - Running")

        # 트레이 아이콘 메뉴 생성
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        exit_action = QAction("Exit", self)

        # 액션 연결
        show_action.triggered.connect(self.show_window)
        exit_action.triggered.connect(self.quit_application) # 안전 종료 메서드 연결

        tray_menu.addAction(show_action)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)

        # 트레이 아이콘 클릭 시그널 연결 (더블 클릭 또는 클릭 시 창 표시)
        self.tray_icon.activated.connect(self.handle_tray_activation)

        self.tray_icon.show() # 트레이 아이콘 표시

    def handle_tray_activation(self, reason):
        """트레이 아이콘 활성화 시 동작 (클릭, 더블클릭 등)"""
        # 왼쪽 버튼 클릭 또는 더블 클릭 시 창 표시
        if reason == QSystemTrayIcon.Trigger or reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def show_window(self):
        """창을 보이게 하고 활성화합니다."""
        self.showNormal() # 최소화 상태에서도 복원
        self.activateWindow() # 창을 앞으로 가져옴
        self.raise_() # 다른 창 위에 표시 (macOS 등에서 필요할 수 있음)

    def quit_application(self):
        """애플리케이션을 안전하게 종료합니다."""
        print("Quit action triggered. Stopping listeners and exiting...")
        # 리스너 스레드 정리 (존재하는 경우)
        if self.keyboard_listener_thread and self.keyboard_listener_thread.isRunning():
            self.keyboard_listener_thread.stop()
            # self.keyboard_listener_thread.wait() # GUI 멈춤 방지를 위해 wait 제거 또는 짧게 설정
        if self.mouse_listener_thread and self.mouse_listener_thread.isRunning():
            self.mouse_listener_thread.stop()
            # self.mouse_listener_thread.wait()

        # 트레이 아이콘 숨기기 (선택 사항, 종료 시 자동으로 제거될 수 있음)
        if self.tray_icon:
            self.tray_icon.hide()

        self._save_settings() # 설정 저장

        QApplication.quit() # QApplication 종료

    def init_ui(self):
        """UI 요소들을 초기화하고 배치합니다."""
        self.setWindowTitle("KeyboardMouseSoundPAAK")
        self.setMinimumSize(500, 200) # 최소 높이 250 -> 200 으로 변경

        # --- 메인 위젯 및 레이아웃 설정 ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # main_layout = QHBoxLayout(central_widget) # 기존 코드 주석처리
        outer_layout = QVBoxLayout(central_widget) # 전체를 감싸는 수직 레이아웃
        outer_layout.setContentsMargins(10, 10, 10, 5) # 전체적인 여백 조정 (하단은 5)

        # --- 기존 좌우 분할 레이아웃 --- # 
        main_layout = QHBoxLayout()
        # 스플리터로 좌우 영역 나누기
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        # 좌우 섹션 생성 및 스플리터에 추가 (기존 코드와 동일)
        # ... (keyboard_frame, mouse_frame 추가하는 부분은 여기에 위치) ...

        # --- 키보드 섹션 (왼쪽) ---
        keyboard_frame = QFrame()
        keyboard_layout = QVBoxLayout(keyboard_frame)
        keyboard_layout.setAlignment(Qt.AlignTop) # 위쪽 정렬
        splitter.addWidget(keyboard_frame)

        # k_title을 인스턴스 변수로 변경
        self.k_title = QLabel("Keyboard Sounds ⌨️")
        self.k_title.setStyleSheet("font-size: 12pt; font-weight: bold;") # 스타일 설정
        self.k_title.setObjectName("TitleLabel") # ObjectName 설정 위치 이동
        keyboard_layout.addWidget(self.k_title)

        # Sound Pack 선택
        k_sound_layout = QHBoxLayout()
        k_sound_label = QLabel("Sound Pack:")
        k_sound_layout.addWidget(k_sound_label)
        k_sound_layout.addSpacing(5) # 레이블과 콤보박스 사이 간격 추가
        self.keyboard_sound_combobox = QComboBox()
        self.keyboard_sound_combobox.addItems(self.keyboard_sound_options)
        if self.keyboard_sound_options and self.keyboard_sound_options[0] != "None":
             self.keyboard_selected_pack = self.keyboard_sound_options[0]
        k_sound_layout.addWidget(self.keyboard_sound_combobox)
        keyboard_layout.addLayout(k_sound_layout)
        keyboard_layout.addSpacing(15) # 사운드 팩 아래 간격 증가 (10 -> 15)

        # Volume 조절
        k_volume_layout = QHBoxLayout()
        k_volume_layout.setContentsMargins(0, 5, 0, 5) # 상하 마진 추가
        k_volume_layout.addWidget(QLabel("Volume:"))
        self.keyboard_volume_slider = QSlider(Qt.Horizontal)
        self.keyboard_volume_slider.setRange(0, 100)
        self.keyboard_volume_slider.setValue(self.keyboard_volume)
        self.keyboard_volume_slider.setMinimumHeight(30) # 슬라이더 최소 높이 설정
        k_volume_layout.addWidget(self.keyboard_volume_slider)
        self.keyboard_volume_label = QLabel(f"{self.keyboard_volume:3d}%")
        k_volume_layout.addWidget(self.keyboard_volume_label)
        keyboard_layout.addLayout(k_volume_layout)
        keyboard_layout.addSpacing(25) # 볼륨 조절 아래 간격 증가

        # 시작/종료 버튼
        k_button_layout = QHBoxLayout()
        self.keyboard_start_button = QPushButton("Start")
        self.keyboard_start_button.setObjectName("StartButton") # ObjectName 설정 위치 이동
        self.keyboard_stop_button = QPushButton("Stop")
        self.keyboard_stop_button.setObjectName("StopButton") # ObjectName 설정 위치 이동
        self.keyboard_stop_button.setEnabled(False)
        k_button_layout.addWidget(self.keyboard_start_button)
        k_button_layout.addWidget(self.keyboard_stop_button)
        keyboard_layout.addLayout(k_button_layout)
        keyboard_layout.addStretch(1) # 버튼 아래 Stretch 다시 추가

        # --- 마우스 섹션 (오른쪽) ---
        mouse_frame = QFrame()
        mouse_layout = QVBoxLayout(mouse_frame)
        mouse_layout.setAlignment(Qt.AlignTop)
        splitter.addWidget(mouse_frame)

        # --- 제목 + 피드백 버튼 레이아웃 --- #
        m_title_layout = QHBoxLayout()
        # --- m_title 정의 추가 --- #
        self.m_title = QLabel("Mouse Sounds 🖱️")
        self.m_title.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.m_title.setObjectName("TitleLabel")
        # --- m_title 정의 끝 --- #
        m_title_layout.addWidget(self.m_title)
        m_title_layout.addStretch(1) # 버튼을 오른쪽으로 밀기

        self.feedback_button = QPushButton("💬")
        self.feedback_button.setToolTip("Send Feedback")
        self.feedback_button.setFlat(True) # 버튼 배경 투명하게
        # self.feedback_button.setFixedSize(25, 25) # 버튼 크기 고정 (임시 주석 처리)
        # 스타일시트 복원 (font-size 제외) + 패딩 제거
        self.feedback_button.setStyleSheet("QPushButton { border: none; padding: 0px; } QPushButton:hover { background-color: #e9ecef; }")
        self.feedback_button.adjustSize() # 내용에 맞게 크기 조정 시도
        m_title_layout.addWidget(self.feedback_button)
        # --- 제목 + 피드백 버튼 레이아웃 끝 --- #

        mouse_layout.addLayout(m_title_layout) # 수정된 제목 레이아웃 추가

        # Click Sound 선택
        m_sound_layout = QHBoxLayout()
        m_sound_label = QLabel("Click Sound:")
        m_sound_layout.addWidget(m_sound_label)
        m_sound_layout.addSpacing(5) # 레이블과 콤보박스 사이 간격 추가
        self.mouse_sound_combobox = QComboBox()
        self.mouse_sound_combobox.addItems(self.mouse_sound_options)
        if self.mouse_sound_options and self.mouse_sound_options[0] != "None":
            self.mouse_selected_sound = self.mouse_sound_options[0]
        m_sound_layout.addWidget(self.mouse_sound_combobox)
        mouse_layout.addLayout(m_sound_layout)
        mouse_layout.addSpacing(15) # 클릭 사운드 아래 간격 증가 (10 -> 15)

        # Volume 조절
        m_volume_layout = QHBoxLayout()
        m_volume_layout.setContentsMargins(0, 5, 0, 5) # 상하 마진 추가
        m_volume_layout.addWidget(QLabel("Volume:"))
        self.mouse_volume_slider = QSlider(Qt.Horizontal)
        self.mouse_volume_slider.setRange(0, 100)
        self.mouse_volume_slider.setValue(self.mouse_volume)
        self.mouse_volume_slider.setMinimumHeight(30) # 슬라이더 최소 높이 설정
        m_volume_layout.addWidget(self.mouse_volume_slider)
        self.mouse_volume_label = QLabel(f"{self.mouse_volume:3d}%")
        m_volume_layout.addWidget(self.mouse_volume_label)
        mouse_layout.addLayout(m_volume_layout)
        mouse_layout.addSpacing(25) # 볼륨 조절 아래 간격 증가

        # 시작/종료 버튼
        m_button_layout = QHBoxLayout()
        self.mouse_start_button = QPushButton("Start")
        self.mouse_start_button.setObjectName("StartButton") # ObjectName 설정 위치 이동
        self.mouse_stop_button = QPushButton("Stop")
        self.mouse_stop_button.setObjectName("StopButton") # ObjectName 설정 위치 이동
        self.mouse_stop_button.setEnabled(False)
        m_button_layout.addWidget(self.mouse_start_button)
        m_button_layout.addWidget(self.mouse_stop_button)
        mouse_layout.addLayout(m_button_layout)
        mouse_layout.addStretch(1) # 버튼 아래 Stretch 다시 추가

        # 스플리터 초기 크기 설정 (비율 조절)
        splitter.setSizes([250, 250])
        # --- 기존 좌우 분할 레이아웃 끝 --- #

        outer_layout.addLayout(main_layout) # 기존 레이아웃을 수직 레이아웃에 추가

        # --- 구분선 추가 --- #
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        outer_layout.addWidget(separator)

        # --- 하단 "Start on Boot" 섹션 --- #
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 5, 0, 0) # 상단 여백만 조금 줌
        self.start_on_boot_checkbox = QCheckBox("Start on Boot")
        bottom_layout.addWidget(self.start_on_boot_checkbox)
        bottom_layout.addStretch(1) # 체크박스를 왼쪽으로 밀착
        outer_layout.addLayout(bottom_layout)
        # --- 하단 섹션 끝 --- #

    def apply_stylesheet(self):
        """애플리케이션에 커스텀 스타일시트를 적용합니다."""
        qss = """
            QMainWindow {
                background-color: #f8f9fa; /* 밝은 배경색 */
            }
            QFrame {
                background-color: #ffffff; /* 프레임 배경 흰색 */
                border-radius: 8px;      /* 둥근 모서리 */
                border: 1px solid #e9ecef; /* 연한 테두리 */
            }
            QLabel {
                font-size: 10pt;         /* 기본 폰트 크기 */
                color: #495057;         /* 약간 어두운 텍스트 색상 */
            }
            QLabel#TitleLabel {
                font-size: 12pt;
                font-weight: bold;
                color: #343a40;
                padding-bottom: 5px;    /* 제목 아래 약간의 여백 */
            }
            QPushButton {
                background-color: #e7f5ff; /* 연한 하늘색 배경 */
                color: #1c7ed6;         /* 파란색 텍스트 */
                border: 1px solid #a5d8ff;
                padding: 6px 12px;
                border-radius: 4px;      /* 약간 둥근 모서리 */
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d0ebff;
                border-color: #74c0fc;
            }
            QPushButton:pressed {
                background-color: #a5d8ff;
            }
            QPushButton:disabled {
                background-color: #6c757d; /* 매우 어두운 회색 배경 */
                color: #dee2e6;         /* 매우 밝은 회색 텍스트 */
                border-color: #495057;   /* 테두리도 어둡게 */
            }
            /* 시작/종료 버튼 색상 차별화 (객체 이름 사용) */
            QPushButton#StartButton {
                 /* 이전: #e6fcf5 (매우 연한 민트) */
                 background-color: #c3fae8; /* 약간 더 진한 민트 */
                 color: #087f5b;         /* 텍스트 색상 유지 */
                 border-color: #63e6be;   /* 테두리 색상 조정 */
            }
            QPushButton#StartButton:hover {
                 /* 이전: #c3fae8 */
                 background-color: #96f2d7;
                 /* 이전: #63e6be */
                 border-color: #38d9a9;   /* 호버 시 테두리 더 진하게 */
            }
            QPushButton#StartButton:pressed {
                 /* 이전: #96f2d7 */
                 background-color: #63e6be;
            }
            /* 비활성화 상태 스타일 추가 */
            QPushButton#StartButton:disabled {
                 background-color: #e0f2f1; /* 연한 민트 계열 회색 */
                 color: #b0bec5;         /* 연한 회색 텍스트 */
                 border-color: #b2dfdb;   /* 조금 더 진한 민트 계열 회색 테두리 */
            }

             QPushButton#StopButton {
                 /* 이전: #fff0f6 (매우 연한 핑크) */
                 background-color: #ffe0e6; /* 약간 더 진한 핑크 */
                 color: #c2255c;         /* 텍스트 색상 유지 */
                 border-color: #faa2c1;   /* 테두리 색상 조정 */
            }
            QPushButton#StopButton:hover {
                 /* 이전: #ffe0e6 */
                 background-color: #fcc2d7;
                 /* 이전: #faa2c1 */
                 border-color: #f783ac;   /* 호버 시 테두리 더 진하게 */
            }
            QPushButton#StopButton:pressed {
                 /* 이전: #fcc2d7 */
                 background-color: #faa2c1;
            }
            /* 비활성화 상태 스타일 추가 */
            QPushButton#StopButton:disabled {
                 background-color: #fce4ec; /* 연한 핑크 계열 회색 */
                 color: #b0bec5;         /* 연한 회색 텍스트 */
                 border-color: #f8bbd0;   /* 조금 더 진한 핑크 계열 회색 테두리 */
            }
            QComboBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                min-height: 20px; /* 최소 높이 설정 */
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #ced4da;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            /* QComboBox::down-arrow 스타일 제거 (아이콘 파일 부재 시 문제 발생 가능) */
            /*
            QComboBox::down-arrow {
                 image: url(assets/down_arrow.png);
                 width: 10px;
                 height: 10px;
            }
            */
             QComboBox:disabled {
                background-color: #f1f3f5;
                color: #adb5bd;
                border-color: #dee2e6;
            }
            QSlider::groove:horizontal {
                border: 1px solid #e9ecef;
                height: 4px; /* Groove 높이 */
                background: #e9ecef;
                margin: 2px 0;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffc0cb; /* 슬라이더 핸들 핑크색 */
                border: 1px solid #f783ac;
                width: 14px; /* 핸들 너비 */
                margin: -5px 0; /* Groove 중앙에 오도록 조정 */
                border-radius: 7px; /* 원형 핸들 */
            }
             QSlider:disabled {
                /* 비활성화 시 슬라이더 스타일 변경 필요 시 추가 */
                background: #f1f3f5; /* Groove 배경만 변경 예시 */
            }
            QSplitter::handle:horizontal {
                background-color: #dee2e6; /* 스플리터 핸들 색상 */
                width: 1px;
                margin: 2px 0;
            }
        """
        self.setStyleSheet(qss)

        # 위젯에 ObjectName 설정 (init_ui로 이동됨)
        # self.k_title.setObjectName("TitleLabel")
        # self.m_title.setObjectName("TitleLabel")
        # self.keyboard_start_button.setObjectName("StartButton")
        # self.keyboard_stop_button.setObjectName("StopButton")
        # self.mouse_start_button.setObjectName("StartButton")
        # self.mouse_stop_button.setObjectName("StopButton")

    # --- 창 중앙 정렬 메서드 --- #
    def center_window(self):
        """애플리케이션 창을 화면 중앙으로 이동시킵니다."""
        try:
            # 창의 현재 지오메트리 정보 가져오기
            qr = self.frameGeometry()
            # 사용 가능한 화면의 중앙 지점 가져오기 (QDesktopWidget 사용)
            cp = QApplication.desktop().availableGeometry().center()
            # 창의 중앙 지점을 화면의 중앙 지점으로 이동
            qr.moveCenter(cp)
            self.move(qr.topLeft())
        except Exception as e:
            print(f"Warning: Could not center window: {e}")
    # --------------------------

    # --- showEvent 재정의 --- #
    def showEvent(self, event):
        """창이 처음 표시될 때 중앙 정렬을 수행합니다."""
        super().showEvent(event) # 부모 클래스의 showEvent 호출
        # 한 번만 실행되도록 플래그 사용 (선택적)
        if not hasattr(self, '_centered') or not self._centered:
            self.center_window()
            self._centered = True # 실행 플래그 설정
    # ------------------------

    def connect_signals(self):
        """위젯의 시그널을 슬롯(메서드)에 연결합니다."""
        # 키보드 사운드팩 변경
        self.keyboard_sound_combobox.currentTextChanged.connect(self._keyboard_pack_changed)
        # 키보드 볼륨
        self.keyboard_volume_slider.valueChanged.connect(self._update_keyboard_volume)
        # 키보드 시작/종료
        self.keyboard_start_button.clicked.connect(self.start_keyboard_sound)
        self.keyboard_stop_button.clicked.connect(self.stop_keyboard_sound)
        # 키보드 GUI 업데이트 시그널
        self.update_keyboard_button_signal.connect(self._update_keyboard_button_state)

        # 마우스 사운드 변경
        self.mouse_sound_combobox.currentTextChanged.connect(self._mouse_sound_changed)
        # 마우스 볼륨
        self.mouse_volume_slider.valueChanged.connect(self._update_mouse_volume)
        # 마우스 시작/종료
        self.mouse_start_button.clicked.connect(self.start_mouse_sound)
        self.mouse_stop_button.clicked.connect(self.stop_mouse_sound)
        # 마우스 GUI 업데이트 시그널
        self.update_mouse_button_signal.connect(self._update_mouse_button_state)

        # 피드백 버튼 클릭
        self.feedback_button.clicked.connect(self._open_feedback_link)

        # 시작 시 부팅 체크박스
        self.start_on_boot_checkbox.stateChanged.connect(self._toggle_start_on_boot)

    # --- 슬롯(콜백) 메서드 --- #
    def _keyboard_pack_changed(self, pack_name):
        self.keyboard_selected_pack = pack_name
        print(f"Keyboard pack selection changed to: {pack_name}")

    def _mouse_sound_changed(self, sound_name):
        self.mouse_selected_sound = sound_name
        print(f"Mouse sound selection changed to: {sound_name}")

    def _update_keyboard_volume(self, value):
        self.keyboard_volume = value
        self.keyboard_volume_label.setText(f"{value:3d}%")
        # if self.sound_player: # SoundPlayer에 해당 메서드 없으므로 제거
        #     self.sound_player.set_keyboard_volume(value)

    def _update_mouse_volume(self, value):
        self.mouse_volume = value
        self.mouse_volume_label.setText(f"{value:3d}%")
        # if self.sound_player: # SoundPlayer에 해당 메서드 없으므로 제거
        #      self.sound_player.set_mouse_volume(value)

    def _update_keyboard_button_state(self, is_running):
        """키보드 시작/종료 버튼 상태 업데이트 (시그널로부터 호출됨)"""
        self.keyboard_start_button.setEnabled(not is_running)
        self.keyboard_stop_button.setEnabled(is_running)
        self.keyboard_sound_combobox.setEnabled(not is_running)

    def _update_mouse_button_state(self, is_running):
        """마우스 시작/종료 버튼 상태 업데이트 (시그널로부터 호출됨)"""
        self.mouse_start_button.setEnabled(not is_running)
        self.mouse_stop_button.setEnabled(is_running)
        self.mouse_sound_combobox.setEnabled(not is_running)

    def _toggle_start_on_boot(self, state):
        """'Start on Boot' 체크박스 상태 변경 시 호출됩니다."""
        is_checked = (state == Qt.Checked)
        print(f"'Start on Boot' checkbox toggled: {is_checked}")
        
        if is_checked:
            try:
                # 패키징된 .exe 상태에서만 등록 가능
                if not getattr(sys, 'frozen', False):
                    print("Not running as a frozen executable. Skipping add to startup.")
                    QMessageBox.warning(self, "Warning", "Start on Boot can only be enabled for the packaged (.exe) version.")
                    self.start_on_boot_checkbox.setChecked(False)
                    return
                
                # 작업 스케줄러에 관리자 권한으로 실행되도록 등록
                executable_path = sys.executable
                if task_scheduler.create_admin_task(executable_path, "--background"):
                    print("Successfully added to task scheduler with admin privileges.")
                else:
                    print("Failed to add to task scheduler.")
                    QMessageBox.critical(self, "Error", 
                        "Failed to register with Task Scheduler. Try running as administrator.")
                    self.start_on_boot_checkbox.setChecked(False)
            except Exception as e:
                print(f"Error adding to task scheduler: {e}")
                QMessageBox.critical(self, "Error", f"Unexpected error enabling Start on Boot.\n{e}")
                self.start_on_boot_checkbox.setChecked(False)
        else:
            try:
                # 작업 스케줄러에서 제거
                if task_scheduler.remove_task():
                    print("Successfully removed from task scheduler.")
                else:
                    print("Failed to remove from task scheduler.")
                    QMessageBox.warning(self, "Warning", 
                        "Failed to remove from Task Scheduler. Try running as administrator.")
            except Exception as e:
                print(f"Error removing from task scheduler: {e}")
                QMessageBox.critical(self, "Error", f"Unexpected error disabling Start on Boot.\n{e}")

    def _check_startup_status(self):
        """애플리케이션이 작업 스케줄러에 등록되어 있는지 확인합니다."""
        try:
            # 작업 스케줄러에서 상태 확인
            return task_scheduler.is_task_exists()
        except Exception as e:
            print(f"Error checking task scheduler status: {e}")
            return False

    def _open_feedback_link(self):
        """피드백 링크를 기본 웹 브라우저에서 엽니다."""
        feedback_url = QUrl("https://github.com/htpaak/KeyboardMouseSoundPAAK/discussions")
        print(f"Opening feedback link: {feedback_url.toString()}")
        QDesktopServices.openUrl(feedback_url)

    def start_keyboard_sound(self):
        if self.keyboard_is_running:
            return

        if self.keyboard_selected_pack == "None" or not self.keyboard_selected_pack:
             QMessageBox.warning(self, "Warning", "Please select a valid sound pack for the keyboard.")
             return

        # 선택된 사운드 팩 미리 로드
        print(f"Loading sound pack: {self.keyboard_selected_pack}...")
        if not self.sound_player.load_sound_pack(self.keyboard_selected_pack):
            QMessageBox.critical(self, "Error", f"Failed to load sound pack '{self.keyboard_selected_pack}'. Check logs.")
            return
        print(f"Sound pack '{self.keyboard_selected_pack}' loaded.")
        # self.sound_player.set_keyboard_volume(self.keyboard_volume) # 시작 시 볼륨 설정 (SoundPlayer에 해당 메서드 없으므로 제거)

        # 키보드 리스너 시작 (스레드 사용)
        try:
            print("Creating KeyboardListener...")
            # --- 리스너/스레드 시작 부분 다시 활성화 ---
            self.keyboard_listener = KeyboardListener(
                on_press_callback=self._handle_key_press,
                on_release_callback=self._handle_key_release
            )
            print("Creating ListenerThread for KeyboardListener...")
            self.keyboard_listener_thread = ListenerThread(self.keyboard_listener)
            print("Starting KeyboardListener thread...")
            self.keyboard_listener_thread.start()
            # -------------------------------------------
            # print("!!! Keyboard listener/thread start TEMPORARILY DISABLED for debugging !!!") # 임시 로그 제거

            self.keyboard_is_running = True # 상태는 True로 설정
            print(f"Keyboard listening started with sound pack: '{self.keyboard_selected_pack}', Volume: {self.keyboard_volume}%") # 로그 메시지 원래대로
            self.update_keyboard_button_signal.emit(self.keyboard_is_running)

        except Exception as e:
             QMessageBox.critical(self, "Error", f"Failed to start keyboard listener: {e}\n{traceback.format_exc()}") # 로그 메시지 원래대로
             # if self.keyboard_listener_thread and self.keyboard_listener_thread.isRunning(): # 실패 시 스레드 정리 로직 복원
             #     self.keyboard_listener_thread.stop()
             self.keyboard_listener_thread = None
             self.keyboard_listener = None
             self.keyboard_is_running = False
             self.update_keyboard_button_signal.emit(self.keyboard_is_running)

    def stop_keyboard_sound(self):
        if not self.keyboard_is_running:
            return

        print("Stopping KeyboardListener thread...") # 로그 메시지 원래대로
        # --- 리스너/스레드 중지 부분 다시 활성화 ---
        if self.keyboard_listener_thread:
            self.keyboard_listener_thread.stop()
            # self.keyboard_listener_thread.wait() # 필요 시 대기
            self.keyboard_listener_thread = None
        # -------------------------------------------

        self.keyboard_listener = None # 리스너 객체도 제거
        self.keyboard_is_running = False
        print("Keyboard listening stopped.") # 로그 메시지 원래대로
        self.update_keyboard_button_signal.emit(self.keyboard_is_running)
        # 언로드는 앱 종료 시에만?
        # if self.sound_player:
        #     self.sound_player.unload_pack(self.keyboard_selected_pack)

    # --- start/stop mouse sound (구현) ---
    def start_mouse_sound(self):
        if self.mouse_is_running:
            return

        if self.mouse_selected_sound == "None" or not self.mouse_selected_sound:
            QMessageBox.warning(self, "Warning", "Please select a valid click sound for the mouse.")
            return

        # 선택된 마우스 사운드 로드 시도
        print(f"Loading mouse sound: {self.mouse_selected_sound}...")
        if not self.sound_player.load_mouse_sound(self.mouse_selected_sound):
            QMessageBox.critical(self, "Error", f"Failed to load mouse sound '{self.mouse_selected_sound}'. Check logs.")
            return
        print(f"Mouse sound '{self.mouse_selected_sound}' loaded.")
        # self.sound_player.set_mouse_volume(self.mouse_volume) # 시작 시 볼륨 설정 (메서드 없음)

        # 마우스 리스너 시작 (스레드 사용)
        try:
            print("Creating MouseListener...")
            self.mouse_listener = MouseListener(on_click_callback=self._handle_mouse_click)
            print("Creating ListenerThread for MouseListener...")
            self.mouse_listener_thread = ListenerThread(self.mouse_listener)
            print("Starting MouseListener thread...")
            self.mouse_listener_thread.start()
            self.mouse_is_running = True
            print(f"Mouse listening started with sound: '{self.mouse_selected_sound}', Volume: {self.mouse_volume}%")
            self.update_mouse_button_signal.emit(self.mouse_is_running)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start mouse listener: {e}\n{traceback.format_exc()}")
            if self.mouse_listener_thread and self.mouse_listener_thread.isRunning():
                self.mouse_listener_thread.stop()
            self.mouse_listener_thread = None
            self.mouse_listener = None
            self.mouse_is_running = False
            self.update_mouse_button_signal.emit(self.mouse_is_running)

    def stop_mouse_sound(self):
        if not self.mouse_is_running:
            return

        print("Stopping MouseListener thread...")
        if self.mouse_listener_thread:
            self.mouse_listener_thread.stop()
            # self.mouse_listener_thread.wait()
            self.mouse_listener_thread = None

            self.mouse_listener = None
        self.mouse_is_running = False
        print("Mouse listening stopped.")
        self.update_mouse_button_signal.emit(self.mouse_is_running)

    # --- 사운드 파일/팩 검색 (기존 로직 유지) ---
    def _find_available_keyboard_packs(self):
        # base_dir = os.path.join("src", "keyboard") # 기존 코드
        base_dir = resource_path(os.path.join("src", "keyboard")) # resource_path 사용
        if not os.path.isdir(base_dir):
            print(f"[WARN] Keyboard sound directory not found: {base_dir}")
            return ["None"]
        available_packs = [item for item in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, item)) and (os.path.isdir(os.path.join(base_dir, item, "press")) or os.path.isdir(os.path.join(base_dir, item, "release")))]
        return ["None"] + available_packs if available_packs else ["None"]

    def _find_available_mouse_sounds(self):
        # base_dir = os.path.join("src", "mouse") # 기존 코드
        base_dir = resource_path(os.path.join("src", "mouse")) # resource_path 사용
        if not os.path.isdir(base_dir):
            print(f"[WARN] Mouse sound directory not found: {base_dir}")
            return ["None"]
        valid_extensions = (".wav", ".mp3", ".ogg")
        # 확장자 제외한 파일 이름만 가져오도록 수정
        available_sounds = [os.path.splitext(f)[0] for f in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, f)) and f.lower().endswith(valid_extensions)]
        # 중복 제거 (선택적이지만 권장)
        available_sounds = sorted(list(set(available_sounds)))
        return ["None"] + available_sounds if available_sounds else ["None"]

    # --- 키/마우스 이벤트 핸들러 --- #
    def _handle_key_press(self, key):
        if self.keyboard_is_running and self.sound_player:
            key_name = self._key_to_filename(key)
            # 키가 유효하고, 아직 눌린 상태가 아닐 때만 처리
            if key_name and key_name not in self.pressed_keys:
                self.pressed_keys.add(key_name) # 눌린 키 집합에 추가
                row_index = KEY_ROW_MAP.get(key_name, None)
                effective_row = 4 if row_index is None or row_index > 4 else row_index
                self.sound_player.play_key_sound(
                    self.keyboard_selected_pack,
                    "press",
                    key_name,
                    self.keyboard_volume,
                    row_index=effective_row
                )
            # else: # 디버깅용: 반복 입력 무시 로그
            #     if key_name:
            #         print(f"Key '{key_name}' already pressed, ignoring repeat.")

    def _handle_key_release(self, key):
        if self.keyboard_is_running and self.sound_player:
            key_name = self._key_to_filename(key)
            # 키가 유효하고, 눌린 상태였을 때만 처리
            if key_name and key_name in self.pressed_keys:
                self.pressed_keys.remove(key_name) # 눌린 키 집합에서 제거
                self.sound_player.play_key_sound(
                    self.keyboard_selected_pack,
                    "release",
                    key_name,
                    self.keyboard_volume
                )
            # else: # 디버깅용: 예상치 못한 release 이벤트 로그
            #     if key_name:
            #         print(f"Key '{key_name}' released but wasn't in pressed_keys set.")

    def _handle_mouse_click(self, x, y, button, pressed):
        # TODO: 마우스 기능 구현 시 필요
        if self.mouse_is_running and pressed and self.sound_player:
            print(f"Mouse clicked: {button}")
            if self.mouse_selected_sound and self.mouse_selected_sound != "None":
                self.sound_player.play_mouse_click_sound(
                     self.mouse_selected_sound,
                     self.mouse_volume
                )
        pass

    # --- _key_to_filename (기존 로직 복사) --- #
    def _key_to_filename(self, key):
        """pynput 키 객체를 KEY_ROW_MAP에서 사용할 키 이름 문자열(대문자)로 변환합니다.
           로직 순서 변경: SPECIAL_KEY_MAP -> Numpad vk -> char -> 기타 vk
        """
        # 1. 특수 키 처리 (SPECIAL_KEY_MAP 우선)
        if key in SPECIAL_KEY_MAP:
            return SPECIAL_KEY_MAP[key]

        # --- 로직 변경: vk 기반 처리를 char 처리보다 먼저 수행 --- #

        # 2. vk (Virtual Keycode) 기반 처리
        if hasattr(key, 'vk'):
            vk = key.vk
            # print(f"Detected vk: {vk}") # vk 코드 확인용 디버깅

            # 2-1. Numpad 0-9 (vk 96-105)
            if 96 <= vk <= 105:
                return f'NUMPAD{vk - 96}'
            # 2-2. Numpad Operators & Decimal
            if vk == 106: return 'NUMPAD_MULTIPLY' # *
            if vk == 107: return 'NUMPAD_ADD'      # +
            if vk == 109: return 'SUBTRACT' # -
            if vk == 110: return 'DECIMAL'  # .
            if vk == 111: return 'DIVIDE'   # /
            # Numpad Enter(vk 13)는 SPECIAL_KEY_MAP에서 Key.enter로 처리됨

            # --- 추가: NumLock 켜진 상태의 Numpad 5 (사용자 로그 기반 vk=12) ---
            if vk == 12: return 'NUMPAD5'

            # 2-3. 기타 vk 기반 키 (Numpad 외)
            # 한/영(vk 21), 한자(vk 25)
            if vk == 21: return 'HANGUL'
            if vk == 25: return 'HANJA'
            # NumLock(vk 144)은 SPECIAL_KEY_MAP에서 Key.num_lock으로 처리됨

            # 여기에 다른 vk 기반 키가 필요하면 추가 (예: 미디어 키 등)
            # print(f"vk {vk} not explicitly handled yet.")

        # --- vk 로 처리되지 않은 경우, char 기반 처리 시도 --- #

        # 3. 문자/숫자 키 처리 (char가 있고 vk로 처리되지 않은 경우)
        if hasattr(key, 'char') and key.char is not None:
            char = key.char
            # 알파벳
            if 'a' <= char.lower() <= 'z': return char.upper()
            # 숫자 및 기호 (Shift 조합 포함)
            # Note: 세미콜론(;)은 파이썬에서 명령 구분자로 사용되지 않으므로 elif로 수정
            if char == '`': return 'BACK_QUOTE'
            elif char == '!': return '1'
            elif char == '@': return '2'
            elif char == '#': return '3'
            elif char == '$': return '4'
            elif char == '%': return '5'
            elif char == '^': return '6'
            elif char == '&': return '7'
            elif char == '*': return '8' # Numpad *는 vk 106에서 처리됨
            elif char == '(': return '9'
            elif char == ')': return '0'
            elif char == '_': return 'MINUS'
            elif char == '+': return 'EQUALS' # Numpad +는 vk 107에서 처리됨
            elif char == '1': return '1'
            elif char == '2': return '2'
            elif char == '3': return '3'
            elif char == '4': return '4'
            elif char == '5': return '5'
            elif char == '6': return '6'
            elif char == '7': return '7'
            elif char == '8': return '8'
            elif char == '9': return '9'
            elif char == '0': return '0'
            elif char == '-': return 'MINUS' # Numpad -는 vk 109에서 처리됨
            elif char == '=': return 'EQUALS'
            elif char == '[': return 'OPEN_BRACKET'
            elif char == ']': return 'CLOSE_BRACKET'
            elif char == '\\': return 'BACK_SLASH'
            elif char == ';': return 'SEMICOLON'
            elif char == '\'': return 'QUOTE'
            elif char == ',': return 'COMMA'
            elif char == '.': return 'PERIOD' # Numpad .는 vk 110에서 처리됨
            elif char == '/': return 'SLASH' # Numpad /는 vk 111에서 처리됨

            # char는 있지만 위에서 처리되지 않은 경우 (아마 없을 것으로 예상)
            # print(f"Unhandled char: {char}")
            return None

        # 최종적으로 매핑되지 않은 키 (vk도 없고 char도 없는 특수키 등)
        # print(f"Unmapped key: {key} (vk={getattr(key, 'vk', None)}, char={getattr(key, 'char', None)})")
        return None

    # --- 애플리케이션 종료 처리 --- #
    def closeEvent(self, event):
        """창 닫기 이벤트 처리 (트레이로 최소화)"""
        if self.tray_icon and self.tray_icon.isVisible():
            # 트레이 아이콘이 존재하고 보이면, 창을 숨기고 트레이 메시지 표시
            event.ignore() # 기본 닫기 동작 취소
            self.hide()
            self.tray_icon.showMessage(
                "KeyboardMouseSoundPAAK",
                "Application minimized to tray.",
                QSystemTrayIcon.Information, # 아이콘 타입
                2000 # 메시지 표시 시간 (ms)
            )
            print("Window hidden to system tray.")
        else:
            # 트레이 아이콘이 없거나 보이지 않으면, 기본 닫기 동작 수행 (종료)
            print("No tray icon or not visible, performing default close.")
            self.quit_application() # 기본 닫기 대신 안전 종료 호출

    def on_closing(self):
        """애플리케이션 종료 시 리스너를 중지합니다."""
        print("Closing application...")
        if self.keyboard_listener_thread and self.keyboard_is_running:
            self.stop_keyboard_sound()
        if self.mouse_listener_thread and self.mouse_is_running: # 스레드 변수 확인
            self.stop_mouse_sound()
        if self.sound_player:
             self.sound_player.unload() # 앱 종료 시 모든 사운드 언로드

    # --- 설정 저장/로드 메서드 --- #
    def _save_settings(self):
        """현재 설정을 JSON 파일에 저장합니다."""
        settings = {
            "keyboard_pack": self.keyboard_sound_combobox.currentText(),
            "keyboard_volume": self.keyboard_volume_slider.value(),
            "keyboard_running": self.keyboard_is_running,
            "mouse_sound": self.mouse_sound_combobox.currentText(),
            "mouse_volume": self.mouse_volume_slider.value(),
            "mouse_running": self.mouse_is_running,
            "start_on_boot": self.start_on_boot_checkbox.isChecked()
        }
        try:
            os.makedirs(SETTINGS_FOLDER, exist_ok=True) # 설정 폴더 생성
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            print(f"Settings saved to {SETTINGS_FILE}")
        except Exception as e:
            print(f"Error saving settings: {e}")
            # 여기서 사용자에게 오류 알림은 생략 (종료 시점)

    def _load_settings(self):
        """JSON 파일에서 설정을 로드하고 UI에 적용합니다."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                print(f"Settings loaded from {SETTINGS_FILE}")

                # UI 요소 업데이트
                self.keyboard_sound_combobox.setCurrentText(settings.get("keyboard_pack", "None"))
                self.keyboard_volume_slider.setValue(settings.get("keyboard_volume", 100))
                # self.keyboard_volume_label 업데이트는 슬라이더 signal 처리기에 의해 자동으로 될 것임

                self.mouse_sound_combobox.setCurrentText(settings.get("mouse_sound", "None"))
                self.mouse_volume_slider.setValue(settings.get("mouse_volume", 100))
                # self.mouse_volume_label 업데이트는 슬라이더 signal 처리기에 의해 자동으로 될 것임

                # 시작 시 부팅 상태는 레지스트리 확인 결과를 우선으로 할 수 있음
                # 여기서는 설정 파일 값을 따르도록 함 (레지스트리 상태와 다를 경우 동기화 문제 가능성 있음)
                # self.start_on_boot_checkbox.setChecked(settings.get("start_on_boot", False))
                # -> __init__ 에서 레지스트리 체크 후 설정하는 로직 유지하고 여기서는 로드만
                stored_start_on_boot = settings.get("start_on_boot", False)
                # print(f"  Loaded start_on_boot setting: {stored_start_on_boot}")
                # 실제 체크박스 설정은 __init__에서 레지스트리 확인 후 진행

                # 저장된 실행 상태에 따라 리스너 자동 시작
                if settings.get("keyboard_running", False):
                    print("  -> Automatically starting keyboard listener based on saved state.")
                    self.start_keyboard_sound()

                if settings.get("mouse_running", False):
                    print("  -> Automatically starting mouse listener based on saved state.")
                    self.start_mouse_sound()

            else:
                print(f"Settings file not found ({SETTINGS_FILE}). Using default values.")

        except json.JSONDecodeError as e:
            print(f"Error decoding settings file ({SETTINGS_FILE}): {e}. Using default values.")
        except Exception as e:
            print(f"Error loading settings: {e}. Using default values.")

# --- 기존 if __name__ == "__main__" 블록은 main.py로 이동했으므로 제거 --- 