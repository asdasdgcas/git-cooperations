# 实时GNSS-STAMP处理系统使用说明

## 📋 系统概述

实时GNSS-STAMP处理系统能够从串口实时读取GPGGA和GPRMC数据，自动进行STAMP协议编码，并保存编码结果。

## 🚀 快速开始

### 方法1: 使用批处理文件（推荐）
```bash
# 双击运行
run_realtime_gnss.bat
```

### 方法2: 使用Python脚本
```bash
# 快速启动
python run_realtime_gnss.py

# 或者指定选项
python run_realtime_gnss.py --quick
```

## ⚙️ 系统配置

### 配置文件: `realtime_gnss_config.json`
```json
{
    "serial_port": "COM3",           // 串口号
    "serial_baudrate": 115200,       // 波特率
    "device_id": "DEADBEEFCAFEBABE", // 设备ID (16位十六进制)
    "link_id": 1024,                 // 链路ID
    "sync_status": "beidouLocked",   // 同步状态
    "src_ip": "2001:db8:1::1",       // 源IP地址
    "dst_ip": "2001:db8:2::2",       // 目标IP地址
    "output_dir": "IGS-Data/STAMP-Realtime", // 输出目录
    "log_level": "INFO"              // 日志级别
}
```

### 配置修改方法
```bash
# 进入配置模式
python run_realtime_gnss.py --config
```

## 🔧 使用步骤

### 1. 硬件连接
- 将GNSS设备连接到计算机串口
- 确认设备正常工作并输出NMEA数据

### 2. 检查串口
```bash
# 测试串口连接
python run_realtime_gnss.py --test
```

### 3. 启动实时处理
```bash
# 快速启动
python run_realtime_gnss.py --quick
```

### 4. 查看结果
处理完成后，结果保存在以下位置：
- `IGS-Data/STAMP-Realtime/stamp_encoded_*.hex` - 编码数据（十六进制格式）
- `IGS-Data/STAMP-Realtime/stamp_results_*.json` - 编码结果（JSON格式，包含解码信息）
- `realtime_gnss_stamp.log` - 运行日志

## 📁 文件说明

### 核心文件
- `realtime_gnss_stamp.py` - 实时处理核心模块
- `run_realtime_gnss.py` - 启动脚本
- `run_realtime_gnss.bat` - Windows批处理启动脚本
- `test_realtime_system.py` - 系统测试脚本

### 配置文件
- `realtime_gnss_config.json` - 实时处理配置
- `gnss_stamp_config.json` - 原有的批处理配置

### 输出文件
- `realtime_gnss_stamp.log` - 实时处理日志
- `IGS-Data/STAMP-Realtime/` - 实时处理输出目录

## 🧪 系统测试

运行系统测试以验证功能：
```bash
python test_realtime_system.py
```

测试项目包括：
- NMEA数据缓冲器功能
- STAMP编码功能  
- 配置文件加载
- 输出目录创建
- 模拟串口数据处理

## 📊 数据流程

```
串口数据 → NMEA解析 → 数据匹配 → STAMP编码 → 文件保存
   ↓           ↓          ↓          ↓          ↓
GPGGA/GPRMC  时间戳提取  数据对匹配  协议封装   HEX/JSON
```

### 数据匹配逻辑
- 系统自动匹配相同时间戳的GPGGA和GPRMC数据
- 使用时分秒（HHMMSS）作为匹配键
- 超过2秒的数据自动清理

### STAMP编码过程
1. 解析NMEA数据提取时间、位置信息
2. 创建STAMP协议数据包
3. 计算CRC校验码
4. ASN.1 DER编码
5. IPv6封装（模拟）

## 🔍 故障排除

### 常见问题

#### 1. 串口连接失败
**症状**: 提示"无法打开串口"
**解决方案**:
- 检查串口号是否正确（使用测试功能检查可用串口）
- 确认串口未被其他程序占用
- 检查串口驱动是否正常

#### 2. 没有NMEA数据
**症状**: 连接成功但无数据输出
**解决方案**:
- 确认GNSS设备正常工作
- 检查波特率设置是否正确
- 确认设备输出GPGGA和GPRMC格式数据

#### 3. 编码失败
**症状**: 接收到数据但编码失败
**解决方案**:
- 检查NMEA数据格式是否正确
- 确认定位状态有效（GPRMC中的A状态）
- 查看日志文件获取详细错误信息

#### 4. 数据匹配失败
**症状**: 接收到NMEA数据但无匹配对
**解决方案**:
- 检查GPGGA和GPRMC的时间戳是否一致
- 确认数据输出频率和时间同步
- 调整缓冲器超时时间

### 日志分析
查看 `realtime_gnss_stamp.log` 文件：
- `INFO` 级别：正常运行信息
- `WARNING` 级别：警告信息，系统可继续运行
- `ERROR` 级别：错误信息，需要处理

## 📞 技术支持

### 调试模式
```bash
# 启用详细日志
# 修改配置文件中的 log_level 为 "DEBUG"
```

### 性能监控
系统会实时显示以下统计信息：
- 接收的NMEA语句总数
- GPGGA和GPRMC数据计数
- 成功匹配的数据对数量
- STAMP编码成功率
- 网络传输数据包数量

### 输出格式说明

#### HEX文件格式
```
#1 [2025-10-08 17:30:15] 长度=89字节
3082005530820051020101020...
```

#### JSON文件格式
```json
{
  "metadata": {
    "encoder_version": "2.0.0",
    "encode_timestamp": "2025-10-08T17:30:15",
    "statistics": {
      "total_packets": 100,
      "successful_encodes": 98,
      "success_rate": 98.0
    }
  },
  "encoded_packets": [
    {
      "packet_index": 1,
      "encoding_timestamp": "2025-10-08T17:30:15",
      "position": {
        "latitude": 30.5316674,
        "longitude": 114.3572281,
        "altitude": 42.636
      },
      "validation": {
        "crc_valid": true
      }
    }
  ]
}
```

## 🔄 与原有系统的区别

| 功能 | 原有系统 | 实时系统 |
|------|----------|----------|
| 数据源 | 固定文件 | 串口实时数据 |
| 处理方式 | 批量处理 | 实时流处理 |
| 数据匹配 | 顺序读取 | 智能匹配 |
| 启动方式 | `python run_gnss_stamp.py` | `python run_realtime_gnss.py` |
| 输出目录 | `IGS-Data/STAMP-Output` | `IGS-Data/STAMP-Realtime` |

## 📈 系统扩展

### 自定义数据处理
可以修改 `_process_nmea_pair` 函数来添加自定义的数据处理逻辑。

### 网络传输
当前版本模拟网络传输，可以扩展为真实的UDP/TCP传输。

### 多串口支持
可以扩展系统支持多个串口同时处理。

---

**版本**: 1.0.0  
**更新日期**: 2025-10-08  
**兼容性**: Python 3.6+, Windows/Linux
