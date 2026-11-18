cmake_minimum_required(VERSION 3.8)
project(handheld_scanner_mapping)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})

ament_package()
