"A helper module to provide helper functions."

# =================================================================================================

class PasteCodes:
    valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    ID_LENGTH = 4

    @classmethod
    def from_int(cls, post_id: int, *, length: int = 4) -> str:
        assert length > 0
        post_id %= len(cls.valid_chars) ** length

        code = ""
        n = post_id

        for _ in range(length):
            n, r = divmod(n, len(cls.valid_chars))
            code = cls.valid_chars[r] + code
        
        return code
    
    @classmethod
    def from_str(cls, post_id: str) -> int | None:
        post_id = post_id.lstrip('A') # Remove padding
        
        value = 0

        for i, char in enumerate(post_id[::-1]):
            if char not in cls.valid_chars:
                return None
            
            value += cls.valid_chars.index(char) * len(cls.valid_chars) ** i

        return value
    
# =================================================================================================

def http_reply(status_code: int, message: str) -> dict[str, int | str]:
    return {
        "status": status_code,
        "message": message or "No message given."
    }

success = http_reply(200, "Success!")
error_400 = lambda message: http_reply(400, message)

# =================================================================================================

from anyio import create_memory_object_stream