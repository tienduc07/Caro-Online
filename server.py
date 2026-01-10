"""
SERVER CARO ONLINE
==================
File này chứa code phía server để quản lý các phòng chơi và kết nối giữa các người chơi.

Chức năng chính:
- Quản lý kết nối của người chơi
- Ghép cặp người chơi vào phòng
- Chuyển tiếp các nước đi giữa 2 người chơi
- Xử lý yêu cầu chơi lại và đổi quân
"""

import socket
import threading

FORMAT = 'utf8'  


game_rooms = {}
player_to_room = {}
room_counter = 0 
waiting_player = None 


def get_opponent(conn):
    room_id = player_to_room.get(conn)
    if room_id and room_id in game_rooms:
        room = game_rooms[room_id]
        if room['player1'] == conn:
            return room['player2']
        elif room['player2'] == conn:
            return room['player1']
    return None


def is_player1(conn):
    room_id = player_to_room.get(conn)
    if room_id and room_id in game_rooms:
        return game_rooms[room_id]['player1'] == conn
    return False


def remove_player(conn):
    global waiting_player
    room_id = player_to_room.get(conn)
    if room_id and room_id in game_rooms:
        del player_to_room[conn]
        room = game_rooms[room_id]
        
        opponent = None
        if room['player1'] == conn:
            opponent = room['player2']
        elif room['player2'] == conn:
            opponent = room['player1']
        
        if opponent:
            try:
                opponent.sendall('OPPONENT_LEFT'.encode(FORMAT))
            except:
                pass
            if opponent in player_to_room:
                del player_to_room[opponent]
        
        del game_rooms[room_id]
    
    if waiting_player == conn:
        waiting_player = None


def handleClient(conn, addr):
    global waiting_player, room_counter, game_rooms, player_to_room

    while True:
        try:
            msg = conn.recv(1024).decode(FORMAT)
            if not msg:
                break
        except:
            print('[NGẮT KẾT NỐI]', addr)
            remove_player(conn)
            conn.close()
            break
        
        msg = msg.split(" ")
        
        # === XỬ LÝ ĐĂNG KÝ TÊN NGƯỜI CHƠI ===
        if msg[0] == 'USERNAME':
            print(f'{msg[1]} đã kết nối từ {addr}')
            
            if waiting_player is None:
                waiting_player = conn
                conn.sendall('WAITING'.encode(FORMAT))
            else:
                room_counter += 1
                room_id = room_counter
                
                game_rooms[room_id] = {
                    'player1': waiting_player,  # Người chơi 1
                    'player2': conn,            # Người chơi 2
                    'restart_requests': set(),  # Tập hợp yêu cầu restart
                    'current_x_player': waiting_player  # Người đang cầm X
                }
                player_to_room[waiting_player] = room_id
                player_to_room[conn] = room_id
                
                waiting_player.sendall('START X'.encode(FORMAT))
                conn.sendall('START O'.encode(FORMAT))
                
                print(f'Phòng {room_id} đã bắt đầu')
                waiting_player = None
        
        # === XỬ LÝ THOÁT GAME ===
        elif msg[0] == 'EXIT':
            print('[THOÁT]', addr)
            remove_player(conn)
            conn.close()
            return
        
        # === XỬ LÝ KẾT THÚC VÁN ĐẤU ===
        elif msg[0] == 'GAMEOVER':
            print('[KẾT THÚC VÁN]', addr)
            opponent = get_opponent(conn)
            if opponent:
                try:
                    opponent.sendall('GAMEOVER'.encode(FORMAT))
                except:
                    pass
        
        # === XỬ LÝ NƯỚC ĐI ===
        elif msg[0] == 'TICK':
            opponent = get_opponent(conn)
            if opponent:
                try:
                    opponent.sendall(f"TICK {msg[1]} {msg[2]} {msg[3]}".encode(FORMAT))
                except:
                    pass
        
        # === XỬ LÝ YÊU CẦU CHƠI LẠI ===
        elif msg[0] == 'RESTART_REQUEST':
            room_id = player_to_room.get(conn)
            if room_id and room_id in game_rooms:
                room = game_rooms[room_id]
                room['restart_requests'].add(conn)  
                opponent = get_opponent(conn)
                
                if opponent:
                    if opponent in room['restart_requests']:
                        old_x_player = room['current_x_player']
                        if old_x_player == room['player1']:
                            room['current_x_player'] = room['player2']
                            room['player1'].sendall('RESTART O'.encode(FORMAT))
                            room['player2'].sendall('RESTART X'.encode(FORMAT))
                        else:
                            room['current_x_player'] = room['player1']
                            room['player1'].sendall('RESTART X'.encode(FORMAT))
                            room['player2'].sendall('RESTART O'.encode(FORMAT))
                        
                        room['restart_requests'].clear()
                        print(f'[CHƠI LẠI] Phòng {room_id} đã restart với vai trò đổi ngược')
                    else:
                        opponent.sendall('RESTART_WAITING'.encode(FORMAT))
                        conn.sendall('RESTART_PENDING'.encode(FORMAT))
        
        # === XỬ LÝ TỪ CHỐI CHƠI LẠI ===
        elif msg[0] == 'RESTART_DECLINE':
            room_id = player_to_room.get(conn)
            if room_id and room_id in game_rooms:
                room = game_rooms[room_id]
                opponent = get_opponent(conn)
                if opponent:
                    opponent.sendall('RESTART_DECLINED'.encode(FORMAT))
                room['restart_requests'].clear()


# === CẤU HÌNH SERVER ===
HOST = '127.0.0.1'  
SERVER_ROOT = 65432  

# Tạo socket TCP
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  
s.bind((HOST, SERVER_ROOT)) 
s.listen(10) 

print('=== CARO ONLINE SERVER ===')
print(f'Server: {HOST}:{SERVER_ROOT}')
print('Đang chờ người chơi kết nối...')

# === VÒNG LẶP CHÍNH - CHẤP NHẬN KẾT NỐI ===
while True:
    try:
        conn, addr = s.accept()
        thr = threading.Thread(target=handleClient, args=(conn, addr))
        thr.daemon = True  
        thr.start()
    except socket.error as err:
        print('Lỗi:', err)
    except KeyboardInterrupt:
        print('\nServer đã dừng')
        break

s.close()  
