#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import zlib
import pyzipper
import argparse
import re
import datetime
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
    
    # 生成日期时间文件夹名（年-月-日-时-分-秒）
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    # 创建带日期时间的完整输出目录
    full_output_dir = os.path.join(output_dir, timestamp)
    os.makedirs(full_output_dir, exist_ok=True)

    # 创建输出文件名（包含原扩展名）
    output_file = os.path.join(full_output_dir, f"{file_stem}{file_ext}.zip")

    # 创建无压缩的加密ZIP文件
    with pyzipper.AESZipFile(output_file, 'w', compression=pyzipper.ZIP_STORED, encryption=pyzipper.WZ_AES) as zipf:
        zipf.setpassword(password)
        zipf.write(file_path, arcname=file_name)

    return output_file, crc32_value


def process_files(file_paths, output_dir=None):
    """处理多个文件"""
    for file_path in file_paths:
        if not os.path.isfile(file_path):
            print(f"错误: 文件不存在 - {file_path}")
            continue

        try:
            output_file, crc32_value = create_encrypted_zip(file_path, output_dir)
            print(f"成功: 文件已加密 - {output_file}")
            print(f"  CRC32密码 (十六进制): {format(crc32_value, '08x')}")
        except Exception as e:
            print(f"错误: 处理文件时出错 - {file_path}")
            print(f"  错误信息: {str(e)}")


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='文件加密工具 - 使用CRC32作为密码，并按日期时间组织输出')
    parser.add_argument('-f', '--files', nargs='+', help='要加密的文件路径列表')
    parser.add_argument('-o', '--output', help='输出目录路径')
    args = parser.parse_args()

    # 检查是否安装了pyzipper
    try:
        import pyzipper
    except ImportError:
        print("错误: 未找到pyzipper库。请先安装: pip install pyzipper")
        sys.exit(1)

    print("===== PasswordCRC-Date 文件加密工具 =====")
    print("功能: 计算文件CRC32值作为密码，创建无压缩加密ZIP文件，并按日期时间组织输出")
    print("提示: 可直接拖放文件到窗口进行处理")

    while True:
        # 检查命令行参数中的文件
        if args.files:
            # 处理命令行参数中的文件路径，支持带空格的路径
            quotes = '"\'
            file_paths = [os.path.normpath(path.strip(quotes)) for path in args.files]
            # 处理完命令行参数中的文件后清除，避免循环处理
            args.files = None
        else:
            # 提示用户输入文件路径
            print("\n请输入文件路径 (多个文件用空格分隔，直接回车重新开始):")
            input_line = input().strip()
            if not input_line:
                continue
            # 处理带空格的路径（支持引号包围）
            # 使用正则表达式安全地分割带引号的路径
            file_paths = re.findall(r'(?:"[^"]*"|\\'[^\']*\\'|[^\s]+)', input_line)
            # 去除路径中的引号并标准化路径
            quotes = '"\'
            file_paths = [os.path.normpath(path.strip(quotes)) for path in file_paths]

        # 处理文件
        process_files(file_paths, args.output)

        # 处理完成，直接继续处理其他文件
        print("\n处理完成，继续等待新文件输入...")
        # 短暂暂停，让用户有时间阅读信息
        import time
        time.sleep(0.5)

    print("程序已退出。")


if __name__ == '__main__':
    main()