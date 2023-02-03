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

        self.odom_broadcaster = TransformBroadcaster(self, 10)
        self.joint_state_pub = self.create_publisher(JointState, "joint_states", 10)
        self.joystick_sub = self.create_subscription(Joy, 'joy', self.get_JoystickInput, 10) #?

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

        #first joint movement in the x direction
        self.joint1_movement += self.scale_factor_joint1 * msg.axes[4]
        
        if self.joint1_movement <= 0.07:
            self.joint1_movement = 0.07
        
        elif self.joint1_movement >= 2.5:
            self.joint1_movement = 2.5

        #second joint movement in the y direction
        self.joint2_movement += self.scale_factor_joint2 * msg.axes[3]

        if self.joint2_movement <= 0.06:
            self.joint2_movement = 0.06
             
        elif self.joint2_movement >= 1.3:
            self.joint2_movement = 1.3
            
        #third joint movement in the z direction
        self.joint3_movement += self.scale_factor_joint3 * msg.axes[1]

        if self.joint3_movement <= 0.0:
            self.joint3_movement = 0.0
            
        elif self.joint3_movement >= 0.15:
            self.joint3_movement = 0.15

        self.broadcastTransformations()

    def broadcastTransformations(self):
        self.time_now = self.get_clock().now().to_msg()
        self.jointstate.header.stamp = self.time_now
        self.jointstate.position = [float(self.joint1_movement), float(self.joint2_movement), float(self.joint3_movement)]
        self.joint_state_pub.publish(self.jointstate)
        
def main(args=None):

    rclpy.init(args=args)
    obj = RobotModel('slicer')
    rclpy.spin(obj)
    
    
if __name__ == "__main__":
    main()
    
    
