import os

from lxml import etree

attribute_type = 0
attribute_value = 1
pc_pcf = '/config/web/pcf/line'


class ProcessPCF:

    def process_pcf(self):
        for x in os.listdir(self.pc_policy_dir):
            print('processing : ' + x)
            self.process_root(x)

    def process_root(self, in_pcf_file):
        tree = etree.parse(self.pc_policy_dir + '/' + in_pcf_file)
        root = tree.getroot()
        for element in root.iter():
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

    def process_tag(self, element):
        available_str = None
        editable_str = None
        visible_str = None
        value_str = None
        required_str = None

        for attribute in element.items():
            if attribute[attribute_type] == 'available':
                available_str = attribute[attribute_value]
            if attribute[attribute_type] == 'editable':
                editable_str = attribute[attribute_value]
            if attribute[attribute_type] == 'visible':
                visible_str = attribute[attribute_value]
            if attribute[attribute_type] == 'value':
                value_str = attribute[attribute_value]
            if attribute[attribute_type] == 'required':
                required_str = attribute[attribute_value]

        if available_str is None or 'SchemeUtil_PMP' not in available_str:
            self.process_available(element, available_str, self.get_field(value_str))

        if editable_str is None or 'SchemeUtil_PMP' not in editable_str:
            self.process_editable(element, editable_str, self.get_field(value_str))

        if visible_str is None or 'SchemeUtil_PMP' not in visible_str:
            self.process_visible(element, visible_str, self.get_field(value_str))

        if required_str is None or 'SchemeUtil_PMP' not in required_str:
            self.process_required(element, required_str, self.get_field(value_str))

    def get_field(self, value_str):
        field_str_array = value_str.split('.')
        field_str = ''
        for field in range(len(field_str_array)):
            if field < len(field_str_array) - 1:
                if field == 0:
                    field_str = field_str + field_str_array[field]
                else:
                    field_str = field_str + '.' + field_str_array[field]
            else:
                field_str = field_str + '#' + field_str_array[field]
        return [field_str_array[0], field_str]

    def process_available(self, element, available_str, value_str):
        if value_str[1].startswith('#'):
            return
        default_str = 'true'
        if available_str is not None:
            default_str = '(' + available_str + ')'

        available_str = 'gw.pmp.scheme.util.SchemeUtil_PMP.isAvailable(' \
                        + value_str[1] + '.PropertyInfo, ' \
                        + default_str + ', ' \
                        + value_str[0] \
                        + ')'

        element.set('available', available_str)

    def process_editable(self, element, editable_str, value_str):
        if value_str[1].startswith('#'):
            return
        default_str = 'true'
        if editable_str is not None:
            default_str = '(' + editable_str + ')'

        editable_str = 'gw.pmp.scheme.util.SchemeUtil_PMP.isEditable(' \
                       + value_str[1] + '.PropertyInfo, ' \
                       + default_str + ', ' \
                       + value_str[0] \
                       + ')'

        element.set('editable', editable_str)

    def process_visible(self, element, visible_str, value_str):
        if value_str[1].startswith('#'):
            return
        default_str = 'true'
        if visible_str is not None:
            default_str = '(' + visible_str + ')'

        visible_str = 'gw.pmp.scheme.util.SchemeUtil_PMP.isVisible(' \
                      + value_str[1] + '.PropertyInfo, ' \
                      + default_str + ', ' \
                      + value_str[0] \
                      + ')'

        element.set('visible', visible_str)

    def process_required(self, element, required_str, value_str):
        if value_str[1].startswith('#'):
            return
        default_str = 'false'
        if required_str is not None:
            default_str = '(' + required_str + ')'

        required_str = 'gw.pmp.scheme.util.SchemeUtil_PMP.isVisible(' \
                       + value_str[1] + '.PropertyInfo, ' \
                       + default_str + ', ' \
                       + value_str[0] \
                       + ')'

        element.set('required', required_str)

    def __init__(self, in_pc_path, in_pc_product_abbreviation):
        self.pc_path = in_pc_path
        self.pc_product_abbreviation = in_pc_product_abbreviation
        self.pc_policy_dir = self.pc_path + pc_pcf + '/' + self.pc_product_abbreviation + '/policy'
        self.pc_policy_file_dir = self.pc_path + pc_pcf + '/' + self.pc_product_abbreviation + '/policyfile'
        self.pc_job_dir = self.pc_path + pc_pcf + '/' + self.pc_product_abbreviation + '/job'
