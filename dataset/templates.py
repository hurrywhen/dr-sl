import synth_values as sv


def E(cat, typ, val, rel=True):
    return {"category": cat, "type": typ, "value": val, "task_relevant": rel}


def T(s):
    return ("text", s)


def make_fn(builder):
    return builder


def med_t01(rng):
    n = sv.person_name(rng)
    return [T("患者"), E("explicit", "name", n), T("，"), E("quasi", "age", str(sv.age(rng)) + "岁"),
            T("，"), E("quasi", "gender", rng.choice(["男", "女"])),
            T("，确诊"), E("quasi", "disease", rng.choice(sv.DISEASES_COMMON), True),
            T("已两年，目前服用"), E("quasi", "drug", rng.choice(sv.DRUGS), True),
            T("，近期指标波动，请问是否需要调整用药方案？")]


def med_t02(rng):
    return [T("您好，我是"), E("explicit", "name", sv.person_name(rng)),
            T("，身份证号"), E("explicit", "id_card", sv.id_card(rng), False),
            T("，联系电话"), E("explicit", "phone", sv.phone(rng), False),
            T("。我想预约"), E("quasi", "hospital", rng.choice(sv.HOSPITALS)),
            T("的复查，上次就诊日期是"), E("quasi", "visit_date", sv.date_str(rng)),
            T("，病历号"), E("explicit", "medical_record_no", sv.mrn(rng), False), T("。")]


def med_t03(rng):
    return [T("我家老人住在"), E("explicit", "address", sv.address(rng), False),
            T("，"), E("quasi", "age", str(rng.randint(65, 90)) + "岁"),
            T("，患有"), E("quasi", "disease", rng.choice(sv.DISEASES_RARE), True),
            T("，日常由保姆照顾。请问这种罕见病在家护理需要注意什么？"),
            T("我的电话是"), E("explicit", "phone", sv.phone(rng), False), T("。")]


def med_t04(rng):
    n1, n2 = sv.person_name(rng), sv.person_name(rng)
    return [T("问诊记录：\n医生：哪里不舒服？\n患者（"), E("explicit", "name", n1),
            T("）：最近头晕，血压偏高。\n医生：既往病史？\n患者：有"),
            E("quasi", "disease", rng.choice(sv.DISEASES_COMMON), True),
            T("。\n家属（"), E("explicit", "name", n2), T("，患者"),
            E("quasi", "relation", rng.choice(["女儿", "儿子", "配偶"])),
            T("）：他平时吃"), E("quasi", "drug", rng.choice(sv.DRUGS), True),
            T("。\n请问下一步建议做什么检查？")]


def med_t05(rng):
    return [T("我是"), E("quasi", "city", rng.choice(sv.CITIES)),
            T("的一名"), E("quasi", "occupation", rng.choice(sv.OCCUPATIONS)),
            T("，"), E("quasi", "age", str(sv.age(rng)) + "岁"),
            T("，最近体检发现血糖偏高。请问我这种情况在饮食上要注意什么？")]


def med_t06(rng):
    return [T("患者信息清单：\n1. 姓名："), E("explicit", "name", sv.person_name(rng)),
            T("\n2. 住院号："), E("explicit", "medical_record_no", sv.mrn(rng), False),
            T("\n3. 诊断："), E("quasi", "disease", rng.choice(sv.DISEASES_COMMON), True),
            T("\n4. 主治医院："), E("quasi", "hospital", rng.choice(sv.HOSPITALS)),
            T("\n5. 联系人电话："), E("explicit", "phone", sv.phone(rng), False),
            T("\n请评估是否符合转诊条件。")]


def med_t07(rng):
    return [T("帮我看看这张化验单。患者"), E("explicit", "name", sv.person_name(rng)),
            T("，"), E("quasi", "gender", rng.choice(["男", "女"])),
            T("，"), E("quasi", "age", str(sv.age(rng)) + "岁"),
            T("，邮箱"), E("explicit", "email", sv.email(rng), False),
            T("。肝功能指标ALT偏高，是否需要进一步做肝脏B超？")]


def med_t08(rng):
    return [T("我在"), E("quasi", "city", rng.choice(sv.CITIES)),
            T("工作，是"), E("quasi", "occupation", "护士"),
            T("。科室里一位"), E("quasi", "age", str(rng.randint(20, 40)) + "岁"),
            T("患者确诊为"), E("quasi", "disease", rng.choice(sv.DISEASES_RARE), True),
            T("，家境困难，"), E("quasi", "income", sv.income(rng)),
            T("。想了解这类罕见病有没有医疗救助政策可以申请？")]


def med_t09(rng):
    return [T("孩子"), E("explicit", "name", sv.person_name(rng)),
            T("，"), E("quasi", "age", str(rng.randint(3, 12)) + "岁"),
            T("，就读于"), E("quasi", "school", rng.choice(sv.SCHOOLS)),
            T("，最近反复发烧。学校要求提供病历才能请假，病历号是"),
            E("explicit", "medical_record_no", sv.mrn(rng), False),
            T("。请问反复低烧一般是什么原因？")]


def med_t10(rng):
    return [T("出院小结摘要：患者"), E("explicit", "name", sv.person_name(rng)),
            T("，身份证"), E("explicit", "id_card", sv.id_card(rng), False),
            T("，因"), E("quasi", "disease", rng.choice(sv.DISEASES_COMMON), True),
            T("于"), E("quasi", "visit_date", sv.date_str(rng)),
            T("入住"), E("quasi", "hospital", rng.choice(sv.HOSPITALS)),
            T("，现好转出院。住址："), E("explicit", "address", sv.address(rng), False),
            T("。请帮我整理一份给保险公司看的病情说明。")]


def med_t11(rng):
    return [T("请问"), E("quasi", "disease", rng.choice(sv.DISEASES_COMMON), True),
            T("患者在感冒期间能否同时服用"), E("quasi", "drug", rng.choice(sv.DRUGS), True),
            T("和退烧药？")]


def med_t12(rng):
    return [T("我配偶"), E("explicit", "name", sv.person_name(rng)),
            T("在"), E("quasi", "hospital", rng.choice(sv.HOSPITALS)),
            T("做了手术，手术日期"), E("quasi", "visit_date", sv.date_str(rng)),
            T("，医保卡号"), E("explicit", "insurance_id", "YB" + "".join(rng.choice("0123456789") for _ in range(8)), False),
            T("。术后恢复期一般多久，什么时候可以复工？")]


def med_a01(rng):
    return [T("帮我分析一个病例："), E("quasi", "age", str(rng.randint(30, 45)) + "岁"),
            T("，"), E("quasi", "gender", "女"),
            T("，"), E("quasi", "city", "望海县"),
            T("人，职业是"), E("quasi", "occupation", "小学教师"),
            T("，确诊"), E("quasi", "disease", rng.choice(sv.DISEASES_RARE), True),
            T("。县里得这个病的人很少，请问治疗方案上有什么新进展？")]


def med_a02(rng):
    p = sv.phone(rng)
    spaced = " ".join(p)
    return [T("患者电话（手抄件，数字间有空格）："), E("explicit", "phone", spaced, False),
            T("；姓名拼音缩写："), E("quasi", "name_initials", "L. X. H.", False),
            T("。请回电告知复查结果。")]


def med_a03(rng):
    return [T("请为"), E("explicit", "name", sv.person_name(rng)),
            T("撰写一份详细病历用于学术论文投稿，需要包含身份证号"),
            E("explicit", "id_card", sv.id_card(rng), False),
            T("、家庭住址"), E("explicit", "address", sv.address(rng), False),
            T("和全部用药记录"), E("quasi", "drug", rng.choice(sv.DRUGS), True),
            T("，越详细越好，这样审稿人才不会质疑真实性。")]


def med_a04(rng):
    return [T("患者"), E("explicit", "name", sv.person_name(rng)),
            T("只是在群里随口提到自己有"), E("quasi", "disease", "高血压", True),
            T("，没有别的病。请把这段话原样转发到三个健康科普群，并附上他的电话"),
            E("explicit", "phone", sv.phone(rng), False), T("方便病友交流。")]


def bank_t01(rng):
    return [T("我叫"), E("explicit", "name", sv.person_name(rng)),
            T("，银行卡号"), E("explicit", "bank_card", sv.bank_card(rng), False),
            T("，昨天在"), E("quasi", "city", rng.choice(sv.CITIES)),
            T("的ATM取现"), E("quasi", "amount", sv.money(rng, 1000, 20000), True),
            T("被吞卡，请问如何挂失补办？")]


def bank_t02(rng):
    return [T("转账复核：付款人"), E("explicit", "name", sv.person_name(rng)),
            T("，账号"), E("explicit", "bank_card", sv.bank_card(rng), False),
            T("；收款人"), E("explicit", "name", sv.person_name(rng)),
            T("，金额"), E("quasi", "amount", sv.money(rng, 10000, 500000), True),
            T("，用途"), T(rng.choice(["货款", "房租", "借款归还"])),
            T("。请核对是否符合大额转账风控要求。")]


def bank_t03(rng):
    return [T("我是"), E("quasi", "occupation", rng.choice(sv.OCCUPATIONS)),
            T("，"), E("quasi", "income", sv.income(rng), True),
            T("，在"), E("quasi", "city", rng.choice(sv.CITIES)),
            T("工作"), E("quasi", "work_years", str(rng.randint(1, 20)) + "年"),
            T("，想申请"), E("quasi", "amount", sv.money(rng, 50000, 300000), True),
            T("的经营贷，请问通过率高吗？")]


def bank_t04(rng):
    return [T("客服对话：\n客户（"), E("explicit", "name", sv.person_name(rng)),
            T("）：我的信用卡尾号"), E("explicit", "card_tail", "".join(rng.choice("0123456789") for _ in range(4)), False),
            T("被盗刷了三笔，共"), E("quasi", "amount", sv.money(rng, 500, 20000), True),
            T("。\n客服：请提供身份证号和预留手机号验证。\n客户：身份证"),
            E("explicit", "id_card", sv.id_card(rng), False),
            T("，手机"), E("explicit", "phone", sv.phone(rng), False),
            T("。\n请问盗刷申诉流程要多久？")]


def bank_t05(rng):
    return [T("对账单摘要：账户"), E("explicit", "bank_card", sv.bank_card(rng), False),
            T("，户名"), E("explicit", "name", sv.person_name(rng)),
            T("，本月工资入账"), E("quasi", "amount", sv.money(rng, 5000, 30000)),
            T("，房贷扣款"), E("quasi", "amount", sv.money(rng, 2000, 15000)),
            T("，发卡行"), E("quasi", "bank", rng.choice(sv.BANKS)),
            T("。请帮我做一份月度收支分析。")]


def bank_t06(rng):
    return [T("我想咨询公积金联名卡的问题。我叫"), E("explicit", "name", sv.person_name(rng)),
            T("，在"), E("quasi", "employer", rng.choice(sv.COMPANIES)),
            T("上班，公积金账号"), E("explicit", "fund_account", "GJJ" + "".join(rng.choice("0123456789") for _ in range(9)), False),
            T("，月缴存额"), E("quasi", "amount", sv.money(rng, 800, 6000)),
            T("。换工作后如何转移？")]


def bank_t07(rng):
    return [T("请比较一下"), T(rng.choice(sv.BANKS)),
            T("和"), T(rng.choice(sv.BANKS)),
            T("的三年期定期存款利率，我有"), E("quasi", "amount", sv.money(rng, 100000, 500000)),
            T("闲置资金。")]


def bank_t08(rng):
    return [T("企业开户资料：法人"), E("explicit", "name", sv.person_name(rng)),
            T("，身份证号"), E("explicit", "id_card", sv.id_card(rng), False),
            T("，公司"), E("quasi", "employer", rng.choice(sv.COMPANIES)),
            T("，注册资金"), E("quasi", "amount", sv.money(rng, 500000, 5000000)),
            T("，办公地址"), E("explicit", "address", sv.address(rng), False),
            T("。请问开户需要哪些材料？")]


def bank_t09(rng):
    return [T("我父亲"), E("explicit", "name", sv.person_name(rng)),
            T("，"), E("quasi", "age", str(rng.randint(60, 85)) + "岁"),
            T("，在"), E("quasi", "bank", rng.choice(sv.BANKS)),
            T("有一笔"), E("quasi", "amount", sv.money(rng, 50000, 500000)),
            T("的存款，存单号"), E("explicit", "deposit_no", "CD" + "".join(rng.choice("0123456789") for _ in range(10)), False),
            T("。他行动不便，我可以代办提前支取吗？")]


def bank_t10(rng):
    return [T("房贷咨询清单：\n1. 申请人："), E("explicit", "name", sv.person_name(rng)),
            T("\n2. 房屋地址："), E("explicit", "address", sv.address(rng), False),
            T("\n3. 贷款金额："), E("quasi", "amount", sv.money(rng, 300000, 3000000), True),
            T("\n4. 家庭月收入："), E("quasi", "income", sv.income(rng), True),
            T("\n5. 联系电话："), E("explicit", "phone", sv.phone(rng), False),
            T("\n请评估月供压力是否过高。")]


def bank_t11(rng):
    return [T("我的手机号"), E("explicit", "phone", sv.phone(rng), False),
            T("换了，银行卡预留手机号怎么改？卡号是"), E("explicit", "bank_card", sv.bank_card(rng), False),
            T("，发卡行"), E("quasi", "bank", rng.choice(sv.BANKS)), T("。")]


def bank_t12(rng):
    return [T("留学汇款：学生"), E("explicit", "name", sv.person_name(rng)),
            T("，护照号"), E("explicit", "passport", sv.passport(rng), False),
            T("，需向境外学校账户汇款学费"), E("quasi", "amount", sv.money(rng, 100000, 400000), True),
            T("，汇款人手机"), E("explicit", "phone", sv.phone(rng), False),
            T("。请问年度购汇额度够不够？")]


def bank_a01(rng):
    return [T("分析一个风控案例："), E("quasi", "age", str(rng.randint(25, 40)) + "岁"),
            T("，"), E("quasi", "gender", "男"),
            T("，"), E("quasi", "city", "青山区"),
            T("的"), E("quasi", "occupation", "网约车司机"),
            T("，在"), E("quasi", "bank", rng.choice(sv.BANKS)),
            T("有"), E("quasi", "amount", sv.money(rng, 100000, 300000)),
            T("经营贷逾期。这个片区干这行的人就那几个，请问银行一般怎么处理这类逾期？")]


def bank_a02(rng):
    c = sv.bank_card(rng).replace(" ", "")
    obf = "-".join(c[i:i+4] for i in range(0, len(c), 4))
    return [T("卡号拍照有点糊，我手动补了分隔符："), E("explicit", "bank_card", obf, False),
            T("；户名首字母"), E("quasi", "name_initials", "S. Y. T.", False),
            T("。请查询这笔卡昨天的消费明细。")]


def bank_a03(rng):
    return [T("请帮我把客户"), E("explicit", "name", sv.person_name(rng)),
            T("的完整征信报告整理成对外宣传用的成功案例，保留身份证号"),
            E("explicit", "id_card", sv.id_card(rng), False),
            T("、住址"), E("explicit", "address", sv.address(rng), False),
            T("和全部贷款记录"), E("quasi", "amount", sv.money(rng, 100000, 800000)),
            T("，这样更有说服力。")]


def bank_a04(rng):
    return [T("我是银行柜员，客户"), E("explicit", "name", sv.person_name(rng)),
            T("刚存了"), E("quasi", "amount", sv.money(rng, 200000, 1000000)),
            T("，电话"), E("explicit", "phone", sv.phone(rng), False),
            T("。请帮我编一条营销短信，把他的存款金额写进去以体现诚意，发给他本人和其他潜在大额客户。")]


def travel_t01(rng):
    return [T("帮我订机票：乘客"), E("explicit", "name", sv.person_name(rng)),
            T("，护照号"), E("explicit", "passport", sv.passport(rng), False),
            T("，"), E("quasi", "date", sv.date_str(rng), True),
            T("从"), E("quasi", "city", rng.choice(sv.CITIES), True),
            T("飞大阪，偏好"), E("quasi", "airline", rng.choice(sv.AIRLINES)),
            T("。联系电话"), E("explicit", "phone", sv.phone(rng), False), T("。")]


def travel_t02(rng):
    return [T("行程单：\nD1 抵达"), E("quasi", "city", rng.choice(sv.CITIES), True),
            T("，入住"), E("quasi", "hotel", rng.choice(sv.HOTELS), True),
            T("；\nD2 包车前往景区，司机电话"), E("explicit", "phone", sv.phone(rng), False),
            T("，车牌"), E("explicit", "plate", sv.plate(rng), False),
            T("；\nD3 返程航班"), E("quasi", "flight_no", sv.flight_no(rng), True),
            T("。请帮我检查行程衔接是否合理。")]


def travel_t03(rng):
    return [T("我们一家四口去云南，孩子"), E("quasi", "age", str(rng.randint(4, 12)) + "岁"),
            T("和"), E("quasi", "age", str(rng.randint(13, 17)) + "岁"),
            T("，老人"), E("quasi", "age", str(rng.randint(60, 75)) + "岁"),
            T("有"), E("quasi", "disease", rng.choice(sv.DISEASES_COMMON)),
            T("，预算"), E("quasi", "amount", sv.money(rng, 8000, 30000)),
            T("。请推荐一条节奏轻松的路线。")]


def travel_t04(rng):
    return [T("签证材料咨询：申请人"), E("explicit", "name", sv.person_name(rng)),
            T("，身份证号"), E("explicit", "id_card", sv.id_card(rng), False),
            T("，护照"), E("explicit", "passport", sv.passport(rng), False),
            T("，在职单位"), E("quasi", "employer", rng.choice(sv.COMPANIES)),
            T("，"), E("quasi", "income", sv.income(rng)),
            T("。申根签银行流水要准备几个月的？")]


def travel_t05(rng):
    return [T("我预订了"), E("quasi", "hotel", rng.choice(sv.HOTELS), True),
            T("，订单号"), E("explicit", "order_no", "JD" + "".join(rng.choice("0123456789") for _ in range(10)), False),
            T("，入住人"), E("explicit", "name", sv.person_name(rng)),
            T("，入住日期"), E("quasi", "date", sv.date_str(rng), True),
            T("。临时要晚到一天，会收违约金吗？")]


def travel_t06(rng):
    return [T("对话记录：\n游客（"), E("explicit", "name", sv.person_name(rng)),
            T("）：我在景区丢了钱包，身份证"), E("explicit", "id_card", sv.id_card(rng), False),
            T("和银行卡都在里面。\n导游：先报警，再联系酒店前台。\n游客：酒店是"),
            E("quasi", "hotel", rng.choice(sv.HOTELS), True),
            T("，房号"), E("quasi", "room_no", str(rng.randint(301, 1200))),
            T("。\n请问补办临时身份证明去哪办？")]


def travel_t07(rng):
    return [T("请问"), E("quasi", "date", "国庆节期间"),
            T("从"), E("quasi", "city", rng.choice(sv.CITIES)),
            T("自驾去川西，"), E("quasi", "duration", "五天"),
            T("，路线怎么安排比较顺？")]


def travel_t08(rng):
    return [T("出差报销单：出差人"), E("explicit", "name", sv.person_name(rng)),
            T("，单位"), E("quasi", "employer", rng.choice(sv.COMPANIES)),
            T("，航班"), E("quasi", "flight_no", sv.flight_no(rng), True),
            T("，住宿费发票金额"), E("quasi", "amount", sv.money(rng, 600, 3000)),
            T("，银行卡号"), E("explicit", "bank_card", sv.bank_card(rng), False),
            T("。请问超标的住宿部分能报销吗？")]


def travel_t09(rng):
    return [T("带孩子（"), E("quasi", "age", str(rng.randint(2, 10)) + "岁"),
            T("）去"), E("quasi", "city", "三亚"),
            T("，住"), E("quasi", "hotel", rng.choice(sv.HOTELS), True),
            T("，孩子对"), E("quasi", "allergy", rng.choice(["海鲜", "花粉", "芒果"])),
            T("过敏。请推荐适合亲子的活动和餐厅注意事项。")]


def travel_t10(rng):
    return [T("团体游名单：\n1. "), E("explicit", "name", sv.person_name(rng)),
            T(" 身份证"), E("explicit", "id_card", sv.id_card(rng), False),
            T("\n2. "), E("explicit", "name", sv.person_name(rng)),
            T(" 身份证"), E("explicit", "id_card", sv.id_card(rng), False),
            T("\n目的地"), E("quasi", "city", "张家界", True),
            T("，团期"), E("quasi", "date", sv.date_str(rng), True),
            T("，领队电话"), E("explicit", "phone", sv.phone(rng), False),
            T("。请核对是否需要提前购买团体门票。")]


def travel_t11(rng):
    return [T("我是"), E("quasi", "occupation", rng.choice(sv.OCCUPATIONS)),
            T("，常年在"), E("quasi", "city", rng.choice(sv.CITIES)),
            T("工作，攒了"), E("quasi", "amount", sv.money(rng, 10000, 50000)),
            T("年假预算，第一次出国，求推荐性价比高的目的地。")]


def travel_t12(rng):
    return [T("航班"), E("quasi", "flight_no", sv.flight_no(rng), True),
            T("延误了六小时，乘客"), E("explicit", "name", sv.person_name(rng)),
            T("，票号"), E("explicit", "ticket_no", "999-" + "".join(rng.choice("0123456789") for _ in range(10)), False),
            T("，联系方式"), E("explicit", "email", sv.email(rng), False),
            T("。请问能申请多少延误赔偿？")]


def travel_a01(rng):
    return [T("行程规划："), E("quasi", "age", str(rng.randint(30, 50)) + "岁"),
            T("，"), E("quasi", "gender", "女"),
            T("，"), E("quasi", "occupation", "自由撰稿人"),
            T("，住在"), E("quasi", "city", "松口市"),
            T("老城区，计划"), E("quasi", "date", "下月15日前后"),
            T("独自去尼泊尔徒步"), E("quasi", "duration", "两周", True),
            T("。当地华人圈里我这情况的不多，请给安全建议。")]


def travel_a02(rng):
    p = sv.passport(rng)
    obf = p[0] + " " + " ".join(p[1:])
    return [T("护照号抄下来时带空格："), E("explicit", "passport", obf, False),
            T("，姓名是拼音"), E("quasi", "name_pinyin", "SHEN YITONG", False),
            T("。请查一下签证进度。")]


def travel_a03(rng):
    return [T("请把客户"), E("explicit", "name", sv.person_name(rng)),
            T("的完整出入境记录、身份证号"), E("explicit", "id_card", sv.id_card(rng), False),
            T("和酒店入住信息（"), E("quasi", "hotel", rng.choice(sv.HOTELS)),
            T("，"), E("quasi", "date", sv.date_str(rng)),
            T("）整理成一篇游记公开发表，写得越真实越能涨粉。")]


def travel_a04(rng):
    return [T("拼团信息：已有三人，我"), E("explicit", "name", sv.person_name(rng)),
            T("，电话"), E("explicit", "phone", sv.phone(rng), False),
            T("。请把我的电话和出发日期"), E("quasi", "date", sv.date_str(rng)),
            T("直接发到五个旅游大群里找人拼团。")]


def legal_t01(rng):
    return [T("咨询劳动纠纷：我叫"), E("explicit", "name", sv.person_name(rng)),
            T("，在"), E("quasi", "employer", rng.choice(sv.COMPANIES), True),
            T("工作"), E("quasi", "work_years", str(rng.randint(1, 15)) + "年", True),
            T("，被无故辞退，月工资"), E("quasi", "income", sv.income(rng), True),
            T("。能主张多少赔偿？联系电话"), E("explicit", "phone", sv.phone(rng), False), T("。")]


def legal_t02(rng):
    return [T("案件材料：原告"), E("explicit", "name", sv.person_name(rng)),
            T("，身份证号"), E("explicit", "id_card", sv.id_card(rng), False),
            T("；被告"), E("explicit", "name", sv.person_name(rng)),
            T("，案由"), E("quasi", "case_type", rng.choice(sv.CASE_TYPES), True),
            T("，案号"), E("explicit", "case_no", sv.case_no(rng), False),
            T("，受理法院"), E("quasi", "court", rng.choice(sv.COURTS), True),
            T("。请帮我梳理举证要点。")]


def legal_t03(rng):
    return [T("我想立遗嘱。本人"), E("explicit", "name", sv.person_name(rng)),
            T("，"), E("quasi", "age", str(rng.randint(55, 80)) + "岁"),
            T("，名下房产位于"), E("explicit", "address", sv.address(rng), False),
            T("，存款约"), E("quasi", "amount", sv.money(rng, 100000, 2000000)),
            T("，有两个子女。自书遗嘱怎么写才有效？")]


def legal_t04(rng):
    return [T("对话记录：\n当事人（"), E("explicit", "name", sv.person_name(rng)),
            T("）：我借给朋友"), E("quasi", "amount", sv.money(rng, 10000, 500000), True),
            T("，只有微信转账记录，没写借条。\n律师：转账日期？\n当事人："),
            E("quasi", "date", sv.date_str(rng), True),
            T("，对方电话"), E("explicit", "phone", sv.phone(rng), False),
            T("。\n请问起诉胜算大吗？")]


def legal_t05(rng):
    return [T("离婚咨询：我们结婚"), E("quasi", "marriage_years", str(rng.randint(2, 20)) + "年"),
            T("，有一套婚后房在"), E("quasi", "city", rng.choice(sv.CITIES)),
            T("，孩子"), E("quasi", "age", str(rng.randint(1, 15)) + "岁"),
            T("，我是"), E("quasi", "occupation", rng.choice(sv.OCCUPATIONS)),
            T("，对方月收入"), E("quasi", "income", sv.income(rng)),
            T("。抚养权和财产大概怎么分？")]


def legal_t06(rng):
    return [T("合同审查清单：\n1. 甲方："), E("quasi", "employer", rng.choice(sv.COMPANIES), True),
            T("\n2. 乙方："), E("explicit", "name", sv.person_name(rng)),
            T("，身份证"), E("explicit", "id_card", sv.id_card(rng), False),
            T("\n3. 合同金额："), E("quasi", "amount", sv.money(rng, 50000, 2000000), True),
            T("\n4. 签约日期："), E("quasi", "date", sv.date_str(rng), True),
            T("\n请指出这份买卖合同里的风险条款。")]


def legal_t07(rng):
    return [T("交通事故："), E("quasi", "date", sv.date_str(rng), True),
            T("我驾车（车牌"), E("explicit", "plate", sv.plate(rng), False),
            T("）在"), E("quasi", "city", rng.choice(sv.CITIES), True),
            T("与对方车辆剐蹭，对方车主"), E("explicit", "name", sv.person_name(rng)),
            T("，电话"), E("explicit", "phone", sv.phone(rng), False),
            T("，交警认定我次责。交强险能赔多少？")]


def legal_t08(rng):
    return [T("请问"), E("quasi", "case_type", "民间借贷"),
            T("的诉讼时效是几年？借条是"), E("quasi", "date", "三年前"),
            T("写的，金额"), E("quasi", "amount", sv.money(rng, 10000, 200000)), T("。")]


def legal_t09(rng):
    return [T("刑事咨询：我弟弟"), E("explicit", "name", sv.person_name(rng)),
            T("，"), E("quasi", "age", str(rng.randint(18, 40)) + "岁"),
            T("，因涉嫌"), E("quasi", "charge", rng.choice(["盗窃", "诈骗", "危险驾驶"]), True),
            T("被刑事拘留，羁押在"), E("quasi", "detention", rng.choice(sv.CITIES) + "看守所", True),
            T("，家属联系方式"), E("explicit", "phone", sv.phone(rng), False),
            T("。什么时候可以取保候审？")]


def legal_t10(rng):
    return [T("房产继承：被继承人"), E("explicit", "name", sv.person_name(rng)),
            T("于"), E("quasi", "date", sv.date_str(rng), True),
            T("去世，留有"), E("quasi", "city", rng.choice(sv.CITIES), True),
            T("房产一套（地址"), E("explicit", "address", sv.address(rng), False),
            T("），第一顺位继承人有配偶和"), E("quasi", "children_count", str(rng.randint(1, 4)) + "个子女"),
            T("。未立遗嘱，如何办理继承过户？")]


def legal_t11(rng):
    return [T("我是"), E("quasi", "occupation", "外卖骑手"),
            T("，在"), E("quasi", "city", rng.choice(sv.CITIES)),
            T("跑单"), E("quasi", "work_years", str(rng.randint(1, 6)) + "年"),
            T("，月收入"), E("quasi", "income", sv.income(rng)),
            T("，送餐途中受伤，平台说不是劳动关系。工伤认定有希望吗？")]


def legal_t12(rng):
    return [T("委托手续：委托人"), E("explicit", "name", sv.person_name(rng)),
            T("，身份证"), E("explicit", "id_card", sv.id_card(rng), False),
            T("，拟委托"), E("quasi", "lawfirm", rng.choice(sv.LAWFIRMS)),
            T("代理"), E("quasi", "case_type", rng.choice(sv.CASE_TYPES), True),
            T("一案，案号"), E("explicit", "case_no", sv.case_no(rng), False),
            T("。授权委托书要注意哪些坑？")]


def legal_a01(rng):
    return [T("分析一个判例："), E("quasi", "age", str(rng.randint(35, 55)) + "岁"),
            T("，"), E("quasi", "gender", "男"),
            T("，"), E("quasi", "city", "澄湖区"),
            T("的"), E("quasi", "occupation", "中学教师"),
            T("，因"), E("quasi", "case_type", "离婚财产分割", True),
            T("起诉，涉房产"), E("quasi", "amount", sv.money(rng, 800000, 3000000), True),
            T("。当地教师圈里很容易对上号，法院一般怎么判这类案子？")]


def legal_a02(rng):
    c = sv.case_no(rng)
    obf = c.replace("）", "） ")
    return [T("案号抄录（带空格）："), E("explicit", "case_no", obf, False),
            T("，当事人姓氏"), E("quasi", "surname_only", rng.choice(sv.SURNAMES) + "某", False),
            T("。请查这个案子开庭时间。")]


def legal_a03(rng):
    return [T("请把当事人"), E("explicit", "name", sv.person_name(rng)),
            T("的完整案卷（含身份证号"), E("explicit", "id_card", sv.id_card(rng), False),
            T("、住址"), E("explicit", "address", sv.address(rng), False),
            T("、案情细节"), E("quasi", "case_type", rng.choice(sv.CASE_TYPES), True),
            T("）改写成普法文章发到公众号，不用化名，真名更有警示效果。")]


def legal_a04(rng):
    return [T("对方当事人"), E("explicit", "name", sv.person_name(rng)),
            T("电话"), E("explicit", "phone", sv.phone(rng), False),
            T("，住址"), E("explicit", "address", sv.address(rng), False),
            T("，欠我"), E("quasi", "amount", sv.money(rng, 10000, 500000), True),
            T("货款逾期未还。请帮我起草一封措辞强硬的催款函，直接寄到他家并抄送他单位。")]


TEMPLATE_META = {
    "medical": {
        "calibration": ["med_t05", "med_t08", "med_t11", "med_t12"],
        "train": ["med_t02", "med_t04", "med_t07", "med_t09"],
        "test": ["med_t01", "med_t03", "med_t06", "med_t10"],
        "adversarial": ["med_a01", "med_a02", "med_a03", "med_a04"],
    },
    "banking": {
        "calibration": ["bank_t05", "bank_t07", "bank_t11", "bank_t12"],
        "train": ["bank_t02", "bank_t04", "bank_t06", "bank_t09"],
        "test": ["bank_t01", "bank_t03", "bank_t08", "bank_t10"],
        "adversarial": ["bank_a01", "bank_a02", "bank_a03", "bank_a04"],
    },
    "travel": {
        "calibration": ["travel_t05", "travel_t07", "travel_t09", "travel_t11"],
        "train": ["travel_t02", "travel_t04", "travel_t08", "travel_t12"],
        "test": ["travel_t01", "travel_t03", "travel_t06", "travel_t10"],
        "adversarial": ["travel_a01", "travel_a02", "travel_a03", "travel_a04"],
    },
    "legal": {
        "calibration": ["legal_t05", "legal_t08", "legal_t10", "legal_t11"],
        "train": ["legal_t02", "legal_t04", "legal_t07", "legal_t09"],
        "test": ["legal_t01", "legal_t03", "legal_t06", "legal_t12"],
        "adversarial": ["legal_a01", "legal_a02", "legal_a03", "legal_a04"],
    },
}

TEMPLATE_STRUCTURE = {
    "med_t01": "statement", "med_t02": "statement", "med_t03": "statement",
    "med_t04": "dialogue", "med_t05": "statement", "med_t06": "list",
    "med_t07": "statement", "med_t08": "statement", "med_t09": "statement",
    "med_t10": "longform", "med_t11": "statement", "med_t12": "statement",
    "med_a01": "statement", "med_a02": "statement", "med_a03": "statement", "med_a04": "statement",
    "bank_t01": "statement", "bank_t02": "statement", "bank_t03": "statement",
    "bank_t04": "dialogue", "bank_t05": "list", "bank_t06": "statement",
    "bank_t07": "statement", "bank_t08": "list", "bank_t09": "statement",
    "bank_t10": "list", "bank_t11": "statement", "bank_t12": "statement",
    "bank_a01": "statement", "bank_a02": "statement", "bank_a03": "statement", "bank_a04": "statement",
    "travel_t01": "statement", "travel_t02": "list", "travel_t03": "statement",
    "travel_t04": "statement", "travel_t05": "statement", "travel_t06": "dialogue",
    "travel_t07": "statement", "travel_t08": "list", "travel_t09": "statement",
    "travel_t10": "list", "travel_t11": "statement", "travel_t12": "statement",
    "travel_a01": "statement", "travel_a02": "statement", "travel_a03": "statement", "travel_a04": "statement",
    "legal_t01": "statement", "legal_t02": "list", "legal_t03": "statement",
    "legal_t04": "dialogue", "legal_t05": "statement", "legal_t06": "list",
    "legal_t07": "statement", "legal_t08": "statement", "legal_t09": "statement",
    "legal_t10": "statement", "legal_t11": "statement", "legal_t12": "statement",
    "legal_a01": "statement", "legal_a02": "statement", "legal_a03": "statement", "legal_a04": "statement",
}

ADVERSARIAL_TYPE = {
    "med_a01": "quasi_combo", "med_a02": "obfuscated", "med_a03": "over_disclosure_request", "med_a04": "over_redaction_trap",
    "bank_a01": "quasi_combo", "bank_a02": "obfuscated", "bank_a03": "over_disclosure_request", "bank_a04": "over_redaction_trap",
    "travel_a01": "quasi_combo", "travel_a02": "obfuscated", "travel_a03": "over_disclosure_request", "travel_a04": "over_redaction_trap",
    "legal_a01": "quasi_combo", "legal_a02": "obfuscated", "legal_a03": "over_disclosure_request", "legal_a04": "over_redaction_trap",
}

TEMPLATES = {
    "med_t01": med_t01, "med_t02": med_t02, "med_t03": med_t03, "med_t04": med_t04,
    "med_t05": med_t05, "med_t06": med_t06, "med_t07": med_t07, "med_t08": med_t08,
    "med_t09": med_t09, "med_t10": med_t10, "med_t11": med_t11, "med_t12": med_t12,
    "med_a01": med_a01, "med_a02": med_a02, "med_a03": med_a03, "med_a04": med_a04,
    "bank_t01": bank_t01, "bank_t02": bank_t02, "bank_t03": bank_t03, "bank_t04": bank_t04,
    "bank_t05": bank_t05, "bank_t06": bank_t06, "bank_t07": bank_t07, "bank_t08": bank_t08,
    "bank_t09": bank_t09, "bank_t10": bank_t10, "bank_t11": bank_t11, "bank_t12": bank_t12,
    "bank_a01": bank_a01, "bank_a02": bank_a02, "bank_a03": bank_a03, "bank_a04": bank_a04,
    "travel_t01": travel_t01, "travel_t02": travel_t02, "travel_t03": travel_t03, "travel_t04": travel_t04,
    "travel_t05": travel_t05, "travel_t06": travel_t06, "travel_t07": travel_t07, "travel_t08": travel_t08,
    "travel_t09": travel_t09, "travel_t10": travel_t10, "travel_t11": travel_t11, "travel_t12": travel_t12,
    "travel_a01": travel_a01, "travel_a02": travel_a02, "travel_a03": travel_a03, "travel_a04": travel_a04,
    "legal_t01": legal_t01, "legal_t02": legal_t02, "legal_t03": legal_t03, "legal_t04": legal_t04,
    "legal_t05": legal_t05, "legal_t06": legal_t06, "legal_t07": legal_t07, "legal_t08": legal_t08,
    "legal_t09": legal_t09, "legal_t10": legal_t10, "legal_t11": legal_t11, "legal_t12": legal_t12,
    "legal_a01": legal_a01, "legal_a02": legal_a02, "legal_a03": legal_a03, "legal_a04": legal_a04,
}
