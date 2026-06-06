import os
import time
import threading

# Helpers
def clr():
    # Clear the terminal screen
    os.system("cls" if os.name == "nt" else "clear")

# Read room.deadline and format it for display
def deadline(room):
    mins = getattr(room, 'remaining_minutes', 0)
    if mins is None:
        return "?"
    if mins <=0:
        return "마감됨"
    return f"{mins}분 후"

# Screen 1 - Main Menu (clear screen, show room list)
# Single-line summary of a room for the main menu list
def format_room_line(room):
    room_id    = getattr(room, 'room_id', '?')
    name       = getattr(room, 'restaurant', '?')
    host       = getattr(room, 'host', '?')
    current    = len(getattr(room, 'participants', []))
    target     = getattr(room, 'target_count', '?')   # spec: current/target
    status     = getattr(room, 'status', lambda: '[?]')()
    meal_type  = getattr(room, 'meal_type', '?')
    deadline_str = deadline(room)
    return (
        f" [{room_id}] {name} | 방장: {host} | "
        f"{current}/{target} | {status} | {meal_type} | 마감: {deadline_str}"
    )
    
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
    
# Screen 2 - Room Detail (clear screen, show menu list, chat, and room actions)
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
            
    # Total 
    total_price = getattr(room, 'total_price', lambda: 0)()
    print (f" 총액: {total_price:,}원")
    
    # Chat log
    print("[채팅]")
    chat_log = getattr(room, 'chat_messages', [])
    if not chat_log:
        print("  (채팅이 없습니다.)")
    else:
        # Display the last 10 messages
        for msg in chat_log[-10:]:
            sender = getattr(msg, 'sender', '?')
            text = getattr(msg, 'text', '')
            print(f" [{sender}] {text}")
            
    print("------------------------------------")
    print("1. 메뉴 추가  2. 메뉴 편집")
    print("3. 메뉴 삭제  4. 채팅")
    
    host = getattr(room, 'host', '')
    if username == host:
        print("5. 완료 (방장만)  0. 나가기")
    else:
        print("0. 나가기")
    print("> 입력: ", end="", flush=True)
    
# Screen 3 - Create Room/ Clone Form
def create_room_form(defaults: dict = None):
    d = defaults or {}
    results = {}
    
    clr()
    print("========== 방 만들기 ==========")
    if defaults:
        print("(엔터를 누르면 기본값으로 설정됩니다.)\n")
        
    def prompt(label, key, cast=str):
        default_val = d.get(key)
        if default_val is not None:
            raw = input(f"> {label} (기본값 = {default_val}): ").strip()
            return raw if raw else str(default_val)
        else:
            value = input(f"> {label}: ").strip()
        return cast(value)
    
    # 1. Restaurant name  
    results['restaurant'] = prompt("식당명", 'restaurant')
    
    # 2. Target count
    results['target_count'] = prompt("목표 인원", 'target_count', cast=int)
    
    # 3. Optional max participants - ask the yes/no question first
    if d.get('max_participants') is not None:
        default_use_max = "Y"
    else:
        default_use_max = "N"
    use_max_raw = input(
        f"> 최대 인원 설정하시겠습니까? (Y/N)"
        + (f" (기본값 = {default_use_max}): " if defaults else ": ")
    ).strip()
    
    if use_max_raw:
        use_max = use_max_raw
    else:
        use_max = default_use_max

    use_max = use_max.upper()
    
    if use_max == 'Y':
        results['max_participants'] = prompt("최대 인원", 'max_participants', cast=int)
    else:
        results['max_participants'] = None

    # 4. Meal type
    results['meal_type'] = prompt("식사 유형 (배달/포장/배달", 'meal_type')
    
    # 5. Deadline (minutes)
    results['deadline_minutes'] = prompt("마감 시간 (현재로부터 몇 분)", 'deadline_minutes', cast=int)

    # 6. Meal time 
    results['meal_time'] = prompt("식사 시간", 'meal_time')
    
    return results

# Screen 4 - Clone: Menu Selection
def clone_menu_selection(menu_items: list):
    clr()
    print("========== 기존 메뉴 선택 ==========")
    print("포함할 메뉴를 선택하세요 (번호를 쉼표로 구분, 예: 1,2):\n")
    for i, item in enumerate(menu_items, 1):
        name = getattr(item, 'name', '?')
        price = getattr(item, 'price', 0)
        qty = getattr(item, 'quantity', 1)
        print(f" [{i}] {name} ×{qty}  ({price:,}원)")
    return input("\n> 선택: ").strip()

# Screen 5 - Complete Room
def complete_room(room):
    total      = result['total']
    count      = result['count']
    per_person = result['per_person']
    meal_type  = result['meal_type']
 
    print("\n=== 완료 ===")
    print(f"총액: {total:,}원", end="")
    if meal_type == '배달':
        print(" (배달비 3,000원 포함)", end="")
    print(f" / {count}명")
    print(f"1인당: {per_person:,}원 (소수점 올림)")
    print("===\n")

# Error/ info messages
def show_error(message: str):
    print(f"[오류] {message}")
    
def show_info(message: str):
    print(f"[안내] {message}")

# Auto-Refresh Thread
class RefreshController:
    def __init__(self, interval: int = 3):
        self._interval = interval
        self._render_fn = None          # The function to call on each tick
        self._stop_event = threading.Event()   # Set → thread exits its loop
        self._pause_event = threading.Event()  # Set → thread is allowed to render
        self._thread = None
 
        # Start paused — nothing renders until start() is called
        self._pause_event.clear()
        
    # Public API 
    def start(self, render_fn):
        self._render_fn = render_fn
        if self._thread and self._thread.is_alive():
            self._stop_event.clear()
            self._pause_event.set()
            return
        
        # Fresh start
        self._stop_event.clear()
        self._pause_event.set()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
 
    def pause(self):
        self._pause_event.clear()
        
    def resume(self):
        self._pause_event.set()
    
    def stop(self):
        self._stop_event.set()
        self._pause_event.set()  # Unpause to allow thread to exit if it was paused
        if self._thread:
            self._thread.join(timeout = self._interval + 1)
        self._thread = None
        
    # Internal loop run by the thread
    def _loop(self):
        while not self._stop_event.is_set():
            self._pause_event.wait()
 
            
            if self._stop_event.is_set():
                break
 
            if self._render_fn:
                try:
                    self._render_fn()
                except Exception:
                    pass
 
            for _ in range(self._interval * 10):
                if self._stop_event.is_set() or not self._pause_event.is_set():
                    break
                time.sleep(0.1)
    