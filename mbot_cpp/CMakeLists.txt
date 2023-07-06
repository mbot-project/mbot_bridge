cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
project(mbot_bridge)

set(CMAKE_BUILD_TYPE RelWithDebInfo)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++14")

find_package(websocketpp)
find_package(mbot_lcm_msgs)

add_executable(mbot_cpp_test test/test_mbot_api.cpp)
target_link_libraries(mbot_cpp_test
)
target_include_directories(mbot_cpp_test PRIVATE
  include
)
