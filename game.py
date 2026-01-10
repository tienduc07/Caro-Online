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