# ==============================================================================
# 改进版 STAMP 协议处理系统
# ==============================================================================
import time 
import json
import struct
import socket
from pyasn1.type import univ, namedtype, constraint, namedval
from pyasn1.codec.der import encoder as der_encoder, decoder as der_decoder
from crc import Calculator, Configuration
from typing import Dict, Optional, Any, Tuple
from datetime import datetime, timezone
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==============================================================================
# 步骤 1: 定义ASN.1数据结构（改进版）
# ==============================================================================

# 同步质量枚举
SyncQuality = univ.Enumerated(
    namedValues=namedval.NamedValues(
        ('unknown', 0), 
        ('gpsLocked', 1), 
        ('beidouLocked', 2),
        ('ppsStable', 3), 
        ('ppsUnstable', 4), 
        ('softwareSync', 5)
    )
)

# 主结构定义
class SpatioTemporalPacket(univ.Sequence):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('version', univ.Integer().subtype(
            subtypeSpec=constraint.ValueRangeConstraint(0, 255)
        )),
        namedtype.NamedType('timestamp_sec', univ.Integer()),
        namedtype.NamedType('timestamp_nsec', univ.Integer().subtype(
            subtypeSpec=constraint.ValueRangeConstraint(0, 999999999)
        )),
        namedtype.NamedType('latitude', univ.Real()),
        namedtype.NamedType('longitude', univ.Real()),
        namedtype.NamedType('altitude', univ.Real()),
        namedtype.NamedType('device_id', univ.OctetString().subtype(
            subtypeSpec=constraint.ValueSizeConstraint(8, 8)
        )),
        namedtype.NamedType('link_id', univ.Integer().subtype(
            subtypeSpec=constraint.ValueRangeConstraint(0, 65535)
        )),
        namedtype.NamedType('sync_status', SyncQuality),
        namedtype.NamedType('crc', univ.OctetString().subtype(
            subtypeSpec=constraint.ValueSizeConstraint(2, 2)
        ))
    )

# ==============================================================================
# 改进的核心功能函数
# ==============================================================================

def parse_nmea_for_info(gpgga_string: str, gnrmc_string: str) -> Optional[Dict]:
    """
    改进的NMEA解析函数，增加错误处理和验证
    """
    try:
        # 验证输入格式
        if not gpgga_string or not gnrmc_string:
            logger.error("NMEA字符串为空")
            return None
            
        # 解析GNRMC
        rmc_parts = gnrmc_string.strip().split(',')
        if len(rmc_parts) < 10:
            logger.error(f"GNRMC格式错误，字段数量不足: {len(rmc_parts)}")
            return None
            
        if rmc_parts[0] not in ('$GNRMC', '$GPRMC'):
            logger.error(f"不支持的RMC格式: {rmc_parts[0]}")
            return None
            
        if rmc_parts[2] != 'A':
            logger.warning(f"定位状态无效: {rmc_parts[2]}")
            return None
            
        # 解析GPGGA
        gga_parts = gpgga_string.strip().split(',')
        if len(gga_parts) < 12:
            logger.error(f"GPGGA格式错误，字段数量不足: {len(gga_parts)}")
            return None
            
        if gga_parts[0] != '$GPGGA':
            logger.error(f"不支持的GGA格式: {gga_parts[0]}")
            return None
            
        if not gga_parts[6] or int(gga_parts[6]) == 0:
            logger.warning("定位质量无效或无定位")
            return None
        
        # 解析时间
        date_str = rmc_parts[9]
        utc_date_str = f"20{date_str[4:6]}-{date_str[2:4]}-{date_str[0:2]}"
        utc_time_str = gga_parts[1]
        
        # 处理时间格式
        if '.' in utc_time_str:
            time_format = "%Y-%m-%d %H%M%S.%f"
        else:
            time_format = "%Y-%m-%d %H%M%S"
            
        dt_obj_naive = datetime.strptime(f"{utc_date_str} {utc_time_str}", time_format)
        dt_obj_utc = dt_obj_naive.replace(tzinfo=timezone.utc)
        
        # 解析坐标
        lat_deg = float(gga_parts[2][:2])
        lat_min = float(gga_parts[2][2:])
        latitude = (lat_deg + lat_min / 60.0) * (-1 if gga_parts[3] == 'S' else 1)
        
        lon_deg = float(gga_parts[4][:3])
        lon_min = float(gga_parts[4][3:])
        longitude = (lon_deg + lon_min / 60.0) * (-1 if gga_parts[5] == 'W' else 1)
        
        # 验证坐标范围
        if not (-90 <= latitude <= 90):
            logger.error(f"纬度超出有效范围: {latitude}")
            return None
            
        if not (-180 <= longitude <= 180):
            logger.error(f"经度超出有效范围: {longitude}")
            return None
        
        result = {
            "timestamp_sec": int(dt_obj_utc.timestamp()),
            "timestamp_nsec": dt_obj_utc.microsecond * 1000,
            "latitude": latitude,
            "longitude": longitude,
            "altitude": float(gga_parts[9])
        }
        
        logger.info(f"NMEA解析成功: 时间={dt_obj_utc}, 位置=({latitude:.6f}, {longitude:.6f}), 高度={result['altitude']}m")
        return result
        
    except (ValueError, IndexError, TypeError) as e:
        logger.error(f"NMEA解析失败: {e}")
        return None

def create_stamp_packet(parsed_info: Dict, device_id: bytes, link_id: int, 
                       sync_status: str, version: int = 1) -> Optional[bytes]:
    """
    改进的STAMP报文创建函数
    """
    try:
        # 验证输入参数
        if len(device_id) != 8:
            logger.error(f"设备ID长度错误: {len(device_id)}，应为8字节")
            return None
            
        if not (0 <= link_id <= 65535):
            logger.error(f"链路ID超出范围: {link_id}")
            return None
            
        # 创建数据包
        packet = SpatioTemporalPacket()
        
        # 填充字段
        packet['version'] = version
        packet['timestamp_sec'] = parsed_info['timestamp_sec']
        packet['timestamp_nsec'] = parsed_info['timestamp_nsec']
        packet['latitude'] = round(parsed_info['latitude'], 8)
        packet['longitude'] = round(parsed_info['longitude'], 8)
        packet['altitude'] = parsed_info['altitude']
        packet['device_id'] = device_id
        packet['link_id'] = link_id
        packet['sync_status'] = sync_status
        packet['crc'] = b'\x00\x00'  # 临时填充
        
        # 计算CRC
        data_for_crc = der_encoder.encode(packet)
        crc_config = Configuration(
            width=16, 
            polynomial=0x1021, 
            init_value=0xFFFF, 
            final_xor_value=0x0000, 
            reverse_input=False, 
            reverse_output=False
        )
        crc_value = Calculator(crc_config).checksum(data_for_crc)
        
        # 设置正确的CRC值
        packet['crc'] = crc_value.to_bytes(2, 'big')
        
        # 最终编码
        final_encoded = der_encoder.encode(packet)
        
        logger.info(f"STAMP报文创建成功: 长度={len(final_encoded)}字节, CRC={crc_value:04X}")
        return final_encoded
        
    except Exception as e:
        logger.error(f"STAMP报文创建失败: {e}")
        return None

def decode_stamp_packet(encoded_bytes: bytes) -> Optional[Dict[str, Any]]:
    """
    改进的STAMP报文解码函数
    """
    try:
        # 解码ASN.1结构
        decoded_packet, _ = der_decoder.decode(encoded_bytes, asn1Spec=SpatioTemporalPacket())
        
        # 提取CRC
        received_crc_bytes = bytes(decoded_packet['crc'])
        
        # 创建用于CRC校验的临时数据包
        packet_for_crc_check = SpatioTemporalPacket()
        for field_name in ['version', 'timestamp_sec', 'timestamp_nsec', 'latitude', 
                          'longitude', 'altitude', 'device_id', 'link_id', 'sync_status']:
            packet_for_crc_check[field_name] = decoded_packet[field_name]
        packet_for_crc_check['crc'] = b'\x00\x00'
        
        # 重新计算CRC
        data_to_recalculate_crc = der_encoder.encode(packet_for_crc_check)
        crc_config = Configuration(
            width=16, 
            polynomial=0x1021, 
            init_value=0xFFFF, 
            final_xor_value=0x0000, 
            reverse_input=False, 
            reverse_output=False
        )
        calculated_crc_bytes = Calculator(crc_config).checksum(data_to_recalculate_crc).to_bytes(2, 'big')
        
        # CRC校验
        if received_crc_bytes != calculated_crc_bytes:
            logger.error(f"CRC校验失败: 接收={received_crc_bytes.hex()}, 计算={calculated_crc_bytes.hex()}")
            return None

        # 提取数据
        result = {
            'version': int(decoded_packet['version']),
            'timestamp_sec': int(decoded_packet['timestamp_sec']),
            'timestamp_nsec': int(decoded_packet['timestamp_nsec']),
            'latitude': float(decoded_packet['latitude']),
            'longitude': float(decoded_packet['longitude']),
            'altitude': float(decoded_packet['altitude']),
            'device_id': bytes(decoded_packet['device_id']).hex().upper(),
            'link_id': int(decoded_packet['link_id']),
            'sync_status': int(decoded_packet['sync_status']),
            'crc': received_crc_bytes.hex().upper()
        }
        
        logger.info(f"STAMP解码成功: CRC校验通过")
        return result
        
    except Exception as e:
        logger.error(f"STAMP解码失败: {e}")
        return None

# ==============================================================================
# 改进的模块A和B
# ==============================================================================

def module_a_generate_stamp(
    gpgga_str: str, gnrmc_str: str, device_id: bytes, link_id: int, sync_status: str
) -> Optional[bytes]:
    """模块A: STAMP编码构造"""
    logger.info("=" * 50)
    logger.info("模块A: STAMP编码构造开始")
    logger.info("=" * 50)
    
    # 解析NMEA数据
    parsed_info = parse_nmea_for_info(gpgga_str, gnrmc_str)
    if not parsed_info:
        logger.error("模块A失败: NMEA解析失败")
        return None
    
    # 创建STAMP报文
    stamp_der_bytes = create_stamp_packet(parsed_info, device_id, link_id, sync_status)
    if not stamp_der_bytes:
        logger.error("模块A失败: STAMP报文创建失败")
        return None
        
    logger.info(f"模块A成功: 生成STAMP DER报文 (长度: {len(stamp_der_bytes)} 字节)")
    logger.info(f"模块A输出 (Hex): {stamp_der_bytes.hex()}")
    return stamp_der_bytes

def module_b_process_ipv6_packet(ipv6_packet_bytes: bytes) -> Optional[Dict[str, Any]]:
    """模块B: STAMP解码与提取"""
    logger.info("=" * 50)
    logger.info("模块B: STAMP解码与提取开始")
    logger.info("=" * 50)
    logger.info(f"模块B接收到 {len(ipv6_packet_bytes)} 字节的IPv6数据包")
    
    IPV6_HEADER_LEN = 40
    if len(ipv6_packet_bytes) < IPV6_HEADER_LEN:
        logger.error("模块B错误: 数据包过短，无法解析IPv6头部")
        return None
        
    # 解析IPv6头部
    next_header = ipv6_packet_bytes[6]
    logger.info(f"模块B解析IPv6头部... Next Header: {next_header}")
    
    STAMP_IPV6_NEXT_HEADER = 254
    if next_header == STAMP_IPV6_NEXT_HEADER:
        logger.info(f"模块B成功: 发现STAMP扩展头 (Next Header = {STAMP_IPV6_NEXT_HEADER})")
        stamp_der_bytes = ipv6_packet_bytes[IPV6_HEADER_LEN:]
        logger.info(f"模块B成功: 提取出 {len(stamp_der_bytes)} 字节的STAMP负载")
        
        # 解码STAMP数据
        result = decode_stamp_packet(stamp_der_bytes)
        if result:
            logger.info("模块B成功: STAMP解码和CRC校验通过")
        else:
            logger.error("模块B失败: STAMP解码或CRC校验失败")
        return result
    else:
        logger.warning(f"模块B未发现STAMP扩展头 (Next Header = {next_header})，跳过处理")
        return None

# ==============================================================================
# 网络封装函数
# ==============================================================================

def _simulate_network_encapsulation(payload: bytes, src_ip: str, dst_ip: str) -> bytes:
    """模拟IPv6封装"""
    try:
        version_tc_flow = (6 << 28)
        payload_length = len(payload)
        next_header = 254  # STAMP扩展头标识
        hop_limit = 64
        src_addr_bytes = socket.inet_pton(socket.AF_INET6, src_ip)
        dst_addr_bytes = socket.inet_pton(socket.AF_INET6, dst_ip)
        
        ipv6_header = struct.pack('!I H B B 16s 16s', 
                                  version_tc_flow, payload_length, next_header,
                                  hop_limit, src_addr_bytes, dst_addr_bytes)
        return ipv6_header + payload
    except Exception as e:
        logger.error(f"IPv6封装失败: {e}")
        return b''

# ==============================================================================
# 测试函数
# ==============================================================================

def test_with_real_gnss_data():
    """使用真实的GNSS数据测试"""
    # 从您的GNSS软件输出中提取的真实数据
    gnrmc_input_str = "$GPRMC,000012.00,A,3031.9000425,N,11421.4368798,E,0.01,0.00,010525,0.0,E,A*37"
    gpgga_input_str = "$GPGGA,000012.00,3031.9000425,N,11421.4368798,E,1,08,1.0,42.636,M,-13.987,M,0.0,*57"
    
    MY_DEVICE_ID = b'\xDE\xAD\xBE\xEF\xCA\xFE\xBA\xBE'
    MY_LINK_ID = 1024
    current_sync_status_name = 'beidouLocked'  # 使用北斗锁定状态
    SRC_IP = "2001:db8:1::1"
    DST_IP = "2001:db8:2::2"

    logger.info("开始端到端测试...")
    
    # 模块A工作
    stamp_payload = module_a_generate_stamp(
        gpgga_input_str, gnrmc_input_str, MY_DEVICE_ID, MY_LINK_ID, current_sync_status_name
    )

    if stamp_payload:
        # 模拟网络传输
        logger.info("模拟网络层将模块A的输出封装进IPv6包进行传输")
        full_ipv6_packet = _simulate_network_encapsulation(stamp_payload, SRC_IP, DST_IP)
        logger.info(f"IPv6数据包已生成，总长度 {len(full_ipv6_packet)} 字节")

        # 模块B工作
        final_data = module_b_process_ipv6_packet(full_ipv6_packet)

        # 最终结果
        if final_data:
            logger.info("=" * 50)
            logger.info("最终输出给误差分析模块的JSON数据")
            logger.info("=" * 50)
            json_output = json.dumps(final_data, indent=4, ensure_ascii=False)
            print(json_output)
            return True
        else:
            logger.error("模块B失败: 解码或CRC校验失败")
            return False
    else:
        logger.error("模块A失败: 无法生成STAMP报文")
        return False

if __name__ == '__main__':
    success = test_with_real_gnss_data()
    if success:
        print("\n✅ 测试成功！STAMP协议处理系统工作正常")
    else:
        print("\n❌ 测试失败！请检查日志信息")
