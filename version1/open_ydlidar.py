import os
import ydlidar
import time
import math

if __name__ == "__main__":
    ydlidar.os_init()
    ports = ydlidar.lidarPortList()
    port = "/dev/ydlidar"
    for key, value in ports.items():
        port = value
    laser = ydlidar.CYdLidar()
    
    # 设置激光雷达参数
    laser.setlidaropt(ydlidar.LidarPropSerialPort, port)
    laser.setlidaropt(ydlidar.LidarPropSerialBaudrate, 230400)
    laser.setlidaropt(ydlidar.LidarPropLidarType, ydlidar.TYPE_TRIANGLE)
    laser.setlidaropt(ydlidar.LidarPropDeviceType, ydlidar.YDLIDAR_TYPE_SERIAL)
    laser.setlidaropt(ydlidar.LidarPropScanFrequency, 10.0)
    laser.setlidaropt(ydlidar.LidarPropSampleRate, 5)
    laser.setlidaropt(ydlidar.LidarPropSingleChannel, False)
    laser.setlidaropt(ydlidar.LidarPropMaxAngle, 180.0)
    laser.setlidaropt(ydlidar.LidarPropMinAngle, -180.0)
    laser.setlidaropt(ydlidar.LidarPropMaxRange, 16.0)
    laser.setlidaropt(ydlidar.LidarPropMinRange, 0.08)
    laser.setlidaropt(ydlidar.LidarPropIntenstiy, False)

    ret = laser.initialize()
    
    if ret:
        ret = laser.turnOn()
        scan = ydlidar.LaserScan()
        last_print_time = time.time()  # 初始化打印时间
        
        while ret and ydlidar.os_isOk():
            r = laser.doProcessSimple(scan)
            if r:
                current_time = time.time()
                
                # 每隔5秒打印一次
                if current_time - last_print_time >= 5.0:
                    last_print_time = current_time
                    
                    # 数据保存到本地
                    with open("lidar_data.txt", "a") as f:
                        for point in scan.points:
                            angle_degrees = point.angle * (180 / math.pi)  # 将弧度转换为度
                            distance_cm = point.range * 100  # 将距离从米转换为厘米
                            f.write(f"Angle: {angle_degrees:.2f} degrees, Distance: {distance_cm:.2f} cm\n")
                    # print(f"Scan received [{scan.stamp}]: {scan.points.size()} points saved.")

            else:
                print("Failed to get Lidar Data")
            
            time.sleep(0.5)  # 处理间隔
            
        laser.turnOff()
    
    laser.disconnecting()
