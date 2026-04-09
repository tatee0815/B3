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
        self.local_ip = self.get_local_ip()

    def get_local_ip(self):
        """Hàm tự động quét và lấy địa chỉ IPv4 LAN của máy hiện tại"""
        try:
            # Mở một socket UDP ảo kết nối đến 1 IP public (Google DNS).
            # Lưu ý: Không có dữ liệu nào thực sự được gửi đi, 
            # nó chỉ ép hệ điều hành báo xem đang dùng Card mạng (Wifi/LAN) nào để ra ngoài.
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            # Đề phòng máy hoàn toàn không có kết nối mạng nào
            return "127.0.0.1"

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
            # 0.0.0.0 nghĩa là lắng nghe trên MỌI card mạng (Wifi, LAN dây, Localhost)
            self.sock.bind(('0.0.0.0', port))
            self.is_host = True
            print("="*40)
            print(f"[Host] Đã mở server thành công trên port {port}")
            print(f"[Host] BẢO BẠN CỦA BẠN NHẬP IP NÀY VÀO: {self.local_ip}")
            print("="*40)
        except OSError as e:
            print(f"[Host] Lỗi mở port {port}: {e}")
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
                        print(f"[Host] Máy khách (Princess) đã kết nối từ {addr}")
                        self.send_data({"type": "handshake_ack"})
                    continue # Đã xử lý nội bộ, không cần trả về cho game state

                elif packet.get("type") == "handshake_ack":
                    if not self.is_host and not self.connected:
                        self.connected = True
                        print("[Client] Đã kết nối thành công tới Host (Knight)!")
                    continue
                    
                # --- ĐƯA GÓI TIN GAME VÀO DANH SÁCH ---
                packets.append(packet)

            except BlockingIOError:
                # Không còn tín hiệu nào trong buffer nữa, thoát vòng lặp
                break 
            except json.JSONDecodeError:
                break
            except Exception as e:
                # Bỏ qua các lỗi mạng vụn vặt để game không bị crash
                break
                
        return packets