import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import shutil
import subprocess
import time


class ProcessesDetailView(tk.Frame):
    """
    Tab Processes — bảng danh sách tiến trình kiểu Task Manager.

    🛠️ GHI CHÚ GIỚI HẠN KỸ THUẬT (đọc trước khi chỉnh sửa):
    - Cột GPU: không có API cross-platform chuẩn để lấy % GPU theo từng PID.
      Ở đây chỉ hỗ trợ NVIDIA qua lệnh `nvidia-smi --query-compute-apps` (nếu máy có cài).
      AMD/Intel hoặc máy không có nvidia-smi sẽ luôn hiện "N/A".
    - Cột Disk: psutil.Process.io_counters() chỉ trả cumulative bytes, nên phải tự tính
      delta theo thời gian giữa 2 lần refresh để ra KB/s. Một số process (không cùng user,
      process hệ thống) sẽ bị AccessDenied -> hiện "N/A".
    - "Restart": Linux không có lệnh restart 1 PID có sẵn như Windows. Đây là bản giả lập:
      lưu lại cmdline + cwd trước khi kill, rồi mở lại đúng lệnh đó bằng subprocess.Popen.
      KHÔNG khôi phục được trạng thái cũ (file đang mở, socket, vị trí cửa sổ...), và sẽ
      thất bại với các process hệ thống/service cần quyền đặc biệt.
    """

    REFRESH_MS = 1500  # Chu kỳ refresh bảng (ms) — không cần nhanh như đồ thị CPU/RAM

    COLUMNS = [
        ("pid", "PID", 70),
        ("name", "Name", 220),
        ("cpu", "CPU", 80),
        ("ram", "RAM", 100),
        ("gpu", "GPU", 80),
        ("user", "User", 120),
        ("disk", "Disk", 100),
    ]

    def __init__(self, parent):
        super().__init__(parent, bg="#ffffff")

        # Cache giữ persistent psutil.Process object theo PID — BẮT BUỘC để cpu_percent()
        # tính đúng delta (nếu tạo Process() mới mỗi vòng, cpu_percent(None) luôn trả 0.0).
        self._proc_cache = {}
        # Cache I/O trước đó theo PID: (read_bytes, write_bytes, timestamp) để tính KB/s
        self._disk_prev = {}

        self._sort_col = "cpu"
        self._sort_reverse = True
        self._refresh_job = None

        self._gpu_available = shutil.which("nvidia-smi") is not None
        self._gpu_map = {}  # pid -> "xxx MB" (chỉ NVIDIA)

        self.setup_ui()
        self._schedule_refresh()

    # ------------------------------------------------------------------
    #  GIAO DIỆN
    # ------------------------------------------------------------------
    def setup_ui(self):
        # --- MENU BAR ---
        self.menu_bar = tk.Frame(self, bg="#f3f3f3", height=40)
        self.menu_bar.pack(side="top", fill="x")
        self.menu_bar.pack_propagate(False)

        self.btn_new_process = tk.Button(
            self.menu_bar, text="🗂  New process", font=("Calibri", 10),
            bg="#f3f3f3", bd=0, padx=15, cursor="hand2",
            activebackground="#e6e6e6",
            command=self.on_new_process_click,
        )
        self.btn_new_process.pack(side="left", fill="y", padx=(10, 0))

        self.lbl_proc_count = tk.Label(self.menu_bar, text="0 processes", font=("Calibri", 9),
                                        bg="#f3f3f3", fg="#555555")
        self.lbl_proc_count.pack(side="right", padx=15)

        # --- BẢNG TREEVIEW ---
        table_frame = tk.Frame(self, bg="#ffffff")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        style = ttk.Style()
        style.configure("Proc.Treeview", rowheight=26, font=("Calibri", 10), background="#ffffff",
                         fieldbackground="#ffffff")
        style.configure("Proc.Treeview.Heading", font=("Calibri Bold", 10))

        col_ids = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(table_frame, columns=col_ids, show="headings", style="Proc.Treeview")
        for col_id, label, width in self.COLUMNS:
            anchor = "w" if col_id in ("name", "user") else "e"
            self.tree.heading(col_id, text=label, anchor=anchor,
                               command=lambda c=col_id: self.on_sort_column(c))
            self.tree.column(col_id, width=width, anchor=anchor, stretch=(col_id == "name"))

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # --- CONTEXT MENU (CLICK PHẢI) ---
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="End process", command=self.on_end_process)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Restart", command=self.on_restart_process)

        self.tree.bind("<Button-3>", self.on_right_click)

    # ------------------------------------------------------------------
    #  NEW PROCESS — TẠM PLACEHOLDER, LOGIC THẬT VIẾT SAU
    # ------------------------------------------------------------------
    def on_new_process_click(self):
        # 🛠️ TODO: thay bằng hộp thoại chọn file .exe/binary rồi subprocess.Popen([path])
        messagebox.showinfo("New process", "Chức năng tạo tiến trình mới sẽ được bổ sung sau.")

    # ------------------------------------------------------------------
    #  CONTEXT MENU CLICK PHẢI
    # ------------------------------------------------------------------
    def on_right_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self.context_menu.tk_popup(event.x_root, event.y_root)
        else:
            self.context_menu.unpost()

    def _get_selected_pid(self):
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(self.tree.item(sel[0], "values")[0])
        except (ValueError, IndexError):
            return None

    def on_end_process(self):
        pid = self._get_selected_pid()
        if pid is None:
            return
        try:
            p = psutil.Process(pid)
            name = p.name()
            p.terminate()
            try:
                p.wait(timeout=2)
            except psutil.TimeoutExpired:
                p.kill()  # Không chịu thoát trong 2s -> force kill
        except psutil.NoSuchProcess:
            pass  # Process đã tự thoát trước đó, không cần báo lỗi
        except psutil.AccessDenied:
            messagebox.showerror("End process", f"Không đủ quyền để kết thúc PID {pid}.\n"
                                                 f"Thử chạy app với quyền cao hơn (sudo).")
        except Exception as e:
            messagebox.showerror("End process", f"Lỗi không xác định: {e}")

    def on_restart_process(self):
        pid = self._get_selected_pid()
        if pid is None:
            return
        try:
            p = psutil.Process(pid)
            # Lưu lại thông tin CẦN THIẾT để mở lại trước khi kill
            cmdline = p.cmdline()
            cwd = None
            try:
                cwd = p.cwd()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            if not cmdline:
                messagebox.showwarning("Restart", "Không lấy được lệnh khởi chạy gốc của process này,\n"
                                                   "không thể giả lập restart.")
                return

            p.terminate()
            try:
                p.wait(timeout=2)
            except psutil.TimeoutExpired:
                p.kill()

            # 🛠️ Đây là RESTART GIẢ LẬP: mở lại đúng lệnh cmdline, KHÔNG khôi phục được
            # trạng thái cũ (file đang mở/socket/vị trí cửa sổ...). Không dùng được với
            # process hệ thống/service cần quyền đặc biệt.
            subprocess.Popen(cmdline, cwd=cwd)

        except psutil.NoSuchProcess:
            messagebox.showwarning("Restart", "Process đã không còn tồn tại.")
        except psutil.AccessDenied:
            messagebox.showerror("Restart", f"Không đủ quyền để restart PID {pid}.")
        except Exception as e:
            messagebox.showerror("Restart", f"Lỗi không xác định: {e}")

    # ------------------------------------------------------------------
    #  SẮP XẾP CỘT
    # ------------------------------------------------------------------
    def on_sort_column(self, col_id):
        if self._sort_col == col_id:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col_id
            self._sort_reverse = False
        # Không cần chờ chu kỳ refresh tiếp theo, áp dụng ngay với dữ liệu đang có
        self._render_rows(self._last_rows if hasattr(self, "_last_rows") else [])

    # ------------------------------------------------------------------
    #  THU THẬP DỮ LIỆU GPU (CHỈ NVIDIA, BEST-EFFORT)
    # ------------------------------------------------------------------
    def _refresh_gpu_map(self):
        if not self._gpu_available:
            return
        try:
            # Chạy lệnh pmon quét 1 chu kỳ để lấy thông tin hoạt động thực tế của process
            # Output gồm các cột: # gpu   pid  type    sm   mem   enc   dec   command
            out = subprocess.check_output(
                ["nvidia-smi", "pmon", "-c", "1"],
                stderr=subprocess.DEVNULL, timeout=1.5
            ).decode("utf-8")
            
            new_map = {}
            lines = out.strip().splitlines()
            
            for line in lines:
                # Bỏ qua dòng tiêu đề hoặc dòng trống
                if line.startswith("#") or not line.strip():
                    continue
                    
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        pid = int(parts[1])
                        sm_util = parts[3]   # Cột sm: % mức độ sử dụng lõi GPU tính toán
                        vram_mb = parts[4]   # Cột mem: Dung lượng VRAM đang chiếm dụng (MB)
                        
                        # Chuẩn hóa nếu tiến trình chạy ngầm nhưng chưa ngốn tải
                        if sm_util == "-":
                            sm_util = "0"
                        if vram_mb == "-":
                            vram_mb = "0"
                            
                        # Gộp lại hiển thị định dạng: "15% (350 MB)" hoặc chỉ hiện "350 MB" nếu % bằng 0
                        if int(sm_util) > 0:
                            new_map[pid] = f"{sm_util}% ({vram_mb} MB)"
                        else:
                            new_map[pid] = f"{vram_mb} MB"
                            
                    except ValueError:
                        continue
                        
            self._gpu_map = new_map
        except Exception:
            self._gpu_map = {}

    # ------------------------------------------------------------------
    #  TÍNH TỐC ĐỘ DISK I/O (KB/s) THEO DELTA
    # ------------------------------------------------------------------
    def _calc_disk_rate(self, proc, pid, now):
        try:
            io = proc.io_counters()
        except (psutil.AccessDenied, NotImplementedError, psutil.NoSuchProcess):
            return "N/A"

        prev = self._disk_prev.get(pid)
        self._disk_prev[pid] = (io.read_bytes, io.write_bytes, now)
        if prev is None:
            return "0 KB/s"

        prev_read, prev_write, prev_t = prev
        dt = max(0.001, now - prev_t)
        delta_bytes = (io.read_bytes - prev_read) + (io.write_bytes - prev_write)
        kbs = max(0.0, delta_bytes / 1024.0 / dt)
        if kbs >= 1024:
            return f"{kbs/1024:.1f} MB/s"
        return f"{kbs:.0f} KB/s"

    # ------------------------------------------------------------------
    #  VÒNG LẶP REFRESH CHÍNH
    # ------------------------------------------------------------------
    def _schedule_refresh(self):
        self._refresh_job = self.after(self.REFRESH_MS, self._refresh_loop)

    def _refresh_loop(self):
        # Chỉ làm việc nặng (quét toàn bộ process) khi tab này đang thật sự hiển thị,
        # tránh tốn CPU vô ích lúc người dùng đang ở tab Performance.
        if self.winfo_viewable():
            self.refresh_once()
        self._schedule_refresh()

    def refresh_once(self):
        self._refresh_gpu_map()
        now = time.time()
        current_pids = set()
        rows = []

        for pid in psutil.pids():
            try:
                if pid not in self._proc_cache:
                    p = psutil.Process(pid)
                    p.cpu_percent(None)  # Mồi lần đầu để lần sau tính được delta
                    self._proc_cache[pid] = p
                p = self._proc_cache[pid]
                current_pids.add(pid)

                with p.oneshot():
                    name = p.name()
                    cpu = p.cpu_percent(None)
                    mem_mb = p.memory_info().rss / (1024 * 1024)
                    try:
                        user = p.username()
                    except (psutil.AccessDenied, KeyError):
                        user = "N/A"

                disk_str = self._calc_disk_rate(p, pid, now)
                gpu_str = self._gpu_map.get(pid, "N/A")

                rows.append((pid, name, cpu, mem_mb, gpu_str, user, disk_str))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Dọn cache của các PID đã chết để tránh phình bộ nhớ vô hạn
        for old_pid in list(self._proc_cache.keys()):
            if old_pid not in current_pids:
                del self._proc_cache[old_pid]
                self._disk_prev.pop(old_pid, None)

        self._last_rows = rows
        self.lbl_proc_count.config(text=f"{len(rows)} processes")
        self._render_rows(rows)

    # ------------------------------------------------------------------
    #  RENDER BẢNG (REBUILD TOÀN BỘ — ĐƠN GIẢN, ĐỦ NHANH VỚI VÀI TRĂM PROCESS)
    # ------------------------------------------------------------------
    def _render_rows(self, rows):
        sort_idx = {"pid": 0, "name": 1, "cpu": 2, "ram": 3, "gpu": 4, "user": 5, "disk": 6}[self._sort_col]

        def sort_key(r):
            val = r[sort_idx]
            return val if isinstance(val, (int, float)) else str(val).lower()

        try:
            rows_sorted = sorted(rows, key=sort_key, reverse=self._sort_reverse)
        except TypeError:
            rows_sorted = rows

        selected_pid = self._get_selected_pid()
        self.tree.delete(*self.tree.get_children())

        for pid, name, cpu, mem_mb, gpu_str, user, disk_str in rows_sorted:
            values = (pid, name, f"{cpu:.1f}%", f"{mem_mb:.1f} MB", gpu_str, user, disk_str)
            item_id = self.tree.insert("", "end", iid=str(pid), values=values)
            if pid == selected_pid:
                self.tree.selection_set(item_id)

    def destroy(self):
        if self._refresh_job is not None:
            try:
                self.after_cancel(self._refresh_job)
            except Exception:
                pass
        super().destroy()