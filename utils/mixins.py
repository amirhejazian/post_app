class APIExceptionMappingMixin:
    exception_mapping = {}

    def handle_exception(self, exc):
        mapped_exception = self.exception_mapping.get(exc.__class__)
        if mapped_exception is not None:
            exc = mapped_exception()
        return super().handle_exception(exc)
