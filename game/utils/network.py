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
            print(f"[Host] Port {port} không hợp lệ, dùng 5555")
            port = 5555
        self.close()  # Đảm bảo socket sạch
        try:
            self.sock.bind(('0.0.0.0', port))
            self.is_host = True
            print(f"[Host] Đã mở server trên port {port}")
        except OSError as e:
            print(f"[Host] Lỗi bind port {port}: {e}")
            raise

    def connect_to_host(self, ip, port=5555):
        self.close()
        self.host_address = (ip, port)
        self.is_host = False
        self.send_data({"type": "handshake", "role": "princess"})
        print(f"[Client] Kết nối tới {ip}:{port}")

    def send_data(self, data):
        try:
            packet = json.dumps(data).encode('utf-8')
            if self.is_host and self.client_address:
                self.sock.sendto(packet, self.client_address)
            elif not self.is_host and self.host_address:
                self.sock.sendto(packet, self.host_address)
        except:
            pass

    def update_network(self):
        try:
            data, addr = self.sock.recvfrom(2048)
            packet = json.loads(data.decode('utf-8'))
            if packet.get("type") == "handshake":
                if self.is_host and not self.connected:
                    self.client_address = addr
                    self.connected = True
                    print(f"[Host] Công chúa kết nối từ {addr}")
                    self.send_data({"type": "handshake_ack"})
            elif packet.get("type") == "handshake_ack" and not self.is_host:
                if not self.connected:
                    self.connected = True
                    print("[Client] Kết nối thành công")
            return packet
        except BlockingIOError:
            return None
        except:
            return None