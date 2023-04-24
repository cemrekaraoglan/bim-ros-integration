from visualization_msgs.msg import Marker, MarkerArray
from rclpy.node import Node
import rclpy
import sys
import numpy as np
import random
from std_msgs.msg import String, Float32
import time


class Gypsum(Node):
    def __init__(self, name):

        super().__init__(name)

        self.gypsum_pub = self.create_publisher(MarkerArray, 'visualization_marker_array', 10)
        self.fab_pub = self.create_publisher(String, '/trigger', 10)
        self.sub_msg = self.create_subscription(String, "/fabrication_status/message", self.message_callback, 10)
        self.sub_dim = self.create_subscription(Float32, '/fabrication_status/dimension', self.dimension_callback, 10)
        
        self.array = MarkerArray()
        self.array2 = MarkerArray()
        self.gypsum = Marker()
        
        self.gypsum.header.frame_id = "odom"

        self.gypsum.header.stamp = self.get_clock().now().to_msg()
        self.gypsum.type = Marker().CUBE
        
        self.gypsum.scale.x = 2.5
        self.gypsum.scale.y = 1.3
        self.gypsum.scale.z = 0.01
        self.dim_x = self.gypsum.scale.x
        
        self.gypsum.id = 100
        self.gypsum.ns = str(f'Gypsumboard {self.gypsum.id}')

        self.gypsum.pose.position.x = 0.12 + self.gypsum.scale.x/2
        self.gypsum.pose.position.y = 0.075 + self.gypsum.scale.y/2
        self.gypsum.pose.position.z = 0.6 + self.gypsum.scale.z/2

        self.gypsum.pose.orientation.x = 0.0
        self.gypsum.pose.orientation.y = 0.0
        self.gypsum.pose.orientation.z = 0.0
        self.gypsum.pose.orientation.w = 1.0

        self.gypsum.color.a = 0.8
        self.gypsum.color.r = random.uniform(0.0, 0.5)
        self.gypsum.color.g = random.uniform(0.0, 0.5)
        self.gypsum.color.b = 1.0 - (self.gypsum.color.r + self.gypsum.color.g)
        self.fab_pub_msg = String()
        self.msg_str = String()
        self.msg_dim = Float32()

        self.marker_added = False
        self.marker_added2 = False


    def dimension_callback(self,msg):
        
        self.msg_dim = msg.data
       
        
    def message_callback(self, msg):

        self.msg_str = msg.data

        time.sleep(0.1)

        if 'cutting has not started' in self.msg_str:

            if self.marker_added == False:
                self.gypsum.id += 1
                self.gypsum.action = Marker().ADD
                self.array.markers.append(self.gypsum)
                self.gypsum_pub.publish(self.array)
                self.get_logger().info(f'cut_0')

                self.marker_added = True

                time.sleep(0.05)

        if 'is cut' in self.msg_str:

            time.sleep(0.05)

            if self.marker_added == True:

                if self.marker_added2 == False:

                    self.gypsum.action = Marker().DELETE
                    self.gypsum_pub.publish(self.array)
                    self.get_logger().info(f'{self.gypsum.id}')

                    for i in range(2):

                        if i == 0:
                            self.gypsum.id += 1
                            self.gypsum.ns = str(f'Panel {self.gypsum.id}')
                            self.gypsum.color.r = random.uniform(0.0, 0.5)
                            self.gypsum.color.g = random.uniform(0.0, 0.5)
                            self.gypsum.color.b = 1.0 - (self.gypsum.color.r + self.gypsum.color.g)
                            self.gypsum.scale.x = self.msg_dim
                            self.gypsum.pose.position.x = 0.12 + self.gypsum.scale.x/2
                            self.gypsum.action = Marker().ADD
                            self.array2.markers.append(self.gypsum)
                            self.gypsum_pub.publish(self.array2)
                            self.get_logger().info(f'{self.gypsum.id}')
                            
                       
                        elif i == 1:
                            #piece 2
                            self.gypsum.id += 1
                            self.gypsum.ns = str(f'Panel {self.gypsum.id}')
                            self.gypsum.color.a = 0.7
                            self.gypsum.color.r = random.uniform(0.0, 0.5)
                            self.gypsum.color.g = random.uniform(0.0, 0.5)
                            self.gypsum.color.b = 1.0 - (self.gypsum.color.r + self.gypsum.color.g)
                            self.get_logger().info(f'{self.gypsum.id}')
                            self.gypsum.scale.x = float(self.dim_x - self.msg_dim)
                            self.gypsum.pose.position.x =  0.12 + self.gypsum.scale.x/2 + self.msg_dim
                            self.gypsum.action = Marker().ADD
                            self.array2.markers.append(self.gypsum)
                            self.gypsum_pub.publish(self.array2)
                
                    self.marker_added2 = True

                    

'''        if 'home position' in self.msg_str:

            time.sleep(0.5)

            if self.marker_added == True:

                if self.marker_added2 == True:

                    self.fab_pub_msg.data = 'Done'
                    self.fab_pub.publish(self.fab_pub_msg)
                    self.get_logger().info('Done')   '''


def main(args=None):

    rclpy.init(args=args)
    obj = Gypsum('slicer')
    
    try:
        rclpy.spin(obj)
    
    except KeyboardInterrupt:
        print(f'Interrupted')
    
if __name__ == "__main__":
    main()

