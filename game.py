"""
GAME CLIENT - CARO ONLINE
==========================
File chính của client game Caro Online.

Chức năng chính:
- Giao diện đồ họa Pygame cho trò chơi Caro
- Kết nối và giao tiếp với server qua socket
- Xử lý logic game và kiểm tra thắng/thua
- Hiển thị màn hình chờ, màn hình chơi, màn hình kết thúc
- Xử lý yêu cầu chơi lại giữa 2 người chơi
"""

from menu import Login

import pygame
import sys
import socket
import threading
from Won import won

# === CẤU HÌNH KẾT NỐI SERVER ===
HOST = '127.0.0.1'      # Địa chỉ IP server
SERVER_PORT = 65432     # Cổng kết nối
FORMAT = 'utf8'         # Định dạng mã hóa tin nhắn

# === BẢNG MÀU GIAO DIỆN (Catppuccin Style) ===
DARK_BG = (30, 30, 46)          # Màu nền tối chính
LIGHT_BG = (45, 45, 65)         # Màu nền sáng hơn
ACCENT_BLUE = (137, 180, 250)   # Màu xanh dương (quân O)
ACCENT_PINK = (245, 194, 231)   # Màu hồng (quân X)
ACCENT_GREEN = (166, 227, 161)  # Màu xanh lá (thắng/lượt của bạn)
ACCENT_RED = (243, 139, 168)    # Màu đỏ (thua/thoát)
ACCENT_YELLOW = (249, 226, 175) # Màu vàng (đang chờ)
ACCENT_ORANGE = (250, 179, 135) # Màu cam (cảnh báo)
WHITE = (205, 214, 244)         # Màu trắng nhạt (chữ)
GRAY = (108, 112, 134)          # Màu xám (chữ phụ)
DARK_GRAY = (69, 71, 90)        # Màu xám đậm
GRID_COLOR = (88, 91, 112)      # Màu đường kẻ bàn cờ

# === HẰNG SỐ KÍCH THƯỚC GAME ===
SIZE_TABLE = 15             # Số ô mỗi chiều (15x15)
CELL_SIZE = 40              # Kích thước mỗi ô (pixel)
BOARD_PADDING = 50          # Khoảng cách biên bàn cờ
HEADER_HEIGHT = 100         # Chiều cao phần header

# === TÍNH TOÁN VỊ TRÍ BÀN CỜ ===
BOARD_WIDTH = SIZE_TABLE * CELL_SIZE    # Chiều rộng bàn cờ
BOARD_HEIGHT = SIZE_TABLE * CELL_SIZE   # Chiều cao bàn cờ
SCREEN_WIDTH = BOARD_WIDTH + BOARD_PADDING * 2      # Chiều rộng màn hình
SCREEN_HEIGHT = BOARD_HEIGHT + BOARD_PADDING + HEADER_HEIGHT  # Chiều cao màn hình

X_START = BOARD_PADDING     # Tọa độ X bắt đầu vẽ bàn cờ
Y_START = HEADER_HEIGHT     # Tọa độ Y bắt đầu vẽ bàn cờ

# === BIẾN TRẠNG THÁI GAME ===
table = [[None] * SIZE_TABLE for _ in range(SIZE_TABLE)]  # Bảng chứa trạng thái các ô
player = None               # Tên người chơi
turned = None              # True nếu đến lượt mình, False nếu đợi đối thủ
ok = True                  # True nếu game đang chạy, False nếu đã kết thúc
game_result = None         # Kết quả: 'win', 'lose', 'draw', 'opponent_left', hoặc None
client = None              # Socket kết nối tới server
w = None                   # Quân cờ của mình: 'X' hoặc 'O'
game_status = 'connecting' # Trạng thái: 'connecting', 'waiting', 'playing', 'gameover'
waiting_for_restart = False    # True khi đã gửi yêu cầu chơi lại
opponent_wants_restart = False # True khi đối thủ muốn chơi lại


# Đặt lại bàn cờ về trạng thái ban đầu (tất cả ô = None)
def reset_table():
    global table
    for i in range(SIZE_TABLE):
        for j in range(SIZE_TABLE):
            table[i][j] = None


# Kiểm tra bàn cờ đã đầy chưa (hòa nếu đầy mà không ai thắng)
def is_board_full():
    for i in range(SIZE_TABLE):
        for j in range(SIZE_TABLE):
            if table[i][j] is None:
                return False
    return True


# Vẽ hình chữ nhật bo góc với màu và bán kính chỉ định
def draw_rounded_rect(surface, color, rect, radius=10):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


# Vẽ header hiển thị tên người chơi, quân cờ và trạng thái lượt
def draw_header():
    # Header background
    draw_rounded_rect(screen, LIGHT_BG, (10, 10, SCREEN_WIDTH - 20, HEADER_HEIGHT - 20), 15)
    
    # Player symbol indicator
    symbol_x = 30
    symbol_y = 25
    symbol_size = 40
    
    if w == 'X':
        pygame.draw.rect(screen, ACCENT_PINK, (symbol_x, symbol_y, symbol_size, symbol_size), border_radius=8)
        draw_x(symbol_x + symbol_size // 2, symbol_y + symbol_size // 2, symbol_size // 3)
        role_text = "(Đi trước)"
    else:
        pygame.draw.rect(screen, ACCENT_BLUE, (symbol_x, symbol_y, symbol_size, symbol_size), border_radius=8)
        draw_o(symbol_x + symbol_size // 2, symbol_y + symbol_size // 2, symbol_size // 3)
        role_text = "(Đi sau)"
    
    # Player name and role
    name_text = title_font.render(player, True, WHITE)
    screen.blit(name_text, (symbol_x + symbol_size + 15, symbol_y))
    
    role_surface = small_font.render(role_text, True, GRAY)
    screen.blit(role_surface, (symbol_x + symbol_size + 15, symbol_y + 32))
    
    # Turn indicator
    if game_status == 'waiting':
        turn_text = "CHỜ ĐỐI THỦ..."
        turn_color = ACCENT_ORANGE
    elif game_status == 'playing':
        if turned:
            turn_text = "LƯỢT CỦA BẠN"
            turn_color = ACCENT_GREEN
        else:
            turn_text = "ĐỢI ĐỐI THỦ..."
            turn_color = ACCENT_YELLOW
    else:
        turn_text = "KẾT THÚC"
        turn_color = GRAY
    
    # Turn indicator box
    turn_rect_width = 180
    turn_rect_x = SCREEN_WIDTH - turn_rect_width - 20
    draw_rounded_rect(screen, turn_color, (turn_rect_x, 25, turn_rect_width, 50), 10)
    
    turn_surface = turn_font.render(turn_text, True, DARK_BG)
    turn_rect = turn_surface.get_rect(center=(turn_rect_x + turn_rect_width // 2, 50))
    screen.blit(turn_surface, turn_rect)


# Vẽ quân X màu hồng tại vị trí tâm (cx, cy) với kích thước size
def draw_x(cx, cy, size):
    thickness = 4
    pygame.draw.line(screen, ACCENT_PINK, (cx - size, cy - size), (cx + size, cy + size), thickness)
    pygame.draw.line(screen, ACCENT_PINK, (cx + size, cy - size), (cx - size, cy + size), thickness)


# Vẽ quân O màu xanh dương tại vị trí tâm (cx, cy) với bán kính size
def draw_o(cx, cy, size):
    pygame.draw.circle(screen, ACCENT_BLUE, (cx, cy), size, 4)


# Vẽ bàn cờ 15x15 với lưới kẻ và các quân cờ đã đặt
def draw_board():
    # Board background
    board_rect = (X_START - 5, Y_START - 5, BOARD_WIDTH + 10, BOARD_HEIGHT + 10)
    draw_rounded_rect(screen, LIGHT_BG, board_rect, 10)
    
    # Draw grid
    for i in range(SIZE_TABLE + 1):
        x = X_START + i * CELL_SIZE
        pygame.draw.line(screen, GRID_COLOR, (x, Y_START), (x, Y_START + BOARD_HEIGHT), 1)
        y = Y_START + i * CELL_SIZE
        pygame.draw.line(screen, GRID_COLOR, (X_START, y), (X_START + BOARD_WIDTH, y), 1)
    
    # Draw pieces
    for i in range(SIZE_TABLE):
        for j in range(SIZE_TABLE):
            cx = X_START + i * CELL_SIZE + CELL_SIZE // 2
            cy = Y_START + j * CELL_SIZE + CELL_SIZE // 2
            
            if table[i][j] == 'X':
                pygame.draw.rect(screen, (80, 60, 80), 
                               (X_START + i * CELL_SIZE + 2, Y_START + j * CELL_SIZE + 2, 
                                CELL_SIZE - 4, CELL_SIZE - 4), border_radius=5)
                draw_x(cx, cy, CELL_SIZE // 3)
            elif table[i][j] == 'O':
                pygame.draw.rect(screen, (60, 70, 90), 
                               (X_START + i * CELL_SIZE + 2, Y_START + j * CELL_SIZE + 2, 
                                CELL_SIZE - 4, CELL_SIZE - 4), border_radius=5)
                draw_o(cx, cy, CELL_SIZE // 3)


# Vẽ màn hình chờ đối thủ với overlay tối và thông báo
def draw_waiting_screen():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    # Waiting box
    box_width = 400
    box_height = 200
    box_x = (SCREEN_WIDTH - box_width) // 2
    box_y = (SCREEN_HEIGHT - box_height) // 2
    
    draw_rounded_rect(screen, LIGHT_BG, (box_x, box_y, box_width, box_height), 20)
    draw_rounded_rect(screen, DARK_GRAY, (box_x + 5, box_y + 5, box_width - 10, box_height - 10), 18)
    
    # Waiting text
    wait_text = big_font.render("Đang chờ đối thủ...", True, ACCENT_YELLOW)
    wait_rect = wait_text.get_rect(center=(SCREEN_WIDTH // 2, box_y + 80))
    screen.blit(wait_text, wait_rect)
    
    # Sub text
    sub_text = small_font.render("Vui lòng đợi người chơi khác tham gia", True, GRAY)
    sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, box_y + 130))
    screen.blit(sub_text, sub_rect)


# Vẽ màn hình kết thúc với kết quả và nút chơi lại/thoát
def draw_game_over_screen():
    global waiting_for_restart, opponent_wants_restart
    
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    # Result box
    box_width = 420
    box_height = 350
    box_x = (SCREEN_WIDTH - box_width) // 2
    box_y = (SCREEN_HEIGHT - box_height) // 2
    
    draw_rounded_rect(screen, LIGHT_BG, (box_x, box_y, box_width, box_height), 20)
    draw_rounded_rect(screen, DARK_GRAY, (box_x + 5, box_y + 5, box_width - 10, box_height - 10), 18)
    
    # Result text
    if game_result == 'win':
        result_text = "BẠN THẮNG!"
        result_color = ACCENT_GREEN
        sub_text = "Chúc mừng bạn!"
    elif game_result == 'lose':
        result_text = "BẠN THUA!"
        result_color = ACCENT_RED
        sub_text = "Chúc bạn may mắn lần sau!"
    elif game_result == 'draw':
        result_text = "HÒA!"
        result_color = ACCENT_YELLOW
        sub_text = "Bàn cờ đã đầy, không ai thắng!"
    elif game_result == 'opponent_left':
        result_text = "ĐỐI THỦ ĐÃ THOÁT"
        result_color = ACCENT_ORANGE
        sub_text = "Người chơi cùng đã rời khỏi trò chơi"
    else:
        result_text = "KẾT THÚC"
        result_color = GRAY
        sub_text = ""
    
    # Main result
    result_surface = big_font.render(result_text, True, result_color)
    result_rect = result_surface.get_rect(center=(SCREEN_WIDTH // 2, box_y + 70))
    screen.blit(result_surface, result_rect)
    
    # Sub text
    sub_surface = small_font.render(sub_text, True, GRAY)
    sub_rect = sub_surface.get_rect(center=(SCREEN_WIDTH // 2, box_y + 115))
    screen.blit(sub_surface, sub_rect)
    
    mouse_pos = pygame.mouse.get_pos()
    btn_width = 200
    btn_height = 50
    btn_x = (SCREEN_WIDTH - btn_width) // 2
    
    play_again_btn = None
    quit_btn = None
    accept_btn = None
    decline_btn = None
    
    # Different UI based on restart state
    if opponent_wants_restart and not waiting_for_restart:
        # Opponent wants to play again - show accept/decline
        notify_text = small_font.render("Đối thủ muốn chơi lại!", True, ACCENT_YELLOW)
        notify_rect = notify_text.get_rect(center=(SCREEN_WIDTH // 2, box_y + 160))
        screen.blit(notify_text, notify_rect)
        
        # Accept button
        accept_btn = pygame.Rect(box_x + 30, box_y + 200, 170, btn_height)
        accept_color = ACCENT_GREEN if accept_btn.collidepoint(mouse_pos) else (100, 180, 100)
        draw_rounded_rect(screen, accept_color, accept_btn, 12)
        accept_text = turn_font.render("ĐỒNG Ý", True, DARK_BG)
        screen.blit(accept_text, accept_text.get_rect(center=accept_btn.center))
        
        # Decline button
        decline_btn = pygame.Rect(box_x + 220, box_y + 200, 170, btn_height)
        decline_color = ACCENT_RED if decline_btn.collidepoint(mouse_pos) else (180, 100, 100)
        draw_rounded_rect(screen, decline_color, decline_btn, 12)
        decline_text = turn_font.render("TỪ CHỐI", True, WHITE)
        screen.blit(decline_text, decline_text.get_rect(center=decline_btn.center))
        
    elif waiting_for_restart:
        # We're waiting for opponent's response
        wait_text = small_font.render("Đang chờ đối thủ xác nhận...", True, ACCENT_YELLOW)
        wait_rect = wait_text.get_rect(center=(SCREEN_WIDTH // 2, box_y + 180))
        screen.blit(wait_text, wait_rect)
        
    elif game_result != 'opponent_left':
        # Normal game over (win/lose/draw) - show play again / quit
        btn_y = box_y + 170
        play_again_btn = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        
        if play_again_btn.collidepoint(mouse_pos):
            btn_color = ACCENT_GREEN
        else:
            btn_color = ACCENT_BLUE
        
        draw_rounded_rect(screen, btn_color, play_again_btn, 12)
        play_text = turn_font.render("CHƠI LẠI", True, DARK_BG)
        screen.blit(play_text, play_text.get_rect(center=play_again_btn.center))
    
    # Quit button (always shown)
    quit_btn_y = box_y + 280 if (opponent_wants_restart or waiting_for_restart) else box_y + 240
    quit_btn = pygame.Rect(btn_x, quit_btn_y, btn_width, btn_height)
    quit_color = ACCENT_RED if quit_btn.collidepoint(mouse_pos) else GRAY
    draw_rounded_rect(screen, quit_color, quit_btn, 12)
    quit_text = turn_font.render("THOÁT GAME", True, WHITE)
    screen.blit(quit_text, quit_text.get_rect(center=quit_btn.center))
    
    return play_again_btn, quit_btn, accept_btn, decline_btn


# Xác định ô nào được click dựa trên tọa độ chuột, trả về (i,j) hoặc (-1,-1)
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


# Xử lý nước đi khi click: kiểm tra hợp lệ, đặt quân và gửi cho server
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
            # Nếu chưa xác định kết quả (đối thủ gửi GAMEOVER)
            if game_result is None:
                # Kiểm tra xem có phải hòa không
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
            # Opponent wants to restart
            opponent_wants_restart = True
            
        elif cmd == 'RESTART_PENDING':
            # Our restart request is pending
            waiting_for_restart = True
            
        elif cmd == 'RESTART_DECLINED':
            # Opponent declined restart
            waiting_for_restart = False
            game_result = 'opponent_left'
            
        elif cmd == 'RESTART':
            # RESTART X or RESTART O - both agreed, new game starts
            w = parts[1]
            turned = (w == 'X')
            game_status = 'playing'
            reset_table()
            ok = True
            game_result = None
            waiting_for_restart = False
            opponent_wants_restart = False


# Vòng lặp chính: kiểm tra thắng, vẽ giao diện, xử lý sự kiện
def run_game():
    global client, player, turned, w, ok, game_result, game_status
    global waiting_for_restart, opponent_wants_restart

    # Start receiver thread
    recv_thread = threading.Thread(target=recv_mess, daemon=True)
    recv_thread.start()
    
    while True:
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
                # Bàn cờ đầy mà không ai thắng -> Hòa
                game_result = 'draw'
                client.sendall('GAMEOVER'.encode(FORMAT))
                ok = False
                game_status = 'gameover'
        
        # Draw screen
        screen.fill(DARK_BG)
        draw_header()
        draw_board()
        
        # Draw overlays based on game status
        if game_status == 'waiting':
            draw_waiting_screen()
            play_again_btn = quit_btn = accept_btn = decline_btn = None
        elif game_status == 'gameover':
            play_again_btn, quit_btn, accept_btn, decline_btn = draw_game_over_screen()
        else:
            play_again_btn = quit_btn = accept_btn = decline_btn = None
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                try:
                    client.sendall('EXIT'.encode(FORMAT))
                except:
                    pass
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                if game_status == 'gameover':
                    if accept_btn and accept_btn.collidepoint(pos):
                        # Accept restart - send our request too
                        client.sendall('RESTART_REQUEST'.encode(FORMAT))
                        
                    elif decline_btn and decline_btn.collidepoint(pos):
                        # Decline restart
                        client.sendall('RESTART_DECLINE'.encode(FORMAT))
                        opponent_wants_restart = False
                        
                    elif play_again_btn and play_again_btn.collidepoint(pos) and not waiting_for_restart:
                        # Request restart
                        client.sendall('RESTART_REQUEST'.encode(FORMAT))
                        waiting_for_restart = True
                        
                    elif quit_btn and quit_btn.collidepoint(pos):
                        client.sendall('EXIT'.encode(FORMAT))
                        pygame.quit()
                        sys.exit()
                        
                elif game_status == 'playing' and turned:
                    tick_v(pos)
        
        pygame.display.update()
        clock.tick(60)


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


# === KHỞI TẠO GAME ===

# Hiển thị cửa sổ đăng nhập và lấy tên người chơi
app = Login()
player = app.run()

# Thoát nếu không nhập tên
if player is None or player.strip() == '':
    sys.exit()

# Khởi tạo Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Caro Online - Game Cờ Caro")
clock = pygame.time.Clock()

# Thiết lập font chữ (dùng Segoe UI hỗ trợ tiếng Việt)
title_font = pygame.font.SysFont("Segoe UI", 24, bold=True)   # Font tiêu đề
turn_font = pygame.font.SysFont("Segoe UI", 18, bold=True)    # Font trạng thái lượt
big_font = pygame.font.SysFont("Segoe UI", 32, bold=True)     # Font kết quả
small_font = pygame.font.SysFont("Segoe UI", 16)              # Font chú thích

# Bắt đầu game - kết nối server
connect_server()
