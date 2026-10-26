# Stingray (Stormy) wrapper launch for wifi_logger_visualizer v2.
# Keeps Mike's upstream launch/config pristine; this file plus
# config/stingray_wifi_params.yaml are the only Stingray-specific additions
# (branch local/stingray-v2). It mirrors the node set of Mike's
# wifi_logger_visualizer.launch.py, loading his config first then our overrides.
#
# Friendly AP names for the browser live OUTSIDE the repo (home AP MACs,
# intentionally uncommitted) at ~/robot_logs/wifi/access_points.yaml; pass to the
# viewer:  ros2 run wifi_logger_visualizer web_viewer.py \
#     --db ~/robot_logs/wifi/stingray_wifi.db \
#     --node-names ~/robot_logs/wifi/access_points.yaml
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory("wifi_logger_visualizer")
    params = [
        os.path.join(share, "config", "wifi_logger_config.yaml"),
        os.path.join(share, "config", "stingray_wifi_params.yaml"),
    ]
    monitoring = LaunchConfiguration("monitoring")
    survey = LaunchConfiguration("survey")
    return LaunchDescription([
        DeclareLaunchArgument("monitoring", default_value="true"),
        DeclareLaunchArgument("survey", default_value="false"),
        DeclareLaunchArgument("visualization", default_value="true"),
        Node(
            package="wifi_logger_visualizer",
            executable="wifi_logger_node.py",
            condition=IfCondition(
                PythonExpression(["'", monitoring, "' == 'true' or '", survey, "' == 'true'"])
            ),
            parameters=params,
            output="screen",
        ),
        Node(
            package="wifi_logger_visualizer",
            executable="wifi_visualizer_node.py",
            condition=IfCondition(LaunchConfiguration("visualization")),
            parameters=params,
            output="screen",
        ),
        Node(
            package="wifi_logger_visualizer",
            executable="survey_node.py",
            condition=IfCondition(survey),
            parameters=params,
            output="screen",
        ),
    ])