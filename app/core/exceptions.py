class BusinessException(Exception):
    """业务异常基类"""

    def __init__(self, biz_code: int, message: str, http_status: int = 400):
        self.biz_code = biz_code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


class AuthException(BusinessException):
    """认证异常：Token 无效或过期"""

    def __init__(self, message: str = "Token 未携带或已过期"):
        super().__init__(biz_code=40101, message=message, http_status=401)


class PermissionException(BusinessException):
    """权限异常：无权限访问"""

    def __init__(self, message: str = "无权限访问该资源"):
        super().__init__(biz_code=40301, message=message, http_status=403)


class NotFoundException(BusinessException):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(biz_code=40401, message=message, http_status=404)


class DuplicateException(BusinessException):
    """数据重复"""

    def __init__(self, message: str = "数据已存在"):
        super().__init__(biz_code=42201, message=message, http_status=422)


class ParamException(BusinessException):
    """参数错误"""

    def __init__(self, message: str = "参数缺失或格式错误"):
        super().__init__(biz_code=40001, message=message, http_status=400)


class ServerException(BusinessException):
    """服务器内部错误"""

    def __init__(self, message: str = "服务器内部错误"):
        super().__init__(biz_code=50001, message=message, http_status=500)
