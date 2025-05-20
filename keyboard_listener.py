# 키보드 리스너 모듈

from pynput import keyboard
import ctypes
import os
import sys
import winreg
import threading

# Windows API 상수 정의
THREAD_SET_INFORMATION = 0x0020
THREAD_PRIORITY_TIME_CRITICAL = 15
PROCESS_SET_INFORMATION = 0x0200
HIGH_PRIORITY_CLASS = 0x00000080
REALTIME_PRIORITY_CLASS = 0x00000100

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
        self._set_keyboard_priority_in_registry()
        self._set_process_priority()

    def _set_process_priority(self):
        """현재 프로세스의 우선순위를 최대로 설정합니다."""
        try:
            # 현재 프로세스의 우선순위 클래스를 REALTIME_PRIORITY_CLASS로 설정
            process_handle = ctypes.windll.kernel32.GetCurrentProcess()
            result = ctypes.windll.kernel32.SetPriorityClass(process_handle, REALTIME_PRIORITY_CLASS)
            if result == 0:
                print(f"프로세스 우선순위 설정 실패: {ctypes.windll.kernel32.GetLastError()}")
            else:
                print("프로세스 우선순위가 REALTIME_PRIORITY_CLASS로 설정되었습니다.")
        except Exception as e:
            print(f"프로세스 우선순위 설정 중 오류 발생: {e}")

    def _set_thread_priority(self, thread_id=None):
        """지정된 스레드의 우선순위를 최대로 설정합니다."""
        try:
            # 스레드 ID가 제공되지 않은 경우 현재 스레드 ID 사용
            if thread_id is None:
                thread_id = threading.current_thread().ident

            # 스레드 핸들 가져오기
            thread_handle = ctypes.windll.kernel32.OpenThread(
                THREAD_SET_INFORMATION, False, thread_id)
            
            if thread_handle == 0:
                print(f"스레드 핸들 획득 실패: {ctypes.windll.kernel32.GetLastError()}")
                return False
            
            # 스레드 우선순위 설정
            result = ctypes.windll.kernel32.SetThreadPriority(
                thread_handle, THREAD_PRIORITY_TIME_CRITICAL)
            
            # 핸들 닫기
            ctypes.windll.kernel32.CloseHandle(thread_handle)
            
            if result == 0:
                print(f"스레드 우선순위 설정 실패: {ctypes.windll.kernel32.GetLastError()}")
                return False
            else:
                print(f"스레드 ID {thread_id}의 우선순위가 TIME_CRITICAL로 설정되었습니다.")
                return True
        except Exception as e:
            print(f"스레드 우선순위 설정 중 오류 발생: {e}")
            return False

    def _set_keyboard_priority_in_registry(self):
        """레지스트리를 사용하여 키보드 입력 우선순위를 최대로 설정합니다."""
        try:
            # 레지스트리 키 경로
            reg_path = r"SYSTEM\CurrentControlSet\Control\PriorityControl"
            
            # 관리자 권한으로 레지스트리 키 열기
            try:
                reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, 
                                         winreg.KEY_WRITE)
            except PermissionError:
                print("레지스트리 수정을 위해 관리자 권한이 필요합니다.")
                if not self._is_admin():
                    print("프로그램을 관리자 권한으로 재시작하세요.")
                return False
            
            # 키보드 우선순위 값 설정 (IRQ8Priority = 1)
            winreg.SetValueEx(reg_key, "IRQ8Priority", 0, winreg.REG_DWORD, 1)
            # 키보드 입력 처리 우선순위 값 설정 (Win32PrioritySeparation = 2)
            winreg.SetValueEx(reg_key, "Win32PrioritySeparation", 0, winreg.REG_DWORD, 2)
            
            winreg.CloseKey(reg_key)
            print("레지스트리에 키보드 우선순위 설정이 완료되었습니다.")
            return True
        except Exception as e:
            print(f"레지스트리 설정 중 오류 발생: {e}")
            return False

    def _is_admin(self):
        """현재 프로세스가 관리자 권한으로 실행 중인지 확인합니다."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

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

    def win32_event_filter(self, msg, data):
        """Windows에서 키 이벤트 필터링 함수
        
        최저 권한 수준으로 키 입력을 감지하고, 최우선순위로 처리합니다.
        """
        # 현재 리스너 스레드의 우선순위를 최대로 설정
        self._set_thread_priority()
        
        # WH_KEYBOARD_LL 후킹을 위한 설정으로, 다른 프로그램보다 낮은 권한으로 실행
        # 이벤트를 통과시키고(True), 다른 애플리케이션에 영향을 미치지 않게 함
        return True

    def start_listening(self):
        """키보드 리스닝 시작"""
        if self.listener is None:
            # win32_event_filter 추가 - 최저 권한으로 키 감지하고 최우선순위로 처리하기 위한 함수
            self.listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release,
                win32_event_filter=self.win32_event_filter)
            
            # 시작 전에 리스너 스레드의 우선순위를 최대로 설정할 준비
            self.listener.daemon = True  # 데몬 스레드로 설정하여 메인 스레드 종료 시 함께 종료되도록 함
            self.listener.start() # 백그라운드 스레드에서 리스너 시작
            
            # 리스너 스레드 ID 얻기 및 우선순위 설정
            if hasattr(self.listener, 'ident'):
                self._set_thread_priority(self.listener.ident)
            
            print("Keyboard listener started with maximum priority (system-wide).")
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