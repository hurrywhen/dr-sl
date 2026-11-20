"""Disjoint vocabulary for holdout-2 (vocabulary-shift stress test).

Every lexicon here is asserted disjoint from ``synth_values.py`` so that the
runtime extractor (whose lexicons are built from synth_values) cannot match
these values by dictionary lookup.  Explicit identifiers remain pattern-based.
This is a stress test of vocabulary shift, not an open-world NER claim.
"""
import random

import synth_values as sv

SURNAMES = ["赵", "钱", "孙", "李", "周", "吴", "郑", "王", "陈", "褚", "卫", "杨", "朱", "秦",
            "尤", "施", "张", "孔", "严", "华", "金", "姜", "戚", "谢", "邹", "喻", "柏", "水", "窦", "章"]
GIVEN = ["建国", "淑芬", "伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋", "勇", "艳",
         "杰", "娟", "涛", "明", "超", "秀英", "建华", "文军", "桂兰", "玉梅", "海燕", "国庆", "晓东", "雪梅", "振华", "春梅"]

CITIES = ["霜林市", "雁门市", "沧澜市", "碧落市", "玄岳市", "赤沙市", "白鹿市", "青川市"]
STREETS = ["松柏巷", "桃李街", "竹溪弄", "樟树路", "桂花里", "榕林道"]
HOSPITALS = ["霜林仁济医院", "雁门博爱医院", "沧澜康宁医院", "碧落济世医院"]
BANKS = ["霜林通商银行", "雁门汇通银行", "沧澜丰业银行", "碧落恒信银行"]
COMPANIES = ["鑫源贸易有限公司", "宏图餐饮管理有限公司", "新华文具制造厂", "顺通物流有限公司"]
SCHOOLS = ["霜林市第二中学", "雁门育才小学", "沧澜县实验中学"]
AIRLINES = ["霜林航空", "雁门航空", "沧澜航空"]
HOTELS = ["霜林山景酒店", "雁门湖滨宾馆", "沧澜花园度假村"]
LAWFIRMS = ["天平律师事务所", "正义律师事务所", "公平律师事务所"]
COURTS = ["霜林市中级人民法院", "雁门市南区人民法院", "沧澜县人民法院"]

DISEASES_COMMON = ["冠心病", "哮喘", "慢性肾炎", "甲状腺功能亢进", "类风湿关节炎"]
DISEASES_RARE = ["肌萎缩侧索硬化", "多发性硬化", "白塞病", "结节病"]
DRUGS = ["硝苯地平", "美托洛尔", "泼尼松", "甲氨蝶呤", "卡马西平"]
OCCUPATIONS = ["小学教师", "公交司机", "医生", "零售商", "出纳", "快递员", "机械工程师"]
INSURANCE_TYPES = ["寿险", "财产保险", "健康保险", "责任保险"]
CASE_TYPES = ["买卖合同纠纷", "租赁合同纠纷", "继承纠纷", "侵权责任纠纷", "股权转让纠纷"]
ALLERGIES = ["牛奶", "鸡蛋", "坚果", "青霉素"]


def assert_disjoint():
    pairs = [
        ("SURNAMES", SURNAMES, sv.SURNAMES), ("GIVEN", GIVEN, sv.GIVEN),
        ("CITIES", CITIES, sv.CITIES), ("STREETS", STREETS, sv.STREETS),
        ("HOSPITALS", HOSPITALS, sv.HOSPITALS), ("BANKS", BANKS, sv.BANKS),
        ("COMPANIES", COMPANIES, sv.COMPANIES), ("SCHOOLS", SCHOOLS, sv.SCHOOLS),
        ("HOTELS", HOTELS, sv.HOTELS), ("LAWFIRMS", LAWFIRMS, sv.LAWFIRMS),
        ("COURTS", COURTS, sv.COURTS),
        ("DISEASES_COMMON", DISEASES_COMMON, sv.DISEASES_COMMON),
        ("DISEASES_RARE", DISEASES_RARE, sv.DISEASES_RARE),
        ("DRUGS", DRUGS, sv.DRUGS), ("OCCUPATIONS", OCCUPATIONS, sv.OCCUPATIONS),
        ("INSURANCE_TYPES", INSURANCE_TYPES, sv.INSURANCE_TYPES),
        ("CASE_TYPES", CASE_TYPES, sv.CASE_TYPES),
    ]
    for name, new, old in pairs:
        overlap = set(new) & set(old)
        assert not overlap, f"{name} overlaps extractor lexicon: {overlap}"
    # names built from the new surname/given pools must not collide with old names
    old_names = {a + b for a in sv.SURNAMES for b in sv.GIVEN}
    new_names = {a + b for a in SURNAMES for b in GIVEN}
    assert not (old_names & new_names), "name pools overlap"
    return True


def person_name(rng):
    return rng.choice(SURNAMES) + rng.choice(GIVEN)


def phone(rng):
    return "191" + "".join(rng.choice("0123456789") for _ in range(8))


def id_card(rng):
    area = rng.choice(["320102", "440304", "110102", "510104"])
    year = rng.randint(1955, 2005)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    seq = rng.randint(100, 999)
    return f"{area}{year}{month:02d}{day:02d}{seq}X"


def bank_card(rng):
    return "6228 " + " ".join("".join(rng.choice("0123456789") for _ in range(4)) for _ in range(3))


def email(rng, name=None):
    user = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(8))
    return f"{user}@example.org"


def address(rng):
    return (rng.choice(CITIES) + rng.choice(STREETS) +
            str(rng.randint(1, 200)) + "号" + str(rng.randint(1, 30)) + "栋" +
            str(rng.randint(101, 2504)) + "室")


def passport(rng):
    return "E" + "".join(rng.choice("0123456789") for _ in range(8))


def plate(rng):
    return rng.choice("ABCDEF") + "".join(rng.choice("0123456789") for _ in range(5))


def flight_no(rng):
    return rng.choice(["SL", "YM", "CL"]) + str(rng.randint(1000, 9999))


def case_no(rng):
    return f"({rng.randint(2020, 2025)}){rng.choice(['苏02','浙04','粤06'])}民初{rng.randint(1000,9999)}号"


def mrn(rng):
    return "ZY" + "".join(rng.choice("0123456789") for _ in range(8))


def age(rng):
    return rng.randint(18, 85)


def income(rng):
    return rng.choice(["月收入约5000元", "月收入约1.5万元", "年收入约25万元", "月收入约9000元"])


def date_str(rng):
    return f"{rng.randint(2022, 2025)}年{rng.randint(1, 12)}月{rng.randint(1, 28)}日"


def money(rng, lo=5000, hi=2000000):
    v = rng.randint(lo // 1000, hi // 1000) * 1000
    return f"{v}元"
