import tkinter as tk
from tkinter import ttk
import psutil
import time
from CpuDetailView import CpuGraphCanvas  # Tái sử dụng lại Canvas đồ thị Matplotlib xịn của fen

class RamCompositionBar(tk.Canvas):
    """Thanh Progress Bar tự vẽ bằng Canvas, hỗ trợ chia nhiều khúc màu (Composition)"""
    def __init__(self, parent, height=100, bg="#e1e1e1"):
        # highlightthickness=0 để xóa viền đen mặc định của Canvas
        super().__init__(parent, height=height, bg=bg, highlightthickness=0)
        
        # Cấu hình màu sắc chuẩn phong cách Windows Task Manager
        self.color_in_use = "#73527E"      # Màu tím đậm (RAM ứng dụng dùng)
        self.color_cache = "#C3B1E1"       # Màu tím nhạt/xám (RAM làm bộ nhớ đệm Cache)
        
        # Bắt sự kiện thay đổi kích thước cửa sổ để thanh luôn tự co giãn rộng tràn viền (Responsive)
        self.bind("<Configure>", self.on_resize)
        self.pct_in_use = 0
        self.pct_cache = 0

    def update_composition(self, pct_in_use, pct_cache):
        """Hàm nhận phần trăm để vẽ lại các khúc màu"""
        self.pct_in_use = pct_in_use
        self.pct_cache = pct_cache
        self.redraw()

    def on_resize(self, event):
        # Mỗi lần kéo giãn cửa sổ thì vẽ lại để cập nhật độ rộng mới
        self.redraw()

    def redraw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 10: return # Tránh vẽ lỗi khi widget chưa map xong

        # Tính độ dài của từng khúc theo pixel dựa trên phần trăm
        w_in_use = (self.pct_in_use / 100) * w
        w_cache = (self.pct_cache / 100) * w

        # 1. Vẽ khúc RAM Đang dùng (In Use)
        if w_in_use > 0:
            self.create_rectangle(0, 0, w_in_use, h, fill=self.color_in_use, outline="")
            
        # 2. Vẽ khúc RAM Đệm (Cache) nối tiếp ngay sau khúc In Use
        if w_cache > 0:
            self.create_rectangle(w_in_use, 0, w_in_use + w_cache, h, fill=self.color_cache, outline="")
class RamDetailView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#ffffff")
        self.total_ram = psutil.virtual_memory().total
        self.ram_history = [0] * 50
        self.global_grid_offset = 0
        self.setup_ui()
        
    def setup_ui(self):
        # Hàng 0: Tiêu đề RAM
        header_frame = tk.Frame(self, bg="#ffffff")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))
        
        lbl_ram_title = tk.Label(header_frame, text="RAM", font=("Calibri Light", 28), bg="#ffffff", fg="#000000")
        lbl_ram_title.pack(side="left", anchor="s")
        
        # Lấy thông số RAM tổng (Ví dụ: 16.0 GB)
        self.lbl_ram_model = tk.Label(header_frame, text="-- GB", font=("Calibri Light", 14), bg="#ffffff", fg="#555555")
        self.lbl_ram_model.pack(side="right", anchor="s", pady=5)
        
        self.lbl_sub_title = tk.Label(self, text="Memory usage", font=("Calibri", 8), bg="#ffffff", fg="#555555")
        self.lbl_sub_title.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 0))

        # Hàng 2: Vùng chứa biểu đồ tổng RAM
        self.graph_container = tk.Frame(self, bg="#ffffff")
        self.graph_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        
        # Đóng vai trò cấu hình chia Grid cho View để đồ thị giãn hết chiều dọc
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)

        # Tạo đồ thị đơn duy nhất cho RAM (Khi click vào đồ thị RAM thì không làm gì nên truyền lambda trống)
        self.graph = CpuGraphCanvas(self.graph_container, click_callback=lambda: None, history_data=self.ram_history, is_logical=False, face_color="#FFE9FF",   # Màu nền miền tím nhạt mộng mơ
        edge_color="#73527E")
        self.graph.pack(fill="both", expand=True)

        # Hàng 3: Memory composition progress
        self.ram_bar = RamCompositionBar(self, height=30)
        self.ram_bar.grid(row=3, column=0, sticky="ew", padx=20, pady=(5, 15))

        # Hàng 4: Khối thông số chi tiết dưới đáy
        self.stats_frame = tk.Frame(self, bg="#ffffff")
        self.stats_frame.grid(row=4, column=0, sticky="ew", padx=(24, 0), pady=(0, 15))
        
        # 🛠️ CẢI TIẾN: Thêm thuộc tính pad=20 vào các cột chữ để tạo khoảng hở 20px giữa các cột
        self.stats_frame.grid_columnconfigure(0, minsize=110, weight=0, pad=20) # Cột Utilization, Processes
        self.stats_frame.grid_columnconfigure(1, minsize=110, weight=0, pad=20) # Cột Speed, Threads
        self.stats_frame.grid_columnconfigure(2, minsize=110, weight=0, pad=20) # Cột Handles
        self.stats_frame.grid_columnconfigure(3, minsize=150, weight=1)        # Cột Cache & Base speed bên phải cùng
        
        # --- CỘT 0 ---
        tk.Label(self.stats_frame, text="In use (Compressed)", font=("Calibri", 8), bg="#ffffff", fg="#555555", anchor="w").grid(row=0, column=0, sticky="sw")
        self.lbl_in_use = tk.Label(self.stats_frame, text="0.0 GB", font=("Calibri", 14), bg="#ffffff", anchor="w")
        self.lbl_in_use.grid(row=1, column=0, sticky="nw")
        
        tk.Label(self.stats_frame, text="Committed", font=("Calibri", 8), bg="#ffffff", fg="#555555", anchor="w").grid(row=2, column=0, sticky="sw", pady=(5, 0))
        self.lbl_committed = tk.Label(self.stats_frame, text="0.0/0.0 GB", font=("Calibri", 14), bg="#ffffff", anchor="w")
        self.lbl_committed.grid(row=3, column=0, sticky="nw")

        # --- CỘT 1 ---
        tk.Label(self.stats_frame, text="Available", font=("Calibri", 8), bg="#ffffff", fg="#555555", anchor="w").grid(row=0, column=1, sticky="sw")
        self.lbl_available = tk.Label(self.stats_frame, text="0.0 GB", font=("Calibri", 14), bg="#ffffff", anchor="w")
        self.lbl_available.grid(row=1, column=1, sticky="nw")
        
        tk.Label(self.stats_frame, text="Cached", font=("Calibri", 8), bg="#ffffff", fg="#555555", anchor="w").grid(row=2, column=1, sticky="sw", pady=(5, 0))
        self.lbl_cached = tk.Label(self.stats_frame, text="0.0 GB", font=("Calibri", 14), bg="#ffffff", anchor="w")
        self.lbl_cached.grid(row=3, column=1, sticky="nw")

        # --- CỘT 2 ---
        tk.Label(self.stats_frame, text="Paged pool", font=("Calibri", 8), bg="#ffffff", fg="#555555", anchor="w").grid(row=0, column=2, sticky="sw")
        self.lbl_paged = tk.Label(self.stats_frame, text="0.0 GB", font=("Calibri", 14), bg="#ffffff", anchor="w")
        self.lbl_paged.grid(row=1, column=2, sticky="nw")
        
        tk.Label(self.stats_frame, text="Non-paged pool", font=("Calibri", 8), bg="#ffffff", fg="#555555", anchor="w").grid(row=2, column=2, sticky="sw", pady=(5, 0))
        self.lbl_non_paged = tk.Label(self.stats_frame, text="0.0 GB", font=("Calibri", 14), bg="#ffffff", anchor="w")
        self.lbl_non_paged.grid(row=3, column=2, sticky="nw")

        # --- CỘT 3: CÁC THÔNG SỐ TĨNH/PHẦN CỨNG BÊN PHẢI ---
        self.col3_sub_frame = tk.Frame(self.stats_frame, bg="#ffffff")
        self.col3_sub_frame.grid(row=0, column=3, rowspan=4, sticky="nw", padx=(20, 0))
        
        tk.Label(self.col3_sub_frame, text="Speed:", font=("Calibri", 9), bg="#ffffff", fg="#555555").grid(row=0, column=0, sticky="w")
        tk.Label(self.col3_sub_frame, text="3200 MHz", font=("Calibri", 9), bg="#ffffff", fg="#000000").grid(row=0, column=1, sticky="w", padx=(15, 0))
        
        tk.Label(self.col3_sub_frame, text="Slots used:", font=("Calibri", 9), bg="#ffffff", fg="#555555").grid(row=1, column=0, sticky="w")
        tk.Label(self.col3_sub_frame, text="1 of 2", font=("Calibri", 9), bg="#ffffff", fg="#000000").grid(row=1, column=1, sticky="w", padx=(15, 0))

        tk.Label(self.col3_sub_frame, text="Form factor:", font=("Calibri", 9), bg="#ffffff", fg="#555555").grid(row=2, column=0, sticky="w")
        tk.Label(self.col3_sub_frame, text="DIMM", font=("Calibri", 9), bg="#ffffff", fg="#000000").grid(row=2, column=1, sticky="w", padx=(15, 0))

        tk.Label(self.col3_sub_frame, text="Hardware reserved:", font=("Calibri", 9), bg="#ffffff", fg="#555555").grid(row=3, column=0, sticky="w")
        self.lbl_hw_reserved = tk.Label(self.col3_sub_frame, text="0 MB", font=("Calibri", 9), bg="#ffffff", fg="#000000")
        self.lbl_hw_reserved.grid(row=3, column=1, sticky="w", padx=(15, 0))
    def receive_central_ram_data(self, ram_percent, pct_cache, in_use_gb, available_gb, cache_gb, 
                                 committed_str, paged_pool, non_paged_pool, 
                                 hardware_total_gb, ram_type, hardware_reserved_str, current_offset):
        self.ram_history.pop(0)
        self.ram_history.append(ram_percent)
        self.global_grid_offset = current_offset
        self.graph.update_graph_only(self.global_grid_offset)
        self.ram_bar.update_composition(ram_percent, pct_cache)
        self.lbl_ram_model.config(text=f"{ram_type}: {hardware_total_gb:.0f} GB")
        self.lbl_in_use.config(text=f"{in_use_gb:.1f} GB")
        self.lbl_available.config(text=f"{available_gb:.1f} GB")
        self.lbl_cached.config(text=f"{cache_gb:.1f} GB")
        self.lbl_committed.config(text=committed_str)
        self.lbl_paged.config(text=paged_pool)
        self.lbl_non_paged.config(text=non_paged_pool)
        self.lbl_hw_reserved.config(text=hardware_reserved_str)