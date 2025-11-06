#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快照GNSS-STAMP系统
从串口读取当前时刻的GPGGA和GPRMC数据，进行一次STAMP编码后停止
"""

import os
import sys
import time
import json
import serial
import serial.tools.list_ports
from datetime import datetime
from typing import Dict, Optional, Tuple
import logging

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gnss_stamp_integration import STAMPProcessor, NetworkTransmitter, load_config
from realtime_gnss_stamp import NMEABuffer, load_realtime_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('snapshot_gnss_stamp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SnapshotSerialReader:
    """快照串口数据读取器 - 只读取一对NMEA数据"""
    
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 30.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None
        self.nmea_buffer = NMEABuffer()
        
    def find_available_ports(self) -> list:
        """列出可用的串口"""
        ports = serial.tools.list_ports.comports()
        available_ports = []
        
        if not ports:
            logger.warning("未检测到任何串口设备")
        else:
            logger.info("可用串口:")
            for port in ports:
                logger.info(f"  {port.device} - {port.description}")
                available_ports.append(port.device)
                
        return available_ports
    
    def connect(self) -> bool:
        """连接串口"""
        try:
            logger.info(f"正在连接串口 {self.port} @ {self.baudrate}...")
            
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            
            time.sleep(1)  # 等待连接稳定
            
            if self.serial_conn.is_open:
                logger.info(f"✅ 成功连接串口: {self.serial_conn.port}")
                return True
            else:
                logger.error("串口连接失败")
                return False
                
        except serial.SerialException as e:
            logger.error(f"无法打开串口: {e}")
            return False
        except Exception as e:
            logger.error(f"串口连接异常: {e}")
            return False
    
    def read_single_nmea_pair(self) -> Optional[Tuple[str, str]]:
        """读取单对NMEA数据（GPRMC + GPGGA）"""
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("串口未连接")
            return None
            
        logger.info(f"🔍 开始读取NMEA数据（超时: {self.timeout}秒）...")
        start_time = time.time()
        sentence_count = 0
        
        try:
            while time.time() - start_time < self.timeout:
                if self.serial_conn.in_waiting > 0:
                    try:
                        # 读取一行数据
                        line = self.serial_conn.readline()
                        text = line.decode('utf-8', errors='ignore').strip()
                        
                        if text:
                            sentence_count += 1
                            logger.debug(f"接收到NMEA语句 #{sentence_count}: {text[:50]}...")
                            
                            # 尝试匹配NMEA数据对
                            matched_pair = self.nmea_buffer.add_nmea_sentence(text)
                            
                            if matched_pair:
                                gprmc, gpgga = matched_pair
                                logger.info(f"✅ 成功匹配到NMEA数据对！")
                                logger.info(f"   GPRMC: {gprmc}")
                                logger.info(f"   GPGGA: {gpgga}")
                                return matched_pair
                                
                    except UnicodeDecodeError:
                        # 忽略解码错误
                        pass
                    except Exception as e:
                        logger.warning(f"数据读取异常: {e}")
                else:
                    time.sleep(0.01)  # 短暂休眠
                    
            logger.warning(f"⏰ 读取超时（{self.timeout}秒），未找到匹配的NMEA数据对")
            logger.info(f"📊 总共接收到 {sentence_count} 条NMEA语句")
            return None
            
        except KeyboardInterrupt:
            logger.info("用户中断读取")
            return None
        except Exception as e:
            logger.error(f"读取异常: {e}")
            return None
    
    def disconnect(self):
        """断开串口连接"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("✅ 串口已关闭")

class SnapshotGNSSSTAMP:
    """快照GNSS-STAMP处理系统"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.serial_reader = None
        self.stamp_processor = None
        self.transmitter = None
        
        # 从配置中获取串口参数
        self.port = config.get('serial_port', 'COM3')
        self.baudrate = config.get('serial_baudrate', 115200)
        self.timeout = config.get('read_timeout', 30.0)
        
    def initialize(self) -> bool:
        """初始化系统组件"""
        try:
            logger.info("🚀 初始化快照GNSS-STAMP系统")
            
            # 初始化STAMP处理器
            device_id = bytes.fromhex(self.config.get('device_id', 'DEADBEEFCAFEBABE'))
            link_id = self.config.get('link_id', 1024)
            sync_status = self.config.get('sync_status', 'beidouLocked')
            
            self.stamp_processor = STAMPProcessor(device_id, link_id, sync_status)
            logger.info("✅ STAMP处理器初始化完成")
            
            # 初始化网络传输器（用于文件输出）
            src_ip = self.config.get('src_ip', '2001:db8:1::1')
            dst_ip = self.config.get('dst_ip', '2001:db8:2::2')
            output_dir = self.config.get('output_dir', 'IGS-Data/STAMP-Snapshot')
            
            self.transmitter = NetworkTransmitter(src_ip, dst_ip, output_dir, self.config)
            logger.info("✅ 网络传输器初始化完成")
            
            # 初始化串口读取器
            self.serial_reader = SnapshotSerialReader(self.port, self.baudrate, self.timeout)
            
            # 检查可用串口
            available_ports = self.serial_reader.find_available_ports()
            if self.port not in available_ports:
                logger.warning(f"指定的串口 {self.port} 不在可用列表中")
                if available_ports:
                    logger.info(f"建议使用: {available_ports[0]}")
            
            # 连接串口
            if not self.serial_reader.connect():
                logger.error("串口连接失败")
                return False
                
            logger.info("✅ 串口连接成功")
            logger.info("🎯 系统初始化完成，准备获取快照数据")
            return True
            
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            return False
    
    def capture_snapshot(self) -> bool:
        """捕获当前时刻的GNSS数据快照"""
        if not self.initialize():
            return False
            
        logger.info("📸 开始捕获GNSS数据快照")
        logger.info("=" * 60)
        logger.info(f"串口: {self.port} @ {self.baudrate}")
        logger.info(f"设备ID: {self.config.get('device_id')}")
        logger.info(f"链路ID: {self.config.get('link_id')}")
        logger.info(f"同步状态: {self.config.get('sync_status')}")
        logger.info(f"读取超时: {self.timeout}秒")
        logger.info("=" * 60)
        
        try:
            # 读取单对NMEA数据
            nmea_pair = self.serial_reader.read_single_nmea_pair()
            
            if not nmea_pair:
                logger.error("❌ 未能获取到NMEA数据对")
                return False
                
            gprmc, gpgga = nmea_pair
            
            # 处理STAMP数据
            logger.info("🔄 开始STAMP编码...")
            stamp_payload = self.stamp_processor.process_nmea_data(gprmc, gpgga)
            
            if stamp_payload:
                # 保存编码结果
                success = self.transmitter.transmit_packet(stamp_payload)
                
                if success:
                    logger.info("✅ STAMP编码和保存成功！")
                    
                    # 显示结果信息
                    self.show_results()
                    return True
                else:
                    logger.error("❌ 数据保存失败")
                    return False
            else:
                logger.error("❌ STAMP编码失败")
                return False
                
        except KeyboardInterrupt:
            logger.info("用户中断操作")
            return False
        except Exception as e:
            logger.error(f"快照捕获异常: {e}")
            return False
        finally:
            # 清理资源
            if self.serial_reader:
                self.serial_reader.disconnect()
            
            # 完成输出
            if self.transmitter:
                self.transmitter.finalize_output()
    
    def show_results(self):
        """显示结果信息"""
        logger.info("=" * 60)
        logger.info("📊 快照结果")
        logger.info("=" * 60)
        
        if self.transmitter:
            logger.info(f"📁 输出目录: {self.transmitter.output_dir}")
            logger.info(f"📄 HEX文件: {os.path.basename(self.transmitter.hex_output_file)}")
            logger.info(f"📋 JSON文件: {os.path.basename(self.transmitter.json_output_file)}")
            
            # 显示文件大小
            try:
                hex_size = os.path.getsize(self.transmitter.hex_output_file)
                json_size = os.path.getsize(self.transmitter.json_output_file)
                logger.info(f"📏 文件大小: HEX={hex_size}字节, JSON={json_size}字节")
            except:
                pass
        
        if self.stamp_processor:
            stats = self.stamp_processor.get_statistics()
            logger.info(f"🎯 处理统计: 成功 {stats['processed_count']} 次")

def load_snapshot_config(config_file: str = 'snapshot_gnss_config.json') -> Dict:
    """加载快照处理配置"""
    default_config = {
        "serial_port": "COM3",
        "serial_baudrate": 115200,
        "read_timeout": 30.0,
        "device_id": "DEADBEEFCAFEBABE",
        "link_id": 1024,
        "sync_status": "beidouLocked",
        "src_ip": "2001:db8:1::1",
        "dst_ip": "2001:db8:2::2",
        "output_dir": "IGS-Data/STAMP-Snapshot",
        "log_level": "INFO"
    }
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            default_config.update(user_config)
            logger.info(f"配置文件加载成功: {config_file}")
        except Exception as e:
            logger.warning(f"配置文件加载失败，使用默认配置: {e}")
    else:
        # 创建默认配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        logger.info(f"已创建默认配置文件: {config_file}")
    
    return default_config

def main():
    """主函数"""
    print("📸 快照GNSS-STAMP处理系统")
    print("=" * 50)
    print("功能: 获取当前时刻的GPGGA和GPRMC数据，进行一次STAMP编码")
    print()
    
    # 加载配置
    config = load_snapshot_config()
    
    # 显示配置信息
    print(f"串口配置: {config['serial_port']} @ {config['serial_baudrate']}")
    print(f"设备ID: {config['device_id']}")
    print(f"读取超时: {config['read_timeout']}秒")
    print(f"输出目录: {config['output_dir']}")
    print()
    
    # 创建并启动快照系统
    snapshot_system = SnapshotGNSSSTAMP(config)
    
    try:
        success = snapshot_system.capture_snapshot()
        if success:
            logger.info("🎉 快照捕获完成！")
            print("\n✅ 快照处理成功完成")
            print("💡 提示: 查看输出目录中的HEX和JSON文件")
        else:
            logger.error("❌ 快照捕获失败")
            print("\n❌ 快照处理失败")
            sys.exit(1)
    except Exception as e:
        logger.error(f"系统运行异常: {e}")
        print(f"\n❌ 系统异常: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

