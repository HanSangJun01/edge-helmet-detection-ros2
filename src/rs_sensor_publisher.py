import argparse
import struct

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import Header

from rs_msgs.msg import RsIntrin, RsSensors
from rs_pkg.rs_sensor import rs_sensors


class SensorPublisher(Node):
    """Publish RealSense color/depth/pointcloud data through RsSensors."""

    def __init__(self, args: argparse.Namespace):
        super().__init__("sensor_publisher")

        self.args = args
        self.bridge = CvBridge()
        self.rs_sensor_publisher = self.create_publisher(RsSensors, "rs_sensors_data", 1)

        self.sensor = rs_sensors()
        self.sensor.connect()
        self.sensor.stream()

        self.timer = self.create_timer(0.01, self.rgbd_callback)

    def rgbd_callback(self) -> None:
        msg = RsSensors()
        intrin_msg = RsIntrin()

        data = self.sensor.get_frame(align=True)

        msg.width = int(data["width"])
        msg.height = int(data["height"])
        msg.dt = float(data["time"])

        intrin = data["depth_intrinsics"]
        intrin_msg.fx = float(intrin["fx"])
        intrin_msg.fy = float(intrin["fy"])
        intrin_msg.ppx = float(intrin["ppx"])
        intrin_msg.ppy = float(intrin["ppy"])
        intrin_msg.width = int(intrin["width"])
        intrin_msg.height = int(intrin["height"])
        msg.intrin = intrin_msg

        color_image = cv2.cvtColor(data["color"], cv2.COLOR_BGR2RGB)
        depth_image = data["depth"]

        msg.rgb = self.bridge.cv2_to_imgmsg(color_image, encoding="rgb8")
        msg.depth = self.bridge.cv2_to_imgmsg(depth_image)
        msg.points = self.create_pointcloud2_message(data["points"])

        self.rs_sensor_publisher.publish(msg)

    def create_pointcloud2_message(self, points) -> PointCloud2:
        header = Header(frame_id="map")
        header.stamp = self.get_clock().now().to_msg()

        fields = [
            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name="u", offset=12, datatype=PointField.FLOAT32, count=1),
            PointField(name="v", offset=16, datatype=PointField.FLOAT32, count=1),
        ]

        verts, texcoords = points["verts"], points["texcoords"]
        buffer = [
            struct.pack("fffff", p[0], p[1], p[2], uv[0], uv[1])
            for p, uv in zip(verts, texcoords)
        ]

        return PointCloud2(
            header=header,
            height=1,
            width=len(verts),
            is_dense=False,
            is_bigendian=False,
            fields=fields,
            point_step=len(fields) * 4,
            row_step=len(fields) * 4 * len(verts),
            data=b"".join(buffer),
        )


def main(args=None):
    parser = argparse.ArgumentParser(description="RS sensor publisher")
    parsed_args = parser.parse_args()

    rclpy.init(args=args)
    node = SensorPublisher(parsed_args)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Publish stopped")
    finally:
        try:
            node.sensor.pipeline.stop()
        except Exception:
            pass
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
