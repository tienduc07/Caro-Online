import tkinter as tk
from username import Connect

class Login(tk.Tk):
    
    
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.usr = None  # Biến lưu tên người chơi

        # Cấu hình cửa sổ
        self.geometry('500x350')
        self.title('Caro Online - Login')
        self.resizable(False, False)
        self.configure(bg='#1e1e2e')
        
        # Căn giữa cửa sổ trên màn hình
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (350 // 2)
        self.geometry(f'500x350+{x}+{y}')

        # Tạo khung header
        self.head = tk.Frame(self, bg='#1e1e2e')
        self.head.pack(side='top', fill='both', expand=0, pady=20)

        # Tạo khung body chứa form
        self.body = tk.Frame(self, bg='#1e1e2e')
        self.body.pack(side="top", fill="both", expand=True)
        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, weight=1)

        # Tạo các thành phần giao diện
        self.create_header()
        self.frame = Connect(parent=self.body)
        self.frame.grid(row=0, column=0, sticky="nsew")
        self.frame.tkraise()
        self.bind_action()

    # Gán các sự kiện: đóng cửa sổ, click nút, nhấn Enter
    def bind_action(self):
        self.bind("<Destroy>", self.quit_prog)
        self.frame.btn_connect['command'] = self.connect
        self.bind('<Return>', lambda e: self.connect())

    # Xử lý khi nhấn nút VÀO CHƠI
    def connect(self):
        username = self.frame.get_info()
        username = username.strip(' ')
        if username:
            self.usr = username
            self.destroy()

    # Xử lý sự kiện đóng cửa sổ
    def quit_prog(self, event):
        try:
            if str(event.widget) == '.':
                pass
        except:
            pass

    # Tạo header với tiêu đề "CARO ONLINE"
    def create_header(self):
        self.lbl_title = tk.Label(
            self.head, text='CARO ONLINE', font=("Segoe UI", 28, "bold"), 
            bg="#1e1e2e", fg="#89b4fa")
        self.lbl_title.pack()
        
        self.lbl_subtitle = tk.Label(
            self.head, text='Nhập tên của bạn để chơi', font=("Segoe UI", 12), 
            bg="#1e1e2e", fg="#6c7086")
        self.lbl_subtitle.pack(pady=(5, 0))

    # Chạy vòng lặp chính và trả về tên người chơi
    def run(self):
        self.mainloop()
        return self.usr