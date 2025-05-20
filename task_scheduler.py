# 작업 스케줄러 관리 모듈
import os
import sys
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
TASK_NAME = "KeyboardMouseSoundPAAK_AutoStart"

def create_admin_task(executable_path, additional_args=None):
    """
    Windows 작업 스케줄러에 관리자 권한으로 실행되는 작업을 생성합니다.
    
    Args:
        executable_path (str): 실행 파일의 절대 경로
        additional_args (str, optional): 추가적인 실행 인자
    
    Returns:
        bool: 작업 생성 성공 여부
    """
    try:
        # 실행 명령에 추가 인자 포함
        command = f'"{executable_path}"'
        if additional_args:
            command += f' {additional_args}'
        
        # 현재 사용자 이름 가져오기
        import getpass
        current_user = getpass.getuser()
        
        # XML 템플릿 작성
        xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}</Date>
    <Author>{current_user}</Author>
    <Description>KeyboardMouseSoundPAAK 애플리케이션을 부팅 시 자동 실행합니다.</Description>
    <URI>\\{TASK_NAME}</URI>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <UserId>{os.environ['COMPUTERNAME']}\\{current_user}</UserId>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{os.environ['COMPUTERNAME']}\\{current_user}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>false</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{executable_path}</Command>
      <Arguments>{additional_args or ""}</Arguments>
    </Exec>
  </Actions>
</Task>"""
        
        # 임시 XML 파일 생성
        xml_path = os.path.join(os.environ['TEMP'], f"{TASK_NAME}.xml")
        with open(xml_path, 'w', encoding='utf-16') as f:
            f.write(xml_content)
        
        # schtasks 명령어로 작업 생성
        cmd = f'schtasks /Create /TN "{TASK_NAME}" /XML "{xml_path}" /F'
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # 임시 파일 삭제
        try:
            os.remove(xml_path)
        except:
            pass
        
        # 결과 확인
        if process.returncode != 0:
            logger.error(f"작업 스케줄러 등록 실패: {process.stderr}")
            return False
        
        logger.info(f"작업 스케줄러에 등록 성공: {TASK_NAME}")
        return True
    
    except Exception as e:
        logger.error(f"작업 스케줄러 작업 생성 중 오류: {e}")
        return False

def remove_task():
    """
    작업 스케줄러에서 작업을 제거합니다.
    
    Returns:
        bool: 작업 제거 성공 여부
    """
    try:
        cmd = f'schtasks /Delete /TN "{TASK_NAME}" /F'
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if process.returncode != 0:
            # 작업이 존재하지 않는 경우는 성공으로 처리
            if "ERROR: The system cannot find the file specified." in process.stderr:
                logger.info(f"작업 제거 성공 (이미 존재하지 않음): {TASK_NAME}")
                return True
            
            logger.error(f"작업 스케줄러 작업 제거 실패: {process.stderr}")
            return False
        
        logger.info(f"작업 스케줄러에서 제거 성공: {TASK_NAME}")
        return True
    
    except Exception as e:
        logger.error(f"작업 스케줄러 작업 제거 중 오류: {e}")
        return False

def is_task_exists():
    """
    작업 스케줄러에 작업이 존재하는지 확인합니다.
    
    Returns:
        bool: 작업 존재 여부
    """
    try:
        cmd = f'schtasks /Query /TN "{TASK_NAME}"'
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        return process.returncode == 0
    
    except Exception as e:
        logger.error(f"작업 스케줄러 작업 확인 중 오류: {e}")
        return False 