@title[Programming Self-driving Car]

# Programming a self driving car using Python

#### [Alexey Simonov](https://www.linkedin.com/in/alexeysimonov/)

#### PyData London 05.12.2017 [meetup](https://www.meetup.com/PyData-London-Meetup/events/245352028/)



---
@title[About Me]

### About me
- CS/Math education |
- Software Engineer. In finance |
- Just Graduated from Udacity SDCE nanodegree |

@fa[arrow-down]


+++
@title[Previous Talk]

### Previous talk: PyData London June 2017
- intro to SDCs for 'hobbyists'
- Behavioral Cloning using AI
- [https://github.com/asimonov/PyData-London-SDC-Behavioural-Cloning](https://github.com/asimonov/PyData-London-SDC-Behavioural-Cloning)




---
@title[Setup]

### The Setup

* nanodegree capstone project
* [team of 5, distributed](https://github.com/orgs/Kairos-Automotive/people)
* develop/test code in simulator
* run on actual car
* about a month




---
@title[Ingridients]

### The Ingridients

- a car (with drive-by-wire capabilities) |
- DBW kit |
- sensors |
- computer (on board) |
- **software** |

@fa[arrow-down]


+++
@title[The Car]

## The car: Lincoln MKZ

![Image-absolute](pydata-presentation/imgs/carla-cropped.jpg)

@fa[arrow-down]


+++
@title[DBW: Why]

### DBW Kit: Why?

![Image-absolute](pydata-presentation/imgs/carla-control.png)

@fa[arrow-down]


+++
@title[DBW: What]

### DBW Kit: [Dataspeed](http://docs.polysync.io/sensors/dataspeed-mkz-dbw)

<a href="http://dataspeedinc.com/wp-content/uploads/2016/11/adas-kit.pdf">
<img src="pydata-presentation/imgs/adas-kit-1.png" width="40%">
<img src="pydata-presentation/imgs/adas-kit-2.png" width="40%">
</a>

@fa[arrow-down]


+++
@title[Sensors]

### Sensors

- LIDAR ([is only used for localization](https://medium.com/udacity/how-the-udacity-self-driving-car-works-575365270a40))
- cameras
- GPS
- RADAR
- others

<img src="pydata-presentation/imgs/carla-lidar.png" width="30%">
<img src="pydata-presentation/imgs/carla-camera.jpeg" width="30%">

@fa[arrow-down]


+++
@title[Computer]

### Computer

- Intel Core i7-6700K CPU @ 4 GHz x 8
- 32 Gb Memory
- Nvidia TITAN X, 12Gb
- Ubuntu 14.04


@fa[arrow-down]

+++
@title[A UK Alternative: StreetDrone ONE]

## [www.streetdrone.com](http://www.streetdrone.com)

![Image-absolute](pydata-presentation/imgs/streetdrone.png)





---
@title[Plan]
### Plan

###### what do we need in SDC car S/W stack?

<img src="pydata-presentation/imgs/carla-pipeline.png" width="85%">

@fa[arrow-down]


+++
@title[Simplify]

## Lets simplify

- route has been planned -> waypoints
- no other road users -> nothing to predict
- no obstacles -> ignore LIDAR data
- only traffic lights -> use camera
- need to accelerate/stop and steer -> control module
- BUT want flexibility to extend/build on this

@fa[arrow-down]


+++
@title[Updated Plan]

### Updated Plan

- Perception Module
    - take image from camera
    - detect traffic light position and colour
- Planning Module
    - take current position
    - compare with list of waypoints
    - check traffic lights ahead (from above)
    - plan next position/desired speed

@fa[arrow-down]


+++
@title[Updated Plan (cntd)]

### Updated Plan (cntd)

- Control Module
    - take current+desired position+speed
    - calculate steering/brake/throttle
    - communicate to the car

@fa[arrow-down]


+++
@title[Now What?]

#### we've got hardware, now what?

- write device drivers
- write communications software
- write perception, navigation, motion planning software
- control algos
- log data
- error handling
- simulation
- @fa[frown-o]






---
@title[ROS]

### [ROS](http://www.ros.org/about-ros)

- [Robot "Operating System"](https://en.wikipedia.org/wiki/Robot_Operating_System) |
- actually a framework (on top of real OS) |
- tools/libraries/conventions |
- NOT real-time |
- open-source, BSD licensed (mostly) |
- came out of Stanford around 2007 |
- python (2.7 only) / C++ |
- no UK meetups (first Ukrainian Meetup in 2017) |


@fa[arrow-down]


+++
@title[ROS : devops]

### ROS : devops

- [native install](http://wiki.ros.org/ROS/Installation)
    - Linux is the only fully supported host OS
    - not recommended
    - good for visualisation
- Docker
    - much better idea
    - repeatable
    - trickier to use in visual mode
- we used ROS Kinetic (released May 2016)

@fa[arrow-down]


+++
@title[ROS : workspace]

### ROS : [workspace](http://wiki.ros.org/ROS/Tutorials)

- sources (python, C++, shell...)
- makefiles (catkin_make)
- dependencies
- target build files


@fa[arrow-down]


+++
@title[ROS : topics]

### ROS : [topics](http://wiki.ros.org/ROS/Tutorials)

- named bus to pass messages
- has associated message type
- physical quantities (position, duration, quaternion etc)
- sensor readings (image, point cloud etc)
- 200+ types
- `rostopic list`
- for continuous data stream

@fa[arrow-down]


+++
@title[ROS : nodes]

### ROS : [nodes](http://wiki.ros.org/ROS/Tutorials)

- separate process
- can publish/subscribe messages
- has its own lifecycle
- `roscore` is master process
- `rosnode list`
- `rosrun node`
- for async interaction

@fa[arrow-down]


+++
@title[ROS : services]

### ROS : [services](http://wiki.ros.org/ROS/Tutorials)

- one-to-one communication
- request/response
- like RPC
- quick simple blocking call
- e.g. check a state

@fa[arrow-down]


+++
@title[ROS : launch files]

### ROS : [launch files](http://wiki.ros.org/ROS/Tutorials)

- list nodes we want to start on our robot
- list parameters
- can be specific to environment (simulator vs car)

@fa[arrow-down]


+++
@title[ROS at BMW]

## ROS at BMW (research)

https://roscon.ros.org/2015/presentations/ROSCon-Automated-Driving.pdf






---
@title[ROS diagram for our car]

### ROS diagram for our car

![Image-absolute](pydata-presentation/imgs/ros-diagram.png)






---
@title[Simulator]

##### Unity-based Simulator (provided by Udacity)

![Image-absolute](pydata-presentation/imgs/simulator.png)

@fa[arrow-down]

+++?code=ros/src/styx/server.py&lang=python&title=server.py: Simulator/ROS Interaction
@[14](rospy import)
@[28](init ROS node)
@[102-103](thread to run rospy.spin)
@[106-112](create a Flask server and listen on port 4567. until ROS node is shutdown)
@[53-62](pass telemetery simulator->ROS)
@[88-94](pass camera image simulator->ROS)
@[65-67](pass control data ROS->simulator)

@fa[arrow-down]

+++?code=ros/src/styx/bridge.py&lang=python&title=bridge.py: Web Server/ROS message conversion






---
@title[Perception Module]

### Perception Module

![Image-absolute](pydata-presentation/imgs/tl-detector.png)

- close to traffic light waypoint?
- get an image
- detect where traffic light is
- classify red/amber/green
- use tensorflow

@fa[arrow-down]


+++
@title[Image Semantic Segmentation]

### Image Semantic Segmentation

- previous project on nanodegree
- using Fully Convolutional Networks
- classifying pixels of image: road, pedestrian, car etc
- Cityscapes Dataset: 35 classes
- [more details on GitHub](https://github.com/asimonov/CarND3-P2-FCN-Semantic-Segmentation)
- (other approach would be to use [SSD- or YOLO-type detector net](https://drive.google.com/file/d/0B9SNmZvpaGj1NnNsbWhTZUxYSlU/view))

@fa[arrow-down]


+++
@title[Image Segmentation: Resulting Video]

#### Image Segmentation: Resulting Video

![YouTube Video](https://youtube.com/embed/rJrD12u4lSI)

@fa[arrow-down]


+++
@title[tl_detector_segmentation.py]

#### tl_detector_segmentation.py

- network defined and trained as a [separate project](https://github.com/Kairos-Automotive/TL-detection-segmentation)
- 2 classes: background, traffic lights
- initially trained on:
    - Citiscapes Dataset
    - Bosch Traffic Light Dataset
- fine-tuned on:
    - hand-labeled images from simulator
    - hand-labeled images from ROS bag provided
- binary weights file optimized down to 40mb
- pushed on GitHub (100mb limit)

@fa[arrow-down]


+++?code=ros/src/tl_detector/tl_detector_segmentation.py&lang=python&title=tl_detector_segmentation.py: TL detector using FCN
@[4-7](imports)
@[16-22](init session, load weights)
@[23-31](extract input/output placeholders, run on fake image)
@[41-52](prediction: run tensorflow graph)
@[54-71](prediction: extract bounding boxes)

@fa[arrow-down]


+++?code=ros/src/tl_detector/tl_detector.py&lang=python&title=tl_detector.py: Detect/Classify/Publish
@[14](using separate thread for detection)
@[47-60](thread synchronisation)
@[67-74](subscribe to what we need)
@[76-77](read the 'map' for traffic light positions)
@[109-112](publishers)
@[125-197](detection + classification + debug image)
@[226-278](determine if we are in range of TL and its WP index)
@[358-369](save image message on ROS node thread)
@[328-355](detect/classify on separate thread)






---
@title[Planning Module]

### Planning Module

- Waypoint Loader
- Waypoint Updater

![Image-absolute](pydata-presentation/imgs/wp-updater.png)

@fa[arrow-down]

+++?code=ros/src/waypoint_loader/waypoint_loader.py&lang=python&title=waypoint_loader.py: Publish Planned Route
@[51-65](load waypoints from CSV file)
@[39-40](publish waypoints once)

@fa[arrow-down]


+++?code=ros/src/waypoint_updater/waypoint_updater.py&lang=python&title=waypoint_updater.py: The Brain
@[38](init ROS node)
@[42-45](subscribe to relevant topics)
@[49](publisher to publish final waypoints for control module to follow)
@[59-62](start processing in loop at required frequency, Hz)
@[64-84](callbacks to receive messages)
@[167-210](main 'planner' logic)






---
@title[Control Module]

### Control Module

- waypoint follower (C++)
    - subscribe to /final_waypoints
    - calculate/publish /twist_cmd to follow waypoints and speeds
- DBW node

![Image-absolute](pydata-presentation/imgs/dbw-node.png)

@fa[arrow-down]


+++?code=ros/src/waypoint_follower/src/pure_pursuit.cpp&lang=cpp&title=waypoint_follower/pure_pursuit.cpp: Trajectory Planner
@[40-44](init ROS node)
@[52-54](publisher for /twist_cmd)
@[56-63](subscribers)
@[65-72](spin at specified rate)

@fa[arrow-down]


+++?code=ros/src/twist_controller/dbw_node.py&lang=python&title=dbw_node.py: DBW Controllers
@[53](init ROS node)
@[55-69](read vehicle parameters)
@[83-88](create publishers)
@[90-101](initialise PID controller for steer/brake/throttle)
@[103-126](subscribe to what we need)
@[128-149](main loop at 50Hz: estimate controls, publish)






---
@title[Debug Tools]

### Debug Tools

- ROS Rviz
- ROS rqt
- custom made

@fa[arrow-down]


+++
@title[ROS Rviz]

### ROS Rviz

![Image-absolute](pydata-presentation/imgs/rviz-rosbag-play.gif)

@fa[arrow-down]


+++
@title[ROS rqt]

### ROS RQT

![Image-absolute](pydata-presentation/imgs/rqt.png)


@fa[arrow-down]


+++
@title[Custom Made Diagnostics Tool]

### Custom Made Diagnostics Tool

- PyQt5
- matplotlib
- separate ROS node

@fa[arrow-down]


+++?image=pydata-presentation/imgs/kairos-diagnostics.png

+++?code=ros/src/waypoint_updater/show_waypoints.py&lang=python&title=show_waypoints.py: Diagnostics Tool
@[13-15](using PyQt5)
@[29-31,35](using matplotlib)
@[38](it is a widget)
@[46](and a ROS node)
@[51-105](subscribe to all we need)
@[107-112](initialize and start update loop)
@[124-151](matplotlib definitions)
@[167-201](matplotlib figure update with fresh data)




---
### Final Video: Simulator

![YouTube Video](https://youtube.com/embed/956Q7wU0-lE?t=28s)



---
### Final Video: ROS Bag from Car

![YouTube Video](https://youtube.com/embed/08Td9rkB7o8)



