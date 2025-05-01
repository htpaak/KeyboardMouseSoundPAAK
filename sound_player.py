# 사운드 플레이어 모듈
import pygame
import os
import time # 사운드 중복 재생 방지용

# kbsim-master 분석 기반: release 시 특정 사운드가 있는 키들
# (kbsim 코드의 keySounds[switchValue].press 객체에 존재하는 키들)
# 실제 kbsim 구현에서는 동적으로 로드되지만, 여기서는 일반적인 키들을 기준으로 정의
SPECIAL_RELEASE_KEYS = {
    'BACKSPACE', 'TAB', 'ENTER', 'CAPSLOCK', 'SHIFT', 'CTRL', 'ALT', 'SPACE',
    'ESC', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
    'PRTSC', 'SCROLLLOCK', 'PAUSE', 'INSERT', 'HOME', 'PGUP', 'DELETE', 'END', 'PGDN',
    'UP', 'DOWN', 'LEFT', 'RIGHT', 'WIN', 'MENU', 'NUMLOCK'
    # 숫자패드 키 등 필요시 추가
}

class SoundPlayer:
    def __init__(self):
        """사운드 플레이어 초기화"""
        self.base_sound_folder = os.path.join("src", "audio")
        self.mixer_initialized = False
        self.last_play_time = {} # 키별 마지막 재생 시간 기록 (중복 방지용)
        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(32)
            self.mixer_initialized = True
            print("Sound player initialized with 32 channels.")
        except pygame.error as e:
            print(f"Failed to initialize pygame mixer: {e}")
            pygame.mixer.quit()

    def _find_sound_file(self, sound_type, event_type, key_name, row_index=None):
        """지정된 경로에서 키에 맞는 사운드 파일(.wav 또는 .mp3)을 찾습니다.
           kbsim 규칙에 따라 fallback 파일을 결정합니다.

        Args:
            sound_type (str): 사운드 종류 (폴더명).
            event_type (str): "press" 또는 "release".
            key_name (str): 대상 키 이름 (예: 'A', 'SPACE').
            row_index (int, optional): 키의 행 인덱스 (0-4). press 이벤트에만 사용됨.

        Returns:
            str or None: 찾은 사운드 파일 경로 또는 None.
        """
        if not self.mixer_initialized or key_name is None:
            return None

        specific_folder = os.path.join(self.base_sound_folder, sound_type, event_type)
        # print(f"[DEBUG] Finding sound: Type='{sound_type}', Event='{event_type}', Key='{key_name}', Row={row_index}") # 로그는 잠시 주석처리

        # --- Press 이벤트 처리 로직 변경 --- #
        if event_type == "press":
            # 1. Backspace, Space, Enter 인 경우: 개별 파일 먼저 시도
            if key_name in ["BACKSPACE", "SPACE", "ENTER"]:
                for ext in [".wav", ".mp3"]:
                    specific_path = os.path.join(specific_folder, f"{key_name}{ext}")
                    if os.path.exists(specific_path):
                        return specific_path
                # 개별 파일 없으면 fallback 으로 진행 (아래에서 처리)

            # 2. 그 외 모든 키 (또는 위 키들의 개별 파일이 없는 경우): Fallback 사용
            fallback_name = None
            if row_index is not None and 0 <= row_index <= 4:
                fallback_name = f"GENERIC_R{row_index}"
            else:
                fallback_name = "GENERIC_R4"

            if fallback_name:
                for ext in [".wav", ".mp3"]:
                    fallback_path = os.path.join(specific_folder, f"{fallback_name}{ext}")
                    if os.path.exists(fallback_path):
                        return fallback_path
            # Fallback도 없으면 None 반환
            return None

        # --- Release 이벤트 처리 로직 (이전과 동일) --- #
        elif event_type == "release":
            # 1. 개별 키 파일 탐색 (모든 키에 대해 시도)
            for ext in [".wav", ".mp3"]:
                specific_path = os.path.join(specific_folder, f"{key_name}{ext}")
                if os.path.exists(specific_path):
                    return specific_path

            # 2. 개별 파일 없고 Backspace, Space, Enter 가 아니면 GENERIC Fallback
            fallback_name = None
            if key_name not in ["BACKSPACE", "SPACE", "ENTER"]:
                 fallback_name = "GENERIC"

            if fallback_name:
                for ext in [".wav", ".mp3"]:
                    fallback_path = os.path.join(specific_folder, f"{fallback_name}{ext}")
                    if os.path.exists(fallback_path):
                        return fallback_path
            # Fallback도 없으면 None 반환
            return None

        # event_type 이 press 나 release 가 아닌 경우
        return None

    def play_key_sound(self, sound_type, event_type, key_name, volume_percent, row_index=None):
        """키 이벤트에 맞는 사운드를 찾아 재생합니다. (행 정보 추가)

        Args:
            sound_type (str): 사운드 종류 (예: "Typewriter").
            event_type (str): 이벤트 종류 ("press" 또는 "release").
            key_name (str): 사운드 파일 이름과 매칭될 키 이름.
            volume_percent (int): 볼륨 크기 (0 ~ 100).
            row_index (int, optional): 키의 행 인덱스 (press 이벤트 시).
        """
        if not self.mixer_initialized:
            return

        # 중복 재생 방지 (개선: 키 이름뿐 아니라 타입과 이벤트도 고려)
        current_time = time.time()
        sound_full_key = f"{sound_type}_{event_type}_{key_name}"
        last_played = self.last_play_time.get(sound_full_key, 0)
        # 재생 간격 임계값 (ms). 너무 짧으면 건너뜀.
        min_interval = 0.03 # 30ms
        if current_time - last_played < min_interval:
             # print(f"Skipping duplicate play for {sound_full_key}")
             return

        # 행 정보를 포함하여 사운드 파일 찾기
        sound_path = self._find_sound_file(sound_type, event_type, key_name, row_index)

        # --- 로그 추가: 최종 선택된 사운드 경로 출력 --- #
        if sound_path:
            print(f"[DEBUG] Play Sound: Path='{sound_path}'")
        else:
            # 파일 못 찾은 경우는 _find_sound_file 내부 로그로 확인 가능
            # print(f"[DEBUG] Play Sound: No sound file found for {sound_type}/{event_type}/{key_name}")
            pass # 파일 없으면 아무것도 재생 안 함

        if sound_path:
            try:
                sound = pygame.mixer.Sound(sound_path)
                volume_float = max(0.0, min(1.0, volume_percent / 100.0))
                sound.set_volume(volume_float)
                channel = pygame.mixer.find_channel(True)
                if channel:
                    channel.play(sound)
                    self.last_play_time[sound_full_key] = current_time
                    # print(f"Playing: {sound_path} on channel {channel}")
                # else: # 채널 부족 메시지는 너무 자주 나올 수 있어 주석 처리
                    # print("No available channels to play sound.")
            except pygame.error as e:
                print(f"Error playing sound '{sound_path}': {e}")
            except Exception as e:
                print(f"Unexpected error playing sound '{sound_path}': {e}")

    def unload(self):
        """pygame mixer 종료"""
        if self.mixer_initialized:
            pygame.mixer.quit()
            self.mixer_initialized = False
            print("Sound player unloaded.")


# --- 테스트용 코드 --- (수정됨)
if __name__ == '__main__':

    # --- 테스트 환경 설정 --- (폴더 및 샘플 파일 생성)
    test_base_folder = os.path.join("src", "audio")
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

    print("Setting up test environment...")
    for stype in sound_types_to_test:
        # Press 폴더 및 파일 생성
        press_folder = os.path.join(test_base_folder, stype, "press")
        os.makedirs(press_folder, exist_ok=True)
        print(f"Ensured directory exists: {press_folder}")
        for key in sample_keys_press["specific"]:
             filepath = os.path.join(press_folder, f"{key}.wav")
             if not os.path.exists(filepath): open(filepath, 'w').close(); print(f"Created dummy: {filepath}")
        for key in sample_keys_press["fallback"].values():
             filepath = os.path.join(press_folder, f"{key}.wav")
             if not os.path.exists(filepath): open(filepath, 'w').close(); print(f"Created dummy: {filepath}")

        # Release 폴더 및 파일 생성
        release_folder = os.path.join(test_base_folder, stype, "release")
        os.makedirs(release_folder, exist_ok=True)
        print(f"Ensured directory exists: {release_folder}")
        for key in sample_keys_release["specific"]:
             filepath = os.path.join(release_folder, f"{key}.wav")
             if not os.path.exists(filepath): open(filepath, 'w').close(); print(f"Created dummy: {filepath}")
        filepath = os.path.join(release_folder, f"{sample_keys_release['fallback']}.wav")
        if not os.path.exists(filepath): open(filepath, 'w').close(); print(f"Created dummy: {filepath}")
    print("Test environment setup complete.")
    # --- 테스트 환경 설정 끝 ---

    player = SoundPlayer()

    if player.mixer_initialized:
        print("\n--- Running Playback Tests (kbsim rules) ---")
        test_sound_type = "TestType1"
        volume = 80

        # Press 테스트
        print("\nTest Press 1: Specific key ('A', row 3 expected)")
        player.play_key_sound(test_sound_type, "press", "A", volume, row_index=3)
        time.sleep(0.1)

        print("\nTest Press 2: Specific key ('SPACE', row 5 -> use 4)")
        player.play_key_sound(test_sound_type, "press", "SPACE", volume, row_index=5) # row 5는 GENERICR4 사용 예상
        time.sleep(0.1)

        print("\nTest Press 3: Non-specific key ('Q', row 2 expected) -> Fallback GENERICR2")
        player.play_key_sound(test_sound_type, "press", "Q", volume, row_index=2)
        time.sleep(0.1)

        print("\nTest Press 4: Non-specific key ('F1', row 0 expected) -> Fallback GENERICR0")
        player.play_key_sound(test_sound_type, "press", "F1", volume, row_index=0)
        time.sleep(0.1)

        # Release 테스트
        print("\nTest Release 1: Specific release key ('SPACE')")
        player.play_key_sound(test_sound_type, "release", "SPACE", volume)
        time.sleep(0.1)

        print("\nTest Release 2: Specific release key ('ENTER')")
        player.play_key_sound(test_sound_type, "release", "ENTER", volume)
        time.sleep(0.1)

        print("\nTest Release 3: Non-specific release key ('A') -> Fallback GENERIC")
        player.play_key_sound(test_sound_type, "release", "A", volume) # 'A'는 SPECIAL_RELEASE_KEYS 에 없으므로 GENERIC 예상
        time.sleep(0.1)

        print("\nTest Release 4: Specific key ('SHIFT') but no specific file -> Fallback GENERIC")
        # SHIFT는 SPECIAL_RELEASE_KEYS에 있지만, 테스트 파일은 생성 안 함 -> GENERIC 예상
        player.play_key_sound(test_sound_type, "release", "SHIFT", volume)
        time.sleep(0.1)

        print("\n--- Playback Tests Finished ---")

    player.unload()
    print("Test finished.") 