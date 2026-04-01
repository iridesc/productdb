from datetime import date, datetime
import random
import string

# 模拟数据库会话和SalesOrder模型
class MockDB:
    def query(self, model):
        return MockQuery()

class MockQuery:
    def filter(self, condition):
        return self
    def count(self):
        return 5  # 模拟当天已有5个订单

class MockSalesOrder:
    pass

# 复制修改后的generate_order_no函数
def generate_order_no(db):
    """生成订单号"""
    today = date.today()
    year_prefix = today.strftime("%Y")[:2]  # 年份前两位
    date_str = today.strftime("%m%d")  # 月日
    
    # 计算当天订单数量
    from datetime import datetime
    today_start = datetime.combine(today, datetime.min.time())
    today_order_count = db.query(MockSalesOrder).filter(
        True  # 模拟条件
    ).count() + 1  # 加1是因为当前订单还未创建
    
    # 生成订单号：SO-年份前两位-月日-当天序号
    return f"SO-{year_prefix}-{date_str}-{today_order_count:03d}"

# 测试订单编号生成
mock_db = MockDB()
order_no = generate_order_no(mock_db)
print(f"生成的订单编号: {order_no}")
print(f"订单编号长度: {len(order_no)}")
