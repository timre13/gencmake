import sys
import os
from glob import iglob

def printerr(s: str): sys.stderr.write(s+"\n")

if len(sys.argv) != 2:
    printerr("Usage: "+sys.argv[0]+" <project name>")
    sys.exit(1)

PROJECT_NAME = sys.argv[1]
CMAKE_MIN_VER = "3.10"
FILE_EXTENSIONS = (
    ".cpp",
    ".c",
    ".cxx",
    ".h",
    ".hpp",
    ".H",
)

class ProjectFile:
    def __init__(self):
        if os.path.exists("./CMakeLists.txt"):
            raise FileExistsError
        self.file = open("CMakeLists.txt", "w+")

    def writeLine(self, val: str=""):
        self.file.write(val+"\n")

    def writeCmakeMinVer(self):
        self.file.write("cmake_minimum_required(VERSION {})\n".format(CMAKE_MIN_VER))

    def writeCxxStandard(self, standard: str):
        self.file.write("set(CMAKE_CXX_STANDARD {})\nset(CMAKE_CXX_STANDARD_REQUIRED true)\n".format(standard))

    def writeProjectDecl(self, projectName: str, projectVersion: str):
        self.file.write("project({} VERSION {})\n".format(projectName, projectVersion))

    def writeFlags(self, flags: tuple):
        self.file.write("set(CMAKE_CXX_FLAGS \"{}\")\n".format(" ".join(flags)))

    def writeExportCCommands(self):
        self.file.write("set(CMAKE_EXPORT_COMPILE_COMMANDS true)\n")

    def writeExeInfo(self, exeName: str):
        sourceFiles = []
        for file in iglob("src/**/*", recursive=True):
            if file.endswith(FILE_EXTENSIONS):
                sourceFiles.append(file)
        if not sourceFiles:
            printerr("Error: No source files found")
            sys.exit(1)
        self.file.write("add_executable({}\n{})\n".format(exeName, "".join([" "*4+x+"\n" for x in sorted(sourceFiles, reverse=True)])))

    def __del__(self):
        try:
            self.file.close()
        except AttributeError:
            pass

try:
    file = ProjectFile()
except:
    printerr("Error: File already exists")
    sys.exit(1)
file.writeCmakeMinVer()
file.writeLine()
file.writeCxxStandard("17")
file.writeLine()
file.writeProjectDecl(PROJECT_NAME, "1.0")
file.writeLine()
file.writeFlags(("-Wall", "-Wextra", "-Wpedantic", "-g3", "-fno-limit-debug-info"))
file.writeLine()
file.writeExportCCommands()
file.writeLine()
file.writeExeInfo(PROJECT_NAME)

