import argparse

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import QoSProfile

from rs_msgs.msg import RsSensors
from viewer_pkg.point_cloud2 import read_points_numpy
from viewer_pkg.viewer import AppState


class ViewerSubscriber(Node):
    def __init__(self, args: argparse.Namespace):
        super().__init__("viewer_subscriber")

        qos = QoSProfile(depth=10)
        self.create_subscription(
            RsSensors,
            "rs_sensors_data",
            self.viewer_callback,
            qos,
        )

        self.args = args
        self.bridge = CvBridge()
        self.state = AppState()

    def viewer_callback(self, msg: RsSensors) -> None:
        win_name = self.args.win_name
        self.state.WIN_NAME = win_name

        rgb = self.bridge.imgmsg_to_cv2(msg.rgb)
        depth = self.bridge.imgmsg_to_cv2(msg.depth)

        pc_numpy = read_points_numpy(cloud=msg.points, skip_nans=True)
        points = {
            "verts": pc_numpy[:, :3],
            "texcoords": pc_numpy[:, 3:],
        }

        intrin_msg = msg.intrin
        intrin = {
            "fx": float(intrin_msg.fx),
            "fy": float(intrin_msg.fy),
            "ppx": float(intrin_msg.ppx),
            "ppy": float(intrin_msg.ppy),
            "width": int(intrin_msg.width),
            "height": int(intrin_msg.height),
        }

        data = {
            "color": rgb,
            "depth": depth,
            "width": int(msg.width),
            "height": int(msg.height),
            "points": points,
            "depth_intrinsics": intrin,
            "time": float(msg.dt),
        }

        if self.args.view_mode == "2d":
            self.state.viewer_2d(data)
        elif self.args.view_mode == "3d":
            self.state.viewer_3d(data)

        key = cv2.waitKey(1)

        if key == ord("z") and self.args.view_mode == "3d":
            self.state.scale ^= True

        if key == ord("r") and self.args.view_mode == "3d":
            self.state.reset()

        if key == ord("p"):
            self.state.paused ^= True

        if key == ord("q"):
            cv2.destroyWindow(win_name)
            raise SystemExit


def main(args=None):
    rclpy.init(args=args)
    parser = argparse.ArgumentParser()
    parser.add_argument("--view_mode", type=str, default="3d", help="2d or 3d")
    parser.add_argument(
        "--win_name", type=str, default="URP", help="viewer window title"
    )
    parsed_args = parser.parse_args()

    node = ViewerSubscriber(parsed_args)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Keyboard Interrupt (SIGINT)")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
