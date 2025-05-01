# 마우스 리스너 모듈
from pynput import mouse
import threading
import logging

logger = logging.getLogger(__name__)

class MouseListener:
    def __init__(self, on_click_callback=None):
        """마우스 리스너 초기화

        Args:
            on_click_callback: 마우스 클릭 시 호출될 함수 (x, y, button, pressed 전달).
        """
        self.on_click_callback = on_click_callback
        self.listener_thread = None
        self.listener = None
        self.stop_event = threading.Event()

    def _on_click(self, x, y, button, pressed):
        """pynput 리스너 내부 콜백. 메인 콜백 호출."""
        if self.on_click_callback:
            try:
                # logger.debug(f"Mouse click: x={x}, y={y}, button={button}, pressed={pressed}") # 상세 로그
                self.on_click_callback(x, y, button, pressed)
            except Exception as e:
                logger.error(f"Error in mouse on_click callback: {e}", exc_info=True)

    def _run_listener(self):
        """리스너 실행 및 이벤트 루프 시작 (별도 스레드에서 실행)"""
        try:
            # Listener 생성 및 시작
            with mouse.Listener(on_click=self._on_click) as self.listener:
                logger.info("Mouse listener started.")
                # self.listener.join() # join은 stop() 호출 시까지 블록킹됨
                # stop_event를 사용하여 외부에서 중지 신호를 받을 때까지 대기
                self.stop_event.wait()
        except Exception as e:
            # 특정 환경에서는 권한 문제 등으로 리스너 시작 실패 가능
            logger.error(f"Failed to start mouse listener: {e}", exc_info=True)
        finally:
            logger.info("Mouse listener thread finished.")
            self.listener = None # 리스너 참조 제거

    def start_listening(self):
        """마우스 이벤트 리스닝을 별도 스레드에서 시작합니다."""
        if self.listener_thread and self.listener_thread.is_alive():
            logger.warning("Mouse listener is already running.")
            return

        self.stop_event.clear() # 중지 이벤트 초기화
        self.listener_thread = threading.Thread(target=self._run_listener, daemon=True)
        self.listener_thread.start()

    def stop_listening(self):
        """마우스 이벤트 리스닝을 중지합니다."""
        if not self.listener_thread or not self.listener_thread.is_alive():
            logger.warning("Mouse listener is not running.")
            return

        logger.info("Stopping mouse listener...")
        # pynput 리스너의 stop()은 내부 스레드에서 호출해야 안전할 수 있음
        # 여기서는 stop_event를 설정하여 _run_listener 루프가 종료되도록 함
        self.stop_event.set()

        # 리스너 스레드가 완전히 종료될 때까지 잠시 대기 (선택 사항)
        # self.listener_thread.join(timeout=1.0)

        # pynput 리스너 객체 직접 중지 (스레드 안전성 고려 필요)
        # if self.listener:
        #     try:
        #         self.listener.stop()
        #     except Exception as e:
        #         # Listener 스레드 외부에서 stop() 호출 시 발생 가능
        #         logger.error(f"Error stopping pynput mouse listener: {e}")

        self.listener_thread = None
        logger.info("Mouse listener stop signal sent.")

# 테스트용 코드 (선택 사항)
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    def test_on_click(x, y, button, pressed):
        action = "Pressed" if pressed else "Released"
        print(f"Mouse {action} at ({x}, {y}) with {button}")

    listener = MouseListener(on_click_callback=test_on_click)
    listener.start_listening()

    try:
        # 메인 스레드 유지 (예: 10초 동안 리스닝)
        print("Listening for mouse clicks for 10 seconds...")
        time.sleep(10)
    except KeyboardInterrupt:
        print("Interrupted.")
    finally:
        listener.stop_listening()
        print("Listener stopped.") 