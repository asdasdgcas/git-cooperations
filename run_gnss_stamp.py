#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GNSS-STAMP系统启动脚本
简化版本，用于快速测试和演示
"""

import os
import sys
import json
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gnss_stamp_integration import GNSSSTAMPIntegration, load_config

def quick_test():
    """快速测试模式"""
    print("🚀 GNSS-STAMP集成系统快速测试")
    print("=" * 50)
    
    # 检查POS文件是否存在
    pos_file = "IGS-Data/JBDH/2025/121/JBDH_2025_121_WUH2_B_D.pos"
    if not os.path.exists(pos_file):
        print(f"❌ 错误：找不到POS文件 {pos_file}")
        print("请先运行GNSS定位软件生成数据文件")
        return False
    
    # 创建测试配置
    test_config = {
        "pos_file_path": pos_file,
        "device_id": "DEADBEEFCAFEBABE",
        "link_id": 1024,
        "sync_status": "beidouLocked",
        "src_ip": "2001:db8:1::1",
        "dst_ip": "2001:db8:2::2",
        "processing_mode": "single"
    }
    
    print(f"📁 数据文件: {pos_file}")
    print(f"🔧 设备ID: {test_config['device_id']}")
    print(f"🔗 链路ID: {test_config['link_id']}")
    print(f"📡 同步状态: {test_config['sync_status']}")
    print()
    
    # 创建集成系统
    integration = GNSSSTAMPIntegration(test_config)
    
    # 运行处理
    print("🔄 开始处理NMEA数据...")
    success = integration.run_single_processing()
    
    if success:
        print("\n✅ 处理完成！")
        print("📊 查看 gnss_stamp.log 文件获取详细日志")
        return True
    else:
        print("\n❌ 处理失败！")
        return False

def interactive_mode():
    """交互模式"""
    print("🎯 GNSS-STAMP集成系统交互模式")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    
    print("当前配置:")
    print(f"  数据文件: {config['pos_file_path']}")
    print(f"  处理模式: {config['processing_mode']}")
    print(f"  设备ID: {config['device_id']}")
    print()
    
    # 选择处理模式
    print("请选择处理模式:")
    print("1. 单次处理 (处理所有数据)")
    print("2. 实时处理 (持续监控)")
    print("3. 退出")
    
    choice = input("请输入选择 (1-3): ").strip()
    
    if choice == '1':
        integration = GNSSSTAMPIntegration(config)
        integration.run_single_processing()
    elif choice == '2':
        interval = float(input("请输入处理间隔(秒，默认1.0): ") or "1.0")
        integration = GNSSSTAMPIntegration(config)
        integration.run_realtime_processing(interval)
    elif choice == '3':
        print("👋 再见！")
        return
    else:
        print("❌ 无效选择")

def show_help():
    """显示帮助信息"""
    print("""
🛰️  GNSS-STAMP集成系统使用说明

📋 功能说明:
   - 读取GNSS定位软件生成的NMEA格式数据
   - 将GPGGA/GPRMC数据转换为STAMP协议格式
   - 通过IPv6网络传输时空数据包

🚀 使用方法:
   python run_gnss_stamp.py [选项]

📝 选项:
   -h, --help     显示此帮助信息
   -t, --test     快速测试模式
   -i, --interactive  交互模式
   -c, --config   指定配置文件路径

📁 文件说明:
   - gnss_stamp_config.json    配置文件
   - gnss_stamp.log           日志文件
   - stamp_improved.py        STAMP协议模块
   - gnss_stamp_integration.py 集成系统主程序

🔧 配置说明:
   修改 gnss_stamp_config.json 文件来调整系统参数:
   - pos_file_path: GNSS输出文件路径
   - device_id: 设备标识符(16位十六进制)
   - link_id: 链路标识符(0-65535)
   - sync_status: 同步状态(beidouLocked/gpsLocked等)
   - processing_mode: 处理模式(single/realtime)

📊 输出格式:
   系统会生成STAMP协议格式的数据包，包含:
   - 时间戳(秒和纳秒)
   - 经纬度坐标
   - 海拔高度
   - 设备信息
   - CRC校验码

🔍 故障排除:
   1. 确保GNSS软件已运行并生成.pos文件
   2. 检查配置文件中的文件路径是否正确
   3. 查看gnss_stamp.log日志文件获取详细错误信息
   4. 确保安装了所需的Python依赖包

📞 技术支持:
   如有问题，请查看日志文件或联系开发团队
""")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['-h', '--help']:
            show_help()
        elif arg in ['-t', '--test']:
            quick_test()
        elif arg in ['-i', '--interactive']:
            interactive_mode()
        elif arg in ['-c', '--config']:
            if len(sys.argv) > 2:
                config_file = sys.argv[2]
                config = load_config(config_file)
                integration = GNSSSTAMPIntegration(config)
                integration.run_single_processing()
            else:
                print("❌ 请指定配置文件路径")
        else:
            print("❌ 未知选项，使用 -h 查看帮助")
    else:
        # 默认运行快速测试
        quick_test()

if __name__ == '__main__':
    main()
