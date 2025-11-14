from cx_Freeze import setup, Executable

setup(
    name="WebSQLAssistant",
    version="1.0",
    description="Web 1C SQL Assistant",
    executables=[Executable("main.py")],
)