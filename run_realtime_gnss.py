#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时GNSS-STAMP系统启动脚本
简化版本，用于快速启动实时处理
"""

import os
import sys
import json
import serial.tools.list_ports
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from realtime_gnss_stamp import RealtimeGNSSSTAMP, load_realtime_config

def show_available_ports():
    """显示可用串口"""
    print("🔍 检测可用串口...")
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("❌ 未检测到任何串口设备")
        return []
    else:
        print("✅ 可用串口:")
        available_ports = []
        for i, port in enumerate(ports, 1):
            print(f"  {i}. {port.device} - {port.description}")
            available_ports.append(port.device)
        return available_ports

def select_port_interactive():
    """交互式选择串口"""
    available_ports = show_available_ports()
    
    if not available_ports:
        return None
        
    print()
    while True:
        try:
            choice = input(f"请选择串口 (1-{len(available_ports)}) 或直接输入串口名 (如COM3): ").strip()
            
            # 如果输入的是数字
            if choice.isdigit():
                index = int(choice) - 1
                if 0 <= index < len(available_ports):
                    return available_ports[index]
                else:
                    print(f"❌ 请输入 1-{len(available_ports)} 之间的数字")
            # 如果直接输入串口名
            elif choice.upper().startswith('COM') or choice.startswith('/dev/'):
                return choice.upper() if choice.upper().startswith('COM') else choice
            else:
                print("❌ 请输入有效的选择")
                
        except KeyboardInterrupt:
            print("\n👋 已取消")
            return None
        except Exception as e:
            print(f"❌ 输入错误: {e}")

def quick_start():
    """快速启动模式"""
    print("🚀 实时GNSS-STAMP系统 - 快速启动")
    print("=" * 50)
    
    # 加载配置
    config = load_realtime_config()
    
    print("当前配置:")
    print(f"  串口: {config['serial_port']} @ {config['serial_baudrate']}")
    print(f"  设备ID: {config['device_id']}")
    print(f"  链路ID: {config['link_id']}")
    print(f"  同步状态: {config['sync_status']}")
    print(f"  输出目录: {config['output_dir']}")
    print()
    
    # 询问是否要更改串口
    try:
        change_port = input("是否要更改串口设置? (y/N): ").strip().lower()
        if change_port in ['y', 'yes']:
            selected_port = select_port_interactive()
            if selected_port:
                config['serial_port'] = selected_port
                print(f"✅ 串口已更改为: {selected_port}")
            else:
                print("❌ 未选择串口，使用默认配置")
        
        print()
        print("🎯 准备启动实时处理...")
        print("📌 提示: 按 Ctrl+C 可以停止处理")
        print()
        
        input("按回车键开始处理...")
        
    except KeyboardInterrupt:
        print("\n👋 已取消启动")
        return False
    
    # 创建并启动实时系统
    realtime_system = RealtimeGNSSSTAMP(config)
    
    try:
        success = realtime_system.start_realtime_processing()
        return success
    except Exception as e:
        print(f"❌ 系统运行异常: {e}")
        return False

def config_mode():
    """配置模式"""
    print("⚙️  实时GNSS-STAMP系统 - 配置模式")
    print("=" * 50)
    
    config_file = 'realtime_gnss_config.json'
    config = load_realtime_config(config_file)
    
    print("当前配置:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()
    
    # 交互式配置
    try:
        print("请输入新的配置值 (直接回车保持当前值):")
        
        # 串口配置
        available_ports = show_available_ports()
        new_port = input(f"串口 [{config['serial_port']}]: ").strip()
        if new_port:
            config['serial_port'] = new_port.upper() if new_port.upper().startswith('COM') else new_port
            
        new_baudrate = input(f"波特率 [{config['serial_baudrate']}]: ").strip()
        if new_baudrate and new_baudrate.isdigit():
            config['serial_baudrate'] = int(new_baudrate)
            
        # 设备配置
        new_device_id = input(f"设备ID (16位十六进制) [{config['device_id']}]: ").strip()
        if new_device_id:
            config['device_id'] = new_device_id.upper()
            
        new_link_id = input(f"链路ID [{config['link_id']}]: ").strip()
        if new_link_id and new_link_id.isdigit():
            config['link_id'] = int(new_link_id)
            
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        print(f"✅ 配置已保存到: {config_file}")
        
    except KeyboardInterrupt:
        print("\n👋 配置已取消")
        return False
        
    return True

def show_help():
    """显示帮助信息"""
    print("""
🛰️  实时GNSS-STAMP系统使用说明

📋 功能说明:
   - 从串口实时读取GPGGA和GPRMC数据
   - 自动匹配NMEA数据对
   - 实时进行STAMP协议编码
   - 保存编码结果到文件

🚀 使用方法:
   python run_realtime_gnss.py [选项]

📝 选项:
   -h, --help      显示此帮助信息
   -q, --quick     快速启动模式 (默认)
   -c, --config    配置模式
   -t, --test      测试串口连接

📁 输出文件:
   - IGS-Data/STAMP-Realtime/stamp_encoded_*.hex    编码数据(十六进制)
   - IGS-Data/STAMP-Realtime/stamp_results_*.json   编码结果(JSON格式)
   - realtime_gnss_stamp.log                        运行日志

⚙️  配置文件:
   - realtime_gnss_config.json    系统配置文件

🔧 常见问题:
   1. 串口连接失败 - 检查串口号和波特率设置
   2. 没有NMEA数据 - 确认GNSS设备正常工作
   3. 编码失败 - 检查NMEA数据格式是否正确

📞 使用流程:
   1. 连接GNSS设备到串口
   2. 运行 python run_realtime_gnss.py
   3. 选择正确的串口
   4. 开始实时处理
   5. 按Ctrl+C停止处理
   6. 查看输出文件和日志
""")

def test_serial_connection():
    """测试串口连接"""
    print("🔧 串口连接测试")
    print("=" * 30)
    
    # 显示可用串口
    available_ports = show_available_ports()
    if not available_ports:
        return False
        
    # 选择串口
    selected_port = select_port_interactive()
    if not selected_port:
        return False
        
    # 测试连接
    print(f"\n🔌 测试连接到 {selected_port}...")
    
    try:
        import serial
        ser = serial.Serial(
            port=selected_port,
            baudrate=115200,
            timeout=1
        )
        
        if ser.is_open:
            print(f"✅ 串口连接成功: {selected_port}")
            
            # 尝试读取几行数据
            print("📡 尝试读取数据 (5秒)...")
            import time
            start_time = time.time()
            data_count = 0
            
            while time.time() - start_time < 5:
                if ser.in_waiting > 0:
                    try:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            data_count += 1
                            print(f"[{data_count}] {line}")
                            if data_count >= 10:  # 最多显示10行
                                break
                    except:
                        pass
                time.sleep(0.1)
                
            ser.close()
            
            if data_count > 0:
                print(f"✅ 测试成功: 接收到 {data_count} 行数据")
            else:
                print("⚠️  未接收到数据，请检查设备是否正常工作")
                
            return True
        else:
            print(f"❌ 串口连接失败: {selected_port}")
            return False
            
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['-h', '--help']:
            show_help()
        elif arg in ['-c', '--config']:
            config_mode()
        elif arg in ['-t', '--test']:
            test_serial_connection()
        elif arg in ['-q', '--quick']:
            quick_start()
        else:
            print("❌ 未知选项，使用 -h 查看帮助")
    else:
        # 默认快速启动
        quick_start()

if __name__ == '__main__':
    main()
