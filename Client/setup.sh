#!/bin/bash
# Client/setup.sh

echo "=== CCTV 서비스 설치 시작 ==="

# 1. 루트 권한 확인
if [ "$EUID" -ne 0 ]; then
  echo "오류: 이 스크립트는 root 권한(sudo)으로 실행해야 합니다."
  exit 1
fi

# 2. 작업 디렉토리 설정 (절대 경로 확보)
REPO_DIR=$(pwd)
SCRIPT_PATH="$REPO_DIR/Client/record.sh"
SERVICE_SOURCE="$REPO_DIR/Client/rpi-cctv-client.service"
SERVICE_DEST="/etc/systemd/system/cctv.service"

# 3. record.sh 실행 권한 부여
chmod +x "$SCRIPT_PATH"
echo "[OK] 실행 권한 부여 완료"

# 4. RAM Disk 설정 (fstab에 없으면 추가)
if ! grep -q "cctv_buffer" /etc/fstab; then
    echo "[Info] RAM Disk(1GB) 설정 추가 중..."
    echo "# for rpi-cctv Client" >> /etc/fstab
    echo "tmpfs /home/pi/cctv_buffer tmpfs defaults,noatime,nosuid,size=1G 0 0" >> /etc/fstab
    mkdir -p /home/pi/cctv_buffer
    mount -a # 즉시 적용
    echo "[OK] RAM Disk 설정 완료"
else
    echo "[Skip] RAM Disk 설정이 이미 존재합니다."
fi

# 5. systemd 서비스 파일 수정 및 등록
echo "[Info] 서비스 등록 중..."

# rpi-cctv-client.service 템플릿 파일에서 ExecStart 경로를 현재 위치로 바꿔서 복사
sed "s|ExecStart=.*|ExecStart=$SCRIPT_PATH|" "$SERVICE_SOURCE" > "$SERVICE_DEST"

# 6. 서비스 재로딩 및 활성화
systemctl daemon-reload
systemctl enable rpi-cctv-client.service
systemctl restart rpi-cctv-client.service

echo "=== 설치 완료! 서비스가 시작되었습니다. ==="
systemctl status rpi-cctv-client.service --no-pager