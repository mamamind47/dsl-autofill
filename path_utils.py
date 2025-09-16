import os
import sys
from pathlib import Path

def get_app_directory():
    """
    ดึง directory ที่แอพควรใช้งาน
    รองรับทั้ง development และ executable
    """
    
    if getattr(sys, 'frozen', False):
        # รันจาก executable (PyInstaller)
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller temp directory (สำหรับไฟล์ที่ bundle มาด้วย)
            bundle_dir = Path(sys._MEIPASS)
        else:
            # Directory ของ executable
            bundle_dir = Path(sys.executable).parent
        
        # ใช้ directory ที่ executable อยู่เป็นหลัก
        app_dir = Path(sys.executable).parent
        
    else:
        # รันจาก source code
        app_dir = Path(__file__).parent
    
    return app_dir

def get_files_directory():
    """ดึง path ของโฟลเดอร์ files"""
    return get_app_directory() / "files"

def get_accounts_directory():
    """ดึง path ของโฟลเดอร์ accounts"""
    return get_app_directory() / "accounts"

def get_completed_directory():
    """ดึง path ของโฟลเดอร์ completed"""
    return get_app_directory() / "completed"

def get_failed_directory():
    """ดึง path ของโฟลเดอร์ failed"""
    return get_app_directory() / "failed"

def ensure_directories_exist():
    """สร้างโฟลเดอร์ที่จำเป็นทั้งหมด"""
    directories = [
        get_files_directory(),
        get_files_directory() / "disbursement",
        get_files_directory() / "sign-contract",
        get_accounts_directory(),
        get_completed_directory(),
        get_completed_directory() / "disbursement", 
        get_completed_directory() / "sign-contract",
        get_failed_directory(),
        get_failed_directory() / "disbursement",
        get_failed_directory() / "sign-contract"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    return True

def get_log_file_path(filename):
    """ดึง path ของไฟล์ log"""
    return get_app_directory() / filename

# Test function
if __name__ == "__main__":
    print("🔧 Testing path detection...")
    print(f"App Directory: {get_app_directory()}")
    print(f"Files Directory: {get_files_directory()}")
    print(f"Accounts Directory: {get_accounts_directory()}")
    print("✅ Path detection working!")