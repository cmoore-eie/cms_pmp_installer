import os

from lxml import etree


attribute_type = 0
attribute_value = 1
pc_pcf = '/config/web/pcf/line'
apd_class = 'gw.web.rules.APDRulesHelper'
pmp_class = 'gw.pmp.apd.web.rules.APDRulesHelper_PMP'
file_ends = ['PanelSet.pcf', 'Popup.pcf', 'ListDetail.pcf', 'Screen.pcf']
no_process = ['MenuItemSet', 'WizardStepSet']
input_tags = ['TextInput', 'RangeInput', 'PickerInput', 'TextAreaInput', 'TypeKeyInput', 'BooleanRadioInput',
              'DateInput', 'MonetaryAmountInput', 'TextCell']
name_change = dict()


def check_no_process(in_file_name: str) -> bool:
    """ There are some instances where the file should no be processed at the moment, by not processing these files
        defined in the no_process variable there may be some small manual changes needed to get the new PCF files to
        be used"""
    for nop in no_process:
        if in_file_name.count(nop) > 0:
            return True
    return False


class ProcessPCF:

    def process_pcf(self):
        for x in os.listdir(self.pc_policy_dir):
            print(f'processing : {x}')
            if not check_no_process(x):
                self.process_root(self.pc_policy_dir, x)
        for x in os.listdir(self.pc_policy_file_dir):
            print(f'processing : {x}')
            if not check_no_process(x):
                self.process_root(self.pc_policy_file_dir, x)
        for x in os.listdir(self.pc_job_dir):
            print(f'processing : {x}')
            if not check_no_process(x):
                self.process_root(self.pc_job_dir, x)

    def process_root(self, in_dir: str, in_pcf_file: str):
        """ The PCF file is opened and each of the elements in the PCF file, depending on the element there may be
            special processing that needs to take place. When a target element is identified the
            function to process the element is called. """
        tree = etree.parse(in_dir + '/' + in_pcf_file)
        self.root = tree.getroot()
        for element in self.root.iter():
            if element.tag == 'InputSet':
                self.process_input_set(element)
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
            if element.tag in input_tags:
                self.process_tag(element)
            if element.tag == 'LocationEntryPoint':
                self.process_location_entry_point(element, in_pcf_file)

        content = etree.tostring(self.root, pretty_print=True)
        new_pcf_file = self.new_file_name(in_pcf_file)
        print(f'writing : {new_pcf_file}')
        file = open(in_dir + "/" + new_pcf_file, 'w')
        file.write(content.decode('utf-8'))
        file.close()

    def process_apd_variable(self, element):
        """ APD sets the variables isEditable and isVisible to use in the PCF, the use of these variables gets
            around the current processing that worked in previous versions of PolicyCenter. To ensure that PMP works
            correctly the other variables isRequired and isAvailable are added. While these are not added by
            APD at the moment they may well feature in a future version."""
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

    def process_ref(self, element, in_ref: str):
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
                            attributes[ref] = _location.replace(_location_name.replace('.pcf', ''),
                                                                _new_name.replace('.pcf', ''))

    def process_id(self, element, in_pfc_file: str):
        """ Updates the id associated with the widget from the original to the modified name
            making use of the _Ext"""
        attributes = element.attrib
        if 'id' in attributes:
            attributes['id'] = self.new_file_name(in_pfc_file).replace('.pcf', '')

    def process_tag(self, element):
        attributes = element.attrib
        if attributes.get('required') is None or (
                not attributes.get('required').startswith(pmp_class) and not attributes.get(
            'required') == 'isRequired'):
            self.process_required(attributes)
        if attributes.get('valueVisible') is not None and (
                not attributes.get('valueVisible').startswith(pmp_class) and not attributes.get(
            'valueVisible') == 'isVisible'):
            self.process_value_visible(attributes, attributes.get('valueVisible'), self.get_field(attributes))
        if attributes.get('available') is None or (
                not attributes.get('available').startswith(pmp_class) and not attributes.get(
            'available') == 'isAvailable'):
            self.process_available(attributes)
        for sub_element in element.iter():
            if sub_element.tag == 'PostOnChange':
                self.process_post_on_change(sub_element)

    def process_post_on_change(self, element):
        """Changes the APD functions used for the post on change to call the PMP equivalent functions. The PMP
           version of the functions act as a wrapper incorporating the original APD functions"""
        attributes = element.attrib
        if attributes.get('disablePostOnEnter') is None or (
                not attributes.get('disablePostOnEnter').startswith(pmp_class)):
            _pmp_code = attributes.get('disablePostOnEnter').replace(apd_class, pmp_class)
            attributes['disablePostOnEnter'] = _pmp_code
        if attributes.get('onChange') is None or (
                not attributes.get('onChange').startswith(pmp_class)):
            _pmp_code = attributes.get('onChange').replace(apd_class, pmp_class)
            attributes['onChange'] = _pmp_code
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

    def process_available(self, attributes):
        attributes['available'] = 'isAvailable'
        return self

    def process_available_variable(self, available_str, value_str):
        if value_str[1].startswith('#'):
            return

        available_str = pmp_class + '.isAvailable(' \
                        + value_str[0] + '.PolicyLine, ' \
                        + value_str[0] + ', ' \
                        + value_str[1] + '.PropertyInfo' \
                        + ')'
        if self:
            return available_str

    def process_required(self, attributes):
        attributes['required'] = 'isRequired'
        return self

    def process_required_variable(self, required_str, value_str):
        """ Function to return the PMP function for the isRequired variable"""
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
        if self:
            return required_str

    def process_value_visible(self, attributes, visible_str, value_str):
        if value_str[1].startswith('#'):
            return
        default_str = 'false'
        if visible_str is not None:
            default_str = '(' + visible_str + ')'
        visible_str = visible_str.replace(apd_class, pmp_class)
        attributes['valueVisible'] = visible_str
        return self

    def process_input_set(self, original_element):
        """ To get round the issue of the PCF on change functionality we need to test for the existence of the
            isRequired variable. If the isEditable and isVisible defined then we are looking in the right place and if
            there is no isRequired variable it will be added. To add the variable, information from the input needs
            to be extracted first."""
        apd_variables = {'isEditable': False, 'isVisible': False, 'isRequired': False, 'isAvailable': False}
        input_attributes = None
        for sub_element in original_element.iter():
            #
            # If there is an input widget in the input set the attributes are stored for later processing
            #
            if sub_element.tag in input_tags:
                input_attributes = sub_element.attrib
            #
            # When a variable is found in the input set and it is in the apa_variables dictionary the
            # item in the dictionary is updated from False to True
            #
            if sub_element.tag == 'Variable':
                attributes = sub_element.attrib
                if 'name' in attributes:
                    _name = attributes['name']
                    apd_variables[_name] = True
                    element = sub_element
        #
        # if there exists only the isEditable and the isVisible variables and the input widget attributes
        # have been saved it is assumed the isRequired and isAvailable variables need to be created
        #
        if apd_variables['isEditable'] and apd_variables['isVisible'] and input_attributes is not None:
            if not apd_variables['isRequired']:
                pmp_function = self.process_required_variable(input_attributes.get('required'),
                                                              self.get_field(input_attributes))
                variable_element = etree.Element('Variable')
                variable_element.set('initialValue', pmp_function)
                variable_element.set('name', 'isRequired')
                variable_element.set('recalculateOnRefresh', 'true')
                variable_element.set('type', 'Boolean')
                original_element.insert(0, variable_element)
            if not apd_variables['isAvailable']:
                pmp_function = self.process_available_variable(input_attributes.get('required'),
                                                               self.get_field(input_attributes))
                variable_element = etree.Element('Variable')
                variable_element.set('initialValue', pmp_function)
                variable_element.set('name', 'isAvailable')
                variable_element.set('recalculateOnRefresh', 'true')
                variable_element.set('type', 'Boolean')
                original_element.insert(0, variable_element)
        return self

    def new_file_name(self, in_pfc_file: str) -> str:
        """Modifications to the originally generated APD PCF files should not be done, to this end this function
           defines the name of the new PCF file to be created. """
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

    def __init__(self, in_config_json):
        self.config_json = in_config_json
        self.root = None
        self.pc_path = in_config_json['pc_path']
        self.pc_product_abbreviation = in_config_json['pc_product_abbreviation']
        self.pc_policy_dir = self.pc_path + pc_pcf + '/' + self.pc_product_abbreviation + '/policy'
        self.pc_policy_file_dir = self.pc_path + pc_pcf + '/' + self.pc_product_abbreviation + '/policyfile'
        self.pc_job_dir = self.pc_path + pc_pcf + '/' + self.pc_product_abbreviation + '/job'
