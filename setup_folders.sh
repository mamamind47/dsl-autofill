#!/bin/bash

echo "===================================="
echo "🤖 DSL Auto Fill Bot - Setup Folders"
echo "===================================="
echo

echo "📁 สร้างโฟลเดอร์หลัก..."
mkdir -p "files"
mkdir -p "completed"
mkdir -p "failed"

echo "📁 สร้างโฟลเดอร์สำหรับ Input Files..."
mkdir -p "files/disbursement"
mkdir -p "files/sign-contract"

echo "📁 สร้างโฟลเดอร์สำหรับ Completed Files..."
mkdir -p "completed/disbursement"
mkdir -p "completed/sign-contract"

echo "📁 สร้างโฟลเดอร์สำหรับ Failed Files..."
mkdir -p "failed/disbursement"
mkdir -p "failed/sign-contract"

echo
echo "✅ สร้างโฟลเดอร์เสร็จสิ้น!"
echo
echo "📂 โครงสร้างโฟลเดอร์:"
echo "   files/"
echo "   ├── disbursement/     (ไฟล์สำหรับลงนามแบบเบิกเงิน)"
echo "   └── sign-contract/    (ไฟล์สำหรับลงนามสัญญา)"
echo
echo "   completed/"
echo "   ├── disbursement/     (ไฟล์ที่สำเร็จ - เบิกเงิน)"
echo "   └── sign-contract/    (ไฟล์ที่สำเร็จ - ลงนามสัญญา)"
echo
echo "   failed/"
echo "   ├── disbursement/     (ไฟล์ที่ล้มเหลว - เบิกเงิน)"
echo "   └── sign-contract/    (ไฟล์ที่ล้มเหลว - ลงนามสัญญา)"
echo
echo "💡 วิธีใช้งาน:"
echo "   1. ใส่ไฟล์ PDF ใน files/disbursement/ หรือ files/sign-contract/"
echo "   2. รันโปรแกรม: python3 main.py"
echo "   3. ตรวจสอบผลลัพธ์ใน completed/ และ failed/"
echo
echo "📋 Log Files ที่จะถูกสร้าง:"
echo "   - success.log      (ไฟล์ที่สำเร็จ)"
echo "   - failed.log       (ไฟล์ที่ล้มเหลว)"
echo "   - duplicate.log    (ไฟล์ที่ทำซ้ำ)"
echo "   - autofill.log     (Log หลัก)"
echo
echo "กด Enter เพื่อปิด..."
read