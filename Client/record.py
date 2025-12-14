import os
import time
import subprocess
import signal
import sys
import shutil
from datetime import datetime

# ================= 설정 구간 =================
# 저장 경로
BUFFER_DIR = "/home/pi/cctv_buffer"

# 녹화 시간 (06시 ~ 17시, 즉 17:59까지)
START_HOUR = 6
END_HOUR = 17

DATE = datetime.now().strftime("%Y%m%d_%H%M%S")
HOSTNAME = os.uname().nodename

# 카메라 설정 (서버 100Mbps 제한에 맞춘 최적값)
# 4Mbps, 24fps, 1640x1232 해상도
CMD_ARGS = [
    "rpicam-vid",
    "-n",
    "-t",
    "0",
    "--segment",
    "120000",
    "--inline",
    "--width",
    "1640",
    "--height",
    "1232",
    "--framerate",
    "24",
    "--bitrate",
    "4000000",
    "--profile",
    "high",
    "-o",
    f"{BUFFER_DIR}/{HOSTNAME}_{DATE}_%04d.h264",
]

# 디스크 용량 제한 (90% 넘으면 삭제)
DISK_THRESHOLD_PERCENT = 90
# ============================================


class CCTVRecorder:
    def __init__(self):
        self.process = None
        self.running = True

        # 종료 신호(Ctrl+C, systemctl stop) 처리
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def shutdown(self, signum, frame):
        print("[Info] 종료 신호를 받았습니다. 정리 중...")
        self.stop_camera()
        self.running = False

    def start_camera(self):
        if self.process is None:
            print(f"[Start] 녹화를 시작합니다. (Bitrate: 4Mbps)")
            # Popen으로 백그라운드 실행
            self.process = subprocess.Popen(CMD_ARGS)

    def stop_camera(self):
        if self.process:
            print("[Stop] 녹화를 종료합니다.")
            self.process.terminate()  # SIGTERM 전송 (안전 종료)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()  # 응답 없으면 강제 종료
            self.process = None

    def cleanup_disk(self):
        """디스크 용량이 부족하면 가장 오래된 파일을 지웁니다."""
        try:
            total, used, free = shutil.disk_usage(BUFFER_DIR)
            usage_percent = (used / total) * 100

            if usage_percent >= DISK_THRESHOLD_PERCENT:
                # 파일 목록을 가져와서 생성 시간순 정렬
                files = [
                    os.path.join(BUFFER_DIR, f)
                    for f in os.listdir(BUFFER_DIR)
                    if f.endswith(".h264")
                ]
                if not files:
                    return

                # 가장 오래된 파일 찾기
                oldest_file = min(files, key=os.path.getmtime)
                os.remove(oldest_file)
                print(
                    f"[Clean] 용량 부족({usage_percent:.1f}%) -> {os.path.basename(oldest_file)} 삭제됨"
                )

        except Exception as e:
            print(f"[Error] 디스크 정리 중 오류: {e}")

    def run(self):
        print(f"=== CCTV 클라이언트 시작 (Time: {START_HOUR}~{END_HOUR}) ===")

        while self.running:
            now = datetime.now()
            current_hour = now.hour

            # 1. 주간/야간 모드 확인
            if START_HOUR <= current_hour <= END_HOUR:
                # 녹화 시간인데 꺼져있으면 -> 켠다
                if self.process is None:
                    self.start_camera()
                # 켜져있으면 -> 프로세스가 죽었는지 확인 (좀비 방지)
                elif self.process.poll() is not None:
                    print("[Warn] 카메라 프로세스가 비정상 종료됨. 재시작합니다.")
                    self.process = None
            else:
                # 녹화 시간이 아닌데 켜져있으면 -> 끈다
                if self.process is not None:
                    print(f"[Sleep] 야간 모드 진입 ({current_hour}시)")
                    self.stop_camera()

            # 2. 디스크 청소 (녹화 중일 때만 수행)
            if self.process is not None:
                self.cleanup_disk()

            # 3. 대기 (10초마다 상태 체크)
            time.sleep(10)


if __name__ == "__main__":
    recorder = CCTVRecorder()
    recorder.run()
