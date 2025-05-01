import sys
import os
import ctypes
from log_setup import setup_logging
# import tkinter as tk # Tkinter 제거
from PyQt5.QtWidgets import QApplication # PyQt5 임포트
from PyQt5.QtGui import QIcon # PyQt5 임포트
from PyQt5.QtCore import Qt # Qt 임포트 추가
# from main_gui import KeyboardMouseSoundPAAK # Tkinter GUI 제거 (추후 PyQt5 GUI 임포트)

setup_logging() # 항상 호출 (내부에서 조건 확인)

COMPANY_NAME = "htpaak"
PRODUCT_NAME = "KeyboardMouseSoundPAAK"
APP_VERSION = "1.0.0" # 버전 정의 (필요시)
MYAPPID = f"{COMPANY_NAME}.{PRODUCT_NAME}.{APP_VERSION}" # AppUserModelID 정의
# --- 리소스 경로 헬퍼 함수 --- #
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        # print(f"Running in PyInstaller bundle, base path: {base_path}") # 디버깅용
    except Exception:
        # Not packaged, use normal path relative to main script
        base_path = os.path.abspath(".")
        # print(f"Running in development, base path: {base_path}") # 디버깅용

    return os.path.join(base_path, relative_path)
# --- 헬퍼 함수 끝 --- #

ICON_PATH = resource_path(os.path.join("assets", "icon.ico")) # 아이콘 경로 정의 (resource_path 사용)

# --- DPI 스케일링 활성화 (QApplication 생성 전) ---
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
print("High DPI Scaling Enabled.") # 확인 로그
# -------------------------------------------------

# --- AppUserModelID 설정 (QApplication 생성 전) ---
try:
    if os.name == 'nt':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(MYAPPID)
        print(f"Set AppUserModelID: {MYAPPID}")
except Exception as appid_e:
    print(f"Warning: Failed to set AppUserModelID: {appid_e}")
# --- AppUserModelID 설정 끝 ---


if __name__ == "__main__":
    """애플리케이션 메인 실행 지점 (PyQt5)"""
    app = QApplication(sys.argv) # QApplication 생성
    app.setQuitOnLastWindowClosed(False) # 마지막 창 닫아도 앱 종료 방지

    # --- 애플리케이션 아이콘 설정 ---
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
        print(f"Application icon set from: {ICON_PATH}")
    else:
        print(f"Warning: Icon file not found at {ICON_PATH}")
    # --- 아이콘 설정 끝 ---

    # --- 메인 윈도우 생성 및 실행 ---
    try:
        from main_gui import MainWindow # PyQt5 MainWindow 임포트
        window = MainWindow()
        window.show()
        # window.center_window() # 창 표시 후 중앙 정렬 호출 (main_gui.py의 showEvent로 이동)
        # # 임시 코드 제거
        # from PyQt5.QtWidgets import QLabel
        # window = QLabel("main_gui.py migration in progress...")
        # window.setWindowTitle("Keyboard Sound App") # 임시 제목
        # window.show()
    except ImportError as import_err:
        print(f"Error: Could not import MainWindow from main_gui.py: {import_err}")
        # PyQt5 메시지 박스를 사용하기 위해 QApplication 인스턴스가 필요
        # 하지만 이 시점에서는 app.exec_()가 호출되지 않았으므로
        # 간단한 print 후 종료하거나, 더 복잡한 오류 처리 필요
        print("Please ensure main_gui.py contains the MainWindow class.")
        sys.exit(1)
    except Exception as e:
        # 예기치 못한 오류 처리 (PyQt5 스타일)
        from PyQt5.QtWidgets import QMessageBox
        import traceback
        # QApplication 인스턴스가 생성된 후이므로 메시지 박스 사용 가능
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Fatal Error")
        msg.setText(f"An unexpected error occurred:\n\n{e}")
        msg.setDetailedText(traceback.format_exc())
        msg.exec_()
        sys.exit(1)
    # --- 메인 윈도우 끝 ---

    sys.exit(app.exec_()) # PyQt5 이벤트 루프 시작
