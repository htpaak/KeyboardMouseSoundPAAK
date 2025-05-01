import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os

# 모듈 임포트
from keyboard_listener import KeyboardListener
from sound_player import SoundPlayer
from pynput import keyboard
from mouse_listener import MouseListener

# --- 키-행(Row) 매핑 (kbsim-master KLE 분석 기반) ---
# 표준 QWERTY 레이아웃 및 kbsim 프리셋 기준
# 참고: kbsim은 행 5 이상을 기본적으로 행 4(GENERIC_R4)로 처리함
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

class KeyboardSoundApp:
    def __init__(self, master):
        self.master = master
        master.title("Sound Input Simulator") # 제목 변경
        master.resizable(False, False) # 창 크기 조절 비활성화

        # --- 창 크기 계산 로직 (나중에 배치 후 다시 계산 필요) --- #
        # master.update_idletasks()
        # window_width = master.winfo_width()
        # window_height = master.winfo_height()
        # screen_width = master.winfo_screenwidth()
        # screen_height = master.winfo_screenheight()
        # center_x = int(screen_width/2 - window_width/2)
        # center_y = int(screen_height/2 - window_height/2)
        # master.geometry(f'+{center_x}+{center_y}')
        # ------------------------- #

        # --- 인스턴스 변수 초기화 --- #
        # 공통
        self.sound_player = SoundPlayer()
        # self.sound_options = self._find_available_sound_packs() # 아래에서 분리됨

        # 키보드용
        self.keyboard_listener = None
        self.keyboard_is_running = False
        self.keyboard_selected_sound_type = None
        self.keyboard_volume = 100
        self.keyboard_sound_var = tk.StringVar(master)
        self.keyboard_sound_options = self._find_available_keyboard_packs() # 메서드명 변경

        # 마우스용 (기능은 추후 구현)
        self.mouse_listener = None # 마우스 리스너 인스턴스 변수 추가
        self.mouse_is_running = False
        self.mouse_selected_sound_file = None # 파일 이름 저장용
        self.mouse_volume = 100
        self.mouse_sound_var = tk.StringVar(master)
        self.mouse_sound_options = self._find_available_mouse_sounds() # 새 메서드 호출
        # --------------------------- #

        # --- GUI 위젯 생성 --- #
        # 부모 프레임 (좌우 분할용)
        parent_frame = ttk.Frame(master, padding="10")
        parent_frame.pack(expand=True, fill=tk.BOTH)

        # --- 키보드 영역 (왼쪽) --- #
        keyboard_section_frame = ttk.LabelFrame(parent_frame, text="Keyboard", padding="10")
        keyboard_section_frame.pack(side=tk.LEFT, padx=(0, 5), fill=tk.BOTH, expand=True)

        # 키보드: 사운드 선택
        k_sound_frame = ttk.LabelFrame(keyboard_section_frame, text="Sound Options", padding="5") # 패딩 줄임
        k_sound_frame.pack(fill=tk.X, pady=(0,5))

        k_sound_label = ttk.Label(k_sound_frame, text="Select Sound Pack:")
        k_sound_label.pack(side=tk.LEFT, padx=(0, 5))

        k_default_sound = self.keyboard_sound_options[0] if self.keyboard_sound_options and self.keyboard_sound_options[0] not in ["None", "Error"] else "None"
        self.keyboard_sound_var.set(k_default_sound)
        self.keyboard_sound_combobox = ttk.Combobox(k_sound_frame, textvariable=self.keyboard_sound_var, values=self.keyboard_sound_options, state="readonly", width=10)
        self.keyboard_sound_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # 키보드: 볼륨 조절
        k_volume_frame = ttk.LabelFrame(keyboard_section_frame, text="Volume Control", padding="5") # 패딩 줄임
        k_volume_frame.pack(fill=tk.X, pady=5)

        self.keyboard_volume_scale = ttk.Scale(k_volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self._update_keyboard_volume) # 콜백 함수명 변경
        self.keyboard_volume_scale.set(self.keyboard_volume)
        self.keyboard_volume_scale.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.keyboard_volume_label = ttk.Label(k_volume_frame, text=f"{self.keyboard_volume}%")
        self.keyboard_volume_label.pack(side=tk.LEFT)

        # 키보드: 시작/종료 버튼
        k_button_frame = ttk.Frame(keyboard_section_frame, padding="5")
        k_button_frame.pack(fill=tk.X)

        self.keyboard_start_button = ttk.Button(k_button_frame, text="Start", command=self.start_keyboard_sound, width=10) # 커맨드 함수명 변경
        self.keyboard_start_button.pack(side=tk.LEFT, expand=True, padx=2)

        self.keyboard_stop_button = ttk.Button(k_button_frame, text="Stop", command=self.stop_keyboard_sound, state=tk.DISABLED, width=10) # 커맨드 함수명 변경
        self.keyboard_stop_button.pack(side=tk.LEFT, expand=True, padx=2)

        # --- 마우스 영역 (오른쪽) --- #
        mouse_section_frame = ttk.LabelFrame(parent_frame, text="Mouse", padding="10")
        mouse_section_frame.pack(side=tk.RIGHT, padx=(5, 0), fill=tk.BOTH, expand=True)

        # 마우스: 사운드 선택
        m_sound_frame = ttk.LabelFrame(mouse_section_frame, text="Click Sound", padding="5") # 레이블 변경
        m_sound_frame.pack(fill=tk.X, pady=(0,5))

        m_sound_label = ttk.Label(m_sound_frame, text="Select Click Sound:") # 레이블 변경
        m_sound_label.pack(side=tk.LEFT, padx=(0, 5))

        m_default_sound = self.mouse_sound_options[0] if self.mouse_sound_options and self.mouse_sound_options[0] not in ["None", "Error"] else "None"
        self.mouse_sound_var.set(m_default_sound)
        self.mouse_sound_combobox = ttk.Combobox(m_sound_frame, textvariable=self.mouse_sound_var, values=self.mouse_sound_options, state="readonly", width=10)
        self.mouse_sound_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # 마우스: 볼륨 조절
        m_volume_frame = ttk.LabelFrame(mouse_section_frame, text="Volume Control", padding="5")
        m_volume_frame.pack(fill=tk.X, pady=5)

        self.mouse_volume_scale = ttk.Scale(m_volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self._update_mouse_volume) # 콜백 함수명 변경 (추후 구현)
        self.mouse_volume_scale.set(self.mouse_volume)
        self.mouse_volume_scale.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.mouse_volume_label = ttk.Label(m_volume_frame, text=f"{self.mouse_volume}%")
        self.mouse_volume_label.pack(side=tk.LEFT)

        # 마우스: 시작/종료 버튼
        m_button_frame = ttk.Frame(mouse_section_frame, padding="5")
        m_button_frame.pack(fill=tk.X)

        self.mouse_start_button = ttk.Button(m_button_frame, text="Start", command=self.start_mouse_sound, width=10) # 커맨드 함수명 변경 (추후 구현)
        self.mouse_start_button.pack(side=tk.LEFT, expand=True, padx=2)

        self.mouse_stop_button = ttk.Button(m_button_frame, text="Stop", command=self.stop_mouse_sound, state=tk.DISABLED, width=10) # 커맨드 함수명 변경 (추후 구현)
        self.mouse_stop_button.pack(side=tk.LEFT, expand=True, padx=2)

        # --- 창 중앙 정렬 (위젯 배치 후 다시 실행) --- #
        master.update_idletasks() # GUI 업데이트 강제하여 정확한 창 크기 얻기
        window_width = master.winfo_width()
        window_height = master.winfo_height()
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        master.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}') # 크기와 위치 함께 설정
        # ----------------------------------------- #

        # 애플리케이션 종료 시 자원 해제 처리
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    # --- 콜백 함수 정의 --- #
    def _update_keyboard_volume(self, value):
        """키보드 볼륨 스케일 변경 시 호출됨"""
        self.keyboard_volume = int(float(value))
        if hasattr(self, 'keyboard_volume_label') and self.keyboard_volume_label:
            self.keyboard_volume_label.config(text=f"{self.keyboard_volume}%")

    def _update_mouse_volume(self, value):
        """마우스 볼륨 스케일 변경 시 호출됨 (추후 구현)"""
        self.mouse_volume = int(float(value))
        if hasattr(self, 'mouse_volume_label') and self.mouse_volume_label:
            self.mouse_volume_label.config(text=f"{self.mouse_volume}%")
        # TODO: 마우스 볼륨 로직 구현
        pass

    # --- 사운드 파일/팩 검색 --- #
    def _find_available_keyboard_packs(self):
        """키보드 사운드 팩(폴더) 목록을 반환합니다."""
        base_dir = os.path.join("src", "keyboard") # 경로 확인
        # 디렉토리 생성 로직은 SoundPlayer.load_sound_pack 에서 처리될 수 있으므로 여기선 생략 가능
        if not os.path.isdir(base_dir):
            messagebox.showwarning("Directory Not Found", f"Keyboard sound directory not found: {base_dir}")
            return ["None"]

        available_packs = []
        try:
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                # 폴더이고, 내부에 press나 release 폴더 중 하나라도 있는지 확인
                if os.path.isdir(item_path) and \
                   (os.path.isdir(os.path.join(item_path, "press")) or \
                    os.path.isdir(os.path.join(item_path, "release"))):
                    available_packs.append(item)
        except Exception as e:
            messagebox.showerror("Error", f"Error reading keyboard sound pack directory '{base_dir}': {e}")
            return ["Error"]

        return sorted(available_packs) if available_packs else ["None"]

    def _find_available_mouse_sounds(self):
        """마우스 클릭 사운드 파일 목록 (확장자 제외)을 반환합니다."""
        base_dir = os.path.join("src", "mouse") # 마우스 사운드 경로
        if not os.path.exists(base_dir):
            try:
                os.makedirs(base_dir)
                print(f"Created directory: {base_dir}")
                return ["None"] # 디렉토리 없었으면 None 반환
            except OSError as e:
                messagebox.showerror("Error", f"Could not create directory {base_dir}: {e}")
                return ["Error"]

        available_sounds = []
        try:
            for filename in os.listdir(base_dir):
                if filename.lower().endswith(('.wav', '.mp3')):
                    sound_name = os.path.splitext(filename)[0]
                    available_sounds.append(sound_name)
        except Exception as e:
            messagebox.showerror("Error", f"Error reading mouse sound directory '{base_dir}': {e}")
            return ["Error"]

        return sorted(available_sounds) if available_sounds else ["None"]

    # --- 키보드 이벤트 핸들러 --- #
    def _handle_key_press(self, key):
        """키 눌림 이벤트 처리: kbsim 규칙에 따라 press 사운드 재생"""
        if self.keyboard_is_running and self.sound_player: # 변수명 변경
            key_name = self._key_to_filename(key)
            # print(f"[DEBUG] Handle Press: Original Key = {key}, Mapped Name = {key_name}") # 로그 줄임

            if key_name:
                # KEY_ROW_MAP에서 행 정보 찾기
                row_index = KEY_ROW_MAP.get(key_name, None)

                # kbsim 규칙: 행 5 이상은 행 4(GENERIC_R4)로 취급
                # 또는 매핑되지 않은 키도 기본값(행 4) 사용
                effective_row = 4 if row_index is None or row_index > 4 else row_index

                self.sound_player.play_key_sound(
                    self.keyboard_selected_sound_type, # 변수명 변경
                    "press",
                    key_name,
                    self.keyboard_volume, # 변수명 변경
                    row_index=effective_row
                )

    def _handle_key_release(self, key):
        """키 뗌 이벤트 처리: kbsim 규칙에 따라 release 사운드 재생"""
        if self.keyboard_is_running and self.sound_player: # 변수명 변경
            key_name = self._key_to_filename(key)
            # print(f"[DEBUG] Handle Release: Original Key = {key}, Mapped Name = {key_name}") # 로그 줄임

            if key_name:
                self.sound_player.play_key_sound(
                    self.keyboard_selected_sound_type, # 변수명 변경
                    "release",
                    key_name,
                    self.keyboard_volume # 변수명 변경
                )

    # --- 마우스 이벤트 핸들러 --- #
    def _handle_mouse_click(self, x, y, button, pressed):
        """마우스 클릭 시 호출될 콜백 함수"""
        if self.mouse_is_running and pressed: # 클릭 누를 때만
            # print(f"Mouse clicked: {button}") # 디버깅 로그
            if self.mouse_selected_sound_file and self.sound_player:
                self.sound_player.play_mouse_click_sound(
                    self.mouse_selected_sound_file,
                    self.mouse_volume
                )
    # def _handle_mouse_scroll(self, x, y, dx, dy): # 스크롤은 아직 미구현
    #     pass

    # --- 시작/종료 로직 --- #
    def start_keyboard_sound(self):
        """키보드 사운드 재생 및 리스닝 시작"""
        if self.keyboard_is_running: # 변수명 변경
            return

        self.keyboard_selected_sound_type = self.keyboard_sound_var.get() # 변수명 변경
        if self.keyboard_selected_sound_type == "None" or self.keyboard_selected_sound_type == "Error":
             messagebox.showerror("Error", "Please select a valid sound pack for the keyboard.")
             return

        # 선택된 사운드 팩 미리 로드
        if not self.sound_player.load_sound_pack(self.keyboard_selected_sound_type):
            messagebox.showerror("Error", f"Failed to load sound pack '{self.keyboard_selected_sound_type}'. Check logs for details.")
            return

        # 키보드 리스너 시작
        try:
            self.keyboard_listener = KeyboardListener(
                on_press_callback=self._handle_key_press,
                on_release_callback=self._handle_key_release
            )
            self.keyboard_listener.start_listening()
            self.keyboard_is_running = True # 변수명 변경
            print(f"Keyboard listening started with sound pack: '{self.keyboard_selected_sound_type}', Volume: {self.keyboard_volume}%")

            # GUI 상태 업데이트
            self._update_gui_state() # GUI 상태 업데이트 함수 호출

        except Exception as e:
             messagebox.showerror("Error", f"Failed to start keyboard listener: {e}")
             if self.keyboard_listener:
                 self.keyboard_listener = None
             self.keyboard_is_running = False # 변수명 변경
             self._update_gui_state() # GUI 상태 업데이트 함수 호출

    def stop_keyboard_sound(self):
        """키보드 리스닝 중지"""
        if not self.keyboard_is_running: # 변수명 변경
            return

        if self.keyboard_listener:
            self.keyboard_listener.stop_listening()
            self.keyboard_listener = None

        self.keyboard_is_running = False # 변수명 변경
        print("Keyboard listening stopped.")

        # GUI 상태 업데이트
        self._update_gui_state()

    def start_mouse_sound(self):
        """마우스 사운드 재생 및 리스닝 시작"""
        if self.mouse_is_running:
            return

        self.mouse_selected_sound_file = self.mouse_sound_var.get()
        if self.mouse_selected_sound_file == "None" or self.mouse_selected_sound_file == "Error":
            messagebox.showerror("Error", "Please select a valid click sound for the mouse.")
            return

        # 선택된 마우스 사운드 로드 시도
        if not self.sound_player.load_mouse_sound(self.mouse_selected_sound_file):
            messagebox.showerror("Error", f"Failed to load mouse sound '{self.mouse_selected_sound_file}'. Check logs.")
            return

        # 마우스 리스너 시작
        try:
            self.mouse_listener = MouseListener(on_click_callback=self._handle_mouse_click)
            self.mouse_listener.start_listening()
            self.mouse_is_running = True
            print(f"Mouse listening started with sound: '{self.mouse_selected_sound_file}', Volume: {self.mouse_volume}%")
            self._update_gui_state()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start mouse listener: {e}")
            if self.mouse_listener:
                self.mouse_listener = None
            self.mouse_is_running = False
            self._update_gui_state()

    def stop_mouse_sound(self):
        """마우스 리스닝 중지"""
        if not self.mouse_is_running:
            return

        if self.mouse_listener:
            self.mouse_listener.stop_listening()
            self.mouse_listener = None

        self.mouse_is_running = False
        print("Mouse listening stopped.")
        self._update_gui_state()

    # --- GUI 상태 업데이트 --- #
    def _update_gui_state(self):
        """현재 실행 상태에 따라 GUI 위젯 상태 업데이트"""
        # Keyboard Controls
        k_state = tk.DISABLED if self.keyboard_is_running else tk.NORMAL
        k_combo_state = tk.DISABLED if self.keyboard_is_running else ("readonly" if self.keyboard_sound_options and self.keyboard_sound_options != ["None"] and self.keyboard_sound_options != ["Error"] else tk.DISABLED)

        self.keyboard_start_button.config(state=k_state)
        self.keyboard_stop_button.config(state=tk.NORMAL if self.keyboard_is_running else tk.DISABLED)
        self.keyboard_sound_combobox.config(state=k_combo_state)
        self.keyboard_volume_scale.config(state=k_state)

        # Mouse Controls
        m_state = tk.DISABLED if self.mouse_is_running else tk.NORMAL
        m_combo_state = tk.DISABLED if self.mouse_is_running else ("readonly" if self.mouse_sound_options and self.mouse_sound_options != ["None"] and self.mouse_sound_options != ["Error"] else tk.DISABLED)

        self.mouse_start_button.config(state=m_state)
        self.mouse_stop_button.config(state=tk.NORMAL if self.mouse_is_running else tk.DISABLED)
        self.mouse_sound_combobox.config(state=m_combo_state)
        self.mouse_volume_scale.config(state=m_state)

    # --- 애플리케이션 종료 --- #
    def on_closing(self):
        """애플리케이션 창 종료 시 호출될 함수"""
        if self.keyboard_is_running:
            self.stop_keyboard_sound()
        if self.mouse_is_running: # 마우스 리스너 중지 추가
            self.stop_mouse_sound()
        if self.sound_player:
            self.sound_player.unload()
        self.master.destroy()

    # --- 키보드 키 이름 변환 --- #
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


if __name__ == "__main__":
    # pynput과 tkinter의 이벤트 루프 충돌 방지 (일부 시스템)
    # import threading
    # def run_tk():
    #     root = tk.Tk()
    #     app = KeyboardSoundApp(root)
    #     root.mainloop()
    # tk_thread = threading.Thread(target=run_tk, daemon=True)
    # tk_thread.start()
    # # 메인 스레드는 여기서 종료될 수 있음 (daemon=True 이므로)
    # # 또는 tk_thread.join()으로 대기

    # 일단 표준 방식으로 실행
    root = tk.Tk()
    app = KeyboardSoundApp(root)
    root.mainloop() 