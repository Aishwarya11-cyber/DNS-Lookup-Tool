import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import threading
import time
import socket
from datetime import datetime
import json
import os
import random

# Try to import dns, handle if not installed
try:
    import dns.resolver
    import dns.reversename
    import dns.exception
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    print("WARNING: dnspython not installed. Please install with: pip install dnspython")

# ============= DNS FUNCTIONS =============
def a_record_lookup(domain):
    """Get A records for a domain"""
    if not DNS_AVAILABLE:
        return ["Error: dnspython module not installed. Install with: pip install dnspython"]
    try:
        answers = dns.resolver.resolve(domain, 'A')
        return [f"IP: {rdata.address}" for rdata in answers]
    except dns.resolver.NXDOMAIN:
        return ["Domain does not exist"]
    except dns.resolver.NoAnswer:
        return ["No A records found"]
    except Exception as e:
        return [f"Error: {str(e)}"]

def mx_record_lookup(domain):
    """Get MX records for a domain"""
    if not DNS_AVAILABLE:
        return ["Error: dnspython module not installed. Install with: pip install dnspython"]
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return [f"Priority: {rdata.preference} → {rdata.exchange}" for rdata in answers]
    except dns.resolver.NXDOMAIN:
        return ["Domain does not exist"]
    except dns.resolver.NoAnswer:
        return ["No MX records found"]
    except Exception as e:
        return [f"Error: {str(e)}"]

def txt_record_lookup(domain):
    """Get TXT records for a domain"""

    if not DNS_AVAILABLE:
        return [
            "Error: dnspython module not installed. Install with: pip install dnspython"
        ]

    try:
        # Remove unwanted spaces
        domain = domain.strip()

        answers = dns.resolver.resolve(domain, 'TXT')

        results = []

        for rdata in answers:
            try:
                # Safely decode TXT record data
                txt_value = b"".join(rdata.strings).decode("utf-8")
                results.append(f"TXT: {txt_value}")

            except Exception:
                # Fallback if decoding fails
                results.append(f"TXT: {str(rdata)}")

        return results if results else ["No TXT records found"]

    except dns.resolver.NXDOMAIN:
        return ["Domain does not exist"]

    except dns.resolver.NoAnswer:
        return ["No TXT records found"]

    except dns.resolver.Timeout:
        return ["DNS query timed out"]

    except dns.resolver.NoNameservers:
        return ["No DNS nameservers available"]

    except Exception as e:
        return [f"Error: {str(e)}"]

def ns_record_lookup(domain):
    """Get NS records for a domain"""
    if not DNS_AVAILABLE:
        return ["Error: dnspython module not installed. Install with: pip install dnspython"]
    try:
        answers = dns.resolver.resolve(domain, 'NS')
        return [f"Nameserver: {rdata.target}" for rdata in answers]
    except dns.resolver.NXDOMAIN:
        return ["Domain does not exist"]
    except dns.resolver.NoAnswer:
        return ["No NS records found"]
    except Exception as e:
        return [f"Error: {str(e)}"]

def reverse_lookup(ip):
    """Perform reverse DNS lookup"""
    if not DNS_AVAILABLE:
        return ["Error: dnspython module not installed. Install with: pip install dnspython"]
    try:
        addr = dns.reversename.from_address(ip)
        answers = dns.resolver.resolve(addr, 'PTR')
        return [f"PTR Record: {rdata.target}" for rdata in answers]
    except dns.resolver.NXDOMAIN:
        return ["No PTR record found"]
    except dns.resolver.NoAnswer:
        return ["No PTR record found"]
    except Exception as e:
        return [f"Error: {str(e)}"]

# Try to import reportlab for PDF export
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ============= MAIN APPLICATION =============
class HackerDNSLookup:
    def __init__(self, window):
        self.window = window
        self.window.title("█▓▒░ H4X0R DNS SCANNER v2.0 ░▒▓█")
        self.window.geometry("1100x750")
        self.window.resizable(True, True)
        
        # Check for DNS availability
        if not DNS_AVAILABLE:
            messagebox.showwarning(
                "⚠ Missing Dependency",
                "dnspython is not installed!\n\nPlease install it with:\npip install dnspython\n\nSome features may not work."
            )
        
        # Hacker Theme Colors
        self.bg_color = "#0a0e0a"
        self.fg_color = "#00ff41"
        self.dark_green = "#003300"
        self.button_color = "#0a1f0a"
        self.entry_color = "#0d1a0d"
        self.highlight_color = "#00ff41"
        self.error_color = "#ff0044"
        self.warning_color = "#ffaa00"
        self.cyan_color = "#00ffff"
        self.purple_color = "#bf00ff"
        self.gold_color = "#ffd700"
        self.gray_color = "#889988"
        
        self.window.configure(bg=self.bg_color)
        
        # Variables
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_interval = 5
        self.history_file = "dns_history.json"
        self.scan_history = self.load_history()
        self.current_results = {}
        
        # Setup UI
        self.setup_ui()
        
        # Bind keys
        self.window.bind('<Escape>', lambda e: self.clear_results())
        self.window.bind('<Control-c>', lambda e: self.copy_results())
        self.window.bind('<Control-f>', lambda e: self.full_scan())
        self.window.bind('<Control-r>', lambda e: self.toggle_monitoring())
        self.window.bind('<Control-e>', lambda e: self.export_pdf() if PDF_AVAILABLE else self.export_text())
        
        # Show banner
        self.show_banner()
    
    def setup_ui(self):
        main_container = tk.Frame(self.window, bg=self.bg_color)
        main_container.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Header
        header_frame = tk.Frame(main_container, bg=self.bg_color, height=100)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)
        
        title_frame = tk.Frame(header_frame, bg=self.bg_color)
        title_frame.pack(side="left", fill="both", expand=True)
        
        tk.Label(
            title_frame,
            text="██████╗ ███╗   ██╗███████╗\n██╔══██╗████╗  ██║██╔════╝\n██║  ██║██╔██╗ ██║███████╗\n██║  ██║██║╚██╗██║╚════██║\n██████╔╝██║ ╚████║███████║\n╚═════╝ ╚═╝  ╚═══╝╚══════╝",
            font=("Consolas", 10, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            justify="left"
        ).pack(side="left", padx=(0, 20))
        
        # Status
        status_right = tk.Frame(header_frame, bg=self.bg_color)
        status_right.pack(side="right", fill="both", expand=True)
        
        self.status_frame = tk.Frame(status_right, bg=self.bg_color)
        self.status_frame.pack(anchor="e", pady=5)
        
        self.status_led = tk.Label(
            self.status_frame,
            text="●",
            font=("Arial", 16),
            bg=self.bg_color,
            fg=self.fg_color
        )
        self.status_led.pack(side="left", padx=(0, 5))
        
        self.status_label = tk.Label(
            self.status_frame,
            text="SYSTEM READY",
            font=("Consolas", 11, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        )
        self.status_label.pack(side="left", padx=(0, 20))
        
        self.time_label = tk.Label(
            status_right,
            text=datetime.now().strftime("%H:%M:%S"),
            font=("Consolas", 12, "bold"),
            bg=self.bg_color,
            fg=self.gold_color
        )
        self.time_label.pack(anchor="e")
        self.update_time()
        
        self.stats_label = tk.Label(
            status_right,
            text=f"SCANS: {len(self.scan_history)}",
            font=("Consolas", 9),
            bg=self.bg_color,
            fg=self.gray_color
        )
        self.stats_label.pack(anchor="e")
        
        # Input
        input_container = tk.Frame(main_container, bg=self.bg_color)
        input_container.pack(fill="x", pady=5)
        
        domain_frame = tk.Frame(input_container, bg=self.bg_color)
        domain_frame.pack(fill="x", pady=3)
        
        tk.Label(
            domain_frame,
            text="▶ TARGET DOMAIN",
            font=("Consolas", 10, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(side="left", padx=(0, 10))
        
        self.domain_entry = tk.Entry(
            domain_frame,
            font=("Consolas", 11),
            bg="#0a120a",
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief="flat",
            highlightthickness=2,
            highlightcolor=self.fg_color,
            highlightbackground=self.dark_green,
            width=50
        )
        self.domain_entry.pack(side="left", fill="x", expand=True)
        self.domain_entry.bind('<Return>', lambda e: self.a_lookup())
        
        ip_frame = tk.Frame(input_container, bg=self.bg_color)
        ip_frame.pack(fill="x", pady=3)
        
        tk.Label(
            ip_frame,
            text="▶ TARGET IP",
            font=("Consolas", 10, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(side="left", padx=(0, 10))
        
        self.ip_entry = tk.Entry(
            ip_frame,
            font=("Consolas", 11),
            bg="#0a120a",
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief="flat",
            highlightthickness=2,
            highlightcolor=self.fg_color,
            highlightbackground=self.dark_green,
            width=50
        )
        self.ip_entry.pack(side="left", fill="x", expand=True)
        self.ip_entry.bind('<Return>', lambda e: self.reverse_lookup_gui())
        
        # Buttons
        button_panel = tk.Frame(main_container, bg=self.bg_color)
        button_panel.pack(fill="x", pady=10)
        
        button_configs = [
            ("⚡ A RECORD", self.a_lookup, "#00ff41"),
            ("📧 MX RECORD", self.mx_lookup, "#00aaff"),
            ("📝 TXT RECORD", self.txt_lookup, "#ffaa00"),
            ("🌐 NS RECORD", self.ns_lookup, "#ff00ff"),
            ("🔄 REVERSE", self.reverse_lookup_gui, "#00ffff"),
            ("🔬 FULL SCAN", self.full_scan, "#ff4444"),
            ("📡 REAL-TIME", self.toggle_monitoring, "#ff6600"),
            ("📊 HISTORY", self.show_history, "#ffd700"),
            ("📄 PDF EXPORT" if PDF_AVAILABLE else "📄 EXPORT", self.export_pdf if PDF_AVAILABLE else self.export_text, "#88ff88"),
            ("🗑 CLEAR", self.clear_results, "#ff0066")
        ]
        
        for i, (text, command, color) in enumerate(button_configs):
            btn = tk.Button(
                button_panel,
                text=text,
                font=("Consolas", 9, "bold"),
                bg="#0a1a0a",
                fg=color,
                relief="flat",
                borderwidth=0,
                highlightthickness=0,
                padx=15,
                pady=8,
                cursor="hand2",
                command=command
            )
            btn.grid(row=i//5, column=i%5, padx=4, pady=4, sticky="ew")
            btn.bind('<Enter>', lambda e, b=btn, c=color: b.config(bg=self.dark_green, fg=c))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg="#0a1a0a", fg=b.cget("fg")))
        
        button_panel.grid_columnconfigure(tuple(range(5)), weight=1)
        
        # Progress bar
        progress_container = tk.Frame(main_container, bg=self.bg_color, height=25)
        progress_container.pack(fill="x", pady=5)
        progress_container.pack_propagate(False)
        
        self.progress = ttk.Progressbar(
            progress_container,
            mode='indeterminate',
            length=100
        )
        self.progress.pack(fill="x", padx=20, pady=2)
        
        # Results
        result_container = tk.Frame(main_container, bg=self.bg_color)
        result_container.pack(fill="both", expand=True, pady=5)
        
        result_header = tk.Frame(result_container, bg=self.bg_color)
        result_header.pack(fill="x")
        
        tk.Label(
            result_header,
            text="┌─ TERMINAL OUTPUT ──────────────────────────────┐",
            font=("Consolas", 9),
            bg=self.bg_color,
            fg=self.gray_color
        ).pack(anchor="w")
        
        text_frame = tk.Frame(result_container, bg=self.bg_color)
        text_frame.pack(fill="both", expand=True)
        
        self.result_box = tk.Text(
            text_frame,
            font=("Consolas", 10),
            bg="#000800",
            fg=self.fg_color,
            insertbackground=self.fg_color,
            relief="flat",
            highlightthickness=0,
            wrap=tk.WORD,
            spacing1=1,
            spacing2=1,
            padx=10,
            pady=10,
            state=tk.DISABLED
        )
        self.result_box.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(
            text_frame,
            orient="vertical",
            command=self.result_box.yview,
            bg=self.bg_color,
            troughcolor=self.bg_color,
            activebackground=self.fg_color
        )
        scrollbar.pack(side="right", fill="y")
        self.result_box.config(yscrollcommand=scrollbar.set)
        
        tk.Label(
            result_container,
            text="└──────────────────────────────────────────────────┘",
            font=("Consolas", 9),
            bg=self.bg_color,
            fg=self.gray_color
        ).pack(anchor="w")
        
        # Bottom bar
        bottom_frame = tk.Frame(main_container, bg=self.bg_color)
        bottom_frame.pack(fill="x", pady=(10, 0))
        
        shortcuts = [
            ("Ctrl+C", "Copy"),
            ("Ctrl+F", "Full Scan"),
            ("Ctrl+R", "Real-time"),
            ("Ctrl+E", "Export"),
            ("Escape", "Clear")
        ]
        
        for key, action in shortcuts:
            tk.Label(
                bottom_frame,
                text=f"{key}: {action}",
                font=("Consolas", 8),
                bg=self.bg_color,
                fg=self.gray_color
            ).pack(side="left", padx=(0, 15))
        
        # Quick targets
        quick_frame = tk.Frame(main_container, bg=self.bg_color)
        quick_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(
            quick_frame,
            text="⚡ QUICK TARGETS:",
            font=("Consolas", 9, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(side="left", padx=(0, 10))
        
        targets = ["google.com", "github.com", "stackoverflow.com", "python.org", "yahoo.com"]
        for target in targets:
            btn = tk.Button(
                quick_frame,
                text=target,
                font=("Consolas", 8),
                bg="#0a120a",
                fg=self.cyan_color,
                relief="flat",
                padx=8,
                pady=3,
                cursor="hand2",
                command=lambda t=target: self.quick_select(t)
            )
            btn.pack(side="left", padx=2)
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=self.dark_green))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg="#0a120a"))
        
        # Configure text tags
        self.result_box.tag_configure("success", foreground="#00ff41")
        self.result_box.tag_configure("error", foreground="#ff0044")
        self.result_box.tag_configure("warning", foreground="#ffaa00")
        self.result_box.tag_configure("info", foreground="#00ccff")
        self.result_box.tag_configure("header", foreground="#ff00ff", font=("Consolas", 11, "bold"))
        self.result_box.tag_configure("important", foreground="#ffd700", font=("Consolas", 10, "bold"))
        self.result_box.tag_configure("cyan", foreground="#00ffff")
        self.result_box.tag_configure("gold", foreground="#ffd700")
    
    def insert_text(self, text, tag=None):
        """Insert text into read-only text box"""
        self.result_box.config(state=tk.NORMAL)
        if tag:
            self.result_box.insert(tk.END, text, tag)
        else:
            self.result_box.insert(tk.END, text)
        self.result_box.config(state=tk.DISABLED)
        self.result_box.see(tk.END)
    
    def update_time(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.window.after(1000, self.update_time)
    
    def quick_select(self, target):
        self.domain_entry.delete(0, tk.END)
        self.domain_entry.insert(0, target)
        self.a_lookup()
    
    def show_banner(self):
        banner = """
╔══════════════════════════════════════════════════════════╗
║  ██╗  ██╗ █████╗ ██╗  ██╗██╗  ██╗██████╗  ██████╗     ║
║  ██║  ██║██╔══██╗╚██╗██╔╝██║  ██║██╔══██╗██╔═══██╗    ║
║  ███████║███████║ ╚███╔╝ ███████║██║  ██║██║   ██║    ║
║  ██╔══██║██╔══██║ ██╔██╗ ██╔══██║██║  ██║██║   ██║    ║
║  ██║  ██║██║  ██║██╔╝ ██╗██║  ██║██████╔╝╚██████╔╝    ║
║  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝     ║
║  DNS RECONNAISSANCE TOOL v2.0                          ║
╚══════════════════════════════════════════════════════════╝
        """
        self.insert_text(banner, "cyan")
        self.insert_text("\n[ SYSTEM INITIALIZED ]\n", "success")
        self.insert_text("[ READY FOR TARGETS ]\n\n", "info")
    
    def get_domain(self):
        domain = self.domain_entry.get().strip()
        if not domain:
            messagebox.showwarning("⚠ INPUT ERROR", "Enter a valid domain name!")
            return None
        return domain
    
    def get_ip(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showwarning("⚠ INPUT ERROR", "Enter a valid IP address!")
            return None
        return ip
    
    def show_results(self, title, results):
        self.insert_text("\n" + "═" * 60 + "\n", "header")
        self.insert_text(f"▶ {title} ◀\n", "header")
        self.insert_text("═" * 60 + "\n\n", "header")
        
        self.current_results[title] = results
        
        if not results:
            self.insert_text("⚠ No records found\n", "warning")
        else:
            for result in results:
                if any(word in result.lower() for word in ["error", "fail", "not found"]):
                    self.insert_text(f"✗ {result}\n", "error")
                else:
                    self.insert_text(f"✓ {result}\n", "success")
        
        self.insert_text("\n" + "─" * 40 + "\n", "info")
        self.status_label.config(text="SCAN COMPLETE", fg=self.fg_color)
        self.window.after(2000, lambda: self.status_label.config(text="SYSTEM READY", fg=self.fg_color))
        self.stats_label.config(text=f"SCANS: {len(self.scan_history)}")
    
    def run_scan(self, scan_func, title, *args):
        self.progress.start()
        self.status_label.config(text=f"SCANNING {title}", fg=self.warning_color)
        try:
            result = scan_func(*args)
            self.show_results(title, result)
            target = args[0] if args else "unknown"
            self.save_to_history(target, title.split()[0], result)
        except Exception as e:
            self.show_results("ERROR", [f"Failed: {str(e)}"])
        finally:
            self.progress.stop()
            self.status_label.config(text="SYSTEM READY", fg=self.fg_color)
    
    def a_lookup(self):
        domain = self.get_domain()
        if domain:
            threading.Thread(target=self.run_scan, args=(a_record_lookup, f"A RECORDS - {domain}", domain), daemon=True).start()
    
    def mx_lookup(self):
        domain = self.get_domain()
        if domain:
            threading.Thread(target=self.run_scan, args=(mx_record_lookup, f"MX RECORDS - {domain}", domain), daemon=True).start()
    
    def txt_lookup(self):
        domain = self.get_domain()
        if domain:
            threading.Thread(target=self.run_scan, args=(txt_record_lookup, f"TXT RECORDS - {domain}", domain), daemon=True).start()
    
    def ns_lookup(self):
        domain = self.get_domain()
        if domain:
            threading.Thread(target=self.run_scan, args=(ns_record_lookup, f"NS RECORDS - {domain}", domain), daemon=True).start()
    
    def reverse_lookup_gui(self):
        ip = self.get_ip()
        if ip:
            threading.Thread(target=self.run_scan, args=(reverse_lookup, f"REVERSE DNS - {ip}", ip), daemon=True).start()
    
    def full_scan(self):
        domain = self.get_domain()
        if not domain:
            return
        
        self.progress.start()
        self.status_label.config(text="FULL SCAN IN PROGRESS", fg=self.error_color)
        
        def full_scan_thread():
            self.insert_text("\n" + "=" * 60 + "\n", "header")
            self.insert_text("🔬 INITIATING FULL SCAN\n", "header")
            self.insert_text("=" * 60 + "\n", "header")
            
            scans = [("A", a_record_lookup), ("MX", mx_record_lookup), ("TXT", txt_record_lookup), ("NS", ns_record_lookup)]
            all_results = {}
            
            for record_type, func in scans:
                try:
                    self.insert_text(f"\n▶ Scanning {record_type} records...\n", "info")
                    result = func(domain)
                    all_results[record_type] = result
                    self.current_results[f"{record_type} Records"] = result
                    for line in result:
                        self.insert_text(f"  ✓ {line}\n", "success")
                except Exception as e:
                    self.insert_text(f"  ✗ Failed: {str(e)}\n", "error")
            
            self.insert_text("\n" + "─" * 60 + "\n", "info")
            self.insert_text("✅ FULL SCAN COMPLETE\n", "success")
            self.save_to_history(domain, "FULL", all_results)
            self.progress.stop()
            self.status_label.config(text="SYSTEM READY", fg=self.fg_color)
            self.stats_label.config(text=f"SCANS: {len(self.scan_history)}")
        
        threading.Thread(target=full_scan_thread, daemon=True).start()
    
    def toggle_monitoring(self):
        if not self.monitoring:
            domain = self.get_domain()
            if domain:
                self.start_monitoring(domain)
        else:
            self.stop_monitoring()
    
    def start_monitoring(self, domain):
        self.monitoring = True
        self.status_label.config(text="MONITORING ACTIVE", fg=self.error_color)
        self.status_led.config(text="●", fg=self.error_color)
        self.insert_text("\n" + "=" * 60 + "\n", "warning")
        self.insert_text("📡 REAL-TIME MONITORING ACTIVATED\n", "warning")
        self.insert_text("=" * 60 + "\n", "warning")
        self.insert_text(f"Target: {domain}\n", "info")
        self.insert_text("Press 'REAL-TIME' again to stop\n\n", "info")
        self.monitor_thread = threading.Thread(target=self.monitor_dns, args=(domain,), daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        self.monitoring = False
        self.status_label.config(text="SYSTEM READY", fg=self.fg_color)
        self.status_led.config(text="●", fg=self.fg_color)
        self.insert_text("\n⏹ MONITORING STOPPED\n", "warning")
    
    def monitor_dns(self, domain):
        last_records = {}
        while self.monitoring:
            try:
                current_records = set(a_record_lookup(domain))
                if domain not in last_records:
                    last_records[domain] = current_records
                    self.insert_text(f"\n[{datetime.now().strftime('%H:%M:%S')}] Initial A records:\n", "info")
                    for record in current_records:
                        self.insert_text(f"  ✓ {record}\n", "success")
                else:
                    old = last_records[domain]
                    added = current_records - old
                    removed = old - current_records
                    if added or removed:
                        self.insert_text(f"\n🚨 [{datetime.now().strftime('%H:%M:%S')}] CHANGES DETECTED!\n", "error")
                        for record in added:
                            self.insert_text(f"  ➕ Added: {record}\n", "warning")
                        for record in removed:
                            self.insert_text(f"  ➖ Removed: {record}\n", "error")
                        last_records[domain] = current_records
                time.sleep(self.monitor_interval)
            except Exception as e:
                self.insert_text(f"⚠ Monitoring error: {str(e)}\n", "error")
                time.sleep(self.monitor_interval)
    
    def save_to_history(self, target, record_type, results):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'target': target,
            'type': record_type,
            'results': results if isinstance(results, list) else [str(results)]
        }
        self.scan_history.append(entry)
        self.save_history()
    
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.scan_history[-100:], f, indent=2)
        except:
            pass
    
    def show_history(self):
        if not self.scan_history:
            self.show_results("HISTORY", ["No scan history found"])
            return
        self.insert_text("\n" + "=" * 60 + "\n", "header")
        self.insert_text("📊 SCAN HISTORY\n", "header")
        self.insert_text("=" * 60 + "\n", "header")
        for i, entry in enumerate(self.scan_history[-15:], 1):
            self.insert_text(f"\n[{i}] {entry['timestamp'][:19]}\n", "info")
            self.insert_text(f"  Target: {entry['target']}\n", "success")
            self.insert_text(f"  Type: {entry['type']}\n", "success")
            if isinstance(entry['results'], list):
                for result in entry['results'][:3]:
                    self.insert_text(f"    • {result[:60]}\n", "success")
                if len(entry['results']) > 3:
                    self.insert_text(f"    • ... and {len(entry['results']) - 3} more\n", "info")
    
    def clear_results(self):
        self.result_box.config(state=tk.NORMAL)
        self.result_box.delete("1.0", tk.END)
        self.result_box.config(state=tk.DISABLED)
        self.insert_text("╔═══════════════════════════════╗\n", "info")
        self.insert_text("║  TERMINAL CLEARED            ║\n", "info")
        self.insert_text("╚═══════════════════════════════╝\n", "info")
        self.current_results = {}
    
    def export_pdf(self):
        if not PDF_AVAILABLE:
            messagebox.showerror("❌ ERROR", "reportlab not installed!\nInstall with: pip install reportlab")
            return
        
        if not self.current_results:
            messagebox.showwarning("⚠ ERROR", "No results to export! Run a scan first.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=f"dns_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
        if not filename:
            return
        
        self.progress.start()
        self.status_label.config(text="GENERATING PDF", fg=self.gold_color)
        
        def generate_pdf():
            try:
                doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#00ff41'), alignment=TA_CENTER, spaceAfter=30)
                heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor('#00ccff'), spaceAfter=12, spaceBefore=12)
                normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10, textColor=colors.black, spaceAfter=6)
                success_style = ParagraphStyle('Success', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#00aa00'), spaceAfter=4)
                error_style = ParagraphStyle('Error', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#cc0000'), spaceAfter=4)
                
                story = []
                story.append(Paragraph("H4X0R DNS SCAN REPORT", title_style))
                story.append(Spacer(1, 0.25*inch))
                story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
                story.append(Paragraph(f"Target: {self.domain_entry.get() or 'N/A'}", normal_style))
                story.append(Spacer(1, 0.25*inch))
                
                for title, results in self.current_results.items():
                    story.append(Paragraph(f"▶ {title}", heading_style))
                    if not results:
                        story.append(Paragraph("No records found", normal_style))
                    else:
                        for result in results:
                            if any(word in result.lower() for word in ["error", "fail", "not found"]):
                                story.append(Paragraph(f"✗ {result}", error_style))
                            else:
                                story.append(Paragraph(f"✓ {result}", success_style))
                    story.append(Spacer(1, 0.1*inch))
                
                story.append(Spacer(1, 0.5*inch))
                story.append(Paragraph("─" * 50, normal_style))
                story.append(Paragraph("Report generated by H4X0R DNS Scanner v2.0", normal_style))
                story.append(Paragraph("For educational and security research purposes only", normal_style))
                
                doc.build(story)
                self.window.after(0, lambda: self.pdf_complete(filename))
            except Exception as e:
                self.window.after(0, lambda: self.pdf_error(str(e)))
        
        threading.Thread(target=generate_pdf, daemon=True).start()
    
    def pdf_complete(self, filename):
        self.progress.stop()
        self.status_label.config(text="SYSTEM READY", fg=self.fg_color)
        messagebox.showinfo("✅ SUCCESS", f"PDF Report exported to:\n{filename}")
    
    def pdf_error(self, error_message):
        self.progress.stop()
        self.status_label.config(text="SYSTEM READY", fg=self.fg_color)
        messagebox.showerror("❌ ERROR", f"PDF export failed:\n{error_message}")
    
    def export_text(self):
        content = self.result_box.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("⚠ ERROR", "Nothing to export!")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"dns_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if not filename:
            return
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("✅ SUCCESS", f"Results exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("❌ ERROR", f"Export failed: {str(e)}")
    
    def copy_results(self):
        self.result_box.config(state=tk.NORMAL)
        content = self.result_box.get("1.0", tk.END)
        self.result_box.config(state=tk.DISABLED)
        if content.strip():
            self.window.clipboard_clear()
            self.window.clipboard_append(content)
            self.status_label.config(text="COPIED TO CLIPBOARD", fg=self.gold_color)
            self.window.after(2000, lambda: self.status_label.config(text="SYSTEM READY", fg=self.fg_color))

# ============= MAIN EXECUTION =============
if __name__ == "__main__":
    root = tk.Tk()
    app = HackerDNSLookup(root)
    root.mainloop()