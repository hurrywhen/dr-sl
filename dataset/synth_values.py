import random

SURNAMES = ["林", "沈", "顾", "陆", "苏", "叶", "许", "韩", "冯", "邓", "曹", "彭", "萧", "程", "袁",
            "傅", "蒋", "贾", "丁", "魏", "薛", "阎", "段", "雷", "侯", "龙", "史", "陶", "贺", "毛"]
GIVEN = ["梓涵", "一诺", "浩然", "欣怡", "子墨", "雨桐", "宇航", "诗涵", "俊杰", "若曦",
         "明轩", "嘉懿", "晨曦", "静姝", "云飞", "梦琪", "志强", "雅雯", "博文", "晓岚"]

CITIES = ["临江市", "云洲市", "望海县", "青山区", "南屏市", "北川县", "澄湖区", "松口市"]
STREETS = ["梧桐巷", "柳荫街", "石桥弄", "槐树路", "杏花里", "枫林道"]
HOSPITALS = ["临江仁和医院", "云洲济民诊所", "望海县中医院", "南屏安康医院"]
BANKS = ["临江商业银行", "云洲发展银行", "南屏农商银行", "北川城市银行"]
COMPANIES = ["恒瑞达贸易公司", "蓝湾餐饮管理有限公司", "晨光文具制造厂", "悦达物流有限公司"]
SCHOOLS = ["临江市第三中学", "云洲实验小学", "望海县第一中学"]
AIRLINES = ["云翔航空", "南屏航空", "蓝天航空"]
HOTELS = ["云洲江畔酒店", "临江南苑宾馆", "望海海景度假村"]
LAWFIRMS = ["正衡律师事务所", "明理律师事务所", "公义律师事务所"]
COURTS = ["临江市中级人民法院", "云洲市北区人民法院", "望海县人民法院"]

DISEASES_COMMON = ["高血压", "2型糖尿病", "慢性胃炎", "过敏性鼻炎", "腰椎间盘突出"]
DISEASES_RARE = ["亨廷顿舞蹈症", "重症肌无力", "系统性红斑狼疮", "克罗恩病"]
DRUGS = ["二甲双胍", "阿托伐他汀", "氯雷他定", "奥美拉唑", "布洛芬"]
OCCUPATIONS = ["中学教师", "货车司机", "护士", "个体商户", "会计", "外卖骑手", "软件工程师"]
INSURANCE_TYPES = ["重疾保险", "车险", "医疗保险", "意外保险"]
CASE_TYPES = ["民间借贷纠纷", "劳动合同纠纷", "离婚财产分割", "交通事故责任纠纷", "房屋买卖合同纠纷"]

FILLER = [
    "相关背景情况已在前期沟通中说明，此处不再赘述。",
    "请结合上述情况给出专业、可操作的建议，并说明理由。",
    "如有需要补充的信息，请列出清单，我会尽快提供。",
    "此前已咨询过其他渠道，但意见不一致，希望获得更明确的分析。",
    "时间比较紧，希望能尽快得到答复，谢谢。",
    "家庭经济状况一般，请在建议中考虑成本因素。",
]


def person_name(rng):
    return rng.choice(SURNAMES) + rng.choice(GIVEN)


def phone(rng):
    return "190" + "".join(rng.choice("0123456789") for _ in range(8))


def id_card(rng):
    area = rng.choice(["330103", "440305", "110105", "510107"])
    year = rng.randint(1955, 2005)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    seq = rng.randint(100, 999)
    return f"{area}{year}{month:02d}{day:02d}{seq}X"


def bank_card(rng):
    return "6222 " + " ".join("".join(rng.choice("0123456789") for _ in range(4)) for _ in range(3))


def email(rng, name=None):
    user = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(8))
    return f"{user}@example.com"


def address(rng):
    return (rng.choice(CITIES) + rng.choice(STREETS) +
            str(rng.randint(1, 200)) + "号" + str(rng.randint(1, 30)) + "栋" +
            str(rng.randint(101, 2504)) + "室")


def passport(rng):
    return "E" + "".join(rng.choice("0123456789") for _ in range(8))


def plate(rng):
    return rng.choice("ABCDEF") + "".join(rng.choice("0123456789") for _ in range(5))


def flight_no(rng):
    return rng.choice(["YX", "NP", "LT"]) + str(rng.randint(1000, 9999))


def case_no(rng):
    return f"({rng.randint(2020, 2025)}){rng.choice(['苏01','浙03','粤05'])}民初{rng.randint(1000,9999)}号"


def mrn(rng):
    return "ZY" + "".join(rng.choice("0123456789") for _ in range(8))


def age(rng):
    return rng.randint(18, 85)


def income(rng):
    return rng.choice(["月收入约4000元", "月收入约1.2万元", "年收入约30万元", "月收入约8000元"])


def date_str(rng):
    return f"{rng.randint(2022, 2025)}年{rng.randint(1, 12)}月{rng.randint(1, 28)}日"


def money(rng, lo=5000, hi=2000000):
    v = rng.randint(lo // 1000, hi // 1000) * 1000
    return f"{v}元"
