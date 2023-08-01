cmake_minimum_required(VERSION 3.12 FATAL_ERROR)
project(mbot_bridge)

set(CMAKE_BUILD_TYPE RelWithDebInfo)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++14")

find_package(websocketpp REQUIRED)
find_package(mbot_lcm_msgs REQUIRED)
find_package(Threads REQUIRED)

add_library(mbot_cpp STATIC
  src/robot.cpp
)
target_link_libraries(mbot_cpp
  ${CMAKE_THREAD_LIBS_INIT}
)
target_include_directories(mbot_cpp PUBLIC
  include
)

add_executable(mbot_cpp_test test/test_mbot_api.cpp
)
target_link_libraries(mbot_cpp_test
  mbot_cpp
)
target_include_directories(mbot_cpp_test PRIVATE
  include
)
