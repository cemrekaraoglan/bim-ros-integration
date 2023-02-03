from sensor_msgs.msg      import Joy, JointState
import numpy              as np
import rclpy
from rclpy.node           import Node
import tf_transformations as tf_trans
from geometry_msgs.msg    import Vector3, Quaternion
from tf2_ros              import TransformBroadcaster, TransformStamped


class RobotModel(Node):

    def __init__(self, name):
        super().__init__('slicer')
        
        self.dim_x = 0.8
        self.odom_broadcaster = TransformBroadcaster(self, 10)
        self.joint_state_pub = self.create_publisher(JointState, "joint_states", 10)
        self.joystick_sub = self.create_subscription(Joy, 'joy', self.get_JoystickInput, 10) #?
        self.fab_pub = self.create_publisher(String, '/fabrication_status/message', 10)
        self.fab_pub_dim = self.create_publisher(Float32, '/fabrication_status/dimension', 10)
        
        #self.tf_buffer = Buffer()
        #self.tf_listener = TransformListener(self.tf_buffer, self)
        
        
        #home position
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.theta = 0.0
        self.phi = 0.0
        self.psi = 0.0

        self.jointstate = JointState()
        self.jointstate.name = ["base_link1_joint", "link1_link2_joint", "link2_link3_joint"]
        self.get_logger().info(f"slicer is on...")

        #add yaml file to config folder and add the details in the  main, setup and launch files to read the parameters
        self.declare_parameter('max_speed', 0.0) 
        self.declare_parameter('name', "default name")
        self.declare_parameter('id', 0)
        self.declare_parameter('scale_factor_joint1', 0.0)
        self.declare_parameter('scale_factor_joint2', 0.0)
        self.declare_parameter('scale_factor_joint3', 0.0)

        self.speed_max_value = self.get_parameter('max_speed').get_parameter_value().double_value 
        self.name_value = self.get_parameter('name').get_parameter_value().string_value
        self.id_value = self.get_parameter('id').get_parameter_value().integer_value
        self.scale_factor_joint1 = self.get_parameter('scale_factor_joint1').get_parameter_value().double_value
        self.scale_factor_joint2 = self.get_parameter('scale_factor_joint2').get_parameter_value().double_value
        self.scale_factor_joint3 = self.get_parameter('scale_factor_joint3').get_parameter_value().double_value

        self.joint1_movement = 0.0
        self.joint2_movement = 0.0
        self.joint3_movement = 0.0
        

    def get_JoystickInput(self, msg):

        if msg.buttons[0] == 1:
            
            #joint 3 moves
            self.joint3_movement -= 0.05
            
            if self.joint3_movement <= 0.0:
                
                self.joint3_movement = 0.0
                
                self.fab_pub.publish('The cutting has started...')
               
               #joint 1 moves
                self.joint1_movement += 0.1 
                
                if self.joint1_movement == self.dim_x:
                    
                    self.joint2_movement += 0.1
                    
                    #joint 2 moves
                    if self.joint2_movement >= 1.3:
                        
                        self.joint2_movement = 1.3
                                               
                        self.fab_pub.publish('Gypsumboard is cut')
   
        self.broadcastTransformations()

    def broadcastTransformations(self):
        self.time_now = self.get_clock().now().to_msg()
        self.jointstate.header.stamp = self.time_now
        self.jointstate.position = [float(self.joint1_movement), float(self.joint2_movement), float(self.joint3_movement)]
        self.joint_state_pub.publish(self.jointstate)
        
        #try:
            #trans = tfBuffer.lookup_transform('link2_link3_joint','odom', rospy.Time())
 
def main(args=None):

    rclpy.init(args=args)
    obj = RobotModel('slicer')
    rclpy.spin(obj)
    
    
if __name__ == "__main__":
    main()
    
    
