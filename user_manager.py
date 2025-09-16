import os
import json
import getpass
from datetime import datetime
from pathlib import Path
from path_utils import get_accounts_directory

def clear_screen():
    """ล้างหน้าจอแบบ Cross-Platform"""
    os.system('cls' if os.name == 'nt' else 'clear')

class UserManager:
    def __init__(self):
        self.accounts_dir = get_accounts_directory()
        self.users_file = self.accounts_dir / "users.json"
        self.setup_accounts_directory()
        self.load_users()
    
    def setup_accounts_directory(self):
        """สร้างโฟลเดอร์ accounts ถ้ายังไม่มี"""
        self.accounts_dir.mkdir(parents=True, exist_ok=True)
    
    def load_users(self):
        """โหลดข้อมูลผู้ใช้จากไฟล์"""
        try:
            if self.users_file.exists():
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            else:
                # สร้างข้อมูลเริ่มต้นจาก config.py
                self.create_default_data()
        except Exception as e:
            print(f"❌ ไม่สามารถโหลดข้อมูลผู้ใช้: {str(e)}")
            self.create_default_data()
    
    def create_default_data(self):
        """สร้างข้อมูลผู้ใช้เริ่มต้น"""
        try:
            # ลองดึงจาก config.py ก่อน (สำหรับผู้ใช้เก่า)
            try:
                import config
                # ตรวจสอบว่า config มีข้อมูลที่ถูกต้องหรือไม่
                if hasattr(config, 'USERNAME') and hasattr(config, 'PASSWORD') and \
                   config.USERNAME not in ["", "your-username"] and config.PASSWORD not in ["", "your-password"]:
                    
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.data = {
                        "current_user": "user1",
                        "users": {
                            "user1": {
                                "name": "บัญชีจาก Config",
                                "username": config.USERNAME,
                                "password": config.PASSWORD,
                                "created": current_time,
                                "last_used": current_time
                            }
                        }
                    }
                    self.save_users()
                    print("✅ นำเข้าข้อมูลผู้ใช้จาก config.py")
                    return
            except:
                pass
                
            # ถ้าไม่มีข้อมูลใน config หรือข้อมูลไม่ถูกต้อง ให้สร้างเป็นฐานข้อมูลเปล่า
            self.data = {"current_user": None, "users": {}}
            self.save_users()
            print("📝 สร้างฐานข้อมูลผู้ใช้ใหม่ (ว่างเปล่า)")
            
        except Exception as e:
            print(f"❌ ไม่สามารถสร้างข้อมูลเริ่มต้น: {str(e)}")
            self.data = {"current_user": None, "users": {}}
    
    def save_users(self):
        """บันทึกข้อมูลผู้ใช้ลงไฟล์"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ ไม่สามารถบันทึกข้อมูลผู้ใช้: {str(e)}")
            return False
    
    def get_current_user(self):
        """ดึงข้อมูลผู้ใช้ปัจจุบัน"""
        current_user_id = self.data.get("current_user")
        if current_user_id and current_user_id in self.data["users"]:
            return self.data["users"][current_user_id]
        return None
    
    def get_current_user_info(self):
        """ดึงข้อมูลผู้ใช้ปัจจุบันสำหรับแสดงผล"""
        user = self.get_current_user()
        if user:
            return f"{user['name']} ({user['username']})"
        return "ไม่มีผู้ใช้"
    
    def list_users(self):
        """แสดงรายชื่อผู้ใช้ทั้งหมด"""
        print("\n📋 รายชื่อผู้ใช้ทั้งหมด")
        print("=" * 50)
        
        if not self.data["users"]:
            print("ไม่มีผู้ใช้ในระบบ")
            return
        
        current_user_id = self.data.get("current_user")
        
        for i, (user_id, user_data) in enumerate(self.data["users"].items(), 1):
            status = " ← ปัจจุบัน" if user_id == current_user_id else ""
            print(f"{i}. {user_data['name']} ({user_data['username']}){status}")
            print(f"   ใช้ครั้งล่าสุด: {user_data['last_used']}")
            print()
    
    def add_user(self):
        """เพิ่มผู้ใช้ใหม่"""
        print("\n➕ เพิ่มผู้ใช้ใหม่")
        print("=" * 20)
        
        try:
            # รับข้อมูลจากผู้ใช้
            name = input("ชื่อเรียก: ").strip()
            if not name:
                print("❌ กรุณากรอกชื่อเรียก")
                return False
            
            username = input("Username: ").strip()
            if not username:
                print("❌ กรุณากรอก Username")
                return False
            
            # ตรวจสอบว่า username ซ้ำหรือไม่
            for user_data in self.data["users"].values():
                if user_data["username"] == username:
                    print("❌ Username นี้มีอยู่แล้ว")
                    return False
            
            password = getpass.getpass("Password: ")
            if not password:
                print("❌ กรุณากรอก Password")
                return False
            
            # สร้าง user ID ใหม่
            user_count = len(self.data["users"]) + 1
            user_id = f"user{user_count}"
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # เพิ่มผู้ใช้ใหม่
            self.data["users"][user_id] = {
                "name": name,
                "username": username,
                "password": password,
                "created": current_time,
                "last_used": current_time
            }
            
            # ถ้าไม่มีผู้ใช้ปัจจุบัน ให้ตั้งผู้ใช้ใหม่เป็นผู้ใช้ปัจจุบัน
            if not self.data.get("current_user"):
                self.data["current_user"] = user_id
                print(f"🎯 ตั้ง '{name}' เป็นผู้ใช้ปัจจุบัน")
            
            if self.save_users():
                print(f"✅ เพิ่มผู้ใช้ '{name}' สำเร็จ!")
                return True
            else:
                return False
                
        except KeyboardInterrupt:
            print("\n⚠️ ยกเลิกการเพิ่มผู้ใช้")
            return False
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            return False
    
    def delete_user(self):
        """ลบผู้ใช้"""
        print("\n❌ ลบผู้ใช้")
        print("=" * 15)
        
        if len(self.data["users"]) <= 1:
            print("⚠️ ไม่สามารถลบได้ ต้องมีผู้ใช้อย่างน้อย 1 คน")
            return False
        
        # แสดงรายชื่อผู้ใช้
        users_list = list(self.data["users"].items())
        current_user_id = self.data.get("current_user")
        
        for i, (user_id, user_data) in enumerate(users_list, 1):
            status = " ← ปัจจุบัน" if user_id == current_user_id else ""
            print(f"{i}. {user_data['name']} ({user_data['username']}){status}")
        
        try:
            choice = input(f"\nเลือกผู้ใช้ที่ต้องการลบ (1-{len(users_list)}): ").strip()
            if not choice.isdigit():
                print("❌ กรุณากรอกตัวเลข")
                return False
            
            index = int(choice) - 1
            if index < 0 or index >= len(users_list):
                print("❌ หมายเลขไม่ถูกต้อง")
                return False
            
            user_id_to_delete, user_data = users_list[index]
            
            # ยืนยันการลบ
            confirm = input(f"ยืนยันการลบ '{user_data['name']}' (y/N): ").strip().lower()
            if confirm != 'y':
                print("ยกเลิกการลบ")
                return False
            
            # ลบผู้ใช้
            del self.data["users"][user_id_to_delete]
            
            # ถ้าเป็นผู้ใช้ปัจจุบัน ให้เปลี่ยนเป็นคนแรก
            if user_id_to_delete == current_user_id:
                first_user_id = list(self.data["users"].keys())[0]
                self.data["current_user"] = first_user_id
                print(f"⚠️ เปลี่ยนผู้ใช้ปัจจุบันเป็น '{self.data['users'][first_user_id]['name']}'")
            
            if self.save_users():
                print(f"✅ ลบผู้ใช้ '{user_data['name']}' สำเร็จ!")
                return True
            else:
                return False
                
        except KeyboardInterrupt:
            print("\n⚠️ ยกเลิกการลบผู้ใช้")
            return False
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            return False
    
    def switch_user(self):
        """สลับผู้ใช้"""
        print("\n🔄 สลับผู้ใช้")
        print("=" * 15)
        
        if len(self.data["users"]) <= 1:
            print("⚠️ มีผู้ใช้เพียงคนเดียว ไม่สามารถสลับได้")
            return False
        
        # แสดงรายชื่อผู้ใช้
        users_list = list(self.data["users"].items())
        current_user_id = self.data.get("current_user")
        
        for i, (user_id, user_data) in enumerate(users_list, 1):
            status = " ← ปัจจุบัน" if user_id == current_user_id else ""
            print(f"{i}. {user_data['name']} ({user_data['username']}){status}")
        
        try:
            choice = input(f"\nเลือกผู้ใช้ (1-{len(users_list)}): ").strip()
            if not choice.isdigit():
                print("❌ กรุณากรอกตัวเลข")
                return False
            
            index = int(choice) - 1
            if index < 0 or index >= len(users_list):
                print("❌ หมายเลขไม่ถูกต้อง")
                return False
            
            user_id_to_switch, user_data = users_list[index]
            
            if user_id_to_switch == current_user_id:
                print("⚠️ เป็นผู้ใช้ปัจจุบันอยู่แล้ว")
                return False
            
            # สลับผู้ใช้
            self.data["current_user"] = user_id_to_switch
            
            # อัปเดตเวลาใช้งานล่าสุด
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.data["users"][user_id_to_switch]["last_used"] = current_time
            
            if self.save_users():
                print(f"✅ สลับเป็น '{user_data['name']}' แล้ว")
                return True
            else:
                return False
                
        except KeyboardInterrupt:
            print("\n⚠️ ยกเลิกการสลับผู้ใช้")
            return False
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            return False
    
    def edit_user(self):
        """แก้ไขข้อมูลผู้ใช้"""
        print("\n✏️ แก้ไขข้อมูลผู้ใช้")
        print("=" * 25)
        
        # แสดงรายชื่อผู้ใช้
        users_list = list(self.data["users"].items())
        current_user_id = self.data.get("current_user")
        
        for i, (user_id, user_data) in enumerate(users_list, 1):
            status = " ← ปัจจุบัน" if user_id == current_user_id else ""
            print(f"{i}. {user_data['name']} ({user_data['username']}){status}")
        
        try:
            choice = input(f"\nเลือกผู้ใช้ที่ต้องการแก้ไข (1-{len(users_list)}): ").strip()
            if not choice.isdigit():
                print("❌ กรุณากรอกตัวเลข")
                return False
            
            index = int(choice) - 1
            if index < 0 or index >= len(users_list):
                print("❌ หมายเลขไม่ถูกต้อง")
                return False
            
            user_id_to_edit, user_data = users_list[index]
            
            print(f"\nแก้ไขข้อมูล: {user_data['name']}")
            print("กด Enter เพื่อใช้ค่าเดิม")
            
            # แก้ไขชื่อเรียก
            new_name = input(f"ชื่อเรียก [{user_data['name']}]: ").strip()
            if new_name:
                user_data['name'] = new_name
            
            # แก้ไข username
            new_username = input(f"Username [{user_data['username']}]: ").strip()
            if new_username:
                # ตรวจสอบว่า username ซ้ำหรือไม่
                for other_user_id, other_user_data in self.data["users"].items():
                    if other_user_id != user_id_to_edit and other_user_data["username"] == new_username:
                        print("❌ Username นี้มีอยู่แล้ว")
                        return False
                user_data['username'] = new_username
            
            # แก้ไข password
            change_password = input("เปลี่ยน Password? (y/N): ").strip().lower()
            if change_password == 'y':
                new_password = getpass.getpass("Password ใหม่: ")
                if new_password:
                    user_data['password'] = new_password
            
            if self.save_users():
                print(f"✅ แก้ไขข้อมูล '{user_data['name']}' สำเร็จ!")
                return True
            else:
                return False
                
        except KeyboardInterrupt:
            print("\n⚠️ ยกเลิกการแก้ไข")
            return False
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            return False
    
    def show_user_menu(self):
        """แสดงเมนูจัดการผู้ใช้"""
        while True:
            clear_screen()
            current_user_info = self.get_current_user_info()
            
            print("\n👤 จัดการผู้ใช้งาน")
            print("=" * 30)
            print(f"ผู้ใช้ปัจจุบัน: {current_user_info}")
            print()
            
            # ถ้าไม่มีผู้ใช้เลย แสดงเฉพาะตัวเลือกเพิ่มผู้ใช้
            if not self.data["users"]:
                print("⚠️  ไม่มีผู้ใช้ในระบบ กรุณาเพิ่มผู้ใช้ก่อน")
                print()
                print("1. ➕ เพิ่มผู้ใช้ใหม่")
                print("0. ↩️  กลับเมนูหลัก")
                print("=" * 30)
                
                try:
                    choice = input("🎯 กรุณาเลือกตัวเลือก (0-1): ").strip()
                    
                    if choice == '0':
                        break
                    elif choice == '1':
                        success = self.add_user()
                        if success:
                            print("✅ เพิ่มผู้ใช้สำเร็จ! ตอนนี้สามารถใช้งานโปรแกรมได้แล้ว")
                    else:
                        print("⚠️ กรุณาเลือกเลข 0 หรือ 1 เท่านั้น")
                    
                    # รอให้ผู้ใช้กด Enter (ยกเว้นการออกจากเมนู)
                    if choice != '0':
                        input("\nกด Enter เพื่อดำเนินการต่อ...")
                        
                except KeyboardInterrupt:
                    print("\n⚠️ กลับสู่เมนูหลัก")
                    break
                except Exception as e:
                    print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            
            else:
                # แสดงเมนูปกติเมื่อมีผู้ใช้แล้ว
                print("1. 📋 แสดงรายชื่อผู้ใช้ทั้งหมด")
                print("2. ➕ เพิ่มผู้ใช้ใหม่")
                print("3. ❌ ลบผู้ใช้")
                print("4. 🔄 สลับผู้ใช้")
                print("5. ✏️  แก้ไขข้อมูลผู้ใช้")
                print("0. ↩️  กลับเมนูหลัก")
                print("=" * 30)
                
                try:
                    choice = input("🎯 กรุณาเลือกตัวเลือก (0-5): ").strip()
                    
                    if choice == '0':
                        break
                    elif choice == '1':
                        self.list_users()
                    elif choice == '2':
                        self.add_user()
                    elif choice == '3':
                        self.delete_user()
                    elif choice == '4':
                        self.switch_user()
                    elif choice == '5':
                        self.edit_user()
                    else:
                        print("⚠️ กรุณาเลือกเลข 0-5 เท่านั้น")
                    
                    # รอให้ผู้ใช้กด Enter (ยกเว้นการออกจากเมนู)
                    if choice != '0':
                        input("\nกด Enter เพื่อดำเนินการต่อ...")
                        
                except KeyboardInterrupt:
                    print("\n⚠️ กลับสู่เมนูหลัก")
                    break
                except Exception as e:
                    print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
    
    def update_current_user_usage(self):
        """อัปเดตเวลาใช้งานล่าสุดของผู้ใช้ปัจจุบัน"""
        current_user_id = self.data.get("current_user")
        if current_user_id and current_user_id in self.data["users"]:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.data["users"][current_user_id]["last_used"] = current_time
            self.save_users()