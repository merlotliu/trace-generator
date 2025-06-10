import requests
import json
import logging

def fetch_data(vin, start_time, end_time, data_type, sub_type=None):
    """
    通过HTTP POST请求从多个节点获取原始数据，返回第一个成功节点的data字段内容。
    参数：
        vin: 车辆VIN码
        start_time: 开始时间，格式 'YYYY-MM-DD HH:MM:SS'
        end_time: 结束时间，格式 'YYYY-MM-DD HH:MM:SS'
        data_type: 数据类型，如 'short', 'gfx' 等
    返回：
        data: list，原始数据列表（只要有一个节点返回即返回）
    节点说明：
        依次尝试多个服务节点，只要有一个节点成功返回数据即视为成功。
    """
    urls = [
        'https://crs-data-service.dev.k8s.lixiang.com/common/req',
        'https://crs-data-service.prod.k8s.lixiang.com/common/req',
    ]
    payload = {
        "identify": f"sci_vin_detail_data_out",
        "param": {
            "type": data_type,
            "sub_type": sub_type,
            "start_date": start_time.split(' ')[0],
            "start_time": start_time.split(' ')[1],
            "end_date": end_time.split(' ')[0],
            "end_time": end_time.split(' ')[1],
            "vin": vin
        }
    }
    headers = {'Content-Type': 'application/json'}
    errors = []
    for url in urls:
        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
            response.raise_for_status()
            try:
                resp_json = response.json()
            except json.JSONDecodeError as e:
                logging.error(f"[{url}] 响应内容不是有效的JSON: {e}\n响应内容: {response.text}")
                errors.append(f"[{url}] JSON解析失败: {e}")
                continue
            if not isinstance(resp_json, dict):
                logging.error(f"[{url}] 响应JSON不是字典类型: {resp_json}")
                errors.append(f"[{url}] 响应JSON不是字典类型")
                continue
            data = resp_json.get('data', [])
            if not isinstance(data, list):
                logging.error(f"[{url}] data字段不是列表类型: {data}")
                errors.append(f"[{url}] data字段不是列表类型")
                continue
            if data:
                return data
            else:
                logging.warning(f"[{url}] data字段为空列表")
                errors.append(f"[{url}] data字段为空列表")
        except requests.RequestException as e:
            logging.error(f"[{url}] 网络请求失败: {e}")
            errors.append(f"[{url}] 网络请求失败: {e}")
        except Exception as e:
            logging.error(f"[{url}] 未知错误: {e}")
            errors.append(f"[{url}] 未知错误: {e}")
    logging.error(f"所有节点均请求失败，错误信息: {errors}")
    return [] 