class LectorMOExceptions(BaseException):
    def __init__(self, *args: object):
        super().__init__(args)
        self.message = "Default exception"

    def too_many_request(self):
        self.message = "Too many requests to the server"
        return Exception(self.message)
