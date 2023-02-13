from cmd import Cmd
import os


def main (input_filepath, output_filepath):
    file_contents = ""
    print("start")
    work_dir = os.path.dirname(os.path.realpath(__file__))
    
    data_dir_output = work_dir+f"{output_filepath}"
    data_dir_input = work_dir+f"{input_filepath}"
    #logger.info(data_dir_output)
    
    #cmd = f"java -jar "+work_dir+"\IfcSTEP2IfcOWL-1.0.0.jar "+data_dir_input+"input.ifc "+data_dir_output+"output.ttl -b http://w3id.org/ioc#"
    cmd = f"java -Xmx8g -Xms8g -jar {work_dir}\\IFCtoRDF-0.4-shaded.jar -b http:\\linkedbuildingdata.net\\ifc\\resources20221218_161821# {data_dir_input}Project1.ifc {data_dir_output}Project1.ttl"

    print(cmd)
    os.system(cmd)

if __name__ == "__main__":
    
    main()
