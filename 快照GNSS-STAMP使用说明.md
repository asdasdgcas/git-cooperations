# 快照GNSS-STAMP处理系统使用说明

## 📸 系统概述

快照GNSS-STAMP处理系统是实时系统的补充版本，专门用于获取**当前时刻**的GPGGA和GPRMC数据，进行一次STAMP编码后自动停止。

## 🆚 与实时系统的区别

| 特性 | 实时系统 (`realtime_gnss_stamp.py`) | 快照系统 (`snapshot_gnss_stamp.py`) |
|------|-------------------------------------|-------------------------------------|
| **运行方式** | 持续运行，直到手动停止 | 获取一次数据后自动停止 |
| **数据量** | 源源不断的多条数据 | 仅一条当前时刻的数据 |
| **输出文件** | 包含多个数据包的文件 | 包含单个数据包的文件 |
| **使用场景** | 长期监控、数据采集 | 测试、验证、快速检查 |
| **输出目录** | `IGS-Data/STAMP-Realtime` | `IGS-Data/STAMP-Snapshot` |

## 🚀 快速开始

### 方法1: 使用批处理文件（推荐）
```bash
# 双击运行
run_snapshot_gnss.bat
```

### 方法2: 使用Python脚本
```bash
# 快速获取快照
python run_snapshot_gnss.py

# 或者
python snapshot_gnss_stamp.py
```

## ⚙️ 系统配置

### 配置文件: `snapshot_gnss_config.json`
```json
{
    "serial_port": "COM3",           // 串口号
    "serial_baudrate": 115200,       // 波特率
    "read_timeout": 30.0,            // 读取超时时间(秒)
    "device_id": "DEADBEEFCAFEBABE", // 设备ID
    "link_id": 1024,                 // 链路ID
    "sync_status": "beidouLocked",   // 同步状态
    "src_ip": "2001:db8:1::1",       // 源IP地址
    "dst_ip": "2001:db8:2::2",       // 目标IP地址
    "output_dir": "IGS-Data/STAMP-Snapshot", // 输出目录
    "log_level": "INFO"              // 日志级别
}
```

### 配置修改方法
```bash
# 进入配置模式
python run_snapshot_gnss.py --config
```

## 🔧 使用步骤

### 1. 硬件连接
- 将GNSS设备连接到计算机串口
- 确认设备正常工作并输出NMEA数据

### 2. 启动快照获取
```bash
# 快速模式
python run_snapshot_gnss.py --quick
```

### 3. 系统工作流程
1. **连接串口** - 自动连接到指定串口
2. **读取数据** - 等待并读取GPGGA和GPRMC数据对
3. **STAMP编码** - 对数据进行STAMP协议编码
4. **保存文件** - 同时生成HEX和JSON文件
5. **自动停止** - 完成后自动退出

### 4. 查看结果
快照完成后，结果保存在：
- `IGS-Data/STAMP-Snapshot/stamp_encoded_*.hex` - 编码数据（十六进制格式）
- `IGS-Data/STAMP-Snapshot/stamp_results_*.json` - 编码结果（JSON格式，包含解码信息）
- `snapshot_gnss_stamp.log` - 运行日志

## 📁 文件说明

### 核心文件
- `snapshot_gnss_stamp.py` - 快照处理核心模块
- `run_snapshot_gnss.py` - 启动脚本
- `run_snapshot_gnss.bat` - Windows批处理启动脚本

### 配置文件
- `snapshot_gnss_config.json` - 快照处理配置

### 输出文件
- `snapshot_gnss_stamp.log` - 快照处理日志
- `IGS-Data/STAMP-Snapshot/` - 快照输出目录

## 📊 数据流程

```
串口连接 → 读取NMEA → 数据匹配 → STAMP编码 → 文件保存 → 自动停止
   ↓         ↓          ↓          ↓          ↓          ↓
  COM3    GPGGA/GPRMC  数据对匹配  协议封装   HEX/JSON   程序结束
```

### 数据读取逻辑
- 系统连接串口后开始监听NMEA数据
- 自动匹配相同时间戳的GPGGA和GPRMC数据
- 找到第一对匹配数据后立即进行编码
- 编码完成后自动断开连接并退出

## 🎯 使用场景

### 1. 设备测试
```bash
# 快速检查GNSS设备是否正常工作
python run_snapshot_gnss.py
```

### 2. 位置验证
```bash
# 获取当前精确位置信息
python snapshot_gnss_stamp.py
```

### 3. 系统调试
```bash
# 验证STAMP编码功能
python run_snapshot_gnss.py --quick
```

### 4. 数据采样
```bash
# 定期获取位置快照（可配合定时任务）
python snapshot_gnss_stamp.py
```

## 🔍 故障排除

### 常见问题

#### 1. 读取超时
**症状**: 提示"读取超时，未找到匹配的NMEA数据对"
**解决方案**:
- 检查GNSS设备是否正常输出数据
- 增加 `read_timeout` 配置值
- 确认串口连接正常

#### 2. 数据格式错误
**症状**: 接收到数据但无法匹配
**解决方案**:
- 确认设备输出标准的GPGGA和GPRMC格式
- 检查数据的时间戳是否一致
- 查看日志文件了解详细错误

#### 3. 串口占用
**症状**: 无法打开串口
**解决方案**:
- 确认串口未被其他程序占用
- 检查串口号是否正确
- 尝试重新插拔设备

## 📈 输出文件格式

### HEX文件示例
```
#1 [2025-10-08 18:15:30] 长度=86字节
305402010102046812B98C020100090E0333303533313636373338452D38...
```

### JSON文件示例
```json
{
  "metadata": {
    "encoder_version": "2.0.0",
    "encode_timestamp": "2025-10-08T18:15:30",
    "statistics": {
      "total_packets": 1,
      "successful_encodes": 1,
      "success_rate": 100.0
    }
  },
  "encoded_packets": [
    {
      "packet_index": 1,
      "position": {
        "latitude": 30.5316674,
        "longitude": 114.3572281,
        "altitude": 42.636
      },
      "timestamp": {
        "datetime_utc": "2025-10-08T10:15:30+00:00"
      },
      "validation": {
        "crc_valid": true
      }
    }
  ]
}
```

## 🔄 与其他系统的集成

### 定时任务集成
```bash
# Windows任务计划程序
# 每小时执行一次快照
schtasks /create /tn "GNSS快照" /tr "python D:\LXZ-PVT-main\snapshot_gnss_stamp.py" /sc hourly
```

### 批处理脚本集成
```batch
@echo off
echo 开始GNSS快照采集...
cd /d "D:\LXZ-PVT-main"
python snapshot_gnss_stamp.py
if %errorlevel% equ 0 (
    echo 快照采集成功
) else (
    echo 快照采集失败
)
```

## 📞 技术支持

### 日志分析
查看 `snapshot_gnss_stamp.log` 文件：
- 连接状态信息
- NMEA数据接收情况
- STAMP编码结果
- 错误和警告信息

### 性能监控
系统会显示以下信息：
- 串口连接状态
- NMEA数据接收统计
- STAMP编码成功率
- 文件保存结果

---

**版本**: 1.0.0  
**更新日期**: 2025-10-08  
**兼容性**: Python 3.6+, Windows/Linux  
**依赖**: 与实时系统相同的依赖包

