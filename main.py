import os
import time
import logging
import shutil
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import config
from user_manager import UserManager
from path_utils import (
    get_app_directory, 
    get_files_directory, 
    get_completed_directory, 
    get_failed_directory,
    get_log_file_path,
    ensure_directories_exist
)

def clear_screen():
    """ล้างหน้าจอแบบ Cross-Platform"""
    os.system('cls' if os.name == 'nt' else 'clear')

class DSLAutoFillBot:
    def __init__(self):
        self.driver = None
        self.user_manager = UserManager()
        self.setup_logging()
        self.setup_result_logs()
        self.setup_directories()
        # ไม่เปิดเบราว์เซอร์ในขั้นตอนนี้ รอให้เลือกฟีเจอร์ก่อน
    
    def setup_result_logs(self):
        """ตั้งค่าไฟล์ log สำหรับผลลัพธ์"""
        self.success_log_file = get_log_file_path("success.log")
        self.failed_log_file = get_log_file_path("failed.log")
        
        # ไม่ล้าง log เก่า - ให้เก็บประวัติไว้
        # เพิ่มตัวคั่นระหว่าง session
        session_start = f"==================== SESSION START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====================\n"
        with open(str(self.success_log_file), 'a', encoding='utf-8') as f:
            f.write(session_start)
        with open(str(self.failed_log_file), 'a', encoding='utf-8') as f:
            f.write(session_start)
    
    def setup_directories(self):
        """สร้างโฟลเดอร์สำหรับเก็บไฟล์ที่ประมวลผลแล้ว"""
        # ใช้ path_utils เพื่อรองรับ executable
        ensure_directories_exist()
        
        # กำหนด path สำหรับใช้งาน
        self.completed_dir = get_completed_directory()
        self.failed_dir = get_failed_directory()
        
        # สร้างโฟลเดอร์ย่อยสำหรับแต่ละฟีเจอร์
        self.completed_disbursement_dir = self.completed_dir / "disbursement"
        self.completed_sign_contract_dir = self.completed_dir / "sign-contract"
        self.failed_disbursement_dir = self.failed_dir / "disbursement"
        self.failed_sign_contract_dir = self.failed_dir / "sign-contract"
        
        self.log(f"📁 โฟลเดอร์สำเร็จ: {self.completed_dir} (disbursement, sign-contract)")
        self.log(f"📁 โฟลเดอร์ล้มเหลว: {self.failed_dir} (disbursement, sign-contract)")
    
    def log_success(self, filename):
        """บันทึกไฟล์ที่สำเร็จ"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{filename} {current_time}\n"
        with open(str(self.success_log_file), 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def log_failed(self, filename):
        """บันทึกไฟล์ที่ล้มเหลว"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{filename} {current_time}\n"
        with open(str(self.failed_log_file), 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def log_duplicate_action(self, filename):
        """บันทึกไฟล์ที่เป็น duplicate action (ทำสำเร็จแล้ว)"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{filename} {current_time} - DUPLICATE_ACTION\n"
        
        # สร้างไฟล์ duplicate.log ถ้ายังไม่มี
        duplicate_log_file = get_log_file_path("duplicate.log")
        
        # เพิ่มตัวคั่น session ถ้าเป็นครั้งแรกของ session
        if not hasattr(self, '_duplicate_session_started'):
            session_start = f"==================== SESSION START: {current_time} ====================\n"
            with open(str(duplicate_log_file), 'a', encoding='utf-8') as f:
                f.write(session_start)
            self._duplicate_session_started = True
        
        # บันทึก entry
        with open(str(duplicate_log_file), 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def move_file_to_completed(self, filename, source_directory):
        """ย้ายไฟล์ที่สำเร็จไปโฟลเดอร์ completed"""
        try:
            source_path = os.path.join(str(source_directory), filename)
            
            # เลือก destination folder ตาม source directory
            if "disbursement" in str(source_directory):
                dest_dir = self.completed_disbursement_dir
                feature_name = "disbursement"
            elif "sign-contract" in str(source_directory):
                dest_dir = self.completed_sign_contract_dir
                feature_name = "sign-contract"
            else:
                # fallback สำหรับ backward compatibility
                dest_dir = self.completed_dir
                feature_name = "general"
            
            dest_path = os.path.join(str(dest_dir), filename)
            
            # ตรวจสอบว่าไฟล์ปลายทางมีอยู่แล้วหรือไม่
            if os.path.exists(dest_path):
                # เพิ่ม timestamp เพื่อหลีกเลี่ยงชื่อซ้ำ
                timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(filename)
                dest_path = os.path.join(str(dest_dir), f"{name}{timestamp}{ext}")
            
            shutil.move(source_path, dest_path)
            self.log(f"📦 ย้ายไฟล์ '{filename}' ไป completed/{feature_name}/ สำเร็จ")
            return True
            
        except Exception as e:
            self.log_error(f"❌ ไม่สามารถย้ายไฟล์ '{filename}' ไป completed/: {str(e)}")
            return False
    
    def move_file_to_failed(self, filename, source_directory):
        """ย้ายไฟล์ที่ล้มเหลวไปโฟลเดอร์ failed"""
        try:
            source_path = os.path.join(str(source_directory), filename)
            
            # เลือก destination folder ตาม source directory
            if "disbursement" in str(source_directory):
                dest_dir = self.failed_disbursement_dir
                feature_name = "disbursement"
            elif "sign-contract" in str(source_directory):
                dest_dir = self.failed_sign_contract_dir
                feature_name = "sign-contract"
            else:
                # fallback สำหรับ backward compatibility
                dest_dir = self.failed_dir
                feature_name = "general"
            
            dest_path = os.path.join(str(dest_dir), filename)
            
            # ตรวจสอบว่าไฟล์ปลายทางมีอยู่แล้วหรือไม่
            if os.path.exists(dest_path):
                # เพิ่ม timestamp เพื่อหลีกเลี่ยงชื่อซ้ำ
                timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(filename)
                dest_path = os.path.join(str(dest_dir), f"{name}{timestamp}{ext}")
            
            shutil.move(source_path, dest_path)
            self.log(f"📦 ย้ายไฟล์ '{filename}' ไป failed/{feature_name}/ สำเร็จ")
            return True
            
        except Exception as e:
            self.log_error(f"❌ ไม่สามารถย้ายไฟล์ '{filename}' ไป failed/: {str(e)}")
            return False
    
    def setup_logging(self):
        if config.LOG_ENABLED:
            log_file_path = get_log_file_path(config.LOG_FILE)
            logging.basicConfig(
                filename=str(log_file_path),
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                filemode='w'
            )
            # เพิ่ม console handler เพื่อแสดงผลใน terminal ด้วย
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            console.setFormatter(formatter)
            logging.getLogger('').addHandler(console)
            
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = None
    
    def log(self, message):
        if self.logger:
            self.logger.info(message)
        else:
            print(f"[INFO] {message}")
    
    def log_warning(self, message):
        if self.logger:
            self.logger.warning(message)
        else:
            print(f"[WARNING] {message}")
    
    def log_error(self, message):
        if self.logger:
            self.logger.error(message)
        else:
            print(f"[ERROR] {message}")
    
    def setup_driver(self):
        try:
            # ตรวจสอบว่าจะใช้เบราว์เซอร์ที่เปิดอยู่แล้วหรือไม่
            if config.USE_EXISTING_BROWSER:
                return self.connect_to_existing_browser()
            else:
                return self.create_new_browser()
        except Exception as e:
            self.log_error(f"ไม่สามารถเริ่มต้นเบราว์เซอร์ได้: {str(e)}")
            raise
    
    def connect_to_existing_browser(self):
        """เชื่อมต่อกับเบราว์เซอร์ที่เปิดอยู่แล้ว"""
        try:
            self.log("🔗 พยายามเชื่อมต่อกับเบราว์เซอร์ที่เปิดอยู่แล้ว...")
            
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{config.CHROME_DEBUG_PORT}")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # ลองเชื่อมต่อโดยไม่ต้องใช้ ChromeDriver service
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.log("✅ เชื่อมต่อกับเบราว์เซอร์ที่เปิดอยู่แล้วสำเร็จ!")
                
                # ตรวจสอบจำนวนแท็บ
                handles = self.driver.window_handles
                self.log(f"🔍 พบ {len(handles)} แท็บในเบราว์เซอร์")
                
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.wait = WebDriverWait(self.driver, config.ELEMENT_WAIT_TIMEOUT)
                
                return True
                
            except Exception as connect_error:
                self.log_warning(f"⚠️  ไม่สามารถเชื่อมต่อกับเบราว์เซอร์ที่เปิดอยู่: {str(connect_error)}")
                self.log("💡 กรุณาเปิด Chrome ด้วยคำสั่ง debug mode หรือเปลี่ยนเป็น USE_EXISTING_BROWSER = False")
                self.log("🚀 กำลังสร้างเบราว์เซอร์ใหม่แทน...")
                return self.create_new_browser()
                
        except Exception as e:
            self.log_error(f"❌ เกิดข้อผิดพลาดขณะเชื่อมต่อเบราว์เซอร์: {str(e)}")
            raise
    
    def create_new_browser(self):
        """สร้างเบราว์เซอร์ใหม่"""
        try:
            chrome_options = Options()
            if config.HEADLESS_MODE:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument(f"--window-size={config.WINDOW_SIZE[0]},{config.WINDOW_SIZE[1]}")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins") 
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # รองรับ Cross-Platform (Mac ARM, Mac Intel, Windows, Linux)
            import platform
            system = platform.system()
            processor = platform.processor()
            
            self.log(f"🖥️  ระบบ: {system} ({processor})")
            
            try:
                if system == "Darwin" and processor == "arm":
                    # Mac ARM (M1/M2/M3)
                    try:
                        service = Service()  # ใช้ ChromeDriver ที่ติดตั้งผ่าน Homebrew
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        self.log("✅ ใช้ ChromeDriver จาก Homebrew (Mac ARM)")
                    except:
                        service = Service(ChromeDriverManager().install())
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        self.log("✅ ใช้ ChromeDriver จาก WebDriver Manager (Mac ARM)")
                
                elif system == "Darwin":
                    # Mac Intel
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.log("✅ ใช้ ChromeDriver สำหรับ Mac Intel")
                
                elif system == "Windows":
                    # Windows (Intel/AMD)
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.log("✅ ใช้ ChromeDriver สำหรับ Windows")
                
                else:
                    # Linux และอื่นๆ
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.log(f"✅ ใช้ ChromeDriver สำหรับ {system}")
                    
            except Exception as driver_error:
                # Fallback: ลองใช้ ChromeDriver ที่อยู่ใน PATH
                self.log_warning(f"⚠️  WebDriver Manager ล้มเหลว: {str(driver_error)}")
                self.log("🔄 ลองใช้ ChromeDriver จาก PATH...")
                try:
                    service = Service()  # ใช้ ChromeDriver ที่อยู่ใน PATH
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.log("✅ ใช้ ChromeDriver จาก PATH สำเร็จ")
                except Exception as fallback_error:
                    self.log_error(f"❌ ไม่สามารถใช้ ChromeDriver จาก PATH: {str(fallback_error)}")
                    raise driver_error  # แสดง error เดิม
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, config.ELEMENT_WAIT_TIMEOUT)
            self.log("✅ สร้างเบราว์เซอร์ใหม่สำเร็จ")
            
            return True
            
        except Exception as e:
            self.log_error(f"❌ ไม่สามารถสร้างเบราว์เซอร์ใหม่ได้: {str(e)}")
            raise
    
    def get_files_list(self, directory_path):
        try:
            directory_path = Path(directory_path)
            if not directory_path.exists():
                directory_path.mkdir(parents=True, exist_ok=True)
                self.log(f"สร้างโฟลเดอร์ {directory_path}")
            
            files = []
            for file_path in directory_path.iterdir():
                if file_path.is_file():
                    file_ext = file_path.suffix.lower()
                    if file_ext in config.ALLOWED_EXTENSIONS:
                        files.append(file_path.name)
            
            self.log(f"พบไฟล์ {len(files)} ไฟล์ในโฟลเดอร์ {directory_path.name}")
            return files
            
        except Exception as e:
            self.log_error(f"ไม่สามารถอ่านไฟล์ได้: {str(e)}")
            return []
    
    def extract_filename_without_extension(self, filename):
        return Path(filename).stem
    
    def wait_for_overlay_disappear(self, timeout=10):
        """รอให้ loading overlay หายไป"""
        try:
            # รอให้ loading overlay หายไป
            overlay_selectors = [
                ".ngx-spinner-overlay",
                "[class*='spinner-overlay']",
                "[class*='loading-overlay']"
            ]
            
            for selector in overlay_selectors:
                try:
                    WebDriverWait(self.driver, timeout).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    self.log(f"⏳ รอ loading overlay หายไป ({selector})")
                    break
                except TimeoutException:
                    continue
            
            # รอเพิ่มอีกนิด เพื่อให้แน่ใจ
            time.sleep(0.5)
            return True
            
        except Exception as e:
            self.log_warning(f"⚠️  ไม่สามารถตรวจสอบ overlay: {str(e)}")
            return True  # ดำเนินการต่อไปเพื่อไม่ให้ค้าง
    
    def wait_and_click(self, selector, description="element", timeout=None):
        try:
            wait_time = timeout if timeout else config.ELEMENT_WAIT_TIMEOUT
            wait = WebDriverWait(self.driver, wait_time)
            
            # รอให้ loading overlay หายก่อน (สำหรับปุ่มสำคัญ)
            important_buttons = ["ค้นหา", "นำเข้าเอกสาร", "ยืนยันการเบิกเงินกู้ยืม", "ยืนยันแบบเบิก", "ยืนยัน", "อัปโหลด"]
            if any(keyword in description for keyword in important_buttons):
                self.wait_for_overlay_disappear()
            
            # ลองหา element ก่อน
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            
            # รอให้ element clickable
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            
            # ตรวจสอบว่า element พร้อมคลิกหรือไม่
            if element.is_enabled() and element.is_displayed():
                # สำหรับ radio button หรือ checkbox ใช้ JavaScript click
                if "radio" in description.lower() or "checkbox" in description.lower():
                    self.driver.execute_script("arguments[0].click();", element)
                    self.log(f"✅ คลิก {description} สำเร็จ (ใช้ JavaScript)")
                # สำหรับปุ่มสำคัญที่อาจถูก overlay บัง ใช้ JavaScript click
                elif any(keyword in description for keyword in important_buttons):
                    self.driver.execute_script("arguments[0].click();", element)
                    self.log(f"✅ คลิก {description} สำเร็จ (ใช้ JavaScript)")
                else:
                    element.click()
                    self.log(f"✅ คลิก {description} สำเร็จ")
            else:
                self.log_warning(f"⚠️  {description} ไม่สามารถคลิกได้ (element ไม่พร้อม)")
                return False
                
            time.sleep(config.WAIT_TIME)
            return True
            
        except TimeoutException:
            self.log_error(f"❌ ไม่พบ {description} (Selector: {selector})")
            return False
        except Exception as e:
            self.log_error(f"❌ เกิดข้อผิดพลาดขณะคลิก {description}: {str(e)}")
            # ลองใช้ JavaScript click เป็น fallback สำหรับปุ่มสำคัญ
            if any(keyword in description for keyword in important_buttons):
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.driver.execute_script("arguments[0].click();", element)
                    self.log(f"✅ คลิก {description} สำเร็จ (ใช้ JavaScript Fallback)")
                    time.sleep(config.WAIT_TIME)
                    return True
                except:
                    pass
            return False
    
    def wait_and_send_keys(self, selector, text, description="input field", clear_first=True):
        try:
            element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            if clear_first:
                element.clear()
            element.send_keys(text)
            self.log(f"✅ กรอกข้อมูล '{text}' ในช่อง {description} สำเร็จ")
            return True
        except TimeoutException:
            self.log_error(f"❌ ไม่พบช่อง {description} (Selector: {selector})")
            return False
        except Exception as e:
            self.log_error(f"❌ เกิดข้อผิดพลาดขณะกรอกข้อมูลในช่อง {description}: {str(e)}")
            return False
    
    def wait_and_upload_file(self, selector, file_path, description="file input"):
        try:
            element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            element.send_keys(file_path)
            self.log(f"✅ อัปโหลดไฟล์ {file_path} สำเร็จ")
            # รอให้เว็บไซต์ประมวลผลไฟล์และรีเฟรช DOM
            time.sleep(config.WAIT_TIME)
            return True
        except TimeoutException:
            self.log_error(f"❌ ไม่พบช่องอัปโหลดไฟล์ {description} (Selector: {selector})")
            return False
        except Exception as e:
            self.log_error(f"❌ เกิดข้อผิดพลาดขณะอัปโหลดไฟล์: {str(e)}")
            return False
    
    def check_element_exists(self, selector, description="element", timeout=5):
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            return True
        except TimeoutException:
            return False
    
    def check_button_by_text(self, selector, button_text, description="button", timeout=5):
        """ตรวจสอบปุ่มโดยดูจากข้อความ"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
            
            for element in elements:
                if button_text in element.text:
                    self.log(f"🔍 เจอปุ่ม '{button_text}' - {description}")
                    return True
            return False
        except TimeoutException:
            return False
    
    def handle_dynamic_checkboxes(self, feature_type="disbursement"):
        """จัดการ checkbox แบบ dynamic - รองรับ 2 หรือ 3 checkbox"""
        try:
            if feature_type == "sign-contract":
                # Checkbox selectors สำหรับฟีเจอร์ลงนามสัญญา
                checkbox_selectors = [
                    # กรณี 2 Checkbox
                    {
                        "address1": config.SIGN_CONTRACT_ADDRESS_CHECKBOX_SELECTOR,
                        "contract": config.SIGN_CONTRACT_CONTRACT_CHECKBOX_2_CASE_SELECTOR
                    },
                    # กรณี 3 Checkbox
                    {
                        "address1": config.SIGN_CONTRACT_ADDRESS_CHECKBOX_SELECTOR,
                        "address2": config.SIGN_CONTRACT_OPTIONAL_CHECKBOX_SELECTOR,
                        "contract": config.SIGN_CONTRACT_CONTRACT_CHECKBOX_SELECTOR
                    }
                ]
            else:
                # Checkbox selectors สำหรับฟีเจอร์เดิม (disbursement)
                checkbox_selectors = [
                    # กรณี 2 Checkbox
                    {
                        "address1": config.ADDRESS_CHECKBOX_SELECTOR,
                        "contract": config.CONTRACT_CHECKBOX_SELECTOR
                    },
                    # กรณี 3 Checkbox
                    {
                        "address1": config.ADDRESS_CHECKBOX_SELECTOR,
                        "address2": config.OPTIONAL_CHECKBOX_SELECTOR,
                        "contract": config.CONTRACT_CHECKBOX_3_CASE_SELECTOR
                    }
                ]
            
            # ลองตรวจสอบว่าเป็นกรณีไหน
            has_3_checkboxes = self.check_element_exists(checkbox_selectors[1]["address2"], "Address2 Checkbox", timeout=2)
            
            if has_3_checkboxes:
                self.log("🔍 ตรวจพบ: รายการมี 3 Checkbox")
                selectors = checkbox_selectors[1]  # ใช้ selectors กรณี 3 checkbox
                
                # คลิก Address 1
                if not self.wait_and_click(selectors["address1"], "Checkbox Address Panel (1/3)"):
                    return False
                
                # คลิก Address 2  
                if not self.wait_and_click(selectors["address2"], "Checkbox Address Panel (2/3)"):
                    return False
                
                # คลิก Contract
                if not self.wait_and_click(selectors["contract"], "Checkbox Contract Panel (3/3)"):
                    return False
                    
                self.log("✅ คลิก Checkbox ทั้ง 3 ตัวเสร็จสิ้น")
                
            else:
                self.log("🔍 ตรวจพบ: รายการมี 2 Checkbox")
                selectors = checkbox_selectors[0]  # ใช้ selectors กรณี 2 checkbox
                
                # คลิก Address
                if not self.wait_and_click(selectors["address1"], "Checkbox Address Panel (1/2)"):
                    return False
                
                # คลิก Contract
                if not self.wait_and_click(selectors["contract"], "Checkbox Contract Panel (2/2)"):
                    return False
                    
                self.log("✅ คลิก Checkbox ทั้ง 2 ตัวเสร็จสิ้น")
            
            return True
            
        except Exception as e:
            self.log_error(f"❌ เกิดข้อผิดพลาดขณะจัดการ Checkbox: {str(e)}")
            return False
    

    def auto_login(self):
        """Login เข้าเว็บไซต์อัตโนมัติ"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.log(f"🔄 ลองใหม่ครั้งที่ {attempt + 1}/{max_retries}...")
                    time.sleep(5)  # รอสักครู่ก่อนลองใหม่
                
                self.log("🔐 เริ่มกระบวนการ Login อัตโนมัติ...")
                
                # 1. เปิดหน้า Login
                self.log(f"🌐 เปิดหน้า Login: {config.LOGIN_PAGE_URL}")
                self.driver.get(config.LOGIN_PAGE_URL)
                
                # รอให้หน้าโหลดเสร็จ (Smart Wait)
                WebDriverWait(self.driver, config.PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, config.USERNAME_SELECTOR))
                )
                
                # รอเพิ่มเติมให้หน้าโหลดเสร็จสมบูรณ์
                self.log("⏳ รอให้หน้า Login โหลดเสร็จสมบูรณ์...")
                time.sleep(2)
                
                # 2. ดึงข้อมูลผู้ใช้ปัจจุบัน
                current_user = self.user_manager.get_current_user()
                if not current_user:
                    self.log_error("❌ ไม่พบข้อมูลผู้ใช้ กรุณาจัดการผู้ใช้งานก่อน")
                    return False
                
                username = current_user['username']
                password = current_user['password']
                
                self.log(f"🔐 ใช้บัญชี: {current_user['name']} ({username})")
                
                # 3. กรอก Username
                if not self.wait_and_send_keys(config.USERNAME_SELECTOR, username, "ช่อง Username"):
                    continue  # ลองใหม่
                
                # 4. กรอก Password
                if not self.wait_and_send_keys(config.PASSWORD_SELECTOR, password, "ช่อง Password"):
                    continue  # ลองใหม่
                
                # 5. คลิกปุ่มเข้าสู่ระบบ
                if not self.wait_and_click(config.LOGIN_BUTTON_SELECTOR, "ปุ่มเข้าสู่ระบบ"):
                    continue  # ลองใหม่
                
                # รอสักครู่หลัง submit login
                time.sleep(3)
                
                # 6. รอให้ Login เสร็จ (Smart Wait)
                self.log("⏳ รอให้ระบบ Login เสร็จ...")
                try:
                    # รอให้ URL เปลี่ยนจากหน้า login
                    WebDriverWait(self.driver, 30).until(
                        lambda driver: config.LOGIN_PAGE_URL not in driver.current_url
                    )
                except TimeoutException:
                    self.log_warning("⚠️ Login อาจใช้เวลานาน - ดำเนินการต่อ")
                
                # 7. ไปที่หน้าที่ต้องการทำงาน
                self.log(f"🎯 ไปยังหน้าทำงาน: {config.WEBSITE_URL}")
                self.driver.get(config.WEBSITE_URL)
                # รอให้หน้าโหลดเสร็จ
                WebDriverWait(self.driver, config.PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, config.RADIO_SELECTOR))
                )
                
                self.log("✅ Login สำเร็จ! พร้อมเริ่มทำงาน")
                return True
                
            except Exception as e:
                self.log_error(f"❌ ครั้งที่ {attempt + 1} ล้มเหลว: {str(e)}")
                if attempt == max_retries - 1:  # ครั้งสุดท้าย
                    self.log_error("❌ Login ล้มเหลวทุกครั้ง")
                    return False
                # ถ้าไม่ใช่ครั้งสุดท้าย จะ continue loop
        
        return False  # ไม่ควรมาถึงจุดนี้

    def process_single_file(self, filename, source_directory):
        try:
            self.log(f"🚀 เริ่มดำเนินการกับไฟล์: {filename}")
            
            # 1. Login อัตโนมัติ (เฉพาะไฟล์แรก)
            if not hasattr(self, '_login_completed'):
                if not self.auto_login():
                    return False
                self._login_completed = True
            else:
                # สำหรับไฟล์ถัดๆ ไป ให้ไปที่หน้าทำงานโดยตรง (ไม่ refresh)
                current_url = self.driver.current_url
                if config.WEBSITE_URL not in current_url:
                    self.log(f"🎯 กลับไปหน้าทำงาน: {config.WEBSITE_URL}")
                    self.driver.get(config.WEBSITE_URL)
                    # รอให้หน้าโหลดเสร็จ
                    WebDriverWait(self.driver, config.PAGE_LOAD_TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, config.RADIO_SELECTOR))
                    )
                else:
                    self.log("✅ อยู่ในหน้าทำงานแล้ว")
            
            # 2. เลือก Radio Button #radio2
            if not self.wait_and_click(config.RADIO_SELECTOR, "Radio Button #radio2"):
                return False
            
            # 3. กรอกชื่อไฟล์ (ตัดนามสกุลออก) ในช่องค้นหา
            search_text = self.extract_filename_without_extension(filename)
            if not self.wait_and_send_keys(config.SEARCH_INPUT_SELECTOR, search_text, "ช่องค้นหา"):
                return False
            
            # 4. คลิกปุ่มค้นหา
            if not self.wait_and_click(config.SEARCH_BUTTON_SELECTOR, "ปุ่มค้นหา"):
                return False
            
            # 5. รอผลการค้นหา (Smart Wait - รอให้เจอผลลัพธ์หรือ error message)
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.find_elements(By.CSS_SELECTOR, config.DISBURSEMENT_CONFIRM_BUTTON_SELECTOR) or 
                                  driver.find_elements(By.CSS_SELECTOR, ".no-data, .empty-result") or
                                  driver.find_elements(By.CSS_SELECTOR, "p.text-green-chartreuse")
                )
            except TimeoutException:
                pass  # จะตรวจในขั้นตอนถัดไป
            
            
            # 6. ตรวจสอบปุ่มที่มีอยู่โดยดูจากข้อความ (เพราะใช้ selector เดียวกัน)
            table_button_selector = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-disbursement > main > section.data-table.full.rounded-none > dsl-workspace-table-v2 > div.max-w-full.overflow-x-auto > table > tbody > tr > td:nth-child(8) > div > div:nth-child(1) > dsl-workspace-button > button"
            
            # ตรวจสอบปุ่มโดยดูข้อความ
            has_import_button = self.check_button_by_text(table_button_selector, "นำเข้าเอกสาร", "ไฟล์ทำ consent แล้ว", timeout=3)
            has_disbursement_button = self.check_button_by_text(table_button_selector, "ยืนยันการเบิกเงินกู้ยืม", "ไฟล์ใหม่", timeout=3)
            
            if not has_disbursement_button and not has_import_button:
                # ตรวจสอบข้อความ "ทำแบบเบิกเงินกู้ยืมสำเร็จ" อีกครั้ง (กรณีไม่เจอปุ่ม)
                success_message_selector = "p.text-green-chartreuse"
                try:
                    success_elements = self.driver.find_elements(By.CSS_SELECTOR, success_message_selector)
                    for element in success_elements:
                        if "ทำแบบเบิกเงินกู้ยืมสำเร็จ" in element.text:
                            self.log(f"✅ พบข้อความ: {element.text}")
                            self.log(f"🎯 ไฟล์ '{filename}' ถูกดำเนินการสำเร็จแล้ว - ย้ายไป completed (ไม่เจอปุ่ม)")
                            self.log_duplicate_action(filename)  # บันทึกเป็น duplicate action
                            return True  # ถือว่าสำเร็จโดยทันที
                except Exception as e:
                    pass  # ไม่เจอก็ไม่เป็นไร
                
                self.log_warning(f"⚠️  ไม่เจอรายการสำหรับไฟล์ '{filename}' - ข้ามไปไฟล์ถัดไป")
                return False
            
            # ให้ปุ่มยืนยันการเบิกเงินกู้ยืมมีลำดับความสำคัญสูงกว่า (กรณีปกติ)
            if has_disbursement_button:
                self.log(f"🔍 พบปุ่มยืนยันการเบิกเงินกู้ยืม - ไฟล์ใหม่ ต้องทำ consent")
                
                # 6a. คลิกปุ่มยืนยันการเบิกเงินกู้ยืม
                if not self.wait_and_click(table_button_selector, "ปุ่มยืนยันการเบิกเงินกู้ยืม"):
                    return False
                
                # 7-9. จัดการ Checkbox แบบ Dynamic (รองรับ 2 หรือ 3 checkbox)
                if not self.handle_dynamic_checkboxes("disbursement"):
                    return False
                
                # 10. คลิกปุ่มยืนยันใน consent page
                if not self.wait_and_click(config.CONSENT_CONFIRM_BUTTON_SELECTOR, "ปุ่มยืนยันใน Consent Page"):
                    return False
                
                # 11. คลิกปุ่มไปหน้าเลือกไฟล์
                if not self.wait_and_click(config.GO_TO_FILE_SELECTION_BUTTON_SELECTOR, "ปุ่มไปหน้าเลือกไฟล์"):
                    return False
                    
            # กรณีพิเศษ: ไฟล์ที่ทำ consent แล้ว (ปุ่มนำเข้าเอกสาร)
            elif has_import_button:
                self.log(f"🔍 พบปุ่มนำเข้าเอกสาร - ไฟล์ทำ consent แล้ว ข้าม consent page")
                
                # 6b. คลิกปุ่มนำเข้าเอกสาร (จะพาไปหน้าเลือกไฟล์โดยตรง)
                if not self.wait_and_click(table_button_selector, "ปุ่มนำเข้าเอกสาร (ข้าม consent)"):
                    return False
            
            # 12. อัปโหลดไฟล์ (ทำงานเหมือนกันในทั้ง 2 กรณี)
            file_path = os.path.abspath(os.path.join(source_directory, filename))
            if not self.wait_and_upload_file(config.FILE_INPUT_SELECTOR, file_path, "ช่องเลือกไฟล์"):
                return False
            
            # 13. คลิกปุ่มยืนยันการอัปโหลดไฟล์
            if not self.wait_and_click(config.FILE_UPLOAD_CONFIRM_BUTTON_SELECTOR, "ปุ่มยืนยันการอัปโหลดไฟล์"):
                return False
            
            # 14. คลิกปุ่มกลับหน้าแรกเพื่อทำซ้ำ
            if not self.wait_and_click(config.BACK_TO_START_BUTTON_SELECTOR, "ปุ่มกลับหน้าแรก"):
                return False
            
            self.log(f"🎉 ดำเนินการกับไฟล์ '{filename}' เสร็จสิ้นสำเร็จ!")
            return True
            
        except Exception as e:
            self.log_error(f"💥 เกิดข้อผิดพลาดขณะดำเนินการกับไฟล์ '{filename}': {str(e)}")
            return False

    def process_sign_contract_file(self, filename, source_directory):
        """ประมวลผลไฟล์สำหรับฟีเจอร์ลงนามสัญญากู้ยืมเงิน"""
        try:
            self.log(f"🚀 เริ่มดำเนินการลงนามสัญญากับไฟล์: {filename}")
            
            # 1. Login อัตโนมัติ (เฉพาะไฟล์แรก)
            if not hasattr(self, '_sign_contract_login_completed'):
                if not self.auto_sign_contract_login():
                    return False
                self._sign_contract_login_completed = True
            else:
                # สำหรับไฟล์ถัดๆ ไป ให้ไปที่หน้าทำงานโดยตรง
                current_url = self.driver.current_url
                if config.SIGN_CONTRACT_URL not in current_url:
                    self.log(f"🎯 กลับไปหน้าลงนามสัญญา: {config.SIGN_CONTRACT_URL}")
                    self.driver.get(config.SIGN_CONTRACT_URL)
                    # รอให้หน้าโหลดเสร็จ
                    WebDriverWait(self.driver, config.PAGE_LOAD_TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, config.SIGN_CONTRACT_RADIO_SELECTOR))
                    )
                else:
                    self.log("✅ อยู่ในหน้าลงนามสัญญาแล้ว")
            
            # 2. เลือก Radio Button #radio2
            if not self.wait_and_click(config.SIGN_CONTRACT_RADIO_SELECTOR, "Radio Button #radio2 (ลงนามสัญญา)"):
                return False
            
            # 3. กรอกชื่อไฟล์ (ตัดนามสกุลออก) ในช่องค้นหา
            search_text = self.extract_filename_without_extension(filename)
            if not self.wait_and_send_keys(config.SIGN_CONTRACT_SEARCH_INPUT_SELECTOR, search_text, "ช่องค้นหา (ลงนามสัญญา)"):
                return False
            
            # 4. คลิกปุ่มค้นหา
            if not self.wait_and_click(config.SIGN_CONTRACT_SEARCH_BUTTON_SELECTOR, "ปุ่มค้นหา (ลงนามสัญญา)"):
                return False
            
            # 5. รอผลการค้นหา
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda driver: driver.find_elements(By.CSS_SELECTOR, config.SIGN_CONTRACT_BUTTON_SELECTOR) or 
                                  driver.find_elements(By.CSS_SELECTOR, ".no-data, .empty-result")
                )
            except TimeoutException:
                pass  # จะตรวจในขั้นตอนถัดไป
            
            # 6. ตรวจสอบปุ่มลงนามสัญญา
            has_sign_contract_button = self.check_button_by_text(config.SIGN_CONTRACT_BUTTON_SELECTOR, "ลงนามสัญญา", "ไฟล์พร้อมลงนามสัญญา", timeout=3)
            
            if not has_sign_contract_button:
                self.log_warning(f"⚠️  ไม่เจอรายการสำหรับไฟล์ '{filename}' - ข้ามไปไฟล์ถัดไป")
                return False
            
            self.log(f"🔍 พบปุ่มลงนามสัญญา - ไฟล์พร้อมลงนามสัญญา")
            
            # 7. คลิกปุ่มลงนามสัญญา
            if not self.wait_and_click(config.SIGN_CONTRACT_BUTTON_SELECTOR, "ปุ่มลงนามสัญญา"):
                return False
            
            # 8. จัดการ Checkbox แบบ Dynamic (รองรับ 2 หรือ 3 checkbox)
            if not self.handle_dynamic_checkboxes("sign-contract"):
                return False
            
            # 9. คลิกปุ่มยืนยันใน consent page
            if not self.wait_and_click(config.SIGN_CONTRACT_CONSENT_CONFIRM_BUTTON_SELECTOR, "ปุ่มยืนยันใน Consent Page (ลงนามสัญญา)"):
                return False
            
            # 10. คลิกปุ่มไปหน้าเลือกไฟล์
            if not self.wait_and_click(config.SIGN_CONTRACT_GO_TO_FILE_SELECTION_BUTTON_SELECTOR, "ปุ่มไปหน้าเลือกไฟล์ (ลงนามสัญญา)"):
                return False
            
            # 11. อัปโหลดไฟล์
            file_path = os.path.abspath(os.path.join(source_directory, filename))
            if not self.wait_and_upload_file(config.SIGN_CONTRACT_FILE_INPUT_SELECTOR, file_path, "ช่องเลือกไฟล์ (ลงนามสัญญา)"):
                return False
            
            # 12. คลิกปุ่มยืนยันการอัปโหลดไฟล์
            if not self.wait_and_click(config.SIGN_CONTRACT_FILE_UPLOAD_CONFIRM_BUTTON_SELECTOR, "ปุ่มยืนยันการอัปโหลดไฟล์ (ลงนามสัญญา)"):
                return False
            
            # 13. คลิกปุ่มกลับหน้าแรกเพื่อทำซ้ำ
            if not self.wait_and_click(config.SIGN_CONTRACT_BACK_TO_START_BUTTON_SELECTOR, "ปุ่มกลับหน้าแรก (ลงนามสัญญา)"):
                return False
            
            self.log(f"🎉 ลงนามสัญญากับไฟล์ '{filename}' เสร็จสิ้นสำเร็จ!")
            return True
            
        except Exception as e:
            self.log_error(f"💥 เกิดข้อผิดพลาดขณะลงนามสัญญากับไฟล์ '{filename}': {str(e)}")
            return False

    def auto_sign_contract_login(self):
        """Login และไปหน้าลงนามสัญญาอัตโนมัติ"""
        try:
            self.log("🔐 เริ่มกระบวนการ Login สำหรับลงนามสัญญา...")
            
            # 1. เปิดหน้า Login
            self.log(f"🌐 เปิดหน้า Login: {config.LOGIN_PAGE_URL}")
            self.driver.get(config.LOGIN_PAGE_URL)
            
            # รอให้หน้าโหลดเสร็จ (Smart Wait)
            WebDriverWait(self.driver, config.PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, config.USERNAME_SELECTOR))
            )
            
            # รอเพิ่มเติมให้หน้าโหลดเสร็จสมบูรณ์
            self.log("⏳ รอให้หน้า Login โหลดเสร็จสมบูรณ์...")
            time.sleep(2)
            
            # 2. ดึงข้อมูลผู้ใช้ปัจจุบัน
            current_user = self.user_manager.get_current_user()
            if not current_user:
                self.log_error("❌ ไม่พบข้อมูลผู้ใช้ กรุณาจัดการผู้ใช้งานก่อน")
                return False
            
            username = current_user['username']
            password = current_user['password']
            
            self.log(f"🔐 ใช้บัญชี: {current_user['name']} ({username})")
            
            # 3. กรอก Username
            if not self.wait_and_send_keys(config.USERNAME_SELECTOR, username, "ช่อง Username (ลงนามสัญญา)"):
                return False
            
            # 4. กรอก Password
            if not self.wait_and_send_keys(config.PASSWORD_SELECTOR, password, "ช่อง Password (ลงนามสัญญา)"):
                return False
            
            # 5. คลิกปุ่มเข้าสู่ระบบ
            if not self.wait_and_click(config.LOGIN_BUTTON_SELECTOR, "ปุ่มเข้าสู่ระบบ (ลงนามสัญญา)"):
                return False
            
            # รอสักครู่หลัง submit login
            time.sleep(3)
            
            # 6. รอให้ Login เสร็จ
            self.log("⏳ รอให้ระบบ Login เสร็จ...")
            try:
                WebDriverWait(self.driver, 30).until(
                    lambda driver: config.LOGIN_PAGE_URL not in driver.current_url
                )
            except TimeoutException:
                self.log_warning("⚠️  Login อาจใช้เวลานาน - ดำเนินการต่อ")
            
            # 7. ไปที่หน้าลงนามสัญญา
            self.log(f"🎯 ไปยังหน้าลงนามสัญญา: {config.SIGN_CONTRACT_URL}")
            self.driver.get(config.SIGN_CONTRACT_URL)
            # รอให้หน้าโหลดเสร็จ
            WebDriverWait(self.driver, config.PAGE_LOAD_TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, config.SIGN_CONTRACT_RADIO_SELECTOR))
            )
            
            
            self.log("✅ Login สำเร็จ! พร้อมเริ่มลงนามสัญญา")
            return True
            
        except Exception as e:
            self.log_error(f"❌ เกิดข้อผิดพลาดขณะ Login สำหรับลงนามสัญญา: {str(e)}")
            return False
    
    def show_menu(self):
        """แสดงเมนูเลือกฟีเจอร์"""
        clear_screen()
        current_user_info = self.user_manager.get_current_user_info()
        
        print("\n" + "="*60)
        print("🤖 DSL Auto Fill Bot - เลือกฟีเจอร์ที่ต้องการใช้งาน")
        print("="*60)
        print(f"👤 ผู้ใช้ปัจจุบัน: {current_user_info}")
        print("="*60)
        print("1. ✍️  ลงนามสัญญากู้ยืมเงิน")
        print("2. 📝 ลงนามแบบยืนยันการเบิกเงินกู้ยืม")
        print("3. 👤 จัดการผู้ใช้งาน")
        print("0. ❌ ออกจากโปรแกรม")
        print("="*60)
        
        while True:
            try:
                choice = input("🎯 กรุณาเลือกฟีเจอร์ (0-3): ").strip()
                if choice in ['0', '1', '2', '3']:
                    return choice
                else:
                    print("⚠️  กรุณาเลือกเลข 0, 1, 2, หรือ 3 เท่านั้น")
            except KeyboardInterrupt:
                print("\n⚠️  โปรแกรมถูกยกเลิกโดยผู้ใช้")
                return '0'
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
                return '0'

    def run_loan_disbursement_feature(self):
        """รันฟีเจอร์ลงนามแบบยืนยันการเบิกเงินกู้ยืม (ฟีเจอร์เดิม)"""
        try:
            self.log("🚀 เริ่มต้นฟีเจอร์: ลงนามแบบยืนยันการเบิกเงินกู้ยืม")
            
            # Reset login status สำหรับ session ใหม่
            if hasattr(self, '_login_completed'):
                delattr(self, '_login_completed')
            
            # เปิดเบราว์เซอร์เมื่อเลือกฟีเจอร์แล้ว
            self.setup_driver()
            
            # ดึงรายชื่อไฟล์จากโฟลเดอร์ disbursement
            disbursement_dir = get_files_directory() / "disbursement"
            files = self.get_files_list(disbursement_dir)
            if not files:
                self.log_warning("⚠️  ไม่พบไฟล์ในโฟลเดอร์ disbursement หรือไฟล์ไม่ถูกต้อง")
                return
            
            success_count = 0
            failed_count = 0
            skipped_count = 0
            total_files = len(files)
            
            self.log(f"📂 พบไฟล์ทั้งหมด {total_files} ไฟล์")
            
            # ดำเนินการกับแต่ละไฟล์
            for i, filename in enumerate(files, 1):
                self.log(f"\n{'='*60}")
                self.log(f"📝 กำลังดำเนินการไฟล์ที่ {i}/{total_files}: '{filename}'")
                self.log(f"{'='*60}")
                
                
                result = self.process_single_file(filename, disbursement_dir)
                
                if result:
                    success_count += 1
                    self.log(f"✅ สำเร็จ: {filename}")
                    self.log_success(filename)  # บันทึกลงไฟล์ success.log
                    
                    # ย้ายไฟล์ไปโฟลเดอร์ completed
                    self.move_file_to_completed(filename, disbursement_dir)
                    
                else:
                    # ตรวจสอบว่าเป็นการข้ามเพราะไม่เจอรายการ หรือ error จริง
                    if "ไม่เจอรายการ" in str(self.log):  # ถ้าไม่เจอรายการ
                        skipped_count += 1
                        self.log(f"⏭️  ข้าม: {filename}")
                        self.log_failed(filename)  # บันทึกลงไฟล์ failed.log (ถือว่าไม่สำเร็จ)
                        
                        # ย้ายไฟล์ไปโฟลเดอร์ failed
                        self.move_file_to_failed(filename, disbursement_dir)
                        
                    else:  # ถ้าเป็น error จริง
                        failed_count += 1
                        self.log_error(f"❌ ล้มเหลว: {filename}")
                        self.log_failed(filename)  # บันทึกลงไฟล์ failed.log
                        
                        # ย้ายไฟล์ไปโฟลเดอร์ failed
                        self.move_file_to_failed(filename, disbursement_dir)
                
                # หน่วงเวลาระหว่างไฟล์
                if i < total_files:
                    self.log(f"⏱️  รอ 2 วินาที ก่อนดำเนินการไฟล์ถัดไป...")
                    time.sleep(2)
            
            # สรุปผลการทำงาน
            self.log(f"\n{'🎯 สรุปผลการทำงาน':=^60}")
            self.log(f"📂 ไฟล์ทั้งหมด: {total_files}")
            self.log(f"✅ สำเร็จ: {success_count}")
            self.log(f"❌ ล้มเหลว: {failed_count}")
            self.log(f"⏭️  ข้าม (ไม่เจอรายการ): {skipped_count}")
            self.log(f"📊 อัตราความสำเร็จ: {(success_count/total_files*100):.1f}%")
            self.log(f"📄 ไฟล์ผลลัพธ์: success.log, failed.log, duplicate.log")
            self.log(f"{'='*60}")
            
            # เพิ่มตัวคั่นท้าย session
            session_end = f"==================== SESSION END: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Success: {success_count}/{total_files}) ====================\n\n"
            with open(str(self.success_log_file), 'a', encoding='utf-8') as f:
                f.write(session_end)
            with open(str(self.failed_log_file), 'a', encoding='utf-8') as f:
                f.write(session_end)
            
            # เพิ่มตัวคั่นท้าย session ใน duplicate.log ด้วย (ถ้ามี)
            if hasattr(self, '_duplicate_session_started'):
                duplicate_log_file = get_log_file_path("duplicate.log")
                with open(str(duplicate_log_file), 'a', encoding='utf-8') as f:
                    f.write(session_end)
            
        except KeyboardInterrupt:
            self.log_warning("⚠️  โปรแกรมถูกยกเลิกโดยผู้ใช้")
        except Exception as e:
            self.log_error(f"💥 เกิดข้อผิดพลาดร้ายแรง: {str(e)}")
        finally:
            # ปิดเบราว์เซอร์เมื่อเสร็จสิ้นฟีเจอร์
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                self.log("🔚 ปิดเบราว์เซอร์แล้ว")
                self.driver = None
            
            # รอให้ผู้ใช้กด Enter เพื่อกลับหน้าแรก
            print()
            input("กด Enter เพื่อกลับไปหน้าแรก...")

    def run_sign_contract_feature(self):
        """รันฟีเจอร์ลงนามสัญญากู้ยืมเงิน"""
        try:
            self.log("✍️  เริ่มต้นฟีเจอร์: ลงนามสัญญากู้ยืมเงิน")
            
            # Reset login status สำหรับ session ใหม่
            if hasattr(self, '_sign_contract_login_completed'):
                delattr(self, '_sign_contract_login_completed')
            
            # เปิดเบราว์เซอร์เมื่อเลือกฟีเจอร์แล้ว
            self.setup_driver()
            
            # ดึงรายชื่อไฟล์จากโฟลเดอร์ sign-contract
            sign_contract_dir = get_files_directory() / "sign-contract"
            files = self.get_files_list(sign_contract_dir)
            if not files:
                self.log_warning("⚠️  ไม่พบไฟล์ในโฟลเดอร์ sign-contract หรือไฟล์ไม่ถูกต้อง")
                return
            
            success_count = 0
            failed_count = 0
            skipped_count = 0
            total_files = len(files)
            
            self.log(f"📂 พบไฟล์ทั้งหมด {total_files} ไฟล์")
            
            # ดำเนินการกับแต่ละไฟล์
            for i, filename in enumerate(files, 1):
                self.log(f"\n{'='*60}")
                self.log(f"✍️  กำลังลงนามสัญญาไฟล์ที่ {i}/{total_files}: '{filename}'")
                self.log(f"{'='*60}")
                
                
                result = self.process_sign_contract_file(filename, sign_contract_dir)
                
                if result:
                    success_count += 1
                    self.log(f"✅ สำเร็จ: {filename}")
                    self.log_success(filename)  # บันทึกลงไฟล์ success.log
                    
                    # ย้ายไฟล์ไปโฟลเดอร์ completed
                    self.move_file_to_completed(filename, sign_contract_dir)
                    
                else:
                    # ตรวจสอบว่าเป็นการข้ามเพราะไม่เจอรายการ หรือ error จริง
                    if "ไม่เจอรายการ" in str(self.log):  # ถ้าไม่เจอรายการ
                        skipped_count += 1
                        self.log(f"⏭️  ข้าม: {filename}")
                        self.log_failed(filename)  # บันทึกลงไฟล์ failed.log (ถือว่าไม่สำเร็จ)
                        
                        # ย้ายไฟล์ไปโฟลเดอร์ failed
                        self.move_file_to_failed(filename, sign_contract_dir)
                        
                    else:  # ถ้าเป็น error จริง
                        failed_count += 1
                        self.log_error(f"❌ ล้มเหลว: {filename}")
                        self.log_failed(filename)  # บันทึกลงไฟล์ failed.log
                        
                        # ย้ายไฟล์ไปโฟลเดอร์ failed
                        self.move_file_to_failed(filename, sign_contract_dir)
                
                # หน่วงเวลาระหว่างไฟล์
                if i < total_files:
                    self.log(f"⏱️  รอ 2 วินาที ก่อนดำเนินการไฟล์ถัดไป...")
                    time.sleep(2)
            
            # สรุปผลการทำงาน
            self.log(f"\n{'🎯 สรุปผลการลงนามสัญญา':=^60}")
            self.log(f"📂 ไฟล์ทั้งหมด: {total_files}")
            self.log(f"✅ สำเร็จ: {success_count}")
            self.log(f"❌ ล้มเหลว: {failed_count}")
            self.log(f"⏭️  ข้าม (ไม่เจอรายการ): {skipped_count}")
            self.log(f"📊 อัตราความสำเร็จ: {(success_count/total_files*100):.1f}%")
            self.log(f"📄 ไฟล์ผลลัพธ์: success.log, failed.log")
            self.log(f"{'='*60}")
            
            # เพิ่มตัวคั่นท้าย session
            session_end = f"==================== SESSION END: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Success: {success_count}/{total_files}) ====================\n\n"
            with open(str(self.success_log_file), 'a', encoding='utf-8') as f:
                f.write(session_end)
            with open(str(self.failed_log_file), 'a', encoding='utf-8') as f:
                f.write(session_end)
            
        except KeyboardInterrupt:
            self.log_warning("⚠️  โปรแกรมถูกยกเลิกโดยผู้ใช้")
        except Exception as e:
            self.log_error(f"💥 เกิดข้อผิดพลาดร้ายแรง: {str(e)}")
        finally:
            # ปิดเบราว์เซอร์เมื่อเสร็จสิ้นฟีเจอร์
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                self.log("🔚 ปิดเบราว์เซอร์แล้ว")
                self.driver = None
            
            # รอให้ผู้ใช้กด Enter เพื่อกลับหน้าแรก
            print()
            input("กด Enter เพื่อกลับไปหน้าแรก...")

    def run_sign_contract_feature_wrapper(self):
        """Wrapper สำหรับ backward compatibility"""
        return self.run_sign_contract_feature()

    def run(self):
        try:
            self.log("🚀 เริ่มต้นโปรแกรม DSL Auto Fill Bot")
            
            # ตรวจสอบว่ามีผู้ใช้หรือไม่ ถ้าไม่มีให้ไปจัดการผู้ใช้ก่อน
            if not self.user_manager.get_current_user():
                clear_screen()
                self.log("⚠️  ไม่พบข้อมูลผู้ใช้ กรุณาเพิ่มผู้ใช้ก่อนใช้งาน")
                input("กด Enter เพื่อไปหน้าจัดการผู้ใช้...")
                self.user_manager.show_user_menu()
                # หลังจากออกจากเมนูผู้ใช้ ตรวจอีกครั้ง
                if not self.user_manager.get_current_user():
                    clear_screen()
                    self.log("❌ ไม่มีผู้ใช้สำหรับการทำงาน ออกจากโปรแกรม")
                    return
            
            # วนลูปแสดงเมนูหลัก
            while True:
                choice = self.show_menu()
                
                if choice == '0':
                    self.log("👋 ออกจากโปรแกรม")
                    break
                elif choice == '1':
                    self.user_manager.update_current_user_usage()
                    self.run_sign_contract_feature()
                elif choice == '2':
                    self.user_manager.update_current_user_usage()
                    self.run_loan_disbursement_feature()
                elif choice == '3':
                    self.user_manager.show_user_menu()
                    # หลังออกจากเมนูผู้ใช้ ตรวจสอบว่ายังมีผู้ใช้หรือไม่
                    if not self.user_manager.get_current_user():
                        clear_screen()
                        self.log("⚠️  ไม่มีผู้ใช้สำหรับการทำงาน")
                        input("กด Enter เพื่อดำเนินการต่อ...")
                        continue
            
        except KeyboardInterrupt:
            self.log_warning("⚠️  โปรแกรมถูกยกเลิกโดยผู้ใช้")
        except Exception as e:
            self.log_error(f"💥 เกิดข้อผิดพลาดร้ายแรง: {str(e)}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        if self.driver:
            self.driver.quit()
            self.log("🔚 ปิดเบราว์เซอร์แล้ว")

if __name__ == "__main__":
    bot = DSLAutoFillBot()
    bot.run()