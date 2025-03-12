from langchain_core.tools import tool
from rich.console import Console
import requests
import json


console = Console(force_terminal=False)



def get_scheduling_result(year, month):
    # 请求接口地址
    url = "http://119.23.69.219:3000/gac/api/month/plan/v2/list"

    # 请求头
    headers = {
        "Content-Type": "application/json"
    }

    # 请求参数
    payload = {
        "factoryId": 40,
        "userId": 11140,
        "year":year,
        "month":month
    }

    try:
        # 发送 POST 请求
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # 检查请求是否成功

        # 解析返回的 JSON 数据
        result = response.json()
        return result['data'][0]['monthDemandId']

    except requests.exceptions.HTTPError as http_err:
        # 处理 HTTP 错误
        print(f"HTTP 错误: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        # 处理连接错误
        print(f"连接错误: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        # 处理超时错误
        print(f"请求超时: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        # 处理其他请求异常
        print(f"请求异常: {req_err}")
    except json.JSONDecodeError as json_err:
        # 处理 JSON 解析错误
        print(f"JSON 解析错误: {json_err}")

    return None

# # 调用函数获取排产结果
# scheduling_result = get_scheduling_result()
# if scheduling_result:
#     print("排产结果:", scheduling_result)
# else:
#     print("获取排产结果失败。")

def check_sale_model(sale_model: str) -> bool:
    # 导入saling models.json
    """
    用于在 call_aps_data_for_specific_saling_model() 函数中, 为匹配正确的车型提供硬规则
    往后的开发,这里应该从数据库中获取数据
    """
    with open(
        "/Users/86183/Desktop/学习日志/大模型/Langchain/APS-agent-main/saling_models.json",
        encoding="utf-8",
    ) as file:
        data = json.load(file)
    if sale_model in data["saling_models"]:
        return True
    else:
        return False


# tool function for agent
@tool
def call_all_aps_data(year: int = 2025, month: int = 2) -> dict:
    """
    在用户没有指定年月时候，默认year参数为2025,month参数为2.
    在用户指定年月后，将相应的值赋给year和month
    在没有给定具体 "在售车型" 的情况下, 请求所有车型的排产数据,返回一个json字符串

    本工具的主要功能是: 在用户没有明确指定要查看某个 "在售车型" 的具体数据时, 你可以请求所有排产数据, 以辅助你完成任务

    但此时, 数据量很大, 更容易对你的分析造成干扰, 不到迫不得已, 一般不调用此功能
    """
    # 请求接口地址
    factory_id = 99
    user_id = 25
    user_name = "wqh"
    month_demand_id = get_scheduling_result(year,month)

    url = "http://119.23.69.219:3000/gac/api/month/plan/v2/schedule/result/v2"

    # 请求头
    headers = {"Content-Type": "application/json"}

    # 请求参数
    payload = {
        "monthDemandId": month_demand_id,
        "factoryId": factory_id,
        "userId": user_id,
        "userName": user_name,
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    result = response.json()
    # console.print(result, style="grey50")
    return {"res": str(result["data"])}





@tool
def count_all_cars_total_amounts(year: int = 2025, month: int = 2) -> dict:
    """
    在用户没有指定年月时候，默认year参数为2025,month参数为2.
    在用户指定年月后，将相应的值赋给year和month
    在没有给定具体 "在售车型" 的情况下, 也可以请求本工具

    但本工具的主要目的是, 分别统计所有车型的总排产量

    数据量相对较小, 且精确
    """
    # 请求接口地址
    factory_id = 99
    user_id = 25
    user_name = "wqh"
    month_demand_id = get_scheduling_result(year,month)

    url = "http://119.23.69.219:3000/gac/api/month/plan/v2/schedule/result/v2"

    # 请求头
    headers = {"Content-Type": "application/json"}

    # 请求参数
    payload = {
        "monthDemandId": month_demand_id,
        "factoryId": factory_id,
        "userId": user_id,
        "userName": user_name,
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    result = response.json()
    data = result["data"]
    for item in data:
        total_count = 0
        for supply in item["supplyCountList"]:
            total_count += supply["count"]
        item["月总生产(辆)"] = total_count
        del item["supplyCountList"]
        del item["monthDemandType"]

    # console.print(data, style="grey50")
    return {"res": str(data)}


@tool
def call_aps_data_for_specific_saling_model(sale_model: str, year: int = 2025, month: int = 2) -> dict:
    """
    在用户没有指定年月时候，默认year参数为2025,month参数为2.
    在用户指定年月后，将相应的值赋给year和month
    
    sale_model: str - 在售车型
    调用此功能时, 请根据用户的问题, 自动匹配正确的 "在售车型" 名称, 否则会返回错误信息

    注意到: "在售车型" 和 "系列车型" 并非一个概念, 因此 sale_model 的值, 千万不要填成下述  "系列车型" 中的任一值:

        "系列车型" 是 "在售车型" 的父级概念,
            目前的 "系列车型" 有 :
                "AION LX"
                "AION V"
                "Hyper GT"
                "Hyper HT"
                "Hyper HT 出口车"

        "在售车型" 只有可能有以下值:
            650激光雷达版
            650智尊版
            650智豪版
            520激光雷达版
            520智尊版
            520智豪版
            千里版
            80D MAX版
            80D 旗舰版
            80 智尊版
            560科技版
            710后驱特高压激光雷达版
            710特高压智驾版
            825欧翼激光雷达版
            825特高压激光雷达版
            825特高压智驾版
            670特高压激光雷达版
            670后驱特高压MAX版
            670鸥翼特高压NDA版
            670鸥翼特高压激光雷达版
            520智享版
            泰国版（右舵） 650版
            菲律宾版（左舵） 650版
            新加坡版（右舵） 650版
            710超充MAX版
            710后驱超充Pro版
            710后驱超充七翼版
            710超充七翼版
            710超充版
            630 3R5V尾翼储备版
            600充换版
            560七翼版
            670后驱特高压NDA版
            670后驱特高压激光雷达版
            670后驱特高压版
            600后驱科技版
            550充换版
            550后驱充换版
            次高配科技版（泰国版 右舵）
            高配科技版（泰国版 右舵）
            印尼版（右舵）
            新加坡版（右舵）
            新加坡版（右舵）-鸥翼
            马来西亚版（右舵）-鸥翼
            马来西亚版（右舵）
            Hyper SSR Sprint 极速版
            Hyper SSR
            610智驾版【IDU00】-183Ah快充
            610智驾版【汇川】-183Ah快充
            610乐享版【IDU00】-183Ah快充
            610乐享版【汇川】-183Ah快充
            510智驾版【PLAN A】-183Ah快充
            510智驾版【日电产 P档】-183Ah快充
            510智领版【PLAN A】-183Ah快充
            510乐享版【PLAN A】-183Ah快充
            500-减电量-因湃
            500-减电量-时广
            YY星耀版-BAT00-400快充
            YY星耀版-EVE减快充
            YY-BAT00-400快充
            YY-EVE减快充
            70星耀版
            650 激光雷达版
            650 智豪版
            520 激光雷达版
            520 智豪版
            520 智享版
            （旧配置表派生）泰国版
            （旧配置表派生）越南版
            巴林（左舵）490AV高阶
            厄瓜多尔（左舵）490AV高阶
            厄瓜多尔（左舵）490AV基础
            菲律宾（左舵）490AV高阶
            菲律宾（左舵）490AV基础
            马来西亚（右舵）490AVNT高阶
            马来西亚（右舵）490AV高阶
            马来西亚（右舵）490AV基础
            马来西亚（右舵）410AVNT高阶
            缅甸（左舵）490AV高阶
            泰国（右舵）490AVNT高阶
            泰国（右舵）410AVNT高阶
            香港（右舵）490ANVT高阶
            香港（右舵）490AV基础
            新加坡（右舵）490AVNT高阶
            新加坡（右舵）490AV基础
            越南（左舵）490AVNT高阶
            老挝（左舵）490AVNT高阶
            柬埔寨（左舵）490AVNT高阶
            菲律宾（左舵）490AVNT高阶
            印尼（右舵）490AVNT高阶
            印尼（右舵）410AVNT高阶
            欧洲版（左舵）490版
            750智尊版
            650智享版
            马来西亚版（右舵） 650版
            越南版（左舵） 650版
            缅甸版（左舵） 650版
            柬埔寨版（左舵） 650版
            老挝版（左舵） 650版
            印尼版（右舵） 650版
            印尼版（右舵） 520版
            630激光雷达版
            670高阶智驾版
            AH8四驱（非晶）
            AH8四驱
            AH8两驱（非晶）
            AH8两驱
            越南版（左舵）
            柬埔寨版（左舵）
            老挝版（左舵）
            欧盟版（左舵）
            阿联酋版（左舵）-鸥翼


    在给定具体在售车型的情况下,请求该车型的排产数据,返回一个json字符串

    本工具的主要功能, 是查询一个具体的 "在售车型" 的排产数据, 数据量更小, 且更精确

    """
    if check_sale_model(sale_model):
        factory_id = 99
        user_id = 25
        user_name = "wqh"
        month_demand_id = get_scheduling_result(year,month)
        # 请求接口地址
        url = "http://119.23.69.219:3000/gac/api/month/plan/v2/schedule/result/v2"

        # 请求头
        headers = {"Content-Type": "application/json"}

        # 请求参数
        payload = {
            "monthDemandId": month_demand_id,
            "factoryId": factory_id,
            "userId": user_id,
            "userName": user_name,
            "saleModel": sale_model,
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()
        # console.print(result, style="grey50")
        return {"res": str(result["data"])}
    else:
        return "'在售车型'参数输入错误!!!"


@tool
def call_all_saling_models_within_series(year:int = 2025, month: int = 2) -> dict:
    """
    在用户没有指定年月时候，默认year参数为2025,month参数为2.
    在用户指定年月后，将相应的值赋给year和month
    
    调用此工具以获取 按照所有 "系列车型" 进行分类的所有 "在售车型" 列表

    数据量相对较小,且精确

    用以解决如下问题:
        一共多少车型?每种车型都有什么车?
        哪个系列生产数量最多?
        续航最长的车是哪个?
        某个系列卖的怎么样?
        海外车型卖的怎么样?
        ....
    """
    factory_id = 99
    user_id = 25
    user_name = "wqh"
    month_demand_id = get_scheduling_result(year, month)

    url = "http://119.23.69.219:3000/gac/api/month/plan/v2/schedule/result/v2"

    # 请求头
    headers = {"Content-Type": "application/json"}

    # 请求参数
    payload = {
        "monthDemandId": month_demand_id,
        "factoryId": factory_id,
        "userId": user_id,
        "userName": user_name,
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    data = response.json()
    # 创建一个字典来存储分类后的数据
    classified_data = {}

    # 遍历数据并进行分类
    for item in data["data"]:
        total_count = 0
        for supply in item["supplyCountList"]:
            total_count += supply["count"]
        item["月总生产(辆)"] = total_count
        car_series = item["carSeries"]
        sale_model = item["saleModel"]
        del item["supplyCountList"]
        del item["monthDemandType"]
        del item["mt"]
        del item["carSeries"]
        del item["startDay"]

        if car_series not in classified_data:
            classified_data[car_series] = {}

        if sale_model not in classified_data[car_series]:
            classified_data[car_series][sale_model] = []

        classified_data[car_series][sale_model].append(item)

    # console.print(classified_data, style="grey50")
    return {"res": str(classified_data)}

