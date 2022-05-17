import json
import sys
import getopt
from json import JSONDecodeError

from ProcessAPI import ProcessAPI
from ProcessProduct import ProcessProduct
from ProcessPCF import ProcessPCF

help_str = '''

Please supply the arguments for -c
        -c, --config - path to the json configuration file
        -h, --help - displays this text

        '''
json_errors = dict()
process_errors = dict()


def main(argv):
    config_file: str = ''

    try:
        opts, args = getopt.getopt(argv, 'c:', ['help', 'config ='])
        for opt, arg in opts:
            if opt in ['-c', '--config']:
                config_file = arg.strip()
            elif opt in ['-h', '--help']:
                print(help_str)
                sys.exit()
            else:
                sys.exit()
    except getopt.GetoptError:
        print(help_str)
        sys.exit(2)

    if config_file == '':
        process_errors[len(process_errors) +
                       1] = "-c (--config) missing and is required"
        sys.exit(1)

    if len(process_errors) > 0:
        print("")
        print("Missing Parameter Information")
        print("=============================")
        for error_item in process_errors:
            print(f"({error_item}) : {process_errors[error_item]}")
    else:
        try:
            file = open(config_file)
        except FileNotFoundError:
            print(f'ERROR - The configuration file {config_file} has not been found')
            sys.exit(1)
        try:
            decoded_json = json.load(file)
            config_json = check_and_fix_json(decoded_json)
            print(f'pc_path : {decoded_json["pc_path"]}')
            print(f'pc_product_line : {decoded_json["pc_product_line"]}')
            print(f'pc_product_abbreviation : {decoded_json["pc_product_abbreviation"]}')
            print(f'pc_product_location : {decoded_json["pc_product_location"]}')
            print(f'process_type : {decoded_json["process_type"]}')
            process_type = str(decoded_json["process_type"])
            if process_type.lower() == 'all' or process_type.lower() == 'pcf':
                product_process = ProcessPCF(decoded_json)
                product_process.process_pcf()

            if process_type.lower() == 'all' or process_type.lower() == 'model':
                product_process = ProcessProduct(decoded_json)
                product_process.process_clause_patterns()

            if process_type.lower() == 'all' or process_type.lower() == 'api':
                product_process = ProcessAPI(decoded_json)
                product_process.process_api()

        except JSONDecodeError:
            print(f'ERROR - The json file {config_file} is invalid and needs correcting before use')
            sys.exit(1)


def check_and_fix_json(config_json):
    """
    Checks the json information and where there is missing information this is set to a default value
    """
    if 'process_type' not in config_json:
        json_errors[len(json_errors) + 1] = 'process_type has not been set (all, pcf, model, api)'

    if 'pc_path' not in config_json:
        json_errors[len(json_errors) + 1] = 'pc_path has not been set'

    if 'pc_product_line' not in config_json:
        json_errors[len(json_errors) + 1] = 'pc_product_line has not been set'

    if 'pc_product_abbreviation' not in config_json:
        json_errors[len(json_errors) + 1] = 'pc_product_abbreviation has not been set'

    if 'pc_product_location' not in config_json:
        json_errors[len(json_errors) + 1] = 'pc_product_location has not been set'

    if len(json_errors) > 0:
        print("")
        print("Configuration issues")
        print("====================")
        for error_item in json_errors:
            print(f"({error_item}) : {json_errors[error_item]}")
        sys.exit(1)

    return config_json


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(help_str)
        sys.exit()
    main(sys.argv[1:])
