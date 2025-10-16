cmake_minimum_required(VERSION 3.16)
project(stest)

find_package(SEAL REQUIRED)

if(SEAL_FOUND)
	include_directories(${SEAL_INCLUDE_DIRS})
	
	add_executable(stest test.cpp)
	target_link_libraries(stest SEAL::seal)
else()
	message(FATAL_ERROR "Microsoft SEAL library not found.")
endif()