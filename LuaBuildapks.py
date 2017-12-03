# coding:UTF-8
# encoding: utf-8
#__author__ = 'zhufx'
from publicfun import *
from LuaProperty import gameConf
from LuaDiff2zip import contrastdict,lua_hotupdate_zip
from configobj import ConfigObj
import re,zipfile
import sys
import chardet
reload(sys)
sys.setdefaultencoding('utf-8')

BuildConfig = {
    'appName':'shmj_an',
    'buildType':'125',
    'recommendID':'',
    'channel':'tcyapp',
    'isUpdateSVN':'Y',
    'isEncrypt':'N',
    'isYQW':'Y'
    }

def getandversionNum(fd):
    proj_version_pattern = r'android:versionName=(\'|")(.*?)(\'|")'
    andVersionName = re.compile(proj_version_pattern,re.I)
    match = andVersionName.search(fd)
    andversionName = match.group(2).replace('.', '_')
    return andversionName

def chgandversionNum(fp,versionNumStr="1.0.20110328",versionCodeStr=None):
    fd = open(fp,'rb').read()
    proj_version_pattern = r'android:versionName=(\'|")(.*?)(\'|")'
    andVersionNum = re.compile(proj_version_pattern)
    versionNum_repl_text = 'android:versionName="%s"' % versionNumStr
    proj_versionCode_pattern = r'android:versionCode=(\'|")(.*?)(\'|")'
    andVersionCode = re.compile(proj_versionCode_pattern)
    if not versionCodeStr:
        versionCodeStr = int(andVersionCode.search(fd).group(2)) - 1
    versionCode_repl_text = 'android:versionCode="%s"' % str(versionCodeStr)
    fd = andVersionNum.sub(versionNum_repl_text,fd)
    fd = andVersionCode.sub(versionCode_repl_text,fd)
    writefile(fd,fp)

def getandpackname(fd):
    proj_package_pattern = r'package=(\'|")(.*?)(\'|")'
    andpackname = re.compile(proj_package_pattern)
    match = andpackname.search(fd)
    andpackname = match.group(2)
    return andpackname

def setAntENV(prop):
    #prop = gameConf(appname)
    #prop.setProVersion(versionNum,proVersion)
    locPropConf = ConfigObj(prop.local_properties_path)
    locPropConf['sdk.dir'] = prop.android_sdk_dir
    locPropConf['key.store'] = prop.key_store_dir
    locPropConf['key.alias'] = prop.key_alias
    if prop.appName == "zhji_an" and prop.proVersion == "huawei":
        locPropConf['key.store'] = "E:/keystores/zhji_an_huawei"
    locPropConf['key.store.password'] = prop.key_store_password
    locPropConf['key.alias.password'] = prop.key_alias_password
    locPropConf.write()

def setBuildTarget(fp,tnum):
    locPropConf = ConfigObj(fp)
    androidtarget = "android-%s" % tnum
    locPropConf['target'] = androidtarget
    locPropConf.write()

def setUmengChannel(fpath,UMENG_CHANNEL,fpath2):
    if not os.path.exists(fpath):
        return;
    fd = open(fpath,'r').read()
    if isinstance(UMENG_CHANNEL,unicode):
        UMENG_CHANNEL = UMENG_CHANNEL.encode('utf-8','ignore')

    #替换友盟渠道
    umengchannel_pattern2 = r'android:value=(\'|")(.*?)(\'|")' \
                            + r'(\s)*android:name=(\s)*(\'|")UMENG_CHANNEL(\'|")'
    umengchannel_pattern = r'android:name=(\'|")UMENG_CHANNEL(\'|")'  \
                            + r'(\s)*android:value=(\s)*(\'|")(.*?)(\'|")'
    umengchannel_replace_text = 'android:name="UMENG_CHANNEL" android:value="%s"' % UMENG_CHANNEL
    r = re.compile(umengchannel_pattern)
    r2 = re.compile(umengchannel_pattern2)
    match = r.search(fd,re.I)
    match2 = r2.search(fd,re.I)
    if not isinstance(UMENG_CHANNEL,str):
        UMENG_CHANNEL = str(UMENG_CHANNEL)
    ChannelConfig = getjson(fpath2)
    ChannelConfig["channelId"] = UMENG_CHANNEL
    if match is not None:
        fd = r.sub(umengchannel_replace_text,fd)
    elif match2 is not None:
        fd = r2.sub(umengchannel_replace_text,fd)
    writefile(fd,fpath)
    if os.path.exists(fpath2):
        savejson(fd=ChannelConfig,fpath=fpath2)

def isLauncher(fp,launcher=True):
    fd = open(fp,'r').read()
    islauncher_pattern = re.compile(r'<category android:name="android\.intent\.category\.\S+?"/>')
    launcher_str = r'<category android:name="android.intent.category.LAUNCHER"/>'
    nolauncher_str = r'<category android:name="android.intent.category.DEFAULT"/>'
    if launcher:
        fd = islauncher_pattern.sub(launcher_str,fd)
    else:
        fd = islauncher_pattern.sub(nolauncher_str,fd)
    writefile(fd,fp)

def setChannelConfig(recommander_id,pay_channel_id,fpath):
    if not isinstance(recommander_id,str):
        recommander_id = str(recommander_id)
    if not isinstance(pay_channel_id,str):
        pay_channel_id = str(pay_channel_id)
    ChannelConfig = dict(recommander_id=recommander_id,pay_channel_id=pay_channel_id)
    savejson(fd=ChannelConfig,fpath=fpath)

def check_AppConfig_version(versionNum):
    vlist = versionNum.split(".")
    if len(vlist) != 3:
        raise Exception(u"版本号配置不正确，正确格式【数字.数字.数字】请重新提交库表格！" .encode('gb2312','ignore'))
    for i in vlist:
        try:
            int(i)
        except ValueError:
            raise Exception(u"版本号配置不正确，正确格式【数字.数字.数字】请重新提交库表格！" .encode('gb2312','ignore'))

def _writeGameFilesTozip(zipOutPath,rootpath,encryptstatus=True,isBoundTcyapp=False):
    gamedirlist,gamefilelist = getGameHotUpdatefilelist(rootpath,isBoundTcyapp)
    z =zipfile.ZipFile(zipOutPath,mode="w",compression=zipfile.ZIP_DEFLATED)
    for dirpath in gamedirlist:
        zipdname = os.path.relpath(dirpath,rootpath)
        z.write(dirpath,zipdname)
    for filepath in gamefilelist:
        if encryptstatus:
            if os.path.splitext(filepath)[-1] == ".lua":
                filepath += "c"
        zipfname = os.path.relpath(filepath,rootpath)
        z.write(filepath,zipfname)
    z.close()

def tcyapp_zip_build(prop,isTest=False,is125=False):
    #tcyapp，lua游戏完整zip包 
    if is125:
        zipoutdir = os.path.join(prop.output_dir, '125apk',prop.versionNum.replace(".","_"), 'tcyapp')
    elif isTest:
        zipoutdir = os.path.join(prop.output_dir, 'testapk',prop.versionNum.replace(".","_"), 'tcyapp')
    else:
        zipoutdir = os.path.join(prop.output_dir, prop.versionNum.replace(".","_"), 'tcyapp')
    if not os.path.exists(zipoutdir):
        os.makedirs(zipoutdir)
    tcyappzipoutpath = os.path.join(zipoutdir,'%s_tcyapp.zip' % prop.appName)
    assets_root = prop.proj_android_assets_dir
    _writeGameFilesTozip(tcyappzipoutpath,assets_root,prop.encryptstatus)

def tcyappios_zip_build(prop,isTest=False,is125=False):
    #tcyapp的IOS版，lua游戏完整zip包
    if is125:
        zipoutdir = os.path.join(prop.output_dir, '125apk',prop.versionNum.replace(".","_"), 'tcyapp')
    elif isTest:
        zipoutdir = os.path.join(prop.output_dir, 'testapk',prop.versionNum.replace(".","_"), 'tcyapp')
    else:
        zipoutdir = os.path.join(prop.output_dir, prop.versionNum.replace(".","_"), 'tcyapp')

    if not os.path.exists(zipoutdir):
        os.makedirs(zipoutdir)
    tcyappzipoutpath = os.path.join(zipoutdir,'%s_tcyappios.zip' % prop.appName)
    assets_root = prop.proj_android_assets_dir
    _writeGameFilesTozip(tcyappzipoutpath,assets_root,prop.encryptstatus)


def tcyapp_Bound_zip_build(prop,isTest=False,is125=False):
    #tcyapp，lua集成游戏完整zip包，需要AppIcon.png
    if is125:
        zipoutdir = os.path.join(prop.output_dir, '125apk',prop.versionNum.replace(".","_"), 'tcyapp')
    elif isTest:
        zipoutdir = os.path.join(prop.output_dir, 'testapk',prop.versionNum.replace(".","_"), 'tcyapp')
    else:
        zipoutdir = os.path.join(prop.output_dir, prop.versionNum.replace(".","_"), 'tcyapp')
    if not os.path.exists(zipoutdir):
        os.makedirs(zipoutdir)
    tcyappzipoutpath = os.path.join(zipoutdir,'%s_tcyapp_jicheng.zip' % prop.appName)
    assets_root = prop.proj_android_assets_dir
    _writeGameFilesTozip(tcyappzipoutpath,assets_root,prop.encryptstatus,isBoundTcyapp=True)

def testLuaHotUpdate(prop,recommander_id,versionNum_lower,is125=False):
    if not is125:
        zipoutdir = os.path.join(prop.output_dir,'testapk',prop.versionNum.replace(".","_"), versionNum_lower.replace(".","_"))
    else:
        zipoutdir = os.path.join(prop.output_dir,'125apk',prop.versionNum.replace(".","_"), versionNum_lower.replace(".","_"))
    if not os.path.exists(zipoutdir):
        os.makedirs(zipoutdir)
    zipoutpath = os.path.join(zipoutdir,"diff_%s_%s.zip" % (prop.appName,recommander_id))
    assets_root = prop.proj_android_assets_dir
    _writeGameFilesTozip(zipoutpath,assets_root,prop.encryptstatus)

def test125build(appname,sysplatform):
    recommander_id = BuildConfig['recommendID']
    proVersion = BuildConfig['channel']
    proVersion = changeproVersion(proVersion)
    prop = gameConf(appname)
    
    if proVersion.lower() == "tcyappios":
        gameConfigInfo = getLibsInfoFromExcel2dict(prop.game_lib_info_file_ios,u"游戏配置信息")
        gamelib = getLibsInfoFromExcel2dict(prop.game_lib_info_file_ios,u"游戏库信息")
    else:
        gameConfigInfo = getLibsInfoFromExcel2dict(prop.game_lib_info_file,u"游戏配置信息")
        gamelib = getLibsInfoFromExcel2dict(prop.game_lib_info_file,u"游戏库信息")
    versionNum = gameConfigInfo['versionName']
    check_AppConfig_version(versionNum)
    prop.setProVersion(versionNum, proVersion)
    proj_android_path = prop.proj_android_path
    gamesrc = gamelib['gamesrc']    
    #versionMCRuntime = getMCRuntimeVersion(prop.game_lib_info_file)

    #添加渠道名称，渠道名称号到版本控制文件
    '''versionNumControl = getjson(prop.gameVersionConf)
    def insertVersionCode():
        print u"是否添加渠道名称:%s,渠道号：%s.到版本控制文件" % (proVersion,versionNum)
        VersionCode = raw_input(u"Y:是，  N：否\r\n".encode("gb2312","ignore"))
        if VersionCode.lower() == "y":
            versionNumControl[proVersion] = versionNum
            savejson(versionNumControl,prop.gameVersionConf)
        elif VersionCode.lower() == "n":
            pass
        else:
            print u"输入的信息错误，请重新输入！\r\n=*20"
            insertVersionCode()
    insertVersionCode()'''

    def NeedUpdateSvn():
        isNeedUpdate = BuildConfig['isUpdateSVN']
        if isNeedUpdate.lower() == "y":
            if os.path.exists(prop.proj_isLuaCompile_json):
                os.remove(prop.proj_isLuaCompile_json)
        else:
            pass
    NeedUpdateSvn()

    def NeedEncryption():
        isNeedEnryption = BuildConfig['isEncrypt']
        if isNeedEnryption.lower() == "y":
            prop.encryptstatus = True
            if gamesrc.find("tags") == -1:
                print u"svn路径不符合加密要求:%s, 打包结束,加密项目的路径必须在tags下\r\n" % (gamesrc)
                sys.exit() 
        else:
            prop.encryptstatus = False
    NeedEncryption()

    def NeedYQWEngine():
        isNeedYQWEngine = BuildConfig['isYQW']
        if isNeedYQWEngine.lower() == "y":
            prop.gradle_dir = prop.gradleYQW_dir
        else:
            pass

    NeedYQWEngine()

    # status状态：0表示已编译，1表示runPublishAssistant正常但未编译，2表示runPublishAssistant错误。
    print u"开始生成工程目录，计算哈希值，加密lua脚本文件。"
    prop.proHallVersion = 0
    if (not os.path.exists(prop.proj_isLuaCompile_json)) or (prop.proHallVersion != getjson(prop.proj_isLuaCompile_json)["HallVersion"]):
        if proVersion.lower() == "tcyappios":
            runPublishAssistantbyIOS(prop)
        else:
            '''if versionMCRuntime >= 20160530:
                runPublishAssistantbyAAR(prop)
            elif versionMCRuntime >= 20151228:
                runPublishAssistantbyGradle(prop)
            else:'''
            runPublishAssistant(prop)

        getAssetsMD5tofile(prop)
        if proVersion.lower() == "tcyappios":
            runluacompile(prop,"IOS")
        else:
            runluacompile(prop,sysplatform)
    elif getjson(prop.proj_isLuaCompile_json)["Status"] == 0:
        if proVersion.lower() == "tcyappios":
            runluacompile(prop,"IOS")
        else:
            runluacompile(prop,sysplatform)

    #设置渠道信息，签名文件信息
    setAntENV(prop)
    setBuildTarget(prop.project_properties_path,prop.proj_build_target)
    setChannelConfig(recommander_id=recommander_id,pay_channel_id="100001",fpath=prop.proj_ChannelConfig_json)
    setUmengChannel(UMENG_CHANNEL="channeltest",fpath=prop.AndroidManifest_xml_path,fpath2=prop.proj_UmengConfig_json)

    def antbuild(lowversion=""):
        #copy apk file
        releaseAPK = os.path.join(proj_android_path, 'bin/MCRuntime-release.apk')                   #ant打的release路径
        apkoutdir=os.path.join(prop.output_dir, '125apk',versionNum.replace(".","_"), lowversion)  #原始包输出目录路径
        apkoutpath=os.path.join(apkoutdir, '%s_%s_%s.apk' % (appname,proVersion,recommander_id))    #各渠道名称的apk路径
        if os.path.exists(proj_android_path + 'bin/'):
            shutil.rmtree(proj_android_path + 'bin/')
        runShellCmd([prop.ant_exe, '-f', prop.build_xml_path, 'clean'])
        runShellCmd([prop.ant_exe, '-f', prop.build_xml_path, 'release'])
        if not os.path.exists(apkoutdir):
            os.makedirs(apkoutdir)
        copyAndCheckFileExists(releaseAPK, apkoutpath, recommander_id, recommander_id, "channeltest", "100001")
        
    def gradlebuild(lowversion=""):
        #copy apk file
        releaseAPK = os.path.join(proj_android_path, 'build/outputs/apk/' + appname + '_' + proVersion + '-release.apk')  #ant打的release路径
        apkoutdir=os.path.join(prop.output_dir, '125apk',versionNum.replace(".","_"), lowversion)              #原始包输出目录路径
        apkoutpath=os.path.join(apkoutdir, '%s_%s_%s.apk' % (appname,proVersion,recommander_id)) 
        if os.path.exists(proj_android_path + 'bin/'):
            shutil.rmtree(proj_android_path + 'bin/')
        cmd='%s build -p %s' % (prop.gradle_dir,prop.proj_android_path)

        runShellCmd(cmd)
        if not os.path.exists(apkoutdir):
            os.makedirs(apkoutdir)
        copyAndCheckFileExists(releaseAPK, apkoutpath, recommander_id, recommander_id, "channeltest", "100001")

    releaseBackAppConfig = os.path.join(prop.proj_android_path,"assets","AppConfig_release.json")
    releaseBackAndroidManifest = os.path.join(prop.proj_android_path,'AndroidManifest_release.xml')
    try:
        #制作正常版本号的外网内测apk包。
        print u'开始制作测试包。渠道名称：%s ，版本号 %s' % (proVersion,versionNum)
        if os.path.exists(prop.proj_android_GameHall_hsl):
            shutil.copy(prop.hall_125_an,prop.proj_android_GameHall_hsl)
        if proVersion.lower() == "tcyapp":
            if os.path.exists(prop.proj_android_GameHall_hsl):
                shutil.copy(prop.hall_125_tcyapp,prop.proj_android_GameHall_hsl)
            tcyapp_zip_build(prop,isTest=False,is125=True)
            tcyapp_Bound_zip_build(prop,isTest=False,is125=True)
        if proVersion.lower() == "tcyappios":
            if os.path.exists(prop.proj_android_GameHall_hsl):
                shutil.copy(prop.hall_125_tcyappios,prop.proj_android_GameHall_hsl)
            #打包工具包名不加.tcy,我自己加行不-------
            shutil.copy(prop.proj_AppConfig_json,releaseBackAppConfig)
            appconfiginfo = getjson(prop.proj_AppConfig_json)
            packageName = appconfiginfo["packageName"]
            # packageName = packageName.rstrip(".tcy") + ".tcy"
            appconfiginfo["packageName"] = packageName
            savejson(appconfiginfo, prop.proj_AppConfig_json)
            ###########################################
            tcyappios_zip_build(prop,isTest=False,is125=True)
            #------------------------------------------
            shutil.copy(releaseBackAppConfig, prop.proj_AppConfig_json)
            ###########################################
        #if proVersion.lower() != "tcyappios":
        if proVersion.lower() != "tcyapp" and proVersion.lower() != "tcyappios":   
            #if versionMCRuntime >= 20151228:
            #    print u'gradlebuild start .....'
            gradlebuild()  #20170210版本打包工具统一使用gradle
            print u'gradlebuild end .....'
            #else:
            #    antbuild()

        #制作低版本号的外网内测apk包。
        versionNum_lower="1.0.20110328"
        versionCode_lower = "1"
        shutil.copy(prop.proj_AppConfig_json,releaseBackAppConfig)
        if os.path.exists(prop.AndroidManifest_xml_path):
            shutil.copy(prop.AndroidManifest_xml_path,releaseBackAndroidManifest)
        if os.path.exists(prop.proj_android_GameHall_hsl):
            shutil.copy(prop.hall_125_an,prop.proj_android_GameHall_hsl)
        if proVersion.lower() == "tcyapp":
            if os.path.exists(prop.proj_android_GameHall_hsl):
                shutil.copy(prop.hall_125_tcyapp,prop.proj_android_GameHall_hsl)
        if proVersion.lower() == "tcyappios":
            if os.path.exists(prop.proj_android_GameHall_hsl):
                shutil.copy(prop.hall_125_tcyappios,prop.proj_android_GameHall_hsl)
        
        print u'开始制作低版本的内网包。渠道名称：%s ，版本号 %s' % (proVersion,versionNum_lower)
        appconfiginfo = getjson(prop.proj_AppConfig_json)
        appconfiginfo["version"] = versionNum_lower
        appconfiginfo["versionCode"] = versionCode_lower
        savejson(appconfiginfo,prop.proj_AppConfig_json)
        if os.path.exists(prop.AndroidManifest_xml_path):
            chgandversionNum(prop.AndroidManifest_xml_path,versionNum_lower,versionCode_lower)
        if proVersion.lower() != "tcyapp" and proVersion.lower() != "tcyappios":
            #if versionMCRuntime >= 20151228:
            gradlebuild(lowversion="lowversion") #20170210版本打包工具统一用gradle打包
            #else:
            #   antbuild(lowversion="lowversion")

        if os.path.exists(releaseBackAppConfig):
            shutil.move(releaseBackAppConfig,prop.proj_AppConfig_json)
        if os.path.exists(releaseBackAndroidManifest):
            shutil.move(releaseBackAndroidManifest,prop.AndroidManifest_xml_path)
        testLuaHotUpdate(prop,recommander_id,versionNum_lower, is125=True)

        #制作完整的版本差异zip文件
        hotupdate_md5_dir = os.path.join(prop.current_dir,'hotupdate_file_md5')
        versionNum_Dir = ".".join(prop.versionNum.split(".")[:2])
        youngVersionNum_md5_json = os.path.join(hotupdate_md5_dir,versionNum_Dir,"%s.json" % (prop.versionNum))
        oldVersionNum_md5_jsons = [item for item in getPathFilesList(hotupdate_md5_dir) if item != youngVersionNum_md5_json]
        if oldVersionNum_md5_jsons:
            print u"开始对比所有hotupdate_file_md5目录下的json文件，并生成差异zip包"
            youngVersionNum_md5 = getjson(youngVersionNum_md5_json)
            for oldVersionNum_json in oldVersionNum_md5_jsons:
                oldVersionNum = os.path.splitext(os.path.basename(oldVersionNum_json))[0]
                oldVersionNum_md5 = getjson(oldVersionNum_json)
                if oldVersionNum_md5.has_key(proVersion):
                    zipoutdir=os.path.join(prop.output_dir,"125apk",versionNum.replace(".","_"),oldVersionNum.replace(".","_"))
                    if not os.path.exists(zipoutdir):
                        os.makedirs(zipoutdir)
                    zipoutpath = os.path.join(zipoutdir,"diff_%s_%s.zip" % (appname,recommander_id))
                    contrastlist = contrastdict(youngVersionNum_md5[proVersion],oldVersionNum_md5[proVersion])
                    lua_hotupdate_zip(zp=zipoutpath,files=contrastlist,rootdir=prop.proj_android_assets_dir,
                                      encryptstatus=prop.encryptstatus,
                                      recommander_id=recommander_id,pay_channel_id="100001")

    finally:
        if os.path.exists(prop.proj_android_GameHall_hsl):
            shutil.copy(prop.hall_an,prop.proj_android_GameHall_hsl)
        if os.path.exists(releaseBackAppConfig):
            shutil.move(releaseBackAppConfig,prop.proj_AppConfig_json)
        if os.path.exists(releaseBackAndroidManifest):
            shutil.move(releaseBackAndroidManifest,prop.AndroidManifest_xml_path)


def testbuild(appname,sysplatform):
    recommander_id = BuildConfig['recommendID']
    proVersion = BuildConfig['channel']
    proVersion = changeproVersion(proVersion)
    prop = gameConf(appname)
    
    if proVersion.lower() == "tcyappios":
        gameConfigInfo = getLibsInfoFromExcel2dict(prop.game_lib_info_file_ios,u"游戏配置信息")
        gamelib = getLibsInfoFromExcel2dict(prop.game_lib_info_file_ios,u"游戏库信息")
    else:
        gameConfigInfo = getLibsInfoFromExcel2dict(prop.game_lib_info_file,u"游戏配置信息")
        gamelib = getLibsInfoFromExcel2dict(prop.game_lib_info_file,u"游戏库信息")
    versionNum = gameConfigInfo['versionName']
    check_AppConfig_version(versionNum)
    prop.setProVersion(versionNum, proVersion)
    proj_android_path = prop.proj_android_path
    gamesrc = gamelib['gamesrc']
    #versionMCRuntime = getMCRuntimeVersion(prop.game_lib_info_file)

    #添加渠道名称，渠道名称号到版本控制文件
    '''versionNumControl = getjson(prop.gameVersionConf)
    def insertVersionCode():
        print u"是否添加渠道名称:%s,渠道号：%s.到版本控制文件" % (proVersion,versionNum)
        VersionCode = raw_input(u"Y:是，  N：否\r\n".encode("gb2312","ignore"))
        if VersionCode.lower() == "y":
            versionNumControl[proVersion] = versionNum
            savejson(versionNumControl,prop.gameVersionConf)
        elif VersionCode.lower() == "n":
            pass
        else:
            print u"输入的信息错误，请重新输入！\r\n=*20"
            insertVersionCode()
    insertVersionCode()'''

    def NeedUpdateSvn():
        isNeedUpdaet = BuildConfig['isUpdateSVN']
        if isNeedUpdaet.lower() == "y":
            if os.path.exists(prop.proj_isLuaCompile_json):
                os.remove(prop.proj_isLuaCompile_json)
        else:
            pass
    NeedUpdateSvn()

    def NeedEncryption():
        isNeedEnryption = BuildConfig['isEncrypt']
        if isNeedEnryption.lower() == "y":
            prop.encryptstatus = True
            if gamesrc.find("tags") == -1:
                print u"svn路径不符合加密要求:%s, 打包结束,加密项目的路径必须在tags下\r\n" % (gamesrc)
                sys.exit() 
        else:
            prop.encryptstatus = False
    NeedEncryption()

    def NeedYQWEngine():
        isNeedYQWEngine = BuildConfig['isYQW']
        if isNeedYQWEngine.lower() == "y":
            prop.gradle_dir = prop.gradleYQW_dir
        else:
            pass

    NeedYQWEngine()

    # status状态：0表示已编译，1表示runPublishAssistant正常但未编译，2表示runPublishAssistant错误。
    print u"开始生成工程目录，计算哈希值，加密lua脚本文件。"    
    prop.proHallVersion = 1
    if not os.path.exists(prop.proj_isLuaCompile_json) or prop.proHallVersion != getjson(prop.proj_isLuaCompile_json)["HallVersion"]:
        if proVersion.lower() == "tcyappios":
            runPublishAssistantbyIOS(prop)
        else:
            '''if versionMCRuntime >= 20160530:
                runPublishAssistantbyAAR(prop)
            elif versionMCRuntime >= 20151228:
	            runPublishAssistantbyGradle(prop)
            else:'''
            runPublishAssistant(prop)

        getAssetsMD5tofile(prop)
        if proVersion.lower() == "tcyappios":
            runluacompile(prop,"IOS")
        else:
            runluacompile(prop,sysplatform)
    elif getjson(prop.proj_isLuaCompile_json)["Status"] == 0:
        if proVersion.lower() == "tcyappios":
            runluacompile(prop,"IOS")
        else:
            runluacompile(prop,sysplatform)

    #设置渠道信息，签名文件信息
    setAntENV(prop)
    setBuildTarget(prop.project_properties_path,prop.proj_build_target)
    setChannelConfig(recommander_id=recommander_id,pay_channel_id="100001",fpath=prop.proj_ChannelConfig_json)
    setUmengChannel(UMENG_CHANNEL="channeltest",fpath=prop.AndroidManifest_xml_path,fpath2=prop.proj_UmengConfig_json)

    def antbuild(lowversion=""):
        #copy apk file
        releaseAPK = os.path.join(proj_android_path, 'bin/MCRuntime-release.apk')                   #ant打的release路径
        apkoutdir=os.path.join(prop.output_dir, 'testapk',versionNum.replace(".","_"), lowversion)  #原始包输出目录路径
        apkoutpath=os.path.join(apkoutdir, '%s_%s_%s.apk' % (appname,proVersion,recommander_id))    #各渠道名称的apk路径
        if os.path.exists(proj_android_path + 'bin/'):
            shutil.rmtree(proj_android_path + 'bin/')
        runShellCmd([prop.ant_exe, '-f', prop.build_xml_path, 'clean'])
        runShellCmd([prop.ant_exe, '-f', prop.build_xml_path, 'release'])
        if not os.path.exists(apkoutdir):
            os.makedirs(apkoutdir)
        copyAndCheckFileExists(releaseAPK, apkoutpath, recommander_id, recommander_id, "channeltest", "100001")
        
    def gradlebuild(lowversion=""):
        #copy apk file
        releaseAPK = os.path.join(proj_android_path, 'build/outputs/apk/' + appname + '_' + proVersion + '-release.apk')  #ant打的release路径
        apkoutdir=os.path.join(prop.output_dir, 'testapk',versionNum.replace(".","_"), lowversion)              #原始包输出目录路径
        apkoutpath=os.path.join(apkoutdir, '%s_%s_%s.apk' % (appname,proVersion,recommander_id)) 
        if os.path.exists(proj_android_path + 'bin/'):
            shutil.rmtree(proj_android_path + 'bin/')
        cmd='%s build -p %s' % (prop.gradle_dir,prop.proj_android_path)
        runShellCmd(cmd)
        if not os.path.exists(apkoutdir):
            os.makedirs(apkoutdir)
        copyAndCheckFileExists(releaseAPK, apkoutpath, recommander_id, recommander_id, "channeltest", "100001")


    releaseBackAppConfig = os.path.join(prop.proj_android_path,"assets","AppConfig_release.json")
    releaseBackAndroidManifest = os.path.join(prop.proj_android_path,'AndroidManifest_release.xml')
    try:
        #制作正常版本号的外网内测apk包。
        print u'开始制作外网内测包。渠道名称：%s ，版本号 %s' % (proVersion,versionNum)
        if os.path.exists(prop.proj_android_GameHall_hsl):
            shutil.copy(prop.hall_888_an,prop.proj_android_GameHall_hsl)
        if proVersion.lower() == "tcyapp":
            if os.path.exists(prop.proj_android_GameHall_hsl):
                shutil.copy(prop.hall_888_tcyapp,prop.proj_android_GameHall_hsl)
            tcyapp_zip_build(prop,isTest=True)
            tcyapp_Bound_zip_build(prop,isTest=True)
        if proVersion.lower() == "tcyappios":
            if os.path.exists(prop.proj_android_GameHall_hsl):
                shutil.copy(prop.hall_888_tcyappios,prop.proj_android_GameHall_hsl)
            #打包工具包名不加.tcy,我自己加行不-------
            shutil.copy(prop.proj_AppConfig_json,releaseBackAppConfig)
            appconfiginfo = getjson(prop.proj_AppConfig_json)
            packageName = appconfiginfo["packageName"]
            # packageName = packageName.rstrip(".tcy") + ".tcy"
            appconfiginfo["packageName"] = packageName
            savejson(appconfiginfo, prop.proj_AppConfig_json)
            ###########################################
            tcyappios_zip_build(prop,isTest=True)
            #------------------------------------------
            shutil.copy(releaseBackAppConfig, prop.proj_AppConfig_json)
            ###########################################
        #if proVersion.lower() != "tcyappios":
        if proVersion.lower() != "tcyapp" and proVersion.lower() != "tcyappios":
            #if versionMCRuntime >= 20151228:
            gradlebuild()  #20170210版本打包工具统一用gradle
            #else:
                #antbuild() 
        print u"开始制作低版本的外网内测包"

        #制作低版本号的外网内测apk包。
        versionNum_lower="1.0.20110328"
        versionCode_lower = "1"
        shutil.copy(prop.proj_AppConfig_json,releaseBackAppConfig)
        if os.path.exists(prop.AndroidManifest_xml_path):
            shutil.copy(prop.AndroidManifest_xml_path,releaseBackAndroidManifest)
        if os.path.exists(prop.proj_android_GameHall_hsl):
             shutil.copy(prop.hall_888_an,prop.proj_android_GameHall_hsl)
        if proVersion.lower() == "tcyapp":
            if os.path.exists(prop.proj_android_GameHall_hsl):
                shutil.copy(prop.hall_888_tcyapp,prop.proj_android_GameHall_hsl)
        if proVersion.lower() == "tcyappios":
            if os.path.exists(prop.proj_android_GameHall_hsl):
                shutil.copy(prop.hall_888_tcyappios,prop.proj_android_GameHall_hsl)
        print u'开始制作低版本的外网内测包。渠道名称：%s ，版本号 %s' % (proVersion,versionNum_lower)
        appconfiginfo = getjson(prop.proj_AppConfig_json)
        appconfiginfo["version"] = versionNum_lower
        appconfiginfo["versionCode"] = versionCode_lower
        savejson(appconfiginfo,prop.proj_AppConfig_json)
        if os.path.exists(prop.AndroidManifest_xml_path):
            chgandversionNum(prop.AndroidManifest_xml_path,versionNum_lower,versionCode_lower)
        if proVersion.lower() != "tcyapp" and proVersion.lower() != "tcyappios":
            #if versionMCRuntime >= 20151228:
            gradlebuild(lowversion="lowversion") #20170210版本打包工具统一用gradle打包
            #else:
            #    antbuild(lowversion="lowversion")

        if os.path.exists(releaseBackAppConfig):
            shutil.move(releaseBackAppConfig,prop.proj_AppConfig_json)
        if os.path.exists(releaseBackAndroidManifest):
            shutil.move(releaseBackAndroidManifest,prop.AndroidManifest_xml_path)
        testLuaHotUpdate(prop,recommander_id,versionNum_lower)

        #制作完整的版本差异zip文件
        hotupdate_md5_dir = os.path.join(prop.current_dir,'hotupdate_file_md5')
        versionNum_Dir = ".".join(prop.versionNum.split(".")[:2])
        youngVersionNum_md5_json = os.path.join(hotupdate_md5_dir,versionNum_Dir,"%s.json" % (prop.versionNum))
        oldVersionNum_md5_jsons = [item for item in getPathFilesList(hotupdate_md5_dir) if item != youngVersionNum_md5_json]
        if oldVersionNum_md5_jsons:
            print u"开始对比所有hotupdate_file_md5目录下的json文件，并生成差异zip包"
            youngVersionNum_md5 = getjson(youngVersionNum_md5_json)
            for oldVersionNum_json in oldVersionNum_md5_jsons:
                oldVersionNum = os.path.splitext(os.path.basename(oldVersionNum_json))[0]
                oldVersionNum_md5 = getjson(oldVersionNum_json)
                if oldVersionNum_md5.has_key(proVersion):
                    zipoutdir=os.path.join(prop.output_dir,"testapk",versionNum.replace(".","_"),oldVersionNum.replace(".","_"))
                    if not os.path.exists(zipoutdir):
                        os.makedirs(zipoutdir)
                    zipoutpath = os.path.join(zipoutdir,"diff_%s_%s.zip" % (appname,recommander_id))
                    contrastlist = contrastdict(youngVersionNum_md5[proVersion],oldVersionNum_md5[proVersion])
                    lua_hotupdate_zip(zp=zipoutpath,files=contrastlist,rootdir=prop.proj_android_assets_dir,
                                      encryptstatus=prop.encryptstatus,
                                      recommander_id=recommander_id,pay_channel_id="100001")

    finally:
        if os.path.exists(prop.proj_android_GameHall_hsl):
            shutil.copy(prop.hall_an,prop.proj_android_GameHall_hsl)
        if os.path.exists(releaseBackAppConfig):
            shutil.move(releaseBackAppConfig,prop.proj_AppConfig_json)
        if os.path.exists(releaseBackAndroidManifest):
            shutil.move(releaseBackAndroidManifest,prop.AndroidManifest_xml_path)

def releasebuild(appname,sysplatform):
    prop = gameConf(appname)
    #自动上传官网记录文件
    gameupload_json_fpath = prop.gameupload_json
    officialapkDL = getjson(gameupload_json_fpath)
    
    versionNumControl = getjson(prop.gameVersionConf)

    #开始遍历xlsx表格文件，并做包
    promotelist = getPromoteIDFromExcel2list(prop.channel_file)
    #打正式包前先删除xxxx_an_tcy/xxxx_an_tcyapp/xxxx_tcyapp_ios
    for item in promotelist:
        proVersion = item["proVersion"].lower()
        proVersion = changeproVersion(proVersion) #映射渠道名称标准化

        if proVersion.lower() == "tcyappios":
            gameConfigInfo = getLibsInfoFromExcel2dict(prop.game_lib_info_file_ios,u"游戏配置信息")
            gamelib = getLibsInfoFromExcel2dict(prop.game_lib_info_file_ios,u"游戏库信息")
            versionNum = gameConfigInfo['versionName']
            versionNumControl[proVersion] = versionNum
            savejson(versionNumControl,prop.gameVersionConf)
            gamesrc = gamelib['gamesrc']
            if gamesrc.find("tags") == -1:
                print u"ios工程路径不符合正式包要求:%s, 项目必须处于tags路径下\r\n" % (gamesrc)
                sys.exit()             
        elif proVersion.lower() == "tcyapp":
            
            gameConfigInfo = getLibsInfoFromExcel2dict(prop.game_lib_info_file,u"游戏配置信息")
            gamelib = getLibsInfoFromExcel2dict(prop.game_lib_info_file,u"游戏库信息")
            versionNum = gameConfigInfo['versionName']
            versionNumControl[proVersion] = versionNum
            savejson(versionNumControl,prop.gameVersionConf)
            gamesrc = gamelib['gamesrc']
            if gamesrc.find("tags") == -1:
                print u"安卓工程路径不符合正式包要求:%s, 项目必须处于tags路径下\r\n" % (gamesrc)
                sys.exit()             
            #versionMCRuntime = getMCRuntimeVersion(prop.game_lib_info_file)
        else:
            def NeedYQWEngine():
                isNeedYQWEngine = BuildConfig['isYQW']
                if isNeedYQWEngine.lower() == "y":
                    prop.gradle_dir = prop.gradleYQW_dir
                else:
                    pass

            NeedYQWEngine()

            versionNum = versionNumControl[proVersion]
            #versionMCRuntime = getMCRuntimeVersion(prop.game_lib_info_file)
        check_AppConfig_version(versionNum)

        check_dir = os.path.join(prop.current_dir, versionNum)
        check_dir = check_dir.replace('\\', '/')

        check_dir = os.path.join(check_dir, prop.appName+'_'+proVersion)
        check_dir = check_dir.replace('\\', '/')
        
        if os.path.exists(check_dir):
            removeDir(check_dir)

    try:
        for item in promotelist:
            recommander_id = str(item["recommander_id"]).strip()
           
            UmengChannel = str(item["UmengChannel"]).strip()
            UmengChannel = autoEncode(UmengChannel)
            pay_channel_id = str(item["pay_channel_id"]).strip()
            isEnableDownload = item["isEnableDownload"]
            proVersion = item["proVersion"].lower()
            proVersion = changeproVersion(proVersion) #映射渠道名称标准化
            if proVersion.lower() == "tcyappios":
                gameConfigInfo = getLibsInfoFromExcel2dict(prop.game_lib_info_file_ios,u"游戏配置信息")
                versionNum = gameConfigInfo['versionName']
                versionNumControl[proVersion] = versionNum
                savejson(versionNumControl,prop.gameVersionConf)
            elif proVersion.lower() == "tcyapp":
                
                gameConfigInfo = getLibsInfoFromExcel2dict(prop.game_lib_info_file,u"游戏配置信息")
                versionNum = gameConfigInfo['versionName']
                versionNumControl[proVersion] = versionNum
                savejson(versionNumControl,prop.gameVersionConf)
                #versionMCRuntime = getMCRuntimeVersion(prop.game_lib_info_file)
            else:
                versionNum = versionNumControl[proVersion]
                #versionMCRuntime = getMCRuntimeVersion(prop.game_lib_info_file)
            check_AppConfig_version(versionNum)
            logger.info(u"开始打包推广ID: %s, 友盟渠道: %s, 充值渠道: %s, 渠道名称：%s 版本号：%s",
                        recommander_id,UmengChannel,pay_channel_id,proVersion,versionNum)

            prop.setProVersion(versionNum, proVersion)
            proj_android_path = prop.proj_android_path

            # status状态：0表示runPublishAssistant正常但未编译；1表示已运行luac机密；2表示不用机密，明文lua。
            if not os.path.exists(prop.proj_isLuaCompile_json):
                if proVersion.lower() == "tcyappios":
                    runPublishAssistantbyIOS(prop)
                else:
                    runPublishAssistant(prop)
                getAssetsMD5tofile(prop)
                if proVersion.lower() == "tcyappios":
                    runluacompile(prop,"IOS")
                else:
                    runluacompile(prop,sysplatform)
            elif getjson(prop.proj_isLuaCompile_json)["Status"] == 0:
                if proVersion.lower() == "tcyappios":
                    runluacompile(prop,"IOS")
                else:
                    runluacompile(prop,sysplatform)

            #设置渠道信息，签名文件信息
            setAntENV(prop)
            setBuildTarget(prop.project_properties_path,prop.proj_build_target)
            if proVersion.lower() == "tcyapp":
                pay_channel_id = '100066'
            if proVersion.lower() == "tcyappios":
                pay_channel_id = '100102'
            setChannelConfig(recommander_id=recommander_id,pay_channel_id=pay_channel_id,fpath=prop.proj_ChannelConfig_json)
            apkoutdir=os.path.join(prop.output_dir, versionNum.replace(".","_"), 'full')                #原始包输出目录路径
            apkoutpath=os.path.join(apkoutdir, '%s_%s.apk' % (appname, recommander_id))  #各渠道名称的apk路径
            if not proVersion.lower() == "tcyappios":
                setUmengChannel(UMENG_CHANNEL=UmengChannel.encode('utf-8','ignore'),fpath=prop.AndroidManifest_xml_path,fpath2=prop.proj_UmengConfig_json)

                if not checkHallhsl(prop.proj_android_GameHall_hsl):
                    print "copy [%s] to [%s]" % (prop.hall_an,prop.proj_android_GameHall_hsl)
                    shutil.copy(prop.hall_an,prop.proj_android_GameHall_hsl)
                    
                def antbuild():
                                      #ant打的release路径           
                    if os.path.exists(proj_android_path + 'bin/'):
                        shutil.rmtree(proj_android_path + 'bin/')
                    runShellCmd([prop.ant_exe, '-f', prop.build_xml_path, 'clean'])
                    runShellCmd([prop.ant_exe, '-f', prop.build_xml_path, 'release'])
                    if not os.path.exists(apkoutdir):
                        os.makedirs(apkoutdir)
                    copyAndCheckFileExists(releaseAPK, apkoutpath, recommander_id, recommander_id, UmengChannel.decode('utf-8'), pay_channel_id)
        
                def gradlebuild():
                     #ant打的release路径
                    
                    if os.path.exists(proj_android_path + 'bin/'):
                        shutil.rmtree(proj_android_path + 'bin/')
                    cmd='%s build -p %s' % (prop.gradle_dir,prop.proj_android_path)
                    runShellCmd(cmd)
                    if not os.path.exists(apkoutdir):
                        os.makedirs(apkoutdir)
                    copyAndCheckFileExists(releaseAPK, apkoutpath, recommander_id, recommander_id, UmengChannel.decode('utf-8'), pay_channel_id)
                
                #if versionMCRuntime >= 20151228:
                releaseAPK = os.path.join(proj_android_path, 'build/outputs/apk/' + appname + '_' + proVersion + '-release.apk') 
                gradlebuild() #20170210版本打包工具统一用gradle打包
                #else:
                #    releaseAPK = os.path.join(proj_android_path, 'bin/MCRuntime-release.apk') 
                #    antbuild()

            if proVersion.lower() == "tcyapp":
                if os.path.exists(prop.proj_android_GameHall_hsl):
                    shutil.copy(prop.hall_tcyapp,prop.proj_android_GameHall_hsl)
                tcyapp_zip_build(prop)
                tcyapp_Bound_zip_build(prop)
                apkoutpathByTcyapp = os.path.join(apkoutdir, '%s_tcyapp.apk' % appname)
                copyAndCheckFileExists(releaseAPK, apkoutpath, recommander_id, recommander_id, UmengChannel, pay_channel_id)
            if proVersion.lower() == "tcyappios":
                if os.path.exists(prop.proj_android_GameHall_hsl):
                    shutil.copy(prop.hall_tcyappios,prop.proj_android_GameHall_hsl)
                tcyappios_zip_build(prop)


            #自动上传官网下载站的记录json
            if isEnableDownload == u"是" or isEnableDownload == 1:
                officialDLURL = 'http://%s/%s/%s/%s.apk' % (prop.officialsvrlist,
                                                            prop.build_xml_projname, recommander_id, prop.game_name_upload)
                preofficialDLURL = 'http://%s/pre_%s/%s/%s.apk' % (prop.officialsvrlist,
                                                                prop.build_xml_projname, recommander_id, prop.game_name_upload)
                officialapkDL[str(recommander_id).decode(encoding='utf-8')] = dict(fpath=apkoutpath,
                                                                              officialDLURL=officialDLURL,
                                                                              preofficialDLURL=preofficialDLURL,
                                                                              uploaded=0)
            logger.info(u'推广ID：%s 制作完成！', recommander_id)
    finally:
        savejson(officialapkDL,prop.gameupload_json)


def main(appname,sysplatform):
    if BuildConfig['buildType'] == '125':
        test125build(appname, sysplatform)
    elif BuildConfig['buildType'] == '888':
        testbuild(appname, sysplatform)
    else:
        releasebuild(appname, sysplatform)

if __name__ == "__main__":
    import sys
    BuildConfig['appName']      = sys.argv[1]
    BuildConfig['buildType']    = sys.argv[2]
    BuildConfig['recommendID']  = sys.argv[3]
    BuildConfig['channel']      = sys.argv[4]
    BuildConfig['isUpdateSVN']  = sys.argv[5]
    BuildConfig['isEncrypt']    = sys.argv[6]
    BuildConfig['isYQW']        = sys.argv[7]

    main(BuildConfig['appName'], "Android")