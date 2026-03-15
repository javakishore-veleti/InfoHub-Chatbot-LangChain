from app.common.dtos.ingest_dtos import IngestReqDto, IngestRespDto
from app.common.dtos.exec_ctx_dto import ExecCtxData


# noinspection PyMethodMayBeStatic,PyPep8Naming
class WfTask:

    def __init__(self):
        self.task_name: str = "UN_DEFINED"

    def set_wf_task_name(self, wf_task_name):
        self.task_name = wf_task_name

    def get_wf_task_name(self):
        return self.task_name

    def execute(self, reqDto:IngestReqDto, respDto:IngestRespDto, execCtxData: ExecCtxData) -> int:
        return 0