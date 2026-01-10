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
