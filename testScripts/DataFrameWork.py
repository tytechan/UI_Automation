#encoding = utf - 8
# 用于实现数据框架驱动

from . import *
from testScripts.WriteTextResult import *
from util.Log import *
from config.global_config import *

def  dataDriverRun(dataSourceSheetObj,stepSheetObj,stepSheetName,isLastModule,funcName,picDir):
    '''
    :param dataSourceSheetObj: 数据模块sheet对象
    :param stepSheetObj: 功能&步骤模块sheet对象
    :return:
    '''
    try:
        # 获取数据模块sheet中“数据状态”列对象
        dataIsExecuteColumn = excelObj.getColumn(dataSourceSheetObj,DataSource_IsExecute)
        # 获取功能&步骤模块sheet中存在数据区域的行数
        stepRowNums = excelObj.getRowsNumber(stepSheetObj)
        # print("功能&步骤sheet中行数为：",stepRowNums)

        # 每次进入步骤&功能sheet后删除所有先前记录
        for myRowInStepSheet in range(2, stepRowNums + 1):
            writeTextResult(stepSheetObj, rowNo=myRowInStepSheet,
                            colsNo="CaseStep", testResult="")
        '''
        requiredDataNo和successStepNo用于判断执行结束标志
        '''
        # 记录成功执行的数据行数
        successDataNo = 0
        # 记录待执行的数据行数
        requiredDataNo = 0
        # 定义 moduleToLoop,便于在首次执行该流程无数据时正常抛错
        moduleToLoop = 1

        for Looptime, ExcuteMsg in enumerate(dataIsExecuteColumn[1:]):
            # print("***** Looptime:",Looptime," ***** ExcuteMsg:",ExcuteMsg,"： ",ExcuteMsg.value)

            # 用于判断是否跳出excel步骤
            isToBreak = False

            myTime = get_value("本流程执行次数")
            lastRow = get_value("已用数据行")
            # 先在数据模块sheet中遍历，判断该行数据是否已执行
            if ExcuteMsg.value != "已使用":
                if lastRow >= Looptime + 2 and myTime > 1:
                        continue

                set_value("可用数据行",Looptime + 2)

                # 写入该流程截图路径
                myColumn = 1
                for myBox in excelObj.getRow(dataSourceSheetObj, 1):
                    if myBox.value == None:
                        break
                    elif myBox.value == "截图路径":
                        excelObj.writeCell(dataSourceSheetObj, content=picDir,rowNo=Looptime+2,colsNo=myColumn)
                        break
                    myColumn += 1

                print("********** 开始调用第 ",Looptime + 2," 行数据 **********")

                # 该功能模块不执行时，跳出循环，TODO
                # 在数据sheet中新增列，判断功能模块是否跳过
                jumpToBreak = False

                myColumnNum = 1
                for myBox in excelObj.getRow(dataSourceSheetObj,1):
                    # 获取数据sheet中与功能sheet同名的列，并判断（Looptime + 2，myColumnNum）的值是否为“跳过”
                    if myBox.value == funcName:
                        # 去除数据表中与当前步骤sheet名相同列的值，可能有“...”和“...*n”两种形式,n对应该步骤sheet循环次数
                        keyValue = excelObj.getCellOfValue(dataSourceSheetObj,rowNo=Looptime+2,colsNo=myColumnNum)
                        if keyValue:
                            jumpValue = keyValue.split("*")[0]
                            if len(keyValue.split("*")) > 1:
                                moduleToLoop = int(keyValue.split("*")[1])
                            else:
                                moduleToLoop = 1
                        else:
                            jumpValue = "跳过"
                            moduleToLoop = 1

                        print("********** 第",Looptime+2,"行",myColumnNum,"列的判断跳出标志位为：",
                              jumpValue," **********")
                        if jumpValue == stepSheetName:
                            pass
                        else:
                            jumpToBreak = True
                        break
                    myColumnNum += 1

                if jumpToBreak:
                    # 若对应表格内值不为“执行”，则不用执行该模块
                    logging.info(u">> 跳过该模块所有步骤...")
                    if isLastModule:
                        writeTextResult(sheetObj = dataSourceSheetObj,rowNo = Looptime + 2,
                                        colsNo = "DataSource",testResult = "成功",
                                        dataUse = "已使用")
                    break

                logging.info(u">> 开始调用数据表...")

                # if "moduleToLoop" not in locals().keys():
                #     moduleToLoop = 1
                for i in range(moduleToLoop):
                    requiredDataNo += 1
                    # 定义循环模块的跳出标志位
                    loopToBreak = False
                    # 定义循环模块的终止循环标志位（通过数据控制循环次数）
                    stopToLoop = False
                    # 定义执行成功步骤数变量
                    successStepNo = 0

                    # 遍历功能&步骤sheet中存在数据的所有行
                    for myRowInStepSheet in range(2,stepRowNums + 1):
                        # 获取sheet中第 myRowInStepSheet 行对象
                        rowObj = excelObj.getRow(stepSheetObj,myRowInStepSheet)
                        # 获取关键字作为调用的函数名
                        keyWord = rowObj[CaseStep_keyname - 1].value
                        # 获取定位方式
                        locationType = rowObj[CaseStep_locationtype - 1].value
                        # 获取定位表达式
                        locatorExpression = rowObj[CaseStep_locatorexpression - 1].value
                        # 获取操作值
                        operateValue = rowObj[CaseStep_operatevalue - 1].value
                        # 获取判断是否有返回值标志位
                        isReturnedValue = rowObj[CaseStep_isreturned - 1].value

                        if operateValue:
                            if isinstance(operateValue,int) or isinstance(operateValue,float):
                                print("*********** 直接通过关键字驱动输入的值为： ",operateValue," ***********")
                                operateValue = str(operateValue)
                                print("数值型var值为：",operateValue)

                            processValue = ""
                            myCount = operateValue.count("|") + 1



                            # TODO .01：从“数据表”sheet按列号取值方法可优化（原方法为通过固定列号查询，新方法为通过表头名称遍历）
                            # if operateValue and operateValue.encode('utf-8').isalpha() and myCount == 1:
                            #     '''
                            #     operateValue不为空，且所有字符均为字母，则说明为调用情况
                            #     '''
                            #     print("字母型var值为：",operateValue)
                            #     coordinate = operateValue + str(Looptime + 2)
                            #     print("获取数据坐标coordinate为：",coordinate)
                            #     operateValue = excelObj.getCellOfValue(dataSourceSheetObj,coordinate = coordinate)
                            #     operateValue = str(operateValue)

                            if operateValue.startswith("#") == True\
                                    and myCount == 1:
                                myColumn = 1
                                for myBox in excelObj.getRow(dataSourceSheetObj, 1):
                                    if myBox.value == None:
                                        break
                                    elif myBox.value == operateValue.replace("#",""):
                                        myValue = excelObj.getCellOfValue(dataSourceSheetObj,rowNo=Looptime+2,colsNo=myColumn)
                                        myValue = str(myValue)
                                        # 下句下标越界后，须检查数据表中对应字段数据格式是否正确
                                        if "*" in myValue and (operateValue.endswith("#") == False):
                                            myValue = myValue.split("*")[i]
                                        print("********** ", operateValue, "的值为：", myValue, " **********")

                                        if operateValue.startswith("##") and i == 0:
                                            # 首次进入循环模块sheet后，遇到“##”开头的特殊字段，将进入此分支
                                            # （由于框架中“”和None均无法传入关键字的限制）
                                            operateValue = "循环初始化"
                                        else:
                                            operateValue = myValue
                                        break
                                    myColumn += 1

                                # 当该字段在第i次循环中的数据为“”（本次循环第一次出现为“”的字段）时，终止循环，进行下一模块
                                if moduleToLoop > 1 \
                                        and i > 0 \
                                        and operateValue == "":
                                    stopToLoop = True
                                    print("********** 循环执行流程时，检测到operateValue的值为空，结束循环流程")
                                    break


                            if myCount > 1:
                                myLoop = 0
                                for var in operateValue.split("|"):
                                    if isinstance(var,int) or isinstance(var,float):
                                        print("*********** 直接通过关键字驱动输入的值为： ",var," ***********")
                                        var = str(var)
                                        print("数值型var值为：",var)


                                    # TODO .02:  此处为修改带分隔符“|”的operateValue中调用和纯字母的情况
                                    # if var and var.encode('utf-8').isalpha() and var.startswith("&") == False:
                                    #     '''
                                    #     var不为空，且所有字符均为字母，则说明为调用情况
                                    #     '''
                                    #     print("字母型var值为：",var)
                                    #     coordinate = var + str(Looptime + 2)
                                    #     print("获取数据坐标coordinate为：",coordinate)
                                    #     var = excelObj.getCellOfValue(dataSourceSheetObj,coordinate = coordinate)
                                    #     var = str(var)
                                    #     print("********** 数据表sheet中调用单元格为： ",coordinate," 对应值为： ",var," **********")

                                    if var.startswith("#") == True:
                                        myColumn = 1
                                        for myBox in excelObj.getRow(dataSourceSheetObj, 1):
                                            if myBox.value == None:
                                                break
                                            elif myBox.value == var.replace("#",""):
                                                myValue = excelObj.getCellOfValue(dataSourceSheetObj,rowNo=Looptime+2,colsNo=myColumn)
                                                print("********** ",operateValue,"的值为：",myValue," **********")
                                                md = str(myValue).split("*")
                                                var = md[0] if len(md) == 1 else md[i]
                                                break
                                            myColumn += 1



                                    if myLoop > 0:
                                        if myCount == 1:
                                            processValue += var
                                        else:
                                            processValue += "|" + var
                                    else:
                                        processValue += var
                                    myLoop += 1

                                if "" in processValue.split("|"):
                                    stopToLoop = True
                                    print("********** 循环执行流程时，检测到operateValue的值为空，结束循环流程")
                                    break

                                operateValue = processValue
                            print("********** 拼接后 operateValue 值为： ",operateValue," **********")


                            # TODO .03：由于TODO .01中删除纯字母从“数据表”sheet取值情况，则以下方法也可删除
                            # if operateValue.startswith("&"):
                            #     '''
                            #     若以“&”开头，则说明该字符串为纯英文，但不是调用数据sheet情况
                            #     '''
                            #     operateValue = str(operateValue.split("&")[1])


                        # 拼接字符串获得需要执行的python表达式，以对应 PageAction.py 中对应函数方法
                        locationType = str(locationType) if isinstance(locationType, int) else locationType
                        locatorExpression = str(locatorExpression) if isinstance(locatorExpression, int) else locatorExpression

                        if locationType and locatorExpression:
                            tmpStr = "'%s','%s'" %(locationType.lower(), locatorExpression.replace("'",'"'))
                        elif locationType:
                            tmpStr = "'%s'" %(locationType.lower())
                        elif locatorExpression:
                            tmpStr = "'%s'" %(locatorExpression.replace("'",'"'))
                        else:
                            tmpStr = ""

                        # tmpStr = "'%s','%s'" %(locationType.lower(),
                        #                        locatorExpression.replace("'",'"')
                        #                        ) if locationType and locatorExpression else ""

                        if tmpStr:
                            tmpStr += ",u'" + operateValue + "'" if operateValue else ""
                        else:
                            tmpStr += "u'" + operateValue + "'" if operateValue else ""

                        runStr = keyWord + "(" + tmpStr + ")"

                        print("********** 拼接后表达式为： ",runStr," **********")

                        try:
                            if operateValue != "不填":
                                # 执行表达式，并返回结果
                                if isReturnedValue:     # 该步骤有返回值
                                    valueReturned = eval(runStr)
                                    print("********** 返回值为：",valueReturned," **********")
                                else:       # 该步骤无返回值
                                    eval(runStr)
                        except Exception as e:
                            print(u"********** 步骤 '%s' 执行异常 **********" %rowObj[CaseStep_stepdescribe - 1].value)

                            errorInfo = traceback.format_exc()
                            logging.info(u"步骤 '%s' 执行异常： \n"
                                          %rowObj[CaseStep_stepdescribe - 1].value,
                                          errorInfo)
                            # 截取异常截图
                            capturePic = capture_screen(picDir)
                            writeTextResult(stepSheetObj,rowNo = myRowInStepSheet,
                                            colsNo = "CaseStep",testResult = "失败",
                                            CaseInfo = str(errorInfo),picPath = capturePic)

                            # 该步骤失败后，模块运行终止
                            isToBreak = True
                            break
                        else:
                            successStepNo += 1
                            logging.info(u"步骤 '%s' 执行结束"
                                         %rowObj[CaseStep_stepdescribe - 1].value)
                            print(u"********** 执行步骤 '%s' 结束 **********" %rowObj[CaseStep_stepdescribe - 1].value)

                            # 正常结束后截图（混合驱动），myValue为”是“则截图，TODO
                            myValue = rowObj[CaseStep_lockpic - 1].value
                            if myValue == '是':
                                capturePic = capture_screen(picDir)
                                writeTextResult(stepSheetObj,rowNo = myRowInStepSheet,
                                                    colsNo = "CaseStep",testResult = "成功",
                                                    CaseInfo = str(myValue),picPath = capturePic)
                            else:
                                writeTextResult(stepSheetObj, rowNo=myRowInStepSheet,
                                                colsNo="CaseStep", testResult="成功")

                            # 判断返回值情况
                            # if isReturnedValue and valueReturned != '':
                            if isReturnedValue:
                                # 将返回值坐标、返回值，组合成JSON
                                if valueReturned is None:
                                    valueReturned = ""
                                JSON_returned = compose_JSON(isReturnedValue, valueReturned)
                                writeTextResult(dataSourceSheetObj,rowNo = Looptime + 2,
                                                colsNo = "DataSource",testResult = "失败",
                                                returnValue = JSON_returned)
                                valueReturned = None

                    if isToBreak:       #执行失败跳出标志
                        writeTextResult(sheetObj = dataSourceSheetObj,rowNo = Looptime + 2,
                                        colsNo = "DataSource",testResult = "失败",
                                        dataUse = "未使用")
                        loopToBreak = True
                        break

                    if (stepRowNums == successStepNo + 1 and moduleToLoop == i + 1) \
                            or stopToLoop == True:
                        '''
                        如果成功执行步骤数 successStepNo 等于表中给出的步骤数，
                        说明第 Looptime+2 行数据执行通过，则写入成功信息                     
                        '''
                        if isLastModule:
                            writeTextResult(sheetObj = dataSourceSheetObj,rowNo = Looptime + 2,
                                            colsNo = "DataSource",testResult = "成功",
                                            dataUse = "已使用")
                        successDataNo += 1
                        # 若该行数据执行成功，则不再执行下一行数据，待确定可否控制是否循环执行所有，TODO！！！
                        loopToBreak = True
                        break
                    else:
                        # 写入失败信息
                        writeTextResult(sheetObj = dataSourceSheetObj,rowNo = Looptime + 2,
                                        colsNo = "DataSource",testResult = "失败",
                                        dataUse="未使用")

                if loopToBreak == True or stopToLoop == True:
                    break

        if (requiredDataNo == successDataNo and moduleToLoop == 1) \
                or (requiredDataNo == successDataNo * moduleToLoop and moduleToLoop > 1) \
                or stopToLoop == True:
            '''
            成功执行数=待执行数 时，表示执行成功或跳出模块
            '''
            if "jumpToBreak" in locals().keys():
                # 存在“未使用”数据行
                if jumpToBreak:
                    return "该模块不执行"
                else:
                    return "模块执行成功"
            else:
                # 不存在“未使用”数据行
                return "无可执行数据"
        else:
            # 表示数据驱动失败
            return errorInfo

    except Exception as e:
        raise e