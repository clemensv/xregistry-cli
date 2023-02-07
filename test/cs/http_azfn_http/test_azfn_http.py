import platform
import signal
import sys
import os
import subprocess
import shutil
import time


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.append(os.path.join(project_root))

import ceregistry

# call ps to find out the process id of the process with the given name and then kill it
def terminate_process(process_name):
    try:
        if platform.system() == 'Windows':
            command = 'taskkill /F /IM {}'.format(process_name)
        else:
            command = 'pkill -9 -f {}'.format(process_name)
        subprocess.run(command, shell=True, check=True)
    except:
        print('Failed to terminate process {}'.format(process_name))


def test_azfn_http():
    # clean the output directory
    output = os.path.join(project_root, "tmp/test/cs/azfn_http/")
    if os.path.exists(output):
        shutil.rmtree(output)
    # generate the producer
    sys.argv = ['ceregistry', 'generate',  
                '--style', 'producer', 
                '--language', 'cs',
                '--definitions', os.path.join(os.path.dirname(__file__), 'azfn_http.disco'),
                '--output', os.path.join(project_root, 'tmp/test/cs/azfn_http/producer/'),
                '--projectname', 'Contoso.ERP.Producer']
    ceregistry.main()
    # generate the consumer
    sys.argv = [ 'ceregistry', 'generate',  
                '--style', 'azfunctionhttp', 
                '--language', 'cs',
                '--definitions', os.path.join(os.path.dirname(__file__), 'azfn_http.disco'),
                '--output', os.path.join(project_root, 'tmp/test/cs/azfn_http/azfn/'),
                '--projectname', 'Contoso.ERP.AzureFunction']
    ceregistry.main()
    
    sentFileName = os.path.join(os.path.dirname(__file__),  "client", "sent.txt")
    receivedFileName = os.path.join(os.path.dirname(__file__), "function","bin","output","received.txt")

    if os.path.exists(sentFileName): os.remove(sentFileName)
    if os.path.exists(receivedFileName): os.remove(receivedFileName)

    my_env = os.environ.copy()
    my_env["RECEIVED_FILE"] = receivedFileName;
    my_env["SENT_FILE"] = sentFileName;
    
    func_process = None
    func_cmd = "func host start --port 11000"
    func_process = subprocess.Popen(func_cmd.split(" ") if platform.system() == "Windows" else func_cmd, env=my_env, stderr=sys.stderr, stdout=sys.stdout, shell=True, cwd=os.path.join(os.path.dirname(__file__), "function"))
    try:
        time.sleep(30);
        # Run the client
        print("Starting the client")
        client_cmd = "dotnet run"
        client_process = subprocess.Popen(client_cmd.split(" ") if platform.system() == "Windows" else client_cmd, env=my_env, cwd=os.path.join(os.path.dirname(__file__), "client"), stderr=sys.stderr, stdout=sys.stdout, shell=True) 
        client_process.wait()
    finally:    
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/pid", str(func_process.pid), "/f", "/t"], stderr=sys.stderr, stdout=sys.stdout)
        else:
            terminate_process("func")
        func_process.wait()
        
        
        
    sent_file = open(sentFileName, "r")
    sent_lines = sent_file.readlines()
    sent_file.close()
    received_file = open(os.path.join(receivedFileName), "r")
    received_lines = received_file.readlines()
    received_file.close()
    # check that each line in sent.txt is in received.txt
    for sent_line in sent_lines:
        if sent_line not in received_lines:
            raise Exception("The line " + sent_line + " was not found in the received.txt file")
