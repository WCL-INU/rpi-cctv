import threading
import time
from dataclasses import dataclass
from typing import Iterator, Optional

import cv2
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from picamera2 import Picamera2

# YOLO inference removed — streaming-only client


@dataclass
class AppConfig:
    capture_interval: float = 0.5
    jpeg_quality: int = 80
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


def load_config() -> AppConfig:
    """Load runtime configuration from environment variables."""
    return AppConfig(
        capture_interval=0.03,
        jpeg_quality=80,
        host="0.0.0.0",
        port=8000,
        debug=False,
    )


class CameraInferenceService:
    """Continuously grab frames from Picamera2 and publish JPEG streams."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.picam2 = Picamera2()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._condition = threading.Condition()
        self._latest_original: Optional[bytes] = None
        self._frame_seq: int = 0

    def start(self) -> None:
        camera_config = self.picam2.create_video_configuration(
            main={"size": (1640, 1232), "format": "RGB888"},
            buffer_count=32,
            sensor={"bit_depth": 8},
            controls={"FrameDurationLimits": (10000, 33333)},
        )
        self.picam2.configure(camera_config)
        self.picam2.start()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        try:
            self.picam2.stop()
        except Exception:
            pass
        try:
            self.picam2.close()
        except Exception:
            pass

    def frame_generator(self) -> Iterator[bytes]:
        boundary = b"--frame"
        last_seq = -1
        while not self._stop.is_set():
            with self._condition:
                while last_seq == self._frame_seq and not self._stop.is_set():
                    self._condition.wait(timeout=1.0)
                if self._stop.is_set():
                    break
                frame = self._latest_original

                seq = self._frame_seq
            if frame is None:
                continue
            last_seq = seq
            yield (boundary + b"\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

    def _loop(self) -> None:
        """Capture frames, store original/detection images, and publish latest paths."""
        jpeg_quality = int(max(10, min(95, self.config.jpeg_quality)))
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
        while not self._stop.is_set():
            try:
                bgr = self.picam2.capture_array()
            except Exception as exc:
                print(f"Camera capture failed: {exc}")
                time.sleep(0.2)
                continue

            if bgr is None:
                time.sleep(0.05)
                continue

            ok_orig, orig_buf = cv2.imencode(".jpg", bgr, encode_params)
            if not ok_orig:
                print("JPEG encoding failed, skipping frame.")
                continue

            with self._condition:
                self._latest_original = orig_buf.tobytes()
                self._frame_seq += 1
                self._condition.notify_all()

            if self.config.capture_interval > 0:
                time.sleep(self.config.capture_interval)


template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
    <title>Live Camera Stream</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; background: #f3f3f3; }
    .wrapper { background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
    .images { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-top: 12px; }
    img { width: 100%; border: 1px solid #ddd; border-radius: 6px; background: #fafafa; min-height: 160px; }
    h1 { margin-bottom: 4px; }
    p { margin: 0; }
  </style>
</head>
<body>
    <div class="wrapper">
    <h1>Camera Monitor</h1>
    <div class="images">
      <div>
        <img id="img-original" src="/stream" alt="Original stream">
      </div>
    </div>
  </div>
</body>
</html>
"""


class SimpleHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            body = template.encode("utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/stream":
            # MJPEG stream
            try:
                self.send_response(200)
                self.send_header(
                    "Content-Type", "multipart/x-mixed-replace; boundary=frame"
                )
                self.end_headers()
                svc = globals().get("service")
                if svc is None:
                    return
                for chunk in svc.frame_generator():
                    try:
                        self.wfile.write(chunk)
                    except BrokenPipeError:
                        break
            except Exception:
                pass
            return

        self.send_response(404)
        self.end_headers()


def main() -> None:
    config = load_config()
    # Streaming-only: do not create a YOLO model
    service = CameraInferenceService(config)
    # Expose service to the HTTP handler
    globals()["service"] = service
    service.start()
    httpd = HTTPServer((config.host, config.port), SimpleHandler)
    print(f"Serving live stream at http://{config.host}:{config.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            httpd.shutdown()
        except Exception:
            pass
        service.stop()


if __name__ == "__main__":
    main()
