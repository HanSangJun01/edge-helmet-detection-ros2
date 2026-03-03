import rclpy
import cv2
import numpy as np
import torch
from cv_bridge import CvBridge
from PIL import Image as PILImage
from rclpy.node import Node
from rclpy.qos import QoSProfile
from sensor_msgs.msg import Image
from torchvision.models.detection import (
    SSDLite320_MobileNet_V3_Large_Weights,
    ssdlite320_mobilenet_v3_large,
)


class DetectionNode(Node):
    """Subscribe image topic and run SSDlite object detection."""

    def __init__(self):
        super().__init__("webcam_image_subscriber")

        qos_profile = QoSProfile(depth=10)
        self.create_subscription(
            Image,
            "WebcamImage",
            self.detect_callback,
            qos_profile,
        )

        self.image = np.empty(shape=[1])
        self.bridge = CvBridge()

        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.get_logger().info(f"Device: {self.device}")

        self.weights = SSDLite320_MobileNet_V3_Large_Weights.COCO_V1
        self.net = ssdlite320_mobilenet_v3_large(weights=self.weights, score_thresh=0.5)
        self.net = self.net.to(self.device)
        self.net.eval()

        self.preprocess = self.weights.transforms()
        self.class_names = self.weights.meta["categories"]

    def detect_callback(self, data: Image) -> None:
        cv_image = self.bridge.imgmsg_to_cv2(data)

        frame_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        frame_rgb = PILImage.fromarray(frame_rgb)
        input_tensor = self.preprocess(frame_rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            detections = self.net(input_tensor)[0]

        for i in range(len(detections["boxes"])):
            box = detections["boxes"].detach().cpu()[i].numpy()
            score = float(detections["scores"].detach().cpu()[i].numpy())
            label_id = int(detections["labels"].detach().cpu()[i].numpy())
            class_name = self.class_names[label_id]

            if score > 0.5:
                xmin, ymin, xmax, ymax = box.astype(int)
                cv2.rectangle(cv_image, (xmin, ymin), (xmax, ymax), (255, 0, 0), 2)
                label = f"{score:.2f}, {class_name}"
                cv2.putText(
                    cv_image,
                    label,
                    (xmin, ymin - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 0, 0),
                    2,
                )

        cv2.imshow("object_detection", cv_image)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = DetectionNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Keyboard Interrupt (SIGINT)")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
