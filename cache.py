import pickle
from os import listdir, mkdir, path

CACHE_DIR = 'cache'

def save(object, rel_file_path: str, overwrite = False, verbose = True):
    
    total_path = path.join(CACHE_DIR, rel_file_path)
    file_path = total_path + ".pickle"
    
    # Check for existing file
    if not overwrite and path.exists(file_path):
        raise FileExistsError(total_path)
    
    with open(file_path, "wb") as output_file:
        pickle.dump(object, output_file, pickle.HIGHEST_PROTOCOL)
    
    if verbose:
        print(f"Saved: '{total_path}'.")

        
def load(rel_file_path, verbose = True):
    
    total_path = path.join(CACHE_DIR, rel_file_path)
    
    with open(total_path + ".pickle", "rb") as input_file:
        file = pickle.load(input_file)
    
    if verbose:
        print(f"Loaded: '{total_path}.pickle'.")
        
    return file

def cache_dir_exists(rel_dir):
    return path.exists(path.join(CACHE_DIR, rel_dir))

def cache_file_exists(rel_dir):
    return path.exists(path.join(CACHE_DIR, rel_dir) + ".pickle")

def cache_list_dir(dir):
    return [item for item in listdir(path.join(CACHE_DIR, dir))]


def _makedir(dir):
    
    mkdir(dir)
    
def ensuredir(rel_dir, verbose = True):
    dir = path.join(CACHE_DIR, rel_dir)
    if not path.exists(dir):
        _makedir(dir)
        if verbose:
            print(f"Created directory '{dir}'")