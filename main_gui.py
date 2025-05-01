import sys
import os
import traceback # traceback 임포트 추가
# import tkinter as tk # Tkinter 제거
# from tkinter import messagebox # Tkinter 제거
# import ttkbootstrap as ttk # ttkbootstrap 제거
# from ttkbootstrap.constants import * # ttkbootstrap 제거

# PyQt5 임포트
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QSlider, QFrame, QSplitter, QStyleFactory,
    QMessageBox # QMessageBox 추가
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread # QThread 추가
from PyQt5.QtGui import QIcon

# 기존 모듈 임포트 (유지)
from keyboard_listener import KeyboardListener
from sound_player import SoundPlayer
from pynput import keyboard
from mouse_listener import MouseListener

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
        # -------------------------------------------

        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """UI 요소들을 초기화하고 배치합니다."""
        self.setWindowTitle("🎧 Sound Input Fun! 🖱️")
        self.setMinimumSize(500, 250) # 최소 크기 설정 (조절 가능)

        # --- 메인 위젯 및 레이아웃 설정 ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 스플리터로 좌우 영역 나누기
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # --- 키보드 섹션 (왼쪽) ---
        keyboard_frame = QFrame()
        keyboard_layout = QVBoxLayout(keyboard_frame)
        keyboard_layout.setAlignment(Qt.AlignTop) # 위쪽 정렬
        splitter.addWidget(keyboard_frame)

        k_title = QLabel("Keyboard Sounds ⌨️")
        k_title.setStyleSheet("font-size: 12pt; font-weight: bold;") # 스타일 설정
        keyboard_layout.addWidget(k_title)

        # Sound Pack 선택
        k_sound_layout = QHBoxLayout()
        k_sound_layout.addWidget(QLabel("Sound Pack:"))
        self.keyboard_sound_combobox = QComboBox()
        self.keyboard_sound_combobox.addItems(self.keyboard_sound_options)
        if self.keyboard_sound_options and self.keyboard_sound_options[0] != "None":
             self.keyboard_selected_pack = self.keyboard_sound_options[0]
        k_sound_layout.addWidget(self.keyboard_sound_combobox)
        keyboard_layout.addLayout(k_sound_layout)

        # Volume 조절
        k_volume_layout = QHBoxLayout()
        k_volume_layout.addWidget(QLabel("Volume:"))
        self.keyboard_volume_slider = QSlider(Qt.Horizontal)
        self.keyboard_volume_slider.setRange(0, 100)
        self.keyboard_volume_slider.setValue(self.keyboard_volume)
        k_volume_layout.addWidget(self.keyboard_volume_slider)
        self.keyboard_volume_label = QLabel(f"{self.keyboard_volume:3d}%")
        k_volume_layout.addWidget(self.keyboard_volume_label)
        keyboard_layout.addLayout(k_volume_layout)

        # 시작/종료 버튼
        k_button_layout = QHBoxLayout()
        self.keyboard_start_button = QPushButton("Start")
        self.keyboard_stop_button = QPushButton("Stop")
        self.keyboard_stop_button.setEnabled(False)
        k_button_layout.addWidget(self.keyboard_start_button)
        k_button_layout.addWidget(self.keyboard_stop_button)
        keyboard_layout.addLayout(k_button_layout)

        # --- 마우스 섹션 (오른쪽) ---
        mouse_frame = QFrame()
        mouse_layout = QVBoxLayout(mouse_frame)
        mouse_layout.setAlignment(Qt.AlignTop)
        splitter.addWidget(mouse_frame)

        m_title = QLabel("Mouse Sounds 🖱️")
        m_title.setStyleSheet("font-size: 12pt; font-weight: bold;")
        mouse_layout.addWidget(m_title)

        # Click Sound 선택
        m_sound_layout = QHBoxLayout()
        m_sound_layout.addWidget(QLabel("Click Sound:"))
        self.mouse_sound_combobox = QComboBox()
        self.mouse_sound_combobox.addItems(self.mouse_sound_options)
        if self.mouse_sound_options and self.mouse_sound_options[0] != "None":
            self.mouse_selected_sound = self.mouse_sound_options[0]
        m_sound_layout.addWidget(self.mouse_sound_combobox)
        mouse_layout.addLayout(m_sound_layout)

        # Volume 조절
        m_volume_layout = QHBoxLayout()
        m_volume_layout.addWidget(QLabel("Volume:"))
        self.mouse_volume_slider = QSlider(Qt.Horizontal)
        self.mouse_volume_slider.setRange(0, 100)
        self.mouse_volume_slider.setValue(self.mouse_volume)
        m_volume_layout.addWidget(self.mouse_volume_slider)
        self.mouse_volume_label = QLabel(f"{self.mouse_volume:3d}%")
        m_volume_layout.addWidget(self.mouse_volume_label)
        mouse_layout.addLayout(m_volume_layout)

        # 시작/종료 버튼
        m_button_layout = QHBoxLayout()
        self.mouse_start_button = QPushButton("Start")
        self.mouse_stop_button = QPushButton("Stop")
        self.mouse_stop_button.setEnabled(False)
        m_button_layout.addWidget(self.mouse_start_button)
        m_button_layout.addWidget(self.mouse_stop_button)
        mouse_layout.addLayout(m_button_layout)

        # 스플리터 초기 크기 설정 (비율 조절)
        splitter.setSizes([250, 250])

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
        if self.sound_player:
            self.sound_player.set_keyboard_volume(value) # SoundPlayer에 해당 메서드 필요

    def _update_mouse_volume(self, value):
        self.mouse_volume = value
        self.mouse_volume_label.setText(f"{value:3d}%")
        if self.sound_player:
             self.sound_player.set_mouse_volume(value) # SoundPlayer에 해당 메서드 필요

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
        base_dir = os.path.join("src", "keyboard")
        if not os.path.isdir(base_dir):
            print(f"[WARN] Keyboard sound directory not found: {base_dir}")
            return ["None"]
        available_packs = [item for item in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, item)) and (os.path.isdir(os.path.join(base_dir, item, "press")) or os.path.isdir(os.path.join(base_dir, item, "release")))]
        return ["None"] + available_packs if available_packs else ["None"]

    def _find_available_mouse_sounds(self):
        base_dir = os.path.join("src", "mouse")
        if not os.path.isdir(base_dir):
            print(f"[WARN] Mouse sound directory not found: {base_dir}")
            return ["None"]
        valid_extensions = (".wav", ".mp3", ".ogg")
        available_sounds = [f for f in os.listdir(base_dir) if os.path.isfile(os.path.join(base_dir, f)) and f.lower().endswith(valid_extensions)]
        return ["None"] + available_sounds if available_sounds else ["None"]

    # --- 키/마우스 이벤트 핸들러 --- #
    def _handle_key_press(self, key):
        if self.keyboard_is_running and self.sound_player:
            key_name = self._key_to_filename(key)
            if key_name:
                row_index = KEY_ROW_MAP.get(key_name, None)
                effective_row = 4 if row_index is None or row_index > 4 else row_index
                self.sound_player.play_key_sound(
                    self.keyboard_selected_pack,
                    "press",
                    key_name,
                    self.keyboard_volume,
                    row_index=effective_row
                )

    def _handle_key_release(self, key):
        if self.keyboard_is_running and self.sound_player:
            key_name = self._key_to_filename(key)
            if key_name:
                self.sound_player.play_key_sound(
                    self.keyboard_selected_pack,
                    "release",
                    key_name,
                    self.keyboard_volume
                )

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
        """QMainWindow의 closeEvent를 오버라이드합니다."""
        self.on_closing()
        event.accept()

    def on_closing(self):
        """애플리케이션 종료 시 리스너를 중지합니다."""
        print("Closing application...")
        if self.keyboard_listener_thread and self.keyboard_is_running:
            self.stop_keyboard_sound()
        if self.mouse_listener_thread and self.mouse_is_running: # 스레드 변수 확인
            self.stop_mouse_sound()
        if self.sound_player:
             self.sound_player.unload() # 앱 종료 시 모든 사운드 언로드

# --- 기존 if __name__ == "__main__" 블록은 main.py로 이동했으므로 제거 --- 