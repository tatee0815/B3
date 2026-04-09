# game/utils/network.py
import socket
import json

class NetworkManager:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.is_host = False
        self.client_address = None
        self.host_address = None
        self.connected = False
        # Tự động lấy IP Local khi khởi tạo mạng
        self.local_ip = self.get_local_ip()

    def get_local_ip(self):
        """Hàm tự động quét và lấy địa chỉ IPv4 LAN của máy hiện tại"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def get_room_code(self):
        """Tạo mã phòng 4-5 số từ IP của Host"""
        if not self.local_ip or self.local_ip == "127.0.0.1":
            return "12345" # Mã đặc biệt nếu chơi trên cùng 1 máy (không có mạng LAN)
            
        parts = self.local_ip.split('.')
        if len(parts) == 4:
            # Lấy 2 cụm cuối của IP gộp lại thành 1 số
            code = int(parts[2]) * 256 + int(parts[3])
            return str(code).zfill(4) 
        return "12345"

    def decode_room_code(self, code_str):
        """Dịch ngược mã phòng thành IP hoàn chỉnh"""
        if code_str == "12345":
            return "127.0.0.1" # Dịch ngược lại về localhost nếu dùng mã test
            
        try:
            code = int(code_str)
            parts = self.local_ip.split('.')
            if len(parts) == 4:
                prefix = f"{parts[0]}.{parts[1]}." 
                p3 = code // 256
                p4 = code % 256
                return f"{prefix}{p3}.{p4}"
        except ValueError:
            pass
        return "255.255.255.255" # Trả về IP lỗi nếu mã bậy bạ

    def close(self):
        """Đóng socket cũ và tạo socket mới, reset trạng thái"""
        try:
            self.sock.close()
        except:
            pass
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.is_host = False
        self.client_address = None
        self.host_address = None
        self.connected = False

    def start_host(self, port=5555):
        if not (1 <= port <= 65535):
            port = 5555
        self.close()
        try:
            self.sock.bind(('0.0.0.0', port))
            self.is_host = True
            print("="*40)
            print(f"[Host] Đã mở server trên IP: {self.local_ip} | Port: {port}")
            print(f"[Host] MÃ PHÒNG: {self.get_room_code()}")
            print("="*40)
        except OSError as e:
            print(f"[Host] Lỗi bind port {port}: {e}")
            raise

    def connect_to_host(self, ip, port=5555):
        self.close()
        self.host_address = (ip, port)
        self.is_host = False
        self.send_data({"type": "handshake", "role": "princess"})
        print(f"[Client] Đang kết nối tới {ip}:{port}")

    def send_data(self, data):
        try:
            packet = json.dumps(data).encode('utf-8')
            if self.is_host and self.client_address:
                self.sock.sendto(packet, self.client_address)
            elif not self.is_host and self.host_address:
                self.sock.sendto(packet, self.host_address)
        except:
            pass

    def get_packets(self):
        """Rút cạn toàn bộ tín hiệu trong buffer mỗi frame để tránh lag/delay"""
        packets = []
        while True:
            try:
                data, addr = self.sock.recvfrom(2048)
                packet = json.loads(data.decode('utf-8'))
                
                # --- XỬ LÝ KẾT NỐI (HANDSHAKE) ---
                if packet.get("type") == "handshake":
                    if self.is_host and not self.connected:
                        self.client_address = addr
                        self.connected = True
                        print(f"[Host] Công Chúa đã kết nối từ {addr}")
                        self.send_data({"type": "handshake_ack"})
                    continue 

                elif packet.get("type") == "handshake_ack":
                    if not self.is_host and not self.connected:
                        self.connected = True
                        print("[Client] Đã kết nối thành công tới Hiệp Sĩ!")
                    continue
                    
                packets.append(packet)

            except BlockingIOError:
                break 
            except json.JSONDecodeError:
                break
            except Exception:
                break
                
        return packets