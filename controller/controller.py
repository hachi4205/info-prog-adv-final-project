from view import display
import storage
from model.model import Room, RoomManager

class Controller:
    def __init__(self):
        self.model = RoomManager()
        self.current_user = ""
        self.refresher = display.RefreshController(interval=3)
        self.current_screen = "main"
        self.current_room_id = None
        self._sync_every = 3    
        self._tick = 0          

    def get_valid_integer(self, prompt_message, min_val=None, max_val=None):
        while True:
            try:
                user_input = input(prompt_message).strip()
                if not user_input:
                    continue
                value = int(user_input)
                if min_val is not None and value < min_val:
                    display.show_error(f"{min_val} 이상의 값을 입력해야 합니다.")
                    continue
                if max_val is not None and value > max_val:
                    display.show_error(f"{max_val} 이하의 값을 입력해야 합니다.")
                    continue
                return value
            except ValueError:
                display.show_error("숫자를 입력해 주세요.")

    def sync_from_cloud(self):
        try:
            room_dicts = storage.load_rooms()
            updated_rooms = {}
            for d in room_dicts:
                room_obj = Room.from_dict(d)
                updated_rooms[room_obj.room_id] = room_obj
            
            self.model.rooms = updated_rooms
            if updated_rooms:
                self.model._next_id = max(updated_rooms.keys()) + 1
        except Exception:
            pass

    def sync_to_cloud(self):
        try:
            all_rooms = self.model.get_all_rooms()
            storage.save_rooms(all_rooms)
        except Exception as e:
            print(f"\n[범인 발견] 구글 동기화 에러: {e}")

    def render_current_view(self):
        if self._tick % self._sync_every == 0:
            self.sync_from_cloud()
        self._tick += 1
        if self.current_screen == "main":
            rooms = self.model.get_all_rooms()
            display.main_menu(rooms, self.current_user)
        elif self.current_screen == "room" and self.current_room_id:
            room = self.model.get_room(self.current_room_id)
            if room:
                display.room_detail(room, self.current_user)

    def handle_create_room(self):
        self.refresher.pause()
        form_data = display.create_room_form()
        
        new_room = self.model.create_room(
            host=self.current_user,
            restaurant=form_data['restaurant'],
            target_count=form_data['target_count'],
            meal_type=form_data['meal_type'],
            deadline_minutes=form_data['deadline_minutes'],
            meal_time=form_data['meal_time'],
            max_participants=form_data['max_participants']
        )

        self.sync_to_cloud()
        self.current_screen = "room"
        self.current_room_id = new_room.room_id
        self.refresher.resume()

    def handle_join_room(self):
        self.refresher.pause()
        self.sync_from_cloud()

        room_id = self.get_valid_integer("참여할 방 번호 입력: ", min_val=1)

        target = self.model.get_room(room_id)
        if target and target.host == self.current_user:
            self.current_screen = "room"
            self.current_room_id = room_id
            self.refresher.resume()
            return

        result = self.model.join_room(room_id, self.current_user)

        if result == "ok":
            self.sync_to_cloud()
            self.current_screen = "room"
            self.current_room_id = room_id
        elif result == "no_room":
            display.show_error("존재하지 않는 방 번호입니다.")
            input("계속하려면 엔터를 누르세요...")
        elif result == "full":
            display.show_error("최대 인원이 초과되어 참여할 수 없습니다.")
            input("계속하려면 엔터를 누르세요...")
        self.refresher.resume()

    def handle_clone_room(self):
        self.refresher.pause()
        source_id = self.get_valid_integer("복제할 과거 방 번호를 입력하세요: ", min_val=1)
        defaults = self.model.get_clone_defaults(source_id)
        
        if not defaults:
            display.show_error("존재하지 않는 방 번호입니다.")
            self.refresher.resume()
            return

        form_data = display.create_room_form(defaults)
        
        source_room = self.model.get_room(source_id)
        keep_indices = []
        if source_room and source_room.menu_items:
            raw_selection = display.clone_menu_selection(source_room.menu_items)
            if raw_selection:
                try:
                    keep_indices = [int(x.strip()) - 1 for x in raw_selection.split(",") if x.strip().isdigit()]
                except ValueError:
                    display.show_error("올바른 번호 형식이 아닙니다. 메뉴 복제를 건너뜁니다.")

        new_room = self.model.clone_room(
            source_id=source_id,
            host=self.current_user,
            restaurant=form_data['restaurant'],
            target_count=form_data['target_count'],
            meal_type=form_data['meal_type'],
            deadline_minutes=form_data['deadline_minutes'],
            meal_time=form_data['meal_time'],
            max_participants=form_data['max_participants'],
            keep_item_indices=keep_indices
        )
        
        self.sync_to_cloud()
        display.show_info(f"방이 성공적으로 복제되었습니다! (새 방 번호: {new_room.room_id})")
        self.refresher.resume()

    def run(self):
        display.clr()
        self.current_user = input("사용자 이름을 입력하세요: ").strip()

        self.sync_from_cloud()
        self.refresher.start(self.render_current_view)

        while True:
            try:
                choice = input().strip()
                room = self.model.get_room(self.current_room_id) if self.current_room_id else None

                if self.current_screen == "main":
                    if choice == "1":
                        self.handle_create_room()
                    elif choice == "2":
                        self.handle_join_room()
                    elif choice == "3":
                        self.handle_clone_room()
                    elif choice == "0":
                        self.refresher.stop()
                        break
                        
                elif self.current_screen == "room" and room:
                    if choice == "0":
                        self.current_screen = "main"
                        self.current_room_id = None
                    elif choice == "1":
                        self.refresher.pause()
                        name = input("메뉴 이름: ").strip()
                        price = self.get_valid_integer("가격: ", min_val=0)
                        qty = self.get_valid_integer("수량: ", min_val=1)
                        room.add_menu_item(name, price, qty)
                        self.sync_to_cloud()
                        self.refresher.resume()
                    elif choice == "2":
                        self.refresher.pause()
                        idx = self.get_valid_integer("수정할 메뉴 번호(위에서부터 1, 2...): ", min_val=1) - 1
                        print("(수정하지 않을 항목은 그냥 엔터를 치세요)")
                        new_name = input("새 이름: ").strip()
                        new_price_str = input("새 가격: ").strip()
                        new_qty_str = input("새 수량: ").strip()
                        
                        p = int(new_price_str) if new_price_str.isdigit() else None
                        q = int(new_qty_str) if new_qty_str.isdigit() else None
                        n = new_name if new_name else None
                        
                        room.edit_menu_item(idx, n, p, q)
                        self.sync_to_cloud()
                        self.refresher.resume()
                    elif choice == "3":
                        self.refresher.pause()
                        idx = self.get_valid_integer("삭제할 메뉴 번호: ", min_val=1) - 1
                        if not room.remove_menu_item(idx):
                            display.show_error("잘못된 번호입니다.")
                        else:
                            self.sync_to_cloud()
                        self.refresher.resume()
                    elif choice == "4":
                        self.refresher.pause()
                        text = input("채팅 입력: ").strip()
                        if text:
                            room.add_chat(self.current_user, text)
                            self.sync_to_cloud()
                        self.refresher.resume()
                    elif choice == "5" and self.current_user == room.host:
                        self.refresher.pause()
                        result_data = room.finalize()
                        self.sync_to_cloud()
                        display.clr()
                        display.complete_room(result_data)
                        input("\n확인하셨으면 엔터를 눌러 메인 메뉴로 돌아갑니다...")
                        self.current_screen = "main"
                        self.current_room_id = None
                        self.refresher.resume()
            except KeyboardInterrupt:
                self.refresher.stop()
                break

# 파일이 직접 실행될 때 프로그램 시작
if __name__ == "__main__":
    app = Controller()
    app.run()