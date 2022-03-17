import os

"""
    For the given path, get the List of all files in the directory tree 
"""


def get_list_of_files(dir_name):
    # create a list of file and sub directories
    # names in the given directory
    listOfFile = os.listdir(dir_name)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        filename = entry.split("/")[-1]
        if filename.startswith("cloud"):
            allFiles.append(filename)
    return allFiles


def main():

    dirName = "/home/hubert/Desktop/Heuristics/RS/extract_flooding_events/earthengine"

    # Get the list of all files in directory tree at given path
    listOfFiles = get_list_of_files(dirName)

    # Print the files
    for elem in listOfFiles:
        print(elem)
    print("****************")

    # Get the list of all files in directory tree at given path
    listOfFiles = list()
    for (dirpath, dirnames, filenames) in os.walk(dirName):
        listOfFiles += [os.path.join(dirpath, file.split("/")[-1]) for file in filenames]

    # Print the files
    for elem in listOfFiles:
        print(elem)


if __name__ == "__main__":
    main()
