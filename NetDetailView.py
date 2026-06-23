import tkinter as tk
import time
import os
import psutil
from CpuDetailView import CpuGraphCanvas

class NetDetailView(tk.Frame):
    def __init__(self, parent, net_name):
        super().__init__(parent, bg="#ffffff")
        self.net_name = net_name
        
        # 🛠️ SỬA: Khởi tạo mảng gồm 50 Tuple (Receive, Send) tương thích chuẩn đồ thị song hành của fen
        self.history_net_combined = [(0, 0)] * 50
        self.global_grid_offset = 0
        
        # Thiết lập Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) 
        self.grid_rowconfigure(1, weight=0) 
        self.grid_rowconfigure(2, weight=1) 
        self.grid_rowconfigure(3, weight=0) 
        
        self.setup_ui()
        
    def setup_ui(self):
        # --- HEADER ---
        header_frame = tk.Frame(self, bg="#ffffff")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))
        
        # Xác định là Wi-Fi hay Ethernet để hiển thị tiêu đề chuẩn Windows
        display_label = "Ethernet"
        if "wlan" in self.net_name or "wlp" in self.net_name:
            display_label = "Wi-Fi"
        elif "ppp" in self.net_name or "tailscale" in self.net_name:
            display_label = "VPN"
        lbl_title = tk.Label(header_frame, text=display_label, font=("", 28), bg="#ffffff", fg="#000000")
        lbl_title.pack(side="left", anchor="s")
        real_model = self.get_real_adapter_model(self.net_name)
        self.lbl_net_adapter = tk.Label(header_frame, text=real_model, font=("", 14), bg="#ffffff", fg="#555555")
        self.lbl_net_adapter.pack(side="right", anchor="s", pady=5)

        secondary_text_frame = tk.Frame(self, bg="#ffffff")
        secondary_text_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 0))
        self.lbl_peak_meter = tk.Label(secondary_text_frame, text="0 Kbps", font=("", 9), bg="#ffffff", fg="#555555")
        self.lbl_peak_meter.pack(side="right", anchor="s", pady=1)
        # --- BIỂU ĐỒ LỚN (Đa nét vẽ giống Disk Transfer) ---
        self.graph_frame = tk.Frame(self, bg="#ffffff")
        self.graph_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        
        self.graph_net = CpuGraphCanvas(
            self.graph_frame, click_callback=lambda: None, 
            history_data=self.history_net_combined, # 🛠️ Đổi sang mảng kết hợp
            is_logical=False, face_color="#F0EFEE", edge_color="#272727", 
            is_disk_transfer=True, component = 'Network'
        )
        self.graph_net.pack(fill="both", expand=True)
        
        # --- THÔNG SỐ ĐÁY ---
        self.stats_frame = tk.Frame(self, bg="#ffffff")
        self.stats_frame.grid(row=3, column=0, sticky="ew", padx=24, pady=(10, 15))
        
        self.stats_frame.grid_columnconfigure(0, minsize=150, weight=0, pad=20)
        self.stats_frame.grid_columnconfigure(1, minsize=150, weight=0, pad=20)
        self.stats_frame.grid_columnconfigure(2, minsize=200, weight=1)
        
        # Cột 0: Tốc độ gửi

        self.canvas_send_box = tk.Canvas(self.stats_frame, bg="#ffffff", highlightthickness=0, width=120, height=60)
        self.canvas_send_box.grid(row=1, column=0, rowspan=2, sticky="nsew", pady=(0, 5))
        self.canvas_send_box.pack_propagate(False)
        self.canvas_send_box.create_line(2, 2, 2, 50, fill="#272727", width=2)
        lbl_send_title = tk.Label(self.canvas_send_box, text="Send", font=("", 8), bg="#ffffff", fg="#555555")
        lbl_send_title.place(x=12, y=2)
        self.lbl_send_val = tk.Label(self.canvas_send_box, text="0 KB/s", font=("", 14), bg="#ffffff", fg="#000000")
        self.lbl_send_val.place(x=12, y=20)


        self.canvas_recv_box = tk.Canvas(self.stats_frame, bg="#ffffff", highlightthickness=0, width=120, height=60)
        self.canvas_recv_box.grid(row=1, column=1, rowspan=2, sticky="nsew", pady=(0, 5))
        self.canvas_recv_box.pack_propagate(False)
        self.canvas_recv_box.create_line(2, 2, 2, 50, fill="#272727", width=2, dash=(3, 2))
        lbl_recv_title = tk.Label(self.canvas_recv_box, text="Receive", font=("", 8), bg="#ffffff", fg="#555555")
        lbl_recv_title.place(x=12, y=2)
        self.lbl_recv_val = tk.Label(self.canvas_recv_box, text="0 KB/s", font=("", 14), bg="#ffffff", fg="#000000")
        self.lbl_recv_val.place(x=12, y=20)
        
        # Cột 2: Thông số mạng tĩnh (IP, Connection Type)
        self.info_sub_frame = tk.Frame(self.stats_frame, bg="#ffffff")
        self.info_sub_frame.grid(row=0, column=2, rowspan=2, sticky="nw", padx=(20, 0))
        
        tk.Label(self.info_sub_frame, text="Interface:", font=("", 9), bg="#ffffff", fg="#555555").grid(row=0, column=0, sticky="w")
        self.lbl_interface = tk.Label(self.info_sub_frame, text=self.net_name, font=("", 9), bg="#ffffff")
        self.lbl_interface.grid(row=0, column=1, sticky="w", padx=(40, 0))

        tk.Label(self.info_sub_frame, text="IPv4 address:", font=("", 9), bg="#ffffff", fg="#555555").grid(row=1, column=0, sticky="w")
        self.lbl_ipv4 = tk.Label(self.info_sub_frame, text="Disconnect", font=("", 9), bg="#ffffff")
        self.lbl_ipv4.grid(row=1, column=1, sticky="w", padx=(40, 0))

        tk.Label(self.info_sub_frame, text="IPv6 address:", font=("", 9), bg="#ffffff", fg="#555555").grid(row=2, column=0, sticky="w")
        self.lbl_ipv6 = tk.Label(self.info_sub_frame, text="Disconnect", font=("", 9), bg="#ffffff")
        self.lbl_ipv6.grid(row=2, column=1, sticky="w", padx=(40, 0))
    def get_real_adapter_model(self, net_name):
        """Hàm bóc tách tên model phần cứng thật của Card mạng từ Kernel Linux"""
        import os
        try:
            # Đường dẫn thiết bị của card mạng trong hệ thống sysfs
            uevent_path = f"/sys/class/net/{net_name}/device/uevent"
            if os.path.exists(uevent_path):
                with open(uevent_path, "r") as f:
                    content = f.read()
                    # Đối với thiết bị bus PCI (Thường là card mạng onboard, card PCIe rời)
                    # Nó sẽ có dòng PCI_SLOT_NAME=0000:03:00.0
                    # Ta có thể dùng lshw hoặc đọc thông tin driver bóc nhanh tên lớp
                    pass
            
            # Giải pháp vạn năng, mượt mà và cực kỳ chính xác: Gọi lệnh lshw cục bộ lớp network
            import subprocess
            cmd = ["lshw", "-C", "network", "-short"]
            # Chạy lệnh lấy danh sách rút gọn
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8")
            
            for line in out.splitlines():
                if net_name in line:
                    # Cấu trúc dòng của lshw -short: /0/100/1c.1/0  wlan0  network  Intel Corporation Wireless-AC 9260
                    # Ta sẽ tách chuỗi lấy phần mô tả phía sau chữ "network"
                    parts = line.split("network")
                    if len(parts) > 1:
                        model_name = parts[1].strip()
                        # Làm đẹp chuỗi tên thương hiệu
                        return model_name
        except:
            pass
            
        # Fallback 2: Đọc qua /proc/net/dev hoặc lspci nếu lshw không có sẵn
        try:
            import subprocess
            # Kiểm tra xem có phải card PCI không và tìm tên thương mại của nó
            device_link = os.readlink(f"/sys/class/net/{net_name}/device")
            pci_id = device_link.split("/")[-1] # Trả về dạng 0000:03:00.0
            out = subprocess.check_output(["lspci", "-s", pci_id]).decode("utf-8")
            if ":" in out:
                return out.split(":")[-1].strip() # Bóc đoạn tên card đằng sau dấu hai chấm
        except:
            pass

        return net_name # Nếu không tìm thấy gì (ví dụ mạng ảo docker/veth), trả về tên gốc (wlan0)
    def receive_central_net_data(self, send_speed_kbs, recv_speed_kbs, current_offset):
        """Hàm nhận dữ liệu chu kỳ 1s từ main.py gửi qua"""
        # 🛠️ SỬA: Đẩy cặp giá trị (Receive, Send) vào mảng lịch sử kép
        self.history_net_combined.pop(0)
        self.history_net_combined.append((recv_speed_kbs, send_speed_kbs))
        
        # Đồng bộ mảng phụ nếu class CpuGraphCanvas của fen có yêu cầu biến phụ
        if hasattr(self.graph_net, 'disk_write_history'):
            self.graph_net.disk_write_history = [item[1] for item in self.history_net_combined]
            
        # Định dạng text hiển thị đơn vị Kbps hoặc Mbps chuẩn hóa tốc độ mạng
        def format_net_speed(kbs):
            bps = kbs * 1024 * 8
            if bps >= 1000000:
                return f"{bps / 1000000:.1f} Mbps"
            return f"{bps / 1000:.1f} Kbps"
            
        self.lbl_send_val.config(text=format_net_speed(send_speed_kbs))
        self.lbl_recv_val.config(text=format_net_speed(recv_speed_kbs))
        
        # Quét lấy IP tĩnh thời gian thực phòng trường hợp đổi mạng
        try:
            addrs = psutil.net_if_addrs().get(self.net_name, [])
            ipv4_str = "Disconnect"
            ipv6_str = "Disconnect"
            for addr in addrs:
                if addr.family == 2: # AF_INET
                    ipv4_str = addr.address
                elif addr.family == 10: # AF_INET6
                    ipv6_str = addr.address.split('%')[0]
            self.lbl_ipv4.config(text=ipv4_str)
            self.lbl_ipv6.config(text=ipv6_str)
        except: pass
        
        # Vẽ lại đồ thị Pillow Canvas siêu nhẹ của fen
        self.graph_net.update_graph_only(current_offset)


        peak_kbps = self.graph_net.peak_val * 8
        if peak_kbps >= 1000000: # Lớn hơn hoặc bằng 1 Gbps (1.000.000 Kbps)
            peak_str = f"{peak_kbps / 1000000:.1f} Gbps"
        elif peak_kbps >= 1000:  # Lớn hơn hoặc bằng 1 Mbps (1.000 Kbps)
            peak_str = f"{peak_kbps / 1000:.1f} Mbps"
        else:
            peak_str = f"{int(peak_kbps)} Kbps"
        self.lbl_peak_meter.config(text=peak_str)