#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STAMP解码器模块
功能：解码STAMP报文、校验CRC、生成JSON输出
"""

import json
import argparse
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# 导入STAMP相关模块
from stamp_improved import (
    SpatioTemporalPacket, 
    decode_stamp_packet,
    der_decoder,
    der_encoder,
    Calculator,
    Configuration
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StampDecoder:
    """STAMP解码器类"""
    
    def __init__(self, output_dir: str = "STAMP-Decoded"):
        """初始化解码器"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.statistics = {
            'total_packets': 0,
            'successful_decodes': 0,
            'crc_failures': 0,
            'format_errors': 0,
            'other_errors': 0,
            'success_rate': 0.0
        }
        self.decoded_data = []
        self.source_file_info = {}
        
        # 设置日志处理器
        self.log_handler = None
    
    def _setup_log_file(self, source_file_path: str) -> str:
        """为解码任务设置专门的日志文件"""
        source_file = Path(source_file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"decode_{source_file.stem}_{timestamp}.log"
        log_file_path = self.output_dir / log_filename
        
        # 移除之前的日志处理器
        if self.log_handler:
            logger.removeHandler(self.log_handler)
        
        # 创建新的文件处理器
        self.log_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        self.log_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        logger.addHandler(self.log_handler)
        
        return str(log_file_path)
    
    def _cleanup_log_handler(self):
        """清理日志处理器"""
        if self.log_handler:
            logger.removeHandler(self.log_handler)
            self.log_handler.close()
            self.log_handler = None
        
    def decode_from_hex_file(self, hex_file_path: str, verbose: bool = False) -> str:
        """从HEX文件解码STAMP数据，返回日志文件路径"""
        try:
            hex_file = Path(hex_file_path)
            if not hex_file.exists():
                logger.error(f"HEX文件不存在: {hex_file_path}")
                return ""
                
            # 设置专门的日志文件
            log_file_path = self._setup_log_file(hex_file_path)
            
            # 记录源文件信息
            file_stats = hex_file.stat()
            self.source_file_info = {
                'source_file': str(hex_file.absolute()),
                'file_type': 'hex',
                'file_size': file_stats.st_size,
                'file_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                'decode_timestamp': datetime.now().isoformat(),
                'log_file': log_file_path
            }
            
            logger.info(f"开始从HEX文件解码: {hex_file_path}")
            logger.info(f"源文件大小: {file_stats.st_size} 字节")
            logger.info(f"日志文件: {log_file_path}")
            
            with open(hex_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 统计文件内容
            hex_data_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and all(c in '0123456789ABCDEFabcdef' for c in line):
                    hex_data_lines.append(line)
            
            self.statistics['total_packets'] = len(hex_data_lines)
            logger.info(f"发现 {self.statistics['total_packets']} 个HEX数据包")
            
            if verbose:
                print(f"\n🔍 开始逐包解码 (总计: {self.statistics['total_packets']} 包)")
                print("=" * 80)
            
            # 逐个解码数据包
            for i, hex_line in enumerate(hex_data_lines):
                try:
                    # 转换HEX到字节
                    packet_bytes = bytes.fromhex(hex_line)
                    
                    if verbose:
                        print(f"\n📦 数据包 #{i+1:4d}/{self.statistics['total_packets']}")
                        print(f"   原始HEX: {hex_line[:60]}{'...' if len(hex_line) > 60 else ''}")
                        print(f"   数据长度: {len(packet_bytes)} 字节")
                    
                    # 解码单个数据包
                    decoded_result = self._decode_single_packet(packet_bytes, i + 1, verbose)
                    
                    if decoded_result:
                        self.decoded_data.append(decoded_result)
                        self.statistics['successful_decodes'] += 1
                        
                        if verbose:
                            self._print_decoded_packet_info(decoded_result)
                            print(f"   ✅ 解码成功")
                    else:
                        if verbose:
                            print(f"   ❌ 解码失败")
                        
                except Exception as e:
                    logger.error(f"处理第 {i+1} 行HEX数据时出错: {e}")
                    self.statistics['other_errors'] += 1
                    if verbose:
                        print(f"   ❌ 处理异常: {e}")
                
                # 显示进度
                if verbose and (i + 1) % 100 == 0:
                    current_success_rate = (self.statistics['successful_decodes'] / (i + 1) * 100)
                    print(f"\n📊 进度报告: {i+1}/{self.statistics['total_packets']} "
                          f"(成功率: {current_success_rate:.1f}%)")
            
            # 计算成功率
            if self.statistics['total_packets'] > 0:
                self.statistics['success_rate'] = (
                    self.statistics['successful_decodes'] / self.statistics['total_packets'] * 100
                )
            
            if verbose:
                print("\n" + "=" * 80)
                print(f"🎯 解码完成总结:")
                print(f"   总数据包: {self.statistics['total_packets']}")
                print(f"   成功解码: {self.statistics['successful_decodes']}")
                print(f"   CRC错误: {self.statistics['crc_failures']}")
                print(f"   格式错误: {self.statistics['format_errors']}")
                print(f"   其他错误: {self.statistics['other_errors']}")
                print(f"   成功率: {self.statistics['success_rate']:.1f}%")
            
            logger.info(f"解码完成: 成功 {self.statistics['successful_decodes']}/{self.statistics['total_packets']} "
                       f"({self.statistics['success_rate']:.1f}%)")
            
            # 记录详细统计信息
            logger.info(f"CRC错误: {self.statistics['crc_failures']}")
            logger.info(f"格式错误: {self.statistics['format_errors']}")
            logger.info(f"其他错误: {self.statistics['other_errors']}")
            
            return log_file_path
            
        except Exception as e:
            logger.error(f"从HEX文件解码失败: {e}")
            return ""
        finally:
            self._cleanup_log_handler()
    
    def decode_from_binary_file(self, binary_file_path: str) -> str:
        """从二进制文件解码STAMP数据，返回日志文件路径"""
        try:
            binary_file = Path(binary_file_path)
            if not binary_file.exists():
                logger.error(f"二进制文件不存在: {binary_file_path}")
                return ""
                
            # 设置专门的日志文件
            log_file_path = self._setup_log_file(binary_file_path)
            
            # 记录源文件信息
            file_stats = binary_file.stat()
            self.source_file_info = {
                'source_file': str(binary_file.absolute()),
                'file_type': 'binary',
                'file_size': file_stats.st_size,
                'file_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                'decode_timestamp': datetime.now().isoformat(),
                'log_file': log_file_path
            }
            
            logger.info(f"开始从二进制文件解码: {binary_file_path}")
            logger.info(f"源文件大小: {file_stats.st_size} 字节")
            logger.info(f"日志文件: {log_file_path}")
            
            with open(binary_file, 'rb') as f:
                data = f.read()
            
            logger.info(f"读取二进制数据: {len(data)} 字节")
            
            # 尝试解码整个文件作为单个数据包
            decoded_result = self._decode_single_packet(data, 1)
            
            if decoded_result:
                self.decoded_data.append(decoded_result)
                self.statistics['total_packets'] = 1
                self.statistics['successful_decodes'] = 1
                self.statistics['success_rate'] = 100.0
                logger.info("二进制文件解码成功")
                return log_file_path
            else:
                self.statistics['total_packets'] = 1
                self.statistics['success_rate'] = 0.0
                logger.error("二进制文件解码失败")
                return ""
                
        except Exception as e:
            logger.error(f"从二进制文件解码失败: {e}")
            return ""
        finally:
            self._cleanup_log_handler()
    
    def _decode_single_packet(self, packet_bytes: bytes, packet_index: int, verbose: bool = False) -> Optional[Dict[str, Any]]:
        """解码单个STAMP数据包"""
        try:
            # 尝试ASN.1 DER解码
            try:
                decoded_packet, _ = der_decoder.decode(packet_bytes, asn1Spec=SpatioTemporalPacket())
            except Exception as asn1_error:
                logger.error(f"数据包 {packet_index} ASN.1解码失败: {asn1_error}")
                self.statistics['format_errors'] += 1
                return None
            
            # 提取接收到的CRC
            received_crc_bytes = bytes(decoded_packet['crc'])
            
            # 重新计算CRC进行校验
            packet_for_crc_check = SpatioTemporalPacket()
            for field_name in ['version', 'timestamp_sec', 'timestamp_nsec', 'latitude', 
                              'longitude', 'altitude', 'device_id', 'link_id', 'sync_status']:
                packet_for_crc_check[field_name] = decoded_packet[field_name]
            packet_for_crc_check['crc'] = b'\x00\x00'
            
            # 计算CRC
            data_for_crc = der_encoder.encode(packet_for_crc_check)
            crc_config = Configuration(
                width=16, 
                polynomial=0x1021, 
                init_value=0xFFFF, 
                final_xor_value=0x0000, 
                reverse_input=False, 
                reverse_output=False
            )
            calculated_crc_bytes = Calculator(crc_config).checksum(data_for_crc).to_bytes(2, 'big')
            
            # CRC校验
            if received_crc_bytes != calculated_crc_bytes:
                logger.error(f"数据包 {packet_index} CRC校验失败: "
                           f"接收={received_crc_bytes.hex().upper()}, "
                           f"计算={calculated_crc_bytes.hex().upper()}")
                self.statistics['crc_failures'] += 1
                return None
            
            # 构建解码结果
            result = {
                'packet_index': packet_index,
                'version': int(decoded_packet['version']),
                'timestamp': {
                    'timestamp_sec': int(decoded_packet['timestamp_sec']),
                    'timestamp_nsec': int(decoded_packet['timestamp_nsec']),
                    'datetime_utc': self._convert_timestamp_to_datetime(
                        int(decoded_packet['timestamp_sec']), 
                        int(decoded_packet['timestamp_nsec'])
                    )
                },
                'position': {
                    'latitude': float(decoded_packet['latitude']),
                    'longitude': float(decoded_packet['longitude']),
                    'altitude': float(decoded_packet['altitude'])
                },
                'device_info': {
                    'device_id': bytes(decoded_packet['device_id']).hex().upper(),
                    'link_id': int(decoded_packet['link_id'])
                },
                'sync_info': {
                    'sync_status': int(decoded_packet['sync_status']),
                    'sync_status_name': self._convert_sync_status_to_name(int(decoded_packet['sync_status']))
                },
                'validation': {
                    'crc': received_crc_bytes.hex().upper(),
                    'crc_valid': True
                }
            }
            
            logger.debug(f"数据包 {packet_index} 解码成功，CRC校验通过")
            return result
            
        except Exception as e:
            logger.error(f"数据包 {packet_index} 解码时出现未知错误: {e}")
            self.statistics['other_errors'] += 1
            return None
    
    def _convert_timestamp_to_datetime(self, timestamp_sec: int, timestamp_nsec: int) -> str:
        """将时间戳转换为可读的日期时间格式"""
        try:
            # 创建UTC datetime对象
            dt = datetime.fromtimestamp(timestamp_sec, tz=timezone.utc)
            # 添加纳秒精度（转换为微秒）
            microseconds = timestamp_nsec // 1000
            dt = dt.replace(microsecond=microseconds)
            return dt.isoformat()
        except Exception as e:
            logger.warning(f"时间戳转换失败: {e}")
            return f"INVALID_TIMESTAMP({timestamp_sec}.{timestamp_nsec:09d})"
    
    def _convert_sync_status_to_name(self, sync_status: int) -> str:
        """将同步状态码转换为名称"""
        sync_status_map = {
            0: 'unknown',
            1: 'gpsLocked',
            2: 'beidouLocked',
            3: 'ppsStable',
            4: 'ppsUnstable',
            5: 'softwareSync'
        }
        return sync_status_map.get(sync_status, f'UNKNOWN_STATUS({sync_status})')
    
    def _print_decoded_packet_info(self, decoded_result: Dict[str, Any]) -> None:
        """打印解码后的数据包详细信息"""
        try:
            print(f"   📍 位置信息:")
            print(f"      纬度: {decoded_result['position']['latitude']:.8f}°")
            print(f"      经度: {decoded_result['position']['longitude']:.8f}°")
            print(f"      高度: {decoded_result['position']['altitude']:.3f}m")
            
            print(f"   ⏰ 时间信息:")
            print(f"      时间戳: {decoded_result['timestamp']['timestamp_sec']}.{decoded_result['timestamp']['timestamp_nsec']:09d}")
            print(f"      UTC时间: {decoded_result['timestamp']['datetime_utc']}")
            
            print(f"   🔧 设备信息:")
            print(f"      设备ID: {decoded_result['device_info']['device_id']}")
            print(f"      链路ID: {decoded_result['device_info']['link_id']}")
            
            print(f"   🔄 同步信息:")
            print(f"      同步状态: {decoded_result['sync_info']['sync_status']} ({decoded_result['sync_info']['sync_status_name']})")
            
            print(f"   ✅ 校验信息:")
            print(f"      CRC: {decoded_result['validation']['crc']}")
            print(f"      版本: {decoded_result['version']}")
            
        except Exception as e:
            print(f"   ⚠️  显示详情时出错: {e}")
    
    def export_to_json(self, source_file_path: str, verbose: bool = False) -> str:
        """导出解码结果到JSON文件，返回输出文件路径"""
        try:
            # 生成输出文件名
            source_file = Path(source_file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"decoded_{source_file.stem}_{timestamp}.json"
            output_path = self.output_dir / json_filename
            
            # 构建输出数据结构
            output_data = {
                'metadata': {
                    'decoder_version': '2.0.0',
                    'decode_timestamp': datetime.now(timezone.utc).isoformat(),
                    'source_file_info': self.source_file_info,
                    'statistics': self.statistics
                },
                'decoded_packets': self.decoded_data
            }
            
            # 写入JSON文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"解码结果已导出到: {output_path}")
            
            if verbose:
                print(f"\n📊 解码统计:")
                print(f"   源文件: {self.source_file_info.get('source_file', 'N/A')}")
                print(f"   文件类型: {self.source_file_info.get('file_type', 'N/A')}")
                print(f"   总数据包: {self.statistics['total_packets']}")
                print(f"   成功解码: {self.statistics['successful_decodes']}")
                print(f"   CRC错误: {self.statistics['crc_failures']}")
                print(f"   格式错误: {self.statistics['format_errors']}")
                print(f"   其他错误: {self.statistics['other_errors']}")
                print(f"   成功率: {self.statistics['success_rate']:.1f}%")
                print(f"\n💾 输出目录: {self.output_dir}")
                print(f"📄 JSON文件: {output_path}")
                print(f"📋 日志文件: {self.source_file_info.get('log_file', 'N/A')}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"导出JSON失败: {e}")
            return ""
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取解码统计信息"""
        return self.statistics.copy()
    
    def get_decoded_data(self) -> List[Dict[str, Any]]:
        """获取解码后的数据"""
        return self.decoded_data.copy()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='STAMP解码器 - 解码STAMP报文并校验CRC',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 从HEX文件解码（自动生成输出文件）
  python stamp_decoder.py input.hex
  
  # 从二进制文件解码
  python stamp_decoder.py input.bin -t binary
  
  # 指定输出目录
  python stamp_decoder.py input.hex -d my_output_dir
  
  # 详细输出模式
  python stamp_decoder.py input.hex -v
        """
    )
    
    parser.add_argument(
        'input_file',
        help='输入文件路径 (HEX或二进制文件)'
    )
    
    parser.add_argument(
        '-d', '--output-dir',
        default='STAMP-Decoded',
        help='输出目录 (默认: STAMP-Decoded)'
    )
    
    parser.add_argument(
        '-t', '--type',
        choices=['hex', 'binary'],
        default='hex',
        help='输入文件类型 (默认: hex)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细输出模式'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试日志'
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)
    
    # 创建解码器
    decoder = StampDecoder(args.output_dir)
    
    print(f"🚀 STAMP解码器启动")
    print(f"📁 输入文件: {args.input_file}")
    print(f"📄 文件类型: {args.type}")
    print(f"📂 输出目录: {args.output_dir}")
    
    # 执行解码
    log_file_path = ""
    if args.type == 'hex':
        log_file_path = decoder.decode_from_hex_file(args.input_file, args.verbose)
    elif args.type == 'binary':
        log_file_path = decoder.decode_from_binary_file(args.input_file)
    
    if log_file_path:
        # 导出结果
        json_file_path = decoder.export_to_json(args.input_file, args.verbose)
        if json_file_path:
            print(f"\n✅ 解码完成！")
            
            if not args.verbose:
                stats = decoder.get_statistics()
                print(f"📊 成功解码: {stats['successful_decodes']}/{stats['total_packets']} "
                      f"({stats['success_rate']:.1f}%)")
                print(f"📄 JSON结果: {json_file_path}")
                print(f"📋 日志文件: {log_file_path}")
        else:
            print(f"\n❌ 结果导出失败！")
            return 1
    else:
        print(f"\n❌ 解码失败！请检查输入文件和日志信息")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
