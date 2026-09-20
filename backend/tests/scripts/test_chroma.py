import asyncio
from app.services.law_browser_service import get_law_browser_service

def test():
    svc = get_law_browser_service()
    code_id = "საქართველოს ადმინისტრაციულ სამართალდარღვევათა კოდექსი"
    res = svc.get_code(code_id)
    print(res)

if __name__ == "__main__":
    test()
