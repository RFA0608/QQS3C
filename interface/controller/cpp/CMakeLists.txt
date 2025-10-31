cmake_minimum_required(VERSION 3.16)
project(enc_ctrl)

find_package(SEAL REQUIRED)

if(SEAL_FOUND)
	include_directories(${SEAL_INCLUDE_DIRS})
	
	add_executable(system_enc ctrl_arx_enc.cpp)
	target_link_libraries(system_enc SEAL::seal)
else()
	message(FATAL_ERROR "Microsoft SEAL library not found.")
endif()