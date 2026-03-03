# edge-helmet-detection-ros2

ROS2 환경에서 **센서 데이터 publish**와 **이미지 객체 검출 subscribe** 예제를 정리한 저장소입니다.

## 구성

- `src/rs_sensor_publisher.py`
  - RealSense 기반 센서 래퍼(`rs_pkg.rs_sensor.rs_sensors`)에서 프레임을 읽습니다.
  - RGB / Depth / PointCloud / Intrinsics를 `rs_msgs/msg/RsSensors`로 publish 합니다.
  - Topic: `rs_sensors_data`

- `src/viewer_subscriber.py`
  - `sensor_msgs/msg/Image` 토픽(`WebcamImage`)을 subscribe 합니다.
  - `torchvision`의 `ssdlite320_mobilenet_v3_large`(COCO pretrained)로 객체 검출을 수행합니다.
  - OpenCV 창(`object_detection`)에 바운딩 박스/레이블을 그려 실시간 표시합니다.

## 프로젝트 구조

```text
.
├── README.md
└── src
    ├── rs_sensor_publisher.py
    └── viewer_subscriber.py
```

## 실행 예시

> 아래 패키지/의존성이 설치되어 있다고 가정합니다: `rclpy`, `cv_bridge`, `torch`, `torchvision`, `opencv-python`, `Pillow`, `rs_msgs`, `rs_pkg`.

### 1) RealSense Publisher 실행

```bash
python3 src/rs_sensor_publisher.py
```

### 2) Detection Subscriber 실행

```bash
python3 src/viewer_subscriber.py
```

## 토픽 요약

- Publisher output:
  - `rs_sensors_data` (`rs_msgs/msg/RsSensors`)

- Detection subscriber input:
  - `WebcamImage` (`sensor_msgs/msg/Image`)

## 참고

- 현재 subscriber는 `WebcamImage` 단일 이미지 토픽을 대상으로 검출합니다.
- `rs_sensors_data.rgb`를 직접 받아 검출하려면 메시지 타입(`RsSensors`) 기반으로 subscriber 콜백을 변경하면 됩니다.
