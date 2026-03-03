###======================= 라이브러리 호출 부분 =======================

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from sensor_msgs.msg import Image
import numpy as np
import cv2
from cv_bridge import CvBridge
import torch
from torch.utils.data import Dataset,DataLoader
import torchvision.models as models
from torchvision import transforms
from PIL import Image as Image1

###===================================================================
        
## For detection
from torchvision.models.detection import ssdlite320_mobilenet_v3_large, SSDLite320_MobileNet_V3_Large_Weights
from torchvision.utils import draw_bounding_boxes
from torchvision.transforms.functional import to_pil_image, pil_to_tensor

#from ssd_detection.misc import Timer ## 작성한 타이머 관련 코드 import

bridge = CvBridge()

class DetectionNode(Node):

    def __init__(self):
        
        ###======================= 토픽 관련 세팅 =======================
		
        super().__init__('WebcamImage_subscriber') # 부모 클래스(Node)의 생성자를 호출하고 이름을 helloworld_publisher로 지정
        qos_profile = QoSProfile(depth=10) # 통신상태가 원활하지 못할 경우 퍼블리시 할 데이터를 버퍼에 10개까지 저장하라는 설정
        self.WebcamImage_subscriber = self.create_subscription( # create_subscription함수를 이용해 helloworld_subscriber 설정
            Image, # 토픽 메시지 타입
            'WebcamImage', # 토픽 이름
            self.detect_callback, # 수신 받은 메세지를 처리할 콜백함수 **
            qos_profile) # QoS: qos_profile
        self.image = np.empty(shape=[1])
  
  
  
		###===================================================================
        
        ###======================= SSD 설정 부분 =======================**
        
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu") ## Device 사용 가능한지 확인
        self.get_logger().info("Device: %s "%(self.device)) ## device 정보 확인
        self.weights = SSDLite320_MobileNet_V3_Large_Weights.COCO_V1 ## mobilenet을 backbone으로 하는 사전학습 모델 불러오기
        #=====
        # ## ver1. torchvision의 checkpoint 이용
        self.net = ssdlite320_mobilenet_v3_large(weights=self.weights, score_thresh=0.5).cuda() ## SSD_mobilenet 모델 선언후 GPU로 올리기
        ## ver2. custom checkpoint 이용
        # self.ckpoint = torch.load("./src/ssd_detection/COCO_CheckPoint.pth") ## 체크포인트 경로 지정
        # self.net = self.ckpoint['model'].cuda() ## SSD_mobilenet 모델 선언후 GPU로 올리기
        # self.net.score_thresh=0.9
        #=====        
        self.net.eval() ## 평가모드로 설정

       
        self.preprocess = self.weights.transforms() ## transform 정보 받아오기
        #=====
        # ## ver1. torchvision의 checkpoint 이용
        self.class_names = self.weights.meta["categories"] ## 카테고리 정보 받아오기(COCO데이터셋)
        print(self.class_names)
        ## ver2. custom checkpoint 이용
        #self.class_names = self.ckpoint['category_list']
        #=====
        ###=============================================================
        

    def detect_callback(self, data):
        
        ###======================= 모델 추론 부분 =======================
        
        
        cv_image = bridge.imgmsg_to_cv2(data)
        
        
        ###=============================================================

        ###======================= 결과 시각화 코드 =======================
        
        
        frame_rgb = cv2.cvtColor(cv_image,cv2.COLOR_BGR2RGB)
    
        frame_rgb = Image1.fromarray(frame_rgb)
    
        input_tensor = self.preprocess(frame_rgb).unsqueeze(0).cuda()
    
        #import pdb;pdb.set_trace()
    
        with torch.no_grad():
            detections = self.net(input_tensor)[0]
    
    
        #import pdb;pdb.set_trace()
        
    
        for i in range(len(detections['boxes'])):
            box = detections['boxes'].cpu()[i].numpy()
            score = detections['scores'].cpu()[i].numpy()
            Class = detections['labels'].cpu()[i].numpy()
            Class_name = self.class_names[Class]
            if score > 0.5:
                xmin,ymin,xmax,ymax = box.astype(int)
                cv2.rectangle(cv_image,(xmin,ymin),(xmax,ymax),(255,0,0),2)
                label = f'{score:.2f},{Class_name}'
            
                cv2.putText(cv_image,label,(xmin,ymin-10),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,0,0),2)
            
        
        ###=============================================================

        # Displaying the predictions
        cv2.imshow('object_detection', cv_image)
        cv2.waitKey(1)

def main(args=None):
        ###======================= main 함수 =======================
        
        
        
        
        rclpy.init(args=args) # 초기화
        node = DetectionNode() # HelloworldSubscriber를 node라는 이름으로 생성
        try:
            rclpy.spin(node) # rclpy에게 이 Node를 반복해서 실행 (=spin) 하라고 전달
        except KeyboardInterrupt: # `Ctrl + c`가 동작했을 때
            node.get_logger().info('Keyboard Interrupt (SIGINT)')
        finally:
            node.destroy_node()  # 노드 소멸
            rclpy.shutdown() # rclpy.shutdown 함수로 노드 종료
        ###=============================================================


if __name__ == '__main__':
    main()
