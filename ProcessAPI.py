import os

from lxml import etree

from APITemplates import uses_values_list, load_values_list

attribute_type = 0
attribute_value = 1
pc_api = '/gsrc/gw/rest/ext/pc/policyperiod'
name_change = dict()

def process_file(in_file_name: str) -> bool:
    """ There are some instances where the file should no be processed at the moment, by not processing these files
        defined in the no_process variable there may be some small manual changes needed to get the new PCF files to
        be used"""
    if in_file_name.find('ExtResource') >= 0:
        return True
    return False


class ProcessAPI:

    def process_api(self):
        for x in os.listdir(self.pc_policy_api_dir):
            print(f'processing : {x}')
            if process_file(x):
                print('processing : ' + x)
                self.process(x)

    def process(self, in_file_name):
        file_path = self.pc_policy_api_dir + '/' + in_file_name
        file_read = open(file_path, 'r')
        file_contents = file_read.readlines()
        # coverages
        if in_file_name.find('CoveragesExtResource') >= 0:
            self.process_uses(file_contents, file_path)
            self.process_load_values(file_contents, file_path)
        # coverage
        if in_file_name.find('CoverageExtResource') >= 0:
            pass
        file_write = open(file_path, "w")
        file_write.writelines(file_contents)
        file_write.close()

    def process_uses(self, file_contents, file_path):
        insert = 0
        for line in file_contents:
            if line.find(uses_values_list()[0]) >= 0:
                return
        for line in file_contents:
            if line.find('package ') == -1:
                insert += 1
                break
        for uses_item in uses_values_list():
            insert += 1
            file_contents.insert(insert, uses_item)

    def process_load_values(self, file_contents, file_path):
        for line in file_contents:
            if line.find(load_values_list()[1]) >= 0:
                return
        file_contents[-1] = ''
        for line in load_values_list():
            file_contents.append(line)
        file_contents.append('}')

    def __init__(self, in_config_json):
        self.config_json = in_config_json
        self.root = None
        self.pc_path = in_config_json['pc_path']
        self.pc_product_abbreviation = in_config_json['pc_product_abbreviation']
        self.pc_policy_api_dir = self.pc_path + pc_api + '/' + self.pc_product_abbreviation + '/' + 'v1' + '/coverage'
