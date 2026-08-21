class RequestContext:

    def __init__(
        self,
        user_id: str,
        document_id: str
    ):
        self.user_id = user_id
        self.document_id = document_id