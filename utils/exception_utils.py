import logging

from config import DEBUG

exp_replacement = {
    ValueError: "is an invalid value!", 
    TypeError: "system error!"
}
                   
#Exception handing to return status and msg
class ExpHandleAll(object):
    def __init__(self):
        self.handle_funcs = {
            "ValueError": self.handleValueError,
            "BadValueError": self.handleBadValueError,
        }
    def __call__(self, func):
        def handle_all(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exp:
                exp_name = type(exp).__name__
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                msg = template.format(exp_name, exp.args)
                
                if DEBUG:
                    logging.info(msg)
                    
                if exp_name in self.handle_funcs:
                    msg = self.handle_funcs[exp_name](exp.args)
                else:
                    msg = exp.args[0]
                return False, msg
        return handle_all
    
    def handleValueError(self, exp_args):
        key, val = exp_args[0].split(":")
        msg = "(%s is an invalid value.)" %(val)
        return msg
    
    def handleBadValueError(self, exp_args):
        print (exp_args)
        key, val = exp_args[0].split(":")
        msg = ""
        if "uninitialized" in key:
            msg = "(Values for required fields are missing.)"
        return msg
    
#sample code
class ErrorIgnore(object):
   def __init__(self, errors, errorreturn = None, errorcall = None):
      self.errors = errors
      self.errorreturn = errorreturn
      self.errorcall = errorcall

   def __call__(self, function):
      def returnfunction(*args, **kwargs):
         try:
            return function(*args, **kwargs)
         except Exception as E:
            if type(E) not in self.errors:
               raise E
            if self.errorcall is not None:
               self.errorcall(E, *args, **kwargs)
            return self.errorreturn
      return returnfunction
  
class ConvertExceptions(object):
    func = None
    def __init__(self, exceptions, replacement=None):
        self.exceptions = exceptions
        self.replacement = replacement
        
    def __call__(self, *args, **kwargs):
        if self.func is None:
            self.func = args[0]
            return self
        try:
            return self.func(*args, **kwargs)
        except self.exceptions:
            return self.replacement
