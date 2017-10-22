#!/usr/bin/env python
import math
import rospy

from geometry_msgs.msg import PoseStamped
from styx_msgs.msg import Lane, Waypoint
from waypoint_helper import is_waypoint_behind_pose
from std_msgs.msg import Int32


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

LOOKAHEAD_WPS = 100 # Number of waypoints we will publish. It comes from launchfile parameter
PUBLISHER_RATE = 5  # Publishing rate on channel /final_waypoints. Hz

dl = lambda a, b: math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2  + (a.z-b.z)**2)

class WaypointUpdater(object):
    def __init__(self):
        global LOOKAHEAD_WPS
        rospy.init_node('waypoint_updater')

        LOOKAHEAD_WPS = rospy.get_param('lookahead_wps', LOOKAHEAD_WPS)

        rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb, queue_size=1)
        rospy.Subscriber('/base_waypoints', Lane, self.base_waypoints_cb, queue_size=1)

        # TODO: Add a subscriber for /traffic_waypoint and /obstacle_waypoint below
        rospy.Subscriber('/traffic_waypoint', Int32, self.traffic_cb, queue_size=1)

        self.final_waypoints_pub = rospy.Publisher('/final_waypoints', Lane, queue_size=1)

        self.current_pose = None
        self.current_frame_id = None
        self.base_waypoints = None
        self.len_base_waypoints = 0
        self.seq = 0
        self.current_waypoint_ahead = None
        self.next_traffic_wp = -1
        
        rate = rospy.Rate(PUBLISHER_RATE)
        while not rospy.is_shutdown():
            self.publish_waypoints_ahead()
            rate.sleep()

    def pose_cb(self, msg):
        self.current_pose = msg.pose
        self.current_frame_id = msg.header.frame_id

        if self.base_waypoints is None:
            return
        
    def base_waypoints_cb(self, waypoints):
        self.base_waypoints = waypoints.waypoints
        self.len_base_waypoints = len(self.base_waypoints)

    def traffic_cb(self, msg):
        self.next_traffic_wp = msg.data
        rospy.logwarn("updater: next TL wp = {}".format(self.next_traffic_wp))

    def obstacle_cb(self, msg):
        # TODO: Callback for /obstacle_waypoint message. We will implement it later
        pass

    def get_waypoint_velocity(self, waypoint):
        return waypoint.twist.twist.linear.x

    def set_waypoint_velocity(self, waypoints, waypoint, velocity):
        waypoints[waypoint].twist.twist.linear.x = velocity

    def distance(self, waypoints, wp1, wp2):
        
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
        waypoints = []
        for i in waypoint_indices:
            waypoints.append(self.base_waypoints[i])
            if i==self.next_traffic_wp:
                # red traffic light -- decelerate and stop
                waypoints = self.decelerate(waypoints)
                # continue adding subsequent waypoints with normal speed. or ramp up?

        lane = Lane()
        lane.header.frame_id = self.current_frame_id
        lane.header.stamp = rospy.Time.now()
        lane.header.seq = self.seq
        lane.waypoints = waypoints

        rospy.logwarn("updater: publish {} waypoints".format(self.next_traffic_wp))

        self.final_waypoints_pub.publish(lane)
        self.seq += 1

    def decelerate(self, waypoints):
        ''' decelerate gradually to last waypoint. taken from waypoint_loader.py '''
        MAX_DECEL = 1.0
        last = waypoints[-1]
        last.twist.twist.linear.x = 0.
        for wp in waypoints[:-1][::-1]:
            dist = dl(wp.pose.pose.position, last.pose.pose.position)
            vel = math.sqrt(2 * MAX_DECEL * dist)
            if vel < 1.:
                vel = 0.
            wp.twist.twist.linear.x = min(vel, wp.twist.twist.linear.x)
        return waypoints


if __name__ == '__main__':
    try:
        WaypointUpdater()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start waypoint updater node.')
