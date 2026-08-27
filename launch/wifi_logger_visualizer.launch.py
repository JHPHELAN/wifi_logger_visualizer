from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node
import os

def generate_launch_description():
    ld = LaunchDescription()

    package_name = 'wifi_logger_visualizer'
    package_dir = get_package_share_directory(package_name)
    config_filepath = os.path.join(package_dir, 'config', 'wifi_logger_config.yaml')

    # Declare conditions:
    run_logger = LaunchConfiguration('run_logger')
    run_logger_arg = DeclareLaunchArgument(
        'run_logger',
        default_value='True',
        description='Run the wifi logger node'
    )
    ld.add_action(run_logger_arg)
    
    run_visualizer = LaunchConfiguration('run_visualizer')
    run_visualizer_arg = DeclareLaunchArgument(
        'run_visualizer',
        default_value='True',
        description='Run the wifi visualizer node'
    )
    ld.add_action(run_visualizer_arg)
    
    run_heatmapper = LaunchConfiguration('run_heatmapper')
    run_heatmapper_arg = DeclareLaunchArgument(
        'run_heatmapper',
        default_value='True',
        description='Run the heat mapper node'
    )
    ld.add_action(run_heatmapper_arg)
    
    ld.add_action(LogInfo(msg=["[wifi_logger_visualizer.launch.py] ",
                               " run_logger: ", run_logger,
                               ", run_visualizer: ", run_visualizer,
                               ", run_heatmapper: ", run_heatmapper]))

    # Declare launch arguments for nodes:
    # NOTE: db_path defaults to '' (unset) so the YAML config's db_path wins.
    # In parameters=[config_filepath, {...}], any key present in the dict
    # overrides the same key from the YAML. When the CLI does not pass
    # db_path:=..., we must NOT put db_path in the override dict, or the
    # YAML absolute pin is silently discarded and the node opens
    # <cwd>/wifi_data.db instead. This matches the pattern already used in
    # heat_mapper.launch.py.
    db_path_arg = DeclareLaunchArgument(
        'db_path',
        default_value='',
        description='Optional SQLite DB path override (defaults to YAML value)'
    )

    # Same empty-default pattern as db_path: '' means "leave YAML alone".
    db_clear_on_start_arg = DeclareLaunchArgument(
        'db_clear_on_start',
        default_value='',
        description="Optional bool override: 'true' or 'false'. Empty defers to YAML."
    )
    
    publish_frequency_arg = DeclareLaunchArgument(
        'publish_frequency',
        default_value='1.0',
        description='Frequency at which to publish costmaps (Hz)'
    )
    
    db_check_frequency_arg = DeclareLaunchArgument(
        'db_check_frequency',
        default_value='2.0',
        description='Frequency at which to check for database updates (Hz)'
    )
    
    max_interpolation_distance_arg = DeclareLaunchArgument(
        'max_interpolation_distance',
        default_value='1.0',
        description='Maximum distance for interpolation in meters'
    )
    
    enable_link_quality_arg = DeclareLaunchArgument(
        'enable_link_quality',
        default_value='true',
        description='Enable link quality costmap'
    )
    
    enable_signal_level_arg = DeclareLaunchArgument(
        'enable_signal_level',
        default_value='true',
        description='Enable signal level costmap'
    )
    
    enable_bit_rate_arg = DeclareLaunchArgument(
        'enable_bit_rate',
        default_value='true',
        description='Enable bit rate costmap'
    )
    
    costmap_topic_arg = DeclareLaunchArgument(
        'costmap_topic',
        default_value='/global_costmap/costmap',
        description='Topic to read costmap dimensions from'
    )

    for action in [
        db_path_arg,
        db_clear_on_start_arg,
        publish_frequency_arg,
        db_check_frequency_arg,
        max_interpolation_distance_arg,
        enable_link_quality_arg,
        enable_signal_level_arg,
        enable_bit_rate_arg,
        costmap_topic_arg,
    ]:
        ld.add_action(action)
    
    # db_path resolution: when the user did not pass db_path:=..., the
    # LaunchConfiguration resolves to '' (see db_path_arg default above),
    # and we omit db_path from the override dict so the YAML wins. When
    # the user did pass a path, we include it so CLI wins over YAML.
    def _build_nodes(context):
        db_path = LaunchConfiguration('db_path').perform(context)
        db_override = {'db_path': db_path} if db_path else {}

        db_clear_str = LaunchConfiguration('db_clear_on_start').perform(context).strip().lower()
        if db_clear_str in ('true', '1', 'yes', 'on'):
            db_override['db_clear_on_start'] = True
        elif db_clear_str in ('false', '0', 'no', 'off'):
            db_override['db_clear_on_start'] = False

        wifi_loger_node = Node(
            condition=IfCondition(run_logger),
            package=package_name,
            executable='wifi_logger_node.py',
            name='wifi_logger_node',
            parameters=[
                config_filepath,
                db_override,
            ],
            # arguments=['--ros-args', '--log-level', 'DEBUG'],
            output='screen'
        )

        wifi_visualizer_node = Node(
            condition=IfCondition(run_visualizer),
            package=package_name,
            executable='wifi_visualizer_node.py',
            name='wifi_visualizer_node',
            output='screen',
            parameters=[
                config_filepath,
                {
                    **db_override,
                    'publish_frequency': LaunchConfiguration('publish_frequency'),
                    'db_check_frequency': LaunchConfiguration('db_check_frequency'),
                    'max_interpolation_distance': LaunchConfiguration('max_interpolation_distance'),
                    'enable_link_quality': LaunchConfiguration('enable_link_quality'),
                    'enable_signal_level': LaunchConfiguration('enable_signal_level'),
                    'enable_bit_rate': LaunchConfiguration('enable_bit_rate'),
                    'costmap_topic': LaunchConfiguration('costmap_topic')
                }
            ]
        )

        heat_mapper_node = Node(
            condition=IfCondition(run_heatmapper),
            package=package_name,
            executable='heat_mapper_node.py',
            name='heat_mapper_node',
            output='screen',
            parameters=[
                config_filepath,
                {
                    **db_override,
                    'costmap_topic': LaunchConfiguration('costmap_topic')
                }
            ]
        )

        return [wifi_loger_node, wifi_visualizer_node, heat_mapper_node]

    ld.add_action(OpaqueFunction(function=_build_nodes))


    return ld
