#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时GNSS-STAMP系统测试脚本
用于验证系统各个组件的功能
"""

import os
import sys
import time
import threading
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from realtime_gnss_stamp import NMEABuffer, RealtimeGNSSSTAMP, load_realtime_config
from gnss_stamp_integration import STAMPProcessor
from stamp_improved import module_a_generate_stamp

def test_nmea_buffer():
    """测试NMEA数据缓冲器"""
    print("🧪 测试NMEA数据缓冲器...")
    
    buffer = NMEABuffer()
    
    # 测试数据
    test_sentences = [
        "$GPRMC,000012.00,A,3031.9000425,N,11421.4368798,E,0.01,0.00,010525,0.0,E,A*37",
        "$GPGGA,000012.00,3031.9000425,N,11421.4368798,E,1,08,1.0,42.636,M,-13.987,M,0.0,*57",
        "$GPRMC,000042.00,A,3031.8994888,N,11421.4369982,E,0.01,0.00,010525,0.0,E,A*38",
        "$GPGGA,000042.00,3031.8994888,N,11421.4369982,E,1,08,1.0,44.391,M,-13.987,M,0.0,*56"
    ]
    
    matched_pairs = 0
    
    for sentence in test_sentences:
        result = buffer.add_nmea_sentence(sentence)
        if result:
            matched_pairs += 1
            gprmc, gpgga = result
            print(f"  ✅ 匹配对 #{matched_pairs}:")
            print(f"    GPRMC: {gprmc[:50]}...")
            print(f"    GPGGA: {gpgga[:50]}...")
    
    print(f"✅ NMEA缓冲器测试完成，匹配到 {matched_pairs} 对数据")
    return matched_pairs > 0

def test_stamp_encoding():
    """测试STAMP编码功能"""
    print("\n🧪 测试STAMP编码功能...")
    
    # 测试数据
    gprmc = "$GPRMC,000012.00,A,3031.9000425,N,11421.4368798,E,0.01,0.00,010525,0.0,E,A*37"
    gpgga = "$GPGGA,000012.00,3031.9000425,N,11421.4368798,E,1,08,1.0,42.636,M,-13.987,M,0.0,*57"
    
    device_id = bytes.fromhex("DEADBEEFCAFEBABE")
    link_id = 1024
    sync_status = "beidouLocked"
    
    # 创建STAMP处理器
    processor = STAMPProcessor(device_id, link_id, sync_status)
    
    # 测试编码
    stamp_payload = processor.process_nmea_data(gprmc, gpgga)
    
    if stamp_payload:
        print(f"  ✅ STAMP编码成功，长度: {len(stamp_payload)} 字节")
        print(f"  📦 编码数据: {stamp_payload.hex()[:100]}...")
        return True
    else:
        print("  ❌ STAMP编码失败")
        return False

def test_config_loading():
    """测试配置加载"""
    print("\n🧪 测试配置加载...")
    
    try:
        config = load_realtime_config()
        print("  ✅ 配置加载成功:")
        for key, value in config.items():
            print(f"    {key}: {value}")
        return True
    except Exception as e:
        print(f"  ❌ 配置加载失败: {e}")
        return False

def test_directory_creation():
    """测试输出目录创建"""
    print("\n🧪 测试输出目录创建...")
    
    test_dirs = [
        "IGS-Data/STAMP-Realtime",
        "IGS-Data/STAMP-Output"
    ]
    
    success = True
    for dir_path in test_dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            if os.path.exists(dir_path):
                print(f"  ✅ 目录创建成功: {dir_path}")
            else:
                print(f"  ❌ 目录创建失败: {dir_path}")
                success = False
        except Exception as e:
            print(f"  ❌ 目录创建异常: {dir_path} - {e}")
            success = False
    
    return success

def simulate_serial_data():
    """模拟串口数据测试"""
    print("\n🧪 模拟串口数据测试...")
    
    # 模拟NMEA数据
    test_data = [
        "$GPRMC,000012.00,A,3031.9000425,N,11421.4368798,E,0.01,0.00,010525,0.0,E,A*37",
        "$GPGGA,000012.00,3031.9000425,N,11421.4368798,E,1,08,1.0,42.636,M,-13.987,M,0.0,*57",
        "$GPRMC,000042.00,A,3031.8994888,N,11421.4369982,E,0.01,0.00,010525,0.0,E,A*38",
        "$GPGGA,000042.00,3031.8994888,N,11421.4369982,E,1,08,1.0,44.391,M,-13.987,M,0.0,*56",
        "$GPRMC,000112.00,A,3031.8998777,N,11421.4366786,E,0.01,0.00,010525,0.0,E,A*3A",
        "$GPGGA,000112.00,3031.8998777,N,11421.4366786,E,1,08,1.0,42.811,M,-13.987,M,0.0,*51"
    ]
    
    # 创建配置
    config = {
        "device_id": "DEADBEEFCAFEBABE",
        "link_id": 1024,
        "sync_status": "beidouLocked",
        "src_ip": "2001:db8:1::1",
        "dst_ip": "2001:db8:2::2",
        "output_dir": "IGS-Data/STAMP-Test"
    }
    
    # 创建处理器
    device_id = bytes.fromhex(config['device_id'])
    processor = STAMPProcessor(device_id, config['link_id'], config['sync_status'])
    
    # 创建NMEA缓冲器
    buffer = NMEABuffer()
    
    processed_count = 0
    
    print("  📡 模拟处理NMEA数据...")
    
    for sentence in test_data:
        # 添加到缓冲器
        result = buffer.add_nmea_sentence(sentence)
        
        if result:
            gprmc, gpgga = result
            print(f"    📍 处理数据对 #{processed_count + 1}")
            
            # 尝试编码
            stamp_payload = processor.process_nmea_data(gprmc, gpgga)
            
            if stamp_payload:
                processed_count += 1
                print(f"      ✅ 编码成功，长度: {len(stamp_payload)} 字节")
            else:
                print(f"      ❌ 编码失败")
    
    print(f"  ✅ 模拟测试完成，成功处理 {processed_count} 个数据对")
    return processed_count > 0

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始实时GNSS-STAMP系统测试")
    print("=" * 60)
    
    tests = [
        ("NMEA数据缓冲器", test_nmea_buffer),
        ("STAMP编码功能", test_stamp_encoding),
        ("配置加载", test_config_loading),
        ("输出目录创建", test_directory_creation),
        ("模拟串口数据", simulate_serial_data)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 测试: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统准备就绪")
        return True
    else:
        print("⚠️  部分测试失败，请检查系统配置")
        return False

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("""
🧪 实时GNSS-STAMP系统测试工具

使用方法:
  python test_realtime_system.py        运行所有测试
  python test_realtime_system.py -h     显示帮助信息

测试项目:
  1. NMEA数据缓冲器功能
  2. STAMP编码功能
  3. 配置文件加载
  4. 输出目录创建
  5. 模拟串口数据处理

测试目的:
  验证实时处理系统的各个组件是否正常工作
""")
        return
    
    success = run_all_tests()
    
    if success:
        print("\n🚀 系统测试完成，可以开始使用实时处理功能")
        print("💡 提示: 运行 python run_realtime_gnss.py 开始实时处理")
    else:
        print("\n🔧 系统测试发现问题，请检查配置和依赖")
        sys.exit(1)

if __name__ == '__main__':
    main()
