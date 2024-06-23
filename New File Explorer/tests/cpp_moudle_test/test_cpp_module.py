import traceback
from search_module import search_advanced

def test_search_advanced():
    try:
        results = search_advanced("Use", "C:\\")
        print("Results:", results)
    except Exception as e:
        print("Exception occurred:", e)
        traceback.print_exc()

if __name__ == "__main__":
    if "C:\\Users" in test_search_advanced():
        print("Lezgoski letgo")
