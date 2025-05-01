import sys
from log_setup import setup_logging
import tkinter as tk
from main_gui import KeyboardSoundApp

setup_logging() # 항상 호출 (내부에서 조건 확인)

# 애플리케이션의 메인 로직을 여기에 작성하세요.
# 예: import my_app
#     my_app.run()

if __name__ == "__main__":
    """애플리케이션 메인 실행 지점"""
    try:
        root = tk.Tk() # 메인 Tkinter 윈도우 생성
        app = KeyboardSoundApp(root) # 애플리케이션 클래스 인스턴스화
        root.mainloop() # Tkinter 이벤트 루프 시작
    except Exception as e:
        # 예기치 못한 오류 발생 시 사용자에게 알림 (선택적)
        import traceback
        from tkinter import messagebox
        # GUI가 초기화되지 않았을 수도 있으므로 간단한 메시지 박스 시도
        try:
            # 간단한 임시 루트 생성 시도
            error_root = tk.Tk()
            error_root.withdraw() # 창 숨김
            messagebox.showerror("Fatal Error", f"An unexpected error occurred:\n\n{e}\n\nTraceback:\n{traceback.format_exc()}")
            error_root.destroy()
        except Exception:
            # GUI 조차 안될 경우 콘솔 출력
            print("--- FATAL ERROR ---")
            print(f"An unexpected error occurred: {e}")
            print("Traceback:")
            print(traceback.format_exc())
        finally:
            # 프로그램 종료
            sys.exit(1)
