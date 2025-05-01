# 키보드 리스너 모듈

from pynput import keyboard

class KeyboardListener:
    def __init__(self, on_press_callback, on_release_callback):
        """리스너 초기화

        Args:
            on_press_callback (function): 키가 눌렸을 때 호출될 콜백 함수.
            on_release_callback (function): 키에서 손을 뗐을 때 호출될 콜백 함수.
                                          각 콜백 함수는 해당 키 정보를 인자로 받습니다.
        """
        self.listener = None
        self.on_press_callback = on_press_callback
        self.on_release_callback = on_release_callback # 릴리스 콜백 저장

    def on_press(self, key):
        """키가 눌렸을 때 실행될 내부 콜백 함수"""
        if self.on_press_callback:
            try:
                # 일반 키 또는 특수 키 모두 콜백 호출
                self.on_press_callback(key)
            except Exception as e:
                print(f"Error in on_press_callback: {e}")

    def on_release(self, key):
        """키에서 손을 뗐을 때 실행될 내부 콜백 함수"""
        if self.on_release_callback:
            try:
                # 일반 키 또는 특수 키 모두 콜백 호출
                self.on_release_callback(key)
            except Exception as e:
                print(f"Error in on_release_callback: {e}")
        # 예시: Esc 키를 누르면 리스너 종료 (테스트용, GUI에서는 사용 안 함)
        # if key == keyboard.Key.esc:
        #     return False

    def start_listening(self):
        """키보드 리스닝 시작"""
        if self.listener is None:
            # on_release 핸들러 추가
            self.listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release)
            self.listener.start() # 백그라운드 스레드에서 리스너 시작
            print("Keyboard listener started (press and release).")
        else:
            print("Listener already running.")

    def stop_listening(self):
        """키보드 리스닝 중지"""
        if self.listener:
            self.listener.stop()
            # self.listener.join() # join()은 GUI 스레드에서 호출 시 멈춤 현상 유발 가능성 -> GUI 종료 시 처리
            self.listener = None
            print("Keyboard listener stopped.")
        # else:
        #     print("Listener not running.")

# 테스트용 코드 (나중에 GUI와 통합 시 제거)
if __name__ == '__main__':
    import time

    def test_press_callback(key):
        try:
            print(f'Press: {key.char}')
        except AttributeError:
            print(f'Press: {key}')

    def test_release_callback(key):
        try:
            print(f'Release: {key.char}')
        except AttributeError:
            print(f'Release: {key}')
        # if key == keyboard.Key.esc:
        #     # Stop listener
        #     return False # This doesn't work well here, stop from main thread
        #     pass

    print("Starting listener test for 10 seconds...")
    listener = KeyboardListener(
        on_press_callback=test_press_callback,
        on_release_callback=test_release_callback
    )
    listener.start_listening()

    try:
        # 리스너 스레드가 실행되는 동안 메인 스레드 유지
        # time.sleep(10) # 리스너는 백그라운드에서 계속 실행됨
        listener.listener.join() # 리스너 스레드가 끝날 때까지 대기 (Esc 등으로 종료되지 않으면 무한 대기)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        print("Stopping listener...")
        listener.stop_listening()
        print("Test finished.") 