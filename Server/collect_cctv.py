#!/usr/bin/env python3

import subprocess
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Tuple
import yaml
import os
import sys

# ================= 설정 구간 =================
CONFIG_FILE = __file__.replace("collect_cctv.py", "config.yaml")


# ================= 함수 구간 =================
def load_config(CONFIG_FILE: str | os.PathLike) -> dict:
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} 파일이 없습니다.")
        sys.exit(1)

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def sync_single_pi(host: str, REMOTE_DIR: str, LOCAL_BASE_DIR: str) -> Tuple[bool, str]:
    """
    개별 라즈베리파이에서 데이터를 수집하는 함수
    """
    success = False
    message = ""
    try:
        # [단계 1] 저장할 로컬 폴더 생성
        local_path = f"{LOCAL_BASE_DIR}/{host}"
        subprocess.run(["mkdir", "-p", local_path], check=True)

        # [단계 2] 가져올 파일 목록 조회 (SSH)
        # find -mmin +1: 마지막 수정 후 1분 지난 파일만 (녹화 중인 파일 제외)
        find_cmd = [
            "ssh",
            host,
            f"find '{REMOTE_DIR}' -name '*' -mmin +1 -type f",
        ]

        # SSH 실행 및 결과 캡처
        result = subprocess.run(find_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return False, f"[{host}] SSH 접속 실패 또는 에러: {result.stderr.strip()}"

        files_to_sync = result.stdout.strip()

        if not files_to_sync:
            return False, f"[{host}] 가져올 파일 없음."

        file_count = len(files_to_sync.split("\n"))

        # [단계 3] Rsync 실행 (파일 목록을 파이프로 넘김)
        rsync_cmd = [
            "rsync",
            "-avz",
            # f"--bwlimit={RSYNC_BWLIMIT}",  # 대역폭 제한
            "--remove-source-files",  # 전송 후 원본 삭제 (RAM 비우기)
            "--files-from=-",  # 표준 입력에서 목록 읽기
            "--no-relative",  # 경로 단순화
            f"{host}:/",  # 소스 (루트 기준)
            f"{local_path}/",  # 목적지
        ]

        # subprocess.run의 input 인자로 파일 목록 문자열을 넘겨줌 (파이프 역할)
        rsync_result = subprocess.run(
            rsync_cmd,
            input=files_to_sync.encode("utf-8"),  # 문자열을 바이트로 변환
            capture_output=True,
        )

        if rsync_result.returncode == 0:
            success = True
            message = f"[{host}] Rsync 성공: {file_count}개 파일 수집 완료."
        else:
            success = False
            message = f"[{host}] Rsync 실패: {rsync_result.stderr.decode().strip()}"

    except Exception as e:
        message = str(e)

    return success, message


def main():

    # 설정 로드
    config = load_config(CONFIG_FILE)

    REMOTE_DIR = config["settings"].get("remote_source_dir", "/home/pi/cctv_buffer")
    LOCAL_BASE_DIR = config["settings"].get(
        "local_storage_dir", "/home/wcl/cctv_collection"
    )
    BATCH_SIZE = config["settings"].get("batch_size", 5)

    PI_HOSTS = config.get("target_hosts", [])

    if os.path.exists(LOCAL_BASE_DIR) is False:
        print(f"로컬 저장 경로 {LOCAL_BASE_DIR}가 없습니다.")
        sys.exit(1)

    if not PI_HOSTS:
        print("수집 대상 라즈베리파이 IP 목록이 비어 있습니다.")
        sys.exit(1)

    start_time = time.time()
    print(f"=== CCTV 수집 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    print(f"총 {len(PI_HOSTS)}대, {BATCH_SIZE}대씩 끊어서 실행")

    results = {}
    # ThreadPoolExecutor를 사용하여 병렬 처리
    with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        future_to_host = {
            executor.submit(sync_single_pi, host, REMOTE_DIR, LOCAL_BASE_DIR): host
            for host in PI_HOSTS
        }

        for future in as_completed(future_to_host):
            host = future_to_host[future]
            try:
                result = future.result()
                results[host] = result
            except Exception as exc:
                results[host] = (False, str(exc))

    # 결과 출력
    for host, (success, message) in results.items():
        status = "성공" if success else "실패"
        print(f"[{host}] 상태: {status} - {message}")

    elapsed = time.time() - start_time
    print(f"\n=== 전체 종료 (소요시간: {elapsed:.1f}초) ===")


if __name__ == "__main__":
    main()
