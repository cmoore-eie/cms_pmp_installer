import os

from lxml import etree

attribute_type = 0
attribute_value = 1
pc_pcf = '/config/web/pcf/line'
apd_class = 'gw.web.rules.APDRulesHelper'
pmp_class = 'gw.pmp.apd.web.rules.APDRulesHelper_PMP'
file_ends = ['PanelSet.pcf', 'Popup.pcf', 'ListDetail.pcf', 'Screen.pcf']
no_process = ['MenuItemSet', 'WizardStepSet']
name_change = dict()


class ProcessPCF:

    def process_pcf(self):
        for x in os.listdir(self.pc_policy_dir):
            print(f'processing : {x}')
            if not self.check_no_process(x):
                self.process_root(self.pc_policy_dir, x)
        for x in os.listdir(self.pc_policy_file_dir):
            print(f'processing : {x}')
            if not self.check_no_process(x):
                self.process_root(self.pc_policy_file_dir, x)
        for x in os.listdir(self.pc_job_dir):
            print(f'processing : {x}')
            if not self.check_no_process(x):
                self.process_root(self.pc_job_dir, x)

    def check_no_process(self, in_file_name: str):
        for nop in no_process:
            if in_file_name.count(nop) > 0:
                return True
        return False

    def process_root(self, in_dir: str, in_pcf_file: str):
        tree = etree.parse(in_dir + '/' + in_pcf_file)
        root = tree.getroot()
        for element in root.iter():
            if element.tag == 'WizardStepSet':
                self.process_id(element, in_pcf_file)
            if element.tag == 'Page':
                self.process_id(element, in_pcf_file)
                self.process_ref(element, 'ScreenRef')
            if element.tag == 'PanelSet':
                self.process_id(element, in_pcf_file)
                self.process_ref(element, 'PanelRef')
            if element.tag == 'Popup':
                self.process_id(element, in_pcf_file)
            if element.tag == 'LocationGroup':
                self.process_id(element, in_pcf_file)
                self.process_ref(element, 'LocationRef')
            if element.tag == 'Screen':
                self.process_id(element, in_pcf_file)
                self.process_ref(element, 'PanelRef')
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
            if element.tag == 'LocationEntryPoint':
                self.process_location_entry_point(element, in_pcf_file)
            if element.tag == 'TextCell':
                self.process_tag(element)

        content = etree.tostring(root, pretty_print=True)
        new_pcf_file = self.new_file_name(in_pcf_file)
        print(f'writing : {new_pcf_file}')
        file = open(in_dir + "/" + new_pcf_file, 'w')
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

    def process_location_entry_point(self, element, in_pfc_file: str):
        attributes = element.attrib
        if 'signature' in attributes:
            _sig_name = in_pfc_file.replace('.pcf', '')
            _new_name = self.new_file_name(in_pfc_file).replace('.pcf', '')
            _location = attributes.get('signature')
            attributes['signature'] = _location.replace(_sig_name, _new_name)

    def process_ref(self, element, in_ref):
        _ref_type = ['ref', 'location', 'def']
        for sub_element in element.iter():
            if sub_element.tag == in_ref:
                attributes = sub_element.attrib
                for ref in _ref_type:
                    if ref in attributes:
                        _location_name = f"{attributes.get(ref).split('(')[0]}.pcf"
                        if _location_name.startswith('OOSEPanelSet'):
                            pass
                        else:
                            _new_name = self.new_file_name(_location_name)
                            _location = attributes.get(ref)
                            attributes[ref] = _location.replace(_location_name.replace('.pcf', ''), _new_name.replace('.pcf', ''))

    def process_id(self, element, in_pfc_file: str):
        attributes = element.attrib
        if 'id' in attributes:
            attributes['id'] = self.new_file_name(in_pfc_file).replace('.pcf', '')

    def process_tag(self, element):
        attributes = element.attrib
        if attributes.get('required') is None or (
                not attributes.get('required').startswith(pmp_class) and not attributes.get(
            'required') == 'isRequired'):
            self.process_required(attributes, attributes.get('required'), self.get_field(attributes))
        if attributes.get('valueVisible') is not None and (
                not attributes.get('valueVisible').startswith(pmp_class) and not attributes.get(
            'valueVisible') == 'isVisible'):
            self.process_value_visible(attributes, attributes.get('valueVisible'), self.get_field(attributes))
        if attributes.get('available') is None or (
                not attributes.get('available').startswith(pmp_class) and not attributes.get(
            'available') == 'isAvailable'):
            self.process_available(attributes, attributes.get('available'), self.get_field(attributes))
        for sub_element in element.iter():
            if sub_element.tag == 'PostOnChange':
                self.process_post_on_change(sub_element)

    def process_post_on_change(self, element):
        attributes = element.attrib
        if attributes.get('disablePostOnEnter') is None or (
                not attributes.get('disablePostOnEnter').startswith(pmp_class)):
            _pmpcode = attributes.get('disablePostOnEnter').replace(apd_class, pmp_class)
            attributes['disablePostOnEnter'] = _pmpcode
        return self

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

    def process_value_visible(self, attributes, visible_str, value_str):
        if value_str[1].startswith('#'):
            return
        default_str = 'false'
        if visible_str is not None:
            default_str = '(' + visible_str + ')'

        visible_str = visible_str.replace(apd_class, pmp_class)

        attributes['valueVisible'] = visible_str
        return self

    def new_file_name(self, in_pfc_file: str):
        if name_change.get(in_pfc_file) is not None:
            return name_change.get(in_pfc_file)
        if in_pfc_file.count('_Ext') > 0:
            return in_pfc_file
        new_pcf_file: str = ''
        for file_ending in file_ends:
            if in_pfc_file.endswith(file_ending):
                new_pcf_file = in_pfc_file.replace(file_ending, '_Ext' + file_ending)
        if new_pcf_file == '':
            new_pcf_file = in_pfc_file.replace('.pcf', '_Ext.pcf')
        if in_pfc_file != new_pcf_file:
            name_change[in_pfc_file] = new_pcf_file
        if self:
            return new_pcf_file

    def __init__(self, in_pc_path, in_pc_product_abbreviation):
        self.pc_path = in_pc_path
        self.pc_product_abbreviation = in_pc_product_abbreviation
        self.pc_policy_dir = self.pc_path + pc_pcf + '/' + self.pc_product_abbreviation + '/policy'
        self.pc_policy_file_dir = self.pc_path + pc_pcf + '/' + self.pc_product_abbreviation + '/policyfile'
        self.pc_job_dir = self.pc_path + pc_pcf + '/' + self.pc_product_abbreviation + '/job'
