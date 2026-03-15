class ExecCtxData:
    def __init__(self):
        self.ctx_data: dict = {}

    def add_ctx_data(self, key: str, value) -> None:
        self.ctx_data.update({key: value})

    def get_ctx_data(self) -> dict:
        return self.ctx_data

    def get_ctx_data_by_key(self, key: str):
        return self.ctx_data.get(key)

