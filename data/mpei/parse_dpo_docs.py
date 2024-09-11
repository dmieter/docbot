import os
from docx import Document
from docx_parser import DocumentParser
import re

path = 'data/pdf/mpei/dpo/'





def retrieve_dpo_name(doc : DocumentParser):
    for _type, item in doc.parse():
        if _type == 'table':
            if len(item['data']) > 0:
                row = item['data'][0]
                if len(row) > 1 and 'Наименование программы'.lower() in row[0].lower():
                    #print(item)
                    #print(row[-1])
                    return row[-1]

    return None            


prof_standard_names = {}
prof_standard_dpos = {}
dpo_fgos = {}
dpo_subjects = {}

def retrieve_prof_standards_plain(document : Document):
    for paragraph in document.paragraphs:
        m = re.search('([0-9][0-9]\.[0-9][0-9][0-9]).*«(.*)»', paragraph.text)
        if m:
            code = m.group(1)
            name = m.group(2)



def retrieve_dpo_subjects(doc : DocumentParser, dpo_name):
    global dpo_subjects
    subjects_set = set()

    for _type, item in doc.parse():
        if _type == 'table':
            rows = item['data']
            if len(rows) > 0:
                row = rows[0]
                if len(row) > 2 and 'Наименование дисциплин'.lower() in row[1].lower():
                    for rownum in range (1, len(rows)):
                        row = rows[rownum]
                        if len(row) > 1 and not 'Наименование дисциплин'.lower() in row[1].lower():
                            subjects_set.add(row[1])

    dpo_subjects[dpo_name] = subjects_set  


def retrieve_fgos_standard(doc : DocumentParser, dpo_name):
    global dpo_fgos

    for _type, item in doc.parse():
        if _type == 'paragraph':
            m = re.search('([0-9][0-9]\.[0-9][0-9]\.[0-9][0-9]) +([^,]*)[,]', item['text'])
            if m:
                code = m.group(1)
                name = m.group(2)
                dpo_fgos[dpo_name] = '{} - {}'.format(code, name)
                return


            if 'Форма реализации'.lower() in item['text'].lower():
                return  # do not parse all document

def retrieve_prof_standards(doc : DocumentParser, dpo_name):
    global prof_standard_names
    global prof_standard_dpos

    for _type, item in doc.parse():
        if _type == 'paragraph':
            m = re.search('([0-9][0-9]\.[0-9][0-9][0-9]).*«(.*)»', item['text'])
            if m:
                code = m.group(1)
                name = m.group(2)
                prof_standard_names[code] = name

                if code in prof_standard_dpos.keys():
                    prof_standard_dpos[code].add(dpo_name)
                else:
                    dpos_set = set()
                    dpos_set.add(dpo_name)
                    prof_standard_dpos[code] = dpos_set


            if 'Форма реализации'.lower() in item['text'].lower():
                return  # do not parse all document



document = Document(path + 'ТЭС/Характеристика_ТЭС_1686_ПП_В_О_1041ч_13_03_01.docx')
#for paragraph in document:
#     print(paragraph.text)
retrieve_prof_standards_plain(document)




#for folder in os.listdir(path):
#    folder_path = os.path.join(path, folder)
#    if os.path.isdir(folder_path):

folder_path = os.path.join(path, 'characteristics')
for file in os.listdir(folder_path):
    if file.startswith("Характеристика") and file.endswith(".docx"):
        print(os.path.join(folder_path, file))

        doc = DocumentParser(os.path.join(folder_path, file))
        dpo_name = retrieve_dpo_name(doc)
        print(dpo_name)
        retrieve_dpo_subjects(doc, dpo_name)
        retrieve_prof_standards(doc, dpo_name)
        retrieve_fgos_standard(doc, dpo_name)
    


#doc = DocumentParser(path + 'ТЭС/Характеристика_ТЭС_1686_ПП_В_О_1041ч_13_03_01.docx')
#for _type, item in doc.parse():
#    print('===================')
#    print(_type, item)

#dpo_name = retrieve_dpo_name(doc)
#retrieve_dpo_subjects(doc, dpo_name)
#retrieve_prof_standards(doc, dpo_name)


print(dpo_fgos)
print(prof_standard_names)
print(prof_standard_dpos)
print(dpo_subjects)

def create_bd_file():
    delimeter = """
    ==========================================
    """
    prof_standart_keywords = """KEYWORDS: какие программы повышения квалификации 
    профессиональной переподготовки ДПО соответствуют реализуют профстандарт профессиональный стандарт {} {}"""
    prof_standsart_data = """Профстандарт {} {} реализуется следующими программами повышения квалификации: {}"""
    subjects_keywords = """KEYWORDS: какие предметы дисциплины входят в программу повышения квалификации ДПО {}, что изучается?"""
    subjects_data = """Следующие дисциплины изучаются в рамках программы ДПО {}: {}"""

    bd_data = ""
    for code, dpos in prof_standard_dpos.items():
        bd_data += prof_standart_keywords.format(code, prof_standard_names[code]) + delimeter
        bd_data += prof_standsart_data.format(code, prof_standard_names[code], ', '.join(dpos)) + delimeter

    for dpo, subjects in dpo_subjects.items():
        bd_data += subjects_keywords.format(dpo) + delimeter
        bd_data += subjects_data.format(dpo, ', '.join(subjects)) + delimeter


    with open(path + '/common_dpo_bd.txt', 'w') as f:
        f.write(bd_data)

    print(bd_data)    


create_bd_file()