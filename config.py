import os

# การตั้งค่าเว็บไซต์
WEBSITE_URL = "https://agent.dsl.studentloan.or.th/main/disbursement-list"
SIGN_CONTRACT_URL = "https://agent.dsl.studentloan.or.th/main/sign-contract-list"  # หน้าลงนามสัญญา
LOGIN_PAGE_URL = "https://agent.dsl.studentloan.or.th/los/login"  # หน้า Login

# การตั้งค่า Login
USERNAME_SELECTOR = "#username"   # ช่องกรอก username
PASSWORD_SELECTOR = "#password"   # ช่องกรอก password  
LOGIN_BUTTON_SELECTOR = "#button" # ปุ่มเข้าสู่ระบบ

# 1. Radio Button สำหรับเลือกประเภท (ปรับตาม element จริง)
RADIO_SELECTOR = 'input[name="radio2"][value="B"]'  # ใช้ attribute แทน

# 2. ช่องกรอกชื่อไฟล์สำหรับค้นหา
SEARCH_INPUT_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-disbursement > main > section[class*='criteria search'] > dsl-workspace-form-search-v2 > div[class*='form-search'] > form > div > div > div:nth-child(5) > input"

# 3. ปุ่มค้นหา
SEARCH_BUTTON_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-disbursement > main > section[class*='criteria search'] > dsl-workspace-form-search-v2 > div:nth-child(3) > footer > div > dsl-workspace-button:nth-child(2) > button"

# 4. ปุ่มยืนยันแบบเบิก (หลังจากค้นหาเจอ)
DISBURSEMENT_CONFIRM_BUTTON_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-disbursement > main > section[class*='data-table'].full.rounded-none > dsl-workspace-table-v2 > div.max-w-full.overflow-x-auto > table > tbody > tr > td:nth-child(8) > div > div:nth-child(1) > dsl-workspace-button > button"

# 5. Checkbox ที่ 1 - Address Panel
ADDRESS_CHECKBOX_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-disbursement-consent-doc > main > div.px-20.mt-12.ng-star-inserted > section:nth-child(2) > app-address-panel > div > label > input"

# 6. Checkbox ที่ 2 - Contract Panel (กรณี 2 checkbox - Disbursement)
CONTRACT_CHECKBOX_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-disbursement-consent-doc > main > div.px-20.mt-12.ng-star-inserted > section:nth-child(4) > dsl-workspace-confirm-contract-panel > label > input"

# 6b. Checkbox Contract สำหรับกรณี 3 checkbox (Disbursement)
CONTRACT_CHECKBOX_3_CASE_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-disbursement-consent-doc > main > div.px-20.mt-12.ng-star-inserted > section:nth-child(5) > dsl-workspace-confirm-contract-panel > label > input"

# 7. Checkbox ที่ 3 - Optional (บางรายการมี บางรายการไม่มี)
OPTIONAL_CHECKBOX_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-disbursement-consent-doc > main > div.px-20.mt-12.ng-star-inserted > section.ng-star-inserted > app-address-panel > div > label > input"

# 7. ปุ่มยืนยันใน consent page
CONSENT_CONFIRM_BUTTON_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-disbursement-consent-doc > footer > dsl-workspace-button.ng-star-inserted > button"

# 8. ปุ่มไปหน้าเลือกไฟล์
GO_TO_FILE_SELECTION_BUTTON_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-disbursement-consent-success > main > section > div.flex.gap-9.justify-center.my-6 > dsl-workspace-button > button"

# 9. ปุ่มเลือกไฟล์ (input file hidden)
FILE_INPUT_SELECTOR = "#frontImage0"

# 10. ปุ่มยืนยันการอัปโหลดไฟล์
FILE_UPLOAD_CONFIRM_BUTTON_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-disbursement-import-file > footer > dsl-workspace-button.ng-star-inserted > button"

# 11. ปุ่มกลับหน้าแรกเพื่อทำซ้ำ
BACK_TO_START_BUTTON_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-disbursement-import-file-success > main > section > div.flex.gap-9.justify-center.my-6 > dsl-workspace-button > button"

# =================== Selectors สำหรับฟีเจอร์ลงนามสัญญากู้ยืมเงิน ===================

# 1. Radio Button สำหรับเลือกประเภท (เดียวกับฟีเจอร์เดิม)
SIGN_CONTRACT_RADIO_SELECTOR = 'input[name="radio2"][value="B"]'

# 2. ช่องกรอกชื่อไฟล์สำหรับค้นหา
SIGN_CONTRACT_SEARCH_INPUT_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-sign-contract > main > section[class*='criteria search'] > dsl-workspace-form-search-v2 > div[class*='form-search'] > form > div > div > div:nth-child(5) > input"

# 3. ปุ่มค้นหา
SIGN_CONTRACT_SEARCH_BUTTON_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-sign-contract > main > section[class*='criteria search'] > dsl-workspace-form-search-v2 > div:nth-child(3) > footer > div > dsl-workspace-button:nth-child(2) > button"

# 4. ปุ่มลงนามสัญญา (หลังจากค้นหาเจอ)
SIGN_CONTRACT_BUTTON_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-sign-contract > main > section[class*='data-table'].full.rounded-none > dsl-workspace-table-v2 > div.max-w-full.overflow-x-auto > table > tbody > tr > td:nth-child(8) > div > div:nth-child(1) > dsl-workspace-button > button"

# 5. Checkbox ที่ 1 - Address Panel
SIGN_CONTRACT_ADDRESS_CHECKBOX_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-sign-contract-consent-doc > main > div > section:nth-child(2) > app-address-panel > div > label > input"

# 6. Checkbox ที่ 2 - Contract Panel (กรณี 3 checkbox)
SIGN_CONTRACT_CONTRACT_CHECKBOX_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-sign-contract-consent-doc > main > div > section:nth-child(4) > dsl-workspace-confirm-contract-panel > label > input"

# 6b. Checkbox Contract สำหรับกรณี 2 checkbox (Sign Contract)
SIGN_CONTRACT_CONTRACT_CHECKBOX_2_CASE_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-sign-contract-consent-doc > main > div > section:nth-child(3) > dsl-workspace-confirm-contract-panel > label > input"

# 7. Checkbox ที่ 3 - Optional (บางรายการมี บางรายการไม่มี)
SIGN_CONTRACT_OPTIONAL_CHECKBOX_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-sign-contract-consent-doc > main > div > section.ng-star-inserted > app-address-panel > div > label > input"

# 8. ปุ่มยืนยันใน consent page
SIGN_CONTRACT_CONSENT_CONFIRM_BUTTON_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-sign-contract-consent-doc > footer > dsl-workspace-button.ng-star-inserted > button"

# 9. ปุ่มไปหน้าเลือกไฟล์
SIGN_CONTRACT_GO_TO_FILE_SELECTION_BUTTON_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-sign-contract-consent-success > main > section > div.flex.gap-9.justify-center.my-6 > dsl-workspace-button:nth-child(2) > button"

# 10. ปุ่มเลือกไฟล์ (input file hidden) - ใช้เดียวกับฟีเจอร์เดิม
SIGN_CONTRACT_FILE_INPUT_SELECTOR = "#frontImage0"

# 11. ปุ่มยืนยันการอัปโหลดไฟล์
SIGN_CONTRACT_FILE_UPLOAD_CONFIRM_BUTTON_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-sign-contract-import-file > footer > dsl-workspace-button.ng-star-inserted > button"

# 12. ปุ่มกลับหน้าแรกเพื่อทำซ้ำ
SIGN_CONTRACT_BACK_TO_START_BUTTON_SELECTOR = "body > dsl-workspace-root > app-content-layout > div > div > main > article > dsl-workspace-sign-contract-import-file-success > main > section > div.flex.gap-9.justify-center.my-6 > dsl-workspace-button:nth-child(1) > button"

# การตั้งค่าไฟล์
# หมายเหตุ: ไดเรกทอรีจะถูกจัดการโดย path_utils.py เพื่อรองรับ executable
ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.png']  # นามสกุลไฟล์ที่อนุญาต

# การตั้งค่าการรอคอย (วินาที)
WAIT_TIME = 2  # รอคอยระหว่างการทำงานแต่ละขั้นตอน
PAGE_LOAD_TIMEOUT = 10  # รอหน้าเว็บโหลด
ELEMENT_WAIT_TIMEOUT = 10  # รอ element ปรากฏ

# การตั้งค่า WebDriver
USE_EXISTING_BROWSER = False  # True = ใช้เบราว์เซอร์ที่เปิดอยู่แล้ว, False = เปิดใหม่
CHROME_DEBUG_PORT = 9222      # พอร์ตสำหรับเชื่อมต่อกับ Chrome ที่เปิดอยู่
LOGIN_WAIT_TIME = 30          # เวลารอให้ผู้ใช้ login (วินาที)
HEADLESS_MODE = False         # True = รันแบบไม่แสดงหน้าต่าง, False = แสดงหน้าต่าง
WINDOW_SIZE = (1920, 1080)    # ขนาดหน้าต่างเบราว์เซอร์

# การตั้งค่า Log
LOG_ENABLED = True  # เปิด/ปิด การบันทึก log
LOG_FILE = "autofill.log"  # ชื่อไฟล์ log