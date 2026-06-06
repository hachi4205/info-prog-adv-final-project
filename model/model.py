import time
import math
import json

class MenuItem:
    def __init__(self, name, price, quantity=1):
        self.name = name
        self.price = price
        self.quantity = quantity
    
    def subtotal(self):
        return self.price * self.quantity

class ChatMessage:
    def __init__(self, sender, text):
        self.sender = sender
        self.text = text

class Room:
    """A meal party room which holds all data and logic for one room"""
    
    def __init__(self, room_id, host, restaurant, target_count,
                   meal_type, deadline_minutes, meal_time, max_participants=None):
        self.room_id = room_id
        self.host = host
        self.restaurant = restaurant
        self.target_count = target_count
        self.meal_type = meal_type
        self.deadline_minutes = deadline_minutes
        self.meal_time = meal_time
        self.max_participants = max_participants
        self.participants = [host]
        self.menu_items = []
        self.chat_messages = []
        self._status = "모집중"
        self._created_at = time.time()

    @property
    def remaining_minutes(self):
        """Minutes left until the deadline. View reads this as an attribute"""
        elapsed = (time.time() - self._created_at) / 60 
        remaining = self.deadline_minutes - elapsed
        return max(0, int(remaining)) 
    
    def total_price(self):
        """Sum of all menu item subtotals"""
        return sum(item.subtotal() for item in self.menu_items)

    def update_status(self):
        """Recompute status based on free seats"""
        if self._status == "완료":
            return
        empty_seats = self.target_count - len(self.participants)
        if empty_seats <= self.target_count * 0.1:
            self._status = "마감임박"
        else:
            self._status = "모집중"

    def status(self):
        """Return display string like '[모집중]'"""
        return f"[{self._status}]"
    
    def add_participant(self, username):
        """Add a user to the room"""
        if username in self.participants:
            return False
        if self.max_participants is not None and len(self.participants) >= self.max_participants:
            return False  
        
        self.participants.append(username)
        self.update_status()
        return True
    
    def add_menu_item(self, name, price, quantity=1):
        """Add a new menu item. Default quantity is 1"""
        self.menu_items.append(MenuItem(name, price, quantity))
        
    def edit_menu_item(self, index, name=None, price=None, quantity=None):
        """Edit an existing menu item by index. Only provided fields are updated"""
        if index < 0 or index >= len(self.menu_items):
            return False
        item = self.menu_items[index]
        if name is not None:
            item.name = name
        if price is not None:
            item.price = price
        if quantity is not None:
            item.quantity = quantity
        return True

    def remove_menu_item(self, index):
        """Remove an item by its index"""
        if index < 0 or index >= len(self.menu_items):
            return False
        self.menu_items.pop(index)
        return True
    
    def add_chat(self, sender, text):
        """Add a new chat message to the room"""
        self.chat_messages.append(ChatMessage(sender, text))

    DELIVERY_FEE = 3000

    def finalize(self):
        """Close the room and compute the per-person cost"""
        total = self.total_price()
        if self.meal_type == "배달":
            total += self.DELIVERY_FEE
            
        count = len(self.participants)
        per_person = math.ceil(total / count) if count > 0 else 0

        self._status = "완료"

        return {
            "total": total,
            "count": count,
            "per_person": per_person,
            "meal_type": self.meal_type,
        }

    def to_dict(self):
        """Convert this room into a flat dict of plain values"""
        return {
            "room_id": self.room_id,
            "host": self.host,
            "restaurant": self.restaurant,
            "target_count": self.target_count,
            "max_participants": self.max_participants if self.max_participants is not None else "",
            "meal_type": self.meal_type,
            "deadline_minutes": self.deadline_minutes,
            "meal_time": self.meal_time,
            "status": self._status,
            "participants": json.dumps(self.participants, ensure_ascii=False),
            "menu_items": json.dumps(
                [{"name": m.name, "price": m.price, "quantity": m.quantity}
                 for m in self.menu_items],
                ensure_ascii=False),
            "chat_messages": json.dumps(
                [{"sender": c.sender, "text": c.text} for c in self.chat_messages],
                ensure_ascii=False),
            "created_at": self._created_at,
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a Room object from a dict produced by to_dict()"""
        max_p = data.get("max_participants")
        max_p = int(max_p) if max_p not in (None, "", "None") else None

        room = cls(
            room_id=int(data["room_id"]),
            host=data["host"],
            restaurant=data["restaurant"],
            target_count=int(data["target_count"]),
            meal_type=data["meal_type"],
            deadline_minutes=int(data["deadline_minutes"]),
            meal_time=data["meal_time"],
            max_participants=max_p,
        )

        room._status = data.get("status", "모집중")
        room.participants = json.loads(data.get("participants") or "[]")
        room._created_at = float(data.get("created_at") or room._created_at)

        for m in json.loads(data.get("menu_items") or "[]"):
            room.add_menu_item(m["name"], m["price"], m["quantity"])
        for c in json.loads(data.get("chat_messages") or "[]"):
            room.add_chat(c["sender"], c["text"])

        return room  

class RoomManager:
    """Manages all rooms"""

    def __init__(self):
        self.rooms = {}        
        self._next_id = 1    

    def create_room(self, host, restaurant, target_count, meal_type,
                    deadline_minutes, meal_time, max_participants=None):
        """Create a new room, store it, and return it"""
        room = Room(
            room_id = self._next_id,
            host = host,
            restaurant = restaurant,
            target_count = target_count,
            meal_type = meal_type,
            deadline_minutes = deadline_minutes,
            meal_time = meal_time,
            max_participants = max_participants,
        )
        self.rooms[self._next_id] = room
        self._next_id += 1
        return room

    def get_room(self, room_id):
        """Return a room by id, or None if it does not exist"""
        return self.rooms.get(room_id)

    def get_all_rooms(self):
        """Return all rooms as a list"""
        return list(self.rooms.values())

    def join_room(self, room_id, username):
        """Try to add a user to a room"""
        room = self.get_room(room_id)
        if room is None:
            return "no_room"
        if room.add_participant(username):
            return "ok"
        return "full"
    
    def get_clone_defaults(self, room_id):
        """Return the old room's settings as defaults for the clone form.
        The View uses this dict to pre-fill the form. Returns None if no room"""
        room = self.get_room(room_id)
        if room is None:
            return None
        return {
            "restaurant": room.restaurant,
            "target_count": room.target_count,
            "max_participants": room.max_participants,
            "meal_type": room.meal_type,
            "deadline_minutes": room.deadline_minutes,
            "meal_time": room.meal_time,
        }

    def clone_room(self, source_id, host, restaurant, target_count, meal_type,
                   deadline_minutes, meal_time, max_participants=None,
                   keep_item_indices=None):
        """Create a new room based on an old one"""
        source = self.get_room(source_id)
        if source is None:
            return None

        new_room = self.create_room(
            host=host,
            restaurant=restaurant,
            target_count=target_count,
            meal_type=meal_type,
            deadline_minutes=deadline_minutes,
            meal_time=meal_time,
            max_participants=max_participants,
        )

        if keep_item_indices:
            for i in keep_item_indices:
                if 0 <= i < len(source.menu_items):
                    old = source.menu_items[i]
                    new_room.add_menu_item(old.name, old.price, old.quantity)

        return new_room
