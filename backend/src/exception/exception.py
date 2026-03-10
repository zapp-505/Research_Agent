import sys

class ResearchAgentException(Exception):
    def __init__(self,error_message,error_details:sys):
        self.error_message = error_message
#take in the traceback object tb only from sys.exc_info,tells where the error happened.
        _,_,exc_tb = error_details.exc_info()
        
        self.lineno=exc_tb.tb_lineno
        self.file_name=exc_tb.tb_frame.f_code.co_filename 
    
    def __str__(self):
        return "Error occured in python script name [{0}] line number [{1}] error message [{2}]".format(
        self.file_name, self.lineno, str(self.error_message))
        