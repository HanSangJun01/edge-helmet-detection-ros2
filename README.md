# edge-helmet-detection-ros2

ROS2 기반 RealSense 데이터 퍼블리셔/뷰어 구성을 정리한 저장소입니다.  
아래 두 노드가 핵심입니다.

- `SensorPublisher`: 센서에서 RGB/Depth/PointCloud를 읽어 `RsSensors`로 publish
- `ViewerSubscriber`: `RsSensors`를 subscribe해서 2D/3D 뷰어로 렌더링

## 프로젝트 구조

```text
.
├── README.md
└── src
    ├── rs_sensor_publisher.py
    └── viewer_subscriber.py
```

## 토픽 및 메시지

- Topic: `rs_sensors_data`
- Message type: `rs_msgs/msg/RsSensors`
  - `rgb`: `sensor_msgs/Image`
  - `depth`: `sensor_msgs/Image`
  - `points`: `sensor_msgs/PointCloud2`
  - `intrin`: `rs_msgs/RsIntrin`
  - `width`, `height`, `dt`

## 실행 방법

> 아래 예시는 ROS2 workspace가 이미 구성되어 있고 `rs_msgs`, `rs_pkg`, `viewer_pkg`가 빌드 가능한 상태라는 가정입니다.

### 1) Publisher 실행

```bash
python3 src/rs_sensor_publisher.py
```

### 2) Subscriber 실행 (3D)

```bash
python3 src/viewer_subscriber.py --view_mode 3d --win_name URP
```

### 3) Subscriber 실행 (2D)

```bash
python3 src/viewer_subscriber.py --view_mode 2d --win_name URP_2D
```

## 뷰어 조작 키

- `z` (3D): 스케일 토글
- `r` (3D): 카메라/뷰 상태 리셋
- `p`: 일시정지 토글
- `q`: 창 종료

## 참고

- 실제 실행 시에는 ROS2 패키지 구조(`setup.py`, `package.xml`, entry point)로 옮겨 등록하는 것을 권장합니다.
- 본 저장소의 스크립트는 코드 정리/문서화 목적의 최소 구조입니다.
