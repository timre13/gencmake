import sys
import os
from glob import iglob
import subprocess as sp

def printerr(s: str): sys.stderr.write(s+"\n")

if len(sys.argv) != 2 and len(sys.argv) != 3:
    printerr("Usage: "+sys.argv[0]+" <project name> <optional: project type>")
    sys.exit(1)

if sys.argv[1] == "--list-project-types".strip() or sys.argv[1].strip() == "-l":
    print("Available project types:\n\
    default:    A project without any libraries.\n\
    sdl2:       A project with the SDL2 graphical library.\n\
    gtkmm-3.0:  A project with the GTK-3 binding for C++.\n\
    fltk:       A project with the FLTK GUI toolkit.")
    sys.exit(0)

PROJECT_NAME = sys.argv[1].strip()
PROJECT_TYPE = "default" if len(sys.argv) == 2 else sys.argv[2].lower()
PROJECT_CFLAGS = ["-Wall", "-Wextra", "-Wpedantic", "-g3", "-fno-limit-debug-info"]
PROJECT_LIBS = []
PROJECT_INCLUDE_DIRS = []
CMAKE_MIN_VER = "3.10"
CXX_STANDARD_VER = "17"
FILE_EXTENSIONS = (
    ".cpp",
    ".c",
    ".cxx",
    ".h",
    ".hpp",
    ".H",
)

MAIN_SKELETONS = {
"default":
r"""#include <iostream>

int main()
{
    std::cout << "Hello, World!\n";
    return 0;
}
""",

"sdl2":
r"""#include <SDL2/SDL.h>
#include <iostream>

#define WINDOW_WIDTH 1500
#define WINDOW_HEIGHT 1000

int main()
{
    if (SDL_Init(SDL_INIT_VIDEO))
    {
        std::cerr << "Failed to initialize SDL2: " << SDL_GetError() << '\n';
        return 1;
    }

    auto window = SDL_CreateWindow("Window", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, WINDOW_WIDTH, WINDOW_HEIGHT, 0);
    if (!window)
    {
        std::cerr << "Failed to create window: " << SDL_GetError() << '\n';
        SDL_Quit();
        return 1;
    }

    auto renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    if (!renderer)
    {
        std::cerr << "Failed to create renderer: " << SDL_GetError() << '\n';
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    bool isDone{};
    while (!isDone)
    {
        SDL_Event event;
        while (!isDone && SDL_PollEvent(&event))
        {
            switch (event.type)
            {
            case SDL_QUIT:
                isDone = true;
                break;

            case SDL_KEYUP:
                switch (event.key.keysym.sym)
                {
                case SDLK_ESCAPE:
                    isDone = true;
                    break;
                }
                break;
            }
        }
        if (isDone)
            break;

        SDL_SetRenderDrawColor(renderer, 100, 100, 100, 255);
        SDL_RenderClear(renderer);

        SDL_RenderPresent(renderer);
        SDL_Delay(16);
    }

    SDL_DestroyWindow(window);
    SDL_DestroyRenderer(renderer);
    SDL_Quit();
    return 0;
}
""",

"gtkmm-3.0":
r"""#include <iostream>

int main()
{
    std::cout << "Hello, World!\n";
    return 0;
}
""",

"fltk":
r"""#include <iostream>

int main()
{
    std::cout << "Hello, World!\n";
    return 0;
}
"""
}

def getCommandOutput(cmd: str) -> str:
    try:
        result = sp.run(cmd.split(" "), stdout=sp.PIPE, stderr=sp.PIPE)
    except:
        printerr("Failed to run command: \"{}\"\nexception: {}".format(cmd, sys.exc_info()))
        sys.exit(1)

    if result.returncode:
        printerr("Failed to run command: \"{}\"\nreturn code: {}\nstdout: {}\nstderr: {}".format(
            cmd, result.returncode, result.stdout, result.stderr))
        sys.exit(1)
    return result.stdout.decode("utf-8")

def fetchCFlagsAndIncludeDirs(cmd: str):
    for val in getCommandOutput(cmd).strip().split(" "):
        if val.strip().startswith("-I"):
            PROJECT_INCLUDE_DIRS.append(val.strip()[2:])
        else:
            PROJECT_CFLAGS.append(val.strip())

def fetchLibs(cmd: str):
    PROJECT_LIBS.extend([x.strip()[2:] for x in getCommandOutput(cmd).strip().split(" ")])

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

    def writeExportCCommands(self):
        self.file.write("set(CMAKE_EXPORT_COMPILE_COMMANDS true)\n")

    def writeProjectDecl(self, projectName: str, projectVersion: str):
        self.file.write("project({} VERSION {})\n".format(projectName, projectVersion))

    def writeFlags(self, flags: tuple):
        self.file.write("set(CMAKE_CXX_FLAGS \"{}\")\n".format(" ".join(flags)))

    def writeIncludeDirs(self, dirs: tuple):
        self.file.write("include_directories(\n{})\n".format("".join([" "*4+x+"\n" for x in dirs])))

    def writeLinkLibs(self, libs: tuple):
        self.file.write("link_libraries(\n{})\n".format("".join([" "*4+x+"\n" for x in libs])))

    def writeExeInfo(self, exeName: str):
        sourceFiles = []
        for file in iglob("src/**/*", recursive=True):
            if file.endswith(FILE_EXTENSIONS):
                sourceFiles.append(file)
        self.file.write("add_executable({}\n{})\n".format(exeName, "".join([" "*4+x+"\n" for x in sorted(sourceFiles or ["src/main.cpp"], reverse=True)])))

    def __del__(self):
        try:
            self.file.close()
        except AttributeError:
            pass

print("Generating project \"{}\" of type \"{}\"".format(PROJECT_NAME, PROJECT_TYPE))
if PROJECT_TYPE == "default":
    pass
elif PROJECT_TYPE == "sdl2":
    fetchCFlagsAndIncludeDirs("sdl2-config --cflags")
    fetchLibs("sdl2-config --libs")
elif PROJECT_TYPE == "gtkmm-3.0":
    fetchCFlagsAndIncludeDirs("pkg-config --cflags gtkmm-3.0")
    fetchLibs("pkg-config --libs gtkmm-3.0")
elif PROJECT_TYPE == "fltk":
    fetchCFlagsAndIncludeDirs("fltk-config --cxxflags")
    fetchLibs("fltk-config --ldflags")
else:
    printerr("Error: Invalid project type. Use `--list-project-types` or `-l` to get the list of available project types.")
    sys.exit(1)
try:
    file = ProjectFile()
except:
    printerr("Error: File already exists")
    sys.exit(1)
file.writeCmakeMinVer()
file.writeLine()
file.writeCxxStandard(CXX_STANDARD_VER)
file.writeLine()
file.writeExportCCommands()
file.writeLine()
file.writeProjectDecl(PROJECT_NAME, "1.0")
file.writeLine()
file.writeFlags(tuple(PROJECT_CFLAGS))
file.writeLine()
if PROJECT_INCLUDE_DIRS:
    file.writeIncludeDirs(tuple(PROJECT_INCLUDE_DIRS))
if PROJECT_LIBS:
    file.writeLinkLibs(tuple(PROJECT_LIBS))
if PROJECT_INCLUDE_DIRS or PROJECT_LIBS:
    file.writeLine()
file.writeExeInfo(PROJECT_NAME)
file.writeLine()
print("CMakeLists.txt written")

print("Writing skeleton")
if not os.path.exists("./src"):
    print("Creating ./src/")
    os.mkdir("./src")
if not os.path.exists("./src/main.cpp"):
    print("Writing ./src/main.cpp")
    with open("./src/main.cpp", "w+") as file:
        file.write(MAIN_SKELETONS[PROJECT_TYPE])
else:
    print("src/main.cpp already exists, not writing")

print("Done")

