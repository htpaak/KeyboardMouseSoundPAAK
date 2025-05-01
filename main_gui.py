import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os

# 모듈 임포트
from keyboard_listener import KeyboardListener
from sound_player import SoundPlayer
from pynput import keyboard

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
        master.title("Keyboard Sound Selector")
        master.resizable(False, False) # 창 크기 조절 비활성화

        # --- 창 중앙 정렬 추가 --- #
        master.update_idletasks() # GUI 업데이트 강제하여 정확한 창 크기 얻기
        window_width = master.winfo_width()
        window_height = master.winfo_height()
        screen_width = master.winfo_screenwidth()
        screen_height = master.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        master.geometry(f'+{center_x}+{center_y}') # 창 위치 설정
        # ------------------------- #

        # 인스턴스 변수 초기화
        self.sound_player = SoundPlayer()
        self.keyboard_listener = None
        self.is_running = False
        self.selected_sound_type = None # 선택된 사운드 타입 (폴더명)
        self.volume = 100 # 볼륨 초기값 저장 (100으로 변경)

        # --- GUI 위젯 생성 --- #
        # 메인 프레임
        main_frame = ttk.Frame(master, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # 사운드 선택
        sound_frame = ttk.LabelFrame(main_frame, text="Sound Options", padding="10")
        sound_frame.pack(fill=tk.X, pady=5)

        sound_label = ttk.Label(sound_frame, text="Select Sound Pack:")
        sound_label.pack(side=tk.LEFT, padx=(0, 5))

        self.sound_options = self._find_available_sound_packs() # 사용 가능한 사운드 팩 (폴더) 찾기
        if not self.sound_options or self.sound_options == ["Error"]:
            if self.sound_options != ["Error"]: # 에러 메시지가 이미 표시되지 않았다면
                messagebox.showwarning("No Sound Packs",
                                       f"No sound pack folders found in '{self.sound_player.base_sound_folder}'.\n" +
                                       "Please create folders like 'Typewriter' inside it.")
            self.sound_options = ["None"] # 폴더가 없을 경우 기본 옵션

        self.sound_var = tk.StringVar(master)
        # 사용 가능한 첫 번째 사운드 팩을 기본값으로 설정 (None 이나 Error가 아닐 경우)
        default_sound = self.sound_options[0] if self.sound_options and self.sound_options[0] not in ["None", "Error"] else "None"
        self.sound_var.set(default_sound)
        self.sound_combobox = ttk.Combobox(sound_frame, textvariable=self.sound_var, values=self.sound_options, state="readonly", width=15)
        self.sound_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # 볼륨 조절
        volume_frame = ttk.LabelFrame(main_frame, text="Volume Control", padding="10")
        volume_frame.pack(fill=tk.X, pady=5)

        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self._update_volume)
        self.volume_scale.set(self.volume) # 초기값 설정 (변경된 self.volume 사용)
        self.volume_scale.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.volume_label = ttk.Label(volume_frame, text=f"{self.volume}%") # 초기 볼륨 표시 (변경된 self.volume 사용)
        self.volume_label.pack(side=tk.LEFT)

        # 시작/종료 버튼
        button_frame = ttk.Frame(main_frame, padding="5")
        button_frame.pack(fill=tk.X)

        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_sound, width=10)
        self.start_button.pack(side=tk.LEFT, expand=True, padx=2)

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_sound, state=tk.DISABLED, width=10)
        self.stop_button.pack(side=tk.LEFT, expand=True, padx=2)

        # 애플리케이션 종료 시 자원 해제 처리
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _update_volume(self, value):
        """볼륨 스케일 변경 시 호출되어 볼륨 값 업데이트 및 라벨 변경"""
        self.volume = int(float(value))
        # self.volume_label 이 초기화되었는지 확인 후 업데이트 (AttributeError 방지)
        if hasattr(self, 'volume_label') and self.volume_label:
            self.volume_label.config(text=f"{self.volume}%")
        # 실행 중일 때 실시간으로 볼륨 반영 (선택적)
        # if self.is_running and self.sound_player:
        #     # 여기서는 재생 시점에 볼륨을 적용하므로 즉시 반영 코드는 생략
        #     pass

    def _find_available_sound_packs(self):
        """지정된 기본 사운드 폴더에서 사용 가능한 사운드 팩(폴더) 목록을 반환합니다."""
        base_dir = self.sound_player.base_sound_folder
        if not os.path.exists(base_dir):
            try:
                os.makedirs(base_dir)
                print(f"Created directory: {base_dir}")
                return [] # 폴더가 없었으므로 빈 리스트 반환
            except OSError as e:
                messagebox.showerror("Error", f"Could not create directory {base_dir}: {e}")
                return ["Error"] # 에러 발생 시

        available_packs = []
        try:
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                # 폴더이고, 내부에 press나 release 폴더 중 하나라도 있는지 확인 (더 엄격한 검사)
                if os.path.isdir(item_path) and \
                   (os.path.isdir(os.path.join(item_path, "press")) or \
                    os.path.isdir(os.path.join(item_path, "release"))):
                    available_packs.append(item)
        except Exception as e:
            messagebox.showerror("Error", f"Error reading sound pack directory '{base_dir}': {e}")
            return ["Error"]

        return sorted(available_packs) if available_packs else []

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

    def _handle_key_press(self, key):
        """키 눌림 이벤트 처리: kbsim 규칙에 따라 press 사운드 재생"""
        if self.is_running and self.sound_player:
            key_name = self._key_to_filename(key)
            print(f"[DEBUG] Handle Press: Original Key = {key}, Mapped Name = {key_name}") # 로그 추가

            if key_name:
                # KEY_ROW_MAP에서 행 정보 찾기
                row_index = KEY_ROW_MAP.get(key_name, None)

                # kbsim 규칙: 행 5 이상은 행 4(GENERIC_R4)로 취급
                # 또는 매핑되지 않은 키도 기본값(행 4) 사용
                effective_row = 4 if row_index is None or row_index > 4 else row_index

                # print(f"Press Event: Key='{key_name}', Row={effective_row}") # 디버깅용

                # 수정된 play_key_sound 호출 (행 정보 전달)
                self.sound_player.play_key_sound(
                    self.selected_sound_type,
                    "press",
                    key_name,
                    self.volume,
                    row_index=effective_row
                )
            # else: # 매핑 안 된 키는 소리 재생 안 함 (kbsim 동작과 유사하게)
                # print(f"Press Event: Unmapped key {key}, no sound played.")
                # pass

    def _handle_key_release(self, key):
        """키 뗌 이벤트 처리: kbsim 규칙에 따라 release 사운드 재생"""
        if self.is_running and self.sound_player:
            key_name = self._key_to_filename(key)
            print(f"[DEBUG] Handle Release: Original Key = {key}, Mapped Name = {key_name}") # 로그 추가

            if key_name:
                # 수정된 play_key_sound 호출 (행 정보 필요 없음)
                # _find_sound_file 내부에서 SPECIAL_RELEASE_KEYS 와 GENERIC fallback 처리
                self.sound_player.play_key_sound(
                    self.selected_sound_type,
                    "release",
                    key_name,
                    self.volume
                    # row_index는 전달 안 함
                )
            # else: # 매핑 안 된 키는 소리 재생 안 함
                # print(f"Release Event: Unmapped key {key}, no sound played.")
                # pass

    def start_sound(self):
        """사운드 재생 및 키보드 리스닝 시작"""
        if self.is_running:
            return

        self.selected_sound_type = self.sound_var.get()
        if self.selected_sound_type == "None" or self.selected_sound_type == "Error":
             messagebox.showerror("Error", "Please select a valid sound pack from the list.")
             return

        # self.volume = self.volume_scale.get() # _update_volume에서 이미 self.volume 업데이트됨

        # --- 선택된 사운드 팩 미리 로드 --- #
        if not self.sound_player.load_sound_pack(self.selected_sound_type):
            messagebox.showerror("Error", f"Failed to load sound pack '{self.selected_sound_type}'. Check logs for details.")
            # GUI 상태 원래대로 복구 (선택 사항, 필요시 _update_gui_state 호출)
            # self._update_gui_state() # stop 상태로 돌려놓기
            return # 로딩 실패 시 리스너 시작 안 함
        # ---------------------------------- #

        # 키보드 리스너 시작
        try:
            # press와 release 콜백을 모두 전달
            self.keyboard_listener = KeyboardListener(
                on_press_callback=self._handle_key_press,
                on_release_callback=self._handle_key_release
            )
            self.keyboard_listener.start_listening()
            self.is_running = True
            print(f"Started listening with sound pack: '{self.selected_sound_type}', Volume: {self.volume}%")

            # GUI 상태 업데이트
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.sound_combobox.config(state=tk.DISABLED)
            self.volume_scale.config(state=tk.DISABLED)

        except Exception as e:
             messagebox.showerror("Error", f"Failed to start keyboard listener: {e}")
             if self.keyboard_listener:
                 # 시도 중 오류 발생 시 stop 호출하면 안 됨 (listener 객체가 비정상일 수 있음)
                 self.keyboard_listener = None # 참조만 제거
             self.is_running = False
             # GUI 원래 상태로 복구
             self._update_gui_state()

    def stop_sound(self):
        """키보드 리스닝 중지"""
        if not self.is_running:
            return

        if self.keyboard_listener:
            self.keyboard_listener.stop_listening()
            self.keyboard_listener = None

        self.is_running = False
        print("Stopped listening.")

        # GUI 상태 업데이트
        self._update_gui_state()

    def _update_gui_state(self):
        """현재 실행 상태(self.is_running)에 따라 GUI 위젯 상태 업데이트"""
        if self.is_running:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.sound_combobox.config(state=tk.DISABLED)
            self.volume_scale.config(state=tk.DISABLED)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            # 사운드 팩 목록이 유효할 때만 콤보박스 활성화
            combo_state = "readonly" if self.sound_options and self.sound_options != ["None"] and self.sound_options != ["Error"] else tk.DISABLED
            self.sound_combobox.config(state=combo_state)
            self.volume_scale.config(state=tk.NORMAL)

    def on_closing(self):
        """애플리케이션 창 종료 시 호출될 함수"""
        if self.is_running:
            self.stop_sound()
        if self.sound_player:
            self.sound_player.unload()
        self.master.destroy()


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