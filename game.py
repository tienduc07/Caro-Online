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

import pygame
import sys

# === BẢNG MÀU GIAO DIỆN (Catppuccin Style) ===
DARK_BG = (30, 30, 46)          # Màu nền tối chính
LIGHT_BG = (45, 45, 65)         # Màu nền sáng hơn
ACCENT_BLUE = (137, 180, 250)   # Màu xanh dương (quân O)
ACCENT_PINK = (245, 194, 231)   # Màu hồng (quân X)
ACCENT_GREEN = (166, 227, 161)  # Màu xanh lá (thắng)
ACCENT_RED = (243, 139, 168)    # Màu đỏ (thua)
ACCENT_YELLOW = (249, 226, 175) # Màu vàng (chờ)
ACCENT_ORANGE = (250, 179, 135) # Màu cam
WHITE = (205, 214, 244)         # Màu chữ
GRAY = (108, 112, 134)          # Màu xám
DARK_GRAY = (69, 71, 90)
GRID_COLOR = (88, 91, 112)      # Màu đường kẻ

# === HẰNG SỐ KÍCH THƯỚC ===
CELL_SIZE = 40
BOARD_PADDING = 50
HEADER_HEIGHT = 100
BOARD_WIDTH = SIZE_TABLE * CELL_SIZE
BOARD_HEIGHT = SIZE_TABLE * CELL_SIZE
SCREEN_WIDTH = BOARD_WIDTH + BOARD_PADDING * 2
SCREEN_HEIGHT = BOARD_HEIGHT + BOARD_PADDING + HEADER_HEIGHT
X_START = BOARD_PADDING
Y_START = HEADER_HEIGHT


# Vẽ hình chữ nhật bo góc
def draw_rounded_rect(surface, color, rect, radius=10):
    pygame.draw.rect(surface, color, rect, border_radius=radius)


# Vẽ header hiển thị tên và trạng thái
def draw_header():
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
    
    turn_rect_width = 180
    turn_rect_x = SCREEN_WIDTH - turn_rect_width - 20
    draw_rounded_rect(screen, turn_color, (turn_rect_x, 25, turn_rect_width, 50), 10)
    
    turn_surface = turn_font.render(turn_text, True, DARK_BG)
    turn_rect = turn_surface.get_rect(center=(turn_rect_x + turn_rect_width // 2, 50))
    screen.blit(turn_surface, turn_rect)


# Vẽ quân X màu hồng
def draw_x(cx, cy, size):
    thickness = 4
    pygame.draw.line(screen, ACCENT_PINK, (cx - size, cy - size), (cx + size, cy + size), thickness)
    pygame.draw.line(screen, ACCENT_PINK, (cx + size, cy - size), (cx - size, cy + size), thickness)


# Vẽ quân O màu xanh
def draw_o(cx, cy, size):
    pygame.draw.circle(screen, ACCENT_BLUE, (cx, cy), size, 4)


# Vẽ bàn cờ 15x15
def draw_board():
    board_rect = (X_START - 5, Y_START - 5, BOARD_WIDTH + 10, BOARD_HEIGHT + 10)
    draw_rounded_rect(screen, LIGHT_BG, board_rect, 10)
    
    # Vẽ lưới
    for i in range(SIZE_TABLE + 1):
        x = X_START + i * CELL_SIZE
        pygame.draw.line(screen, GRID_COLOR, (x, Y_START), (x, Y_START + BOARD_HEIGHT), 1)
        y = Y_START + i * CELL_SIZE
        pygame.draw.line(screen, GRID_COLOR, (X_START, y), (X_START + BOARD_WIDTH, y), 1)
    
    # Vẽ quân cờ
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


# Vẽ màn hình chờ đối thủ
def draw_waiting_screen():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    box_width = 400
    box_height = 200
    box_x = (SCREEN_WIDTH - box_width) // 2
    box_y = (SCREEN_HEIGHT - box_height) // 2
    
    draw_rounded_rect(screen, LIGHT_BG, (box_x, box_y, box_width, box_height), 20)
    draw_rounded_rect(screen, DARK_GRAY, (box_x + 5, box_y + 5, box_width - 10, box_height - 10), 18)
    
    wait_text = big_font.render("Đang chờ đối thủ...", True, ACCENT_YELLOW)
    wait_rect = wait_text.get_rect(center=(SCREEN_WIDTH // 2, box_y + 80))
    screen.blit(wait_text, wait_rect)
    
    sub_text = small_font.render("Vui lòng đợi người chơi khác tham gia", True, GRAY)
    sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, box_y + 130))
    screen.blit(sub_text, sub_rect)


# Vẽ màn hình kết thúc game
def draw_game_over_screen():
    # ... (code hiển thị kết quả và nút chơi lại/thoát)
    pass


# === KHỞI TẠO PYGAME ===
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Caro Online - Game Cờ Caro")
clock = pygame.time.Clock()

# Thiết lập font chữ
title_font = pygame.font.SysFont("Segoe UI", 24, bold=True)
turn_font = pygame.font.SysFont("Segoe UI", 18, bold=True)
big_font = pygame.font.SysFont("Segoe UI", 32, bold=True)
small_font = pygame.font.SysFont("Segoe UI", 16)