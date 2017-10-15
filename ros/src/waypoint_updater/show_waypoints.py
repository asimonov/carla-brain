#!/usr/bin/python
"""
Visualize the project

"""

import sys
import math
import threading
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import QPen
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer

import rospy
from std_msgs.msg import Int32, Bool
from geometry_msgs.msg import PoseStamped
from dbw_mkz_msgs.msg import SteeringCmd, SteeringReport
from styx_msgs.msg import TrafficLightArray, Lane
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge, CvBridgeError


class Visualization(QtWidgets.QWidget):

    """
    Subscribe to all the ros publisher and show their content
    """

    def __init__(self):
        super(Visualization, self).__init__()
        rospy.init_node('show_waypoints')
        self.lock = threading.Lock()
        self.bridge = CvBridge()

        self.waypoints = None
        self.base_waypoints = None
        self.steering = 0
        self.steering_report = None
        self.lights = None
        self.traffic_light = - 1
        self.current_pose = None
        self.dbw_enabled = False
        self.max_x, self.max_y, self.min_x, self.min_y = (0.1, 0.1, 0.0, 0.0)

        rospy.Subscriber('/final_waypoints', Lane, self.waypoints_cb)
        rospy.Subscriber('/base_waypoints', Lane, self.base_waypoints_cb)
        rospy.Subscriber('/vehicle/steering_cmd', SteeringCmd, self.steering_cb)
        rospy.Subscriber('/vehicle/steering_report', SteeringReport, self.steering_report_cb)
        rospy.Subscriber('/image_color', Image, self.camera_callback)
        rospy.Subscriber('/vehicle/traffic_lights', TrafficLightArray, self.traffic_cb)
        rospy.Subscriber('/traffic_waypoint', Int32, self.traffic_waypoint_cb)
        rospy.Subscriber('/current_pose', PoseStamped, self.current_pose_cb)
        rospy.Subscriber('/vehicle/dbw_enabled', Bool, self.dbw_enabled_cb)

        self.img_format_table = {'rgb8': QtGui.QImage.Format_RGB888, 'mono8': QtGui.QImage.Format_Mono,
                                 'bgr8': QtGui.QImage.Format_RGB888}
        self.image = None
        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.repaint)
        self.timer.setInterval(300)
        self.timer.start()

    def initUI(self):
        """"
        Initialize the gui
        """
        self.setGeometry(10, 10, 2200, 1000)
        self.setWindowTitle('Points')
        self.show()

    def paintEvent(self, e):
        """
        Paint all the ocntent
        :param e:
        :return:
        """
        painter = QtGui.QPainter()
        painter.begin(self)
        self.drawPoints(painter)
        painter.end()

    def calculate_position(self, orig_x, orig_y):
        """
        Readjust the position to be displayed within (150,150,950, 950)
        :param orig_x:
        :param orig_y:
        :return:
        """
        mov_x = -1*self.min_x
        mov_y = -1*self.min_y 
        #rospy.logwarn("x and y %r %r   %r %r   %r %r", self.max_x, self.max_y, self.min_x, self.min_y, mov_x, mov_y)

        x = (orig_x + mov_x) * 800 / (self.max_x - self.min_x) + 150
        y = (orig_y + mov_y)* 800 / (self.max_y - self.min_y) + 150
        return (x, y)

    def draw_traffic_lights(self, painter):
        """
        If traffic lights have been provided, draw them.
        :param painter:
        :return:
        """
        if self.lights:
            pen = QPen()
            pen.setWidth(10)
            pen.setColor(Qt.blue)
            painter.setPen(pen)
            for position in self.lights:
                x, y = self.calculate_position(position.pose.pose.position.x, position.pose.pose.position.y)
                painter.drawPoint(x, y)

    def draw_dbw_enabled(self, painter):
        """
        Are we in manual or automatic mode
        :param painter:
        :return:
        """
        pen = QPen()
        pen.setColor(Qt.black)
        painter.setPen(pen)
        text = "Automatic" if self.dbw_enabled else "Manual"
        painter.drawText(QPointF(10, 20), text)

    def draw_current_pose(self, painter):
        """
        Draw the current position
        :param painter:
        :return:
        """
        if self.current_pose:
            pen = QPen()
            pen.setWidth(15)
            pen.setColor(Qt.darkMagenta)
            painter.setPen(pen)
            x, y = self.calculate_position(self.current_pose.pose.position.x, self.current_pose.pose.position.y)
            painter.drawPoint(x, y)

    def draw_next_traffic_light(self, painter):
        """
        Draw the upcoming traffic light
        :param painter:
        :return:
        """
        twp = self.traffic_light
        if twp >= 0 and self.lights and twp <= len(self.base_waypoints):
            #rospy.logwarn("%r %r", twp, len(self.base_waypoints))
            pen = QPen()
            pen.setWidth(20)
            pen.setColor(Qt.red)
            painter.setPen(pen)
            x, y = self.calculate_position(self.base_waypoints[twp].pose.pose.position.x,
                                           self.base_waypoints[twp].pose.pose.position.y)
            painter.drawPoint(x, y)

    def drawPoints(self, painter):
        """
        Draw the recevied content
        :param painter:
        :return:
        """
        pen = QPen()
        pen.setWidth(4)
        pen.setColor(Qt.black)
        painter.setPen(pen)
        if self.base_waypoints:
            for waypoint in self.base_waypoints:
                x, y = self.calculate_position(waypoint.pose.pose.position.x,
                                               waypoint.pose.pose.position.y)
                painter.drawPoint(x, y)

        pen = QPen()
        pen.setWidth(6)
        pen.setColor(Qt.red)
        painter.setPen(pen)
        if self.waypoints:
            for waypoint in self.waypoints:
                x, y = self.calculate_position(waypoint.pose.pose.position.x,
                                               waypoint.pose.pose.position.y)
                painter.drawPoint(x, y)

        cx = 500
        cy = 500
        r = 100.0
        pen = QPen()
        pen.setWidth(3)
        pen.setColor(Qt.black)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        self.draw_steering(painter, cx, cy, r, 10, self.steering, Qt.red)
        self.draw_steering_report(painter, cx, cy, r, Qt.blue)

        if self.image:
            painter.drawImage(QRectF(1000, 200, self.image.size().width(), self.image.size().height()), self.image)

        self.draw_next_traffic_light(painter)
        self.draw_dbw_enabled(painter)
        self.draw_current_pose(painter)
        self.draw_traffic_lights(painter)

    def draw_steering(self, painter, cx, cy, r, width, steering, color):
        """
        Draw the steering angle
        """
        pen = QPen()
        pen.setWidth(width)
        pen.setColor(color)
        painter.setPen(pen)
        x = cx + r * math.cos(-math.pi / 2 + steering * -1)
        y = cy + r * math.sin(-math.pi / 2 + steering * -1)
        painter.drawLine(QPointF(cx, cy), QPointF(x, y))

    def draw_steering_report(self, painter, cx, cy, r, color):
        """
        Draw the reported steering angle
        """
        if self.steering_report:
            pen = QPen()
            pen.setColor(Qt.black)
            painter.setPen(pen)
            text = "%4d km/h" % (self.steering_report.speed*3.6)
            painter.drawText(QPointF(cx, cy-r-40), text)

            self.draw_steering(painter, cx, cy, r, 5, self.steering_report.steering_wheel_angle, color)

    def waypoints_cb(self, msg):
        """
        Callback for /final_waypoints
        :param msg:
        :return:
        """
        self.waypoints = msg.waypoints

    def steering_cb(self, msg):
        """
        Callback for /vehicle/steering_cmd
        :param msg:
        :return:
        """
        self.steering = msg.steering_wheel_angle_cmd

    def steering_report_cb(self, msg):
        """
        Callback for /vehicle/steering_cmd
        :param msg:
        :return:
        """
        self.steering_report = msg

    def base_waypoints_cb(self, msg):
        """
        Callback for /base_waypoints
        :param msg:
        :return:
        """
        self.base_waypoints = msg.waypoints

        max_x = -sys.maxint
        max_y = -sys.maxint
        min_x = sys.maxint
        min_y = sys.maxint
        for waypoint in self.base_waypoints:
            max_x = max(waypoint.pose.pose.position.x, max_x)
            max_y = max(waypoint.pose.pose.position.y, max_y)
            min_x = min(waypoint.pose.pose.position.x, min_x)
            min_y = min(waypoint.pose.pose.position.y, min_y)
        rospy.logwarn("x and y %r %r   %r %r", max_x, max_y, min_x, min_y)
        self.max_x, self.max_y, self.min_x, self.min_y = (max_x, max_y, min_x, min_y)

    def camera_callback(self, data):
        """
        Callback for /image_color
        :param data:
        :return:
        """
        _format = self.img_format_table[data.encoding]
        if data.encoding == "bgr8":
            cv_image = self.bridge.imgmsg_to_cv2(data, desired_encoding="passthrough")
            image_data = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        else:
            image_data = data.data
        image = QtGui.QImage(image_data, data.width, data.height, _format)
        self.image = image

    def traffic_cb(self, msg):
        """
        Callback for /vehicle/traffic_lights
        :param msg:
        :return:
        """
        self.lights = msg.lights

    def traffic_waypoint_cb(self, msg):
        """
        Callback for /traffic_waypoint
        :param msg:
        :return:
        """
        self.traffic_light = msg.data

    def current_pose_cb(self, msg):
        """
        Callback for /traffic_waypoint
        :param msg:
        :return:
        """
        self.current_pose = msg

    def dbw_enabled_cb(self, msg):
        """
        Callback for /vehicle/dbw_enable
        :param msg:
        :return:
        """
        self.dbw_enabled = msg.data

def main():
    app = QtWidgets.QApplication(sys.argv)
    Visualization()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()