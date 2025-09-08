#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GNSS-STAMP集成系统
将GNSS定位数据实时转换为STAMP协议格式并传输
"""

import os
import sys
import time
import json
import threading
import queue
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# 导入STAMP模块
from stamp_improved import (
    module_a_generate_stamp, 
    module_b_process_ipv6_packet,
    _simulate_network_encapsulation
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gnss_stamp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NMEADataReader:
    """NMEA数据读取器"""
    
    def __init__(self, pos_file_path: str):
        self.pos_file_path = pos_file_path
        self.current_line = 0
        self.total_lines = 0
        self._count_lines()
        
    def _count_lines(self):
        """统计文件总行数"""
        try:
            with open(self.pos_file_path, 'r', encoding='utf-8') as f:
                self.total_lines = sum(1 for _ in f)
            logger.info(f"NMEA文件总行数: {self.total_lines}")
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            self.total_lines = 0
    
    def read_next_nmea_pair(self) -> Optional[Tuple[str, str]]:
        """读取下一对GPGGA和GPRMC数据"""
        try:
            with open(self.pos_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # 查找当前行之后的GPRMC和GPGGA对
            for i in range(self.current_line, len(lines)):
                line = lines[i].strip()
                if line.startswith('$GPRMC'):
                    # 查找对应的GPGGA
                    for j in range(i + 1, min(i + 3, len(lines))):
                        gga_line = lines[j].strip()
                        if gga_line.startswith('$GPGGA'):
                            self.current_line = j + 1
                            return line, gga_line
                            
            return None  # 没有更多数据
            
        except Exception as e:
            logger.error(f"读取NMEA数据失败: {e}")
            return None
    
    def get_progress(self) -> float:
        """获取读取进度"""
        if self.total_lines == 0:
            return 0.0
        return (self.current_line / self.total_lines) * 100

class STAMPProcessor:
    """STAMP数据处理器"""
    
    def __init__(self, device_id: bytes, link_id: int, sync_status: str = 'beidouLocked'):
        self.device_id = device_id
        self.link_id = link_id
        self.sync_status = sync_status
        self.processed_count = 0
        self.error_count = 0
        
    def process_nmea_data(self, gnrmc: str, gpgga: str) -> Optional[bytes]:
        """处理NMEA数据并生成STAMP报文"""
        try:
            stamp_payload = module_a_generate_stamp(
                gpgga, gnrmc, self.device_id, self.link_id, self.sync_status
            )
            
            if stamp_payload:
                self.processed_count += 1
                logger.info(f"STAMP处理成功 #{self.processed_count}")
                return stamp_payload
            else:
                self.error_count += 1
                logger.warning(f"STAMP处理失败 #{self.error_count}")
                return None
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"STAMP处理异常: {e}")
            return None
    
    def get_statistics(self) -> Dict:
        """获取处理统计信息"""
        total = self.processed_count + self.error_count
        success_rate = (self.processed_count / total * 100) if total > 0 else 0
        
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'success_rate': success_rate
        }

class NetworkTransmitter:
    """网络传输器"""
    
    def __init__(self, src_ip: str, dst_ip: str, output_dir: str = "IGS-Data/STAMP-Output"):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.transmitted_count = 0
        self.transmission_queue = queue.Queue(maxsize=1000)
        self.output_dir = output_dir
        self.encoded_results = []  # 存储编码结果
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 创建输出文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.hex_output_file = os.path.join(self.output_dir, f"stamp_encoded_{timestamp}.hex")
        self.json_output_file = os.path.join(self.output_dir, f"stamp_results_{timestamp}.json")
        self.binary_output_file = os.path.join(self.output_dir, f"stamp_binary_{timestamp}.bin")
        
        logger.info(f"输出文件将保存到: {self.output_dir}")
        logger.info(f"HEX文件: {self.hex_output_file}")
        logger.info(f"JSON文件: {self.json_output_file}")
        logger.info(f"二进制文件: {self.binary_output_file}")
        
    def enqueue_stamp_packet(self, stamp_payload: bytes):
        """将STAMP数据包加入传输队列"""
        try:
            self.transmission_queue.put_nowait(stamp_payload)
        except queue.Full:
            logger.warning("传输队列已满，丢弃数据包")
    
    def transmit_packet(self, stamp_payload: bytes) -> bool:
        """传输单个STAMP数据包并保存编码结果"""
        try:
            # 封装为IPv6数据包
            ipv6_packet = _simulate_network_encapsulation(
                stamp_payload, self.src_ip, self.dst_ip
            )
            
            # 保存编码结果
            self._save_encoded_result(stamp_payload)
            
            # 这里可以添加实际的网络传输代码
            # 例如：socket.sendto(ipv6_packet, (dst_ip, port))
            
            self.transmitted_count += 1
            logger.info(f"数据包传输成功 #{self.transmitted_count}")
            return True
            
        except Exception as e:
            logger.error(f"数据包传输失败: {e}")
            return False
    
    def _save_encoded_result(self, stamp_payload: bytes):
        """保存单个编码结果"""
        try:
            # 记录编码结果
            result_info = {
                'sequence': self.transmitted_count + 1,
                'timestamp': datetime.now().isoformat(),
                'payload_length': len(stamp_payload),
                'payload_hex': stamp_payload.hex().upper(),
                'src_ip': self.src_ip,
                'dst_ip': self.dst_ip
            }
            
            self.encoded_results.append(result_info)
            
            # 实时写入HEX文件（方便实时查看）
            with open(self.hex_output_file, 'a', encoding='utf-8') as f:
                f.write(f"#{self.transmitted_count + 1} [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                       f"长度={len(stamp_payload)}字节\n")
                f.write(f"{stamp_payload.hex().upper()}\n\n")
            
            # 实时写入二进制文件
            with open(self.binary_output_file, 'ab') as f:
                # 写入长度信息（4字节）和数据
                f.write(len(stamp_payload).to_bytes(4, 'big'))
                f.write(stamp_payload)
                
        except Exception as e:
            logger.error(f"保存编码结果失败: {e}")
    
    def finalize_output(self):
        """完成处理后保存完整的JSON结果文件"""
        try:
            # 准备完整的输出数据
            output_data = {
                'metadata': {
                    'total_packets': len(self.encoded_results),
                    'generation_time': datetime.now().isoformat(),
                    'src_ip': self.src_ip,
                    'dst_ip': self.dst_ip,
                    'output_directory': self.output_dir
                },
                'packets': self.encoded_results,
                'statistics': {
                    'total_bytes': sum(result['payload_length'] for result in self.encoded_results),
                    'average_packet_size': sum(result['payload_length'] for result in self.encoded_results) / len(self.encoded_results) if self.encoded_results else 0,
                    'min_packet_size': min(result['payload_length'] for result in self.encoded_results) if self.encoded_results else 0,
                    'max_packet_size': max(result['payload_length'] for result in self.encoded_results) if self.encoded_results else 0
                }
            }
            
            # 保存JSON文件
            with open(self.json_output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ STAMP编码结果已保存:")
            logger.info(f"   📁 输出目录: {self.output_dir}")
            logger.info(f"   📄 HEX文件: {os.path.basename(self.hex_output_file)} ({len(self.encoded_results)} 个数据包)")
            logger.info(f"   📋 JSON文件: {os.path.basename(self.json_output_file)} (包含元数据和统计信息)")
            logger.info(f"   🗃️  二进制文件: {os.path.basename(self.binary_output_file)} ({sum(result['payload_length'] for result in self.encoded_results)} 字节)")
            
        except Exception as e:
            logger.error(f"保存最终结果失败: {e}")
    
    def start_transmission_thread(self):
        """启动传输线程"""
        def transmission_worker():
            while True:
                try:
                    stamp_payload = self.transmission_queue.get(timeout=1.0)
                    self.transmit_packet(stamp_payload)
                    self.transmission_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"传输线程异常: {e}")
        
        thread = threading.Thread(target=transmission_worker, daemon=True)
        thread.start()
        logger.info("网络传输线程已启动")

class GNSSSTAMPIntegration:
    """GNSS-STAMP集成主控制器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.is_running = False
        self.reader = None
        self.processor = None
        self.transmitter = None
        
    def initialize(self):
        """初始化系统组件"""
        try:
            # 初始化NMEA读取器
            pos_file = self.config.get('pos_file_path')
            if not pos_file or not os.path.exists(pos_file):
                raise FileNotFoundError(f"POS文件不存在: {pos_file}")
            
            self.reader = NMEADataReader(pos_file)
            
            # 初始化STAMP处理器
            device_id = bytes.fromhex(self.config.get('device_id', 'DEADBEEFCAFEBABE'))
            link_id = self.config.get('link_id', 1024)
            sync_status = self.config.get('sync_status', 'beidouLocked')
            
            self.processor = STAMPProcessor(device_id, link_id, sync_status)
            
            # 初始化网络传输器
            src_ip = self.config.get('src_ip', '2001:db8:1::1')
            dst_ip = self.config.get('dst_ip', '2001:db8:2::2')
            
            self.transmitter = NetworkTransmitter(src_ip, dst_ip)
            self.transmitter.start_transmission_thread()
            
            logger.info("系统初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            return False
    
    def run_single_processing(self):
        """单次处理模式"""
        logger.info("开始单次处理模式")
        
        if not self.initialize():
            return False
        
        # 读取并处理所有NMEA数据
        while True:
            nmea_pair = self.reader.read_next_nmea_pair()
            if not nmea_pair:
                break
                
            gnrmc, gpgga = nmea_pair
            
            # 处理STAMP数据
            stamp_payload = self.processor.process_nmea_data(gnrmc, gpgga)
            if stamp_payload:
                # 传输数据包
                self.transmitter.enqueue_stamp_packet(stamp_payload)
            
            # 显示进度
            progress = self.reader.get_progress()
            if int(progress) % 10 == 0:  # 每10%显示一次进度
                logger.info(f"处理进度: {progress:.1f}%")
        
        # 等待传输完成
        time.sleep(2)
        
        # 保存编码结果到文件
        if self.transmitter:
            self.transmitter.finalize_output()
        
        # 显示统计信息
        self.show_statistics()
        return True
    
    def run_realtime_processing(self, interval: float = 1.0):
        """实时处理模式"""
        logger.info(f"开始实时处理模式，间隔: {interval}秒")
        
        if not self.initialize():
            return False
        
        self.is_running = True
        
        try:
            while self.is_running:
                nmea_pair = self.reader.read_next_nmea_pair()
                if nmea_pair:
                    gnrmc, gpgga = nmea_pair
                    
                    # 处理STAMP数据
                    stamp_payload = self.processor.process_nmea_data(gnrmc, gpgga)
                    if stamp_payload:
                        # 传输数据包
                        self.transmitter.enqueue_stamp_packet(stamp_payload)
                else:
                    logger.info("NMEA数据读取完毕，等待新数据...")
                    time.sleep(interval)
                    continue
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("接收到停止信号")
        finally:
            self.is_running = False
            # 保存编码结果到文件
            if self.transmitter:
                self.transmitter.finalize_output()
            self.show_statistics()
        
        return True
    
    def show_statistics(self):
        """显示统计信息"""
        logger.info("=" * 50)
        logger.info("处理统计信息")
        logger.info("=" * 50)
        
        if self.reader:
            logger.info(f"数据读取进度: {self.reader.get_progress():.1f}%")
        
        if self.processor:
            stats = self.processor.get_statistics()
            logger.info(f"STAMP处理: 成功 {stats['processed_count']} 次, "
                       f"失败 {stats['error_count']} 次, "
                       f"成功率 {stats['success_rate']:.1f}%")
        
        if self.transmitter:
            logger.info(f"网络传输: {self.transmitter.transmitted_count} 个数据包")

def load_config(config_file: str = 'gnss_stamp_config.json') -> Dict:
    """加载配置文件"""
    default_config = {
        "pos_file_path": "IGS-Data/JBDH/2025/121/JBDH_2025_121_WUH2_B_D.pos",
        "device_id": "DEADBEEFCAFEBABE",
        "link_id": 1024,
        "sync_status": "beidouLocked",
        "src_ip": "2001:db8:1::1",
        "dst_ip": "2001:db8:2::2",
        "processing_mode": "single",  # single 或 realtime
        "realtime_interval": 1.0
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
    logger.info("GNSS-STAMP集成系统启动")
    
    # 加载配置
    config = load_config()
    
    # 创建集成系统
    integration = GNSSSTAMPIntegration(config)
    
    # 根据配置选择处理模式
    processing_mode = config.get('processing_mode', 'single')
    
    if processing_mode == 'realtime':
        interval = config.get('realtime_interval', 1.0)
        success = integration.run_realtime_processing(interval)
    else:
        success = integration.run_single_processing()
    
    if success:
        logger.info("系统运行完成")
    else:
        logger.error("系统运行失败")
        sys.exit(1)

if __name__ == '__main__':
    main()
