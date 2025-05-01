# 사운드 플레이어 모듈
import pygame
import os
import sys # sys 모듈 임포트 추가
import time # 사운드 중복 재생 방지용
import logging # 로깅 추가

# 로거 설정 (main_gui.py와 동일한 설정 사용 권장)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG) # 필요시 레벨 조정
# handler = logging.StreamHandler()
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)

# --- 리소스 경로 헬퍼 함수 --- #
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Not packaged, use normal path relative to this script
        base_path = os.path.abspath(os.path.dirname(__file__))

    return os.path.join(base_path, relative_path)
# --- 헬퍼 함수 끝 --- #

# --- 키보드 관련 설정 --- #
# kbsim-master 분석 기반: release 시 특정 사운드가 있는 키들
SPECIAL_RELEASE_KEYS = {
    'BACKSPACE', 'TAB', 'ENTER', 'CAPSLOCK', 'SHIFT', 'CTRL', 'ALT', 'SPACE',
    'ESC', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
    'PRTSC', 'SCROLLLOCK', 'PAUSE', 'INSERT', 'HOME', 'PGUP', 'DELETE', 'END', 'PGDN',
    'UP', 'DOWN', 'LEFT', 'RIGHT', 'WIN', 'MENU', 'NUMLOCK'
}

# --- 마우스 관련 설정 --- #
# MOUSE_SOUND_FOLDER = os.path.join("src", "mouse") # 기존 코드
MOUSE_SOUND_FOLDER = resource_path(os.path.join("src", "mouse")) # resource_path 사용

class SoundPlayer:
    def __init__(self):
        """사운드 플레이어 초기화"""
        # self.keyboard_base_folder = os.path.join("src", "keyboard") # 기존 코드
        self.keyboard_base_folder = resource_path(os.path.join("src", "keyboard")) # resource_path 사용
        self.mixer_initialized = False
        self.last_play_time = {} # 키별 마지막 재생 시간 기록
        self.sound_cache = {} # 사운드 객체 캐시
        self.current_sound_pack = None # 현재 로드된 사운드 팩

        try:
            # pre_init으로 버퍼 크기 조정 시도 (값은 실험 필요)
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=256)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(32) # 채널 수 증가 고려
            self.mixer_initialized = True
            logger.info("Sound player initialized.")
        except pygame.error as e:
            logger.error(f"Failed to initialize pygame mixer: {e}")
            pygame.mixer.quit()

    def load_sound_pack(self, sound_type):
        """지정된 사운드 팩의 모든 사운드 파일을 미리 로드하여 캐시에 저장합니다."""
        if not self.mixer_initialized:
            logger.warning("Mixer not initialized. Cannot load sound pack.")
            return False
        if self.current_sound_pack == sound_type:
            logger.info(f"Sound pack '{sound_type}' is already loaded.")
            return True

        logger.info(f"Loading sound pack: '{sound_type}'...")
        self.sound_cache.clear() # 기존 캐시 비우기
        self.current_sound_pack = None # 로드 중 상태로 설정
        pack_path = os.path.join(self.keyboard_base_folder, sound_type) # 이미 적용됨, 확인용

        if not os.path.isdir(pack_path):
            logger.error(f"Sound pack directory not found: {pack_path}")
            return False

        for event_type in ["press", "release"]:
            event_folder = os.path.join(pack_path, event_type)
            if not os.path.isdir(event_folder):
                logger.warning(f"Subdirectory not found, skipping: {event_folder}")
                continue

            for filename in os.listdir(event_folder):
                if filename.lower().endswith(('.wav', '.mp3')):
                    file_path = os.path.join(event_folder, filename)
                    cache_key = (event_type, os.path.splitext(filename)[0].upper()) # (event_type, KEY_NAME)
                    try:
                        sound = pygame.mixer.Sound(file_path)
                        self.sound_cache[cache_key] = sound
                        # logger.debug(f"Loaded sound: {cache_key} from {file_path}") # 상세 로드 로그
                    except pygame.error as e:
                        logger.error(f"Failed to load sound '{file_path}': {e}")

        if self.sound_cache:
            self.current_sound_pack = sound_type
            logger.info(f"Successfully loaded {len(self.sound_cache)} sounds for pack '{sound_type}'")
            return True
        else:
            logger.error(f"No sounds loaded for pack '{sound_type}'")
            return False

    def load_mouse_sound(self, sound_name):
        """지정된 마우스 사운드 이름(확장자 제외)으로 파일을 찾아 로드하고 캐시합니다."""
        if not self.mixer_initialized:
            logger.warning("Mixer not initialized. Cannot load mouse sound.")
            return False
        if not sound_name or sound_name == "None":
            logger.warning("Invalid mouse sound name provided.")
            return False

        # 캐시 키는 확장자 없는 이름 사용
        cache_key = ('mouse', sound_name)
        if cache_key in self.sound_cache:
            # logger.debug(f"Mouse sound '{sound_name}' is already cached.")
            return True # 이미 캐시됨

        logger.info(f"Loading mouse sound: '{sound_name}'...")
        loaded = False
        # --- 파일 찾기: .wav, .mp3, .ogg 순서로 시도 --- #
        for ext in [".wav", ".mp3", ".ogg"]:
            # file_path = os.path.join(MOUSE_SOUND_FOLDER, f"{sound_name}{ext}") # resource_path 적용은 MOUSE_SOUND_FOLDER 초기화에서 이미 됨
            file_path = os.path.join(MOUSE_SOUND_FOLDER, f"{sound_name}{ext}") # 이미 적용됨, 확인용
            if os.path.exists(file_path):
                try:
                    sound = pygame.mixer.Sound(file_path)
                    self.sound_cache[cache_key] = sound # 캐시 키는 확장자 없는 이름
                    logger.info(f"Successfully loaded mouse sound '{file_path}' with cache key: {cache_key}")
                    loaded = True
                    break # 찾았으면 중단
                except pygame.error as e:
                    logger.error(f"Failed to load mouse sound '{file_path}': {e}")
                    # 로드 실패 시 다음 확장자 시도 (여기서 return False 하지 않음)
                    loaded = False # 명시적으로 실패 상태 유지

        if not loaded:
            # 시도한 모든 확장자에 대해 파일을 찾지 못함
            logger.error(f"Mouse sound file not found for basename '{sound_name}' with supported extensions in '{MOUSE_SOUND_FOLDER}'")

        return loaded

    def _find_sound_object(self, sound_type, event_type, key_name, row_index=None):
        """캐시에서 키에 맞는 Sound 객체를 찾습니다.

        Args:
            sound_type (str): 사운드 종류 (폴더명 또는 'mouse').
            event_type (str): "press" 또는 "release" (마우스의 경우 None).
            key_name (str): 대상 키 이름 (예: 'A', 'SPACE') 또는 마우스 사운드 이름 (확장자 제외).
            row_index (int, optional): 키의 행 인덱스 (0-4). press 이벤트에만 사용됨.

        Returns:
            pygame.mixer.Sound or None: 찾은 Sound 객체 또는 None.
        """
        if not self.mixer_initialized or key_name is None:
            return None

        # --- 마우스 사운드 처리 수정: key_name은 확장자 없는 이름 --- #
        if sound_type == 'mouse':
            cache_key = ('mouse', key_name)
            return self.sound_cache.get(cache_key)
        # ------------------------------------------------------ #

        # 현재 로드된 키보드 팩과 요청된 팩이 다르면 로드 시도 또는 None 반환
        if self.current_sound_pack != sound_type:
            logger.warning(f"Requested sound pack '{sound_type}' is not loaded. Current: '{self.current_sound_pack}'")
            return None

        target_sound_name = None # 찾을 사운드의 이름 (키 이름 또는 fallback 이름)

        # --- Press 이벤트 처리 로직 --- #
        if event_type == "press":
            # 1. Backspace, Space, Enter 인 경우: 개별 이름 먼저 시도
            if key_name in ["BACKSPACE", "SPACE", "ENTER"]:
                cache_key = (event_type, key_name)
                if cache_key in self.sound_cache:
                    return self.sound_cache[cache_key]
                # 개별 사운드 없으면 fallback 으로 진행

            # 2. 그 외 모든 키 (또는 위 키들의 개별 사운드가 없는 경우): Fallback 이름 사용
            if row_index is not None and 0 <= row_index <= 4:
                target_sound_name = f"GENERIC_R{row_index}"
            else:
                target_sound_name = "GENERIC_R4"

        # --- Release 이벤트 처리 로직 --- #
        elif event_type == "release":
            # 1. 개별 키 이름으로 캐시 탐색 시도
            cache_key = (event_type, key_name)
            if cache_key in self.sound_cache:
                 return self.sound_cache[cache_key]

            # 2. 개별 사운드 없고, 특정 키가 아니면 GENERIC Fallback 이름 사용
            if key_name not in ["BACKSPACE", "SPACE", "ENTER"]:
                 target_sound_name = "GENERIC"
            # 특정 키인데 개별 사운드 없으면 여기서는 target_sound_name이 None 유지 -> 소리 없음

        # 결정된 target_sound_name으로 캐시 조회
        if target_sound_name:
            cache_key = (event_type, target_sound_name)
            return self.sound_cache.get(cache_key) # 없으면 None 반환

        # 특정 press/release 키에 대한 개별 사운드도 없고 fallback 대상도 아닌 경우
        return None

    def play_key_sound(self, sound_type, event_type, key_name, volume_percent, row_index=None):
        """키 이벤트에 맞는 캐시된 Sound 객체를 찾아 재생합니다."""
        if not self.mixer_initialized:
            return

        # 중복 재생 방지 (기존과 동일)
        current_time = time.time()
        sound_full_key = f"{sound_type}_{event_type}_{key_name}"
        last_played = self.last_play_time.get(sound_full_key, 0)
        min_interval = 0.02 # 간격 약간 줄여보기 (30ms -> 20ms)
        if current_time - last_played < min_interval:
             # logger.debug(f"Skipping duplicate play for {sound_full_key}")
             return

        # 캐시에서 Sound 객체 찾기 (sound_type이 'keyboard'임을 명시적으로 가정)
        sound_object = self._find_sound_object(sound_type, event_type, key_name, row_index)

        if sound_object:
            # 캐시 키 로깅 (파일 경로 대신)
            # 재생 대상 찾기 로직에서 cache_key를 반환하도록 수정하거나, 여기서 다시 계산 필요
            # 여기서는 간단히 key_name으로 로깅
            logger.debug(f"[DEBUG] Play Sound: Found cached object for {event_type}/{key_name}")
            try:
                volume_float = max(0.0, min(1.0, volume_percent / 100.0))
                sound_object.set_volume(volume_float)
                channel = pygame.mixer.find_channel(True) # 여유 채널 찾기
                if channel:
                    channel.play(sound_object)
                    self.last_play_time[sound_full_key] = current_time
                    # logger.debug(f"Playing sound on channel {channel}")
                else:
                     logger.warning("No available channels to play sound.")
            except pygame.error as e:
                logger.error(f"Error playing sound for key '{key_name}': {e}")
            except Exception as e:
                logger.error(f"Unexpected error playing sound for key '{key_name}': {e}")
        # else:
            # logger.debug(f"[DEBUG] Play Sound: No sound object found for {sound_type}/{event_type}/{key_name}")

    def play_mouse_click_sound(self, sound_name, volume_percent):
        """캐시된 마우스 클릭 사운드를 찾아 재생합니다. (sound_name은 확장자 제외)"""
        if not self.mixer_initialized or not sound_name or sound_name == "None":
            return

        # 캐시에서 Sound 객체 찾기 (sound_type='mouse', key_name=sound_name 사용)
        sound_object = self._find_sound_object('mouse', None, sound_name)

        if sound_object:
            logger.debug(f"[DEBUG] Play Mouse Sound: Found cached object for {sound_name}")
            try:
                volume_float = max(0.0, min(1.0, volume_percent / 100.0))
                sound_object.set_volume(volume_float)
                sound_object.play()
            except pygame.error as e:
                logger.error(f"Error playing mouse sound '{sound_name}': {e}")
            except Exception as e:
                logger.error(f"Unexpected error playing mouse sound '{sound_name}': {e}")
        else:
            logger.warning(f"Mouse sound object not found in cache for '{sound_name}'. Please load it first.")

    def unload(self):
        """모든 로드된 사운드를 언로드하고 캐시를 비웁니다."""
        if self.mixer_initialized:
            pygame.mixer.stop() # 모든 사운드 재생 중지
        self.sound_cache.clear()
        self.last_play_time.clear()
        self.current_sound_pack = None
        logger.info("Sound player unloaded and cache cleared.")


# --- 테스트용 코드 --- (수정됨)
if __name__ == '__main__':

    # --- 테스트 환경 설정 --- (폴더 및 샘플 파일 생성)
    keyboard_test_base_folder = os.path.join("src", "keyboard") # 키보드 경로
    mouse_test_folder = os.path.join("src", "mouse") # 마우스 경로
    os.makedirs(mouse_test_folder, exist_ok=True)

    sound_types_to_test = ["TestType1"]
    event_types = ["press", "release"]
    # kbsim 규칙에 맞는 샘플 키와 Fallback 파일 정의
    sample_keys_press = {
        "specific": ["A", "SPACE", "ENTER"], # 특정 소리 파일이 있을 키
        "fallback": { # 행별 Fallback 파일
            0: "GENERICR0", 1: "GENERICR1", 2: "GENERICR2", 3: "GENERICR3", 4: "GENERICR4"
        }
    }
    sample_keys_release = {
        "specific": ["SPACE", "ENTER", "BACKSPACE"], # 특정 release 소리가 있을 키 (SPECIAL_RELEASE_KEYS 와 유사해야 함)
        "fallback": "GENERIC" # 일반 release fallback
    }

    print("Setting up keyboard test environment...")
    for stype in sound_types_to_test:
        # Press 폴더 및 파일 생성
        press_folder = os.path.join(keyboard_test_base_folder, stype, "press")
        os.makedirs(press_folder, exist_ok=True)
        print(f"Ensured directory exists: {press_folder}")
        for key in sample_keys_press["specific"]:
             filepath = os.path.join(press_folder, f"{key}.wav")
             if not os.path.exists(filepath): open(filepath, 'w').close(); print(f"Created dummy: {filepath}")
        for key in sample_keys_press["fallback"].values():
             filepath = os.path.join(press_folder, f"{key}.wav")
             if not os.path.exists(filepath): open(filepath, 'w').close(); print(f"Created dummy: {filepath}")

        # Release 폴더 및 파일 생성
        release_folder = os.path.join(keyboard_test_base_folder, stype, "release")
        os.makedirs(release_folder, exist_ok=True)
        print(f"Ensured directory exists: {release_folder}")
        for key in sample_keys_release["specific"]:
             filepath = os.path.join(release_folder, f"{key}.wav")
             if not os.path.exists(filepath): open(filepath, 'w').close(); print(f"Created dummy: {filepath}")
        filepath = os.path.join(release_folder, f"{sample_keys_release['fallback']}.wav")
        if not os.path.exists(filepath): open(filepath, 'w').close(); print(f"Created dummy: {filepath}")
    print("Keyboard test environment setup complete.")

    # 마우스 테스트 파일 생성
    print("Setting up mouse test environment...")
    mouse_files = ["click_1.wav", "click_2.mp3"]
    for mfile in mouse_files:
        mpath = os.path.join(mouse_test_folder, mfile)
        if not os.path.exists(mpath): open(mpath, 'w').close(); print(f"Created dummy: {mpath}")
    print("Mouse test environment setup complete.")

    # --- 테스트 환경 설정 끝 ---

    player = SoundPlayer()

    if player.mixer_initialized:
        print("\n--- Running Keyboard Playback Tests ---")
        test_keyboard_pack = "TestType1"
        volume = 80
        # 키보드 팩 로드
        player.load_sound_pack(test_keyboard_pack)

        # Press 테스트
        print("\nTest Press 1: Specific key ('A', row 3 expected)")
        player.play_key_sound(test_keyboard_pack, "press", "A", volume, row_index=3)
        time.sleep(0.1)

        print("\nTest Press 2: Specific key ('SPACE', row 5 -> use 4)")
        player.play_key_sound(test_keyboard_pack, "press", "SPACE", volume, row_index=5) # row 5는 GENERICR4 사용 예상
        time.sleep(0.1)

        print("\nTest Press 3: Non-specific key ('Q', row 2 expected) -> Fallback GENERICR2")
        player.play_key_sound(test_keyboard_pack, "press", "Q", volume, row_index=2)
        time.sleep(0.1)

        print("\nTest Press 4: Non-specific key ('F1', row 0 expected) -> Fallback GENERICR0")
        player.play_key_sound(test_keyboard_pack, "press", "F1", volume, row_index=0)
        time.sleep(0.1)

        # Release 테스트
        print("\nTest Release 1: Specific release key ('SPACE')")
        player.play_key_sound(test_keyboard_pack, "release", "SPACE", volume)
        time.sleep(0.1)

        print("\nTest Release 2: Specific release key ('ENTER')")
        player.play_key_sound(test_keyboard_pack, "release", "ENTER", volume)
        time.sleep(0.1)

        print("\nTest Release 3: Non-specific release key ('A') -> Fallback GENERIC")
        player.play_key_sound(test_keyboard_pack, "release", "A", volume) # 'A'는 SPECIAL_RELEASE_KEYS 에 없으므로 GENERIC 예상
        time.sleep(0.1)

        print("\nTest Release 4: Specific key ('SHIFT') but no specific file -> Fallback GENERIC")
        # SHIFT는 SPECIAL_RELEASE_KEYS에 있지만, 테스트 파일은 생성 안 함 -> GENERIC 예상
        player.play_key_sound(test_keyboard_pack, "release", "SHIFT", volume)
        time.sleep(0.1)

        print("\n--- Keyboard Playback Tests Finished ---")

        # 마우스 사운드 테스트
        print("\n--- Running Mouse Playback Tests ---")
        test_mouse_sound1 = "click_1"
        test_mouse_sound2 = "click_2"

        # 마우스 사운드 로드
        player.load_mouse_sound(test_mouse_sound1)
        player.load_mouse_sound(test_mouse_sound2)

        print(f"\nTest Mouse Click 1: '{test_mouse_sound1}'")
        player.play_mouse_click_sound(test_mouse_sound1, 90)
        time.sleep(0.2)

        print(f"\nTest Mouse Click 2: '{test_mouse_sound2}'")
        player.play_mouse_click_sound(test_mouse_sound2, 70)
        time.sleep(0.2)

        print(f"\nTest Mouse Click (Not Loaded): 'click_3'")
        player.play_mouse_click_sound("click_3", 80) # 캐시에 없으므로 경고 예상
        time.sleep(0.1)

        print("\n--- Mouse Playback Tests Finished ---")

    player.unload()
    print("Test finished.") 