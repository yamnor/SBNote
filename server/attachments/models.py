from helpers import CustomBaseModel


class AttachmentCreateResponse(CustomBaseModel):
    filename: str
    url: str
    original_filename: str
