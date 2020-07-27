import os
from lxml import etree
from lxml.etree import CDATA

attribute_type = 0
attribute_value = 1
existence_dict = {
    'Suggested': 'ExistenceType.TC_SUGGESTED',
    'Required': 'ExistenceType.TC_REQUIRED',
    'Electable': 'ExistenceType.TC_ELECTABLE'
}

pc_product_model = '/config/resources/productmodel/policylinepatterns'


class ProcessProduct:
    root = None
    """
    Clause pattern files are read from the directory and processed one by one, where the
    XML is examined and adjusted for PMP, the lookup files are excluded as there is nothing
    to change in these files.
    """

    def process_clause_patterns(self):
        for x in os.listdir(self.pc_product_dir):
            #
            # Only need to process the clauses and not the lookup
            #
            if not ('lookup' in x):
                print('processing : ' + x)
                self.process_root(x)

    """
    Processing of the individual clause pattern XML file. The files are examined for specific items and these are
    adjusted or created as needed
    """

    def process_root(self, in_xml_file):
        tree = etree.parse(self.pc_product_dir + '/' + in_xml_file)
        root = tree.getroot()
        children = list(root)
        for att in root.items():
            if att[attribute_type] == 'codeIdentifier':
                self.code_identifier = att[attribute_value]
            if att[attribute_type] == 'owningEntityType':
                self.owning_entity = att[attribute_value]
            if att[attribute_type] == 'existence':
                self.existence = att[attribute_value]

        availability_tag = False
        existence_tag = False
        initialize_tag = False

        for child in children:
            if child.tag == 'AvailabilityScript':
                availability_tag = True
                self.process_availability(root, availability_tag, child, 'clause', self.code_identifier)
            if child.tag == 'ExistenceScript':
                existence_tag = True
                self.process_existence(root, existence_tag, child)
            if child.tag == 'InitializeScript':
                initialize_tag = True
                self.process_initialize(root, initialize_tag, child)
            if child.tag == 'CovTerms':
                self.process_covterms(root, child)
            if child.tag == 'Schedules':
                pass

        if not availability_tag:
            self.process_availability(root, availability_tag, None, 'clause', self.code_identifier)
        if not existence_tag:
            self.process_existence(root, existence_tag, None)
        if not initialize_tag:
            self.process_initialize(root, initialize_tag, None)

        content = etree.tostring(root, pretty_print=True)
        file = open(self.pc_product_dir + "/" + self.code_identifier + '.xml', 'w')
        file.write(content.decode('utf-8'))
        file.close()

    def add_clause_initialize(self):
        initialize_string = 'return gw.pmp.scheme.util.SchemeUtil_PMP.updateTermValue(' \
                            + self.code_identifier + ')'
        return initialize_string

    def add_availability(self, script_type, identifier, actual):
        availability_string = ''
        if script_type == 'clause':
            if not actual:
                availability_string = 'return gw.pmp.scheme.util.SchemeUtil_PMP.isCoverageIncluded("' \
                                      + identifier \
                                      + '", true, ' \
                                      + self.owning_entity + ')'
            else:
                availability_string = 'return gw.pmp.scheme.util.SchemeUtil_PMP.isCoverageIncluded("' \
                                      + identifier \
                                      + '", actual, ' \
                                      + self.owning_entity + ')'

        if script_type == 'term':
            if not actual:
                availability_string = 'return gw.pmp.scheme.util.SchemeUtil_PMP.isCoverageTermIncluded("' \
                                      + identifier \
                                      + '", true, ' \
                                      + self.owning_entity + ')'
            else:
                availability_string = 'return gw.pmp.scheme.util.SchemeUtil_PMP.isCoverageTermIncluded("' \
                                      + identifier \
                                      + '", actual, ' \
                                      + self.owning_entity + ')'

        if script_type == 'term_option':
            risk_object = 'CovTerm.' \
                          + identifier[0] \
                          + '.OwningCoverable'
            if not actual:
                availability_string = 'return gw.pmp.scheme.util.SchemeUtil_PMP.isCoverageTermOptionIncluded("' \
                                      + identifier[0] + '", "' \
                                      + identifier[1] + '", "' \
                                      + identifier[2] \
                                      + '", true, ' \
                                      + risk_object + ')'
            else:
                availability_string = 'return gw.pmp.scheme.util.SchemeUtil_PMP.isCoverageTermOptionIncluded("' \
                                      + identifier[0] + '", "' \
                                      + identifier[1] + '", "' \
                                      + identifier[2] \
                                      + '", actual, ' \
                                      + risk_object + ')'

        if script_type == 'term_package':
            risk_object = 'CovTerm.' \
                          + identifier[0] \
                          + '.OwningCoverable'
            if not actual:
                availability_string = 'return gw.pmp.scheme.util.SchemeUtil_PMP.isCoverageTermPackageIncluded("' \
                                      + identifier[0] + '", "' \
                                      + identifier[1] + '", "' \
                                      + identifier[2] \
                                      + '", true, ' \
                                      + risk_object + ')'
            else:
                availability_string = 'return gw.pmp.scheme.util.SchemeUtil_PMP.isCoverageTermPackageIncluded("' \
                                      + identifier[0] + '", "' \
                                      + identifier[1] + '", "' \
                                      + identifier[2] \
                                      + '", actual, ' \
                                      + risk_object + ')'

        return availability_string

    def add_clause_existence(self):
        existence_string = 'return gw.pmp.scheme.util.SchemeUtil_PMP.coverageExistence("' \
                           + self.code_identifier \
                           + '", ' + existence_dict[self.existence] + ', ' \
                           + self.owning_entity + ')'
        return existence_string

    """
    Processing for the availability on the clause, if there is existing code that is not PMP code this is 
    assigned to the variable 'actual' and used as the default for the PMP function call
    """

    def process_availability(self, root, tag, child, script_type, identifier):
        if tag:
            if child.text is None:
                child.text = CDATA(self.add_availability(script_type, identifier, False))
            else:
                if 'SchemeUtil_PMP' not in child.text:
                    new_var = ''
                    current_code_array = child.text.splitlines()
                    current_code = ''
                    for line_code in current_code_array:
                        if line_code.startswith('//'):
                            pass
                        else:
                            current_code = current_code + line_code + '\n'
                        
                    if child.text.count('return ') > 1:
                        new_var = new_var + 'var actual : boolean'
                        new_var = new_var + str(current_code).replace('return', 'actual =').replace('"', '\"')
                    else:
                        new_var = str(current_code).replace('return', 'var actual =', 1).replace('"', '\"')
                    child.text = CDATA(new_var + '\n' + self.add_availability(script_type, identifier, True))
        else:
            new_element = etree.Element('AvailabilityScript')
            new_element.text = CDATA(self.add_availability(script_type, identifier, False))
            root.insert(0, new_element)

    """
    Processing of the existence on the clause. If there is an existence attribute this is removed and the value it held
    used to create the default used in the PMP Scheme Function
    """

    def process_existence(self, root, tag, child):
        if self.existence != '':
            del root.attrib['existence']
            if tag:
                if child.text is None:
                    child.text = CDATA(self.add_clause_existence())
            else:
                new_element = etree.Element('ExistenceScript')
                new_element.text = CDATA(self.add_clause_existence())
                root.insert(0, new_element)

    """
    Processing for the initialization on the clause
    """

    def process_initialize(self, root, tag, child):
        if tag:
            if child.text is None:
                child.text = CDATA(self.add_clause_initialize())
        else:
            new_element = etree.Element('InitializeScript')
            new_element.text = CDATA(self.add_clause_initialize())
            root.insert(0, new_element)

    """
    Process the coverage terms, this involves similar process to the root
    """

    def process_covterms(self, root, child):
        for child_element in child:

            term_identifier = None
            for att in child_element.items():
                if att[attribute_type] == 'codeIdentifier':
                    term_identifier = att[attribute_value]

            if child_element.tag == 'PackageCovTermPattern':
                self.process_base_covterms(root, child_element, term_identifier)
                self.process_package_covterms(root, child_element, term_identifier)
            if child_element.tag == 'OptionCovTermPattern':
                self.process_base_covterms(root, child_element, term_identifier)
                self.process_option_covterms(root, child_element, term_identifier)
            if child_element.tag == 'GenericCovTermPattern':
                self.process_base_covterms(root, child_element, term_identifier)
            if child_element.tag == 'DirectCovTermPattern':
                self.process_base_covterms(root, child_element, term_identifier)

    def process_option_covterms(self, root, child_element, term_identifier):
        for option_cov_term in child_element:
            if option_cov_term.tag == 'Options':
                for cov_term_opt in option_cov_term:
                    cov_term_opt_identifier = ''
                    for cov_term_opt_att in cov_term_opt.items():
                        if cov_term_opt_att[attribute_type] == 'codeIdentifier':
                            cov_term_opt_identifier = cov_term_opt_att[attribute_value]
                    cov_term_opt_tag = False
                    for cov_term_opt_item in cov_term_opt:
                        cov_term_opt_tag = True
                        self.process_availability(cov_term_opt, cov_term_opt_tag, cov_term_opt_item
                                                  , 'term_option',
                                                  [self.code_identifier, term_identifier,
                                                   cov_term_opt_identifier])
                    if not cov_term_opt_tag:
                        self.process_availability(cov_term_opt, False, None
                                                  , 'term_option',
                                                  [self.code_identifier, term_identifier,
                                                   cov_term_opt_identifier])

    def process_base_covterms(self, root, child_element, term_identifier):
        availability_tag = False
        for child_element_child in child_element:
            if child_element_child.tag == 'AvailabilityScript':
                availability_tag = True
                self.process_availability(child_element, availability_tag, child_element_child
                                          , 'term', term_identifier)

        if not availability_tag:
            self.process_availability(child_element, availability_tag, None
                                      , 'term', term_identifier)

    def process_package_covterms(self, root, child_element, term_identifier):
        for option_cov_term in child_element:
            if option_cov_term.tag == 'Packages':
                for cov_term_opt in option_cov_term:
                    for cov_term_opt_item in cov_term_opt:
                        if cov_term_opt_item.text is not None:
                            if cov_term_opt_item.tag == 'PackageTerms':
                                pass
                            else:
                                cov_term_opt_item.text = CDATA(cov_term_opt_item.text)

    def __init__(self, in_pc_path, in_pc_product_line):
        self.pc_path = in_pc_path
        self.pc_product_line = in_pc_product_line
        self.pc_product_dir = self.pc_path + pc_product_model + '/' + self.pc_product_line + '/coveragepatterns'
        self.code_identifier = ''
        self.owning_entity = ''
        self.existence = ''
