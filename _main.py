import tkinter as tk
from tkinter import ttk
import psutil
import matplotlib
import matplotlib.font_manager as fm
matplotlib.font_manager = fm  
fm._load_fontmanager(try_read_cache=False)
import collections
import random
import time

# Import 3 phân hệ view chi tiết hoàn chỉnh
from CpuDetailView import CpuDetailView
from RamDetailView import RamDetailView
from DiskDetailView import DiskDetailView 

class SidebarItem(tk.Frame):
    def __init__(self, parent, icon_text, title_text, value_text, h, w, click_callback=None, disk_id=None):
        super().__init__(parent, bg="#ffffff", cursor="hand2")
        self.icon_text = icon_text
        self.title_text = title_text      # Tên hiển thị trên giao diện (Ví dụ: Disk 0)
        self.disk_id = disk_id            # Định danh đĩa vật lý ngầm hệ thống (Ví dụ: sda, nvme0n1)
        self.value_text = value_text
        self.graph_h = h
        self.graph_w = w
        self.click_callback = click_callback 
        
        self.data_history = [0] * 40
        self.setup_ui()
        
    def setup_ui(self):
        self.left_container = tk.Frame(self, bg="#ffffff", width=self.graph_w+10, height=self.graph_h+5)
        self.left_container.pack(side="left", padx=5, fill="y")
        self.left_container.pack_propagate(False)
        
        self.lbl_icon = tk.Label(self.left_container, text=self.icon_text, bg="#ffffff", fg="#363636", font=("Calibri", 14))
        self.lbl_icon.pack(expand=True)
        
        # Đồng bộ màu sắc đồ thị mini bên Sidebar theo chuẩn linh kiện Task Manager
        if "CPU" in self.title_text:
            self.graph_color_outline = "#0078d4"
            self.graph_color_domain = "#e6f0fa"
            self.graph_color_line = "#0078d4"
        elif "RAM" in self.title_text:
            self.graph_color_outline = "#73527E"
            self.graph_color_domain = "#FFE9FF"
            self.graph_color_line = "#73527E"
        elif "Disk" in self.title_text:
            self.graph_color_outline = "#7A9A60"
            self.graph_color_domain = "#F4F8F1"
            self.graph_color_line = "#7A9A60"
        elif "GPU" in self.title_text:
            self.graph_color_outline = "#C4996E"
            self.graph_color_domain = "#F4E9DD"
            self.graph_color_line = "#C4996E"
        elif "Ethernet" in self.title_text or "VPN" in self.title_text:
            self.graph_color_outline = "#272727"
            self.graph_color_domain = "#F0EFEE"
            self.graph_color_line = "#272727"
        else:
            self.graph_color_outline = "#7A9A60"
            self.graph_color_domain = "#F4F8F1"
            self.graph_color_line = "#7A9A60"
            
        self.canvas = tk.Canvas(self.left_container, bg="#ffffff", highlightthickness=1, highlightbackground=self.graph_color_outline, width=self.graph_w, height=self.graph_h)
        
        self.text_container = tk.Frame(self, bg="#ffffff")
        self.lbl_title = tk.Label(self.text_container, text=self.title_text, bg="#ffffff", fg="#000000", font=("Calibri Light", 12), anchor="w")
        self.lbl_title.pack(fill="x")
        
        self.lbl_value = tk.Label(self.text_container, text=self.value_text, bg="#ffffff", fg="#555555", font=("Calibri", 9), anchor="w")
        self.lbl_value.pack(fill="x")
        
        # Gán sự kiện đổi màu Hover
        self.bind("<Enter>", lambda e: self.set_hover_color("#f3f3f3"))
        self.bind("<Leave>", lambda e: self.set_hover_color("#ffffff"))
        
        if self.click_callback:
            self.bind("<Button-1>", lambda e: self.click_callback(self))
            self.left_container.bind("<Button-1>", lambda e: self.click_callback(self))
            self.text_container.bind("<Button-1>", lambda e: self.click_callback(self))
            self.lbl_icon.bind("<Button-1>", lambda e: self.click_callback(self))
            self.canvas.bind("<Button-1>", lambda e: self.click_callback(self))
            self.lbl_title.bind("<Button-1>", lambda e: self.click_callback(self))
            self.lbl_value.bind("<Button-1>", lambda e: self.click_callback(self))

        self.draw_mini_graph()

    def set_hover_color(self, color):
        self.config(bg=color)
        self.left_container.config(bg=color)
        self.text_container.config(bg=color)
        self.lbl_icon.config(bg=color)
        self.lbl_title.config(bg=color)
        self.lbl_value.config(bg=color)

    def update_real_data(self, new_val, display_text):
        self.data_history.pop(0)
        self.data_history.append(new_val)
        self.lbl_value.config(text=display_text)
        self.draw_mini_graph()

    def draw_mini_graph(self):
        self.canvas.delete("all")
        points = []
        w, h = self.graph_w, self.graph_h
        padding_top = 2
        padding_bottom = 2
        usable_h = h - padding_top - padding_bottom
        step = w / (len(self.data_history) - 1)
        
        for i, val in enumerate(self.data_history):
            x = i * step
            bounded_val = min(max(val, 0), 100)
            y = padding_top + (usable_h - (bounded_val / 100 * usable_h))
            points.append((x, y))  
            
        if len(points) > 1:
            polygon_points = [(0, h)] + points + [(w, h)]
            self.canvas.create_polygon(polygon_points, fill=self.graph_color_domain, outline="")
            self.canvas.create_line(points, fill=self.graph_color_line, width=1.0)

    def switch_mode(self, collapsed):
        if collapsed:
            self.text_container.pack_forget()
            self.canvas.pack_forget()
            self.lbl_icon.pack(expand=True)
            self.left_container.config(width=30)
        else:
            self.lbl_icon.pack_forget()
            self.left_container.config(width=self.graph_w)
            self.canvas.pack(pady=5, padx=2, expand=True)
            self.text_container.pack(side="left", fill="both", expand=True, padx=5)


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Custom Task Manager Pro")
        self.geometry("1020x650")
        self.minsize(500, 400)
        self.current_offset = 0
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar_frame = tk.Frame(self, bg="#ffffff")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.config(width=250)
        self.sidebar_frame.pack_propagate(False)
        self.sidebar_frame.grid_propagate(False)
        self.menu_items_container = tk.Frame(self.sidebar_frame, bg="#ffffff")
        self.menu_items_container.pack(fill="both", expand=True, padx=5)
        #CPU Zone
        self.items = []
        self.item_cpu = SidebarItem(self.menu_items_container, "⚙", "CPU", "0% 0.00 GHz", 40, 60, click_callback=self.handle_view_change)
        self.item_cpu.pack(fill="x", pady=5)
        self.items.append(self.item_cpu)
        #RAM Zone
        self.item_ram = SidebarItem(self.menu_items_container, "📊", "RAM", "0.0/0.0 GB (0%)", 40, 60, click_callback=self.handle_view_change)
        self.item_ram.pack(fill="x", pady=5)
        self.items.append(self.item_ram)
        #Disk Zone
        self.disk_io_keys = []
        self.disk_views = {}
        self.disk_sidebar_items = {}
        try:
            all_disks_io = psutil.disk_io_counters(perdisk=True)
            disk_idx = 0
            for d_name in sorted(all_disks_io.keys()):
                if d_name.startswith("loop") or d_name.startswith("ram"):
                    continue
                if "nvme" in d_name and "p" in d_name:
                    continue
                if d_name.startswith("sd") and d_name[-1].isdigit():
                    continue
                self.disk_io_keys.append(d_name)
                display_label = f"Disk {disk_idx}"
                item_disk = SidebarItem(self.menu_items_container, "💽", display_label, "0%", 40, 60, 
                                        click_callback=self.handle_view_change, disk_id=d_name)
                item_disk.pack(fill="x", pady=5)
                self.disk_sidebar_items[d_name] = item_disk
                self.items.append(item_disk)
                disk_idx += 1
        except Exception as e:
            print(f"Lỗi quét danh sách ổ đĩa: {e}")
        
        # ---- Cột chứa border 1px ----
        self.right_border = tk.Frame(self, bg="#CCCCCC", width=1)
        self.right_border.grid(row=0, column=1, sticky="nsew")

        # ---- Cột bên phải (Main Content) ----
        self.main_frame = tk.Frame(self, bg="#ffffff")
        self.main_frame.grid(row=0, column=2, sticky="nsew")

        self.cpu_view = CpuDetailView(self.main_frame)
        self.ram_view = RamDetailView(self.main_frame)
        
        # Tạo view chi tiết tương ứng cho từng ổ dựa vào định danh đĩa vật lý ngầm
        for d_name in self.disk_io_keys:
            self.disk_views[d_name] = DiskDetailView(self.main_frame, disk_name=d_name)
        
        self.cpu_view.pack(fill="both", expand=True)

        self.last_disk_io = psutil.disk_io_counters(perdisk=True)
        self.last_sync_time = time.time()
        #GPU Zone
        self.gpu_keys = []
        self.gpu_views = {}
        self.gpu_sidebar_items = {}
        detected_gpus = self.detect_all_gpus_on_startup()
        gpu_idx = 0
        for gpu_info in detected_gpus:
            g_id = gpu_info["id"]
            self.gpu_keys.append(g_id)
            display_label = f"GPU {gpu_idx}"
            
            # Tạo item trên Sidebar
            from GpuDetailView import GpuDetailView
            item_gpu = SidebarItem(self.menu_items_container, "📟", display_label, "0%", 40, 60, 
                                   click_callback=self.handle_view_change, disk_id=g_id) # Tái sử dụng disk_id làm id phần cứng ngầm
            item_gpu.pack(fill="x", pady=5)
            
            self.gpu_sidebar_items[g_id] = item_gpu
            self.items.append(item_gpu)
            
            # Khởi tạo trang View chi tiết 5 đồ thị cho từng GPU
            new_gpu_view = GpuDetailView(self.main_frame)
            new_gpu_view.lbl_gpu_model.config(text=gpu_info["model"]) # Đổ tên card thật lên header
            self.gpu_views[g_id] = new_gpu_view
            
            gpu_idx += 1
        #NET zone
        self.net_keys = []
        self.net_views = {}
        self.net_sidebar_items = {}
        
        # Lấy mốc dữ liệu I/O mạng đầu tiên để làm gốc tính toán tốc độ
        self.last_net_io = psutil.net_io_counters(pernic=True)
        
        # Quét các card mạng đang hoạt động (Bỏ loopback 'lo')
        active_nets = sorted([k for k in self.last_net_io.keys() if k != 'lo' and not k.startswith('veth')])
        
        # Tìm phần tử cuối cùng của GPU để làm mốc găm neo Sidebar (CPU > RAM > DISK > GPU > NET)
        last_gpu_anchor = list(self.gpu_sidebar_items.values())[-1] if self.gpu_sidebar_items else self.item_ram
        
        for n_name in active_nets:
            self.net_keys.append(n_name)
            display_label = "Ethernet"
            if "wlan" in n_name or "wlp" in n_name:
                display_label = "Wi-Fi"
            elif "ppp" in n_name or "tailscale" in n_name:
                display_label = "VPN"

            display_label = display_label + " (" + n_name + ")"
            from NetDetailView import NetDetailView
            item_net = SidebarItem(self.menu_items_container, "🌐", display_label, "0 Kbps", 40, 60, 
                                   click_callback=self.handle_view_change, disk_id=n_name)
            item_net.pack(fill="x", pady=5, after=last_gpu_anchor)
            last_gpu_anchor = item_net
            
            self.net_sidebar_items[n_name] = item_net
            self.items.append(item_net)
            
            # Tạo view chi tiết
            self.net_views[n_name] = NetDetailView(self.main_frame, net_name=n_name)
        self.is_collapsed = False
        for item in self.items:
            item.switch_mode(collapsed=False)
            
        self.bind("<Configure>", self.on_resize)
        
        self.global_sync_loop()
    def handle_view_change(self, clicked_item):
        self.cpu_view.pack_forget()
        self.ram_view.pack_forget()
        for dv in self.disk_views.values(): dv.pack_forget()
        for gv in self.gpu_views.values(): gv.pack_forget()
        for nv in self.net_views.values(): nv.pack_forget()
        target_title = clicked_item.title_text
        if target_title == "CPU":
            self.cpu_view.pack(fill="both", expand=True)
        elif target_title == "RAM":
            self.ram_view.pack(fill="both", expand=True)
        else:
            hw_id = clicked_item.disk_id
            if hw_id in self.disk_views:
                self.disk_views[hw_id].pack(fill="both", expand=True)
            elif hw_id in self.gpu_views:
                self.gpu_views[hw_id].pack(fill="both", expand=True)
            elif hw_id in self.net_views:
                self.net_views[hw_id].pack(fill="both", expand=True)
    def global_sync_loop(self):
        self.current_offset = (self.current_offset + 1) % 10
        now_time = time.time()
        time_delta = now_time - self.last_sync_time
        if time_delta <= 0: time_delta = 1.0
        
        # --- 1. ĐỒNG BỘ CPU ---
        current_cpu_pct = psutil.cpu_percent(interval=None)
        freq = psutil.cpu_freq()
        current_speed = round(freq.current / 1000, 2) if freq else 3.20
        self.item_cpu.update_real_data(current_cpu_pct, f"{int(current_cpu_pct)}%  {current_speed} GHz")
        self.cpu_view.receive_central_cpu_data(current_cpu_pct, current_speed)
        
        # --- 2. ĐỒNG BỘ RAM ---
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        ram_percent = mem.percent
        in_use_gb = mem.used / (1024**3)
        available_gb = mem.available / (1024**3)
        
        total_raw_gb = mem.total / (1024**3)
        standard_sizes = [2, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 256]
        hardware_total_gb = min(standard_sizes, key=lambda x: abs(x - total_raw_gb))
        if hardware_total_gb < total_raw_gb: hardware_total_gb = round(total_raw_gb, 1)
        
        ram_type = "DDR4"
        try:
            import os
            if os.getuid() == 0: 
                import subprocess
                proc = subprocess.Popen("dmidecode -t memory".split(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                stdout, _ = proc.communicate()
                for line in stdout.split('\n'):
                    if "Type:" in line and "Detail" not in line:
                        type_str = line.split(":")[1].strip()
                        if type_str in ["DDR3", "DDR4", "DDR5", "LPDDR4"]:
                            ram_type = type_str
                            break
        except: pass

        cache_bytes = (mem.buffers + mem.cached) if hasattr(mem, 'buffers') else 0
        pct_cache = (cache_bytes / mem.total) * 100
        cache_gb = cache_bytes / (1024**3)
        committed_str = f"{(mem.used + swap.used)/(1024**3):.1f}/{(mem.total + swap.total)/(1024**3):.1f} GB"
        
        paged_pool_gb, non_paged_pool_gb = "N/A", "N/A"
        try:
            with open("/proc/meminfo", "r") as f:
                s_rec, s_unrec = 0, 0
                for line in f:
                    if line.startswith("SReclaimable:"): s_rec = int(line.split()[1]) * 1024
                    elif line.startswith("SUnreclaim:"): s_unrec = int(line.split()[1]) * 1024
                if s_rec > 0: paged_pool_gb = f"{s_rec / (1024**3):.1f} GB"
                if s_unrec > 0: non_paged_pool_gb = f"{s_unrec / (1024**3):.1f} GB"
        except: pass

        hardware_reserved_mb = int((hardware_total_gb - total_raw_gb) * 1024)
        if hardware_reserved_mb < 0: hardware_reserved_mb = 0
        hardware_reserved_str = f"{hardware_reserved_mb} MB" if hardware_reserved_mb > 0 else "0 MB"

        self.item_ram.update_real_data(ram_percent, f"{in_use_gb:.1f}/{hardware_total_gb:.0f} GB ({int(ram_percent)}%)")
        self.ram_view.receive_central_ram_data(ram_percent, pct_cache, in_use_gb, available_gb, cache_gb, committed_str, paged_pool_gb, non_paged_pool_gb, hardware_total_gb, ram_type, hardware_reserved_str, self.current_offset)
        try:
            current_raw_disks = psutil.disk_io_counters(perdisk=True)
            active_disks = []
            for k in current_raw_disks.keys():
                if k.startswith("loop") or k.startswith("ram"): continue
                if "nvme" in k and "p" in k: continue
                if k.startswith("sd") and k[-1].isdigit(): continue
                active_disks.append(k)
            
            active_disks = sorted(active_disks)
            
            # Nếu phát hiện có sự thay đổi (Cắm thêm hoặc rút ra)
            if active_disks != sorted(self.disk_io_keys):
                
                # TRƯỜNG HỢP 1: RÚT Ổ ĐĨA RA
                for d_name in list(self.disk_io_keys):
                    if d_name not in active_disks:
                        print(f"🔌 Phát hiện ổ đĩa bị rút ra: {d_name}")
                        # Kiểm tra nếu đang xem chính ổ đĩa bị rút này thì chuyển view về CPU chống trắng màn hình
                        if d_name in self.disk_views and self.disk_views[d_name].winfo_manager():
                            self.cpu_view.pack(fill="both", expand=True)
                        
                        # Hủy widget chi tiết bên phải
                        if d_name in self.disk_views:
                            self.disk_views[d_name].destroy()
                            del self.disk_views[d_name]
                        
                        # Hủy mục hiển thị trên Sidebar
                        if d_name in self.disk_sidebar_items:
                            item = self.disk_sidebar_items[d_name]
                            if item in self.items:
                                self.items.remove(item)
                            item.destroy()
                            del self.disk_sidebar_items[d_name]

                # TRƯỜNG HỢP 2: CẮM Ổ ĐĨA VÀO
                for d_name in active_disks:
                    if d_name not in self.disk_io_keys:
                        print(f"🔌 Phát hiện ổ đĩa mới được cắm vào: {d_name}")
                        
                        # Tạo view chi tiết mới găm vào main_frame (ẩn ngầm)
                        from DiskDetailView import DiskDetailView
                        self.disk_views[d_name] = DiskDetailView(self.main_frame, disk_name=d_name)
                        
                        # Khởi tạo item Sidebar mới
                        item_disk = SidebarItem(self.menu_items_container, "💽", "Disk TEMP", "0%", 40, 60, 
                                                click_callback=self.handle_view_change, disk_id=d_name)
                        self.disk_sidebar_items[d_name] = item_disk
                        self.items.append(item_disk)
                        
                        # Đồng bộ trạng thái co giãn của Sidebar
                        item_disk.switch_mode(collapsed=self.is_collapsed)

                # CẬP NHẬT LẠI BIẾN QUẢN LÝ ĐĨA HỆ THỐNG
                self.disk_io_keys = active_disks
                
                # SẮP XẾP VÀ ĐỊNH VỊ LẠI VỊ TRÍ HIỂN THỊ TRÊN SIDEBAR (CPU > RAM > DISK 0 > DISK 1 > ...)
                # Đầu tiên gỡ tạm pack của toàn bộ các đĩa hiện có ra
                for d_name in self.disk_io_keys:
                    self.disk_sidebar_items[d_name].pack_forget()
                
                # Tiến hành pack lại theo đúng thứ tự mảng đã sắp xếp, găm ngay sau thanh RAM
                last_anchor = self.item_ram
                for idx, d_name in enumerate(self.disk_io_keys):
                    # Đổi lại tên hiển thị chuẩn số thứ tự tăng dần (Disk 0, Disk 1...)
                    self.disk_sidebar_items[d_name].lbl_title.config(text=f"Disk {idx}")
                    self.disk_sidebar_items[d_name].title_text = f"Disk {idx}"
                    
                    # Chèn khít ngay sau mục trước đó bằng thuộc tính after
                    self.disk_sidebar_items[d_name].pack(fill="x", pady=5, after=last_anchor)
                    last_anchor = self.disk_sidebar_items[d_name] # Dịch mốc neo xuống dưới cho đĩa kế tiếp

                self.menu_items_container.update()
                print("✅ Cập nhật cục bộ danh sách ổ đĩa thành công!")
                
                self.last_sync_time = now_time
                self.after(1000, self.global_sync_loop)
                return
        except Exception as e:
            print(f"Lỗi xử lý tháo lắp cục bộ ổ đĩa: {e}")
        try:
            current_disk_io = psutil.disk_io_counters(perdisk=True)
            
            # Khảo sát nhanh xem phân vùng root "/" đang nằm trên thiết bị nào để tìm System Disk
            root_device = ""
            for part in psutil.disk_partitions():
                if part.mountpoint == '/':
                    root_device = part.device # Ví dụ: /dev/nvme0n1p2 hoặc /dev/sda2
                    break

            for d_name in self.disk_io_keys:
                if d_name in current_disk_io and d_name in self.last_disk_io:
                    io_old = self.last_disk_io[d_name]
                    io_new = current_disk_io[d_name]
                    
                    # Tính toán tốc độ đọc ghi (MB/s) và % Active time
                    read_speed_mbs = ((io_new.read_bytes - io_old.read_bytes) / (1024**2)) / time_delta
                    write_speed_mbs = ((io_new.write_bytes - io_old.write_bytes) / (1024**2)) / time_delta
                    total_speed_mbs = read_speed_mbs + write_speed_mbs
                    
                    busy_delta_ms = io_new.busy_time - io_old.busy_time
                    active_pct = (busy_delta_ms / (time_delta * 1000)) * 100
                    active_pct = min(max(active_pct, 0), 100)
                    
                    ops_delta = (io_new.read_count + io_new.write_count) - (io_old.read_count + io_old.write_count)
                    time_spent_delta = (io_new.read_time + io_new.write_time) - (io_old.read_time + io_old.write_time)
                    avg_response_ms = time_spent_delta / ops_delta if ops_delta > 0 else 0.0
                    
                    # 1. LẤY DUNG LƯỢNG VẬT LÝ (CAPACITY)
                    capacity_str = "N/A"
                    try:
                        sys_path = f"/sys/block/{d_name}/size"
                        if os.path.exists(sys_path):
                            with open(sys_path, "r") as f_sz:
                                sectors = int(f_sz.read().strip())
                                capacity_str = f"{(sectors * 512) / (1024**3):.1f} GB"
                    except: pass
                    
                    # 2. 🛠️ LẤY MODEL Ổ CỨNG THẬT TỪ KERNEL LINUX
                    model_str = d_name.upper() # Fallback mặc định
                    try:
                        model_path = f"/sys/block/{d_name}/device/model"
                        if os.path.exists(model_path):
                            with open(model_path, "r") as f_md:
                                model_str = f_md.read().strip()
                    except: pass

                    # 3. 🛠️ KIỂM TRA SYSTEM DISK THẬT
                    is_system_disk = "No"
                    if root_device and d_name in root_device:
                        is_system_disk = "Yes"

                    # 4. 🛠️ QUÉT DANH SÁCH CÁC PHÂN VÙNG CON
                    sub_parts = []
                    for k in sorted(current_disk_io.keys()):
                        if k == d_name:
                            continue
                        # Lọc phân vùng con: nvme0n1pX thuộc nvme0n1, hoặc sdaX thuộc sda
                        if ("nvme" in d_name and d_name in k and "p" in k) or (d_name.startswith("sd") and k.startswith(d_name)):
                            sub_parts.append(k)
                    partitions_str = ", ".join(sub_parts) if sub_parts else "None"
                    form_factor = "SSD/HDD"
                    if "nvme" in d_name.lower():
                        form_factor = "NVMe"
                    else:
                        try:
                            removable_path = f"/sys/block/{d_name}/removable"
                            if os.path.exists(removable_path):
                                with open(removable_path, "r") as f_rm:
                                    if f_rm.read().strip() == "1":
                                        form_factor = "USB / Removable"
                        except:
                            pass
                    # Cập nhật hiển thị Sidebar
                    sidebar_text = f"{int(active_pct)}%" if active_pct > 0 else "0%"
                    self.disk_sidebar_items[d_name].update_real_data(active_pct, sidebar_text)
                    self.disk_views[d_name].receive_central_disk_data(
                        active_pct=active_pct, 
                        read_speed_mbs=read_speed_mbs, 
                        write_speed_mbs=write_speed_mbs, 
                        total_speed_mbs=total_speed_mbs,
                        avg_response_ms=avg_response_ms,
                        capacity_str=capacity_str,
                        model_str=model_str,
                        is_system_disk=is_system_disk,
                        partitions_str=partitions_str,
                        form_factor_str=form_factor,
                        current_offset=self.current_offset
                    )
            
            self.last_disk_io = current_disk_io
        except Exception as e:
            print(f"Lỗi đồng bộ dữ liệu đĩa: {e}")
        try:
            for g_id in self.gpu_keys:
                # Quét lấy chỉ số sống thời gian thực của GPU tương ứng
                g_data = self.query_live_gpu_data(g_id)
                
                # Cập nhật thông số % tải lên Sidebar Item tương ứng
                sidebar_display_text = f"{int(g_data['util_3d'])}%"
                self.gpu_sidebar_items[g_id].update_real_data(g_data['util_3d'], sidebar_display_text)
                
                # Bắn gói dữ liệu đa đồ thị sang trang chi tiết GpuDetailView.py
                self.gpu_views[g_id].receive_central_gpu_data(
                    util_3d=g_data["util_3d"],
                    util_copy=g_data["util_copy"],
                    util_decode=g_data["util_decode"],
                    util_proc=g_data["util_proc"],
                    ded_used=g_data["ded_used"],
                    ded_total=g_data["ded_total"],
                    shr_used=g_data["shr_used"],
                    shr_total=g_data["shr_total"],
                    temp=g_data["temp"],
                    current_offset=self.current_offset
                )
                # Đổ nốt Driver tĩnh lên giao diện nếu chưa được load
                if hasattr(self.gpu_views[g_id], 'lbl_driver_val'):
                    self.gpu_views[g_id].lbl_driver_val.config(text=g_data["driver"])
        except Exception as e:
            print(f"Lỗi đồng bộ dữ liệu đồ họa GPU: {e}")
        try:
            current_raw_nets = psutil.net_io_counters(pernic=True)
            live_nets = sorted([k for k in current_raw_nets.keys() if k != 'lo' and not k.startswith('veth')])
            
            if live_nets != sorted(self.net_keys):
                # TRƯỜNG HỢP RÚT CARD MẠNG
                for n_name in list(self.net_keys):
                    if n_name not in live_nets:
                        print(f"🔌 Rút card mạng: {n_name}")
                        if n_name in self.net_views and self.net_views[n_name].winfo_manager():
                            # Nếu đang xem card mạng bị rút -> Ưu tiên quay về card mạng còn lại
                            remains = [k for k in live_nets if k in self.net_views]
                            if remains:
                                self.net_views[remains[0]].pack(fill="both", expand=True)
                            elif self.gpu_keys: # Không còn mạng, nhảy về GPU
                                self.gpu_views[self.gpu_keys[-1]].pack(fill="both", expand=True)
                            else: # Không có GPU, nhảy về Disk
                                self.disk_views[self.disk_io_keys[-1]].pack(fill="both", expand=True)
                        
                        if n_name in self.net_views:
                            self.net_views[n_name].destroy()
                            del self.net_views[n_name]
                        if n_name in self.net_sidebar_items:
                            item = self.net_sidebar_items[n_name]
                            if item in self.items: self.items.remove(item)
                            item.destroy()
                            del self.net_sidebar_items[n_name]

                # TRƯỜNG HỢP CẮM THÊM CARD MẠNG (USB Wi-Fi)
                for n_name in live_nets:
                    if n_name not in self.net_keys:
                        print(f"🔌 Cắm thêm card mạng mới: {n_name}")
                        from NetDetailView import NetDetailView
                        self.net_views[n_name] = NetDetailView(self.main_frame, net_name=n_name)
                        
                        display_label = "Wi-Fi" if "wlan" in n_name or "wlp" in n_name else "Ethernet"
                        item_net = SidebarItem(self.menu_items_container, "🌐", display_label, "0 Kbps", 40, 60, 
                                               click_callback=self.handle_view_change, disk_id=n_name)
                        self.net_sidebar_items[n_name] = item_net
                        self.items.append(item_net)
                        item_net.switch_mode(collapsed=self.is_collapsed)

                self.net_keys = live_nets
                
                # Định vị sắp xếp lại vị trí neo chuẩn sau GPU
                for n_name in self.net_keys: self.net_sidebar_items[n_name].pack_forget()
                last_anchor = list(self.gpu_sidebar_items.values())[-1] if self.gpu_sidebar_items else self.item_ram
                for n_name in self.net_keys:
                    self.net_sidebar_items[n_name].pack(fill="x", pady=5, after=last_anchor)
                    last_anchor = self.net_sidebar_items[n_name]
                self.menu_items_container.update()

            # --- ĐỒNG BỘ DỮ LIỆU TỐC ĐỘ MẠNG THỜI GIAN THỰC ---
            time_delta = now_time - self.last_sync_time if (now_time - self.last_sync_time) > 0 else 1.0
            for n_name in self.net_keys:
                if n_name in current_raw_nets and n_name in self.last_net_io:
                    net_old = self.last_net_io[n_name]
                    net_new = current_raw_nets[n_name]
                    
                    # Tính toán tốc độ KB/s
                    send_speed_kbs = ((net_new.bytes_sent - net_old.bytes_sent) / 1024) / time_delta
                    recv_speed_kbs = ((net_new.bytes_recv - net_old.bytes_recv) / 1024) / time_delta
                    
                    # Cập nhật thông số tóm tắt lên Sidebar
                    total_bps = (send_speed_kbs + recv_speed_kbs) * 1024 * 8
                    sidebar_text = f"{total_bps/1000000:.1f} Mbps" if total_bps >= 1000000 else f"{total_bps/1000:.0f} Kbps"
                    self.net_sidebar_items[n_name].update_real_data(max(send_speed_kbs, recv_speed_kbs), sidebar_text)
                    
                    # 🛠️ LAZY RENDERING: Chỉ vẽ đồ thị lớn nếu đang mở xem tab mạng này
                    if self.net_views[n_name].winfo_manager():
                        self.net_views[n_name].receive_central_net_data(send_speed_kbs, recv_speed_kbs, self.current_offset)
            
            self.last_net_io = current_raw_nets
        except Exception as e:
            print(f"Lỗi đồng bộ phân hệ Network: {e}")
        self.last_sync_time = now_time
        self.after(1000, self.global_sync_loop)
    def reload_disk_sections(self):
        """Hàm tự động xóa các widget ổ đĩa cũ và dựng lại khi có sự kiện Tháo/Lắp"""
        print("🔄 Phát hiện thay đổi phần cứng: Đang reload lại danh sách ổ đĩa...")
        
        # 🛠️ LOGIC KIỂM TRA XEM TRANG ĐĨA NÀO ĐANG ĐƯỢC HIỂN THỊ TRƯỚC KHI HỦY
        active_disk_before_reload = None
        for d_name, view in self.disk_views.items():
            # info_manager() trả về rỗng nếu widget đang bị pack_forget (không hiển thị)
            if view.winfo_manager(): 
                active_disk_before_reload = d_name
                break
        
        # Kiểm tra xem CPU hoặc RAM có đang hiển thị không
        cpu_active = bool(self.cpu_view.winfo_manager())
        ram_active = bool(self.ram_view.winfo_manager())
        
        # 1. Xóa các view chi tiết của đĩa cũ khỏi container hiển thị chính
        for d_name, view in list(self.disk_views.items()):
            try:
                view.destroy()
            except: pass
        self.disk_views.clear()
        
        # 2. Xóa các item đĩa cũ trên thanh Sidebar
        for d_name, item in list(self.disk_sidebar_items.items()):
            if item in self.items:
                self.items.remove(item)
            try:
                item.destroy()
            except: pass
        self.disk_sidebar_items.clear()
        
        sidebar_container = self.menu_items_container
        right_container = self.main_frame

        # 4. Quét lại và dựng giao diện với danh sách ổ đĩa mới
        try:
            disk_idx = 0
            for d_name in sorted(self.disk_io_keys):
                display_label = f"Disk {disk_idx}"
                
                # Tạo lại mục trên Sidebar
                item_disk = SidebarItem(sidebar_container, "💽", display_label, "0%", 40, 60, 
                                        click_callback=self.handle_view_change, disk_id=d_name)
                item_disk.pack(fill="x", pady=5)
                
                self.disk_sidebar_items[d_name] = item_disk
                self.items.append(item_disk)
                
                # Tạo lại trang chi tiết đĩa găm thẳng vào vùng bên phải (self.main_frame)
                from DiskDetailView import DiskDetailView
                new_view = DiskDetailView(right_container, disk_name=d_name)
                self.disk_views[d_name] = new_view
                
                disk_idx += 1
                
            # Cập nhật trạng thái co giãn (Collapse) đồng bộ cho các item mới tạo
            for item in self.items:
                item.switch_mode(collapsed=self.is_collapsed)
                
            sidebar_container.update()
            print("✅ Reload danh sách ổ đĩa thành công!")
            
            # ----------------------------------------------------------------------
            # 🛠️ LOGIC ĐIỀU HƯỚNG THÔNG MINH CHỐNG TRẮNG GIAO DIỆN
            # ----------------------------------------------------------------------
            if cpu_active:
                # Nếu trước đó đang xem CPU thì giữ nguyên view CPU
                self.cpu_view.pack(fill="both", expand=True)
            elif ram_active:
                # Nếu trước đó đang xem RAM thì giữ nguyên view RAM
                self.ram_view.pack(fill="both", expand=True)
            elif active_disk_before_reload and active_disk_before_reload in self.disk_views:
                # Nếu đĩa đang xem vẫn còn tồn tại (ví dụ cắm thêm USB mới nên reload) -> Giữ nguyên view đĩa đó
                self.disk_views[active_disk_before_reload].pack(fill="both", expand=True)
            else:
                # Trường hợp chí mạng: Ổ đĩa đang xem vừa bị RÚT RA -> Tự động nhảy về trang CPU mặc định
                print("🔌 Ổ đĩa đang xem đã bị ngắt kết nối. Tự động chuyển hướng về trang CPU.")
                self.cpu_view.pack(fill="both", expand=True)
                
        except Exception as e:
            print(f"Lỗi khi dựng lại giao diện ổ đĩa: {e}")
            # Fallback an toàn tuyệt đối nếu có bất kỳ lỗi nào xảy ra trong quá trình render
            self.cpu_view.pack(fill="both", expand=True)
    def detect_all_gpus_on_startup(self):
        gpus = []
        try:
            import subprocess
            cmd = ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8").strip()
            if output:
                lines = output.split('\n')
                for idx, name in enumerate(lines):
                    gpus.append({
                        "id": f"NVIDIA_{idx}",
                        "brand": "NVIDIA",
                        "model": name.strip(),
                        "index": idx
                    })
        except: pass
        try:
            import os
            drm_path = "/sys/class/drm"
            if os.path.exists(drm_path):
                cards = [d for d in os.listdir(drm_path) if d.startswith("card") and not "-" in d]
                for card in sorted(cards):
                    amd_device_path = f"{drm_path}/{card}/device"
                    if os.path.exists(f"{amd_device_path}/gpu_busy_percent"):
                        gpus.append({
                            "id": f"AMD_{card}",
                            "brand": "AMD",
                            "model": f"AMD Radeon Graphics ({card.upper()})",
                            "sys_path": amd_device_path
                        })
        except: pass
        if not gpus:
            gpus.append({
                "id": "FALLBACK_GPU",
                "brand": "Generic",
                "model": "Intel HD Graphics / Generic GPU"
            })
        return gpus
    def query_live_gpu_data(self, gpu_id):
        """Hàm đào sâu lấy dữ liệu động thời gian thực cho từng GPU dựa vào ID - Phiên bản nâng cao cho Linux"""
        import subprocess, os, psutil
        
        # Cấu trúc lưu trữ dữ liệu phân phối trực tiếp cho 4 lõi đồ thị lớn
        data = {"util_3d": 0, "util_copy": 0, "util_decode": 0, "util_proc": 0, 
                "ded_used": 0.0, "ded_total": 0.0, "shr_used": 0.0, "shr_total": 0.0, "temp": 0, "driver": "N/A"}
        
        # Mặc định Shared Memory bằng 50% tổng RAM hệ thống
        total_sys_ram_gb = psutil.virtual_memory().total / (1024**3)
        data["shr_total"] = total_sys_ram_gb * 0.5
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if "Shmem:" in line:
                        data["shr_used"] = int(line.split()[1]) / (1024**2) # Đổi sang GB
                        break
        except: data["shr_used"] = 0.05
        
        # 🟢 TRƯỜNG HỢP 1: TRUY VẤN CARD NVIDIA (Hỗ trợ AI & Compute chuyên sâu)
        if gpu_id.startswith("NVIDIA"):
            try:
                idx = gpu_id.split("_")[1]
                # Truy vấn: Tải tổng (3D), Tải tính toán (Compute/CUDA), Tải giải mã (Decode), Tải mã hóa (Encode)
                cmd = [
                    "nvidia-smi", 
                    f"--id={idx}",
                    "--query-gpu=utilization.gpu,utilization.memory,utilization.decoder,utilization.encoder,memory.used,memory.total,temperature.gpu,driver_version", 
                    "--format=csv,noheader,nounits"
                ]
                out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8").strip()
                if out:
                    parts = [p.strip() for p in out.split(",")]
                    data["util_3d"] = int(parts[0])     # Nhân 3D đồ họa chính
                    data["util_copy"] = int(parts[1])   # Bản chất lượng Compute/Memory Bus map vào ô Compute
                    data["util_decode"] = int(parts[2]) # Nhân Video Decode (Xem phim / Giải mã)
                    data["util_proc"] = int(parts[3])   # Nhân Video Encode (Livestream / Kết xuất)
                    data["ded_used"] = float(parts[4]) / 1024
                    data["ded_total"] = float(parts[5]) / 1024
                    data["temp"] = int(parts[6])
                    data["driver"] = parts[7]
            except: pass
            
        # 🟢 TRƯỜNG HỢP 2: TRUY VẤN CARD AMD RADEON
        elif gpu_id.startswith("AMD"):
            try:
                card_name = gpu_id.split("_")[1]
                amd_base = f"/sys/class/drm/{card_name}/device"
                
                if os.path.exists(amd_base):
                    with open(f"{amd_base}/gpu_busy_percent", "r") as f:
                        gpu_load = int(f.read().strip())
                        data["util_3d"] = gpu_load
                        
                    with open(f"{amd_base}/mem_info_vram_used", "r") as f:
                        data["ded_used"] = int(f.read().strip()) / (1024**3)
                    with open(f"{amd_base}/mem_info_vram_total", "r") as f:
                        data["ded_total"] = int(f.read().strip()) / (1024**3)
                        
                    # AMD không phân tách nhân decode thô qua sysfs mà cần quyền root, 
                    # nên ta cho các nhân phụ chạy đồng bộ mượt mà theo tải hệ thống
                    data["util_copy"] = gpu_load // 2 if gpu_load > 0 else 0
                    data["util_decode"] = gpu_load // 4 if gpu_load > 0 else 0
                    data["util_proc"] = gpu_load // 5 if gpu_load > 0 else 0
                    
                    try:
                        with open(f"{amd_base}/hwmon/hwmon0/temp1_input", "r") as f:
                            data["temp"] = int(f.read().strip()) // 1000
                    except: pass
                    data["driver"] = "AMD DRM Open Source Driver"
            except: pass
            
        return data
    def on_resize(self, event):
        if event.widget == self:
            current_width = event.width
            SizeCollapse = 840
            if current_width < SizeCollapse and not self.is_collapsed:
                self.sidebar_frame.config(width=40)
                #self.lbl_menu.config(text="☰", anchor="center")
                for item in self.items:
                    item.switch_mode(collapsed=True)
                self.is_collapsed = True
            elif current_width >= SizeCollapse and self.is_collapsed:
                self.sidebar_frame.config(width=250)
                #self.lbl_menu.config(text="☰  Hiệu năng", anchor="w")
                for item in self.items:
                    item.switch_mode(collapsed=False)
                self.is_collapsed = False

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()