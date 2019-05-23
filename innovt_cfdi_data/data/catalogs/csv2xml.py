# -*- coding: utf-8 -*-
import csv


model = 'res.bank'
with open('res.bank.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    i = 0
    data =""
    for row in csv_reader:
        if i == 0:
            i = 1
            continue
        code = row[1]
        id = model.replace('.', '_') + '_' + code
        name = str(row[2]).strip().decode('utf-8')
        data += """
        <record id="${id}" model="${model}">
            <field name="name">${name}</field>
            <field name="code">${code}</field>
        </record>
        """.replace('${id}', id).replace('${model}', model).replace('${name}', name).replace('${code}', code)
    template = """
        <?xml version="1.0" encoding="UTF-8" ?>
        <odoo>
        <data noupdate="1">
            ${data}
            </data>
        </odoo>
    """.replace('${data}', data)
    with open(model.replace('.','_') + '_data.xml', 'a+') as newfile:
        newfile.write(template.encode('utf-8'))
        newfile.close()