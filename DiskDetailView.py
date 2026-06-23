import tkinter as tk
import psutil
import numpy as np
from CpuDetailView import CpuGraphCanvas

class DiskDetailView(tk.Frame):
    def __init__(self, parent, disk_name):
        super().__init__(parent, bg="#ffffff")
        self.disk_name = disk_name  
        
        self.active_history = [0] * 50
        self.transfer_history = [[0.0, 0.0] for _ in range(50)]
        self.global_grid_offset = 0
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) 
        self.grid_rowconfigure(1, weight=0) 
        self.grid_rowconfigure(2, weight=1) 
        self.grid_rowconfigure(3, weight=0) 
        self.grid_rowconfigure(4, weight=1) 
        self.grid_rowconfigure(5, weight=0) 
        
        self.setup_ui()
        
    def setup_ui(self):
        # HÀNG 0: HEADER DISK
        header_frame = tk.Frame(self, bg="#ffffff")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))
        
        lbl_title = tk.Label(header_frame, text="Disk", font=("", 28), bg="#ffffff", fg="#000000")
        lbl_title.pack(side="left", anchor="s")
        
        self.lbl_disk_model = tk.Label(header_frame, text=self.disk_name, font=("", 14), bg="#ffffff", fg="#555555")
        self.lbl_disk_model.pack(side="right", anchor="s", pady=5)
        
        # HÀNG 1: CHỮ PHỤ ACTIVE TIME
        lbl_sub1 = tk.Label(self, text="Active time", font=("", 9), bg="#ffffff", fg="#555555")
        lbl_sub1.grid(row=1, column=0, sticky="w", padx=20, pady=(5, 0))
        
        # HÀNG 2: BIỂU ĐỒ 1 (ACTIVE TIME)
        self.container_graph1 = tk.Frame(self, bg="#ffffff")
        self.container_graph1.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        self.container_graph1.grid_columnconfigure(0, weight=1)
        self.container_graph1.grid_rowconfigure(0, weight=1)
        
        self.graph_active = CpuGraphCanvas(
            self.container_graph1, click_callback=lambda: None, history_data=self.active_history,
            is_logical=False, face_color="#F4F8F1", edge_color="#7A9A60"
        )
        self.graph_active.grid(row=0, column=0, sticky="nsew")
        
        # HÀNG 3: TIÊU ĐỀ TRANSFER RATE + PEAK LABEL BÊN PHẢI
        transfer_title_frame = tk.Frame(self, bg="#ffffff")
        transfer_title_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(5, 0))
        
        lbl_sub2 = tk.Label(transfer_title_frame, text="Transfer rate", font=("", 9), bg="#ffffff", fg="#555555")
        lbl_sub2.pack(side="left")
        
        self.lbl_transfer_peak = tk.Label(transfer_title_frame, text="0 KB/s", font=("", 9), bg="#ffffff", fg="#555555")
        self.lbl_transfer_peak.pack(side="right")
        
        # HÀNG 4: BIỂU ĐỒ 2 (TRANSFER RATE ĐỌC/GHI)
        self.container_graph2 = tk.Frame(self, bg="#ffffff")
        self.container_graph2.grid(row=4, column=0, sticky="nsew", padx=20, pady=5)
        self.container_graph2.grid_columnconfigure(0, weight=1)
        self.container_graph2.grid_rowconfigure(0, weight=1)
        
        self.graph_transfer = CpuGraphCanvas(
            self.container_graph2, click_callback=lambda: None, history_data=self.transfer_history,
            is_logical=False, face_color="#F4F8F1", edge_color="#7A9A60", is_disk_transfer=True
        )
        self.graph_transfer.grid(row=0, column=0, sticky="nsew")
        
        # ----------------------------------------------------------------------
        # 🛠️ HÀNG 5: KHỐI THÔNG TIN ĐÁY CHUẨN WINDOWS (CHIA ĐỀU CỘT PAD=20PX)
        # ----------------------------------------------------------------------
        self.stats_frame = tk.Frame(self, bg="#ffffff")
        self.stats_frame.grid(row=5, column=0, sticky="ew", padx=(24, 0), pady=(10, 15))
        
        # Thiết lập 4 cột dãn cách bằng nhau tăm tắp
        self.stats_frame.grid_columnconfigure(0, minsize=130, weight=0, pad=20)
        self.stats_frame.grid_columnconfigure(1, minsize=130, weight=0, pad=20)
        self.stats_frame.grid_columnconfigure(2, minsize=130, weight=1, pad=20)
        
        # CỘT 0: Active time & Average response time
        tk.Label(self.stats_frame, text="Active time", font=("", 8), bg="#ffffff", fg="#555555", anchor="w").grid(row=0, column=0, sticky="sw")
        self.lbl_active_val = tk.Label(self.stats_frame, text="0%", font=("", 14), bg="#ffffff", anchor="w")
        self.lbl_active_val.grid(row=1, column=0, sticky="nw", pady=(0, 5))
        tk.Label(self.stats_frame, text="Average response time", font=("", 8), bg="#ffffff", fg="#555555", anchor="w").grid(row=0, column=1, sticky="sw")
        self.lbl_response_val = tk.Label(self.stats_frame, text="0.0 ms", font=("", 14), bg="#ffffff", anchor="w")
        self.lbl_response_val.grid(row=1, column=1, sticky="nw")
        
        # CỘT 1: Read speed & Capacity
        self.canvas_read_box = tk.Canvas(self.stats_frame, bg="#ffffff", highlightthickness=0, width=120, height=60)
        self.canvas_read_box.grid(row=2, column=0, rowspan=2, sticky="nsew", pady=(0, 5))
        self.canvas_read_box.pack_propagate(False)
        self.canvas_read_box.create_line(2, 2, 2, 50, fill="#7A9A60", width=2)
        lbl_read_title = tk.Label(self.canvas_read_box, text="Read speed", font=("", 8), bg="#ffffff", fg="#555555")
        lbl_read_title.place(x=12, y=2)
        self.lbl_read_val = tk.Label(self.canvas_read_box, text="0 KB/s", font=("", 14), bg="#ffffff", fg="#000000")
        self.lbl_read_val.place(x=12, y=20)
        tk.Label(self.stats_frame, text="Capacity:", font=("", 9), bg="#ffffff", fg="#555555", anchor="w").grid(row=2, column=1, sticky="sw", pady=(5, 0))
        self.lbl_capacity_val = tk.Label(self.stats_frame, text="0 GB", font=("", 9, "bold"), bg="#ffffff", anchor="w")
        self.lbl_capacity_val.grid(row=2, column=1, sticky="nw", padx=(65, 0), pady=(5, 0))
        self.canvas_write_box = tk.Canvas(self.stats_frame, bg="#ffffff", highlightthickness=0, width=120, height=60)
        self.canvas_write_box.grid(row=2, column=1, rowspan=2, sticky="nsew", pady=(0, 5))
        self.canvas_write_box.pack_propagate(False)
        self.canvas_write_box.create_line(2, 2, 2, 50, fill="#7A9A60", width=2, dash=(3, 2))
        lbl_write_title = tk.Label(self.canvas_write_box, text="Write speed", font=("", 8), bg="#ffffff", fg="#555555")
        lbl_write_title.place(x=12, y=2)
        self.lbl_write_val = tk.Label(self.canvas_write_box, text="0 KB/s", font=("", 14), bg="#ffffff", fg="#000000")
        self.lbl_write_val.place(x=12, y=20)
        
        
        self.col4_sub_frame = tk.Frame(self.stats_frame, bg="#ffffff")
        self.col4_sub_frame.grid(row=0, column=2, rowspan=6, sticky="nw", padx=(20, 0))
        tk.Label(self.col4_sub_frame, text="Form factor:", font=("", 9), bg="#ffffff", fg="#555555", anchor="w").grid(row=0, column=0, sticky="sw")
        self.lbl_form_val = tk.Label(self.col4_sub_frame, text="form_factor_str" if "nvme" in self.disk_name.lower() else "SSD/HDD", font=("Calibri", 9), bg="#ffffff", anchor="w")
        self.lbl_form_val.grid(row=0, column=1, sticky="nw", padx=(70, 0))

        tk.Label(self.col4_sub_frame, text="Capacity:", font=("", 9), bg="#ffffff", fg="#555555", anchor="w").grid(row=1, column=0, sticky="sw")
        self.lbl_capacity_val = tk.Label(self.col4_sub_frame, text="0 GB", font=("", 9), bg="#ffffff", anchor="w")
        self.lbl_capacity_val.grid(row=1, column=1, sticky="nw", padx=(70, 0))
        
        tk.Label(self.col4_sub_frame, text="System disk:", font=("", 9), bg="#ffffff", fg="#555555", anchor="w").grid(row=2, column=0, sticky="sw")
        self.lbl_system_val = tk.Label(self.col4_sub_frame, text="No", font=("", 9), bg="#ffffff", anchor="w")
        self.lbl_system_val.grid(row=2, column=1, sticky="nw", padx=(70, 0))
        tk.Label(self.col4_sub_frame, text="Partitions:", font=("", 9), bg="#ffffff", fg="#555555", anchor="w").grid(row=3, column=0, sticky="sw")
        self.lbl_partitions_val = tk.Label(self.col4_sub_frame, text="--", font=("", 9), bg="#ffffff", fg="#0078d4", anchor="w") # Màu xanh nhạt cho phân vùng bắt mắt
        self.lbl_partitions_val.grid(row=3, column=1, sticky="nw", padx=(70, 0))

    def receive_central_disk_data(self, active_pct, read_speed_mbs, write_speed_mbs, total_speed_mbs, 
                                 avg_response_ms, capacity_str, model_str, is_system_disk, partitions_str, form_factor_str, current_offset):
        """Hàm nhận dữ liệu nâng cao được phân phối từ main.py"""
        self.lbl_form_val.config(text=form_factor_str)
        # 1. Đồ thị % Active Time
        self.active_history.pop(0)
        self.active_history.append(active_pct)
        self.lbl_active_val.config(text=f"{int(active_pct)}%")
        
        # 2. Đồ thị Tốc độ Đọc Ghi
        self.transfer_history.pop(0)
        self.transfer_history.append([read_speed_mbs, write_speed_mbs])
        
        # 3. Cập nhật các ô số liệu lớn hàng trên
        self.lbl_read_val.config(text=f"{read_speed_mbs:.1f} MB/s" if read_speed_mbs >= 1.0 else f"{read_speed_mbs*1024:.0f} KB/s")
        self.lbl_write_val.config(text=f"{write_speed_mbs:.1f} MB/s" if write_speed_mbs >= 1.0 else f"{write_speed_mbs*1024:.0f} KB/s")
        
        # 4. 🛠️ CẬP NHẬT CÁC THÔNG SỐ NÂNG CAO MỚI
        self.lbl_response_val.config(text=f"{avg_response_ms:.1f} ms" if avg_response_ms > 0 else "0.0 ms")
        self.lbl_capacity_val.config(text=capacity_str)
        self.lbl_system_val.config(text=is_system_disk)
        self.lbl_partitions_val.config(text=partitions_str)
        self.lbl_disk_model.config(text=model_str)
        # 5. Làm mới đồ thị và cuộn lưới nền
        self.global_grid_offset = current_offset
        self.graph_active.update_graph_only(self.global_grid_offset)
        self.graph_transfer.update_graph_only(self.global_grid_offset)
        
        # 6. Đổ chữ nice_max vào góc phải cùng hàng
        nice_max = self.graph_transfer.peak_val
        if nice_max >= 1000.0:
            peak_str = f"{nice_max/1024:.1f} GB/s" if nice_max % 1024 != 0 else f"{int(nice_max/1024)} GB/s"
        elif nice_max >= 1.0:
            peak_str = f"{int(nice_max)} MB/s"
        else:
            peak_str = f"{int(nice_max * 1024)} KB/s"
        self.lbl_transfer_peak.config(text=peak_str)