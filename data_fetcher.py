import requests
import json

def fetch_data(vin, start_time, end_time, data_type):
    """
    通过HTTP POST请求获取原始数据，返回data字段内容。
    参数：
        vin: 车辆VIN码
        start_time: 开始时间，格式 'YYYY-MM-DD HH:MM:SS'
        end_time: 结束时间，格式 'YYYY-MM-DD HH:MM:SS'
        data_type: 数据类型，如 'short', 'gfx' 等
    返回：
        data: list，原始数据列表
    """
    url = 'https://crs-data-service.prod.k8s.lixiang.com/common/req'
    payload = {
        "identify": f"sci_vin_detail_data_out",
        "param": {
            "type": data_type,
            "start_date": start_time.split(' ')[0],
            "start_time": start_time.split(' ')[1],
            "end_date": end_time.split(' ')[0],
            "end_time": end_time.split(' ')[1],
            "vin": vin
        }
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    response.raise_for_status()
    resp_json = response.json()
    return resp_json.get('data', []) 