#! python3.9
# @author sin0n0me

import os
import subprocess
import datetime
import glob
from time import sleep
from urllib.request import urlopen, HTTPError, urlretrieve

# solution files
SOLUTION_FILES_NAME = []

# NuGet
NUGET_DOWNLOAD_URL = 'https://dist.nuget.org/win-x86-commandline/latest/nuget.exe'
NUGET_EXE_FILE_NAME = 'nuget.exe'

# MSBuile
# 'C:/Program Files (x86)/Microsoft Visual Studio/2017/Professional/MSBuild/15.0/Bin'
MSBUILED_PATH = 'C:/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin'


# Nugetパッケージの復元
def restore_nuget_package(sln_file_path_list: list) -> bool:
    # nuget.exeが存在しない場合ダウンロード
    if not os.path.exists(NUGET_EXE_FILE_NAME):
        print('download: nuget.exe')
        urlretrieve(NUGET_DOWNLOAD_URL, NUGET_EXE_FILE_NAME)
        print('done')

    # 復元
    try:
        for sln_file_path in sln_file_path_list:
            print(f'restore: nuget package filename:{sln_file_path}')
            command = ['nuget.exe', 'restore', sln_file_path]
            subprocess.run(command, check=True)
            print('restore done')
    except subprocess.CalledProcessError as e:
        print(e)
        return False

    return True


# MSBuiledで外部からコンパイルする
def exec_msbuiled(msbuiled_path: str, solution_files: list) -> bool:
    print(f'ビルドを開始します')

    # 一致するslnファイルのパスを取得
    compile_file_path_list = []
    solution_file_path_list = glob.glob('./**/*.sln', recursive=True)
    if solution_files == []:
        compile_file_path_list = solution_file_path_list  # slnファイルのパスが空なら全てコンパイル対象にする
    else:
        for solution_file_path in solution_file_path_list:
            if os.path.basename(solution_file_path) in solution_files:
                compile_file_path_list.append(
                    solution_file_path.replace('\\', '/', 128))
            elif os.path.splitext(os.path.basename(solution_file_path))[0] in solution_files:
                compile_file_path_list.append(
                    solution_file_path.replace('\\', '/', 128))

    # packages.configが存在する場合Nugetの復元
    packages_config_file = glob.glob('./**/packages.config', recursive=True)
    if packages_config_file != []:
        if not restore_nuget_package(compile_file_path_list):
            return False

    msbuiled_path = msbuiled_path.replace('"', '')
    if not os.path.exists(msbuiled_path):
        print(f'Not a valid path')
        print(f'path:"{msbuiled_path}"')
        return False

    try:
        CONFIGURATION = 0
        PLATFORM = 1

        for compile_sln_path in compile_file_path_list:

            # slnからconfigurationとPlatformを抽出
            configuration_list = []
            platform_list = []
            build_config_list: list[tuple] = []
            with open(compile_sln_path, mode='r', encoding="utf-8") as sln:
                lines = sln.readlines()
                section_start = False

                for line in lines:
                    if 'GlobalSection(SolutionConfigurationPlatforms)' in line:
                        section_start = True
                        continue

                    if 'EndGlobalSection' in line:
                        section_start = False
                        break

                    if section_start:
                        # タブ文字取り除き  \t\tWinDebug|x64 = WinDebug|x64 -> WinDebug|x64 = WinDebug|x64
                        line = line.replace('\t', '')
                        # スペース取り除き  WinDebug|x64 = WinDebug|x64 -> WinDebug|x64=WinDebug|x64
                        line = line.replace(' ', '')
                        # =で分割          WinDebug|x64=WinDebug|x64 -> [WinDebug|x64][WinDebug|x64]
                        line = line.split('=')
                        # |でさらに分割     WinDebug|x64 -> [WinDebug][x64]
                        line = line[0].split('|')

                        build_config_list.append(
                            (line[CONFIGURATION], line[PLATFORM]))

                        configuration_list.append(line[CONFIGURATION])
                        platform_list.append(line[PLATFORM])

            print(f'configuration:"{configuration_list}"')
            print(f'Platform:"{platform_list}"')

            # build
            for build_config in build_config_list:
                configuration = build_config[CONFIGURATION]
                platform = build_config[PLATFORM]

                print(f'compile sln file path:{compile_sln_path}')
                print(f'configuration:{configuration}')
                print(f'platform:{platform}')
                print(f'build start\n')

                command = [
                    f'{msbuiled_path}/MSBuild.exe',
                    compile_sln_path,
                    f'/t:build',
                    f'/p:configuration={configuration}',
                    f'/p:Platform={platform}'
                ]

                subprocess.run(command, check=True)
                print(f'build done\n')

    except subprocess.CalledProcessError as e:
        print(e)
        return False

    return True


def main() -> int:
    start_time = datetime.datetime.now()

    # compile
    if not exec_msbuiled(MSBUILED_PATH, SOLUTION_FILES_NAME):
        return -1
    print(f'経過時間:' + str(datetime.datetime.now() - start_time))


if __name__ == '__main__':
    main()
    count = 10
    for i in range(count):
        print('\r %d 秒後に終了します ' % (count - i), end='')
        sleep(1)
