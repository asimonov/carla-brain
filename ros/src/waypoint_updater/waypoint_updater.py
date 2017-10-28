#!/usr/bin/env python
import math
import numpy as np
import rospy
from std_msgs.msg import Int32
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import TwistStamped
from styx_msgs.msg import Lane, Waypoint
from styx_msgs.msg import TrafficLightArray
from waypoint_helper import is_waypoint_behind_pose

'''
This node will publish waypoints from the car's current position to some `x` distance ahead.

As mentioned in the doc, you should ideally first implement a version which does not care
about traffic lights or obstacles.

Once you have created dbw_node, you will update this node to use the status of traffic lights too.

Please note that our simulator also provides the exact location of traffic lights and their
current status in `/vehicle/traffic_lights` message. You can use this message to build this node
as well as to verify your TL classifier.

TODO (for Yousuf and Aaron): Stopline location for each traffic light.
'''

LOOKAHEAD_WPS = 100 # Number of waypoints we will publish. You can change this number via parameter
PUBLISHER_RATE = 5  # Publishin rate on channel /final_waypoints
MAX_SPEED = 10 # replace with the configurable one

dl = lambda a, b: math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2  + (a.z-b.z)**2)

class WaypointUpdater(object):
    def __init__(self):
        global LOOKAHEAD_WPS
        rospy.init_node('waypoint_updater')

        LOOKAHEAD_WPS = rospy.get_param('lookahead_wps', LOOKAHEAD_WPS)
        rospy.logwarn('wp_updater: LOOKAHEAD_WPS={}'.format(LOOKAHEAD_WPS))

        MAX_SPEED = rospy.get_param('velocity', MAX_SPEED)
        rospy.logwarn('wp_updater: MAX_SPEED={}'.format(MAX_SPEED))

        rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb, queue_size=1)
        rospy.Subscriber('/base_waypoints', Lane, self.base_waypoints_cb, queue_size=1)
        rospy.Subscriber('/traffic_waypoint', Int32, self.traffic_cb, queue_size=1)
        rospy.Subscriber('/current_velocity', TwistStamped, self.velocity_cb, queue_size=1)
        # for testing: Gives the state of the traffic lights
        rospy.Subscriber('/vehicle/traffic_lights',TrafficLightArray, self.tfl_state_cb, queue_size=1)

        self.final_waypoints_pub = rospy.Publisher('/final_waypoints', Lane, queue_size=1)

        self.current_pose = None
        self.current_frame_id = None
        self.base_waypoints = None
        self.len_base_waypoints = 0
        self.seq = 0
        self.current_waypoint_ahead = None
        self.closest_obstacle = None
        self.current_velocity = None
        self.current_tfl_state = None
        rate = rospy.Rate(PUBLISHER_RATE)
        while not rospy.is_shutdown():
            self.publish_waypoints_ahead()
            rate.sleep()

    def pose_cb(self, msg):
        """
        Updates the state of the vehicle and which frame is the current one.
        """
        self.current_pose = msg.pose
        self.current_frame_id = msg.header.frame_id

        if self.base_waypoints is None:
            return

    def base_waypoints_cb(self, waypoints):
        """
        Sets the callbacks in this object
        """
        self.base_waypoints = waypoints.waypoints
        self.len_base_waypoints = len(self.base_waypoints)

    def tfl_state_cb(self, tfl_array):
        """
         Sets the state if traffic lights
         All the lights have the same state at the same time
        """
        self.current_tfl_state = 2# tfl_array.lights[0].state

    def traffic_cb(self, msg):
        """
        Callback to get the position of the next traffic light
        """
        if msg.data != -1:
            # assign the next waypoint
            self.closest_obstacle = msg.data
        else:
            self.closest_obstacle = None

    def velocity_cb(self, msg):
        """
        Callback to get the current speed of the vehicle
        """
        self.current_velocity = msg.twist.linear.x

    def obstacle_cb(self, msg):
        # TODO: Callback for /obstacle_waypoint message. We will implement it later
        pass

    def get_waypoint_velocity(self, waypoint):
        """
        Unwraps the waypoint to return the value of the linear speed
        """
        return waypoint.twist.twist.linear.x

    def set_waypoint_velocity(self, waypoints, waypoint, velocity):
        """
        Unwraps the waypoint object to set the value for the linear speed
        """
        waypoints[waypoint].twist.twist.linear.x = velocity

    def distance(self, waypoints, wp1, wp2):
        """
        Calculates the euclidean distance between two waypoints given
        """
        dist = 0
        for i in range(wp1, wp2+1):
            dist += dl(waypoints[wp1].pose.pose.position, waypoints[i].pose.pose.position)
            wp1 = i
        return dist

    def _get_waypoint_indices(self, start_index, length=None):
        """Computes a cyclic list of waypoint indices

        Args:
        start_index (int): Initial index of the list
        length (int): Desired length of resulting list, defaults to length of base points list

        Returns:
        cyclic list of waypoint indices
        """
        if length is None:
            lenght = self.len_base_waypoints

        # making sure that length does not overpass base waypoints length
        length = min(self.len_base_waypoints, length)

        end_index = start_index + length
        q, r = divmod(end_index, self.len_base_waypoints)

        # q can either be 0 or 1
        if q == 0:
            return range(start_index, r)
        else:
            return range(start_index, self.len_base_waypoints) + range(0, r)

    def _closest_waypoint_index(self):
        """ Computes the index of closest waypoint w.r.t current position
        """

        rospy.logdebug("computing closest_waypoint_index for pos %d, %d",
                    self.current_pose.position.x,
                    self.current_pose.position.y)

        if self.current_waypoint_ahead is None:
            possible_waypoint_indices = self._get_waypoint_indices(0,
                                                                   self.len_base_waypoints)
            closest_distance = float('inf')
        else:
            possible_waypoint_indices = self._get_waypoint_indices(self.current_waypoint_ahead, LOOKAHEAD_WPS)
            closest_distance = dl(self.base_waypoints[self.current_waypoint_ahead].pose.pose.position,
                                self.current_pose.position)

        prev_index = possible_waypoint_indices.pop(0)
        closer_point_found = True

        while closer_point_found and len(possible_waypoint_indices) > 0:
            index = possible_waypoint_indices.pop(0)
            distance = dl(self.base_waypoints[index].pose.pose.position,
                         self.current_pose.position)

            if distance > closest_distance:
                closer_point_found = False
            else:
                closest_distance = distance
                prev_index = index

        while is_waypoint_behind_pose(self.current_pose, self.base_waypoints[prev_index]):
            prev_index += 1
            prev_index %= self.len_base_waypoints

        self.current_waypoint_ahead = prev_index

        return prev_index


    def publish_waypoints_ahead(self):
        """ Publishes a Lane of LOOKAHEAD_WPS waypoints /final_waypoint topic
        """
        if self.base_waypoints is None or self.current_pose is None:
            return

        start_index = self._closest_waypoint_index()
        self.current_waypoint_ahead = start_index

        waypoint_indices = self._get_waypoint_indices(start_index, LOOKAHEAD_WPS)

        lane = Lane()
        lane.header.frame_id = self.current_frame_id
        lane.header.stamp = rospy.Time.now()
        lane.header.seq = self.seq
        lane.waypoints = [self.base_waypoints[i] for i in waypoint_indices]

        if self.closest_obstacle is None or self.closest_obstacle > waypoint_indices[-1] or self.current_tfl_state != 2:
            # There is no traffic light near us, go full speed
            self.current_velocity = self.current_velocity+0.5 if self.current_velocity < MAX_SPEED else self.current_velocity
            speeds = np.linspace(self.current_velocity, MAX_SPEED, 1+(LOOKAHEAD_WPS//17))
            full_speed = np.ones(16*LOOKAHEAD_WPS//17) * MAX_SPEED
            speeds = 10# np.concatenate((speeds, full_speed))

        # There is a traffic light in front
        elif self.current_tfl_state ==  2:
            remaining_wp = abs(self.closest_obstacle - self.current_waypoint_ahead)
            distance = self.distance(lane.waypoints, 0, self.closest_obstacle - start_index)
            """ Keeping comments for future reference in this commit only
            rospy.logwarn("BreakSpeed")
            rospy.logwarn("rem wp: " + str(remaining_wp))
            if self.current_velocity > 1.5 and remaining_wp >= 55:
                rospy.logwarn("rm sp: " + str(100*(remaining_wp-LOOKAHEAD_WPS)/LOOKAHEAD_WPS))
                # Giving some extra space to reach speed == 0
                remaining_wp = remaining_wp - 15 if remaining_wp > 15 else remaining_wp
                # generate the ramp from current speed to full stop in the remaining space
                #breaking = np.linspace(self.current_velocity-0.2, 0, remaining_wp)
                breaking = np.ones(remaining_wp) * self.current_velocity * 0.9
                # Adjust the vector to LOOKAHEAD_WPS size
                speeds = np.concatenate((breaking, np.zeros(LOOKAHEAD_WPS - len(breaking))))
                #speeds =  100*(remaining_wp - LOOKAHEAD_WPS)/LOOKAHEAD_WPS #np.zeros(LOOKAHEAD_WPS)
                speeds = 7.5
            elif 55 > remaining_wp >= 35:
                speeds = 5
            elif 35 > remaining_wp > 15:
                speeds = 3
            else:
                speeds = 0 #np.zeros(LOOKAHEAD_WPS)
            """
            if self.current_velocity > 2:
                #speeds =  4*(LOOKAHEAD_WPS)/float(LOOKAHEAD_WPS - remaining_wp)
                speeds =  min(10, .15*(distance - 5))
            else:
                speeds = 0

        else:
            speeds = np.linspace(self.current_velocity, MAX_SPEED, 1+(LOOKAHEAD_WPS//8))
            full_speed = np.ones(7*LOOKAHEAD_WPS//8) * MAX_SPEED
            speeds = np.concatenate((speeds, full_speed))

        rospy.logwarn(speeds)

        for i in range(LOOKAHEAD_WPS):
            self.set_waypoint_velocity(lane.waypoints, i, speeds)

        self.final_waypoints_pub.publish(lane)
        self.seq += 1


if __name__ == '__main__':
    try:
        WaypointUpdater()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start waypoint updater node.')
