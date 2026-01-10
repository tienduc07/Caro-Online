"""
FORM NHẬP TÊN NGƯỜI CHƠI - CARO ONLINE
======================================
Module chứa widget form để nhập tên người chơi.

Sử dụng tkinter Frame để tạo giao diện nhập liệu.
"""

import tkinter as tk


# Lớp widget form nhập tên người chơi
class Connect(tk.Frame):
    
    # Khởi tạo widget form với widget cha
    def __init__(self, parent):
        tk.Frame.__init__(self, parent, bg='#1e1e2e')
        self.create_widgets()

    # Tạo các thành phần giao diện: label, ô nhập tên, nút VÀO CHƠI
    def create_widgets(self):
        # Label hướng dẫn nhập tên
        self.lbl_ip = tk.Label(
            self, 
            text="Tên người chơi", 
            font=("Segoe UI", 14, "bold"),
            bg="#1e1e2e",   # Màu nền tối
            fg="#cdd6f4"    # Màu chữ trắng nhạt
        )
        self.lbl_ip.pack(pady=(20, 5))
        
        # Ô nhập tên người chơi
        self.txt_ip = tk.Entry(
            self, 
            width=30, 
            font=("Segoe UI", 14),
            bg="#313244",           # Màu nền ô nhập (xám đậm)
            fg="#cdd6f4",           # Màu chữ
            insertbackground="#cdd6f4",  # Màu con trỏ
            relief="flat",          # Không viền
            justify="center"        # Căn giữa chữ
        )
        self.txt_ip.pack(pady=10, ipady=10)
        self.txt_ip.focus()  # Tự động focus vào ô nhập
        
        # Nút VÀO CHƠI
        self.btn_connect = tk.Button(
            self, 
            text="VÀO CHƠI", 
            width=20, 
            font=("Segoe UI", 12, "bold"),
            bg="#89b4fa",           # Màu nền xanh dương
            fg="#1e1e2e",           # Màu chữ tối
            activebackground="#a6e3a1",  # Màu khi hover (xanh lá)
            activeforeground="#1e1e2e",  # Màu chữ khi hover
            relief="flat",          # Không viền
            cursor="hand2"          # Con trỏ dạng tay khi hover
        )
        self.btn_connect.pack(pady=20, ipady=8)

    # Lấy tên người chơi từ ô nhập
    def get_info(self):
        return self.txt_ip.get()

    # Xóa toàn bộ nội dung trong ô nhập tên
    def clear_all(self):
        self.txt_ip.delete(0, tk.END)
