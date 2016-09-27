# -*- coding: utf-8 -*-
import os
import sys
import time
import hashlib
import subprocess
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib

# Project相关

PROJECT_WORKSPACE = "xxxx.xcworkspace"

PROJECT_NAME = "xxxx.xcodeproj"
# scheme
PROJECT_SCHEME = "xxxx"

PROJECT_TARGET = "xxxx"
# 相关证书
# IN HOUSE
CODE_SIGN_IDENTITY_INHOUSE = "xxxxxxx"
PROVISIONING_PROFILE_INHOUSE = "xxxxxxxxxxxxx"
CONFIGURATION_INHOUSE = "InHouse"
BUNDLE_ID_INHOUSE = "com.xxx.xxxx"
# APP STORE
CODE_SIGN_IDENTITY_APP_STORE = "xxxxxxxxxxxxxxxxxx"
PROVISIONING_PROFILE_APP_STORE = "xxxxxxxxxxx"
CONFIGURATION_APP_STORE = "Release"
BUNDLE_ID_APP_STORE = "com.xxxx.xxxx"

# firm的api token
FIR_API_TOKEN = "xxxxxxxxxxxxxxxxxxxx"

MAIL_FROM_ADDRESS = "xxxxx@sina.com"
MAIL_PASSWORD = "8888888888"
SMTP_SERVER = "smtp.sina.com"
MAIL_TO_ADDRESS = 'aa@qq.com,bb@qq.com'

# pgyerd的api key
PGYER_USER_KEY = "xxxxxxxxx"
PGYER_API_KEY = "xxxxxxxxxx"


# 清理项目 创建build目录
def clean_project_mkdir_build(project_path):
    os.system('cd %s;xcodebuild clean' % project_path)  # clean 项目
    build_path = '%s/build' % (project_path)
    print "buildDir %s" % (build_path);
    if os.path.exists(build_path):
        cleanCmd = "rm -r %s" % (build_path)
        os.system(cleanCmd)
    os.system('cd %s;mkdir build' % project_path)

#构建企业版
def build_inhouse_workspace(project_path):
    print("build release inhouse start")
    os.system('xcodebuild -list')
    build_path = '%s/build' % (project_path)

    buildCmd = 'xcodebuild -workspace %s -scheme %s -sdk iphoneos -configuration %s build CODE_SIGN_IDENTITY="%s"' \
               ' PROVISIONING_PROFILE="%s" SYMROOT=%s' % (PROJECT_WORKSPACE, PROJECT_SCHEME, CONFIGURATION_INHOUSE,
                                                          CODE_SIGN_IDENTITY_INHOUSE, PROVISIONING_PROFILE_INHOUSE,
                                                          build_path)
    os.system(buildCmd)

#构建AppStore版本
def build_app_store_workspace(project_path):
    print("build release app store start")
    os.system('xcodebuild -list')
    build_path = '%s/build' % (project_path)

    buildCmd = 'xcodebuild -workspace %s -scheme %s -sdk iphoneos -configuration %s build CODE_SIGN_IDENTITY="%s"' \
               ' PROVISIONING_PROFILE="%s" SYMROOT=%s' % (PROJECT_WORKSPACE, PROJECT_SCHEME, CONFIGURATION_APP_STORE,
                                                          CODE_SIGN_IDENTITY_APP_STORE, PROVISIONING_PROFILE_APP_STORE,
                                                          build_path)
    os.system(buildCmd)


# 打包ipa 并且保存在桌面
def build_ipa(output_path, configuration):

    ipa_filename = time.strftime('ChunyuYuer_%Y-%m-%d-%H-%M-%S.ipa', time.localtime(time.time()))
    signApp = "./build/%s-iphoneos/%s.app" % (configuration, PROJECT_SCHEME)
    if os.path.exists(signApp):
        signCmd = "xcrun -sdk iphoneos -v PackageApplication %s -o %s/%s" % (signApp, output_path, ipa_filename)
        os.system(signCmd)
        return ipa_filename
    else:
        print("没有找到app文件")
        return ''

#修改bundleId
def modify_bundle_id():
    modifyBundle = "sed -i '' 's/%s/%s/g' ./%s/project.pbxproj" % (BUNDLE_ID_APP_STORE,BUNDLE_ID_INHOUSE,PROJECT_NAME)
    os.system(modifyBundle)

#还原bundleId
def restore_bundle_id():
    modifyBundle = "sed -i '' 's/%s/%s/g' ./%s/project.pbxproj" % (BUNDLE_ID_INHOUSE,BUNDLE_ID_APP_STORE, PROJECT_NAME)
    os.system(modifyBundle)

#增加版本号
def increase_build_number(project_path):
    build_number_shell = '/usr/libexec/PlistBuddy -c "Print CFBundleVersion" "%s/%s/Info.plist"' % (
    project_path, PROJECT_SCHEME)
    process = subprocess.Popen(build_number_shell, stdout=subprocess.PIPE, shell=True)
    (stdoutdata, stderrdata) = process.communicate()

    build_number = stdoutdata
    print('build_number %s' % (build_number))
    set_build_number = '/usr/libexec/PlistBuddy -c "Set :CFBundleVersion %s" "%s/%s/Info.plist"' % (
    int(build_number) + 1, project_path, PROJECT_SCHEME)
    os.system(set_build_number)


# 上传到fir
def upload_fir(output_path, file_name):
    if os.path.exists("%s/%s" % (output_path, file_name)):
        print('uploading...')
        # 直接使用fir 有问题 这里使用了绝对地址 在终端通过 which fir 获得
        ret = os.system("/usr/local/bin/fir p '%s/%s' -T '%s'" % (output_path, file_name, FIR_API_TOKEN))
    else:
        print("没有找到ipa文件")


# 上传到蒲公英
def upload_pgyer(output_path, file_name):
    if os.path.exists("%s/%s" % (output_path, file_name)):
        print('uploading...')
        os.system("curl -F 'file=@%s/%s' -F 'uKey=%s' -F '_api_key=%s' http://www.pgyer.com/apiv1/app/upload" % (
        output_path, file_name, PGYER_USER_KEY, PGYER_API_KEY))
    else:
        print("没有找到ipa文件")

#格式化地址
def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


# 发邮件

def send_mail():
    msg = MIMEText('xx iOS测试项目已经打包完毕，请前往 http://fir.im/xxxxx 下载测试！', 'plain', 'utf-8')
    msg['From'] = _format_addr('自动打包系统 <%s>' % MAIL_FROM_ADDRESS)
    msg['To'] = _format_addr('xx测试人员 <%s>' % MAIL_TO_ADDRESS)
    msg['Subject'] = Header('xx iOS客户端打包程序', 'utf-8').encode()
    server = smtplib.SMTP(SMTP_SERVER, 25)
    server.set_debuglevel(1)
    server.login(MAIL_FROM_ADDRESS, MAIL_PASSWORD)
    server.sendmail(MAIL_FROM_ADDRESS, [MAIL_TO_ADDRESS], msg.as_string())
    server.quit()

# 获取输入文件路径

def get_output_path(project_path):
    items = project_path.split("/")
    user_path = "/".join(items[:3])
    output_path = "%s/Desktop" % (user_path)
    return output_path

# 打包 InHouse
def build_inhouse(project_path):
    # 清理并创建build目录
    clean_project_mkdir_build(project_path)
    # 增加build号
    increase_build_number(project_path)
    # 修改bundle
    modify_bundle_id()
    # 编译coocaPods项目文件并 执行编译目录
    build_inhouse_workspace(project_path)
    # 打包ipa 并放到桌面

    file_name = build_ipa(get_output_path(project_path), CONFIGURATION_INHOUSE)
    print("%s" % (file_name))
    if len(file_name) > 0:
        # 上传蒲公英
        upload_pgyer(get_output_path(project_path), file_name)
    # 修改会原来的bundleId
    restore_bundle_id()
    # 上传fir
    # upload_fir(get_output_path(project_path), file_name)
    # 发邮件
    # send_mail()

# 打包 App Store
def build_appstore(project_path):
    # 清理并创建build目录
    clean_project_mkdir_build(project_path)
    # 编译coocaPods项目文件并 执行编译目录
    # 增加build号
    increase_build_number(project_path)
    # 构建
    build_app_store_workspace(project_path)
    # 打包ipa 并放到桌面
    build_ipa(get_output_path(project_path), CONFIGURATION_APP_STORE)


def main():
    # 打包环境,如果type是inhouse,则打包企业版本,自动上传,如果是appstore则是打包到app store
    # python make_ipa.py appstore 则打的包用于上传app store
    # python make_ipa.py 打的包是In house,用于内部测试，其中包含菜单选择页面
    args = sys.argv;

    # 获取当前目录
    #os.getcwd()
    process = subprocess.Popen("pwd", stdout=subprocess.PIPE)
    (stdoutdata, stderrdata) = process.communicate()
    project_path = stdoutdata.strip()

    if len(args) > 1:
        type = sys.argv[1]
        if type == 'appstore':
            build_appstore(project_path)
        else:
            build_inhouse(project_path)
    else:
        build_inhouse(project_path)


# 执行
main()
