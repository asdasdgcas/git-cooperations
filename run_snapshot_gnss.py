#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快照GNSS-STAMP系统启动脚本
用于快速获取当前时刻的GNSS数据快照
"""

import os
import sys
import json
import serial.tools.list_ports
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from snapshot_gnss_stamp import SnapshotGNSSSTAMP, load_snapshot_config

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

def quick_snapshot():
    """快速快照模式"""
    print("📸 快照GNSS-STAMP系统 - 快速模式")
    print("=" * 50)
    
    # 加载配置
    config = load_snapshot_config()
    
    print("当前配置:")
    print(f"  串口: {config['serial_port']} @ {config['serial_baudrate']}")
    print(f"  设备ID: {config['device_id']}")
    print(f"  链路ID: {config['link_id']}")
    print(f"  读取超时: {config['read_timeout']}秒")
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
        print("🎯 准备获取GNSS数据快照...")
        print("📌 提示: 确保GNSS设备正在输出NMEA数据")
        print("📌 系统将读取当前时刻的一对GPGGA和GPRMC数据")
        print()
        
        input("按回车键开始获取快照...")
        
    except KeyboardInterrupt:
        print("\n👋 已取消操作")
        return False
    
    # 创建并启动快照系统
    snapshot_system = SnapshotGNSSSTAMP(config)
    
    try:
        success = snapshot_system.capture_snapshot()
        return success
    except Exception as e:
        print(f"❌ 系统运行异常: {e}")
        return False

def config_mode():
    """配置模式"""
    print("⚙️  快照GNSS-STAMP系统 - 配置模式")
    print("=" * 50)
    
    config_file = 'snapshot_gnss_config.json'
    config = load_snapshot_config(config_file)
    
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
            
        new_timeout = input(f"读取超时(秒) [{config['read_timeout']}]: ").strip()
        if new_timeout:
            try:
                config['read_timeout'] = float(new_timeout)
            except ValueError:
                print("⚠️ 超时值无效，保持原值")
            
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
📸 快照GNSS-STAMP系统使用说明

📋 功能说明:
   - 从串口读取当前时刻的GPGGA和GPRMC数据
   - 进行一次STAMP协议编码后停止
   - 生成包含单条数据的HEX和JSON文件

🚀 使用方法:
   python run_snapshot_gnss.py [选项]

📝 选项:
   -h, --help      显示此帮助信息
   -q, --quick     快速快照模式 (默认)
   -c, --config    配置模式

📁 输出文件:
   - IGS-Data/STAMP-Snapshot/stamp_encoded_*.hex    编码数据(十六进制)
   - IGS-Data/STAMP-Snapshot/stamp_results_*.json   编码结果(JSON格式)
   - snapshot_gnss_stamp.log                        运行日志

⚙️  配置文件:
   - snapshot_gnss_config.json    快照系统配置文件

🆚 与实时系统的区别:
   - 实时系统: 持续读取和编码数据，直到手动停止
   - 快照系统: 只读取当前时刻的一对数据，编码后自动停止

🔧 使用场景:
   - 测试GNSS设备当前状态
   - 获取特定时刻的位置数据
   - 验证STAMP编码功能
   - 调试和故障排除

📞 使用流程:
   1. 连接GNSS设备到串口
   2. 运行 python run_snapshot_gnss.py
   3. 选择正确的串口
   4. 系统自动获取一对NMEA数据
   5. 完成STAMP编码并保存文件
   6. 查看输出文件
""")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['-h', '--help']:
            show_help()
        elif arg in ['-c', '--config']:
            config_mode()
        elif arg in ['-q', '--quick']:
            quick_snapshot()
        else:
            print("❌ 未知选项，使用 -h 查看帮助")
    else:
        # 默认快速快照
        quick_snapshot()

if __name__ == '__main__':
    main()

