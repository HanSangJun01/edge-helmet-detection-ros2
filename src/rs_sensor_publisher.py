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

bridge = CvBridge()


class SensorPublisher(Node):
    def __init__(self, args: argparse.Namespace):
        super().__init__("sensor_publisher")

        self.args = args
        self.rs_sensor_publisher = self.create_publisher(RsSensors, "rs_sensors_data", 1)

        self.sensor = rs_sensors()
        self.sensor.connect()
        self.sensor.stream()

        time_period = 0.01
        self.timer = self.create_timer(time_period, self.rgbd_callback)

    def rgbd_callback(self) -> None:
        msg = RsSensors()
        intrin_msg = RsIntrin()

        data = self.sensor.get_frame(align=True)

        msg.width = data["width"]
        msg.height = data["height"]
        msg.dt = data["time"]

        intrin = data["depth_intrinsics"]
        intrin_msg.fx = intrin["fx"]
        intrin_msg.fy = intrin["fy"]
        intrin_msg.ppx = intrin["ppx"]
        intrin_msg.ppy = intrin["ppy"]
        intrin_msg.width = intrin["width"]
        intrin_msg.height = intrin["height"]

        msg.intrin = intrin_msg

        color_image, depth_image = data["color"], data["depth"]

        color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
        msg.rgb = bridge.cv2_to_imgmsg(color_image, encoding="rgb8")
        msg.depth = bridge.cv2_to_imgmsg(depth_image)
        msg.points = self.create_pointcloud2_message(data["points"])

        self.rs_sensor_publisher.publish(msg)
        self.get_logger().debug("Published rs_sensors_data")

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
        buf = [
            struct.pack("fffff", point[0], point[1], point[2], uv[0], uv[1])
            for point, uv in zip(verts, texcoords)
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
            data=b"".join(buf),
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
        node.destroy_node()
        try:
            node.sensor.pipeline.stop()
        except Exception:
            pass
        rclpy.shutdown()


if __name__ == "__main__":
    main()
