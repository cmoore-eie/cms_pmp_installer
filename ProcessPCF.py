import os

from lxml import etree

attribute_type = 0
attribute_value = 1
pc_pcf = '/config/web/pcf/line'
apd_class = 'gw.web.rules.APDRulesHelper'
pmp_class = 'gw.pmp.apd.web.rules.APDRulesHelper_PMP'


class ProcessPCF:

    def process_pcf(self):
        for x in os.listdir(self.pc_policy_dir):
            print('processing : ' + x)
            self.process_root(x)

    def process_root(self, in_pcf_file):
        tree = etree.parse(self.pc_policy_dir + '/' + in_pcf_file)
        root = tree.getroot()
        for element in root.iter():
            if element.tag == 'Variable':
                self.process_apd_variable(element)
            if element.tag == 'TextInput':
                self.process_tag(element)
            if element.tag == 'RangeInput':
                self.process_tag(element)
            if element.tag == 'PickerInput':
                self.process_tag(element)
            if element.tag == 'TextAreaInput':
                self.process_tag(element)
            if element.tag == 'TypeKeyInput':
                self.process_tag(element)
            if element.tag == 'BooleanRadioInput':
                self.process_tag(element)
            if element.tag == 'DateInput':
                self.process_tag(element)
            if element.tag == 'MonetaryAmountInput':
                self.process_tag(element)

        content = etree.tostring(root, pretty_print=True)
        file = open(self.pc_policy_dir + "/" + in_pcf_file, 'w')
        file.write(content.decode('utf-8'))
        file.close()

    def process_apd_variable(self, element):
        required_str = None
        attributes = element.attrib
        if 'name' in attributes:
            _name = attributes.get('name')
            if _name == 'isEditable':
                self.update_apd_tag(attributes)
            if _name == 'isVisible':
                self.update_apd_tag(attributes)
            if _name == 'isRequired':
                self.update_apd_tag(attributes)
            if _name == 'isAvailable':
                self.update_apd_tag(attributes)

    def process_tag(self, element):
        attributes = element.attrib
        if attributes.get('required') is None or (not attributes.get('required').startswith(pmp_class) and not attributes.get('required') == 'isRequired'):
            self.process_required(attributes, attributes.get('required'), self.get_field(attributes))
        if attributes.get('available') is None or (not attributes.get('available').startswith(pmp_class) and not attributes.get('available') == 'isAvailable'):
            self.process_available(attributes, attributes.get('available'), self.get_field(attributes))

    def update_apd_tag(self, attributes):
        if 'initialValue' in attributes:
            _initialValue = attributes.get('initialValue').replace(apd_class, pmp_class)
            attributes['initialValue'] = _initialValue
        return self

    def get_field(self, attributes):
        field_str_array = attributes.get('value').split('.')
        field_str = ''
        for field in range(len(field_str_array)):
            if field < len(field_str_array) - 1:
                if field == 0:
                    field_str = field_str + field_str_array[field]
                else:
                    field_str = field_str + '.' + field_str_array[field]
            else:
                field_str = field_str + '#' + field_str_array[field]
        if self:
            return [field_str_array[0], field_str]

    def process_available(self, attributes, available_str, value_str):
        if value_str[1].startswith('#'):
            return
        default_str = 'true'
        if available_str is not None:
            default_str = '(' + available_str + ')'

        available_str = pmp_class + '.isAvailable(' \
                        + value_str[0] + '.PolicyLine, ' \
                        + value_str[0] + ', ' \
                        + value_str[1] + '.PropertyInfo' \
                        + ')'

        attributes['available'] = available_str
        return self

    def process_required(self, attributes, required_str, value_str):
        if value_str[1].startswith('#'):
            return
        default_str = 'false'
        if required_str is not None:
            default_str = '(' + required_str + ')'

        required_str = pmp_class + '.isRequired(' \
                       + value_str[0] + '.PolicyLine, ' \
                       + value_str[0] + ', ' \
                       + value_str[1] + '.PropertyInfo, ' \
                       + default_str \
                       + ')'

        attributes['required'] = required_str
        return self

    def __init__(self, in_pc_path, in_pc_product_abbreviation):
        self.pc_path = in_pc_path
        self.pc_product_abbreviation = in_pc_product_abbreviation
        self.pc_policy_dir = self.pc_path + pc_pcf + '/' + self.pc_product_abbreviation + '/policy'
        self.pc_policy_file_dir = self.pc_path + pc_pcf + '/' + self.pc_product_abbreviation + '/policyfile'
        self.pc_job_dir = self.pc_path + pc_pcf + '/' + self.pc_product_abbreviation + '/job'