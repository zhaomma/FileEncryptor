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


def calculate_crc32(file_path):
    """计算文件的CRC32值"""
    crc = 0
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            crc = zlib.crc32(chunk, crc)
    # 返回无符号整数形式的CRC32值
    return crc & 0xFFFFFFFF


def create_encrypted_zip(file_path, output_dir=None):
    """创建加密ZIP文件，使用CRC32作为密码"""
    # 计算文件的CRC32值作为密码（使用十六进制格式）
    crc32_value = calculate_crc32(file_path)
    password = format(crc32_value, '08x').encode()

    # 获取文件名和扩展名
    file_name = os.path.basename(file_path)
    file_stem, file_ext = os.path.splitext(file_name)

    # 确定输出目录
    if output_dir is None:
        output_dir = os.path.dirname(file_path)
    else:
        os.makedirs(output_dir, exist_ok=True)

    # 创建输出文件名（包含原扩展名）
    output_file = os.path.join(output_dir, f"{file_stem}{file_ext}.zip")

    # 创建无压缩的加密ZIP文件
    with pyzipper.AESZipFile(output_file, 'w', compression=pyzipper.ZIP_STORED, encryption=pyzipper.WZ_AES) as zipf:
        zipf.setpassword(password)
        zipf.write(file_path, arcname=file_name)

    return output_file, crc32_value


def process_files(file_paths, output_dir=None, delete_original=False):
    """处理多个文件"""
    for file_path in file_paths:
        if not os.path.isfile(file_path):
            print(f"错误: 文件不存在 - {file_path}")
            continue

        try:
            output_file, crc32_value = create_encrypted_zip(file_path, output_dir)
            print(f"成功: 文件已加密 - {output_file}")
            print(f"  CRC32密码 (十六进制): {format(crc32_value, '08x')}")

            # 删除原文件
            if delete_original:
                try:
                    os.remove(file_path)
                    print(f"  原文件已删除 - {file_path}")
                except Exception as e:
                    print(f"  警告: 无法删除原文件 - {file_path}")
                    print(f"    错误信息: {str(e)}")
        except Exception as e:
            print(f"错误: 处理文件时出错 - {file_path}")
            print(f"  错误信息: {str(e)}")


def process_directory(directory_path, output_dir=None, delete_original=False):
    """处理指定目录下的所有文件（不包含子文件夹）"""
    if not os.path.isdir(directory_path):
        print(f"错误: 目录不存在 - {directory_path}")
        return

    # 获取目录下的所有文件（不包含子文件夹）
    file_paths = []
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isfile(item_path):
            file_paths.append(item_path)

    if not file_paths:
        print(f"提示: 目录 '{directory_path}' 中没有找到文件")
        return

    print(f"找到 {len(file_paths)} 个文件待处理")
    process_files(file_paths, output_dir, delete_original)


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='批量文件加密工具 - 使用CRC32作为密码')
    parser.add_argument('-d', '--directory', help='要处理的目录路径')
    parser.add_argument('-o', '--output', help='输出目录路径')
    parser.add_argument('-f', '--files', nargs='+', help='要加密的文件路径列表')
    parser.add_argument('--delete', action='store_true', help='加密完成后删除原文件')
    args = parser.parse_args()

    # 检查是否安装了pyzipper
    try:
        import pyzipper
    except ImportError:
        print("错误: 未找到pyzipper库。请先安装: pip install pyzipper")
        sys.exit(1)

    print("===== PasswordCRC-Batch 批量文件加密工具 =====")
    print("功能: 批量处理目录下文件，计算CRC32值作为密码，创建无压缩加密ZIP文件")
    print("提示: 可指定目录处理所有文件，加密后可选择删除原文件")

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
            print("1. 处理指定目录下的所有文件")
            print("2. 处理指定文件")
            print("3. 退出")
            choice = input("请输入选项 (1-3): ").strip()

            if choice == '1':
                directory_path = input("请输入目录路径: ").strip()
                if not directory_path:
                    print("错误: 目录路径不能为空")
                    continue
                output_dir = input("请输入输出目录路径 (可选): ").strip() or None
                delete_original = input("加密完成后是否删除原文件? (y/n): ").strip().lower() == 'y'
                process_directory(directory_path, output_dir, delete_original)
            elif choice == '2':
                print("请输入文件路径 (多个文件用空格分隔):")
                input_line = input().strip()
                if not input_line:
                    print("错误: 文件路径不能为空")
                    continue
                # 处理带空格的路径（支持引号包围）
                file_paths = re.findall(r'(?:"[^"]*"|\\'[^\']*\\'|[^\s]+)', input_line)
                # 去除路径中的引号并标准化路径
                quotes = '"\'
                file_paths = [os.path.normpath(path.strip(quotes)) for path in file_paths]
                output_dir = input("请输入输出目录路径 (可选): ").strip() or None
                delete_original = input("加密完成后是否删除原文件? (y/n): ").strip().lower() == 'y'
                process_files(file_paths, output_dir, delete_original)
            elif choice == '3':
                print("程序已退出。")
                sys.exit(0)
            else:
                print("错误: 无效的选项，请重新输入")

    print("\n所有操作已完成。")


if __name__ == '__main__':
    main()