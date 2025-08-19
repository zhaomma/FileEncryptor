#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import zlib
import pyzipper
import argparse
import re
import time
from pathlib import Path


def calculate_crc32_from_zip(zip_file_path):
    """从ZIP文件元数据中获取内部文件的CRC32值
    无需解压或解密ZIP文件，直接读取文件头中的CRC32值
    """
    try:
        with open(zip_file_path, 'rb') as f:
            # 读取本地文件头签名
            signature = f.read(4)
            if signature != b'PK\x03\x04':
                print(f"错误: '{zip_file_path}' 不是有效的ZIP文件")
                return None

            # 跳过到CRC32值的位置（签名后10字节）
            f.seek(10, 1)  # 从当前位置再跳过10字节

            # 读取CRC32值
            crc32_value = int.from_bytes(f.read(4), byteorder='little')
            return crc32_value
    except Exception as e:
        print(f"错误: 读取ZIP文件 '{zip_file_path}' 时出错 - {str(e)}")
        return None


def extract_encrypted_zip(zip_file_path, output_dir=None, delete_original=False):
    """解密ZIP文件"""
    # 从ZIP文件元数据中获取CRC32值作为密码
    crc32_value = calculate_crc32_from_zip(zip_file_path)
    if crc32_value is None:
        return False

    # 使用十六进制格式的CRC32值作为密码
    password = format(crc32_value, '08x').encode()

    # 确定输出目录
    if output_dir is None:
        output_dir = os.path.dirname(zip_file_path)
    else:
        os.makedirs(output_dir, exist_ok=True)

    try:
        with pyzipper.AESZipFile(zip_file_path, 'r', encryption=pyzipper.WZ_AES) as zipf:
            zipf.setpassword(password)
            # 提取所有文件
            zipf.extractall(output_dir)

        print(f"成功: ZIP文件已解密 - {zip_file_path}")
        print(f"  使用的CRC32密码 (十六进制): {format(crc32_value, '08x')}")

        # 删除原ZIP文件
        if delete_original:
            try:
                os.remove(zip_file_path)
                print(f"  原ZIP文件已删除 - {zip_file_path}")
            except Exception as e:
                print(f"  警告: 无法删除原ZIP文件 - {zip_file_path}")
                print(f"    错误信息: {str(e)}")

        return True
    except Exception as e:
        print(f"错误: 解密ZIP文件 '{zip_file_path}' 时出错 - {str(e)}")
        return False


def process_files(file_paths, output_dir=None, delete_original=False):
    """处理多个ZIP文件"""
    for file_path in file_paths:
        if not os.path.isfile(file_path):
            print(f"错误: 文件不存在 - {file_path}")
            continue

        # 检查文件是否为ZIP文件
        if not file_path.lower().endswith('.zip'):
            print(f"错误: 不是ZIP文件 - {file_path}")
            continue

        extract_encrypted_zip(file_path, output_dir, delete_original)


def process_directory(directory_path, output_dir=None, delete_original=False):
    """处理指定目录下的所有ZIP文件（不包含子文件夹）"""
    if not os.path.isdir(directory_path):
        print(f"错误: 目录不存在 - {directory_path}")
        return

    # 获取目录下的所有ZIP文件（不包含子文件夹）
    zip_paths = []
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isfile(item_path) and item_path.lower().endswith('.zip'):
            zip_paths.append(item_path)

    if not zip_paths:
        print(f"提示: 目录 '{directory_path}' 中没有找到ZIP文件")
        return

    print(f"找到 {len(zip_paths)} 个ZIP文件待处理")
    process_files(zip_paths, output_dir, delete_original)


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='批量ZIP解密工具 - 使用CRC32作为密码')
    parser.add_argument('-d', '--directory', help='要处理的目录路径')
    parser.add_argument('-o', '--output', help='输出目录路径')
    parser.add_argument('-f', '--files', nargs='+', help='要解密的ZIP文件路径列表')
    parser.add_argument('--delete', action='store_true', help='解密完成后删除原ZIP文件')
    args = parser.parse_args()

    # 检查是否安装了pyzipper
    try:
        import pyzipper
    except ImportError:
        print("错误: 未找到pyzipper库。请先安装: pip install pyzipper")
        sys.exit(1)

    print("===== PasswordCRC-Decrypt 批量ZIP解密工具 =====")
    print("功能: 批量处理加密ZIP文件，自动计算CRC32密码并解密")
    print("提示: 可指定目录处理所有ZIP文件，解密后可选择删除原文件")

    # 处理命令行参数
    if args.directory:
        process_directory(args.directory, args.output, args.delete)
    elif args.files:
        # 处理命令行参数中的文件路径，支持带空格的路径
        quotes = '"\'
        file_paths = [os.path.normpath(path.strip(quotes)) for path in args.files]
        process_files(file_paths, args.output, args.delete)
    else:
        # 交互式模式
        while True:
            print("\n请选择操作:")
            print("1. 处理指定目录下的所有ZIP文件")
            print("2. 处理指定ZIP文件")
            print("3. 退出")
            choice = input("请输入选项 (1-3): ").strip()

            if choice == '1':
                directory_path = input("请输入目录路径: ").strip()
                output_dir = input("请输入输出目录路径 (可选，直接回车表示与源文件同目录): ").strip() or None
                delete_original = input("解密后是否删除原ZIP文件? (y/n): ").strip().lower() == 'y'
                process_directory(directory_path, output_dir, delete_original)
            elif choice == '2':
                file_paths_input = input("请输入ZIP文件路径 (多个文件用空格分隔): ").strip()
                # 处理带空格的文件路径
                quotes = '"\'
                file_paths = re.findall(r'(?<![\\])[\\'"].*?(?<![\\])[\\'"]|\S+', file_paths_input)
                file_paths = [path.strip(quotes) for path in file_paths]
                output_dir = input("请输入输出目录路径 (可选，直接回车表示与源文件同目录): ").strip() or None
                delete_original = input("解密后是否删除原ZIP文件? (y/n): ").strip().lower() == 'y'
                process_files(file_paths, output_dir, delete_original)
            elif choice == '3':
                print("感谢使用，再见！")
                break
            else:
                print("无效选项，请重新输入。")


if __name__ == '__main__':
    main()