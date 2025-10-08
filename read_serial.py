# 文件路径: d:/AAA-Study/项目/网安项目/test/test.py

import serial
import serial.tools.list_ports
import time
import threading
import sys

# 全局变量控制退出
exit_event = threading.Event()

def find_available_ports():
    """列出当前可用的串口"""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("❌ 未检测到任何串口设备")
    else:
        print("✅ 可用串口:")
        for port in ports:
            print(f"    {port.device} - {port.description}")
    print("-" * 50)

def read_from_serial(ser):
    """子线程：持续读取串口数据"""
    while not exit_event.is_set():
        try:
            if ser.in_waiting > 0:
                data = ser.readline()
                try:
                    text = data.decode('utf-8', errors='ignore').strip()
                    if text:
                        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        print(f"[{timestamp}] ← {text}")
                except Exception as e:
                    hex_data = ' '.join([f'{b:02X}' for b in data])
                    print(f"[← Hex] {hex_data}")
            else:
                time.sleep(0.01)
        except Exception as e:
            if not exit_event.is_set():
                print(f"❌ 接收错误: {e}")
            break

def send_to_serial(ser):
    """主线程：接收用户输入并发送"""
    print("\n📌 输入指令（支持）:")
    print("   - 直接输入文本（如 AT+RESET）并回车发送")
    print("   - 输入 hex:0A0B0C 发送十六进制（如换行符）")
    print("   - 输入 quit 或 exit 退出")
    print("-" * 50)

    while not exit_event.is_set():
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit']:
                print("🛑 正在退出...")
                exit_event.set()
                break

            # 发送十六进制：格式 hex:0A0B0C
            if user_input.lower().startswith("hex:"):
                try:
                    hex_str = user_input[4:].replace(' ', '')
                    byte_data = bytes.fromhex(hex_str)
                    ser.write(byte_data)
                    print(f"[→ Hex] {hex_str.upper()}")
                except ValueError as e:
                    print(f"❌ 十六进制格式错误: {e}")
            else:
                # 发送文本（UTF-8 编码 + \n）
                message = user_input + '\n'
                ser.write(message.encode('utf-8'))
                print(f"[→ TXT] {user_input}")

        except EOFError:
            # input 被中断（如 Ctrl+D）
            exit_event.set()
            break
        except Exception as e:
            print(f"❌ 发送失败: {e}")
            exit_event.set()
            break

def main():
    # ======== 配置区（请根据你的设备修改）========
    PORT = "COM3"        # ← 修改为你的串口号
    BAUDRATE = 115200      # ← 修改为你的设备波特率
    # ===========================================

    find_available_ports()

    ser = None
    try:
        print(f"🔌 正在连接串口 {PORT} @ {BAUDRATE}...")
        ser = serial.Serial(
            port=PORT,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        time.sleep(1)

        if ser.is_open:
            print(f"✅ 成功打开串口: {ser.port}")
            print("🟢 开始监听数据... (输入指令或键入 exit 退出)")

        # 启动接收线程
        reader_thread = threading.Thread(target=read_from_serial, args=(ser,), daemon=True)
        reader_thread.start()

        # 主线程负责发送
        send_to_serial(ser)

    except serial.SerialException as e:
        print(f"❌ 无法打开串口: {e}")
        print("请检查：串口是否被占用、设备是否断unlgo开、驱动是否正常")
    except Exception as e:
        print(f"❌ 未知错误: {e}")
    finally:
        exit_event.set()
        if ser and ser.is_open:
            ser.close()
            print("✅ 串口已安全关闭")
        print("👋 程序结束")

if __name__ == "__main__":
    main()