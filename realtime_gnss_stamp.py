#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时GNSS-STAMP系统
从串口读取GPGGA和GPRMC数据，实时进行STAMP编码
"""

import os
import sys
import time
import json
import threading
import queue
import serial
import serial.tools.list_ports
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Callable
import logging

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gnss_stamp_integration import STAMPProcessor, NetworkTransmitter, load_config
from stamp_improved import module_a_generate_stamp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('realtime_gnss_stamp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NMEABuffer:
    """NMEA数据缓冲器，用于匹配GPGGA和GPRMC数据对"""
    
    def __init__(self, max_age_seconds: float = 2.0):
        self.max_age_seconds = max_age_seconds
        self.gprmc_buffer = {}  # 时间戳 -> GPRMC数据
        self.gpgga_buffer = {}  # 时间戳 -> GPGGA数据
        self.lock = threading.Lock()
        
    def add_nmea_sentence(self, sentence: str) -> Optional[Tuple[str, str]]:
        """添加NMEA语句，如果找到匹配的对则返回"""
        try:
            sentence = sentence.strip()
            if not sentence:
                return None
                
            parts = sentence.split(',')
            if len(parts) < 2:
                return None
                
            sentence_type = parts[0]
            time_field = parts[1] if len(parts) > 1 else ""
            
            # 提取时间戳作为匹配键
            time_key = self._extract_time_key(time_field)
            if not time_key:
                return None
                
            with self.lock:
                current_time = time.time()
                
                # 清理过期数据
                self._cleanup_old_data(current_time)
                
                if sentence_type in ['$GPRMC', '$GNRMC']:
                    # 存储GPRMC数据
                    self.gprmc_buffer[time_key] = {
                        'sentence': sentence,
                        'timestamp': current_time
                    }
                    
                    # 查找匹配的GPGGA
                    if time_key in self.gpgga_buffer:
                        gpgga_data = self.gpgga_buffer.pop(time_key)
                        return sentence, gpgga_data['sentence']
                        
                elif sentence_type == '$GPGGA':
                    # 存储GPGGA数据
                    self.gpgga_buffer[time_key] = {
                        'sentence': sentence,
                        'timestamp': current_time
                    }
                    
                    # 查找匹配的GPRMC
                    if time_key in self.gprmc_buffer:
                        gprmc_data = self.gprmc_buffer.pop(time_key)
                        return gprmc_data['sentence'], sentence
                        
            return None
            
        except Exception as e:
            logger.warning(f"处理NMEA语句失败: {e}")
            return None
    
    def _extract_time_key(self, time_field: str) -> Optional[str]:
        """从时间字段提取匹配键"""
        try:
            if not time_field or len(time_field) < 6:
                return None
            # 使用时分秒作为匹配键，忽略毫秒部分的差异
            return time_field[:6]  # HHMMSS
        except:
            return None
    
    def _cleanup_old_data(self, current_time: float):
        """清理过期的缓冲数据"""
        cutoff_time = current_time - self.max_age_seconds
        
        # 清理GPRMC缓冲
        expired_keys = [k for k, v in self.gprmc_buffer.items() 
                       if v['timestamp'] < cutoff_time]
        for key in expired_keys:
            del self.gprmc_buffer[key]
            
        # 清理GPGGA缓冲
        expired_keys = [k for k, v in self.gpgga_buffer.items() 
                       if v['timestamp'] < cutoff_time]
        for key in expired_keys:
            del self.gpgga_buffer[key]

class RealtimeSerialReader:
    """实时串口数据读取器"""
    
    def __init__(self, port: str, baudrate: int = 115200, 
                 data_callback: Optional[Callable[[str, str], None]] = None):
        self.port = port
        self.baudrate = baudrate
        self.data_callback = data_callback
        self.serial_conn = None
        self.is_running = False
        self.nmea_buffer = NMEABuffer()
        self.stats = {
            'total_sentences': 0,
            'gprmc_count': 0,
            'gpgga_count': 0,
            'matched_pairs': 0,
            'errors': 0
        }
        
    def find_available_ports(self) -> List[str]:
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
    
    def start_reading(self):
        """开始读取数据"""
        if not self.serial_conn or not self.serial_conn.is_open:
            logger.error("串口未连接")
            return False
            
        self.is_running = True
        logger.info("🟢 开始读取NMEA数据...")
        
        try:
            while self.is_running:
                if self.serial_conn.in_waiting > 0:
                    try:
                        # 读取一行数据
                        line = self.serial_conn.readline()
                        text = line.decode('utf-8', errors='ignore').strip()
                        
                        if text:
                            self.stats['total_sentences'] += 1
                            
                            # 统计不同类型的NMEA语句
                            if text.startswith('$GPRMC') or text.startswith('$GNRMC'):
                                self.stats['gprmc_count'] += 1
                            elif text.startswith('$GPGGA'):
                                self.stats['gpgga_count'] += 1
                            
                            # 尝试匹配NMEA数据对
                            matched_pair = self.nmea_buffer.add_nmea_sentence(text)
                            
                            if matched_pair:
                                self.stats['matched_pairs'] += 1
                                gprmc, gpgga = matched_pair
                                
                                logger.info(f"📍 匹配到NMEA数据对 #{self.stats['matched_pairs']}")
                                logger.debug(f"GPRMC: {gprmc}")
                                logger.debug(f"GPGGA: {gpgga}")
                                
                                # 调用回调函数处理数据
                                if self.data_callback:
                                    try:
                                        self.data_callback(gprmc, gpgga)
                                    except Exception as e:
                                        logger.error(f"数据回调处理失败: {e}")
                                        self.stats['errors'] += 1
                                        
                    except UnicodeDecodeError:
                        # 忽略解码错误
                        pass
                    except Exception as e:
                        logger.warning(f"数据读取异常: {e}")
                        self.stats['errors'] += 1
                else:
                    time.sleep(0.01)  # 短暂休眠避免CPU占用过高
                    
        except KeyboardInterrupt:
            logger.info("接收到停止信号")
        except Exception as e:
            logger.error(f"读取线程异常: {e}")
        finally:
            self.is_running = False
            
        return True
    
    def stop_reading(self):
        """停止读取数据"""
        logger.info("🛑 停止读取数据...")
        self.is_running = False
        
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info("✅ 串口已关闭")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()

class RealtimeGNSSSTAMP:
    """实时GNSS-STAMP处理系统"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.serial_reader = None
        self.stamp_processor = None
        self.transmitter = None
        self.is_running = False
        
        # 从配置中获取串口参数
        self.port = config.get('serial_port', 'COM3')
        self.baudrate = config.get('serial_baudrate', 115200)
        
    def initialize(self) -> bool:
        """初始化系统组件"""
        try:
            logger.info("🚀 初始化实时GNSS-STAMP系统")
            
            # 初始化STAMP处理器
            device_id = bytes.fromhex(self.config.get('device_id', 'DEADBEEFCAFEBABE'))
            link_id = self.config.get('link_id', 1024)
            sync_status = self.config.get('sync_status', 'beidouLocked')
            
            self.stamp_processor = STAMPProcessor(device_id, link_id, sync_status)
            logger.info("✅ STAMP处理器初始化完成")
            
            # 初始化网络传输器
            src_ip = self.config.get('src_ip', '2001:db8:1::1')
            dst_ip = self.config.get('dst_ip', '2001:db8:2::2')
            output_dir = self.config.get('output_dir', 'IGS-Data/STAMP-Realtime')
            
            self.transmitter = NetworkTransmitter(src_ip, dst_ip, output_dir, self.config)
            self.transmitter.start_transmission_thread()
            logger.info("✅ 网络传输器初始化完成")
            
            # 初始化串口读取器
            self.serial_reader = RealtimeSerialReader(
                self.port, self.baudrate, self._process_nmea_pair
            )
            
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
            logger.info("🎯 系统初始化完成，准备开始实时处理")
            return True
            
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            return False
    
    def _process_nmea_pair(self, gprmc: str, gpgga: str):
        """处理NMEA数据对的回调函数"""
        try:
            # 使用STAMP处理器编码数据
            stamp_payload = self.stamp_processor.process_nmea_data(gprmc, gpgga)
            
            if stamp_payload:
                # 将编码结果加入传输队列
                self.transmitter.enqueue_stamp_packet(stamp_payload)
                logger.info(f"✅ STAMP编码成功，已加入传输队列")
            else:
                logger.warning("❌ STAMP编码失败")
                
        except Exception as e:
            logger.error(f"NMEA数据处理异常: {e}")
    
    def start_realtime_processing(self):
        """开始实时处理"""
        if not self.initialize():
            return False
            
        logger.info("🚀 开始实时GNSS-STAMP处理")
        logger.info("=" * 60)
        logger.info(f"串口: {self.port} @ {self.baudrate}")
        logger.info(f"设备ID: {self.config.get('device_id')}")
        logger.info(f"链路ID: {self.config.get('link_id')}")
        logger.info(f"同步状态: {self.config.get('sync_status')}")
        logger.info("=" * 60)
        logger.info("按 Ctrl+C 停止处理")
        
        self.is_running = True
        
        try:
            # 启动数据读取（阻塞运行）
            self.serial_reader.start_reading()
            
        except KeyboardInterrupt:
            logger.info("接收到停止信号")
        finally:
            self.stop_processing()
            
        return True
    
    def stop_processing(self):
        """停止处理"""
        logger.info("🛑 停止实时处理...")
        self.is_running = False
        
        if self.serial_reader:
            self.serial_reader.stop_reading()
            
        # 等待传输完成
        time.sleep(2)
        
        # 保存编码结果
        if self.transmitter:
            self.transmitter.finalize_output()
            
        # 显示统计信息
        self.show_statistics()
        
        logger.info("👋 实时处理已停止")
    
    def show_statistics(self):
        """显示统计信息"""
        logger.info("=" * 60)
        logger.info("📊 实时处理统计信息")
        logger.info("=" * 60)
        
        if self.serial_reader:
            serial_stats = self.serial_reader.get_statistics()
            logger.info(f"串口数据: 总计 {serial_stats['total_sentences']} 条NMEA语句")
            logger.info(f"  GPRMC: {serial_stats['gprmc_count']} 条")
            logger.info(f"  GPGGA: {serial_stats['gpgga_count']} 条")
            logger.info(f"  匹配对: {serial_stats['matched_pairs']} 对")
            logger.info(f"  错误: {serial_stats['errors']} 次")
            
        if self.stamp_processor:
            stamp_stats = self.stamp_processor.get_statistics()
            logger.info(f"STAMP处理: 成功 {stamp_stats['processed_count']} 次, "
                       f"失败 {stamp_stats['error_count']} 次, "
                       f"成功率 {stamp_stats['success_rate']:.1f}%")
            
        if self.transmitter:
            logger.info(f"网络传输: {self.transmitter.transmitted_count} 个数据包")

def load_realtime_config(config_file: str = 'realtime_gnss_config.json') -> Dict:
    """加载实时处理配置"""
    default_config = {
        "serial_port": "COM3",
        "serial_baudrate": 115200,
        "device_id": "DEADBEEFCAFEBABE",
        "link_id": 1024,
        "sync_status": "beidouLocked",
        "src_ip": "2001:db8:1::1",
        "dst_ip": "2001:db8:2::2",
        "output_dir": "IGS-Data/STAMP-Realtime",
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
    print("🛰️  实时GNSS-STAMP处理系统")
    print("=" * 50)
    
    # 加载配置
    config = load_realtime_config()
    
    # 显示配置信息
    print(f"串口配置: {config['serial_port']} @ {config['serial_baudrate']}")
    print(f"设备ID: {config['device_id']}")
    print(f"输出目录: {config['output_dir']}")
    print()
    
    # 创建并启动实时处理系统
    realtime_system = RealtimeGNSSSTAMP(config)
    
    try:
        success = realtime_system.start_realtime_processing()
        if success:
            logger.info("✅ 实时处理完成")
        else:
            logger.error("❌ 实时处理失败")
            sys.exit(1)
    except Exception as e:
        logger.error(f"系统运行异常: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
