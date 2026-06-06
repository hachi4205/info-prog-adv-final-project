import os
import threading
import time

# Helpers
def clr():
    # Clear the terminal screen
    os.system("cls" if os.name == "nt" else "clear")
    
      
# Screen 1 - Main Menu
def main_menu(rooms: list, username: str = ""):
    clr()
    if username:
        print(f"========== [사용자: {username}] ==========")
    print("========== 식사 파티 모집 ==========")
    print("[방 목록] (3초마다 자동으로 갱신합니다.)")
 
    if not rooms:
        print("  (아직 모집 중인 방이 없습니다.)")
    else:
        for room in rooms:
            print(_format_room_line(room))
 
    print("------------------------------------")
    print("1. 방 만들기")
    print("2. 방 참여")
    print("3. 방 복제 (완료된 방)")
    print("0. 종료")
    print("> 입력: ", end="", flush=True)
    

# Screen 2 - Room Detail
def room_detail(room, username: str = ""):
    clr()
    room_id = getattr(room, 'room_id', '?')
    name = getattr(room, 'restaurant', '?')
    print(f"========== [{room_id}] {name} ========== (3초마다 자동으로 갱신합니다.)")
    
    # Menu list
    print("[메뉴 목록]")
    menu_items = getattr(room, 'menu_items', [])
    if not menu_items:
        print("  (아직 메뉴가 없습니다.)")
    else:
        for item in menu_items:
            item_name = getattr(item, 'name', '?')
            price = getattr(item, 'price', 0)
            qty = getattr(item, 'quantity', 1)
            subtotal = price * qty
            print(f" {item_name} × {qty} = {subtotal:,}원")