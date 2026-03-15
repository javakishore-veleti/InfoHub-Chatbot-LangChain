class AbstractReqRespDto:
    def __init__(self):
        self.status: str = "success"
        self.ctx_data: dict = {}

    def add_ctx_data(self, key: str, value) -> None:
        self.ctx_data.update({key: value})

    def remove_ctx_data(self, key: str) -> None:
        self.ctx_data.pop(key)

    def get_ctx_data(self) -> dict:
        return self.ctx_data

    def set_status(self, status: str) -> None:
        self.status = status

    def set_ctx_data(self, ctx_data: dict) -> None:
        self.ctx_data = ctx_data

    def get_ctx_data_by_key(self, key: str):
        return self.ctx_data.get(key)