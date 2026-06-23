import tkinter as tk
import numpy as np
from CpuDetailView import CpuGraphCanvas

class GpuDetailView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ffffff")
        
        # Khởi tạo các mảng lịch sử lưu dữ liệu cuộn động cho 5 đồ thị (mặc định 50 phần tử bằng 0)
        self.history_3d = [0] * 50
        self.history_copy = [0] * 50
        self.history_decode = [0] * 50
        self.history_processing = [0] * 50
        self.history_dedicated = [0] * 50
        self.history_shared = [0] * 50
        
        self.global_grid_offset = 0
        
        # Cấu hình lưới chính cho trang GPU View
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Khung chứa 4 đồ thị nhỏ phía trên (Grid 2x2)
        self.grid_rowconfigure(2, weight=1)  # Đồ thị Dedicated Memory trải dài
        self.grid_rowconfigure(3, weight=1)  # Đồ thị Shared Memory trải dài
        self.grid_rowconfigure(4, weight=0)  # Khung thông số đáy (Stats frame)
        
        self.setup_ui()
        
    def setup_ui(self):
        # ----------------------------------------------------------------------
        # HÀNG 0: HEADER GPU
        # ----------------------------------------------------------------------
        header_frame = tk.Frame(self, bg="#ffffff")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))
        
        lbl_title = tk.Label(header_frame, text="GPU", font=("Calibri Light", 28), bg="#ffffff", fg="#000000")
        lbl_title.pack(side="left", anchor="s")
        
        self.lbl_gpu_model = tk.Label(header_frame, text="NVIDIA GeForce / AMD Radeon", font=("Calibri Light", 14), bg="#ffffff", fg="#555555")
        self.lbl_gpu_model.pack(side="right", anchor="s", pady=5)
        
        # ----------------------------------------------------------------------
        # HÀNG 1: KHUNG 4 ĐỒ THỊ NHỎ PHÍA TRÊN (ENGINE UTILIZATION)
        # ----------------------------------------------------------------------
        top_engines_frame = tk.Frame(self, bg="#ffffff")
        top_engines_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        
        # Chia khung 2 hàng x 2 cột bằng nhau
        top_engines_frame.grid_columnconfigure(0, weight=1, uniform="top_grid")
        top_engines_frame.grid_columnconfigure(1, weight=1, uniform="top_grid")
        top_engines_frame.grid_rowconfigure(0, weight=1)
        top_engines_frame.grid_rowconfigure(1, weight=1)
        
        # Ô 1: 3D
        f_3d = tk.Frame(top_engines_frame, bg="#ffffff")
        f_3d.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        tk.Label(f_3d, text="3D", font=("Calibri", 9), bg="#ffffff", fg="#555555").pack(anchor="w")
        self.graph_3d = CpuGraphCanvas(f_3d, click_callback=lambda: None, history_data=self.history_3d, is_logical=False, face_color="#F4E9DD", edge_color="#C4996E")
        self.graph_3d.pack(fill="both", expand=True)
        
        # Ô 2: Copy
        f_copy = tk.Frame(top_engines_frame, bg="#ffffff")
        f_copy.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        tk.Label(f_copy, text="Compute / CUDA", font=("Calibri", 9), bg="#ffffff", fg="#555555").pack(anchor="w")
        self.graph_copy = CpuGraphCanvas(f_copy, click_callback=lambda: None, history_data=self.history_copy, is_logical=False, face_color="#F4E9DD", edge_color="#C4996E")
        self.graph_copy.pack(fill="both", expand=True)
        
        # Ô 3: Video Decode
        f_decode = tk.Frame(top_engines_frame, bg="#ffffff")
        f_decode.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        tk.Label(f_decode, text="Video Decode", font=("Calibri", 9), bg="#ffffff", fg="#555555").pack(anchor="w")
        self.graph_decode = CpuGraphCanvas(f_decode, click_callback=lambda: None, history_data=self.history_decode, is_logical=False, face_color="#F4E9DD", edge_color="#C4996E")
        self.graph_decode.pack(fill="both", expand=True)
        
        # Ô 4: Video Processing (Đơn giản hóa thay cho Video Processing phụ)
        f_proc = tk.Frame(top_engines_frame, bg="#ffffff")
        f_proc.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        tk.Label(f_proc, text="Video Encode", font=("Calibri", 9), bg="#ffffff", fg="#555555").pack(anchor="w")
        self.graph_processing = CpuGraphCanvas(f_proc, click_callback=lambda: None, history_data=self.history_processing, is_logical=False, face_color="#F4E9DD", edge_color="#C4996E")
        self.graph_processing.pack(fill="both", expand=True)
        
        # ----------------------------------------------------------------------
        # HÀNG 2: ĐỒ THỊ 5 (DEDICATED GPU MEMORY - TRẢI DÀI HÀNG NGANG)
        # ----------------------------------------------------------------------
        f_ded_mem = tk.Frame(self, bg="#ffffff")
        f_ded_mem.grid(row=2, column=0, sticky="nsew", padx=18, pady=5)
        
        lbl_ded_title = tk.Label(f_ded_mem, text="Dedicated GPU Memory Usage", font=("Calibri", 9), bg="#ffffff", fg="#555555")
        lbl_ded_title.pack(anchor="w")
        
        self.graph_dedicated = CpuGraphCanvas(f_ded_mem, click_callback=lambda: None, history_data=self.history_dedicated, is_logical=False, face_color="#F4E9DD", edge_color="#C4996E")
        self.graph_dedicated.pack(fill="both", expand=True)
        
        # ----------------------------------------------------------------------
        # HÀNG 3: ĐỒ THỊ 6 (SHARED GPU MEMORY - TRẢI DÀI HÀNG NGANG)
        # ----------------------------------------------------------------------
        f_shr_mem = tk.Frame(self, bg="#ffffff")
        f_shr_mem.grid(row=3, column=0, sticky="nsew", padx=20, pady=5)
        
        lbl_shr_title = tk.Label(f_shr_mem, text="Shared GPU Memory Usage", font=("Calibri", 9), bg="#ffffff", fg="#555555")
        lbl_shr_title.pack(anchor="w")
        
        self.graph_shared = CpuGraphCanvas(f_shr_mem, click_callback=lambda: None, history_data=self.history_shared, is_logical=False, face_color="#F4E9DD", edge_color="#C4996E")
        self.graph_shared.pack(fill="both", expand=True)
        
        # ----------------------------------------------------------------------
        # HÀNG 4: KHỐI THÔNG SỐ ĐÁY CHUẨN (CHIA CỘT DÃN CÁCH PAD=20PX)
        # ----------------------------------------------------------------------
        self.stats_frame = tk.Frame(self, bg="#ffffff")
        self.stats_frame.grid(row=4, column=0, sticky="ew", padx=(24, 0), pady=(10, 15))
        
        self.stats_frame.grid_columnconfigure(0, minsize=130, weight=0, pad=20)
        self.stats_frame.grid_columnconfigure(1, minsize=130, weight=0, pad=20)
        self.stats_frame.grid_columnconfigure(2, minsize=130, weight=0, pad=20)
        self.stats_frame.grid_columnconfigure(3, minsize=180, weight=1)
        
        # CỘT 0: GPU Utilization
        tk.Label(self.stats_frame, text="GPU Utilization", font=("", 8), bg="#ffffff", fg="#555555", anchor="w").grid(row=0, column=0, sticky="sw")
        self.lbl_util_val = tk.Label(self.stats_frame, text="0%", font=("", 14), bg="#ffffff", anchor="w")
        self.lbl_util_val.grid(row=1, column=0, sticky="nw", pady=(0, 5))
        
        tk.Label(self.stats_frame, text="GPU Temperature", font=("", 8), bg="#ffffff", fg="#555555", anchor="w").grid(row=2, column=0, sticky="sw")
        self.lbl_temp_val = tk.Label(self.stats_frame, text="0 °C", font=("", 14), bg="#ffffff", anchor="w")
        self.lbl_temp_val.grid(row=3, column=0, sticky="nw")
        
        # CỘT 1: Dedicated GPU Memory Numbers
        tk.Label(self.stats_frame, text="Dedicated GPU Memory", font=("", 8), bg="#ffffff", fg="#555555", anchor="w").grid(row=0, column=1, sticky="sw")
        self.lbl_ded_val = tk.Label(self.stats_frame, text="0.0 / 0.0 GB", font=("", 14), bg="#ffffff", anchor="w")
        self.lbl_ded_val.grid(row=1, column=1, sticky="nw", pady=(0, 5))
        
        # CỘT 2: Shared GPU Memory Numbers
        tk.Label(self.stats_frame, text="Shared GPU Memory", font=("", 8), bg="#ffffff", fg="#555555", anchor="w").grid(row=0, column=2, sticky="sw")
        self.lbl_shared_val = tk.Label(self.stats_frame, text="0.0 / 0.0 GB", font=("", 14), bg="#ffffff", anchor="w")
        self.lbl_shared_val.grid(row=1, column=2, sticky="nw", pady=(0, 5))
        
        # CỘT 3: Thông số tĩnh bên phải
        self.col3_sub_frame = tk.Frame(self.stats_frame, bg="#ffffff")
        self.col3_sub_frame.grid(row=0, column=3, rowspan=4, sticky="nw", padx=(20, 0))
        
        tk.Label(self.col3_sub_frame, text="Driver version:", font=("", 9), bg="#ffffff", fg="#555555").grid(row=0, column=0, sticky="w")
        self.lbl_driver_val = tk.Label(self.col3_sub_frame, text="Loading...", font=("", 9), bg="#ffffff")
        self.lbl_driver_val.grid(row=0, column=1, sticky="w", padx=(60, 0))
        
        tk.Label(self.col3_sub_frame, text="Physical Location:", font=("", 9), bg="#ffffff", fg="#555555").grid(row=1, column=0, sticky="w")
        self.lbl_location_val = tk.Label(self.col3_sub_frame, text="PCI bus 1, device 0", font=("", 9), bg="#ffffff")
        self.lbl_location_val.grid(row=1, column=1, sticky="w", padx=(60, 0))

    def receive_central_gpu_data(self, util_3d, util_copy, util_decode, util_proc, ded_used, ded_total, shr_used, shr_total, temp, current_offset):
        """Hàm nhận và đẩy dữ liệu thật chu kỳ 1 giây vào 5 đồ thị nền"""
        # 1. Đẩy data vào mảng lịch sử cuộn động
        for hist, val in [
            (self.history_3d, util_3d), (self.history_copy, util_copy),
            (self.history_decode, util_decode), (self.history_processing, util_proc),
            (self.history_dedicated, (ded_used / ded_total * 100) if ded_total > 0 else 0),
            (self.history_shared, (shr_used / shr_total * 100) if shr_total > 0 else 0)
        ]:
            hist.pop(0)
            hist.append(val)
            
        # 2. Cập nhật nhãn chữ hiển thị số liệu lớn đáy
        self.lbl_util_val.config(text=f"{int(util_3d)}%")
        self.lbl_temp_val.config(text=f"{int(temp)} °C" if temp > 0 else "--")
        self.lbl_ded_val.config(text=f"{ded_used:.1f} / {ded_total:.1f} GB")
        self.lbl_shared_val.config(text=f"{shr_used:.1f} / {shr_total:.1f} GB")
        
        # 3. Kích hoạt vẽ lại 5 đồ thị đồng bộ lưới nền cuộn động
        for graph in [self.graph_3d, self.graph_copy, self.graph_decode, self.graph_processing, self.graph_dedicated, self.graph_shared]:
            graph.update_graph_only(current_offset)