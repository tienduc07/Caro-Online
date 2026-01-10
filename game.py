# === CẤU HÌNH KẾT NỐI SERVER ===
HOST = '127.0.0.1'      # Địa chỉ IP server
SERVER_PORT = 65432     # Cổng kết nối
FORMAT = 'utf8'         # Định dạng mã hóa tin nhắn

# === BIẾN TRẠNG THÁI GAME ===
client = None              # Socket kết nối tới server
game_status = 'connecting' # Trạng thái: 'connecting', 'waiting', 'playing', 'gameover'
waiting_for_restart = False
opponent_wants_restart = False


# Nhận và xử lý tin nhắn từ server (chạy trong thread riêng)
def recv_mess():
    global turned, client, ok, game_result, table, game_status, w
    global waiting_for_restart, opponent_wants_restart
    
    while True:
        try:
            msg = client.recv(1024).decode(FORMAT)
            if not msg:
                break
        except:
            break
        
        parts = msg.split(' ')
        cmd = parts[0]
        
        if cmd == 'WAITING':
            game_status = 'waiting'
            
        elif cmd == 'START':
            # START X or START O
            w = parts[1]
            turned = (w == 'X')
            game_status = 'playing'
            reset_table()
            ok = True
            game_result = None
            waiting_for_restart = False
            opponent_wants_restart = False
            
        elif cmd == 'TICK':
            turned = True
            table[int(parts[2])][int(parts[3])] = parts[1]
            
        elif cmd == 'GAMEOVER':
            if game_result is None:
                if is_board_full():
                    game_result = 'draw'
                else:
                    game_result = 'win'
            ok = False
            game_status = 'gameover'
            
        elif cmd == 'OPPONENT_LEFT':
            game_result = 'opponent_left'
            ok = False
            game_status = 'gameover'
            waiting_for_restart = False
            opponent_wants_restart = False
            
        elif cmd == 'RESTART_WAITING':
            opponent_wants_restart = True
            
        elif cmd == 'RESTART_PENDING':
            waiting_for_restart = True
            
        elif cmd == 'RESTART_DECLINED':
            waiting_for_restart = False
            game_result = 'opponent_left'
            
        elif cmd == 'RESTART':
            # RESTART X or RESTART O
            w = parts[1]
            turned = (w == 'X')
            game_status = 'playing'
            reset_table()
            ok = True
            game_result = None
            waiting_for_restart = False
            opponent_wants_restart = False


# Kết nối tới server và bắt đầu game
def connect_server():
    global client, game_status
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('CLIENT SIDE')
    client.connect((HOST, SERVER_PORT))
    print('client address:', client.getsockname())
    
    msg = "USERNAME " + player
    client.sendall(msg.encode(FORMAT))
    game_status = 'connecting'
    
    run_game()



# === HẰNG SỐ KÍCH THƯỚC GAME ===
SIZE_TABLE = 15             # Số ô mỗi chiều (15x15)

# === BIẾN TRẠNG THÁI GAME ===
table = [[None] * SIZE_TABLE for _ in range(SIZE_TABLE)]
player = None               # Tên người chơi
turned = None              # True nếu đến lượt mình
ok = True                  # True nếu game đang chạy
game_result = None         # Kết quả: 'win', 'lose', 'draw', 'opponent_left'
w = None                   # Quân cờ của mình: 'X' hoặc 'O'


# Đặt lại bàn cờ về trạng thái ban đầu
def reset_table():
    global table
    for i in range(SIZE_TABLE):
        for j in range(SIZE_TABLE):
            table[i][j] = None


# Kiểm tra bàn cờ đã đầy chưa (hòa)
def is_board_full():
    for i in range(SIZE_TABLE):
        for j in range(SIZE_TABLE):
            if table[i][j] is None:
                return False
    return True


# Xác định ô nào được click
def check_pos(pos):
    x, y = pos
    for i in range(SIZE_TABLE):
        cell_x = X_START + i * CELL_SIZE
        if cell_x <= x < cell_x + CELL_SIZE:
            for j in range(SIZE_TABLE):
                cell_y = Y_START + j * CELL_SIZE
                if cell_y <= y < cell_y + CELL_SIZE:
                    return (i, j)
    return (-1, -1)


# Xử lý nước đi khi click
def tick_v(pos):
    global client, turned
    if not turned or game_status != 'playing':
        return
    
    x, y = check_pos(pos)
    if x == -1 and y == -1:
        return
    if table[x][y] == 'X' or table[x][y] == 'O':
        return
    
    table[x][y] = w
    msg = f"TICK {w} {x} {y}"
    client.sendall(msg.encode(FORMAT))
    turned = False


# Vòng lặp chính: kiểm tra thắng
def run_game():
    # ... (phần xử lý sự kiện)
    
    # Check win/draw condition
    if ok and game_status == 'playing':
        win_check = won(table=table)
        if win_check == 1:
            game_result = 'win' if w == 'X' else 'lose'
            client.sendall('GAMEOVER'.encode(FORMAT))
            ok = False
            game_status = 'gameover'
        elif win_check == 2:
            game_result = 'win' if w == 'O' else 'lose'
            client.sendall('GAMEOVER'.encode(FORMAT))
            ok = False
            game_status = 'gameover'
        elif is_board_full():
            game_result = 'draw'
            client.sendall('GAMEOVER'.encode(FORMAT))
            ok = False
            game_status = 'gameover'