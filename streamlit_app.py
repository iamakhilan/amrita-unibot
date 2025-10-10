"""
Streamlit Cloud entrypoint wrapper.
This file imports and runs the main() function in `chatbot_ver2.py` so Streamlit Cloud can detect
and run the app as `streamlit run streamlit_app.py`.
"""
from chatbot_ver2 import main


def run():
    main()


if __name__ == "__main__":
    run()
