from cmd import Cmd
import os

def convert_2_OWL (input_filename, output_filename):
    file_contents = ""
    print("start")
    work_dir = os.path.dirname(os.path.realpath(__file__))
    
    data_dir_output = f'{output_filename}'
    data_dir_input = f'{input_filename}'

    cmd = f"java -jar "+work_dir+"/IFCtoLBD_CLI.jar "+data_dir_input+" -u=http://w3id.org/ioc#  --target_file="+data_dir_output+" --level=3 --hasGeometry --ifcOWL"


    os.system(cmd)

