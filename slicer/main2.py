from visualization_msgs.msg import Marker, MarkerArray
from rclpy.node import Node
import rclpy
import sys
import numpy as np
import random
from std_msgs.msg import String, Float32

class Gypsum(Node):
    def __init__(self, name):

        super().__init__(name)

        self.gypsum_pub = self.create_publisher(MarkerArray, 'visualization_marker_array', 10)
        self.sub_msg = self.create_subscription(String, "/fabrication_status/message", self.message_callback, 10)
        self.sub_dim = self.create_subscription(Float32, '/fabrication_status/dimension', self.dimension_callback, 10)
        
        self.array = MarkerArray()
        self.gypsum = Marker()
        
        self.gypsum.header.frame_id = "odom"
        self.gypsum.ns =""
        self.gypsum.header.stamp = self.get_clock().now().to_msg()
        self.gypsum.type = Marker().CUBE
    
        self.gypsum.pose.position.x = 0.119
        self.gypsum.pose.position.y = 0.107
        self.gypsum.pose.position.z = 0.6
        
        self.gypsum.pose.orientation.x = 0.0
        self.gypsum.pose.orientation.y = 0.0
        self.gypsum.pose.orientation.z = 0.0
        self.gypsum.pose.orientation.w = 1.0
    
        self.dim_x = 2.5
        self.dim_y = 1.3
        self.dim_z = 0.005
    
        self.gypsum.scale.x = 2.5
        self.gypsum.scale.y = 1.3
        self.gypsum.scale.z = 0.005

        self.gypsum.color.a = 1.0
        self.gypsum.color.r = random.uniform(0.0, 0.5)
        self.gypsum.color.g = random.uniform(0.0, 0.5)
        self.gypsum.color.b = 1.0 - (self.gypsum.color.r + self.gypsum.color.g)
        
        self.msg_str = String()
        self.msg_dim = Float32()
        
    
    def dimension_callback(self,msg):
 
        self.msg_dim = float(msg.data)
        
    def message_callback(self, msg):
        
        self.msg_str = msg.data

        if self.msg_str == 'The cutting has started':
            self.get_logger().info(f'Hello1')
            self.gypsum.action = Marker().ADD
            self.array.markers.append(self.gypsum)
            self.gypsum_pub.publish(self.array)
            
        
        elif self.msg_str== 'Gypsumboard is cut':
            self.gypsum.action = Marker().DELETE
            
            self.get_logger().info(f'Hello2')
            #piece 1
            self.gypsum.color.r = random.uniform(0.0, 0.5)
            self.gypsum.color.g = random.uniform(0.0, 0.5)
            self.gypsum.color.b = 1.0 - (self.gypsum.color.r + self.gypsum.color.g)
    
            self.gypsum.scale.x = self.msg_dim

            self.gypsum.action = Marker().ADD
        
            self.array.markers.append(self.gypsum)

            #piece 2
            self.gypsum.color.a = 1.0
            self.gypsum.color.r = random.uniform(0.0, 0.5)
            self.gypsum.color.g = random.uniform(0.0, 0.5)
            self.gypsum.color.b = 1.0 - (self.gypsum.color.r + self.gypsum.color.g)

            self.gypsum.scale.x = self.dim_x-float(self.msg_dim)
          

            self.gypsum.pose.position.x = (self.msg_dim)

            self.gypsum.action = Marker().ADD
        
            self.array.markers.append(self.gypsum)

            self.gypsum_pub.publish(self.array)
            
            self.get_logger().info(f'Hello3')


def main(args=None):

    rclpy.init(args=args)
    obj = Gypsum('slicer')
    
    try:
        rclpy.spin(obj)
    
    except KeyboardInterrupt:
        print(f'Interrupted')
    
if __name__ == "__main__":
    main()
    
    
