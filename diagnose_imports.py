try:
    import sheets_utils
    import summarizer
    import config
    import drive_utils
    import pdf_parser
    print("✅ All imports succeeded.")
except Exception as e:
    print(f"❌ Import error: {e}")
