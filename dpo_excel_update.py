import pandas as pd
import index_dpo_file as idpo

path = 'upload/dpo/'

class DPO:
    def __init__(self, name, dpo_type="", description=""):
        self.name = name
        self.dpo_type = dpo_type
        self.form = ""
        self.implementation = ""
        self.diploma = ""
        self.requirements = ""
        self.cost = None
        self.terms = ""
        self.contact_person = ""
        self.phone_number = ""
        self.complexity_hours = None
        self.description = description
        self.fgos = set()
        self.profstandards = set()
        self.subjects = []

    def get_name(self):
        name_str = self.name
        if self.complexity_hours:
            name_str += ' ({} часов)'.format(self.complexity_hours) 

        return name_str   

prof_standard_names = {}
prof_standard_dpos = {}
dpos_by_name = {}
faq=[]

def get_prof_standard_name(code):
    if code in prof_standard_names:
        return "{} - {}".format(code, prof_standard_names[code])
    else:
        return code

def upload_dpo_excel(path):

    prof_standard_dpos.clear()
    dpos_by_name.clear()
    dpos_by_name.clear()
    faq.clear()

    # 1. Fill in the dictionary with names of profstandards
    df = pd.read_excel(path, sheet_name='Профстандарты', converters={'Код профстаднарта':str})
    for index, row in df.iterrows():
        prof_standard_names[str(row['Код профстаднарта']).strip()] = row['Название']


    # 2. Load information about particular DPOs
    df = pd.read_excel(path, sheet_name='Программы')
    for index, row in df.iterrows():
        dpo = DPO(row['Название программы'])
        dpo.dpo_type = row['Тип программы']
        dpo.complexity_hours = int(row['Количество часов'])
        dpo.form = row['Форма обучения']
        dpo.implementation = row['Форма реализации']
        dpo.diploma = row['Выдаваемый документ']
        dpo.cost = int(str(row['Стоимость, руб.']).replace(' ', '').replace(',', ''))
        dpo.terms = row['Сроки обучения']
        dpo.contact_person = row['Контактное лицо']
        dpo.phone_number = row['Телефон']

        profstandards_str = str(row['Профстандарт'])
        if profstandards_str:
            for ps_code in profstandards_str.splitlines():
                ps_code = ps_code.strip()
                if ps_code in prof_standard_names:
                    dpo.profstandards.add(get_prof_standard_name(ps_code))
                else:
                    dpo.profstandards.add(ps_code)

        subjects_str = str(row['Содержание'])
        if subjects_str:
            dpo.subjects.extend(subjects_str.splitlines()) 

        dpos_by_name[dpo.name] = dpo



        # 3. Collect data about profstandards groupings
        for ps_code in profstandards_str.splitlines():
            if ps_code in prof_standard_dpos.keys():
                prof_standard_dpos[ps_code].add(dpo.name)
            else:
                dpos_set = set()
                dpos_set.add(dpo.name)
                prof_standard_dpos[ps_code] = dpos_set

    #4. Load faq sheet
    df = pd.read_excel(path, sheet_name='FAQ')
    for index, row in df.iterrows():
        faq.append((row['Вопрос'], row['Ответ']))

def create_bd_file_standards():
    delimeter = """
==========================================
"""
    prof_standart_keywords = """KEYWORDS: какие программы ДПО соответствуют реализуют профстандарт профессиональный стандарт {}"""
    prof_standsart_data = """Профстандарт {} реализуется следующими программами ДПО: 
{}"""
    dpo_fgos_keywords = """KEYWORDS: {} фгос образовательный стандарт"""
    dpo_fgos_data = """Программа {} {} реализует следующие фгос образовательные стандарты: {}."""
    dpo_profs_keywords = """KEYWORDS: {} профстандарт профессиональный стандарт"""
    dpo_profs_data = """Программа {} {} реализует следующие профессиональные стандарты: 
{}."""


    bd_data = ""
    for code, dpos in prof_standard_dpos.items():
        code_name = get_prof_standard_name(code)
        bd_data += prof_standart_keywords.format(code_name) + delimeter
        bd_data += prof_standsart_data.format(code_name, '\n'.join(dpos)) + delimeter

    #for dpo_name, dpo in dpos_by_name.items():
    #    bd_data += dpo_fgos_keywords.format(dpo.name) + delimeter
    #    bd_data += dpo_fgos_data.format(dpo.dpo_type, dpo.name, '\n'.join(dpo.fgos)) + delimeter

    for dpo_name, dpo in dpos_by_name.items():
        bd_data += dpo_profs_keywords.format(dpo.name) + delimeter
        bd_data += dpo_profs_data.format(dpo.dpo_type, dpo.name, '\n'.join(dpo.profstandards)) + delimeter

    with open(path + '/dpo_standards_excel.txt', 'w') as f:
        f.write(bd_data)


def create_bd_file_programms():
    delimeter = """
==========================================
"""
    subjects_keywords = """KEYWORDS: какие предметы дисциплины входят в программу {}, что изучается?"""
    subjects_data = """Следующие предметы изучаются в рамках программы {} {}: {}"""
    single_dpo_keywords = """KEYWORDS: {} обучение детали"""
    single_dpo_data = """Программа {} "{}". 
Форма обучения: {}, {}.
Выдается документ: {}. 
Стоимость обучения: {} руб.
Сроки обучения: {}.
Реализует ФГОС стандарт по направлению подготовки {}.
Реализует профстандарты: {}.
Контактное лицо: {}, тел. {}"""

    bd_data = ""
    for dpo_name, dpo in dpos_by_name.items():
        bd_data += subjects_keywords.format(dpo.name) + delimeter
        bd_data += subjects_data.format(dpo.dpo_type, dpo.get_name(), '\n'.join(dpo.subjects)) + delimeter

    for dpo_name, dpo in dpos_by_name.items():
        bd_data += single_dpo_keywords.format(dpo.name) + delimeter
        bd_data += single_dpo_data.format(dpo.dpo_type, dpo.get_name(), dpo.form, dpo.implementation, dpo.diploma, dpo.cost, dpo.terms,  ', '.join(dpo.fgos), ', '.join(dpo.profstandards), dpo.contact_person, dpo.phone_number) + delimeter
        
    with open(path + '/dpo_programms_excel.txt', 'w') as f:
        f.write(bd_data) 


def create_bd_file_stats():
    delimeter = """
==========================================
"""
    complexity_top_keywords = """KEYWORDS: самые большие объемные долгие программы обучения ДПО"""
    complexity_top_data = """10 самых больших программ ДПО включают в себя: \n{}"""

    complexity_bottom_keywords = """KEYWORDS: самые короткие маленькие быстрые объемные долгие программы обучения ДПО"""
    complexity_bottom_data = """10 самых коротких программ ДПО включают в себя: \n{}"""

    cost_bottom_keywords = """KEYWORDS: самые дешевые недорогие бюджетные программы обучения ДПО"""
    cost_bottom_data = """10 самых недорогих программ ДПО включают в себя: \n{}"""
    
    bd_data = ""
   
    complexity_top_dpos = sorted(dpos_by_name.values(), key=lambda x: int(x.complexity_hours), reverse=True)[:10]
    complexity_top_dpos_str = '\n'.join(["{} {}".format(dpo.get_name(), dpo.form) for dpo in complexity_top_dpos])
    bd_data += complexity_top_keywords + delimeter
    bd_data += complexity_top_data.format(complexity_top_dpos_str) + delimeter

    complexity_bottom_dpos = sorted(dpos_by_name.values(), key=lambda x: int(x.complexity_hours), reverse=False)[:10]
    complexity_bottom_dpos_str = '\n'.join(["{} {}".format(dpo.get_name(), dpo.form) for dpo in complexity_bottom_dpos])
    bd_data += complexity_bottom_keywords + delimeter
    bd_data += complexity_bottom_data.format(complexity_bottom_dpos_str) + delimeter

    cost_bottom_dpos = sorted(dpos_by_name.values(), key=lambda x: int(x.cost), reverse=False)[:10]
    cost_bottom_dpos_str = '\n'.join(["{} руб. - {}".format(dpo.cost, dpo.get_name()) for dpo in cost_bottom_dpos])
    bd_data += cost_bottom_keywords + delimeter
    bd_data += cost_bottom_data.format(cost_bottom_dpos_str) + delimeter
 
    with open(path + '/dpo_stats_excel.txt', 'w') as f:
        f.write(bd_data)

def create_bd_file_faq():
    delimeter = """
==========================================
"""
    bd_data = ""

    for (question, answer) in faq:
        bd_data += question + delimeter
        bd_data += question + '?\n\n' + answer + delimeter

    with open(path + '/dpo_faq_excel.txt', 'w') as f:
        f.write(bd_data)


def process_file(excel_file_path):
    upload_dpo_excel(excel_file_path)
    #upload_dpo_excel(path + 'dpo.xlsx')

    create_bd_file_programms()
    create_bd_file_standards()
    create_bd_file_stats()
    create_bd_file_faq()

    idpo.index_dpo_file(path + "/dpo_programms_excel.txt", "dpo_programms", True)
    idpo.index_dpo_file(path + "/dpo_standards_excel.txt", "dpo_standards", True)
    idpo.index_dpo_file(path + "/dpo_stats_excel.txt", "dpo_stats", True)
    idpo.index_dpo_file(path + "/dpo_faq_excel.txt", "dpo_faq", True)