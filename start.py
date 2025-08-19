#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import platform


def check_dependencies():
    """检查是否安装了必要的依赖"""
    try:
        import pyzipper
        return True
    except ImportError:
        print("错误: 未找到pyzipper库。")
        install_choice = input("是否自动安装pyzipper库? (y/n): ").strip().lower()
        if install_choice == 'y':
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyzipper'])
                print("成功安装pyzipper库。")
                return True
            except Exception as e:
                print(f"安装pyzipper库失败: {str(e)}")
                print("请手动安装: pip install pyzipper")
                return False
        else:
            return False


def run_tool(script_name, description):
    """运行指定的工具"""
    print(f"启动 {description}...")
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    
    # 根据操作系统选择不同的启动方式
    if platform.system() == 'Windows':
        # 在Windows上使用start命令打开新窗口
        cmd = f'start cmd /k "{sys.executable} {script_path}"'
        subprocess.Popen(cmd, shell=True)
    else:
        # 在非Windows系统上直接运行
        subprocess.Popen([sys.executable, script_path])
    
    print(f"{description}已在新窗口启动。")


def main():
    """主函数"""
    print("===== PasswordCRC 工具集 =====")
    print("一个使用CRC32校验值作为密码的文件加密解密工具集")
    print("")

    # 检查依赖
    if not check_dependencies():
        print("缺少必要的依赖，无法继续。")
        input("按Enter键退出...")
        return

    while True:
        print("请选择要启动的工具:")
        print("1. 基础加密工具 (passwordcrc.py)")
        print("2. 批量加密工具 (passwordcrc-batch.py)")
        print("3. 日期组织加密工具 (passwordcrc-date.py)")
        print("4. 批量解密工具 (passwordcrc-decrypt.py)")
        print("5. 退出")

        choice = input("请输入选项 (1-5): ").strip()

        if choice == '1':
            run_tool('passwordcrc.py', '基础加密工具')
        elif choice == '2':
            run_tool('passwordcrc-batch.py', '批量加密工具')
        elif choice == '3':
            run_tool('passwordcrc-date.py', '日期组织加密工具')
        elif choice == '4':
            run_tool('passwordcrc-decrypt.py', '批量解密工具')
        elif choice == '5':
            print("感谢使用 PasswordCRC 工具集，再见！")
            break
        else:
            print("无效选项，请重新输入。")
            input("按Enter键继续...")
        
        print("")


if __name__ == '__main__':
    main()